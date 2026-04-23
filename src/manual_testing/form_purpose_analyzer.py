from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser as StdHTMLParser
from typing import Any

try:
    from selectolax.parser import HTMLParser as SelectolaxHTMLParser
except ModuleNotFoundError:  # pragma: no cover
    SelectolaxHTMLParser = None


INPUT_PURPOSE_TOKENS = {
    "name",
    "honorific-prefix",
    "given-name",
    "additional-name",
    "family-name",
    "honorific-suffix",
    "nickname",
    "organization-title",
    "username",
    "new-password",
    "current-password",
    "organization",
    "street-address",
    "address-line1",
    "address-line2",
    "address-line3",
    "address-level4",
    "address-level3",
    "address-level2",
    "address-level1",
    "country",
    "country-name",
    "postal-code",
    "cc-name",
    "cc-given-name",
    "cc-additional-name",
    "cc-family-name",
    "cc-number",
    "cc-exp",
    "cc-exp-month",
    "cc-exp-year",
    "cc-csc",
    "cc-type",
    "transaction-currency",
    "transaction-amount",
    "language",
    "bday",
    "bday-day",
    "bday-month",
    "bday-year",
    "sex",
    "url",
    "photo",
    "tel",
    "tel-country-code",
    "tel-national",
    "tel-area-code",
    "tel-local",
    "tel-local-prefix",
    "tel-local-suffix",
    "tel-extension",
    "email",
    "impp",
}

_IGNORE_INPUT_TYPES = {"hidden", "submit", "button", "reset", "image", "file"}

_PURPOSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b(email|e-mail)\b")),
    ("tel", re.compile(r"\b(phone|telephone|mobile|tel)\b")),
    ("current-password", re.compile(r"\b(current[_\s-]?password|password)\b")),
    ("new-password", re.compile(r"\b(new[_\s-]?password|create[_\s-]?password|confirm[_\s-]?password)\b")),
    ("username", re.compile(r"\b(username|user[_\s-]?name|login)\b")),
    ("given-name", re.compile(r"\b(first[_\s-]?name|given[_\s-]?name)\b")),
    ("family-name", re.compile(r"\b(last[_\s-]?name|family[_\s-]?name|surname)\b")),
    ("name", re.compile(r"\b(full[_\s-]?name|your[_\s-]?name|name)\b")),
    ("street-address", re.compile(r"\b(street|address)\b")),
    ("address-line1", re.compile(r"\b(address[_\s-]?line[_\s-]?1|address1)\b")),
    ("address-line2", re.compile(r"\b(address[_\s-]?line[_\s-]?2|address2|apt|suite|unit)\b")),
    ("address-level2", re.compile(r"\b(city|town|locality)\b")),
    ("address-level1", re.compile(r"\b(state|province|region)\b")),
    ("postal-code", re.compile(r"\b(zip|postal|postcode)\b")),
    ("country", re.compile(r"\b(country)\b")),
    ("organization", re.compile(r"\b(company|organization|organisation|employer)\b")),
    ("organization-title", re.compile(r"\b(job[_\s-]?title|title|role)\b")),
    ("cc-number", re.compile(r"\b(card[_\s-]?number|credit[_\s-]?card|cc[_\s-]?number)\b")),
    ("cc-name", re.compile(r"\b(name[_\s-]?on[_\s-]?card)\b")),
    ("cc-exp", re.compile(r"\b(expiration|expiry|exp[_\s-]?date)\b")),
    ("cc-exp-month", re.compile(r"\b(exp[_\s-]?month)\b")),
    ("cc-exp-year", re.compile(r"\b(exp[_\s-]?year)\b")),
    ("cc-csc", re.compile(r"\b(cvc|cvv|csc|security[_\s-]?code)\b")),
    ("bday", re.compile(r"\b(birthday|date[_\s-]?of[_\s-]?birth|dob)\b")),
    ("url", re.compile(r"\b(website|url|homepage)\b")),
]


@dataclass
class FormPurposeAnalysis:
    summary: dict[str, Any]
    fields: list[dict[str, Any]]
    parser: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "fields": self.fields,
            "parser": self.parser,
            "warnings": self.warnings,
        }


