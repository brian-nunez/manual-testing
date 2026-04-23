from __future__ import annotations

from pathlib import Path

from manual_testing.models import ManualQuestion


def build_prompt(
    question: ManualQuestion,
    *,
    url: str | None,
    html: str | None,
    screenshot_paths: list[Path],
    html_max_chars: int,
) -> str:
    html_excerpt = (html or "No HTML was provided.").strip()
    if len(html_excerpt) > html_max_chars:
        html_excerpt = html_excerpt[:html_max_chars]

    screenshot_text = "\n".join(f"- {path.name}" for path in screenshot_paths) or "- No screenshots provided"

    return f"""You are an accessibility manual-testing triage assistant.

Goal:
- Decide whether the user SHOULD run this manual test for the current page.
- Decide whether the test is relevant to the current page state.
- Explain the reason with concrete evidence from the provided inputs.

Manual test identifier: {question.question_id}
Manual test title: {question.title}
Page URL: {url or "No URL provided"}

Manual Test Definition (authoritative):
{question.body_markdown}

Decision rules:
1) `relevant` is true only when this page appears to include the type of content, interaction, or condition targeted by this manual test.
2) `needs_manual_testing` is true when the test is relevant AND a manual/human validation step is still required to verify WCAG behavior.
3) If the test is clearly not relevant, set both `relevant=false` and `needs_manual_testing=false`.
4) Use conservative reasoning; do not assume missing evidence.
5) Keep `reason` concise and specific.

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
  "relevant": boolean,
  "reason": string
}}"""
