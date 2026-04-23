from __future__ import annotations

from pathlib import Path
from typing import Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import LLMHTTPError, encode_image_to_base64, mime_type_for, post_json


class OpenAICompatibleAdapter(LLMAdapter):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        api_key: str | None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.extra_headers = extra_headers or {}

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> str:
        headers = dict(self.extra_headers)
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        user_content: list[dict] = [{"type": "text", "text": prompt}]
        for image_path in image_paths:
            mime = mime_type_for(image_path)
            b64 = encode_image_to_base64(image_path)
            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"},
                }
            )

        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return only strict JSON."},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
        }

        url = f"{self.base_url}/chat/completions"

        try:
            response = post_json(url, payload, headers=headers, timeout_seconds=timeout_seconds)
        except LLMHTTPError as exc:
            if "response_format" not in str(exc):
                raise

            payload.pop("response_format", None)
            response = post_json(url, payload, headers=headers, timeout_seconds=timeout_seconds)

        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError(f"No choices returned by {self.name} adapter")

        message = choices[0].get("message") or {}
        content = message.get("content")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            joined = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    joined.append(part.get("text", ""))
            if joined:
                return "\n".join(joined)

        raise RuntimeError(f"Unexpected response content from {self.name}: {message}")
