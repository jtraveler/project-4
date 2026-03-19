# CC_RUN_INSTRUCTIONS_SESSION_139.md
# Session 139 — Run Instructions for Claude Code

**Date:** March 2026
**Specs in this session:** 3 code specs + 2 docs specs
**Full test suite runs:** 1 (after all 3 code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_139.md, then run these specs in order: CC_SPEC_139_A_SOURCE_IMAGE_CARD_REDESIGN.md, CC_SPEC_139_B_GLOBAL_LIGHTBOX.md, CC_SPEC_139_C_RESULTS_PAGE_FIXES.md, CC_SPEC_139_D_NEW_FEATURES_DOCS.md, CC_SPEC_139_E_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_139_A_SOURCE_IMAGE_CARD_REDESIGN.md` | Code | `prompt_detail.html`, `prompt-detail.css`, `tasks.py` |
| **2** | `CC_SPEC_139_B_GLOBAL_LIGHTBOX.md` | Code | `bulk-generator-gallery.js`, `bulk-generator-job.css`, `prompt_detail.html`, `prompt-detail.css` |
| **3** | `CC_SPEC_139_C_RESULTS_PAGE_FIXES.md` | Code | `bulk-generator-job.css`, `bulk_generator.html` |
| **4** | `CC_SPEC_139_D_NEW_FEATURES_DOCS.md` | Docs | `CLAUDE.md` |
| **5** | `CC_SPEC_139_E_DOCS_UPDATE.md` | Docs | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` |

---

## ⚠️ CRITICAL ORDERING — Spec A before Spec B

Spec A removes the Bootstrap modal and wires `openSourceImageLightbox()` which
calls `window.openPromptDetailLightbox`. Spec B defines `window.openPromptDetailLightbox`.
Both must commit before the feature works end-to-end — but Spec A must run
first since it sets up the caller side.

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_139_A_SOURCE_IMAGE_CARD_REDESIGN.md`
1. Read spec, complete Step 0 greps
2. Step 1: Merge source credit + source image into one rail-card
3. Step 2: Add source image CSS to prompt-detail.css
4. Step 3: WebP conversion in `_upload_source_image_to_b2`
5. PRE-AGENT SELF-CHECK → 4 agents: @frontend-developer, @django-pro, @ux-ui-designer, @security-auditor
6. `python manage.py check` — 0 issues
7. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_139_B_GLOBAL_LIGHTBOX.md`
1. Read spec, complete Step 0 greps
2. Step 1: Remove caption from results page lightbox
3. Step 2: Add `openPromptDetailLightbox` to prompt_detail.html
4. Step 3: Wrap hero image with zoom container
5. Step 4: Add hero image zoom CSS
6. Step 5: Copy lightbox CSS to prompt-detail.css
7. PRE-AGENT SELF-CHECK → 3 agents: @frontend-developer, @ux-ui-designer, @accessibility
8. `python manage.py check` — 0 issues
9. **DO NOT COMMIT**

---

### SPEC 3 — `CC_SPEC_139_C_RESULTS_PAGE_FIXES.md`
1. Read spec, complete Step 0 greps — read CURRENT CSS state from disk
2. Step 1: Remove `.prompt-image-slot:hover .btn-select` hover rule
3. Step 2: Set 2:3 as active default in bulk_generator.html
4. Step 3: `clearAllConfirm` paste cleanup
5. Step 4: P3 micro-cleanup (redundant filter, published lightbox guard, border opacity, docstring)
6. PRE-AGENT SELF-CHECK → 3 agents: @frontend-developer, @ux-ui-designer, @accessibility
7. `python manage.py check` — 0 issues
8. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after Specs 1-3 agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9–10 → commit in order
- Fails → most likely Spec A (tasks.py Pillow change) → fix, max 2 attempts

---

### SPEC 4 — `CC_SPEC_139_D_NEW_FEATURES_DOCS.md` (after code specs committed)
1. Read spec, complete Step 0 greps
2. Add 4 feature sections to CLAUDE.md
3. PRE-AGENT SELF-CHECK → 1 agent: @docs-architect
4. **Per v2.1: if below 8.0 → fix and re-run**
5. Commit immediately after confirmed score

---

### SPEC 5 — `CC_SPEC_139_E_DOCS_UPDATE.md` (after Spec 4 committed)
1. Read spec, complete Step 0 greps
2. Verify 138-C CSS fixes, add Session 139 entry
3. PRE-AGENT SELF-CHECK → 1 agent: @docs-architect
4. **Per v2.1: if below 8.0 → fix and re-run**
5. Commit immediately after confirmed score

---

## 💾 COMMIT ORDER

```
1. feat(prompt-detail): merged source card, zoom lightbox, 180px thumb, WebP conversion
2. feat(lightbox): global lightbox — remove caption from results, add to hero image, open-in-new-tab
3. fix(results): btn-select hover isolation, 2:3 default dimension, clear-all paste cleanup, P3 batch
4. docs: planned new features — translate, vision prompt gen, watermark removal, save draft
5. END OF SESSION DOCS UPDATE: session 139 — source card, lightbox, results fixes, 138-C closed
```

---

## ⛔ HARD RULES

1. `tasks.py` is 🔴 Critical — 1 str_replace call max (Spec A, Step 3)
2. `prompt_detail.html` is 🟡 Caution — appears in Specs A and B. Track
   str_replace calls: Spec A uses the source cards section; Spec B uses the
   hero image and script sections. No overlap — safe if carefully anchored.
3. `bulk-generator-job.css` is 🟡 Caution — Spec B uses 1 call (caption CSS),
   Spec C uses 1 call (btn-select hover). Total: 2 calls.
4. WebP conversion in Spec A must NEVER cause `_upload_source_image_to_b2` to
   fail — wrap fully in try/except, upload original bytes on Pillow failure
5. Spec B must NOT remove lightbox CSS from `bulk-generator-job.css` — copy only
6. Per v2.1: both docs specs require confirmed (not projected) agent scores

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected |
|--------|----------|
| Tests | 1193+ passing, 12 skipped, 0 failures |
| Source card | One row: credit left, image right |
| Source image | 180×180px, WebP, click opens lightbox |
| Hero image | Magnifying glass on hover, click opens lightbox |
| Results lightbox | No prompt text caption |
| Prompt detail lightbox | "Open in new tab" button |
| btn-select | Only reacts to direct hover on circle |
| Default dimension | 2:3 (1024×1536) |
| New features | Documented in CLAUDE.md |
| 138-C | Confirmed closed |

---

## 🔔 REMINDER FOR DEVELOPER (Mateo)

After Session 139, please test all outstanding items:

**From Sessions 135–138 (still pending):**
1–9: (same as Session 138 run instructions)

**New from Session 139:**
10. Source card — one row, credit + image side by side
11. Source image thumbnail — hover shows magnifying glass, click opens lightbox
12. Hero image — hover shows magnifying glass, click opens lightbox
13. Lightbox on results page — verify NO prompt text/caption appears
14. Lightbox on prompt detail — verify "Open in new tab" link present
15. btn-select — image hover does NOT trigger check mark; direct circle hover does
16. New bulk gen job — default dimension is 2:3
17. Generate with paste source image — check B2 for WebP format

---

**END OF RUN INSTRUCTIONS**
