# Manual Accessibility Testing Triage (Python)

A minimal Python project that:

- Loads manual WCAG questions from `manual-list/question_*.md`
- Captures page artifacts with Playwright (HTML + screenshots by viewport + trace)
- Sends each question to a pluggable LLM adapter strategy (`codex`, `gemini`, `llama`, `ollama`)
- Returns one consolidated JSON report with per-question decisions
- Optionally publishes the report to an API (`POST`) and uploads Playwright traces to S3 path-style URLs

## Output decision schema

Each question returns:

```json
{
  "needs_manual_testing": true,
  "relevant": true,
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
export OPENAI_API_KEY="..."
manual-testing-run \
  --provider codex \
  --model gpt-5.4-mini \
  --url "https://example.com" \
  --output-dir run-artifacts
```

The command writes a full JSON report to `run-artifacts/<run-id>/...` and prints a summary to stdout.

## Generic adapter strategy

Adapters are selected with `--provider` (or `LLM_PROVIDER`):

- `codex`: OpenAI-compatible `/v1/chat/completions`
- `gemini`: Google `generateContent`
- `llama`: OpenAI-compatible endpoint for hosted/self-hosted Llama servers
- `ollama`: Local `OLLAMA_BASE_URL/api/generate`

Implementations live in:

- `src/manual_testing/llm/base.py`
- `src/manual_testing/llm/factory.py`
- `src/manual_testing/llm/*.py`

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
- always stops tracing in a `finally` block

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

## CLI options

```bash
manual-testing-run --help
```

Useful options:

- `--question-ids question_1,question_4`
- `--capture-browser true|false`
- `--headless true|false`
- `--navigation-timeout-ms 45000`
- `--default-viewports-json '[{"name":"desktop","width":1366,"height":768}]'`
- `--screenshot-question-ids question_4,question_9,question_16`
- `--include-raw-response true`
- `--include-prompt-in-output true`

## Airflow-friendly behavior

- Single command invocation with explicit exit code
- JSON output file for downstream tasks
- Defensive per-question error handling (one question failing does not abort all results)
- Optional upstream/downstream API integration through ENV-driven config
