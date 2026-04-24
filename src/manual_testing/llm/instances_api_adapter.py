from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Any, Sequence

from manual_testing.llm.base import LLMAdapter
from manual_testing.llm.http_utils import encode_image_to_base64, mime_type_for, request_json


class InstancesAPIAdapter(LLMAdapter):
    name = "instances_api"

    def __init__(
        self,
        *,
        endpoint_url: str,
        api_key: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 10000,
        top_p: float = 0.3,
        top_k: int = 8,
        image_quality: int = 70,
        image_max_side: int = 1280,
        image_force_jpeg: bool = True,
    ) -> None:
        endpoint = endpoint_url.strip()
        if not endpoint:
            raise ValueError("INSTANCES_API_URL is required for the instances_api adapter")

        self.endpoint_url = endpoint
        self.api_key = (api_key or "").strip()
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.image_quality = max(1, min(int(image_quality), 95))
        self.image_max_side = max(0, int(image_max_side))
        self.image_force_jpeg = bool(image_force_jpeg)

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
        user_objects = _build_user_objects(
            html=html,
            image_paths=image_paths,
            structured_evidence=structured_evidence,
            url=url,
            question_id=question_id,
            question_title=question_title,
            image_quality=self.image_quality,
            image_max_side=self.image_max_side,
            image_force_jpeg=self.image_force_jpeg,
        )
        payload = {
            "instances": [
                {
                    "messages": [
                        {
                            "content": prompt,
                            "role": "system",
                        },
                        *user_objects,
                    ],
                    "model": model,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                    "top_p": self.top_p,
                    "top_k": self.top_k,
                }
            ]
        }

        headers = self._headers()
        response = request_json(
            self.endpoint_url,
            method="POST",
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected instances API response type: {type(response).__name__}")

        message_content = _extract_message_content(response)
        if message_content is None:
            raise RuntimeError(f"Unexpected instances API response body: {_safe_repr(response)}")

        if isinstance(message_content, str):
            return message_content
        return json.dumps(message_content)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}


def _extract_message_content(response: dict[str, Any]) -> str | dict[str, Any] | None:
    predictions = response.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        return None

    first_prediction = predictions[0]
    if not isinstance(first_prediction, dict):
        return None

    choices = first_prediction.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        return None

    message = first_choice.get("message")
    if not isinstance(message, dict):
        return None

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, dict):
        return content
    return None


def _build_user_objects(
    *,
    html: str | None,
    image_paths: Sequence[Path],
    structured_evidence: dict[str, Any] | None,
    url: str | None,
    question_id: str | None,
    question_title: str | None,
    image_quality: int,
    image_max_side: int,
    image_force_jpeg: bool,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "type": "page_context",
                    "question_id": question_id,
                    "question_title": question_title,
                    "url": url,
                },
                ensure_ascii=False,
            ),
        }
    )

    if structured_evidence is not None:
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "type": "structured_evidence",
                        "data": structured_evidence,
                    },
                    ensure_ascii=False,
                ),
            }
        )

    if html:
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "type": "html",
                        "content": html,
                    },
                    ensure_ascii=False,
                ),
            }
        )

    for image_path in image_paths:
        encoded = _encode_image_for_payload(
            image_path=image_path,
            image_quality=image_quality,
            image_max_side=image_max_side,
            image_force_jpeg=image_force_jpeg,
        )
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "type": "image",
                        "filename": encoded["filename"],
                        "mime_type": encoded["mime_type"],
                        "data_base64": encoded["data_base64"],
                        "original_filename": image_path.name,
                    },
                    ensure_ascii=False,
                ),
            }
        )

    messages.append(
        {
            "role": "user",
            "content": json.dumps(
                {
                    "type": "instruction",
                    "content": "Use all provided objects as evidence and return only the required JSON schema.",
                },
                ensure_ascii=False,
            ),
        }
    )
    return messages


