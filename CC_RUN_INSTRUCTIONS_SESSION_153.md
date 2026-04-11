# CC_RUN_INSTRUCTIONS_SESSION_153.md
# Session 153 — Run Instructions for Claude Code

**Date:** April 2026
**Specs in this session:** 2 code specs
**Full test suite runs:** 1 (after both code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_153.md, then run these specs in order: CC_SPEC_153_A_GPT_IMAGE_15_UPGRADE.md, CC_SPEC_153_B_PROGRESS_BAR_REFRESH.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE (files reviewed before session)

The following have been verified and require NO changes beyond what the specs describe:
- ✅ `openai_provider.py`: `images.edit()` at line ~132 and `images.generate()` at line ~140 use `model='gpt-image-1'` — Spec A updates both to `gpt-image-1.5`
- ✅ `models.py`: `AI_GENERATOR_CHOICES` has `('gpt-image-1', 'GPT-Image-1')` — Spec A adds the 1.5 entry after it
- ✅ `models.py`: `model_name` and `generator_category` defaults are `'gpt-image-1'` — Spec A updates both
- ✅ `tasks.py`: 4 occurrences of `ai_generator='gpt-image-1'` at lines ~3280, ~3317, ~3528, ~3585 — Spec A updates via sed
- ✅ `bulk_generator.html`: `gpt-image-1` option present with `selected` — Spec A adds 1.5 option as new default
- ✅ Progress bar main counter (`data-completed-count`) confirmed working — NOT the subject of Spec B
- ✅ `bulk-generator-ui.js`: `updateSlotToGenerating` creates CSS animation from 0% on every call — Spec B adds first-render guard
- ✅ `bulk-generator-polling.js`: `initPage` correctly seeds `G.initialCompleted` — Spec B adds `G.isFirstRenderPass` flag here

The following need fixing:
- ❌ `openai_provider.py`: API calls still use `gpt-image-1` — Spec A
- ❌ `models.py`, `tasks.py`, `bulk_generation.py`, `bulk_generator_views.py`, `bulk_generator.html`: all reference `gpt-image-1` as active model — Spec A
- ❌ `bulk-generator-ui.js` + `bulk-generator-polling.js`: per-image progress animation restarts from 0% on page refresh — Spec B

---

## 📋 SPEC QUEUE

| Order | Spec | Type | Key Files | Migration |
|-------|------|------|-----------|-----------|
| **1** | `CC_SPEC_153_A_GPT_IMAGE_15_UPGRADE.md` | Code | `openai_provider.py`, `models.py`, `tasks.py`, `bulk_generation.py`, `bulk_generator_views.py`, `bulk_generator.html`, test files | ✅ Yes (choices-only + defaults) |
| **2** | `CC_SPEC_153_B_PROGRESS_BAR_REFRESH.md` | Code | `bulk-generator-ui.js`, `bulk-generator-polling.js` | ❌ No |

---

## ⚠️ FILE BUDGET

**`models.py`** — appears in Spec A:
- Spec A: 2 str_replace calls (add choice + update 2 defaults)
- **Tier: 🔴 CRITICAL — 2000+ lines. Maximum 2 str_replace calls.**

**`tasks.py`** — appears in Spec A:
- Spec A: use `sed` (not str_replace) — 4 identical string changes
- **Tier: 🔴 CRITICAL — 3500+ lines. DO NOT use str_replace. sed only.**

**`bulk_generator_views.py`** — appears in Spec A:
- Spec A: up to 3 str_replace calls (lines ~173, ~421, ~1308)
- **Check `wc -l` in Step 0 to confirm tier before editing.**

**`bulk-generator-ui.js`** — appears in Spec B:
- Spec B: 2 str_replace calls
- **Check `wc -l` in Step 0 to confirm tier.**

**`bulk-generator-polling.js`** — appears in Spec B:
- Spec B: 1 str_replace call
- **Check `wc -l` in Step 0 to confirm tier.**

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_153_A_GPT_IMAGE_15_UPGRADE.md`
1. Read spec fully before touching any file
2. Complete ALL Step 0 greps — verify line numbers match
3. Update `openai_provider.py` — 2 API call strings
4. Update `models.py` — add choice + 2 defaults (2 str_replace max)
5. Update `tasks.py` — use sed, verify 0 old occurrences remain
6. Update `bulk_generation.py` — 1 default parameter
7. Update `bulk_generator_views.py` — 3 hardcoded defaults
8. Update `bulk_generator.html` — add 1.5 option, move `selected`
9. Run `python manage.py makemigrations --name upgrade_gpt_image_15`
10. Run `python manage.py migrate`
11. Update tests — Category A only (see spec); Category B unchanged
12. Add 2 new choice tests
13. PRE-AGENT SELF-CHECK
14. 4 agents: @code-reviewer, @django-security, @tdd-coach, @accessibility-auditor
15. `python manage.py check` — 0 issues
16. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_153_B_PROGRESS_BAR_REFRESH.md`
1. Read spec fully before touching any file
2. Complete ALL Step 0 greps
3. Add `G.isFirstRenderPass = true` flag in `bulk-generator-polling.js` `initPage`
4. Update `renderImages` in `bulk-generator-ui.js` to clear the flag after first pass
5. Update `updateSlotToGenerating` in `bulk-generator-ui.js` to skip animation on first pass
6. PRE-AGENT SELF-CHECK
7. 3 agents: @frontend-developer, @accessibility-expert, @code-reviewer
8. `python manage.py check` — 0 issues
9. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after both specs agent-approved)

