from __future__ import annotations

from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from manual_testing.config import AppConfig
from manual_testing.models import BrowserArtifacts, ManualQuestion, Viewport
from manual_testing.telemetry import NullLogger, OtelLogger


class BrowserCaptureError(RuntimeError):
    pass


def collect_browser_artifacts(
    config: AppConfig,
    questions: list[ManualQuestion],
    run_dir: Path,
    logger: OtelLogger | NullLogger | None = None,
) -> BrowserArtifacts:
    logger = logger or NullLogger()
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
        logger.info(
            "browser_launch_start",
            {
                "headless": config.headless,
                "default_viewport": config.default_viewports[0].key,
            },
        )
        browser = playwright.chromium.launch(headless=config.headless)
        context = browser.new_context(
            viewport={
                "width": config.default_viewports[0].width,
                "height": config.default_viewports[0].height,
            }
        )
        started_trace = False

        try:
            logger.info("playwright_trace_start", {"trace_path": str(trace_path)})
            context.tracing.start(screenshots=True, snapshots=True, sources=True)
            started_trace = True

            page = context.new_page()
            logger.info(
                "page_navigation_start",
                {
                    "url": config.url,
                    "wait_until": config.wait_until,
                    "navigation_timeout_ms": config.navigation_timeout_ms,
                },
            )
            page.goto(config.url, wait_until=config.wait_until, timeout=config.navigation_timeout_ms)
            if config.post_load_wait_ms > 0:
                page.wait_for_timeout(config.post_load_wait_ms)

            final_url = page.url
            html = page.content()
            logger.info(
                "page_navigation_complete",
                {
                    "requested_url": config.url,
                    "final_url": final_url,
                    "html_size_chars": len(html),
                },
            )

            _capture_automatic_behavior_timeseries(
                page=page,
                config=config,
                questions=questions,
                screenshot_dir=screenshot_dir,
                screenshots_by_question=screenshots_by_question,
                logger=logger,
            )

            requested_viewports = _question_viewports(config, questions)
            logger.info(
                "viewport_capture_plan",
                {
                    "question_count": len(requested_viewports),
                    "questions": ",".join(sorted(requested_viewports.keys())),
                },
            )
            for question_id, viewports in requested_viewports.items():
                for viewport in viewports:
                    if viewport.key not in screenshot_by_viewport_key:
                        logger.debug(
                            "viewport_capture_start",
                            {
                                "question_id": question_id,
                                "viewport": viewport.key,
                                "width": viewport.width,
                                "height": viewport.height,
                            },
                        )
                        page.set_viewport_size({"width": viewport.width, "height": viewport.height})
                        if config.viewport_settle_ms > 0:
                            page.wait_for_timeout(config.viewport_settle_ms)

                        screenshot_path = screenshot_dir / f"{viewport.key}.png"
                        page.screenshot(path=str(screenshot_path), full_page=True)
                        screenshot_by_viewport_key[viewport.key] = screenshot_path
                        logger.debug(
                            "viewport_capture_complete",
                            {
                                "question_id": question_id,
                                "viewport": viewport.key,
                                "path": str(screenshot_path),
                            },
                        )

                    screenshots_by_question[question_id].append(screenshot_by_viewport_key[viewport.key])
                    logger.debug(
                        "question_screenshot_associated",
                        {
                            "question_id": question_id,
                            "path": str(screenshot_by_viewport_key[viewport.key]),
                        },
                    )

        except PlaywrightTimeoutError as exc:
            logger.error(
                "page_navigation_timeout",
                {"url": config.url, "error": str(exc)},
            )
            recovered = _recover_timeout_artifacts(
                page=page,
                config=config,
                questions=questions,
                screenshot_dir=screenshot_dir,
                logger=logger,
            )
            if not recovered:
                raise BrowserCaptureError(f"Navigation timeout for {config.url}: {exc}") from exc

            final_url = recovered["final_url"] or final_url
            html = recovered["html"] or html
            for question_id, recovered_paths in recovered["screenshots_by_question"].items():
                screenshots_by_question.setdefault(question_id, [])
                screenshots_by_question[question_id].extend(recovered_paths)
            logger.warn(
                "page_navigation_timeout_recovered",
                {
                    "final_url": final_url,
                    "html_available": bool(html),
                    "recovered_questions": ",".join(sorted(recovered["screenshots_by_question"].keys())),
                },
            )
        except Exception as exc:
            logger.error("browser_capture_exception", {"error": str(exc)})
            raise BrowserCaptureError(f"Playwright capture failed: {exc}") from exc
        finally:
            if started_trace:
                try:
                    context.tracing.stop(path=str(trace_path))
                    logger.info("playwright_trace_stop", {"trace_path": str(trace_path)})
                except Exception:
                    trace_path = None
                    logger.error("playwright_trace_stop_failed", {"trace_path": str(trace_path)})
            context.close()
            browser.close()
            logger.info("browser_context_closed", {"final_url": final_url})

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


