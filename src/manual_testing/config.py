from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from manual_testing.models import Viewport


DEFAULT_SCREENSHOT_QUESTION_IDS = {
    "question_1",
    "question_3",
    "question_4",
    "question_5",
    "question_8",
    "question_9",
    "question_10",
    "question_12",
    "question_14",
    "question_15",
    "question_16",
}

DEFAULT_VIEWPORTS = [Viewport(name="desktop", width=1366, height=768)]

DEFAULT_QUESTION_VIEWPORTS: dict[str, list[Viewport]] = {
    "question_9": [
        Viewport(name="mobile", width=320, height=900),
        Viewport(name="tablet", width=768, height=1024),
        Viewport(name="desktop", width=1366, height=900),
    ],
    "question_16": [
        Viewport(name="mobile", width=390, height=844),
        Viewport(name="desktop", width=1366, height=900),
    ],
}


@dataclass
class AppConfig:
    run_id: str
    provider: str
    model: str
    manual_list_dir: Path
    output_dir: Path
    output_file: Path
    url: str | None
    html_file: Path | None
    screenshot_files: list[Path]
    question_ids: list[str] | None
    capture_browser: bool
    headless: bool
    wait_until: str
    navigation_timeout_ms: int
    post_load_wait_ms: int
    viewport_settle_ms: int
    llm_timeout_seconds: int
    html_max_chars: int
    include_raw_response: bool
    include_prompt_in_output: bool
    automatic_behavior_question_id: str
    automatic_behavior_timeseries_enabled: bool
    automatic_behavior_interval_ms: int
    automatic_behavior_duration_ms: int
    otel_logging_enabled: bool
    otel_collector_url: str | None
    otel_service_name: str
    otel_resource_attributes: dict[str, str]
    otel_headers: dict[str, str]
    otel_flush_on_each_log: bool
    otel_timeout_seconds: int
    default_viewports: list[Viewport] = field(default_factory=lambda: list(DEFAULT_VIEWPORTS))
    question_viewports: dict[str, list[Viewport]] = field(default_factory=lambda: dict(DEFAULT_QUESTION_VIEWPORTS))
    screenshot_question_ids: set[str] = field(default_factory=lambda: set(DEFAULT_SCREENSHOT_QUESTION_IDS))
    publish_api_url: str | None = None
    publish_api_token: str | None = None
    publish_timeout_seconds: int = 30
    s3_upload_enabled: bool = False
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_region: str = "us-east-1"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_session_token: str | None = None
    s3_key_prefix: str = "playwright-traces"
    s3_method: str = "POST"

    @classmethod
    def from_sources(cls, args: Any) -> "AppConfig":
        run_id = _coalesce(args.run_id, os.getenv("RUN_ID"), str(uuid.uuid4()))
        provider = _coalesce(args.provider, os.getenv("LLM_PROVIDER"), "codex").lower()

        default_model = {
            "codex": "gpt-5.4-mini",
            "gemini": "gemini-2.5-flash",
            "llama": "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "ollama": "llama3.2-vision",
        }.get(provider, "gpt-5.4-mini")
        model = _coalesce(args.model, os.getenv("LLM_MODEL"), default_model)

        manual_list_dir = Path(_coalesce(args.manual_list_dir, os.getenv("MANUAL_LIST_DIR"), "manual-list")).expanduser().resolve()
        output_dir = Path(_coalesce(args.output_dir, os.getenv("OUTPUT_DIR"), "run-artifacts")).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = Path(
            _coalesce(
                args.output_file,
                os.getenv("OUTPUT_FILE"),
                str(output_dir / f"manual_triage_{run_id}.json"),
            )
        ).expanduser().resolve()

        url = _coalesce(args.url, os.getenv("TARGET_URL"), None)
        html_file_raw = _coalesce(args.html_file, os.getenv("HTML_FILE"), None)
        html_file = Path(html_file_raw).expanduser().resolve() if html_file_raw else None

        screenshot_files = [Path(p).expanduser().resolve() for p in (args.screenshot_files or [])]

        question_ids = _parse_csv_list(_coalesce(args.question_ids, os.getenv("QUESTION_IDS"), None))

        capture_browser = _to_bool(_coalesce(args.capture_browser, os.getenv("CAPTURE_BROWSER"), "true"))
        headless = _to_bool(_coalesce(args.headless, os.getenv("PLAYWRIGHT_HEADLESS"), "true"))
        wait_until = _coalesce(args.wait_until, os.getenv("PLAYWRIGHT_WAIT_UNTIL"), "domcontentloaded")

        navigation_timeout_ms = int(_coalesce(args.navigation_timeout_ms, os.getenv("NAVIGATION_TIMEOUT_MS"), 45000))
        post_load_wait_ms = int(_coalesce(args.post_load_wait_ms, os.getenv("POST_LOAD_WAIT_MS"), 1200))
        viewport_settle_ms = int(_coalesce(args.viewport_settle_ms, os.getenv("VIEWPORT_SETTLE_MS"), 500))
        llm_timeout_seconds = int(_coalesce(args.llm_timeout_seconds, os.getenv("LLM_TIMEOUT_SECONDS"), 90))
        html_max_chars = int(_coalesce(args.html_max_chars, os.getenv("HTML_MAX_CHARS"), 30000))

        include_raw_response = _to_bool(
            _coalesce(args.include_raw_response, os.getenv("INCLUDE_RAW_RESPONSE"), "false")
        )
        include_prompt_in_output = _to_bool(
            _coalesce(args.include_prompt_in_output, os.getenv("INCLUDE_PROMPT_IN_OUTPUT"), "false")
        )

        automatic_behavior_question_id = _coalesce(
            args.automatic_behavior_question_id,
            os.getenv("AUTOMATIC_BEHAVIOR_QUESTION_ID"),
            "question_1",
        )
        automatic_behavior_timeseries_enabled = _to_bool(
            _coalesce(
                args.automatic_behavior_timeseries_enabled,
                os.getenv("AUTOMATIC_BEHAVIOR_TIMESERIES_ENABLED"),
                "true",
            )
        )
        automatic_behavior_interval_ms = int(
            _coalesce(
                args.automatic_behavior_interval_ms,
                os.getenv("AUTOMATIC_BEHAVIOR_INTERVAL_MS"),
                500,
            )
        )
        automatic_behavior_duration_ms = int(
            _coalesce(
                args.automatic_behavior_duration_ms,
                os.getenv("AUTOMATIC_BEHAVIOR_DURATION_MS"),
                3000,
            )
        )

        otel_logging_enabled = _to_bool(
            _coalesce(args.otel_logging_enabled, os.getenv("OTEL_LOGGING_ENABLED"), "false")
        )
        otel_collector_url = _coalesce(args.otel_collector_url, os.getenv("OTEL_COLLECTOR_URL"), None)
        otel_service_name = _coalesce(
            args.otel_service_name,
            os.getenv("OTEL_SERVICE_NAME"),
            "manual-testing-triage",
        )
        otel_resource_attributes = _parse_json_object(
            _coalesce(
                args.otel_resource_attributes_json,
                os.getenv("OTEL_RESOURCE_ATTRIBUTES_JSON"),
                None,
            )
        )
        otel_headers = _parse_json_object(
            _coalesce(args.otel_headers_json, os.getenv("OTEL_HEADERS_JSON"), None)
        )
        otel_flush_on_each_log = _to_bool(
            _coalesce(args.otel_flush_on_each_log, os.getenv("OTEL_FLUSH_ON_EACH_LOG"), "false")
        )
        otel_timeout_seconds = int(
            _coalesce(args.otel_timeout_seconds, os.getenv("OTEL_TIMEOUT_SECONDS"), 10)
        )

        default_viewports = _parse_viewports(
            _coalesce(args.default_viewports_json, os.getenv("DEFAULT_VIEWPORTS_JSON"), None),
            fallback=list(DEFAULT_VIEWPORTS),
        )
        question_viewports = _parse_question_viewports(
            _coalesce(args.question_viewports_json, os.getenv("QUESTION_VIEWPORTS_JSON"), None),
            fallback=dict(DEFAULT_QUESTION_VIEWPORTS),
        )

        screenshot_question_ids = set(
            _parse_csv_list(
                _coalesce(
                    args.screenshot_question_ids,
                    os.getenv("SCREENSHOT_QUESTION_IDS"),
                    ",".join(sorted(DEFAULT_SCREENSHOT_QUESTION_IDS)),
                )
            )
            or []
        )

        publish_api_url = _coalesce(args.publish_api_url, os.getenv("PUBLISH_API_URL"), None)
        publish_api_token = _coalesce(args.publish_api_token, os.getenv("PUBLISH_API_TOKEN"), None)
        publish_timeout_seconds = int(
            _coalesce(args.publish_timeout_seconds, os.getenv("PUBLISH_TIMEOUT_SECONDS"), 30)
        )

        s3_upload_enabled = _to_bool(_coalesce(args.s3_upload_enabled, os.getenv("S3_UPLOAD_ENABLED"), "false"))
        s3_endpoint_url = _coalesce(args.s3_endpoint_url, os.getenv("S3_ENDPOINT_URL"), None)
        s3_bucket = _coalesce(args.s3_bucket, os.getenv("S3_BUCKET"), None)
        s3_region = _coalesce(args.s3_region, os.getenv("AWS_REGION"), "us-east-1")
        s3_access_key_id = _coalesce(args.s3_access_key_id, os.getenv("AWS_ACCESS_KEY_ID"), None)
        s3_secret_access_key = _coalesce(args.s3_secret_access_key, os.getenv("AWS_SECRET_ACCESS_KEY"), None)
        s3_session_token = _coalesce(args.s3_session_token, os.getenv("AWS_SESSION_TOKEN"), None)
        s3_key_prefix = _coalesce(args.s3_key_prefix, os.getenv("S3_KEY_PREFIX"), "playwright-traces")
        s3_method = _coalesce(args.s3_method, os.getenv("S3_UPLOAD_METHOD"), "POST").upper()
        if s3_method not in {"PUT", "POST"}:
            s3_method = "POST"

        return cls(
            run_id=run_id,
            provider=provider,
            model=model,
            manual_list_dir=manual_list_dir,
            output_dir=output_dir,
            output_file=output_file,
            url=url,
            html_file=html_file,
            screenshot_files=screenshot_files,
            question_ids=question_ids,
            capture_browser=capture_browser,
            headless=headless,
            wait_until=wait_until,
            navigation_timeout_ms=navigation_timeout_ms,
            post_load_wait_ms=post_load_wait_ms,
            viewport_settle_ms=viewport_settle_ms,
            llm_timeout_seconds=llm_timeout_seconds,
            html_max_chars=html_max_chars,
            include_raw_response=include_raw_response,
            include_prompt_in_output=include_prompt_in_output,
            automatic_behavior_question_id=automatic_behavior_question_id,
            automatic_behavior_timeseries_enabled=automatic_behavior_timeseries_enabled,
            automatic_behavior_interval_ms=automatic_behavior_interval_ms,
            automatic_behavior_duration_ms=automatic_behavior_duration_ms,
            otel_logging_enabled=otel_logging_enabled,
            otel_collector_url=otel_collector_url,
            otel_service_name=otel_service_name,
            otel_resource_attributes=otel_resource_attributes,
            otel_headers=otel_headers,
            otel_flush_on_each_log=otel_flush_on_each_log,
            otel_timeout_seconds=otel_timeout_seconds,
            default_viewports=default_viewports,
            question_viewports=question_viewports,
            screenshot_question_ids=screenshot_question_ids,
            publish_api_url=publish_api_url,
            publish_api_token=publish_api_token,
            publish_timeout_seconds=publish_timeout_seconds,
            s3_upload_enabled=s3_upload_enabled,
            s3_endpoint_url=s3_endpoint_url,
            s3_bucket=s3_bucket,
            s3_region=s3_region,
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
            s3_session_token=s3_session_token,
            s3_key_prefix=s3_key_prefix,
            s3_method=s3_method,
        )


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue
        return value
    return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv_list(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [part.strip() for part in value.split(",") if part.strip()]
    return parts or None


def _parse_viewports(raw_json: str | None, fallback: list[Viewport]) -> list[Viewport]:
    if not raw_json:
        return fallback

    data = json.loads(raw_json)
    result: list[Viewport] = []
    for item in data:
        result.append(
            Viewport(
                name=str(item.get("name", f"vp-{len(result) + 1}")),
                width=int(item["width"]),
                height=int(item["height"]),
            )
        )

    return result if result else fallback


def _parse_question_viewports(
    raw_json: str | None,
    fallback: dict[str, list[Viewport]],
) -> dict[str, list[Viewport]]:
    if not raw_json:
        return fallback

    data = json.loads(raw_json)
    parsed: dict[str, list[Viewport]] = {}
    for question_id, viewport_data in data.items():
        parsed[question_id] = _parse_viewports(json.dumps(viewport_data), fallback=[])

    return parsed if parsed else fallback


def _parse_json_object(raw_json: str | None) -> dict[str, str]:
    if not raw_json:
        return {}
    parsed = json.loads(raw_json)
    if not isinstance(parsed, dict):
        raise ValueError("Expected JSON object")
    return {str(k): str(v) for k, v in parsed.items()}
