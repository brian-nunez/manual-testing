from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from pathlib import Path

from manual_testing.config import AppConfig
from manual_testing.form_purpose_analyzer import analyze_input_purposes
from manual_testing.json_utils import decision_fallback, parse_decision_response
from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.factory import build_adapter
from manual_testing.models import Decision, ManualQuestion, QuestionResult, RunOutput
from manual_testing.prompt_builder import build_prompt
from manual_testing.publisher import PublishError, publish_results
from manual_testing.question_loader import load_manual_questions
from manual_testing.s3_upload import S3UploadError, upload_file_path_style
from manual_testing.telemetry import NullLogger, OtelLogger, build_logger

_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", flags=re.DOTALL)
_HTML_HEAD_RE = re.compile(r"<head\b[^>]*>.*?</head>", flags=re.IGNORECASE | re.DOTALL)
_HTML_NONCONTENT_TAG_RE = re.compile(
    r"<(?:script|style|noscript|template)\b[^>]*>.*?</(?:script|style|noscript|template)>",
    flags=re.IGNORECASE | re.DOTALL,
)
_HTML_BODY_RE = re.compile(r"<body\b[^>]*>(.*?)</body>", flags=re.IGNORECASE | re.DOTALL)
_HTML_BETWEEN_TAG_WS_RE = re.compile(r">\s+<")
_HTML_MULTI_WS_RE = re.compile(r"\s{2,}")
_HTML_ATTR_VALUE_RE = r"(?:\"[^\"]*\"|'[^']*'|[^\s>]+)"
_HTML_CLASS_ATTR_RE = re.compile(rf"\sclass\s*=\s*{_HTML_ATTR_VALUE_RE}", flags=re.IGNORECASE)
_HTML_STYLE_ATTR_RE = re.compile(rf"\sstyle\s*=\s*{_HTML_ATTR_VALUE_RE}", flags=re.IGNORECASE)
_HTML_NOISE_ATTR_RE = re.compile(
    rf"\s(?:data-[a-zA-Z0-9:_-]+|x-data|x-on:[a-zA-Z0-9:_-]+|"
    rf"ng-[a-zA-Z0-9:_-]+|data-testid|data-test|data-cy|nonce|integrity|crossorigin|"
    rf"referrerpolicy|fetchpriority|decoding|loading)\s*=\s*{_HTML_ATTR_VALUE_RE}",
    flags=re.IGNORECASE,
)
_SVG_OPEN_TAG_RE = re.compile(
    r"<(?P<tag>"
    r"svg|path|g|defs|symbol|use|circle|ellipse|line|polyline|polygon|rect|"
    r"text|tspan|clipPath|mask|pattern|marker|linearGradient|radialGradient|stop|"
    r"filter|fe[a-zA-Z]+"
    r")(?P<attrs>\s[^>]*)?>",
    flags=re.IGNORECASE,
)
_SVG_DROP_ATTR_NAMES = {
    "class",
    "style",
    "fill",
    "fill-opacity",
    "fill-rule",
    "stroke",
    "stroke-width",
    "stroke-opacity",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-dasharray",
    "stroke-dashoffset",
    "opacity",
    "transform",
    "filter",
    "mask",
    "clip-path",
    "clip-rule",
    "d",
    "points",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "width",
    "height",
    "viewbox",
    "preserveaspectratio",
    "xmlns",
    "xmlns:xlink",
    "href",
    "xlink:href",
}
_SVG_ATTR_RE = re.compile(
    r"(?P<space>\s+)(?P<name>[a-zA-Z_:][a-zA-Z0-9:_.-]*)\s*=\s*"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^\s>]+)"
)


