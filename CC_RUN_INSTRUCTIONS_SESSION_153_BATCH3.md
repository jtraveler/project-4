# CC_RUN_INSTRUCTIONS_SESSION_153_BATCH3.md
# Session 153 Batch 3 — Run Instructions for Claude Code

**Date:** April 2026
**Specs in this batch:** 3 (1 feature + 1 cleanup + 1 docs)
**Full test suite runs:** 1 (after both code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_153_BATCH3.md, then run these specs in order: CC_SPEC_153_K_JS_COST_TEMPLATE.md, CC_SPEC_153_L_CLEANUP_BATCH3.md, CC_SPEC_153_M_DOCS_ARCHIVE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE

- ✅ `get_image_cost()` helper exists in `constants.py` (153-J)
- ✅ `I.COST_MAP` in `bulk-generator.js` lines 97-101 hardcoded — Spec K replaces with template context
- ✅ `_apply_generation_result` signature still has dead `IMAGE_COST_MAP` param — Spec L removes
- ✅ `_run_generation_loop` signature still has dead `IMAGE_COST_MAP` param — Spec L removes
- ✅ `get_image_cost()` fallback is hardcoded `0.034` — Spec L makes dynamic
- ✅ `loading-spinner` rule duplicated at CSS lines 528 and 1058 — Spec L removes duplicate
- ✅ `test_integrity_error_triggers_uuid_suffix_retry` missing `needs_seo_review` assert — Spec L adds it
- ✅ CLAUDE.md is 2184 lines and has ~45 Recently Completed entries — Spec M archives oldest

---

## 📋 SPEC QUEUE

| Order | Spec | Type | Key Files |
|-------|------|------|-----------|
| **1** | `CC_SPEC_153_K_JS_COST_TEMPLATE.md` | Code | `views/bulk_generator_views.py`, `bulk_generator.html`, `bulk-generator.js` |
| **2** | `CC_SPEC_153_L_CLEANUP_BATCH3.md` | Code | `tasks.py`, `constants.py`, `bulk-generator-job.css`, `test_bulk_page_creation.py` |
| **3** | `CC_SPEC_153_M_DOCS_ARCHIVE.md` | Docs | `CLAUDE.md`, new `CLAUDE_ARCHIVE_COMPLETED.md` |

---

## ⚠️ FILE BUDGET

**`prompts/tasks.py`** — appears in Spec L:
- Remove `IMAGE_COST_MAP` from 2 function signatures + 2 call sites + 1 import
- **Tier: 🔴 CRITICAL — Python script approach (not sed, too many related changes)**

**`static/js/bulk-generator.js`** — appears in Spec K:
- Replace hardcoded `I.COST_MAP` with parsed template JSON
- **Check `wc -l` in Step 0**

**`CLAUDE.md`** — appears in Spec M:
- **Tier: 🔴 CRITICAL — archive rows from Recently Completed table only**
- Maximum 2 str_replace calls

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_153_K_JS_COST_TEMPLATE.md`
1. Read spec fully
2. Step 0 greps — find bulk generator GET view, confirm template data attrs
3. Add `cost_map_json` to view context
4. Add `data-cost-map` attribute to template
5. Replace `I.COST_MAP` init with JSON parse from data attribute
6. `python manage.py check` — 0 issues
7. `python manage.py collectstatic --noinput`
8. Agents: @frontend-developer, @django-security, @code-reviewer
9. All ≥ 8.0 → partial report
10. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_153_L_CLEANUP_BATCH3.md`
1. Read spec fully
2. Step 0 greps
3. Remove dead IMAGE_COST_MAP parameter (Python script)
4. Dynamic fallback in constants.py
5. Remove duplicate CSS rule
6. Add IntegrityError retry test assertion
7. Add inline pattern comments
8. `python manage.py check` — 0 issues
9. Agents: @code-reviewer, @tdd-orchestrator
10. All ≥ 8.0 → partial report
11. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after Specs K and L agent-approved)

```bash
python manage.py test
```

Expected: 1226+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9-10 → commit in order
- Fails → identify which spec introduced regression → fix in-place

---

### SPEC 3 — `CC_SPEC_153_M_DOCS_ARCHIVE.md` (Docs — commits immediately per v2.2)
1. Read spec fully
2. Step 0 greps
3. Create `CLAUDE_ARCHIVE_COMPLETED.md` with archived rows
4. Remove archived rows from CLAUDE.md Recently Completed table
5. 2 agents: @docs-architect, @api-documenter
6. Both ≥ 8.0 → commit immediately

---

## 💾 COMMIT ORDER

```
1. feat(bulk-gen): inject IMAGE_COST_MAP into template context — JS pricing never drifts from Python
2. refactor(bulk-gen): cleanup batch 3 — dead IMAGE_COST_MAP param, dynamic fallback, CSS dedup, tests
3. docs: archive oldest CLAUDE.md Recently Completed entries to CLAUDE_ARCHIVE_COMPLETED.md
```

---

## ⛔ AGENT NAME RULE (Enforced)

Use EXACT agent names from each spec. Authorised substitutions for this batch only:
- `@django-security` → `@backend-security-coder`
- `@tdd-coach` → `@tdd-orchestrator`
- `@accessibility-expert` → `@ui-visual-validator`

Document any substitution in Section 7.

---

**END OF RUN INSTRUCTIONS**
