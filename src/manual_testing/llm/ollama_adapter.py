from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import encode_image_to_base64, post_json


class OllamaAdapter(LLMAdapter):
    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "images": [encode_image_to_base64(path) for path in image_paths],
            "options": {"temperature": 0},
        }

        response = post_json(
            f"{self.base_url}/api/generate",
            payload,
            headers={},
            timeout_seconds=timeout_seconds,
        )

        text = response.get("response")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"Unexpected Ollama response: {response}")

        return text


def build_ollama_adapter() -> OllamaAdapter:
    return OllamaAdapter(base_url=os.getenv("OLLAMA_BASE_URL"))