def analyze_input_purposes(html: str) -> FormPurposeAnalysis:
    if not html.strip():
        return FormPurposeAnalysis(
            summary=_empty_summary(),
            fields=[],
            parser="selectolax",
            warnings=["Empty HTML input"],
        )

    if SelectolaxHTMLParser is not None:
        parsed_fields = _extract_fields_with_selectolax(html)
        parser_name = "selectolax"
        warnings: list[str] = []
    else:
        parsed_fields = _extract_fields_with_stdlib(html)
        parser_name = "stdlib_html_parser"
        warnings = ["selectolax is not installed; using stdlib HTML parser fallback."]

    fields = _evaluate_fields(parsed_fields)

    user_fields = [f for f in fields if f["is_user_data_field"]]
    scoped_fields = [f for f in user_fields if f["in_wcag_input_purposes"]]
    missing_autocomplete = [f for f in scoped_fields if f["issue"] == "missing_autocomplete"]
    mismatched_autocomplete = [f for f in scoped_fields if f["issue"] == "autocomplete_mismatch"]

    summary = {
        "total_fields": len(fields),
        "user_info_field_count": len(user_fields),
        "wcag_input_purpose_field_count": len(scoped_fields),
        "fields_missing_autocomplete_count": len(missing_autocomplete),
        "fields_mismatched_autocomplete_count": len(mismatched_autocomplete),
        "relevant_recommendation": len(user_fields) > 0,
        "needs_manual_testing_recommendation": len(user_fields) > 0,
        "recommendation_reason": _build_recommendation_reason(
            user_field_count=len(user_fields),
            scoped_field_count=len(scoped_fields),
            missing_count=len(missing_autocomplete),
            mismatch_count=len(mismatched_autocomplete),
        ),
    }

    return FormPurposeAnalysis(
        summary=summary,
        fields=fields,
        parser=parser_name,
        warnings=warnings,
    )


def _build_label_map(tree: SelectolaxHTMLParser) -> dict[str, str]:
    label_map: dict[str, str] = {}
    for label in tree.css("label"):
        text = " ".join((label.text(separator=" ", strip=True) or "").split())
        if not text:
            continue
        target_id = (label.attributes.get("for", "") or "").strip()
        if target_id:
            label_map[target_id] = text
            continue

        child = label.css_first("input, select, textarea")
        if child:
            child_id = (child.attributes.get("id", "") or "").strip()
            if child_id:
                label_map[child_id] = text
    return label_map


def _extract_fields_with_selectolax(html: str) -> list[dict[str, Any]]:
    tree = SelectolaxHTMLParser(html)
    label_by_for = _build_label_map(tree)
    parsed_fields: list[dict[str, Any]] = []
    for idx, node in enumerate(tree.css("input, select, textarea"), start=1):
        attrs = node.attributes
        field_id = (attrs.get("id", "") or "").strip()
        parsed_fields.append(
            {
                "index": idx,
                "tag": node.tag.lower(),
                "type": (attrs.get("type", "") or "").strip().lower(),
                "name": (attrs.get("name", "") or "").strip(),
                "id": field_id,
                "label": label_by_for.get(field_id, "") if field_id else "",
                "aria_label": (attrs.get("aria-label", "") or "").strip(),
                "placeholder": (attrs.get("placeholder", "") or "").strip(),
                "autocomplete_raw": (attrs.get("autocomplete", "") or "").strip(),
            }
        )
    return parsed_fields


class _StdFieldParser(StdHTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fields: list[dict[str, Any]] = []
        self.labels_by_for: dict[str, str] = {}
        self._label_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): (value or "") for name, value in attrs}
        tag = tag.lower()

        if tag == "label":
            self._label_stack.append(
                {
                    "for": (attr_map.get("for", "") or "").strip(),
                    "text_parts": [],
                    "fields": [],
                }
            )
            return

        if tag not in {"input", "select", "textarea"}:
            return

        field = {
            "tag": tag,
            "type": (attr_map.get("type", "") or "").strip().lower(),
            "name": (attr_map.get("name", "") or "").strip(),
            "id": (attr_map.get("id", "") or "").strip(),
            "label": "",
            "aria_label": (attr_map.get("aria-label", "") or "").strip(),
            "placeholder": (attr_map.get("placeholder", "") or "").strip(),
            "autocomplete_raw": (attr_map.get("autocomplete", "") or "").strip(),
        }
        self.fields.append(field)
        if self._label_stack:
            self._label_stack[-1]["fields"].append(field)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "label" or not self._label_stack:
            return
        label_info = self._label_stack.pop()
        text = " ".join(" ".join(label_info["text_parts"]).split())
        target_id = label_info["for"]
        if target_id and text:
            self.labels_by_for[target_id] = text
            return
        if text:
            for field in label_info["fields"]:
                if not field["label"]:
                    field["label"] = text

    def handle_data(self, data: str) -> None:
        if self._label_stack and data.strip():
            self._label_stack[-1]["text_parts"].append(data.strip())


def _extract_fields_with_stdlib(html: str) -> list[dict[str, Any]]:
    parser = _StdFieldParser()
    parser.feed(html)
    parser.close()

    parsed_fields: list[dict[str, Any]] = []
    for idx, field in enumerate(parser.fields, start=1):
        field_copy = dict(field)
        field_id = field_copy.get("id", "")
        if field_id and not field_copy.get("label"):
            field_copy["label"] = parser.labels_by_for.get(field_id, "")
        field_copy["index"] = idx
        parsed_fields.append(field_copy)
    return parsed_fields


