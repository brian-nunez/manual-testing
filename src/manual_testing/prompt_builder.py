from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manual_testing.models import ManualQuestion
from manual_testing.question_prompts import get_question_prompt


def build_prompt(
    question: ManualQuestion,
    *,
    url: str | None,
    html: str | None,
    screenshot_paths: list[Path],
    html_max_chars: int,
    structured_evidence: dict[str, Any] | None = None,
) -> str:
    html_excerpt = (html or "No HTML was provided.").strip()
    if len(html_excerpt) > html_max_chars:
        html_excerpt = html_excerpt[:html_max_chars]

    screenshot_text = "\n".join(f"- {path.name}" for path in screenshot_paths) or "- No screenshots provided"
    question_specific_prompt = get_question_prompt(question.question_id)
    structured_evidence_text = (
        json.dumps(structured_evidence, indent=2)
        if structured_evidence is not None
        else "None"
    )

    return f"""You are an accessibility manual-testing triage assistant.

Test metadata:
- Manual test id: {question.question_id}
- Manual test title: {question.title}
- Page URL: {url or "No URL provided"}

Task:
- Decide whether this specific manual test should be run for this page.
- Provide a concise reason grounded in available evidence.

Evidence policy:
- If deterministic structured evidence is provided, treat it as high-confidence extracted facts.
- Combine deterministic evidence with HTML and screenshots to make the final decision.
- Some test-specific text may mention the concept of relevance/applicability. Treat that as internal reasoning only.
- Final output must NOT include a `relevant` field.

Test-specific evaluation prompt:
{question_specific_prompt}

Deterministic structured evidence:
{structured_evidence_text}

Available screenshot artifacts:
{screenshot_text}

HTML snapshot (may be truncated):
{html_excerpt}

STRICT OUTPUT INSTRUCTIONS:
- Return ONLY valid JSON.
- Do not include markdown, comments, or extra keys.
- Do not wrap the JSON in code fences.
- Output must be parseable with JSON.parse.

Return exactly:
{{
  "needs_manual_testing": boolean,
  "reason": string
}}"""
