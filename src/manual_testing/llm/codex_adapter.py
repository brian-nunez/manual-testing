from __future__ import annotations

import os

from manual_testing.llm.openai_compatible import OpenAICompatibleAdapter


def build_codex_adapter() -> OpenAICompatibleAdapter:
    return OpenAICompatibleAdapter(
        name="codex",
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