def _capture_automatic_behavior_timeseries(
    *,
    page,
    config: AppConfig,
    questions: list[ManualQuestion],
    screenshot_dir: Path,
    screenshots_by_question: dict[str, list[Path]],
    logger: OtelLogger | NullLogger,
) -> None:
    question_id = config.automatic_behavior_question_id
    if not config.automatic_behavior_timeseries_enabled:
        logger.debug("automatic_behavior_timeseries_disabled", {"question_id": question_id})
        return

    question_set = {question.question_id for question in questions}
    if question_id not in question_set:
        logger.debug(
            "automatic_behavior_question_not_in_scope",
            {"question_id": question_id},
        )
        return

    if config.automatic_behavior_interval_ms <= 0:
        logger.warn(
            "automatic_behavior_invalid_interval",
            {"interval_ms": config.automatic_behavior_interval_ms},
        )
        return

    frame_count = (max(config.automatic_behavior_duration_ms, 0) // config.automatic_behavior_interval_ms) + 1
    logger.info(
        "automatic_behavior_timeseries_start",
        {
            "question_id": question_id,
            "duration_ms": config.automatic_behavior_duration_ms,
            "interval_ms": config.automatic_behavior_interval_ms,
            "frames": frame_count,
        },
    )

    for frame_idx in range(frame_count):
        elapsed_ms = frame_idx * config.automatic_behavior_interval_ms
        screenshot_path = screenshot_dir / f"{question_id}_timeseries_{elapsed_ms:04d}ms.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        screenshots_by_question.setdefault(question_id, []).append(screenshot_path)
        logger.debug(
            "automatic_behavior_timeseries_frame",
            {
                "question_id": question_id,
                "frame_index": frame_idx,
                "elapsed_ms": elapsed_ms,
                "path": str(screenshot_path),
            },
        )
        if frame_idx < frame_count - 1:
            page.wait_for_timeout(config.automatic_behavior_interval_ms)

    logger.info("automatic_behavior_timeseries_complete", {"question_id": question_id})


def _recover_timeout_artifacts(
    *,
    page,
    config: AppConfig,
    questions: list[ManualQuestion],
    screenshot_dir: Path,
    logger: OtelLogger | NullLogger,
) -> dict | None:
    try:
        final_url = page.url
    except Exception:
        final_url = config.url or ""

    html = None
    try:
        html = page.content()
    except Exception as exc:
        logger.warn("timeout_recovery_html_failed", {"error": str(exc)})

    recovered_screenshots: dict[str, list[Path]] = {}
    try:
        screenshot_path = screenshot_dir / "timeout_recovery.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        for question in questions:
            if question.question_id in config.screenshot_question_ids:
                recovered_screenshots.setdefault(question.question_id, []).append(screenshot_path)
        logger.info(
            "timeout_recovery_screenshot_captured",
            {
                "path": str(screenshot_path),
                "questions_covered": len(recovered_screenshots),
            },
        )
    except Exception as exc:
        logger.warn("timeout_recovery_screenshot_failed", {"error": str(exc)})

    if not html and not recovered_screenshots:
        return None

    return {
        "final_url": final_url,
        "html": html,
        "screenshots_by_question": recovered_screenshots,
    }
