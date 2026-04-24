from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import request_json


class InstancesAPIAdapter(LLMAdapter):
    name = "instances_api"

    def __init__(
        self,
        *,
        endpoint_url: str,
        api_key: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 10000,
        top_p: float = 0.3,
        top_k: int = 8,
    ) -> None:
        endpoint = endpoint_url.strip()
        if not endpoint:
            raise ValueError("INSTANCES_API_URL is required for the instances_api adapter")

        self.endpoint_url = endpoint
        self.api_key = (api_key or "").strip()
        self.system_prompt = (system_prompt or "Return only strict JSON.").strip()
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.top_p = float(top_p)
        self.top_k = int(top_k)

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> str:
        payload = {
            "instances": [
                {
                    "messages": [
                        {
                            "content": self.system_prompt,
                            "role": "system",
                        },
                        {
                            "content": prompt,
                            "role": "user",
                        },
                    ],
                    "model": model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "top_k": self.top_k,
                }
            ]
        }

        headers = self._headers()
        response = request_json(
            self.endpoint_url,
            method="POST",
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected instances API response type: {type(response).__name__}")

        message_content = _extract_message_content(response)
        if message_content is None:
            raise RuntimeError(f"Unexpected instances API response body: {_safe_repr(response)}")

        if isinstance(message_content, str):
            return message_content
        return json.dumps(message_content)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}


def _extract_message_content(response: dict[str, Any]) -> str | dict[str, Any] | None:
    predictions = response.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        return None

    first_prediction = predictions[0]
    if not isinstance(first_prediction, dict):
        return None

    choices = first_prediction.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, dict):
        return content
    return None


def _safe_repr(value: Any, max_len: int = 1800) -> str:
    try:
        rendered = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        rendered = repr(value)
    if len(rendered) <= max_len:
        return rendered
    return rendered[:max_len] + "...(truncated)"


def build_instances_api_adapter() -> InstancesAPIAdapter:
    return InstancesAPIAdapter(
        endpoint_url=os.getenv("INSTANCES_API_URL", ""),
        api_key=os.getenv("INSTANCES_API_KEY"),
        system_prompt=os.getenv("INSTANCES_API_SYSTEM_PROMPT"),
        temperature=float(os.getenv("INSTANCES_API_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("INSTANCES_API_MAX_TOKENS", "10000")),
        top_p=float(os.getenv("INSTANCES_API_TOP_P", "0.3")),
        top_k=int(os.getenv("INSTANCES_API_TOP_K", "8")),
    )
