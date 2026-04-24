from __future__ import annotations

from manual_testing.models import ManualQuestion
from manual_testing.question_prompts import get_question_prompt


def build_prompt(
    question: ManualQuestion,
    *,
    url: str | None,
) -> str:
    question_specific_prompt = get_question_prompt(question.question_id)

    return f"""You are an accessibility manual-testing triage assistant.

Test metadata:
- Manual test id: {question.question_id}
- Manual test title: {question.title}
- Page URL: {url or "No URL provided"}

Task:
- Decide whether this specific manual test should be run for this page.
- Provide a concise reason grounded in available evidence.

Evidence policy:
- Deterministic structured evidence, HTML, and screenshots are provided as separate user content objects.
- Treat deterministic structured evidence as high-confidence extracted facts.
- Some test-specific text may mention relevance/applicability. Treat that as internal reasoning only.
- Final output must NOT include a `relevant` field.

Test-specific evaluation prompt:
{question_specific_prompt}

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