def _evaluate_fields(parsed_fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for field in parsed_fields:
        tag = field["tag"]
        input_type = (field.get("type") or "").strip().lower()
        if tag == "input" and input_type in _IGNORE_INPUT_TYPES:
            continue

        autocomplete_value = (field.get("autocomplete_raw") or "").strip()
        autocomplete_token = _extract_autocomplete_token(autocomplete_value)

        field_id = (field.get("id") or "").strip()
        label_text = (field.get("label") or "").strip()
        aria_label = (field.get("aria_label") or "").strip()
        placeholder = (field.get("placeholder") or "").strip()
        name = (field.get("name") or "").strip()

        inferred_purpose = _infer_purpose(
            autocomplete_token=autocomplete_token,
            tag=tag,
            input_type=input_type,
            name=name,
            field_id=field_id,
            label_text=label_text,
            aria_label=aria_label,
            placeholder=placeholder,
        )
        is_user_data_field = inferred_purpose is not None
        in_wcag_purpose_list = inferred_purpose in INPUT_PURPOSE_TOKENS if inferred_purpose else False
        autocomplete_present = bool(autocomplete_value)
        autocomplete_matches = (
            bool(autocomplete_token and inferred_purpose and autocomplete_token == inferred_purpose)
            if is_user_data_field
            else None
        )

        issue = None
        if is_user_data_field and in_wcag_purpose_list:
            if not autocomplete_present:
                issue = "missing_autocomplete"
            elif autocomplete_matches is False:
                issue = "autocomplete_mismatch"

        fields.append(
            {
                "index": field.get("index"),
                "tag": tag,
                "type": input_type or None,
                "name": name or None,
                "id": field_id or None,
                "label": label_text or None,
                "aria_label": aria_label or None,
                "placeholder": placeholder or None,
                "autocomplete_raw": autocomplete_value or None,
                "autocomplete_token": autocomplete_token,
                "inferred_purpose": inferred_purpose,
                "in_wcag_input_purposes": in_wcag_purpose_list,
                "is_user_data_field": is_user_data_field,
                "autocomplete_present": autocomplete_present,
                "autocomplete_matches_inferred_purpose": autocomplete_matches,
                "issue": issue,
            }
        )
    return fields


def _extract_autocomplete_token(value: str) -> str | None:
    if not value:
        return None
    parts = [part.strip().lower() for part in value.split() if part.strip()]
    if not parts:
        return None

    for part in reversed(parts):
        if part in INPUT_PURPOSE_TOKENS:
            return part
    return None


def _infer_purpose(
    *,
    autocomplete_token: str | None,
    tag: str,
    input_type: str,
    name: str,
    field_id: str,
    label_text: str,
    aria_label: str,
    placeholder: str,
) -> str | None:
    if autocomplete_token in INPUT_PURPOSE_TOKENS:
        return autocomplete_token

    if input_type == "email":
        return "email"
    if input_type == "tel":
        return "tel"
    if input_type == "url":
        return "url"
    if input_type == "password":
        return "current-password"

    haystack = " ".join(
        part
        for part in [name, field_id, label_text, aria_label, placeholder]
        if part
    ).lower()
    if not haystack:
        return None

    for token, pattern in _PURPOSE_PATTERNS:
        if pattern.search(haystack):
            return token

    return None


def _empty_summary() -> dict[str, Any]:
    return {
        "total_fields": 0,
        "user_info_field_count": 0,
        "wcag_input_purpose_field_count": 0,
        "fields_missing_autocomplete_count": 0,
        "fields_mismatched_autocomplete_count": 0,
        "relevant_recommendation": False,
        "needs_manual_testing_recommendation": False,
        "recommendation_reason": "No form fields detected.",
    }


def _build_recommendation_reason(
    *,
    user_field_count: int,
    scoped_field_count: int,
    missing_count: int,
    mismatch_count: int,
) -> str:
    if user_field_count == 0:
        return "No user-information fields detected."
    if scoped_field_count == 0:
        return "User-information fields detected, but none confidently mapped to WCAG input-purpose tokens."
    if missing_count > 0 or mismatch_count > 0:
        return (
            f"Detected {scoped_field_count} WCAG-mappable user fields; "
            f"{missing_count} missing autocomplete and {mismatch_count} with potential token mismatch."
        )
    return (
        f"Detected {scoped_field_count} WCAG-mappable user fields with autocomplete tokens present; "
        "manual verification still recommended for purpose/token correctness."
    )
