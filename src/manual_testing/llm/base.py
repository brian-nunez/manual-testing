from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
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
    ) -> str:
        raise NotImplementedError
