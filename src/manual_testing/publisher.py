from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class PublishError(RuntimeError):
    pass


def publish_results(
    payload: dict[str, Any],
    *,
    url: str,
    token: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url=url, data=body, headers=headers, method="POST")

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            text = response.read().decode("utf-8", errors="replace")
            status = int(response.status)
    except HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise PublishError(f"Publish API returned {exc.code} {exc.reason}: {error_text}") from exc
    except URLError as exc:
        raise PublishError(f"Failed to publish to API: {exc}") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"raw": text}

    return {"status_code": status, "response": parsed}