```bash
python manage.py test
```

Expected: 1215+ tests, 0 failures, 12 skipped.
(Baseline: 1213 passing. Spec A adds 2 new choice tests = 1215 minimum.)

- **Passes** → fill Sections 9–10 on both reports → commit in order
- **Fails** → most likely Spec A test updates (Category A/B mix-up) or migration issue
  → fix in-place max 2 attempts → if unresolved, stop and report

---

## 💾 COMMIT ORDER

```
1. feat(bulk-gen): upgrade image generation to GPT-Image-1.5 — API calls, choices, defaults, tests, migration
2. fix(bulk-gen): per-image progress animation no longer restarts from 0% on page refresh
```

---

## ⛔ HARD RULES

1. **`tasks.py`** — use `sed` only. No str_replace. CRITICAL tier.
2. **`models.py`** — maximum 2 str_replace calls. CRITICAL tier.
3. **DO NOT remove `gpt-image-1` option from the template dropdown** — keep it as non-default
4. **DO NOT backfill existing `BulkGenerationJob` records** — old jobs stay as `gpt-image-1`
5. **DO NOT change Category B tests** — they test backward compatibility
6. **DO NOT commit until developer confirms browser test AND full suite passes**
7. **Spec B is a UI behavioural fix only** — no backend changes, no migration

---

## 🔢 EXPECTED FINAL STATE

| Item | Expected |
|------|----------|
| Tests | 1215+ passing, 12 skipped, 0 failures |
| `openai_provider.py` | Both `images.edit()` and `images.generate()` use `model='gpt-image-1.5'` |
| `AI_GENERATOR_CHOICES` | Both `gpt-image-1` and `gpt-image-1.5` present |
| `model_name` default | `'gpt-image-1.5'` |
| `generator_category` default | `'gpt-image-1.5'` |
| `tasks.py` `ai_generator` | All 4 occurrences use `'gpt-image-1.5'` |
| Template dropdown | GPT-Image-1.5 selected by default; GPT-Image-1 still present |
| Migration | `00XX_upgrade_gpt_image_15.py` applied cleanly |
| Per-image progress animation | Does not restart from 0% on page refresh |
| `G.isFirstRenderPass` | Cleared after first `renderImages` call completes |

---

## 🔔 REMINDER FOR DEVELOPER (Mateo)

After Session 153 please test:
1. Open bulk generator → model dropdown shows GPT-Image-1.5 selected ✅
2. GPT-Image-1 still visible in dropdown (not removed) ✅
3. Start a generation job → confirm images generate successfully ✅
4. During generation, refresh the page → per-image cards show spinner only (no fake 0% animation bar) ✅
5. After refresh, progress bar shows correct count (not 0%) ✅

---

**END OF RUN INSTRUCTIONS**
