from __future__ import annotations

import os

from manual_testing.llm.openai_compatible import OpenAICompatibleAdapter


def build_llama_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        name="llama",
        base_url=os.getenv("LLAMA_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.getenv("LLAMA_API_KEY"),
    )