def run_pipeline(config: AppConfig) -> tuple[RunOutput, Path]:
    logger = build_logger(
        enabled=config.otel_logging_enabled,
        collector_url=config.otel_collector_url,
        service_name=config.otel_service_name,
        resource_attributes=config.otel_resource_attributes,
        headers=config.otel_headers,
        flush_on_each_log=config.otel_flush_on_each_log,
        timeout_seconds=config.otel_timeout_seconds,
        run_id=config.run_id,
    )
    logger.start()

    try:
        logger.info(
            "pipeline_start",
            {
                "provider": config.provider,
                "model": config.model,
                "capture_browser": config.capture_browser,
                "target_url": config.url or "",
                "manual_list_dir": str(config.manual_list_dir),
                "output_file": str(config.output_file),
            },
        )

        questions = load_manual_questions(config.manual_list_dir, config.question_ids)
        logger.info("questions_loaded", {"count": len(questions)})

        run_dir = config.output_dir / config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("run_directory_ready", {"run_dir": str(run_dir)})

        html: str | None = None
        final_url = config.url
        trace_path: Path | None = None
        structured_evidence_by_question: dict[str, dict] = {}

        screenshots_by_question: dict[str, list[Path]] = {question.question_id: [] for question in questions}

        provided_screenshots = _existing_paths(config.screenshot_files)
        logger.info("provided_screenshots_loaded", {"count": len(provided_screenshots)})

        if config.html_file:
            html = config.html_file.read_text(encoding="utf-8")
            logger.info(
                "html_file_loaded",
                {"path": str(config.html_file), "chars": len(html)},
            )

        browser_error: str | None = None
        if config.capture_browser and config.url:
            logger.info("browser_capture_enabled", {"url": config.url})
            try:
                from manual_testing.browser_capture import BrowserCaptureError, collect_browser_artifacts

                browser_artifacts = collect_browser_artifacts(
                    config,
                    questions,
                    run_dir,
                    logger=logger,
                )
                final_url = browser_artifacts.final_url
                trace_path = browser_artifacts.trace_path
                if not html and browser_artifacts.html:
                    html = browser_artifacts.html
                    logger.info("html_source_selected", {"source": "browser_capture"})

                for question_id, screenshot_paths in browser_artifacts.screenshots_by_question.items():
                    screenshots_by_question.setdefault(question_id, [])
                    screenshots_by_question[question_id].extend(screenshot_paths)

                logger.info(
                    "browser_capture_completed",
                    {
                        "final_url": final_url or "",
                        "trace_path": str(trace_path) if trace_path else "",
                    },
                )

            except BrowserCaptureError as exc:
                browser_error = str(exc)
                logger.error("browser_capture_failed", {"error": browser_error})
            except ModuleNotFoundError as exc:
                browser_error = f"Playwright is not installed: {exc}"
                logger.error("browser_capture_module_missing", {"error": browser_error})
        else:
            logger.info(
                "browser_capture_skipped",
                {"capture_browser": config.capture_browser, "has_url": bool(config.url)},
            )

        if not html and not provided_screenshots and not any(screenshots_by_question.values()):
            logger.error("no_page_input", {})
            if browser_error:
                raise RuntimeError(
                    "Browser capture failed and no fallback input was collected. "
                    f"Browser error: {browser_error}. "
                    "Try --wait-until domcontentloaded, increase --navigation-timeout-ms, "
                    "or provide --html-file/--screenshot-file."
                )
            raise RuntimeError(
                "No page input available. Provide --url, --html-file, and/or --screenshot-file."
            )

        question_ids = {question.question_id for question in questions}
        if html and "question_7" in question_ids:
            form_analysis = analyze_input_purposes(html).to_dict()
            structured_evidence_by_question["question_7"] = {
                "source": "selectolax_form_purpose_analyzer",
                "analysis": form_analysis,
            }
            logger.info(
                "question_7_form_analysis_ready",
                {
                    "parser": form_analysis.get("parser", ""),
                    "total_fields": form_analysis.get("summary", {}).get("total_fields", 0),
                    "user_info_field_count": form_analysis.get("summary", {}).get("user_info_field_count", 0),
                    "missing_autocomplete_count": form_analysis.get("summary", {}).get(
                        "fields_missing_autocomplete_count", 0
                    ),
                    "mismatched_autocomplete_count": form_analysis.get("summary", {}).get(
                        "fields_mismatched_autocomplete_count", 0
                    ),
                },
            )

        adapter = build_adapter(config.provider)
        logger.info("llm_adapter_ready", {"provider": config.provider, "adapter_type": type(adapter).__name__})
        results = _process_questions(
            questions=questions,
            adapter=adapter,
            config=config,
            final_url=final_url,
            html=html,
            screenshots_by_question=screenshots_by_question,
            provided_screenshots=provided_screenshots,
            structured_evidence_by_question=structured_evidence_by_question,
            logger=logger,
        )

        run_output = RunOutput(
            run_id=config.run_id,
            provider=config.provider,
            model=config.model,
            url=final_url,
            results=results,
            trace_path=str(trace_path) if trace_path else None,
            trace_upload_url=None,
            publish_status=None,
        )

        payload = run_output.to_dict()
        logger.info("result_payload_built", {"results_count": len(results)})

        if browser_error:
            payload["browser_capture_error"] = browser_error
            logger.warn("result_payload_browser_error_attached", {"error": browser_error})

        if config.s3_upload_enabled and trace_path:
            logger.info("trace_upload_start", {"trace_path": str(trace_path)})
            trace_upload_url, trace_upload_error = _upload_trace(config, trace_path, logger=logger)
            run_output.trace_upload_url = trace_upload_url
            payload["artifacts"]["trace_upload_url"] = trace_upload_url
            if trace_upload_error:
                payload["trace_upload_error"] = trace_upload_error
                logger.error("trace_upload_failed", {"error": trace_upload_error})
            else:
                logger.info("trace_upload_complete", {"trace_upload_url": trace_upload_url or ""})
        else:
            logger.info(
                "trace_upload_skipped",
                {"s3_upload_enabled": config.s3_upload_enabled, "has_trace_path": bool(trace_path)},
            )

        if config.publish_api_url:
            logger.info("publish_start", {"url": config.publish_api_url})
            try:
                publish_status = publish_results(
                    payload,
                    url=config.publish_api_url,
                    token=config.publish_api_token,
                    timeout_seconds=config.publish_timeout_seconds,
                )
                run_output.publish_status = publish_status
                payload["publish_status"] = publish_status
                logger.info(
                    "publish_complete",
                    {"status_code": publish_status.get("status_code", "")},
                )
            except PublishError as exc:
                run_output.publish_status = {"error": str(exc)}
                payload["publish_status"] = run_output.publish_status
                logger.error("publish_failed", {"error": str(exc)})
        else:
            logger.info("publish_skipped", {})

        config.output_file.parent.mkdir(parents=True, exist_ok=True)
        config.output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        logger.info(
            "output_written",
            {
                "output_file": str(config.output_file),
                "output_size_bytes": config.output_file.stat().st_size,
            },
        )

        logger.info(
            "pipeline_complete",
            {
                "total_questions": payload["summary"]["total_questions"],
                "errors": payload["summary"]["errors"],
                "needs_manual_testing": payload["summary"]["needs_manual_testing"],
            },
        )
        return run_output, config.output_file

    except Exception as exc:
        logger.error("pipeline_exception", {"error": str(exc)})
        raise
    finally:
        logger.stop()


