from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from typing import Sequence


class LLMAdapter(ABC):
    name: str

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
        html: str | None = None,
        structured_evidence: dict[str, Any] | None = None,
        url: str | None = None,
        question_id: str | None = None,
        question_title: str | None = None,
    ) -> str:
        raise NotImplementedError
