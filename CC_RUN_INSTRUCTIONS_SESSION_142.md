# CC_RUN_INSTRUCTIONS_SESSION_142.md
# Session 142 — Run Instructions for Claude Code

**Date:** March 2026
**Specs in this session:** 3 code/review specs + 1 docs spec
**Full test suite runs:** 1 (after all code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_142.md, then run these specs in order: CC_SPEC_142_A_THUMBNAIL_PROXY_REVIEW.md, CC_SPEC_142_B_141D_CLOSURE_AND_GALLERY_LIGHTBOX.md, CC_SPEC_142_C_P3_BATCH.md, CC_SPEC_142_D_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE (files reviewed before session)

The following have been verified and require NO code changes:
- ✅ `proxy_image_thumbnail` view exists in `upload_api_views.py`
- ✅ `api/bulk-gen/image-proxy/` wired in `urls.py`
- ✅ `prompt_detail.html` lightbox: `overlay.appendChild(closeBtn)` correct
- ✅ `lightbox.css`: `.lightbox-close` has `position: absolute; top: 16px`
- ✅ `openai_provider.py`: `images.edit()` correctly implemented

The following still need fixing:
- ❌ `bulk-generator-gallery.js`: close button still in `inner`, caption present
- ❌ `bulk-generator.js`: thumb.src not using image proxy
- ❌ `bulk-generator.js`: single-box ✕ clear missing B2 delete
- ❌ `upload_api_views.py`: download proxy missing `X-Content-Type-Options`
- ❌ `openai_provider.py`: 141-D protocol violation needs formal agent closure

---

## 📋 SPEC QUEUE

| Order | Spec | Type | Code Changes | Review Only |
|-------|------|------|-------------|-------------|
| **1** | `CC_SPEC_142_A_THUMBNAIL_PROXY_REVIEW.md` | Code+Review | `bulk-generator.js` (1 str_replace) | `upload_api_views.py`, `urls.py` |
| **2** | `CC_SPEC_142_B_141D_CLOSURE_AND_GALLERY_LIGHTBOX.md` | Code+Review | `bulk-generator-gallery.js` | `openai_provider.py`, `prompt_detail.html`, `lightbox.css` |
| **3** | `CC_SPEC_142_C_P3_BATCH.md` | Code+Docs | `bulk-generator.js` (1 str_replace), `upload_api_views.py` (1 str_replace), `CLAUDE.md` | — |
| **4** | `CC_SPEC_142_D_DOCS_UPDATE.md` | Docs | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` | — |

---

## ⚠️ FILE BUDGET

`bulk-generator.js` — appears in Specs A and C:
- Spec A: 1 str_replace (thumb.src → image proxy)
- Spec C: 1 str_replace (single-box ✕ B2 delete)
- **Total: 2 str_replace calls — at the 🟠 High Risk limit**

`upload_api_views.py` — appears in Specs A and C:
- Spec A: verify/confirm only (no str_replace)
- Spec C: 1 str_replace (nosniff on download proxy)
- **Total: 1 str_replace — within limit**

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_142_A_THUMBNAIL_PROXY_REVIEW.md`
1. Read spec fully
2. Complete Step 0 greps
3. Step 1: Verify `proxy_image_thumbnail` matches spec requirements
   (it exists — verify, don't duplicate)
4. Step 2: Update `thumb.src` in blur handler (str_replace 1 of 2 on
   `bulk-generator.js`)
5. Step 3: MANDATORY verification gate
6. PRE-AGENT SELF-CHECK including WCAG 1.4.11
7. 5 agents: @security-auditor, @backend-security-coder,
   @threat-modeling-expert, @frontend-developer, @accessibility-expert
8. `python manage.py check` — 0 issues
9. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_142_B_141D_CLOSURE_AND_GALLERY_LIGHTBOX.md`
1. Read spec fully — read Confirmed Current State above
2. Complete Step 0 greps — read gallery.js carefully (old structure confirmed)
3. Part A: Run @django-pro and @python-pro on openai_provider.py (no
   code changes — review and confirm)
4. Part B: Fix createLightbox in gallery.js (close on overlay, no caption)
5. Part B: Fix openLightbox — remove caption lines
6. Part B: Verify prompt_detail.html and lightbox.css (no changes needed)
7. Step 1: MANDATORY verification greps
8. PRE-AGENT SELF-CHECK including WCAG 1.4.11
9. 6 agents: @django-pro, @python-pro, @frontend-developer,
   @accessibility-expert, @frontend-security-coder, @code-reviewer
10. `python manage.py test prompts.tests.test_bulk_generator`
11. `python manage.py check` — 0 issues
12. **DO NOT COMMIT**

---

### SPEC 3 — `CC_SPEC_142_C_P3_BATCH.md`
1. Read spec fully
2. Complete Step 0 greps
3. Step 1: Single-box ✕ B2 delete (str_replace 2 of 2 on `bulk-generator.js`)
4. Step 2: nosniff on download proxy (str_replace 1 of 1 on
   `upload_api_views.py`)
5. Step 3: images.edit() note in CLAUDE.md
6. Step 4: MANDATORY verification greps
7. PRE-AGENT SELF-CHECK
8. 5 agents: @frontend-developer, @javascript-pro, @security-auditor,
   @django-pro, @code-reviewer
9. `python manage.py check` — 0 issues
10. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after Specs 1-3 agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9–10 → commit in order
- Fails → most likely Spec A (blur handler change) or Spec B (gallery.js)
  → fix in-place max 2 attempts → if unresolved, stop and report

---

### SPEC 4 — `CC_SPEC_142_D_DOCS_UPDATE.md` (after code specs committed)
1. Complete Step 0 greps
2. Add Session 142 changelog, update CLAUDE.md
3. 2 agents: @docs-architect, @api-documenter
4. Per v2.2: if below 8.0 → fix and re-run
5. Commit immediately after confirmed scores

---

## 💾 COMMIT ORDER

```
1. feat(bulk-gen): thumbnail proxy STRIDE reviewed, thumb.src routes through proxy
2. fix(lightbox): gallery.js close on overlay, caption removed; 141-D formally closed
3. fix(bulk-gen): single-box clear B2 delete, nosniff on download proxy, SDK note
4. END OF SESSION DOCS UPDATE: session 142
```

---

## ⛔ HARD RULES

1. `bulk-generator.js` — 2 str_replace calls maximum (Specs A and C)
2. Do NOT add a second `proxy_image_thumbnail` — it already exists
3. Spec B: `openai_provider.py`, `prompt_detail.html`, `lightbox.css`
   are review-only — no code changes unless agents find genuine issues
4. 141-D must be explicitly stated as closed in Spec B Section 3
5. Lightbox fix verification: `overlay.appendChild(closeBtn)` must appear
   in grep output — `inner.appendChild` means the fix failed
6. Per v2.2: docs spec requires confirmed scores before committing

---

## 🔢 EXPECTED FINAL STATE

| Item | Expected |
|------|----------|
| Tests | 1193+ passing, 12 skipped, 0 failures |
| Thumbnail proxy | STRIDE complete, 12 controls confirmed |
| thumb.src | Routes through `/api/bulk-gen/image-proxy/` |
| 141-D | Formally closed, confirmed 8.0+ from both agents |
| gallery.js lightbox | Close button on overlay, no caption |
| prompt_detail.html lightbox | Already correct — confirmed |
| lightbox.css | Already correct — confirmed |
| Single-box ✕ clear | Fires B2 delete before clearing field |
| Download proxy | X-Content-Type-Options: nosniff added |
| CLAUDE.md | images.edit() SDK note documented |

---

## 🔔 REMINDER FOR DEVELOPER (Mateo)

After Session 142 please test:
1. Type Wikipedia ant URL → blur → thumbnail appears ✅
2. Type PromptHero Next.js URL → blur → thumbnail appears ✅
3. Paste image → click ✕ → Heroku logs show `[PASTE-DELETE]` ✅
4. Open lightbox on results page → × is top-right, not on image ✅
5. Resize to mobile → × stays top-right ✅

---

**END OF RUN INSTRUCTIONS**