def _process_questions(
    *,
    questions: list[ManualQuestion],
    adapter: LLMAdapter,
    config: AppConfig,
    final_url: str | None,
    html: str | None,
    screenshots_by_question: dict[str, list[Path]],
    provided_screenshots: list[Path],
    structured_evidence_by_question: dict[str, dict],
    logger: OtelLogger | NullLogger,
) -> list[QuestionResult]:
    total_questions = len(questions)
    if total_questions <= 1 or config.execution_mode == "sequential":
        logger.info(
            "question_execution_mode",
            {"mode": "sequential", "question_count": total_questions, "max_workers": 1},
        )
        return [
            _evaluate_question(
                question=question,
                adapter=adapter,
                config=config,
                final_url=final_url,
                html=html,
                screenshots_by_question=screenshots_by_question,
                provided_screenshots=provided_screenshots,
                structured_evidence_by_question=structured_evidence_by_question,
                logger=logger,
            )
            for question in questions
        ]

    worker_count = max(1, min(config.max_workers, total_questions))
    logger.info(
        "question_execution_mode",
        {"mode": "parallel", "question_count": total_questions, "max_workers": worker_count},
    )

    ordered_results: list[QuestionResult | None] = [None] * total_questions
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="question-worker") as executor:
        future_to_index = {
            executor.submit(
                _evaluate_question,
                question=question,
                adapter=adapter,
                config=config,
                final_url=final_url,
                html=html,
                screenshots_by_question=screenshots_by_question,
                provided_screenshots=provided_screenshots,
                structured_evidence_by_question=structured_evidence_by_question,
                logger=logger,
            ): index
            for index, question in enumerate(questions)
        }
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            question = questions[index]
            try:
                ordered_results[index] = future.result()
            except Exception as exc:
                logger.error(
                    "question_worker_exception",
                    {"question_id": question.question_id, "error": str(exc)},
                )
                ordered_results[index] = QuestionResult(
                    question_id=question.question_id,
                    title=question.title,
                    decision=decision_fallback(f"Question processing failed: {exc}"),
                    prompt=None,
                    raw_response=None,
                    screenshots=[],
                    structured_evidence=structured_evidence_by_question.get(question.question_id),
                    error=str(exc),
                )

    return [result for result in ordered_results if result is not None]


