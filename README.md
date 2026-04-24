# Manual Accessibility Testing Triage (Python)

A minimal Python project that:

- Loads manual WCAG questions from `manual-list/question_*.md`
- Uses dedicated per-question prompt instructions for all 16 tests
- Captures page artifacts with Playwright (HTML + screenshots by viewport + trace)
- Sends each question through the `instances_api` adapter (`instances[]` request + `predictions[]` response)
- Uses deterministic `selectolax` extraction for Test #7 form input-purpose evidence
- Returns one consolidated JSON report with per-question decisions
- Optionally publishes the report to an API (`POST`) and uploads Playwright traces to S3 path-style URLs

## Output decision schema

Each question returns:

```json
{
  "needs_manual_testing": true,
  "reason": "String describing why this test applies or can be skipped"
}
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m playwright install chromium
```

## Quick run

```bash
export INSTANCES_API_URL="https://your-endpoint"
export INSTANCES_API_KEY="..."
manual-testing-run \
  --provider instances_api \
  --model llama32-90b-instruct \
  --url "https://example.com" \
  --output-dir run-artifacts
```

The command writes a full JSON report to `run-artifacts/<run-id>/...` and prints a summary to stdout.

## LLM Adapter

Only `instances_api` is supported.

Instances API adapter environment variables:

- `INSTANCES_API_URL` (required)
- `INSTANCES_API_KEY` (optional bearer token)
- `INSTANCES_API_TEMPERATURE` (default `0.1`)
- `INSTANCES_API_MAX_TOKENS` (default `10000`)
- `INSTANCES_API_TOP_P` (default `0.3`)
- `INSTANCES_API_TOP_K` (default `8`)

Implementations live in:

- `src/manual_testing/llm/base.py`
- `src/manual_testing/llm/factory.py`
- `src/manual_testing/llm/*.py`

## Deterministic Form Analysis (#7)

Test #7 includes a deterministic pre-analysis step implemented with `selectolax`:

- Extracts form fields from HTML
- Infers likely WCAG input-purpose tokens
- Checks `autocomplete` presence and token plausibility
- Injects structured evidence JSON into the Test #7 prompt
- Uses deterministic fallback only if the LLM call fails (so LLM remains primary decision-maker when available)

Implementation:

- `src/manual_testing/form_purpose_analyzer.py`

## Per-question prompts

- Prompt library: `src/manual_testing/question_prompts.py`
- Prompt assembly: `src/manual_testing/prompt_builder.py`

Each question (`question_1` ... `question_16`) has authored, test-specific instructions in addition to the source markdown definition.

## Inputs

Any combination is supported:

- `--url` (browser capture)
- `--html-file /path/to/file.html`
- `--screenshot-file /path/to/image.png` (repeatable)

If `--url` is provided and `--capture-browser` is true (default), Playwright:

- starts tracing
- opens Chromium
- waits for page load
- captures HTML
- captures screenshots for questions configured to require screenshots
- resizes to question-specific viewports (with configurable defaults)
- captures an automatic-behavior time series for `question_1` (default): every 500ms for 3000ms after load
- always stops tracing in a `finally` block

Navigation wait default is `domcontentloaded` (safer for highly dynamic sites that may never reach `networkidle`).

Automatic behavior time-series settings:

- `AUTOMATIC_BEHAVIOR_QUESTION_ID` (default `question_1`)
- `AUTOMATIC_BEHAVIOR_TIMESERIES_ENABLED` (default `true`)
- `AUTOMATIC_BEHAVIOR_INTERVAL_MS` (default `500`)
- `AUTOMATIC_BEHAVIOR_DURATION_MS` (default `3000`)

## Viewport config

Default viewport is desktop `1366x768`.

Overrides are supported with JSON:

- `DEFAULT_VIEWPORTS_JSON`
- `QUESTION_VIEWPORTS_JSON`

Example:

```bash
export QUESTION_VIEWPORTS_JSON='{"question_9":[{"name":"mobile","width":320,"height":900},{"name":"desktop","width":1440,"height":900}]}'
```

## Publish results to API

Set:

- `PUBLISH_API_URL`
- `PUBLISH_API_TOKEN` (optional)

The final consolidated JSON report is POSTed to the configured API.

## Upload Playwright trace to S3 (path style)

Enable:

- `S3_UPLOAD_ENABLED=true`
- `S3_ENDPOINT_URL=https://s3.amazonaws.com` (or compatible endpoint)
- `S3_BUCKET=your-bucket`
- `AWS_ACCESS_KEY_ID=...`
- `AWS_SECRET_ACCESS_KEY=...`
- `AWS_REGION=us-east-1` (default)
- `S3_KEY_PREFIX=playwright-traces` (optional)
- `S3_UPLOAD_METHOD=POST` (default; set `PUT` if your S3 target requires PUT object uploads)

The uploader signs requests with AWS SigV4 and uploads the trace file using path-style URLs:

`<endpoint>/<bucket>/<key>`

## OTel logging

The runner emits high-volume structured logs and can dispatch OTLP logs to a collector when feature-flagged on.

Set:

- `OTEL_LOGGING_ENABLED=true`
- `OTEL_COLLECTOR_URL=http://localhost:4318/v1/logs`
- `OTEL_SERVICE_NAME=manual-testing-triage`
- `OTEL_RESOURCE_ATTRIBUTES_JSON='{\"deployment.environment\":\"local\"}'` (optional)
- `OTEL_HEADERS_JSON='{\"Authorization\":\"Bearer ...\"}'` (optional)
- `OTEL_FLUSH_ON_EACH_LOG=false` (optional)
- `OTEL_TIMEOUT_SECONDS=10` (optional)

## CLI options

```bash
manual-testing-run --help
```

Useful options:

- `--question-ids question_1,question_4`
- `--execution-mode sequential|parallel`
- `--max-workers 4`
- `--capture-browser true|false`
- `--headless true|false`
- `--navigation-timeout-ms 45000`
- `--default-viewports-json '[{"name":"desktop","width":1366,"height":768}]'`
- `--screenshot-question-ids question_4,question_9,question_16`
- `--automatic-behavior-interval-ms 500`
- `--automatic-behavior-duration-ms 3000`
- `--otel-logging-enabled true`
- `--otel-collector-url http://localhost:4318/v1/logs`
- `--include-raw-response true`
- `--include-prompt-in-output true`

## Airflow-friendly behavior

- Single command invocation with explicit exit code
- JSON output file for downstream tasks
- Question execution mode switch: `EXECUTION_MODE=sequential|parallel` with `MAX_WORKERS` cap
- Defensive per-question error handling (one question failing does not abort all results)
- Optional upstream/downstream API integration through ENV-driven config
