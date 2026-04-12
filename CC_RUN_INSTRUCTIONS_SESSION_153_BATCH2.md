# CC_RUN_INSTRUCTIONS_SESSION_153_BATCH2.md
# Session 153 Batch 2 — Run Instructions for Claude Code

**Date:** April 2026
**Specs in this batch:** 4 (1 docs + 3 code)
**Full test suite runs:** 1 (after all code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_153_BATCH2.md, then run these specs in order: CC_SPEC_153_G_DOCS_UPDATE.md, CC_SPEC_153_H_NEEDS_SEO_REVIEW.md, CC_SPEC_153_I_CLEANUP_BATCH.md, CC_SPEC_153_J_PRICE_HELPER.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE

The following have been verified before this batch was written:

- ✅ `needs_seo_review` field exists on `Prompt` model (line 880)
- ✅ `needs_seo_review = True` set in single-upload pipeline (lines 1437, 1538)
- ✅ `needs_seo_review` NOT set in `create_prompt_pages_from_job` (the bug — Spec H)
- ✅ `spinLoader` animation NOT in `prefers-reduced-motion` block (line 485/527)
- ✅ `_fire_quota_alert_notification` body says "quota ran out" (line 3709)
- ✅ Billing check uses string match only — no `hasattr(e, 'code')` guard
- ✅ `openai_provider.py` class and method docstrings still say "GPT-Image-1"
- ✅ `tasks.py` lines ~3323 and ~3591 still say "GPT-Image-1" in comments
- ✅ Test method `test_vision_called_with_gpt_image_1` at line 756
- ✅ Safari ISO fix needed in `bulk-generator-ui.js` line ~196
- ✅ `IMAGE_COST_MAP.get().get()` duplicated across 3 Python call sites
- ✅ `IMAGE_COST_MAP` imported locally in `tasks.py` at line 2915

---

## 📋 SPEC QUEUE

| Order | Spec | Type | Key Files |
|-------|------|------|-----------|
| **1** | `CC_SPEC_153_G_DOCS_UPDATE.md` | Docs | CLAUDE.md, CLAUDE_CHANGELOG.md, PROJECT_FILE_STRUCTURE.md |
| **2** | `CC_SPEC_153_H_NEEDS_SEO_REVIEW.md` | Code | `prompts/tasks.py` |
| **3** | `CC_SPEC_153_I_CLEANUP_BATCH.md` | Code | `openai_provider.py`, `tasks.py`, `test_bulk_page_creation.py`, `bulk-generator-ui.js`, `bulk-generator-job.css` |
| **4** | `CC_SPEC_153_J_PRICE_HELPER.md` | Code | `constants.py`, `openai_provider.py`, `tasks.py`, `bulk_generator_views.py` |

---

## ⚠️ FILE BUDGET

**`prompts/tasks.py`** — appears in Specs H, I, and J:
- **Spec H:** sed — add `needs_seo_review=True` + fix comment at line ~3323
- **Spec I:** sed — fix comment at ~3591, fix notification text at ~3709
- **Spec J:** sed — update cost call at ~2663
- **All changes are at non-overlapping line ranges — no conflicts**
- **Tier: 🔴 CRITICAL (3500+ lines). sed ONLY for all three specs.**

**`prompts/services/image_providers/openai_provider.py`** — appears in Specs I and J:
- **Spec I:** billing hardening + docstring fixes (2-3 str_replace)
- **Spec J:** price helper call site (1 str_replace)
- **Total: 3-4 str_replace — within ✅ SAFE tier**

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_153_G_DOCS_UPDATE.md` (Docs — commits immediately per v2.2)
1. Read spec fully
2. Step 0 greps
3. Update CLAUDE.md, CLAUDE_CHANGELOG.md, PROJECT_FILE_STRUCTURE.md
4. `python manage.py check` — 0 issues
5. 2 agents: @docs-architect, @api-documenter
6. Both ≥ 8.0 → commit immediately
7. **Commit immediately after confirmed scores (docs spec rule)**

---

### SPEC 2 — `CC_SPEC_153_H_NEEDS_SEO_REVIEW.md`
1. Read spec fully
2. Step 0 greps — confirm ALL Prompt creation sites in bulk pipeline
3. Add `needs_seo_review=True` via sed
4. Fix stale GPT-Image-1 comment at ~3323 via sed
5. `python manage.py check` — 0 issues
6. Agents: @django-security, @tdd-coach, @code-reviewer
7. All ≥ 8.0 → write partial report (Sections 1-8, 11)
8. **DO NOT COMMIT**

---

### SPEC 3 — `CC_SPEC_153_I_CLEANUP_BATCH.md`
1. Read spec fully
2. Step 0 greps
3. Fix spinLoader CSS
4. Fix quota notification text via sed
5. Fix stale GPT-Image-1 comment at ~3591 via sed
6. Billing check hardening in openai_provider.py
7. Fix stale docstrings in openai_provider.py
8. Rename test method
9. Safari ISO fix in bulk-generator-ui.js
10. `python manage.py check` — 0 issues
11. Agents: @code-reviewer, @accessibility-expert, @django-security
12. All ≥ 8.0 → write partial report
13. **DO NOT COMMIT**

---

### SPEC 4 — `CC_SPEC_153_J_PRICE_HELPER.md`
1. Read spec fully
2. Step 0 greps
3. Add `get_image_cost()` helper to `constants.py`
4. Update 3 call sites
5. `python manage.py check` — 0 issues
6. Agents: @code-reviewer, @tdd-coach
7. All ≥ 8.0 → write partial report
8. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after Specs H, I, J agent-approved)

```bash
python manage.py test
```

Expected: 1221+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9-10 on all 3 reports → commit in order
- Fails → identify which spec introduced regression → fix in-place → re-run

---

## 💾 COMMIT ORDER

```
1. END OF SESSION DOCS UPDATE: session 153
2. fix(bulk-gen): set needs_seo_review=True on bulk-created prompt pages
3. fix(bulk-gen): cleanup batch — CSS a11y, billing hardening, stale comments, test rename, Safari fix
4. refactor(bulk-gen): introduce get_image_cost() helper, eliminate duplicated price lookups
```

---

## ⛔ HARD RULES

1. **`tasks.py`** — sed ONLY for all three specs that touch it. NEVER str_replace.
2. **`needs_seo_review=True`** must be verified at ALL Prompt creation sites in the bulk pipeline — not just the one mentioned in the spec
3. **Do NOT commit code specs until full suite passes**
4. **Docs spec (153-G) commits immediately** per protocol v2.2

---

## ⛔ CRITICAL: AGENT NAME RULE (NEW — Apply This Session)

**USE THE EXACT AGENT NAMES FROM EACH SPEC. DO NOT SUBSTITUTE.**

Previous sessions have seen CC substitute agent names (e.g. using
`@backend-security-coder` when the spec says `@django-security`,
`@ui-visual-validator` when the spec says `@accessibility-expert`).
This is a protocol violation. From this session forward:

- If the spec says `@django-security` → use `@django-security`
- If the spec says `@accessibility-expert` → use `@accessibility-expert`
- If the spec says `@tdd-coach` → use `@tdd-coach`
- If an agent is not available → stop and report, do NOT substitute

---

**END OF RUN INSTRUCTIONS**
