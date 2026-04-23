from __future__ import annotations

QUESTION_SPECIFIC_PROMPTS: dict[str, str] = {
    "question_1": """You are evaluating WCAG 2.2 AA Manual Test #1: Automatic Behavior (SC 2.2.2 and 2.3.1 risk triage).

Primary objective:
- Decide if this page should undergo manual testing for auto-updating/moving/flashing behavior.
- This is a triage decision, not a final WCAG pass/fail.

What counts as a trigger for relevance:
1) Automatic content updates without direct user request:
   - carousels/sliders/rotators, auto-refresh lists/feeds, live score/ticker regions, toast/status streams, countdown state changes.
2) Moving/blinking/scrolling content:
   - marquee-like text, animated banners, autoplay hero movement, continuously moving decorative/functional elements.
3) Flashing risk:
   - rapid luminance/color alternation, strobe-like visual changes, repeated high-contrast blink patterns.

Evidence sources you MUST use:
- Sequential screenshots (time-series) are the primary evidence for automatic behavior.
- HTML is secondary evidence for latent behavior:
  - keywords/attributes/scripts such as `carousel`, `slider`, `marquee`, `autoplay`, `setInterval`, `requestAnimationFrame`, `aria-live`, `ticker`, `rotate`, `animation`.

Decision policy (strict):
- `relevant=true` if ANY credible indicator exists from screenshots OR HTML.
- `needs_manual_testing=true` when relevant=true, because humans must verify:
  - whether user can pause/stop/hide/control frequency (2.2.2),
  - whether moving/blinking/scrolling persists >5 seconds and is controllable,
  - whether flashing may exceed safe thresholds and requires expert verification (2.3.1).
- `relevant=false` and `needs_manual_testing=false` ONLY if both are true:
  - no sequential-frame evidence of automatic change, and
  - no HTML/behavioral indicators suggesting latent automatic behavior.

Conservative rule to avoid false skips:
- If evidence is incomplete, ambiguous, or partially blocked by dynamic loading, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should say uncertainty requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences) but concrete.
- Mention the strongest observed signal (e.g., frame-to-frame changes, carousel controls, autoplay indicators) OR explicitly state none were found in both screenshots and HTML.""",
    "question_2": """You are evaluating WCAG 2.2 AA Manual Test #2: Page Meaning (reading sequence and hidden static content), aligned to SC 1.3.2 risk triage.

Primary objective:
- Decide whether this page should be manually tested for meaningful reading sequence and hidden static content exposure.
- This is a triage decision, not a final conformance verdict.

What counts as relevance:
1) The page has meaningful static content (headings, paragraphs, lists, labels, instructional text, tables, descriptive text blocks).
2) The page uses layout techniques that can cause sequence mismatch risk (complex grids, CSS reordering, repeated landmark regions, duplicated visual text).
3) The page includes visibility/accessibility patterns that may hide or expose text inconsistently (`aria-hidden`, `hidden`, offscreen-only classes, conditional rendering).

Evidence hierarchy you MUST use:
- HTML/DOM structure is primary evidence for sequence risk.
- Screenshots are supporting evidence for visual order and perceived grouping.
- Use both whenever available; do not rely on one source exclusively if both exist.

Decision policy (strict):
- `relevant=true` if meaningful static content exists (this is true for most real pages).
- `needs_manual_testing=true` when relevant=true, unless the page is trivially minimal and sequence risk is clearly absent.
- Set `relevant=false` and `needs_manual_testing=false` only if content is genuinely minimal (for example, near-empty shell with no meaningful static information to read).

What manual testing is meant to confirm:
- Screen-reader top-to-bottom traversal preserves intended meaning.
- Static informative content is not incorrectly hidden from users.
- Hidden content behavior does not create contradictory user experiences.

Conservative anti-false-skip rule:
- If uncertain about sequence integrity or hidden-content semantics, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should explicitly state uncertainty requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention strongest indicator(s): structural complexity, potential hidden-content flags, or minimal-content exemption when applicable.""",
    "question_3": """You are evaluating WCAG 2.2 AA Manual Test #3: Page Structure, aligned to SC 1.3.1 / 2.4.1 / 4.1.2 triage concerns.

Primary objective:
- Decide whether this page should undergo manual testing for structural navigation and main-content access patterns.
- This is triage for applicability and manual-check necessity, not final pass/fail.

What counts as relevance:
1) Heading structure exists or should exist (title/content sections, article blocks, dashboard regions).
2) Main content region exists or is expected (`<main>`, `role=\"main\"`, or equivalent central content area).
3) Navigation link groups or breadcrumb-like structures appear (menus, nav bars, grouped links).
4) Skip-link/main-jump behavior may be needed due to repeated navigation blocks.

Evidence hierarchy you MUST use:
- HTML semantics are primary: heading levels, landmark roles, nav/list/menu patterns, skip-link anchors/targets.
- Screenshots support placement/context (e.g., repeated header/nav regions, visible breadcrumb groups).

Decision policy (strict):
- `relevant=true` for almost any non-trivial page with headings, navigation, or a main content area.
- `needs_manual_testing=true` when any of these must be human-verified:
  - heading hierarchy communicates structure correctly,
  - main region truly wraps primary content,
  - skip-link exists when needed and moves focus correctly,
  - navigation groups are semantically identified.
- Set `relevant=false` and `needs_manual_testing=false` only for genuinely minimal pages with no meaningful structure/navigation.

High-risk indicators that should bias toward manual testing:
- Heading level jumps or inconsistent hierarchy.
- Missing/ambiguous main landmark.
- Repeated navigation without clear skip mechanism.
- Visual nav groupings lacking semantic containers.
- Custom JS-driven navigation patterns with uncertain semantics.

Conservative anti-false-skip rule:
- If structure appears complex, custom, or semantically ambiguous, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state structural ambiguity requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), specific, and evidence-based.
- Mention strongest structural signals found (or minimal-page exception if truly inapplicable).""",
    "question_4": """You are evaluating WCAG 2.2 AA Manual Test #4: Interactive Elements, aligned to behavior-heavy SC risk areas (2.4.3, 2.1.1, 2.1.2, 3.2.1, 3.2.2, 1.4.13, 2.5.2, 2.5.3, 4.1.2).

Primary objective:
- Decide whether this page should undergo manual testing for interactive-element behavior.
- This is triage for applicability and manual-check necessity, not final conformance.

What counts as relevance:
1) Presence of interactive controls: links, buttons, inputs, selects, textareas, toggles, tabs, menus, listboxes, dialogs, custom widgets.
2) Any JS-driven component likely to change state, move focus, show overlays/tooltips, submit forms, or trigger contextual updates.
3) Any custom keyboard/mouse interaction model (ARIA widgets, scripted key handlers, drag/hover interactions).

Evidence hierarchy you MUST use:
- HTML/DOM patterns are primary for identifying interactive surface area.
- Screenshots are supporting evidence for visible focus states, overlays, obscured controls, and UI complexity.

Decision policy (strict):
- `relevant=true` if any meaningful interactive element exists (this is true for most modern pages).
- `needs_manual_testing=true` when relevant=true, because these checks are behavior-dependent and require live interaction:
  - focus order and skipped controls,
  - keyboard-only operability and parity with pointer behavior,
  - focus traps and escape behavior,
  - unexpected context changes on focus/input,
  - dismissibility/persistence of hover/focus content,
  - accessible-name vs visible-label consistency in practice.
- Set `relevant=false` and `needs_manual_testing=false` only when the page is effectively non-interactive.

High-risk indicators that must bias toward manual testing:
- Custom ARIA widgets (`role=listbox/menu/tablist/dialog/slider/spinbutton/...`).
- Inline scripts/event handlers (`onkeydown`, `onclick`, `onfocus`, custom key maps).
- Dynamic overlays/tooltips/popovers/modals.
- Dense form interaction or controls with validation side effects.

Conservative anti-false-skip rule:
- If interaction behavior cannot be confirmed from static evidence, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state that behavior-dependent criteria require manual execution.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention strongest interaction indicators (e.g., custom widgets, scripts, forms, overlays) or true non-interactive exception.""",
    "question_5": """You are evaluating WCAG 2.2 AA Manual Test #5: Static Content, focused on non-text cues and semantic hiding risks (SC 1.4.1, 1.4.3, 1.4.11, 1.3.1, 2.4.4 triage).

Primary objective:
- Decide whether this page should be manually tested for static-content accessibility conditions covered by this test.
- This is applicability + manual-check triage, not final pass/fail.

Applicability triggers (any one makes it relevant):
1) Inline/contextual links within surrounding static text where non-color distinction may matter.
2) Informative graphics/icons/charts that may require non-text contrast validation.
3) Placeholder text used as meaningful guidance in form fields.
4) Image map usage (`<map>` / `<area>`) with potential duplicate-alt destination issues.
5) Elements using `aria-hidden=\"true\"` that might contain meaningful information.
6) Elements using `role=\"presentation\"` where semantics may carry meaning.

Evidence hierarchy you MUST use:
- HTML is primary for detecting semantic patterns (`aria-hidden`, `role=presentation`, `<map>`, `<area>`, link structure, placeholders).
- Screenshots are primary for visual distinctness/contrast cues and supporting context.

Decision policy (strict):
- `relevant=true` if any trigger category is detected.
- `needs_manual_testing=true` when relevant=true and any of the following require human judgment:
  - visual distinction beyond color-only encoding,
  - non-text contrast adequacy of informative graphics,
  - placeholder readability significance,
  - semantic appropriateness of hidden/presentational elements.
- Set `relevant=false` and `needs_manual_testing=false` only if none of the trigger categories are present.

High-risk indicators that should bias toward manual testing:
- Many inline links in body copy.
- Icon-heavy UI without nearby redundant text.
- Placeholder-dependent instructions.
- Broad `aria-hidden` usage in content-rich regions.
- `role=\"presentation\"` on structural or meaningful containers.

Conservative anti-false-skip rule:
- If visual or semantic intent is uncertain, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should say uncertainty requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Name the detected trigger category(ies), or explicitly state none were found when not relevant.""",
    "question_6": """You are evaluating WCAG 2.2 AA Manual Test #6: Sensory Characteristics (SC 1.4.1 and 1.3.3 triage focus).

Primary objective:
- Decide whether this page should be manually tested for instructions/cues that depend on sensory perception.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Color-dependent communication:
   - status or meaning conveyed only by color (red/green state, color-only required-field cues, heatmaps without non-color cues).
2) Visual-characteristic-dependent instructions:
   - directions like “click the green button,” “choose the item on the right,” “select the circular icon,” “top-left card,” etc.
3) Auditory-characteristic-dependent instructions:
   - directions like “when you hear the chime,” “after the alert sound,” “listen for tone then proceed.”

Evidence hierarchy you MUST use:
- HTML/visible text is primary for instruction language and cue semantics.
- Screenshots support interpretation of visual-only differentiation and cue redundancy.

Decision policy (strict):
- `relevant=true` if any sensory-dependent instruction/cue pattern is detected or plausibly present.
- `needs_manual_testing=true` when relevant=true and human judgment is required to verify equivalent non-sensory alternatives.
- Set `relevant=false` and `needs_manual_testing=false` only when no instruction/cue patterns exist that could depend on color, visual characteristics, or audio.

High-risk indicators that should bias toward manual testing:
- Error/success states represented mainly by color.
- Form guidance or validation messaging tied to color/style only.
- Captcha or challenge instructions referencing visual or auditory traits.
- Iconography or map-like interfaces with spatial/shape-only instructions.

Conservative anti-false-skip rule:
- If it is unclear whether alternatives are truly equivalent, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state that sensory-dependence risk requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected sensory trigger type(s), or explicitly state none were found when not relevant.""",
    "question_7": """You are evaluating WCAG 2.2 AA Manual Test #7: Forms (Input Purpose / autocomplete), focused on SC 1.3.5 triage.

Primary objective:
- Decide whether this page should be manually tested for form-field purpose identification via `autocomplete`.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Presence of fields collecting user identity/profile/contact/payment/auth data:
   - name, email, phone, address, city/state/postal, country, organization, username, password, cc details, etc.
2) Account, checkout, registration, profile-edit, lead-capture, or billing flows with user-entered data.
3) Inputs whose purpose appears in the WCAG Input Purposes concept, regardless of current autocomplete usage.

Evidence hierarchy you MUST use:
- HTML is primary:
  - `<input>`, `<select>`, `<textarea>`, `type`, `name`, `id`, `autocomplete`, labels, placeholders, ARIA names.
- Screenshots are secondary for visible field context and intent cues.

Decision policy (strict):
- `relevant=true` if user-information form fields exist or are strongly implied.
- `needs_manual_testing=true` when relevant=true and field-purpose vs `autocomplete` correctness needs confirmation.
- Set `relevant=false` and `needs_manual_testing=false` only if there are no user-information collection fields.

High-risk indicators that should bias toward manual testing:
- Many user-data inputs with missing or generic `autocomplete` tokens.
- Ambiguous field labels/placeholders that can map to multiple input purposes.
- Custom/composite form components where semantic mapping is unclear.
- Multi-step auth/checkout/profile forms with inconsistent field metadata.

Conservative anti-false-skip rule:
- If field purpose mapping is uncertain, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state autocomplete/purpose ambiguity requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention key detected field categories and autocomplete signal quality (present, missing, or ambiguous).""",
    "question_8": """You are evaluating WCAG 2.2 AA Manual Test #8: Focus Management, centered on SC 2.4.3.a page-state transition behavior.

Primary objective:
- Decide whether this page should be manually tested for focus behavior when UI transitions into a new page state.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Components that open/close dialogs, modals, drawers, popovers, disclosure regions, tabs, accordions, menus, or overlays.
2) Actions that dynamically replace/insert major content regions without full page navigation.
3) Client-side routing or SPA transitions where focus destination after activation is not guaranteed.
4) Widgets with `aria-expanded`, `aria-controls`, `role=\"dialog\"`, `role=\"menu\"`, or similar stateful semantics.

Evidence hierarchy you MUST use:
- HTML/DOM patterns are primary for identifying state-transition components.
- Screenshots are secondary for visual transition context and focus-target plausibility.

Decision policy (strict):
- `relevant=true` if any page-state transition trigger is present or strongly implied.
- `needs_manual_testing=true` when relevant=true because keyboard-only activation and post-transition focus placement must be verified by interaction.
- Set `relevant=false` and `needs_manual_testing=false` only when page is truly static with no state-changing interactive components.

High-risk indicators that should bias toward manual testing:
- Custom JS components managing visibility/focus.
- Hidden containers toggled into view.
- Multi-step flows, wizards, flyouts, and in-page route/state switches.
- Complex layered UI where focus can be lost, trapped, or remain on stale controls.

Conservative anti-false-skip rule:
- If focus destination behavior cannot be proven from static artifacts, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state transition/focus behavior requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected transition indicators, or clearly state absence of state-changing components when not relevant.""",
    "question_9": """You are evaluating WCAG 2.2 AA Manual Test #9: Text Resize, Reflow, and Spacing (SC 1.4.4, 1.4.10, 1.4.12 triage focus).

Primary objective:
- Decide whether this page should be manually tested for text scaling, 320px reflow behavior, and text-spacing resilience.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Page contains meaningful text content and interactive functionality.
2) Page uses responsive layouts, breakpoints, columns, sidebars, sticky regions, or adaptive components.
3) Page has dense content structures (forms, tables, cards, dashboards, nav + content compositions) that can fail at zoom/reflow.

Evidence hierarchy you MUST use:
- Screenshots across viewports are primary evidence for responsive complexity and potential clipping/overflow risk.
- HTML/CSS structure signals are secondary evidence (container complexity, layout semantics, controls density).

Decision policy (strict):
- `relevant=true` for almost all non-trivial pages with text and layout.
- `needs_manual_testing=true` when relevant=true, because this test requires live verification of:
  - text doubling behavior without loss (1.4.4),
  - 320px reflow without unnecessary horizontal scroll/loss (1.4.10),
  - increased text spacing without loss of content/functionality (1.4.12).
- Set `relevant=false` and `needs_manual_testing=false` only for genuinely minimal pages with negligible text/functionality.

High-risk indicators that should bias toward manual testing:
- Multi-column or panel layouts.
- Fixed-width containers or overflow-prone components.
- Complex nav/header/footer combinations.
- Dense forms or data-heavy UI.
- Components likely to truncate, overlap, or hide controls under zoom/spacing changes.

Conservative anti-false-skip rule:
- If reflow/spacing outcomes cannot be confidently inferred, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state zoom/reflow/spacing behavior requires manual execution.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention layout/viewport complexity signals, or clearly justify a true minimal-page exemption when not relevant.""",
    "question_10": """You are evaluating WCAG 2.2 AA Manual Test #10: Status Messages (SC 4.1.3 and related persistence risk under 2.2.1 triage focus).

Primary objective:
- Decide whether this page should be manually tested for assistive-technology status message behavior.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) UI emits success/error/progress/waiting/validation/confirmation feedback after user actions.
2) Dynamic notifications/toasts/banners/snackbars/inline status text appear without focus change.
3) Live region semantics or status roles exist (`aria-live`, `role=\"status\"`, `role=\"alert\"`, `aria-atomic`, `aria-relevant`).
4) Messages auto-dismiss or are likely transient while underlying condition may persist.

Evidence hierarchy you MUST use:
- HTML/DOM semantics are primary for detection of status-message mechanisms.
- Screenshots are supporting evidence for visible transient message patterns and timing cues.

Decision policy (strict):
- `relevant=true` if any status-message mechanism is present or strongly implied.
- `needs_manual_testing=true` when relevant=true, because manual AT validation is needed to confirm:
  - immediate announcement behavior (4.1.3),
  - message persistence vs underlying condition state,
  - equivalent persistent availability of critical status information if auto-dismiss occurs.
- Set `relevant=false` and `needs_manual_testing=false` only when no status-message patterns are detected.

High-risk indicators that should bias toward manual testing:
- Form validation flows with dynamic inline errors.
- Async actions (submit/save/upload/search) producing non-focus-shifting feedback.
- Auto-dismissing toasts/snackbars.
- Live regions with unclear announcement reliability.

Conservative anti-false-skip rule:
- If dynamic feedback behavior is uncertain, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state screen-reader announcement/persistence behavior requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected status-message mechanism(s), or clearly state none were found when not relevant.""",
    "question_11": """You are evaluating WCAG 2.2 AA Manual Test #11: Alternatives for Timed Media (SC 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5 triage focus).

Primary objective:
- Decide whether this page should be manually tested for timed-media text/audio alternatives.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Audio-only media (podcasts, narrated clips, voice-only assets).
2) Video-only media (no meaningful audio track carrying visual meaning).
3) Video with audio (prerecorded or live streams/webinars/player embeds).
4) Embedded media players or third-party media iframes indicating timed-media content.

Evidence hierarchy you MUST use:
- HTML/DOM evidence is primary:
  - `<audio>`, `<video>`, `<track>`, player embeds, media links, transcript links, caption controls.
- Screenshots are supporting evidence for visible player UI and transcript/caption affordances.

Decision policy (strict):
- `relevant=true` if any timed-media content is present or strongly implied.
- `needs_manual_testing=true` when relevant=true, because manual verification is needed to confirm:
  - transcript completeness/accuracy for audio-only or video-only alternatives,
  - caption quality and synchronization for prerecorded/live video with audio,
  - audio-description adequacy where essential visual information is present,
  - fallback transcript adequacy for visual-only essential content.
- Set `relevant=false` and `needs_manual_testing=false` only when no timed-media content exists.

High-risk indicators that should bias toward manual testing:
- Custom or third-party player components.
- Missing `<track>` elements or unclear caption state.
- Media-heavy pages (marketing hero videos, tutorials, webinars, recorded demos).
- Links labeled as transcript/captions without verifiable completeness.

Conservative anti-false-skip rule:
- If media alternatives cannot be confidently validated from artifacts, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state media alternative quality requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected media type(s) and alternative indicators (tracks/transcript/ad cues), or clearly state no timed media was found.""",
    "question_12": """You are evaluating WCAG 2.2 AA Manual Test #12: Tables (SC 1.3.1 and 4.1.2 table-structure triage focus).

Primary objective:
- Decide whether this page should be manually tested for data-table semantics and header associations.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Presence of data tables using `<table>` or ARIA table/grid roles.
2) Tabular UIs with row/column relationships (including custom table-like components).
3) Sortable columns or interactive table headers.
4) Complex/irregular/multi-level table header structures.

Evidence hierarchy you MUST use:
- HTML/DOM is primary:
  - `<table>`, `<tr>`, `<th>`, `<td>`, `scope`, `headers`, `id`, `colgroup`, `rowspan`, `colspan`,
  - ARIA roles (`table`, `grid`, `row`, `cell`, `gridcell`, `columnheader`, `rowheader`),
  - sorting semantics (`aria-sort`, accessible naming cues).
- Screenshots are secondary for confirming visible table complexity and header layout patterns.

Decision policy (strict):
- `relevant=true` if any data-table or table-like relationship exists.
- `needs_manual_testing=true` when relevant=true and human verification is needed for:
  - correct row/cell/header semantics,
  - proper scope/header association (especially irregular/multi-level tables),
  - sortable-header accessibility signaling,
  - consistency between visual table structure and semantic mapping.
- Set `relevant=false` and `needs_manual_testing=false` only when no data-table behavior exists.

High-risk indicators that should bias toward manual testing:
- ARIA table/grid implementations without native table elements.
- Multi-row/column spanning headers.
- Repeated or restructured headers across sections.
- Sortable tables with unclear `aria-sort` or naming signals.
- Data cells requiring multiple header references.

Conservative anti-false-skip rule:
- If table semantics or header mapping is uncertain, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state table association complexity requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected table type/complexity and key semantic signals, or explicitly state no table relationships were found.""",
    "question_13": """You are evaluating WCAG 2.2 AA Manual Test #13: Time Limits (SC 2.2.1 triage focus).

Primary objective:
- Decide whether this page should be manually tested for user-facing time-limit behavior.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Session timeout or inactivity expiration behavior (auth/session warnings, auto-logout prompts).
2) Countdown timers, expiring steps, time-bounded form/task completion, reservation/checkout hold timers.
3) Renewal/extend-session prompts or timeout warning dialogs.
4) Any UX where user action must occur before a timer expires.

Evidence hierarchy you MUST use:
- HTML/DOM and visible UI text are primary:
  - timeout/session keywords, timer components, warning dialogs, extension controls.
- Screenshots are supporting evidence for visible countdown/warning elements.

Decision policy (strict):
- `relevant=true` if any time-limit indicator exists or is strongly implied.
- `needs_manual_testing=true` when relevant=true because manual verification is required to confirm:
  - warning appears before expiry,
  - warning announcement accessibility (e.g., screen-reader behavior),
  - user gets sufficient time and simple mechanism to extend,
  - extension can be operated via keyboard/AT and repeated as required.
- Set `relevant=false` and `needs_manual_testing=false` only when no time-limit behavior is present.

Potential exemption clues (do NOT auto-skip solely from these):
- Real-time event constraints (auction-like behavior).
- Essential timing constraints.
- Very long limits.
Even with clues, if uncertain, retain manual testing.

High-risk indicators that should bias toward manual testing:
- Authenticated account/session pages.
- Multi-step forms with inactivity handling.
- Financial/booking/check-out workflows with hold expiration.
- Countdown banners/modals with unclear extension paths.

Conservative anti-false-skip rule:
- If timeout behavior is uncertain or partially observable, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state expiry/warning/extension behavior requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected timer/session indicators, or explicitly state none were found when not relevant.""",
    "question_14": """You are evaluating WCAG 2.2 AA Manual Test #14: Shortcuts (SC 2.1.1 and 2.1.4 triage focus).

Primary objective:
- Decide whether this page should be manually tested for custom keyboard shortcut behavior.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Custom keyboard shortcut declarations or help text (e.g., “Press /”, “Press K”, “hotkeys”, “keyboard shortcuts”).
2) Scripted key handlers likely implementing app-level shortcuts (`keydown`/`keyup` listeners, command palettes).
3) Single-key activation patterns (letter/number/symbol without modifiers) outside text-entry scope.
4) Complex web-app interfaces where shortcut conflicts with browser/AT are plausible.

Evidence hierarchy you MUST use:
- HTML/DOM/script indicators are primary for shortcut presence and likely scope.
- Screenshots are supporting evidence for shortcut UI hints or help dialogs.

Decision policy (strict):
- `relevant=true` if custom shortcuts are present or strongly implied.
- `needs_manual_testing=true` when relevant=true, because manual validation is needed to confirm:
  - no harmful conflicts with browser/screen-reader shortcuts,
  - single-key shortcuts are disabled/remappable/focus-scoped when required,
  - keyboard interaction remains operable for assistive-tech users.
- Set `relevant=false` and `needs_manual_testing=false` only when no shortcut indicators exist.

High-risk indicators that should bias toward manual testing:
- Single-key shortcuts enabled globally.
- App-like interfaces with extensive keyboard command systems.
- Missing visible controls for disabling/remapping shortcuts.
- Handlers bound at `document`/global scope without clear focus gating.

Conservative anti-false-skip rule:
- If shortcut behavior or scope is uncertain, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state shortcut conflict/scope requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected shortcut indicators and single-key risk posture, or explicitly state none were found when not relevant.""",
    "question_15": """You are evaluating WCAG 2.2 AA Manual Test #15: Motion and Gestures (SC 2.5.1, 2.5.4, 2.5.7 triage focus).

Primary objective:
- Decide whether this page should be manually tested for gesture- and motion-dependent input requirements.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Dragging-required interactions (sliders, drag-and-drop lists, canvas positioning, map panning controls, sortable boards).
2) Path-based or multipoint gesture interactions (swipe paths, pinch/zoom gestures, two-finger actions).
3) Device/user motion input usage (shake, tilt, gyroscope/accelerometer-driven controls).
4) Mobile-first interaction hints suggesting gesture-only operation.

Evidence hierarchy you MUST use:
- HTML/DOM/script indicators are primary:
  - drag handlers, pointer/touch gesture listeners, motion/orientation APIs, gesture-specific UI text.
- Screenshots are supporting evidence for gesture affordances (drag handles, swipe carousels, mobile gesture UI).

Decision policy (strict):
- `relevant=true` if any gesture/motion-dependent interaction is present or strongly implied.
- `needs_manual_testing=true` when relevant=true, because manual validation is needed to confirm:
  - equivalent single-pointer/non-path alternative exists (2.5.1, 2.5.7),
  - equivalent non-motion controls exist for motion input (2.5.4),
  - motion-based operation can be disabled when required (2.5.4).
- Set `relevant=false` and `needs_manual_testing=false` only when no gesture/motion interaction patterns are detected.

High-risk indicators that should bias toward manual testing:
- Drag-only UIs without clear click/tap alternatives.
- Swipe/pinch-dependent mobile components.
- Game-like or map-like controls with path dependence.
- Motion-controlled features with no visible fallback controls.

Conservative anti-false-skip rule:
- If equivalence/disablement cannot be confidently established from artifacts, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state gesture/motion equivalence requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention detected gesture/motion indicators and fallback/disablement uncertainty, or explicitly state none were found when not relevant.""",
    "question_16": """You are evaluating WCAG 2.2 AA Manual Test #16: Target Size (SC 2.5.8 triage focus).

Primary objective:
- Decide whether this page should be manually tested for pointer target size and spacing adequacy.
- This is applicability + manual-check triage, not final conformance.

Applicability triggers (any one makes it relevant):
1) Presence of clickable/tappable controls or links that may be smaller than 24x24 CSS px.
2) Dense UI clusters with adjacent controls (icon toolbars, compact navs, data-table action columns, card action chips).
3) Mobile/touch-oriented views where small targets are likely problematic.
4) Custom controls whose hit area is unclear from semantics alone.

Evidence hierarchy you MUST use:
- Screenshots are primary for visual target density and adjacency risk.
- HTML/DOM is supporting evidence for control types, interactive semantics, and potential user-agent-sized exceptions.

Decision policy (strict):
- `relevant=true` if actionable pointer targets are present (most interactive pages).
- `needs_manual_testing=true` when relevant=true, because manual inspection is needed to verify:
  - target dimensions meet 24x24 expectations, or
  - valid exceptions apply (inline text link context, user-agent sized controls, equivalent control, spacing exception).
- Set `relevant=false` and `needs_manual_testing=false` only when there are effectively no actionable pointer targets.

High-risk indicators that should bias toward manual testing:
- Small icon-only buttons/links.
- Tight spacing between adjacent controls.
- Dense toolbar/action menus.
- Complex responsive layouts where controls shrink at smaller viewports.

Exception handling posture:
- Do not assume exceptions apply unless evidence clearly supports them.
- If exception applicability is uncertain, keep manual testing required.

Conservative anti-false-skip rule:
- If size/spacing cannot be confidently determined from available artifacts, choose:
  - `relevant=true`
  - `needs_manual_testing=true`
  - reason should state target-size/spacing requires manual verification.

Reason-writing requirements:
- Keep reason concise (1-3 sentences), concrete, and evidence-based.
- Mention key target-density/size indicators and exception uncertainty, or explicitly state no actionable targets were found when not relevant.""",
}


def get_question_prompt(question_id: str) -> str:
    return QUESTION_SPECIFIC_PROMPTS.get(
        question_id,
        "You are evaluating a manual accessibility test. Determine relevance and whether manual validation is required.",
    )
