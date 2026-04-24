from __future__ import annotations

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.instances_api_adapter import build_instances_api_adapter


def build_adapter(provider: str) -> LLMAdapter:
    normalized = provider.lower().strip()
    if normalized == "instances_api":
        return build_instances_api_adapter()

    raise ValueError("Unsupported provider. Only 'instances_api' is supported.")
