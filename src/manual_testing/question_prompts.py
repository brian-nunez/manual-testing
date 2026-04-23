from __future__ import annotations

QUESTION_SPECIFIC_PROMPTS: dict[str, str] = {
    "question_1": """Evaluate Automatic Behavior on the current page state.

Focus checks:
- Auto-updating content (carousels, feeds, live regions, rotating banners).
- Moving, blinking, or scrolling content that persists longer than 5 seconds.
- Flashing content frequency risk.

Evidence rules:
- Use both HTML and screenshots.
- Prioritize time-sequence screenshots to detect motion/updates over time.
- If time-sequence frames show visible changes without user interaction, treat automatic behavior as present.

Decision guidance:
- relevant=true only if there is plausible automatic update/motion/flashing behavior.
- needs_manual_testing=true if relevant behavior appears and human validation is needed for pause/stop/hide/control or flash safety thresholds.
- If no indicators of automatic behavior exist, set relevant=false and needs_manual_testing=false.

Reason requirements:
- Mention concrete evidence (specific element patterns, changing frames, or absence of indicators).""",
    "question_2": """Evaluate Page Meaning (reading sequence and hidden static content).

Focus checks:
- Whether content order in DOM and structure likely supports correct screen reader reading sequence.
- Whether static informative content might be hidden from assistive tech or intentionally hidden visually.

Evidence rules:
- Use semantic structure from HTML (`main`, headings, regions, landmarks, DOM ordering).
- Flag only when sequence/visibility issues are plausible from provided artifacts.

Decision guidance:
- relevant=true for almost all content pages with meaningful static content.
- needs_manual_testing=true when sequence/hidden-content behavior requires assistive-tech verification.
- If page is too minimal/no static content context, relevant can be false.

Reason requirements:
- Cite structural indicators and why a screen-reader pass is or is not needed.""",
    "question_3": """Evaluate Page Structure.

Focus checks:
- Heading hierarchy continuity.
- Existence and correctness of main-content targeting (`<main>`/`role=main`/skip links).
- Grouping and identification of navigation link sets.

Evidence rules:
- Use heading tags, landmarks, skip-link patterns, and nav/list/menu semantics.
- If structure appears custom or ambiguous, preserve need for manual verification.

Decision guidance:
- relevant=true when page has headings, main content, or navigation groups (typical pages).
- needs_manual_testing=true when structure quality needs human confirmation or patterns look risky.
- relevant=false only for pages lacking meaningful structure/navigation content.

Reason requirements:
- Mention which structural patterns were found or missing.""",
    "question_4": """Evaluate Interactive Elements.

Focus checks:
- Focus order completeness and focus traps.
- Focus-triggered side effects and hover/focus content behavior.
- Keyboard/mouse parity and expected widget key interactions.
- Accessible name vs visible label consistency.

Evidence rules:
- Use HTML interactive controls and ARIA roles as indicators.
- Presence of custom widgets/events implies manual interaction is required.

Decision guidance:
- relevant=true if any interactive controls/widgets exist.
- needs_manual_testing=true for most interactive pages because keyboard/focus behavior needs live validation.
- relevant=false only when page has no meaningful interactive controls.

Reason requirements:
- Reference detected interactive controls and why manual keyboard/focus testing is needed or not.""",
    "question_5": """Evaluate Static Content accessibility concerns.

Focus checks:
- Link differentiation in body text.
- Informative graphics and non-text contrast risk.
- Placeholder text contrast where placeholder conveys meaning.
- Image maps, aria-hidden misuse, and role=presentation misuse.

Evidence rules:
- Use HTML patterns (`<a>`, `<img>`, `<map>/<area>`, aria-hidden, role=presentation).
- If color/contrast cannot be reliably proven from artifacts, keep manual testing as needed.

Decision guidance:
- relevant=true when links/graphics/placeholders/aria-hidden/presentation patterns appear.
- needs_manual_testing=true when visual differentiation/contrast or semantic intent needs human judgment.
- relevant=false if none of these patterns appear.

Reason requirements:
- Mention specific content types detected and what requires verification.""",
    "question_6": """Evaluate Sensory Characteristics.

Focus checks:
- Instructions or cues relying only on color.
- Instructions requiring visual characteristics (shape/location/orientation).
- Instructions requiring auditory characteristics.

Evidence rules:
- Use instructional text and UI messaging in HTML/screenshots.
- If instruction semantics are ambiguous, preserve manual verification.

Decision guidance:
- relevant=true when user instructions or status cues are present.
- needs_manual_testing=true when potential sensory-dependent instructions/cues exist.
- relevant=false when no instruction-like content is present.

Reason requirements:
- Call out detected instruction patterns and dependence risks.""",
    "question_7": """Evaluate Forms (Input Purpose / autocomplete).

Focus checks:
- Presence of user-information form fields.
- Whether autocomplete attributes exist and plausibly match input purposes.

Evidence rules:
- Use HTML input/select/textarea types, names, labels, and autocomplete attributes.
- If user-data fields exist without clear autocomplete purpose mapping, testing is needed.

Decision guidance:
- relevant=true when user-data form fields are present.
- needs_manual_testing=true when autocomplete intent/compliance requires review.
- relevant=false when no user-data forms exist.

Reason requirements:
- Mention form field evidence and autocomplete signal quality.""",
    "question_8": """Evaluate Focus Management during page-state transitions.

Focus checks:
- Components that open dialogs/drawers/menus/new states.
- Whether focus is likely moved or retained meaningfully after activation.

Evidence rules:
- Use trigger elements, modal/dialog patterns, aria-expanded, hidden toggles, role=dialog.
- Dynamic state behavior cannot be fully inferred statically; favor manual validation when present.

Decision guidance:
- relevant=true when state-transition components exist.
- needs_manual_testing=true when focus movement after activation must be validated with keyboard.
- relevant=false if page appears fully static with no transition components.

Reason requirements:
- Point to transition component indicators and resulting need for manual focus checks.""",
    "question_9": """Evaluate Text Resize, Reflow, and Spacing.

Focus checks:
- Behavior at zoom changes and narrow viewport (320px).
- Breakpoint transitions and possible loss of content/functionality.
- Text-spacing tolerance.

Evidence rules:
- Use responsive layout clues from screenshots across viewports.
- If responsive behavior exists, manual validation is usually required.

Decision guidance:
- relevant=true for most non-trivial pages with layout/content.
- needs_manual_testing=true when zoom/reflow/spacing outcomes require live interaction and breakpoint checks.
- relevant=false only for trivial/minimal pages with no meaningful content.

Reason requirements:
- Reference responsive complexity and why manual reflow/spacing checks are needed or not.""",
    "question_10": """Evaluate Status Messages.

Focus checks:
- Presence of transient feedback/status/error/success/wait/progress messages.
- Whether those messages likely rely on assistive-tech announcement timing.

Evidence rules:
- Use live-region patterns (`aria-live`, role=status/alert) and UI messaging clues.
- Announcement behavior requires screen-reader validation when status messaging exists.

Decision guidance:
- relevant=true when status messages or equivalent dynamic feedback mechanisms are present.
- needs_manual_testing=true when immediate announcement/disappearance behavior must be verified.
- relevant=false if no status-message patterns are present.

Reason requirements:
- Mention detected status-message cues and expected screen-reader checks.""",
    "question_11": """Evaluate Alternatives for Timed Media.

Focus checks:
- Audio-only, video-only, prerecorded multimedia, and live media.
- Presence/quality indicators for transcripts, captions, and audio descriptions.

Evidence rules:
- Use media tags, embeds, transcript links, caption tracks, and nearby text alternatives.
- Quality/accuracy of alternatives usually requires manual review when media exists.

Decision guidance:
- relevant=true if timed media is present or strongly implied.
- needs_manual_testing=true when transcript/caption/audio-description sufficiency must be validated.
- relevant=false if no timed media is present.

Reason requirements:
- Cite media evidence and missing/uncertain alternative indicators.""",
    "question_12": """Evaluate Tables.

Focus checks:
- Data table semantics: rows/cells/headers/scope/roles.
- Sortable table accessibility signaling (`aria-sort`, accessible naming).
- Complex header associations (`headers`, `aria-labelledby`, IDs).

Evidence rules:
- Use table markup (`table`, `th`, `td`, roles, scope, headers, colgroup).
- For irregular/multi-level structures, manual verification is often required.

Decision guidance:
- relevant=true when data tables or table/grid roles are present.
- needs_manual_testing=true if structural/header association correctness is uncertain or complex.
- relevant=false when no data tables appear.

Reason requirements:
- Mention specific table patterns found and verification needs.""",
    "question_13": """Evaluate Time Limits.

Focus checks:
- Session timeouts, countdowns, expiring actions, or renewal prompts.
- Exemptions and extension mechanisms.
- Warning announcement/accessibility behavior.

Evidence rules:
- Use timeout messaging, timers, auth/session hints, and interactive renewal UI clues.
- Actual expiry/warning behavior requires live manual validation when time limits appear.

Decision guidance:
- relevant=true when timeout or timer behavior is present/plausible.
- needs_manual_testing=true when warnings/extensions/keyboard+SR operability must be verified.
- relevant=false if no time-limit signals exist.

Reason requirements:
- Identify timeout evidence or absence of it.""",
    "question_14": """Evaluate Keyboard Shortcuts.

Focus checks:
- Presence of custom keyboard shortcuts.
- Single-key shortcut behavior and conflict risk.

Evidence rules:
- Use keyboard shortcut hints in UI text/help/handlers.
- Shortcut conflict/remapping/focus scoping generally requires manual testing.

Decision guidance:
- relevant=true when custom shortcuts are present or likely.
- needs_manual_testing=true when shortcut behavior must be validated.
- relevant=false if no shortcut indicators are found.

Reason requirements:
- Mention shortcut evidence and any single-key risk indicators.""",
    "question_15": """Evaluate Motion and Gestures.

Focus checks:
- Dragging, path-based, multipoint, device-motion, or user-motion input.
- Existence of equivalent single-pointer or non-motion alternatives.
- Motion disablement.

Evidence rules:
- Use gesture-related controls, drag handles, swipe instructions, motion API cues.
- Interaction equivalence and disablement usually require manual testing.

Decision guidance:
- relevant=true when motion/gesture-dependent interactions are present.
- needs_manual_testing=true when alternatives/disable controls must be confirmed.
- relevant=false when no motion/gesture patterns appear.

Reason requirements:
- Describe detected gesture/motion indicators and manual verification rationale.""",
    "question_16": """Evaluate Target Size.

Focus checks:
- Interactive targets likely smaller than 24x24 px.
- Exception cases (inline text links, user-agent sized controls, equivalent or spacing exceptions).
- Dependencies on prior automated findings for role issues.

Evidence rules:
- Use screenshots and HTML control sizes/classes as indicators.
- Exact target dimensions and spacing exceptions often require manual inspection.

Decision guidance:
- relevant=true when page contains interactive controls/links where target size could be an issue.
- needs_manual_testing=true when target-size or exception validation is required.
- relevant=false when no actionable interactive targets exist.

Reason requirements:
- Mention control density/size cues and why manual target-size validation is or is not needed.""",
}


def get_question_prompt(question_id: str) -> str:
    return QUESTION_SPECIFIC_PROMPTS.get(
        question_id,
        "Evaluate this manual accessibility test using the provided criteria and evidence.",
    )
