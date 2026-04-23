from __future__ import annotations

import json

from manual_testing.models import Decision


class DecisionParseError(ValueError):
    pass


def parse_decision_response(raw_text: str) -> Decision:
    payload = _extract_json_payload(raw_text)

    needs_manual_testing = payload.get("needs_manual_testing")
    reason = payload.get("reason")

    if not isinstance(needs_manual_testing, bool):
        raise DecisionParseError("Field 'needs_manual_testing' must be boolean")
    if not isinstance(reason, str):
        raise DecisionParseError("Field 'reason' must be string")

    normalized_reason = " ".join(reason.strip().split())
    if not normalized_reason:
        normalized_reason = "No reason returned by model."

    return Decision(
        needs_manual_testing=needs_manual_testing,
        reason=normalized_reason,
    )


def decision_fallback(reason: str) -> Decision:
    return Decision(
        needs_manual_testing=False,
        reason=reason,
    )


def _extract_json_payload(raw_text: str) -> dict:
    text = raw_text.strip()
    if not text:
        raise DecisionParseError("LLM response was empty")

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    maybe_object = _find_first_json_object(text)
    if not maybe_object:
        raise DecisionParseError("No JSON object found in LLM response")

    try:
        parsed = json.loads(maybe_object)
    except json.JSONDecodeError as exc:
        raise DecisionParseError(f"Invalid JSON object in LLM response: {exc}") from exc

    if not isinstance(parsed, dict):
        raise DecisionParseError("Top-level JSON is not an object")

    return parsed


def _find_first_json_object(text: str) -> str | None:
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(text)):
            char = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

        start = text.find("{", start + 1)

    return None