def _safe_repr(value: Any, max_len: int = 1800) -> str:
    try:
        rendered = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        rendered = repr(value)
    if len(rendered) <= max_len:
        return rendered
    return rendered[:max_len] + "...(truncated)"


def _encode_image_for_payload(
    *,
    image_path: Path,
    image_quality: int,
    image_max_side: int,
    image_force_jpeg: bool,
) -> dict[str, str]:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        # Fallback: send original image when Pillow is not available.
        return {
            "filename": image_path.name,
            "mime_type": mime_type_for(image_path),
            "data_base64": encode_image_to_base64(image_path),
        }

    with Image.open(image_path) as original:
        image = original.copy()

    if image_max_side > 0:
        max_current_side = max(image.width, image.height)
        if max_current_side > image_max_side:
            scale = image_max_side / float(max_current_side)
            resized_width = max(1, int(image.width * scale))
            resized_height = max(1, int(image.height * scale))
            image = image.resize((resized_width, resized_height), resample=Image.Resampling.LANCZOS)

    if image_force_jpeg:
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        out = BytesIO()
        image.save(
            out,
            format="JPEG",
            quality=image_quality,
            optimize=True,
            progressive=True,
        )
        encoded = out.getvalue()
        return {
            "filename": _with_jpeg_extension(image_path.name),
            "mime_type": "image/jpeg",
            "data_base64": _bytes_to_b64(encoded),
        }

    out = BytesIO()
    image_format = _normalized_image_format(image)
    save_kwargs: dict[str, Any] = {}
    if image_format == "JPEG":
        if image.mode in {"RGBA", "LA"}:
            image = image.convert("RGB")
        save_kwargs = {"quality": image_quality, "optimize": True, "progressive": True}
    image.save(out, format=image_format, **save_kwargs)
    encoded = out.getvalue()
    extension = _extension_for_format(image_format)
    filename = image_path.name
    if extension and not filename.lower().endswith(extension):
        filename = f"{Path(filename).stem}{extension}"
    return {
        "filename": filename,
        "mime_type": f"image/{image_format.lower()}",
        "data_base64": _bytes_to_b64(encoded),
    }


def _normalized_image_format(image: Any) -> str:
    fmt = (getattr(image, "format", None) or "PNG").upper()
    if fmt in {"JPG", "JPEG"}:
        return "JPEG"
    if fmt in {"PNG", "WEBP"}:
        return fmt
    return "PNG"


def _extension_for_format(image_format: str) -> str:
    if image_format == "JPEG":
        return ".jpg"
    if image_format == "PNG":
        return ".png"
    if image_format == "WEBP":
        return ".webp"
    return ""


def _with_jpeg_extension(filename: str) -> str:
    stem = Path(filename).stem
    return f"{stem}.jpg"


def _bytes_to_b64(raw: bytes) -> str:
    import base64

    return base64.b64encode(raw).decode("ascii")


def _to_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if not normalized:
        return default
    return normalized in {"1", "true", "yes", "on"}


def build_instances_api_adapter() -> InstancesAPIAdapter:
    return InstancesAPIAdapter(
        endpoint_url=os.getenv("INSTANCES_API_URL", ""),
        api_key=os.getenv("INSTANCES_API_KEY"),
        temperature=float(os.getenv("INSTANCES_API_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("INSTANCES_API_MAX_TOKENS", "10000")),
        top_p=float(os.getenv("INSTANCES_API_TOP_P", "0.3")),
        top_k=int(os.getenv("INSTANCES_API_TOP_K", "8")),
        image_quality=int(os.getenv("INSTANCES_API_IMAGE_QUALITY", "70")),
        image_max_side=int(os.getenv("INSTANCES_API_IMAGE_MAX_SIDE", "1280")),
        image_force_jpeg=_to_bool(os.getenv("INSTANCES_API_IMAGE_FORCE_JPEG"), default=True),
    )