def _evaluate_question(
    *,
    question: ManualQuestion,
    adapter: LLMAdapter,
    config: AppConfig,
    final_url: str | None,
    html: str | None,
    screenshots_by_question: dict[str, list[Path]],
    provided_screenshots: list[Path],
    structured_evidence_by_question: dict[str, dict],
    logger: OtelLogger | NullLogger,
) -> QuestionResult:
    try:
        question_structured_evidence = structured_evidence_by_question.get(question.question_id)
        question_screens = _merge_unique_paths(
            screenshots_by_question.get(question.question_id, []) + provided_screenshots
        )
        logger.info(
            "question_processing_start",
            {
                "question_id": question.question_id,
                "title": question.title,
                "screenshot_count": len(question_screens),
                "html_available": bool(html),
            },
        )

        prompt: str | None = None
        raw_response: str | None = None
        error: str | None = None
        llm_failed = False

        prompt = build_prompt(
            question,
            url=final_url,
        )
        logger.debug(
            "question_prompt_built",
            {"question_id": question.question_id, "prompt_chars": len(prompt)},
        )

        try:
            logger.info(
                "llm_generate_start",
                {
                    "question_id": question.question_id,
                    "model": config.model,
                    "image_count": len(question_screens),
                },
            )
            raw_response = adapter.generate(
                prompt,
                model=config.model,
                image_paths=question_screens,
                timeout_seconds=config.llm_timeout_seconds,
                html=_prepare_html_for_llm(html, config.html_max_chars),
                structured_evidence=question_structured_evidence,
                url=final_url,
                question_id=question.question_id,
                question_title=question.title,
            )
            logger.debug(
                "llm_generate_complete",
                {
                    "question_id": question.question_id,
                    "response_chars": len(raw_response),
                },
            )
            decision = parse_decision_response(raw_response)
            logger.info(
                "decision_parsed",
                {
                    "question_id": question.question_id,
                    "needs_manual_testing": decision.needs_manual_testing,
                },
            )
        except Exception as exc:
            llm_failed = True
            decision = decision_fallback(f"Decision generation failed: {exc}")
            raw_response = None
            error = str(exc)
            logger.error(
                "question_processing_error",
                {"question_id": question.question_id, "error": error},
            )

        decision = _apply_question_7_fallback_on_llm_error(
            question_id=question.question_id,
            decision=decision,
            structured_evidence=question_structured_evidence,
            llm_failed=llm_failed,
            logger=logger,
        )

        result = QuestionResult(
            question_id=question.question_id,
            title=question.title,
            decision=decision,
            prompt=prompt if config.include_prompt_in_output else None,
            raw_response=raw_response if config.include_raw_response else None,
            screenshots=[str(path) for path in question_screens],
            structured_evidence=question_structured_evidence,
            error=error,
        )
        logger.info(
            "question_processing_complete",
            {
                "question_id": question.question_id,
                "error": bool(error),
                "needs_manual_testing": decision.needs_manual_testing,
            },
        )
        return result

    except Exception as exc:
        error_message = str(exc)
        logger.error(
            "question_processing_unhandled_error",
            {"question_id": question.question_id, "error": error_message},
        )
        return QuestionResult(
            question_id=question.question_id,
            title=question.title,
            decision=decision_fallback(f"Question processing failed: {error_message}"),
            prompt=None,
            raw_response=None,
            screenshots=[],
            structured_evidence=structured_evidence_by_question.get(question.question_id),
            error=error_message,
        )


def _upload_trace(
    config: AppConfig,
    trace_path: Path,
    logger: OtelLogger | NullLogger | None = None,
) -> tuple[str | None, str | None]:
    logger = logger or NullLogger()
    required = [
        config.s3_endpoint_url,
        config.s3_bucket,
        config.s3_access_key_id,
        config.s3_secret_access_key,
    ]
    if any(not value for value in required):
        logger.warn("trace_upload_missing_settings", {})
        return None, "S3 upload enabled but required S3/AWS settings are missing."

    object_key = f"{config.s3_key_prefix.rstrip('/')}/{config.run_id}/{trace_path.name}"
    try:
        logger.info(
            "trace_upload_request",
            {
                "endpoint_url": config.s3_endpoint_url or "",
                "bucket": config.s3_bucket or "",
                "object_key": object_key,
                "method": config.s3_method,
            },
        )
        return (
            upload_file_path_style(
                trace_path,
                endpoint_url=config.s3_endpoint_url or "",
                bucket=config.s3_bucket or "",
                object_key=object_key,
                region=config.s3_region,
                access_key_id=config.s3_access_key_id or "",
                secret_access_key=config.s3_secret_access_key or "",
                session_token=config.s3_session_token,
                method=config.s3_method,
            ),
            None,
        )
    except S3UploadError as exc:
        logger.error("trace_upload_error", {"error": str(exc)})
        return None, str(exc)


