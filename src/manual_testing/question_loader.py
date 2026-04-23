from __future__ import annotations

import re
from pathlib import Path

from manual_testing.models import ManualQuestion


_TITLE_RE = re.compile(r"^###\s+(?P<title>.+?)\s*$", flags=re.MULTILINE)
_DIGIT_RE = re.compile(r"(\d+)")


def load_manual_questions(manual_list_dir: Path, question_ids: list[str] | None = None) -> list[ManualQuestion]:
    if not manual_list_dir.exists() or not manual_list_dir.is_dir():
        raise FileNotFoundError(f"Manual list directory not found: {manual_list_dir}")

    allowed = set(question_ids or [])
    questions: list[ManualQuestion] = []

    for path in sorted(manual_list_dir.glob("*.md"), key=_sort_key):
        question_id = path.stem
        if allowed and question_id not in allowed:
            continue

        content = path.read_text(encoding="utf-8").strip()
        title_match = _TITLE_RE.search(content)
        title = title_match.group("title") if title_match else question_id

        questions.append(
            ManualQuestion(
                question_id=question_id,
                title=title,
                body_markdown=content,
                source_path=path,
            )
        )

    if not questions:
        raise ValueError("No manual questions found. Check MANUAL_LIST_DIR / QUESTION_IDS settings.")

    return questions


def _sort_key(path: Path) -> tuple[int, str]:
    match = _DIGIT_RE.search(path.stem)
    number = int(match.group(1)) if match else 10**9
    return number, path.stem
