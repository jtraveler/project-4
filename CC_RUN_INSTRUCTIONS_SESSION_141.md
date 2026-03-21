# CC_RUN_INSTRUCTIONS_SESSION_141.md
# Session 141 — Run Instructions for Claude Code

**Date:** March 2026
**Specs in this session:** 4 code specs + 1 docs spec
**Full test suite runs:** 1 (after all 4 code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_141.md, then run these specs in order: CC_SPEC_141_A_DOWNLOAD_AND_BLUR_THUMBNAIL.md, CC_SPEC_141_B_CLEAR_ALL_AND_SINGLE_BOX_RESET.md, CC_SPEC_141_C_LIGHTBOX_CLOSE_BUTTON_FIX.md, CC_SPEC_141_D_REFERENCE_IMAGE_FIX.md, CC_SPEC_141_E_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 🚨 CRITICAL SESSION WARNING — RECURRING BUGS

Specs A, B, and C address bugs that have been attempted in previous sessions
and reported as fixed but remained broken in the browser. The root cause each
time was CC verifying code was written without verifying behaviour works.

**Each of these specs has a MANDATORY VERIFICATION GATE** (Step 5 in Spec A,
Step 3 in Spec B, Step 6 in Spec C) that CC must pass before running agents.
These gates are not optional. A spec that does not show verification grep
output in its report will be rejected regardless of agent scores.

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched | Risk |
|-------|-----------|------|---------------|------|
| **1** | `CC_SPEC_141_A_DOWNLOAD_AND_BLUR_THUMBNAIL.md` | Code | `upload_api_views.py`, `urls.py`, `bulk-generator-selection.js`, `bulk-generator.js` | Mixed |
| **2** | `CC_SPEC_141_B_CLEAR_ALL_AND_SINGLE_BOX_RESET.md` | Code | `bulk-generator.js` | 🟠 High Risk |
| **3** | `CC_SPEC_141_C_LIGHTBOX_CLOSE_BUTTON_FIX.md` | Code | `bulk-generator-gallery.js`, `prompt_detail.html`, `bulk-generator-job.css`, `prompt-detail.css`, `lightbox.css` (new) | Mixed |
| **4** | `CC_SPEC_141_D_REFERENCE_IMAGE_FIX.md` | Code | `openai_provider.py` | ✅ Safe |
| **5** | `CC_SPEC_141_E_DOCS_UPDATE.md` | Docs | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` | ✅ Safe |

---

## ⚠️ FILE BUDGET — `bulk-generator.js`

`bulk-generator.js` appears in Specs A and B:
- Spec A: 1 str_replace call (blur thumbnail)
- Spec B: 2 str_replace calls (clearAllConfirm + single-box clear)
- **Total: 3 calls across 2 specs**

This is above the per-spec limit of 2 but acceptable across separate specs
with distinct anchors. Track usage carefully. If any str_replace fails to
match its anchor, stop and report.

`bulk-generator-job.css` appears in Spec C:
- Spec C: 2 str_replace calls (lightbox-close, reduced-motion)
- Within limit ✅

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_141_A_DOWNLOAD_AND_BLUR_THUMBNAIL.md`
1. Read spec fully — read the "Why these bugs keep recurring" section
2. Complete Step 0 greps
3. Step 1: Create proxy endpoint in `upload_api_views.py`
4. Step 2: Wire URL in `urls.py`
5. Step 3: Update `handleDownload` in `bulk-generator-selection.js`
6. Step 4: Fix blur handler in `bulk-generator.js` (str_replace call 1 of 1)
7. **⛔ MANDATORY: Complete Step 5 verification gate — all checks must pass,
   show all grep outputs in report**
8. PRE-AGENT SELF-CHECK
9. 5 agents: @frontend-developer, @security-auditor, @django-pro, @accessibility, @code-reviewer
10. `python manage.py check` — 0 issues
11. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_141_B_CLEAR_ALL_AND_SINGLE_BOX_RESET.md`
1. Read spec fully
2. Complete Step 0 greps — read the clearAllConfirm handler carefully
3. Step 1: Replace clearAllConfirm handler (str_replace call 1 of 2)
4. Step 2: Fix single-box ✕ clear (str_replace call 2 of 2)
5. **⛔ MANDATORY: Complete Step 3 verification gate — both greps must pass**
6. PRE-AGENT SELF-CHECK
7. 3 agents: @frontend-developer, @security-auditor, @code-reviewer
8. `python manage.py check` — 0 issues
9. **DO NOT COMMIT**

---

### SPEC 3 — `CC_SPEC_141_C_LIGHTBOX_CLOSE_BUTTON_FIX.md`
1. Read spec fully — read the "IMPORTANT: READ CURRENT STATE" warning
2. Complete Step 0 greps — confirm actual current state before writing anything
3. Step 1: Fix `createLightbox` in gallery.js
4. Step 2: Fix `createPdLightbox` in prompt_detail.html
5. Step 3: Update lightbox CSS in bulk-generator-job.css (2 str_replace calls)
6. Step 4: Apply same CSS to prompt-detail.css
7. Step 5: Create lightbox.css component file and link in templates
8. **⛔ MANDATORY: Complete Step 6 verification gate**
9. PRE-AGENT SELF-CHECK including WCAG 1.4.11 on close button
10. 4 agents: @frontend-developer, @ux-ui-designer, @accessibility, @code-reviewer
11. `python manage.py check` — 0 issues
12. **DO NOT COMMIT**

---

### SPEC 4 — `CC_SPEC_141_D_REFERENCE_IMAGE_FIX.md`
1. Read spec fully
2. Complete Step 0 greps — identify download pattern and SDK version
3. Step 1: Update `generate()` to pass reference image as BytesIO
4. **⛔ MANDATORY: Complete Step 2 verification gate**
5. PRE-AGENT SELF-CHECK
6. 3 agents: @django-pro, @security-auditor, @code-reviewer
7. `python manage.py test prompts.tests.test_bulk_generator` — 0 failures
8. `python manage.py check` — 0 issues
9. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after all 4 code specs agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9–10 → commit in order
- Fails → most likely Spec D (new API call pattern) or Spec A (new endpoint)
  → fix in-place max 2 attempts → if unresolved, stop and report

---

### SPEC 5 — `CC_SPEC_141_E_DOCS_UPDATE.md` (after code specs committed)
1. Complete Step 0 greps
2. Add Session 141 changelog, update docs
3. 1 agent: @docs-architect
4. Per v2.2: if below 8.0 → fix and re-run
5. Commit immediately after confirmed score

---

## 💾 COMMIT ORDER

```
1. fix(bulk-gen): download via server-side proxy (CORS), blur thumbnail preview restored
2. fix(bulk-gen): clear-all B2 cleanup ordering hardened, single-box clear thumb reset
3. fix(lightbox): close button absolutely positioned on overlay, caption removed, CSS extracted
4. fix(bulk-gen): pass reference image to GPT-Image-1 API (was silently ignored)
5. END OF SESSION DOCS UPDATE: session 141 — download proxy, blur thumbnail, lightbox fix, reference image
```

---

## ⛔ HARD RULES

1. **Verification gates are mandatory** — Spec A Step 5, Spec B Step 3,
   Spec C Step 6 must all pass before agents run. Show grep outputs in reports.
2. `bulk-generator.js` — 3 str_replace calls total across Specs A and B
3. `bulk-generator-job.css` — 2 str_replace calls (Spec C only)
4. Reference image download failure must NEVER fail generation (non-fatal only)
5. Download proxy must validate URL domain before fetching (SSRF prevention)
6. Close button must be `position: absolute` on the overlay in BOTH lightboxes
7. Per v2.2: docs spec requires confirmed agent score before committing

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected |
|--------|----------|
| Tests | 1193+ passing, 12 skipped, 0 failures |
| Download button | Downloads via `/api/bulk-gen/download/` proxy |
| Blur thumbnail | Shows preview for valid typed URLs |
| Clear All | Collects URLs before clearing, resets all paste state |
| Single-box ✕ | Resets thumb.src and onerror |
| Lightbox × button | `position: absolute` top-right on overlay always |
| Lightbox caption | Completely removed from results page lightbox |
| Lightbox CSS | Centralised in `static/css/components/lightbox.css` |
| Reference image | Passed to GPT-Image-1 as BytesIO object |

---

## 🔔 REMINDER FOR DEVELOPER (Mateo)

After Session 141, these must be tested:
1. Download → file saves to Downloads folder (not opens in browser)
2. Type valid image URL → tab away → thumbnail appears
3. Paste image → Clear All → Heroku logs show `[PASTE-DELETE]`
4. Click ✕ on a prompt with paste → thumbnail disappears
5. Open lightbox on results page → × is top-right, NOT below image
6. Open lightbox on prompt detail → × is top-right, "Open in new tab" below image
7. Mobile: open either lightbox → × stays at top-right
8. Generate with reference image → Heroku logs show `[REF-IMAGE] Attached` →
   generated image reflects the reference person/character

---

**END OF RUN INSTRUCTIONS**
