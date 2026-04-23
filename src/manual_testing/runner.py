from __future__ import annotations

import json
from pathlib import Path

from manual_testing.config import AppConfig
from manual_testing.json_utils import decision_fallback, parse_decision_response
from manual_testing.llm.factory import build_adapter
from manual_testing.models import QuestionResult, RunOutput
from manual_testing.prompt_builder import build_prompt
from manual_testing.publisher import PublishError, publish_results
from manual_testing.question_loader import load_manual_questions
from manual_testing.s3_upload import S3UploadError, upload_file_path_style
from manual_testing.telemetry import NullLogger, OtelLogger, build_logger


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

        adapter = build_adapter(config.provider)
        logger.info("llm_adapter_ready", {"provider": config.provider, "adapter_type": type(adapter).__name__})
        results: list[QuestionResult] = []

        for question in questions:
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

            prompt = build_prompt(
                question,
                url=final_url,
                html=html,
                screenshot_paths=question_screens,
                html_max_chars=config.html_max_chars,
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
                )
                logger.debug(
                    "llm_generate_complete",
                    {
                        "question_id": question.question_id,
                        "response_chars": len(raw_response),
                    },
                )
                decision = parse_decision_response(raw_response)
                error = None
                logger.info(
                    "decision_parsed",
                    {
                        "question_id": question.question_id,
                        "relevant": decision.relevant,
                        "needs_manual_testing": decision.needs_manual_testing,
                    },
                )
            except Exception as exc:
                decision = decision_fallback(f"Decision generation failed: {exc}")
                raw_response = None
                error = str(exc)
                logger.error(
                    "question_processing_error",
                    {"question_id": question.question_id, "error": error},
                )

            results.append(
                QuestionResult(
                    question_id=question.question_id,
                    title=question.title,
                    decision=decision,
                    prompt=prompt if config.include_prompt_in_output else None,
                    raw_response=raw_response if config.include_raw_response else None,
                    screenshots=[str(path) for path in question_screens],
                    error=error,
                )
            )
            logger.info(
                "question_processing_complete",
                {
                    "question_id": question.question_id,
                    "error": bool(error),
                    "relevant": decision.relevant,
                    "needs_manual_testing": decision.needs_manual_testing,
                },
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
