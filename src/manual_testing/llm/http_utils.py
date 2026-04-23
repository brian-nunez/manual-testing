from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMHTTPError(RuntimeError):
    pass


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    response = request_json(
        url,
        method="POST",
        payload=payload,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    if not isinstance(response, dict):
        raise LLMHTTPError(f"Expected JSON object response from {url}, got: {type(response).__name__}")
    return response


def request_json(
    url: str,
    *,
    method: str,
    headers: dict[str, str],
    timeout_seconds: int,
    payload: dict[str, Any] | None = None,
) -> Any:
    method_normalized = method.strip().upper()
    data = None
    merged_headers = dict(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        merged_headers = {"Content-Type": "application/json", **merged_headers}

    request = Request(url=url, data=data, headers=merged_headers, method=method_normalized)

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LLMHTTPError(f"{exc.code} {exc.reason}: {body}") from exc
    except URLError as exc:
        raise LLMHTTPError(f"Network error calling {url}: {exc}") from exc

    if not body.strip():
        return {}

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise LLMHTTPError(f"Expected JSON response from {url}, got: {body[:500]}") from exc

    return parsed


def encode_image_to_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def mime_type_for(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "application/octet-stream"
