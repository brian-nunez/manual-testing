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


def run_pipeline(config: AppConfig) -> tuple[RunOutput, Path]:
    questions = load_manual_questions(config.manual_list_dir, config.question_ids)
    run_dir = config.output_dir / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    html: str | None = None
    final_url = config.url
    trace_path: Path | None = None

    screenshots_by_question: dict[str, list[Path]] = {question.question_id: [] for question in questions}

    provided_screenshots = _existing_paths(config.screenshot_files)

    if config.html_file:
        html = config.html_file.read_text(encoding="utf-8")

    browser_error: str | None = None
    if config.capture_browser and config.url:
        try:
            from manual_testing.browser_capture import BrowserCaptureError, collect_browser_artifacts

            browser_artifacts = collect_browser_artifacts(config, questions, run_dir)
            final_url = browser_artifacts.final_url
            trace_path = browser_artifacts.trace_path
            if not html and browser_artifacts.html:
                html = browser_artifacts.html

            for question_id, screenshot_paths in browser_artifacts.screenshots_by_question.items():
                screenshots_by_question.setdefault(question_id, [])
                screenshots_by_question[question_id].extend(screenshot_paths)

        except BrowserCaptureError as exc:
            browser_error = str(exc)
        except ModuleNotFoundError as exc:
            browser_error = f"Playwright is not installed: {exc}"

    if not html and not provided_screenshots and not any(screenshots_by_question.values()):
        raise RuntimeError(
            "No page input available. Provide --url, --html-file, and/or --screenshot-file."
        )

    adapter = build_adapter(config.provider)
    results: list[QuestionResult] = []

    for question in questions:
        question_screens = _merge_unique_paths(
            screenshots_by_question.get(question.question_id, []) + provided_screenshots
        )

        prompt = build_prompt(
            question,
            url=final_url,
            html=html,
            screenshot_paths=question_screens,
            html_max_chars=config.html_max_chars,
        )

        try:
            raw_response = adapter.generate(
                prompt,
                model=config.model,
                image_paths=question_screens,
                timeout_seconds=config.llm_timeout_seconds,
            )
            decision = parse_decision_response(raw_response)
            error = None
        except Exception as exc:
            decision = decision_fallback(f"Decision generation failed: {exc}")
            raw_response = None
            error = str(exc)

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

    if browser_error:
        payload["browser_capture_error"] = browser_error

    if config.s3_upload_enabled and trace_path:
        trace_upload_url, trace_upload_error = _upload_trace(config, trace_path)
        run_output.trace_upload_url = trace_upload_url
        payload["artifacts"]["trace_upload_url"] = trace_upload_url
        if trace_upload_error:
            payload["trace_upload_error"] = trace_upload_error

    if config.publish_api_url:
        try:
            publish_status = publish_results(
                payload,
                url=config.publish_api_url,
                token=config.publish_api_token,
                timeout_seconds=config.publish_timeout_seconds,
            )
            run_output.publish_status = publish_status
            payload["publish_status"] = publish_status
        except PublishError as exc:
            run_output.publish_status = {"error": str(exc)}
            payload["publish_status"] = run_output.publish_status

    config.output_file.parent.mkdir(parents=True, exist_ok=True)
    config.output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return run_output, config.output_file


def _upload_trace(config: AppConfig, trace_path: Path) -> tuple[str | None, str | None]:
    required = [
        config.s3_endpoint_url,
        config.s3_bucket,
        config.s3_access_key_id,
        config.s3_secret_access_key,
    ]
    if any(not value for value in required):
        return None, "S3 upload enabled but required S3/AWS settings are missing."

    object_key = f"{config.s3_key_prefix.rstrip('/')}/{config.run_id}/{trace_path.name}"
    try:
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