def _existing_paths(paths: list[Path]) -> list[Path]:
    existing = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Screenshot file not found: {path}")
        existing.append(path)
    return existing


def _merge_unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _prepare_html_for_llm(html: str | None, max_chars: int) -> str | None:
    if html is None:
        return None
    normalized = html.strip()
    if not normalized:
        return None

    # Remove obvious non-semantic/noisy sections to reduce token waste.
    normalized = _HTML_COMMENT_RE.sub("", normalized)
    normalized = _HTML_HEAD_RE.sub("", normalized)
    normalized = _HTML_NONCONTENT_TAG_RE.sub("", normalized)
    normalized = _strip_global_noise_attributes(normalized)
    normalized = _strip_svg_noise_attributes(normalized)

    # Keep body content when available.
    body_match = _HTML_BODY_RE.search(normalized)
    if body_match:
        normalized = body_match.group(1)

    # Compact whitespace.
    normalized = _HTML_BETWEEN_TAG_WS_RE.sub("><", normalized)
    normalized = _HTML_MULTI_WS_RE.sub(" ", normalized).strip()

    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars]


def _strip_global_noise_attributes(html: str) -> str:
    cleaned = _HTML_CLASS_ATTR_RE.sub("", html)
    cleaned = _HTML_STYLE_ATTR_RE.sub("", cleaned)
    cleaned = _HTML_NOISE_ATTR_RE.sub("", cleaned)
    return cleaned


def _strip_svg_noise_attributes(html: str) -> str:
    def _replace_tag(match: re.Match[str]) -> str:
        tag = match.group("tag")
        attrs = match.group("attrs") or ""
        sanitized_attrs = _strip_svg_attrs(attrs)
        return f"<{tag}{sanitized_attrs}>"

    return _SVG_OPEN_TAG_RE.sub(_replace_tag, html)


def _strip_svg_attrs(attrs: str) -> str:
    if not attrs:
        return ""

    def _drop_attr(match: re.Match[str]) -> str:
        name = match.group("name").lower()
        if name in _SVG_DROP_ATTR_NAMES:
            return ""
        if name.startswith("data-"):
            return ""
        return match.group(0)

    cleaned = _SVG_ATTR_RE.sub(_drop_attr, attrs)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    if not cleaned:
        return ""
    return f" {cleaned}"


def _apply_question_7_fallback_on_llm_error(
    *,
    question_id: str,
    decision: Decision,
    structured_evidence: dict | None,
    llm_failed: bool,
    logger: OtelLogger | NullLogger,
) -> Decision:
    if question_id != "question_7":
        return decision
    if not structured_evidence:
        return decision
    if not llm_failed:
        return decision

    summary = (structured_evidence.get("analysis") or {}).get("summary") or {}
    user_info_field_count = int(summary.get("user_info_field_count", 0) or 0)
    if user_info_field_count <= 0:
        return decision

    if decision.needs_manual_testing:
        return decision

    missing_count = int(summary.get("fields_missing_autocomplete_count", 0) or 0)
    mismatch_count = int(summary.get("fields_mismatched_autocomplete_count", 0) or 0)

    reason = (
        f"Overridden by deterministic form analysis: detected {user_info_field_count} user-information field(s). "
        f"Potential autocomplete issues: missing={missing_count}, mismatch={mismatch_count}. "
        "Manual Test #7 applies and should be run."
    )
    logger.warn(
        "question_7_llm_error_fallback_override",
        {
            "previous_needs_manual_testing": decision.needs_manual_testing,
            "user_info_field_count": user_info_field_count,
            "missing_autocomplete_count": missing_count,
            "mismatched_autocomplete_count": mismatch_count,
        },
    )
    return Decision(
        needs_manual_testing=True,
        reason=reason,
    )
