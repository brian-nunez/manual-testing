from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int

    @property
    def key(self) -> str:
        return f"{self.name}_{self.width}x{self.height}"


@dataclass(frozen=True)
class ManualQuestion:
    question_id: str
    title: str
    body_markdown: str
    source_path: Path


@dataclass
class Decision:
    needs_manual_testing: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "needs_manual_testing": self.needs_manual_testing,
            "reason": self.reason,
        }


@dataclass
class QuestionResult:
    question_id: str
    title: str
    decision: Decision
    prompt: str | None = None
    raw_response: str | None = None
    screenshots: list[str] = field(default_factory=list)
    structured_evidence: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "title": self.title,
            "decision": self.decision.to_dict(),
            "screenshots": self.screenshots,
            "structured_evidence": self.structured_evidence,
            "error": self.error,
            "raw_response": self.raw_response,
            "prompt": self.prompt,
        }


@dataclass
class BrowserArtifacts:
    final_url: str
    html: str | None
    screenshots_by_question: dict[str, list[Path]]
    trace_path: Path | None


@dataclass
class RunOutput:
    run_id: str
    provider: str
    model: str
    url: str | None
    results: list[QuestionResult]
    trace_path: str | None
    trace_upload_url: str | None
    publish_status: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        total = len(self.results)
        must_test = sum(1 for r in self.results if r.decision.needs_manual_testing)
        errors = sum(1 for r in self.results if r.error)

        return {
            "run_id": self.run_id,
            "provider": self.provider,
            "model": self.model,
            "url": self.url,
            "summary": {
                "total_questions": total,
                "needs_manual_testing": must_test,
                "skippable_questions": total - must_test,
                "errors": errors,
            },
            "artifacts": {
                "trace_path": self.trace_path,
                "trace_upload_url": self.trace_upload_url,
            },
            "publish_status": self.publish_status,
            "results": [result.to_dict() for result in self.results],
        }
