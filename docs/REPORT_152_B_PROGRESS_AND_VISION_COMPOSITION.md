# REPORT_152_B_PROGRESS_AND_VISION_COMPOSITION.md

**Spec:** CC_SPEC_152_B_PROGRESS_AND_VISION_COMPOSITION.md
**Session:** 152-B
**Date:** April 5, 2026

---

## Section 1 — Overview

The bulk AI image generator's progress bar showed 0% when users refreshed the page immediately after starting a job. This occurred because images start in `queued` status before Django-Q picks them up, and the progress query only counted `completed` and `generating` statuses (from the 152-A fix). Additionally, the Vision "Prompt from Image" feature produced spatially inaccurate prompts — subjects appeared on the wrong side of the frame, depth relationships were lost, background people were omitted, decorative details were skipped, and background blur was hallucinated.

Both issues were in `bulk_generator_views.py`. The progress bar fix replaced the explicit status filter with `exclude(status='failed')` to count all non-failed images. The Vision system prompt was completely rewritten with explicit frame-position vocabulary (LEFT/RIGHT/CENTRE from viewer's perspective), depth-layer instructions (FOREGROUND/MIDGROUND/BACKGROUND), background crowd requirements, decorative detail instructions, and an explicit anti-blur directive.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Progress bar uses `exclude(status='failed')` instead of `filter(status__in=[...])` | ✅ Met |
| Vision system prompt includes frame-position language (LEFT/RIGHT/CENTRE) | ✅ Met |
| Vision system prompt includes depth/layering (FOREGROUND/MIDGROUND/BACKGROUND) | ✅ Met |
| Vision system prompt includes background crowd instruction | ✅ Met |
| Vision system prompt includes decorative details instruction | ✅ Met |
| Vision system prompt includes explicit anti-blur/bokeh directive | ✅ Met |
| "RECREATE" instruction still present and prominent | ✅ Met |
| `ignore_watermark_rule` and `no_watermark_output_rule` still correctly placed | ✅ Met |
| `detail: 'high'` not reverted | ✅ Met |

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py

**Progress bar fix (line 100-104):**
- Replaced `job.images.filter(status__in=['completed', 'generating']).count()` with `job.images.exclude(status='failed').count()`
- Added 4-line comment explaining the rationale (counts queued + generating + completed, future-proof)

**Vision system prompt replacement (lines 788-853):**
- Completely replaced the `system_prompt = (...)` block
- Added frame-position analysis instruction: "State whether subjects appear on the LEFT side, RIGHT side, or CENTRE of the image frame. This is critical — left/right must be from the viewer's perspective, not the subjects'."
- Added depth/layering analysis instruction: "explicitly describe who or what is in the FOREGROUND (closest to viewer), MIDGROUND, and BACKGROUND"
- Added "ALL people in the scene" analysis instruction: "do not skip background figures"
- Added decorative details analysis instruction: "describe ALL visible accessories, patterns, embroidery, jewellery, and ornamental details"
- Added background sharpness instruction: "State explicitly whether the background is IN SHARP FOCUS or BLURRED. Do not add blur that is not in the image."
- Added frame-position rule: "LEFT, RIGHT, CENTRE refers to the image frame from the viewer's perspective — never relative to another subject"
- Added depth rule with example: '"The man stands slightly behind and to the right of the woman" is correct. "The man and woman stand together" loses depth.'
- Added anti-blur rule: "NEVER add depth-of-field blur or bokeh unless it is clearly present in the source image"
- Added background crowd rule: "Describe ALL people visible in the scene — including background crowd, bystanders, and distant figures"
- Added clothing detail rule with example: '"White flowing dress with intricate gold and teal embroidery at the neckline" not "white dress"'
- Added hair/jewellery rule: "Describe hair decorations, jewellery, and accessories on every person — do not omit them"

**Step 3 verification grep outputs:**

Grep 1 — exclude query in place:
```
104:    live_completed_count = job.images.exclude(status='failed').count()
107:        (live_completed_count / total_images_for_percent) * 100, 1
118:        'live_completed_count': live_completed_count,
```

Grep 2 — key phrases present:
```
798: CENTRE of the image frame
801: FOREGROUND (closest to viewer), MIDGROUND, and BACKGROUND
809: ALL people in the scene: do not skip background figures
831: image frame from the viewer's perspective
837: NEVER add depth-of-field blur or bokeh unless it is clearly
839: Describe ALL people visible in the scene — including background
```

Grep 3 — RECREATE present:
```
789: Your goal is to RECREATE
829: RECREATE, do not reinterpret. Describe what is there.
```

Grep 4 — watermark rules conditional:
```
775: ignore_watermark_rule = (
782: no_watermark_output_rule = (
849: + ignore_watermark_rule
850: + no_watermark_output_rule +
```

Grep 5 — detail:high in place:
```
860: 'detail': 'high',  # High detail preserves spatial accuracy for faithful recreation
```

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. Both edits applied cleanly via str_replace.

## Section 5 — Remaining Issues

**Issue:** @django-pro flagged that `exclude(status='failed')` would silently count any future status values (e.g. `cancelled`, `paused`) toward progress.
**Recommended fix:** If new statuses are added in the future, revisit the progress bar query to determine whether the new status should count toward progress. The current four-status enum (`queued`, `generating`, `completed`, `failed`) is well-defined and the exclude approach is correct for it.
**Priority:** P3
**Reason not resolved:** The spec explicitly mandates `exclude(status='failed')` over `filter(status__in=[...])`. The concern is hypothetical — no new statuses are planned. The spec author chose exclude intentionally for the future-proof benefit.

**Issue:** @code-reviewer noted that the polling API returns `completed_count` (only truly completed images), while the template initial value now counts all non-failed images. This creates a brief visual mismatch on page load for in-progress jobs (1-3 seconds before first poll corrects it).
**Recommended fix:** Consider aligning the polling API's `completed_count` to use the same semantics, or accept the brief mismatch as a UX trade-off (showing "something happening" is better than 0%).
**Priority:** P3
**Reason not resolved:** The mismatch is self-correcting within 1-3 seconds and the 0% bug was a worse UX problem.

## Section 6 — Concerns and Areas for Improvement

**Concern:** Variable name `live_completed_count` no longer accurately describes its semantics (it now counts non-failed images, not just completed ones).
**Impact:** Could confuse future maintainers reading the code.
**Recommended action:** Consider renaming to `live_progress_count` in a future cleanup pass. Low priority — the comment above the line explains the intent clearly.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 7.0/10 | Suggests explicit `filter(status__in=[...])` over `exclude` for future-proofing risk. Confirmed ORM correctness and ordering. | No — spec mandates `exclude(status='failed')` and rejects `filter(status__in=[...])`. Concern documented in Section 5. |
| 1 | @python-pro | 9.5/10 | String concatenation correct, watermark rules properly conditional, no stale sentences from old prompt. Minor maintainability note on paired watermark rules. | No action needed — all checks pass. |
| 1 | @code-reviewer | 8.5/10 | All 5 production failures addressed. Noted polling API semantic mismatch (brief, self-correcting). Confirmed `detail: 'high'` in place. | No action needed — mismatch documented in Section 5. |
| **Average** | | **8.33/10** | | **Pass >= 8.0** |

**Note on @django-pro 7.0 score:** The agent's suggested fix (`filter(status__in=['queued', 'generating', 'completed'])`) directly contradicts the spec's explicit requirement to use `exclude(status='failed')`. The spec states work will be rejected if `filter(status__in=[...])` is used. The agent's concern about hypothetical future statuses is documented but does not warrant a code change.

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The changes are backend-only (no CSS, no templates, no accessibility surface).

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test --verbosity=0
# Result: Ran 1213 tests in 1195s — OK (skipped=12), 0 failures
```

**Manual browser checks (developer):**

1. **Progress bar** — Start generation with 3+ prompts → refresh page IMMEDIATELY (before any images finish) → bar should show >0% right away (all images are queued = counted by exclude query)

2. **Vision frame position** — Use "Prompt from Image" feature → paste a multi-person family photo → Vision="Yes", no direction → Generate → verify the generated prompt describes:
   - Subjects on correct LEFT/RIGHT side of frame
   - Depth relationships (who is in front/behind)
   - Background people/crowd if present
   - Background sharpness accurately described
   - Decorative details (accessories, jewellery, embroidery)

## Section 10 — Commits

| Hash | Message |
|------|---------|
| c3a1c71 | fix(bulk-gen): progress bar exclude-failed query, Vision composition accuracy |

## Section 11 — What to Work on Next

1. **Production Vision accuracy testing** — Run the Vision feature on the specific family painting test case to confirm spatial accuracy improvements. This is the primary validation for the prompt changes.
2. **Polling API alignment** — Consider updating `get_job_status` to return a `progress_count` that uses `exclude(status='failed')` to match the template initial value, eliminating the brief mismatch on page load.
3. **Variable rename** — Rename `live_completed_count` to `live_progress_count` in a future cleanup pass to match its new semantics.
