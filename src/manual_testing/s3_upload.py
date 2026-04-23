from __future__ import annotations

import datetime as dt
import hashlib
import hmac
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse, urlunparse
from urllib.request import Request, urlopen


class S3UploadError(RuntimeError):
    pass


def upload_file_path_style(
    file_path: Path,
    *,
    endpoint_url: str,
    bucket: str,
    object_key: str,
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None = None,
    method: str = "PUT",
    timeout_seconds: int = 60,
) -> str:
    if not file_path.exists():
        raise S3UploadError(f"Trace file not found: {file_path}")

    parsed_endpoint = urlparse(endpoint_url)
    if parsed_endpoint.scheme not in {"http", "https"}:
        raise S3UploadError("S3 endpoint must start with http:// or https://")

    payload = file_path.read_bytes()
    payload_hash = hashlib.sha256(payload).hexdigest()

    amz_date = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    date_stamp = amz_date[:8]
    service = "s3"

    escaped_key = quote(object_key.lstrip("/"), safe="/-_.~")
    prefix_path = parsed_endpoint.path.rstrip("/")
    canonical_uri = f"{prefix_path}/{bucket}/{escaped_key}"
    if not canonical_uri.startswith("/"):
        canonical_uri = "/" + canonical_uri

    host = parsed_endpoint.netloc

    headers = {
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "content-type": "application/zip",
    }
    if session_token:
        headers["x-amz-security-token"] = session_token

    signed_header_names = sorted(headers.keys())
    canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in signed_header_names)
    signed_headers = ";".join(signed_header_names)

    canonical_request = "\n".join(
        [
            method,
            canonical_uri,
            "",
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    signing_key = _signature_key(secret_access_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        "AWS4-HMAC-SHA256 "
        f"Credential={access_key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    request_headers = {
        "Authorization": authorization,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Content-Type": "application/zip",
    }
    if session_token:
        request_headers["x-amz-security-token"] = session_token

    request_url = urlunparse(
        (
            parsed_endpoint.scheme,
            parsed_endpoint.netloc,
            canonical_uri,
            "",
            "",
            "",
        )
    )

    request = Request(
        url=request_url,
        data=payload,
        headers=request_headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout_seconds):
            pass
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise S3UploadError(f"S3 upload failed ({exc.code} {exc.reason}): {body}") from exc
    except URLError as exc:
        raise S3UploadError(f"S3 upload network error: {exc}") from exc

    return request_url


def _signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()
