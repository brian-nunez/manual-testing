from __future__ import annotations

import argparse
import json
import sys

from manual_testing.config import AppConfig
from manual_testing.runner import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLM-based WCAG manual testing triage pipeline",
    )

    parser.add_argument("--run-id")
    parser.add_argument(
        "--provider",
        choices=["instances_api"],
    )
    parser.add_argument("--model")

    parser.add_argument("--manual-list-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--output-file")

    parser.add_argument("--url")
    parser.add_argument("--html-file")
    parser.add_argument(
        "--screenshot-file",
        dest="screenshot_files",
        action="append",
        default=[],
        help="Repeatable path to screenshot file",
    )
    parser.add_argument("--question-ids", help="Comma-separated list, e.g. question_1,question_4")

    parser.add_argument("--capture-browser", help="true/false")
    parser.add_argument("--headless", help="true/false")
    parser.add_argument("--wait-until", choices=["load", "domcontentloaded", "networkidle", "commit"])
    parser.add_argument("--navigation-timeout-ms")
    parser.add_argument("--post-load-wait-ms")
    parser.add_argument("--viewport-settle-ms")

    parser.add_argument("--llm-timeout-seconds")
    parser.add_argument("--execution-mode", choices=["sequential", "parallel"])
    parser.add_argument("--max-workers")
    parser.add_argument("--html-max-chars")
    parser.add_argument("--automatic-behavior-question-id")
    parser.add_argument("--automatic-behavior-timeseries-enabled", help="true/false")
    parser.add_argument("--automatic-behavior-interval-ms")
    parser.add_argument("--automatic-behavior-duration-ms")

    parser.add_argument("--default-viewports-json")
    parser.add_argument("--question-viewports-json")
    parser.add_argument("--screenshot-question-ids")

    parser.add_argument("--include-raw-response", help="true/false")
    parser.add_argument("--include-prompt-in-output", help="true/false")

    parser.add_argument("--publish-api-url")
    parser.add_argument("--publish-api-token")
    parser.add_argument("--publish-timeout-seconds")

    parser.add_argument("--s3-upload-enabled", help="true/false")
    parser.add_argument("--s3-endpoint-url")
    parser.add_argument("--s3-bucket")
    parser.add_argument("--s3-region")
    parser.add_argument("--s3-access-key-id")
    parser.add_argument("--s3-secret-access-key")
    parser.add_argument("--s3-session-token")
    parser.add_argument("--s3-key-prefix")
    parser.add_argument("--s3-method", choices=["PUT", "POST"])

    parser.add_argument("--otel-logging-enabled", help="true/false")
    parser.add_argument("--otel-collector-url")
    parser.add_argument("--otel-service-name")
    parser.add_argument("--otel-resource-attributes-json")
    parser.add_argument("--otel-headers-json")
    parser.add_argument("--otel-flush-on-each-log", help="true/false")
    parser.add_argument("--otel-timeout-seconds")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = AppConfig.from_sources(args)
        run_output, output_path = run_pipeline(config)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload = run_output.to_dict()
    print(json.dumps({"output_file": str(output_path), "summary": payload["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
