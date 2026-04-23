from __future__ import annotations

from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from manual_testing.config import AppConfig
from manual_testing.models import BrowserArtifacts, ManualQuestion, Viewport


class BrowserCaptureError(RuntimeError):
    pass


def collect_browser_artifacts(
    config: AppConfig,
    questions: list[ManualQuestion],
    run_dir: Path,
) -> BrowserArtifacts:
    if not config.url:
        raise ValueError("URL is required for browser capture")

    screenshot_dir = run_dir / "screenshots"
    trace_dir = run_dir / "traces"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    trace_path = trace_dir / f"playwright_trace_{config.run_id}.zip"

    screenshots_by_question: dict[str, list[Path]] = {question.question_id: [] for question in questions}
    screenshot_by_viewport_key: dict[str, Path] = {}
    html: str | None = None
    final_url = config.url

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=config.headless)
        context = browser.new_context(
            viewport={
                "width": config.default_viewports[0].width,
                "height": config.default_viewports[0].height,
            }
        )
        started_trace = False

        try:
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            started_trace = True

            page = context.new_page()
            page.goto(config.url, wait_until=config.wait_until, timeout=config.navigation_timeout_ms)
            if config.post_load_wait_ms > 0:
                page.wait_for_timeout(config.post_load_wait_ms)

            final_url = page.url
            html = page.content()

            requested_viewports = _question_viewports(config, questions)
            for question_id, viewports in requested_viewports.items():
                for viewport in viewports:
                    if viewport.key not in screenshot_by_viewport_key:
                        page.set_viewport_size({"width": viewport.width, "height": viewport.height})
                        if config.viewport_settle_ms > 0:
                            page.wait_for_timeout(config.viewport_settle_ms)

                        screenshot_path = screenshot_dir / f"{viewport.key}.png"
                        page.screenshot(path=str(screenshot_path), full_page=True)
                        screenshot_by_viewport_key[viewport.key] = screenshot_path

                    screenshots_by_question[question_id].append(screenshot_by_viewport_key[viewport.key])

        except PlaywrightTimeoutError as exc:
            raise BrowserCaptureError(f"Navigation timeout for {config.url}: {exc}") from exc
        except Exception as exc:
            raise BrowserCaptureError(f"Playwright capture failed: {exc}") from exc
        finally:
            if started_trace:
                try:
                    context.tracing.stop(path=str(trace_path))
                except Exception:
                    trace_path = None
            context.close()
            browser.close()

    return BrowserArtifacts(
        final_url=final_url,
        html=html,
        screenshots_by_question=screenshots_by_question,
        trace_path=trace_path,
    )


def _question_viewports(
    config: AppConfig,
    questions: list[ManualQuestion],
) -> dict[str, list[Viewport]]:
    requested: dict[str, list[Viewport]] = {}
    for question in questions:
        if question.question_id not in config.screenshot_question_ids:
            continue
        requested[question.question_id] = config.question_viewports.get(
            question.question_id,
            config.default_viewports,
        )
    return requested
