from __future__ import annotations

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.codex_adapter import build_codex_adapter
from manual_testing.llm.gemini_adapter import build_gemini_adapter
from manual_testing.llm.llama_adapter import build_llama_adapter
from manual_testing.llm.ollama_adapter import build_ollama_adapter


def build_adapter(provider: str) -> LLMAdapter:
    normalized = provider.lower().strip()

    if normalized == "codex":
        return build_codex_adapter()
    if normalized == "gemini":
        return build_gemini_adapter()
    if normalized == "llama":
        return build_llama_adapter()
    if normalized == "ollama":
        return build_ollama_adapter()

    supported = "codex, gemini, llama, ollama"
    raise ValueError(f"Unsupported provider '{provider}'. Supported: {supported}")
