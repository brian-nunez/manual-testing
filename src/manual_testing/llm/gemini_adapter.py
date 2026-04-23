from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import encode_image_to_base64, mime_type_for, post_json


class GeminiAdapter(LLMAdapter):
    name = "gemini"

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for the Gemini adapter")

        self.api_key = api_key
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> str:
        parts: list[dict] = [{"text": prompt}]
        for image_path in image_paths:
            parts.append(
                {
                    "inlineData": {
                        "mimeType": mime_type_for(image_path),
                        "data": encode_image_to_base64(image_path),
                    }
                }
            )

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }

        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        response = post_json(url, payload, headers={}, timeout_seconds=timeout_seconds)

        candidates = response.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"No candidates returned by Gemini: {response}")

        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
        merged = "\n".join(part for part in text_parts if part)

        if not merged:
            raise RuntimeError(f"Gemini returned no text output: {response}")

        return merged


def build_gemini_adapter() -> GeminiAdapter:
    return GeminiAdapter(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )
