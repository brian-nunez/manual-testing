from __future__ import annotations

import base64
import json
import os
import uuid
from pathlib import Path
from typing import Any, Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import LLMHTTPError, encode_image_to_base64, mime_type_for, request_json


_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "needs_manual_testing": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["needs_manual_testing", "reason"],
    "additionalProperties": False,
}


class OpencodeAdapter(LLMAdapter):
    name = "opencode"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        provider_id: str | None = None,
        keep_sessions: bool = False,
    ) -> None:
        self.base_url = (base_url or "http://127.0.0.1:4096").rstrip("/")
        self.username = (username or "opencode").strip() or "opencode"
        self.password = (password or "").strip()
        self.provider_id = (provider_id or "").strip()
        self.keep_sessions = keep_sessions

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> str:
        session_id = self._create_session(timeout_seconds=timeout_seconds)
        try:
            response = self._send_message_with_fallbacks(
                session_id=session_id,
                prompt=prompt,
                model=model,
                image_paths=image_paths,
                timeout_seconds=timeout_seconds,
            )
            structured_output = _extract_structured_output(response)
            if structured_output is not None:
                return json.dumps(structured_output)

            text = _extract_text_response(response)
            if not text:
                raise RuntimeError(f"Unexpected OpenCode message response: {response}")
            return text
        finally:
            if self.keep_sessions:
                return
            self._delete_session(session_id=session_id, timeout_seconds=timeout_seconds)

    def _send_message_with_fallbacks(
        self,
        *,
        session_id: str,
        prompt: str,
        model: str,
        image_paths: Sequence[Path],
        timeout_seconds: int,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        for payload in self._message_payload_variants(prompt=prompt, model=model, image_paths=image_paths):
            try:
                response = request_json(
                    f"{self.base_url}/session/{session_id}/message",
                    method="POST",
                    payload=payload,
                    headers=self._headers(),
                    timeout_seconds=timeout_seconds,
                )
                if isinstance(response, dict):
                    return response
                raise RuntimeError(f"Unexpected OpenCode API response type: {type(response).__name__}")
            except (LLMHTTPError, RuntimeError) as exc:
                last_error = exc

        if last_error:
            raise RuntimeError(f"OpenCode request failed after retries: {last_error}") from last_error
        raise RuntimeError("OpenCode request failed without a captured error")

    def _message_payload_variants(
        self,
        *,
        prompt: str,
        model: str,
        image_paths: Sequence[Path],
    ) -> list[dict[str, Any]]:
        text_only_parts = [{"type": "text", "text": prompt}]
        image_parts = [_build_image_part(path) for path in image_paths]
        parts_with_images = text_only_parts + image_parts if image_parts else text_only_parts

        model_variants: list[Any] = [_build_model_spec(model=model, provider_id=self.provider_id)]
        if "/" in model:
            model_variants.append(model)

        variants: list[dict[str, Any]] = []
        for model_value in model_variants:
            # Preferred: rich parts + enforced JSON schema output.
            variants.append(
                {
                    "model": model_value,
                    "parts": parts_with_images,
                    "format": {
                        "type": "json_schema",
                        "schema": _DECISION_SCHEMA,
                    },
                }
            )
            # Fallback: rich parts without format in case server version does not support it.
            variants.append({"model": model_value, "parts": parts_with_images})
            if parts_with_images != text_only_parts:
                # Final fallback for stricter server schemas that reject file parts.
                variants.append({"model": model_value, "parts": text_only_parts})
        return variants

    def _create_session(self, *, timeout_seconds: int) -> str:
        payload = {"title": f"manual-testing-{uuid.uuid4().hex[:8]}"}
        response = request_json(
            f"{self.base_url}/session",
            method="POST",
            payload=payload,
            headers=self._headers(),
            timeout_seconds=timeout_seconds,
        )
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected OpenCode create-session response: {response}")

        session_id = (
            response.get("id")
            or response.get("session_id")
            or response.get("sessionID")
            or ((response.get("info") or {}).get("id") if isinstance(response.get("info"), dict) else None)
        )
        if not isinstance(session_id, str) or not session_id.strip():
            raise RuntimeError(f"OpenCode create-session response missing id: {response}")
        return session_id

    def _delete_session(self, *, session_id: str, timeout_seconds: int) -> None:
        try:
            request_json(
                f"{self.base_url}/session/{session_id}",
                method="DELETE",
                headers=self._headers(),
                timeout_seconds=timeout_seconds,
            )
        except Exception:
            return

    def _headers(self) -> dict[str, str]:
        if not self.password:
            return {}
        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}


def _build_model_spec(*, model: str, provider_id: str) -> Any:
    model = model.strip()
    if "/" in model:
        parsed_provider, parsed_model = model.split("/", 1)
        if parsed_provider and parsed_model:
            return {"providerID": parsed_provider, "modelID": parsed_model}
    if provider_id:
        return {"providerID": provider_id, "modelID": model}
    return model


def _build_image_part(path: Path) -> dict[str, str]:
    mime = mime_type_for(path)
    data = encode_image_to_base64(path)
    return {
        "type": "file",
        "url": f"data:{mime};base64,{data}",
        "mime": mime,
        "filename": path.name,
        "source": "inline",
    }


def _extract_structured_output(response: dict[str, Any]) -> dict[str, Any] | None:
    top_level_structured = response.get("structured")
    if _is_decision_dict(top_level_structured):
        return top_level_structured

    info = response.get("info")
    if not isinstance(info, dict):
        info = {}

    for key in ("structured", "structured_output", "structuredOutput"):
        structured = info.get(key)
        if _is_decision_dict(structured):
            return structured

    # Some OpenCode responses return tool-call parts only, where the decision
    # object is nested in a StructuredOutput tool call payload.
    parts = response.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if not isinstance(part, dict):
                continue

            for key in ("input", "output", "state"):
                candidate = part.get(key)
                extracted = _extract_decision_from_unknown(candidate)
                if extracted is not None:
                    return extracted

            state = part.get("state")
            if isinstance(state, dict):
                for nested_key in ("input", "output"):
                    extracted = _extract_decision_from_unknown(state.get(nested_key))
                    if extracted is not None:
                        return extracted

    return None


def _extract_decision_from_unknown(value: Any) -> dict[str, Any] | None:
    if _is_decision_dict(value):
        return value
    if isinstance(value, dict):
        for nested in value.values():
            extracted = _extract_decision_from_unknown(nested)
            if extracted is not None:
                return extracted
    if isinstance(value, list):
        for item in value:
            extracted = _extract_decision_from_unknown(item)
            if extracted is not None:
                return extracted
    return None


def _is_decision_dict(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if "needs_manual_testing" not in value or "reason" not in value:
        return False
    if not isinstance(value["needs_manual_testing"], bool):
        return False
    if not isinstance(value["reason"], str):
        return False
    return True


def _extract_text_response(response: dict[str, Any]) -> str:
    parts = response.get("parts")
    if isinstance(parts, list):
        text_parts: list[str] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                text_parts.append(text)
                continue
            content = part.get("content")
            if isinstance(content, str) and content.strip():
                text_parts.append(content)
        if text_parts:
            return "\n".join(text_parts)

    direct_text = response.get("response")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text

    return ""


def build_opencode_adapter() -> OpencodeAdapter:
    keep_sessions = str(os.getenv("OPENCODE_KEEP_SESSIONS", "false")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    return OpencodeAdapter(
        base_url=os.getenv("OPENCODE_BASE_URL", "http://127.0.0.1:4096"),
        username=os.getenv("OPENCODE_SERVER_USERNAME", "opencode"),
        password=os.getenv("OPENCODE_SERVER_PASSWORD"),
        provider_id=os.getenv("OPENCODE_PROVIDER_ID"),
        keep_sessions=keep_sessions,
    )
