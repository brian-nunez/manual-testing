from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


_SEVERITY_NUMBER = {
    "TRACE": 1,
    "DEBUG": 5,
    "INFO": 9,
    "WARN": 13,
    "ERROR": 17,
    "FATAL": 21,
}


@dataclass
class _LogEvent:
    timestamp_ns: int
    severity_text: str
    body: str
    attributes: dict[str, Any] = field(default_factory=dict)


class OtelLogger:
    def __init__(
        self,
        *,
        enabled: bool,
        collector_url: str | None,
        service_name: str,
        resource_attributes: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        flush_on_each_log: bool = False,
        timeout_seconds: int = 10,
        run_id: str | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.collector_url = _normalize_collector_url(collector_url)
        self.service_name = service_name
        self.resource_attributes = resource_attributes or {}
        self.headers = headers or {}
        self.flush_on_each_log = bool(flush_on_each_log)
        self.timeout_seconds = int(timeout_seconds)
        self.run_id = run_id

        self._events: list[_LogEvent] = []
        self._started = False
        self._stopped = False
        self._lock = Lock()

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True

        self.info(
            "otel_logger_started",
            {
                "otel_enabled": self.enabled,
                "collector_url": self.collector_url or "",
                "service_name": self.service_name,
                "flush_on_each_log": self.flush_on_each_log,
                "run_id": self.run_id or "",
            },
        )

    def stop(self) -> None:
        with self._lock:
            if not self._started or self._stopped:
                return
            self._stopped = True

        self.info("otel_logger_stopping", {"run_id": self.run_id or ""})
        self.flush()

    def debug(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        self._log("DEBUG", event, attributes)

    def info(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        self._log("INFO", event, attributes)

    def warn(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        self._log("WARN", event, attributes)

    def error(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        self._log("ERROR", event, attributes)

    def flush(self) -> None:
        with self._lock:
            if not self._events:
                return
            batch = list(self._events)
            self._events.clear()

        if not self.enabled:
            return
        if not self.collector_url:
            self._write_stderr("OTEL logging enabled, but OTEL collector URL is missing; dropping log batch")
            return

        payload = self._build_payload(batch)
        body = json.dumps(payload).encode("utf-8")

        request_headers = {
            "Content-Type": "application/json",
            **self.headers,
        }

        request = Request(
            url=self.collector_url,
            data=body,
            headers=request_headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds):
                pass
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            self._write_stderr(
                f"OTEL export HTTP error {exc.code} {exc.reason}; body={response_body[:1200]}"
            )
        except URLError as exc:
            self._write_stderr(f"OTEL export network error: {exc}")
        except Exception as exc:
            self._write_stderr(f"OTEL export unexpected error: {exc}")

    def _log(self, severity_text: str, event: str, attributes: dict[str, Any] | None) -> None:
        normalized_attributes = dict(attributes or {})
        normalized_attributes.setdefault("event", event)
        if self.run_id:
            normalized_attributes.setdefault("run_id", self.run_id)

        record = _LogEvent(
            timestamp_ns=time.time_ns(),
            severity_text=severity_text,
            body=event,
            attributes=normalized_attributes,
        )

        line = {
            "ts_unix_nano": str(record.timestamp_ns),
            "severity": severity_text,
            "event": event,
            "attributes": normalized_attributes,
        }
        print(json.dumps(line, sort_keys=True), file=sys.stderr, flush=True)

        with self._lock:
            self._events.append(record)

        if self.flush_on_each_log:
            self.flush()

    def _build_payload(self, events: list[_LogEvent]) -> dict[str, Any]:
        resource_attrs = {
            "service.name": self.service_name,
            "service.instance.id": self.run_id or "",
            **self.resource_attributes,
        }

        return {
            "resourceLogs": [
                {
                    "resource": {
                        "attributes": [
                            _to_otel_kv(key, value) for key, value in resource_attrs.items() if value != ""
                        ]
                    },
                    "scopeLogs": [
                        {
                            "scope": {
                                "name": "manual-testing-triage",
                                "version": "0.1.0",
                            },
                            "logRecords": [
                                {
                                    "timeUnixNano": str(event.timestamp_ns),
                                    "severityNumber": _SEVERITY_NUMBER.get(event.severity_text, 9),
                                    "severityText": event.severity_text,
                                    "body": {"stringValue": event.body},
                                    "attributes": [
                                        _to_otel_kv(key, value) for key, value in event.attributes.items()
                                    ],
                                }
                                for event in events
                            ],
                        }
                    ],
                }
            ]
        }

    @staticmethod
    def _write_stderr(message: str) -> None:
        print(message, file=sys.stderr, flush=True)


class NullLogger:
    def start(self) -> None:
        return

    def stop(self) -> None:
        return

    def debug(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        return

    def info(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        return

    def warn(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        return

    def error(self, event: str, attributes: dict[str, Any] | None = None) -> None:
        return

    def flush(self) -> None:
        return


def build_logger(
    *,
    enabled: bool,
    collector_url: str | None,
    service_name: str,
    resource_attributes: dict[str, str],
    headers: dict[str, str],
    flush_on_each_log: bool,
    timeout_seconds: int,
    run_id: str,
) -> OtelLogger | NullLogger:
    return OtelLogger(
        enabled=enabled,
        collector_url=collector_url,
        service_name=service_name,
        resource_attributes=resource_attributes,
        headers=headers,
        flush_on_each_log=flush_on_each_log,
        timeout_seconds=timeout_seconds,
        run_id=run_id,
    )


def _to_otel_kv(key: str, value: Any) -> dict[str, Any]:
    return {
        "key": str(key),
        "value": _to_otel_any_value(value),
    }


def _to_otel_any_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if value is None:
        return {"stringValue": ""}
    return {"stringValue": str(value)}


def _normalize_collector_url(url: str | None) -> str | None:
    if not url:
        return None

    parsed = urlparse(url)
    if not parsed.scheme:
        return None

    if parsed.path and parsed.path != "/":
        return url

    return url.rstrip("/") + "/v1/logs"
