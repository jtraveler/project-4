# CC_RUN_INSTRUCTIONS_SESSION_143.md
# Session 143 — Run Instructions for Claude Code

**Date:** March 2026
**Specs in this session:** 1 docs spec + 3 code specs
**Full test suite runs:** 1 (after all code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_143.md, then run these specs in order: CC_SPEC_143_A_DOCS_SAFEGUARD_D.md, CC_SPEC_143_B_PENDING_SWEEP_AND_RATE_LIMIT.md, CC_SPEC_143_C_QUOTA_ERROR_AND_NOTIFICATION.md, CC_SPEC_143_D_INPUT_JS_SPLIT.md`

---

## READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## CONFIRMED CURRENT STATE (verified before session)

- tasks.py: `_run_generation_loop()` exists, returns `(completed_count, failed_count, total_cost)`
- tasks.py: `process_bulk_generation_job()` calls `_run_generation_loop()` then `job.refresh_from_db()`
- settings.py: `BULK_GEN_MAX_CONCURRENT` exists, no `OPENAI_INTER_BATCH_DELAY` yet
- models.py: `NOTIFICATION_TYPES` includes `bulk_gen_partial` as last bulk gen type
- openai_provider.py: `RateLimitError` handler returns `error_type='rate_limit'` for ALL rate limit errors
- bulk_generation.py: `_sanitise_error_message()` has `'quota'` bundled into rate limit check
- bulk-generator-config.js: `_getReadableErrorReason()` at ~line 108, no `'Quota exceeded'` mapping
- bulk-generator.js: 1685 lines, single IIFE, no `BulkGenInput` namespace
- Tests: 1193 passing, 12 skipped

---

## SPEC QUEUE

| Order | Spec | Type | High Risk Files | Notes |
|-------|------|------|----------------|-------|
| **1** | `CC_SPEC_143_A_DOCS_SAFEGUARD_D.md` | Docs | None | Commits immediately |
| **2** | `CC_SPEC_143_B_PENDING_SWEEP_AND_RATE_LIMIT.md` | Code | `tasks.py` (2 str_replace) | D1 sweep + D3 delay |
| **3** | `CC_SPEC_143_C_QUOTA_ERROR_AND_NOTIFICATION.md` | Code | `tasks.py` (2 str_replace), `models.py` (1) | Depends on 143-B |
| **4** | `CC_SPEC_143_D_INPUT_JS_SPLIT.md` | Code | `bulk-generator.js` (rewrite) | JS split, no logic changes |

---

## FILE BUDGET

**`prompts/tasks.py`** — appears in Specs B and C:
- Spec B: 2 str_replace (D1 sweep + D3 delay)
- Spec C: 2 str_replace (quota routing + notification call) + 1 append (helper function)
- **Total: 4 str_replace + 1 append — each spec treated as separate budget**

**`prompts/models.py`** — appears in Spec C:
- Spec C: 1 str_replace (add notification type)
- **Total: 1 — within limit**

**`static/js/bulk-generator.js`** — appears in Spec D:
- Spec D: Full rewrite (create-new strategy)
- **No str_replace — use Write tool to create new files**

---

## EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_143_A_DOCS_SAFEGUARD_D.md` (Docs — commits immediately)
1. Read spec fully
2. Complete Step 0 greps
3. Add all 3 text blocks to CLAUDE.md verbatim
4. `python manage.py check` — 0 issues
5. PRE-AGENT SELF-CHECK
6. 2 agents: @docs-architect, @api-documenter → both 8.0+
7. Write FULL report (all 11 sections)
8. **Commit immediately** (docs spec — no full suite needed)

---

### SPEC 2 — `CC_SPEC_143_B_PENDING_SWEEP_AND_RATE_LIMIT.md`
1. Read spec fully — note tasks.py is CRITICAL tier
2. Complete ALL 10 Step 0 greps — read `_run_generation_loop()` in full
3. str_replace 1: D1 pending sweep after `_run_generation_loop()` returns
4. str_replace 2: D3 inter-batch delay at end of batch loop
5. Add `OPENAI_INTER_BATCH_DELAY` to settings.py
6. Write 4 tests
7. `python manage.py check` — 0 issues
8. PRE-AGENT SELF-CHECK
9. 6 agents → all 8.0+
10. Write PARTIAL report (Sections 1-8 and 11)
11. **DO NOT COMMIT — HOLD state**

---

### SPEC 3 — `CC_SPEC_143_C_QUOTA_ERROR_AND_NOTIFICATION.md`
**DEPENDENCY:** Spec B must be agent-reviewed and in HOLD state first.

1. Read spec fully
2. Complete ALL 10 Step 0 greps
3. File 1: Update openai_provider.py RateLimitError handler (quota detection)
4. File 2: Update bulk_generation.py sanitiser (split quota from rate limit)
5. File 3: tasks.py — add `_fire_quota_alert_notification()` at bottom,
   then 2 str_replace (quota routing + notification call)
6. File 4: models.py — add `openai_quota_alert` to NOTIFICATION_TYPES
7. File 5: Run `makemigrations` + `migrate`
8. File 6: Update bulk-generator-config.js reasonMap
9. Write 6 tests
10. `python manage.py check` — 0 issues
11. PRE-AGENT SELF-CHECK
12. 7 agents → all 8.0+
13. Write PARTIAL report (Sections 1-8 and 11)
14. **DO NOT COMMIT — HOLD state**

---

### SPEC 4 — `CC_SPEC_143_D_INPUT_JS_SPLIT.md`
1. Read spec fully
2. Complete ALL Step 0 greps — build cross-reference table of shared vars
3. Create `bulk-generator-generation.js` (new file, ~620 lines)
4. Create `bulk-generator-autosave.js` (new file, ~360 lines)
5. Rewrite `bulk-generator.js` (remove extracted sections, add namespace, ~750 lines)
6. Update `bulk_generator.html` script tags (add 2 new entries)
7. Run MANDATORY VERIFICATION greps
8. `python manage.py check` — 0 issues
9. PRE-AGENT SELF-CHECK
10. 4 agents → all 8.0+
11. Write PARTIAL report (Sections 1-8 and 11)
12. **DO NOT COMMIT — HOLD state**

---

## FULL SUITE GATE (after Specs 2-4 agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests (Spec B adds 4, Spec C adds 6), 0 failures, 12 skipped.

- Passes → fill Sections 9-10 → commit in order (B, C, D)
- Fails → identify which spec introduced regression:
  - Spec B: likely in D1 sweep or D3 delay
  - Spec C: likely in quota routing or migration
  - Spec D: likely in namespace references (JS split)
  → fix in-place, max 2 attempts → if unresolved, stop and report

---

### SPEC 1 commits immediately (docs).
### SPECS 2-4 commit after suite passes, in order:

---

## COMMIT ORDER

```
1. docs: add safeguard section D, rate limit compliance note, quota architecture (Session 143)
   ← Spec A — committed immediately after agents pass

2. fix: D1 pending image sweep + D3 rate limit inter-batch delay (Session 143)
   ← Spec B — after full suite

3. feat: quota error distinct from rate limit, bell notification on quota kill (Session 143)
   ← Spec C — after full suite

4. refactor: split bulk-generator.js (1685 lines) into 3 modules via BulkGenInput namespace
   ← Spec D — after full suite
```

---

## HARD RULES

1. **tasks.py** — Specs B and C each get their own str_replace budget (2 each)
2. **Spec C depends on Spec B** — do not start C until B is in HOLD state
3. **Spec D: NO str_replace on bulk-generator.js** — use Write tool (create-new strategy)
4. **Spec D: main file MUST be under 800 lines** after split
5. **Per v2.2:** all agent scores 8.0+ individually
6. **Docs spec (A)** commits immediately — does not wait for full suite
7. **DO NOT combine any two specs into one commit**
8. **DO NOT modify bulk-generator.js in any spec other than D**
   (Spec C modifies `bulk-generator-config.js` — different file)

---

## SESSION BUDGET NOTE

This session has 1 docs + 3 high-risk code specs. Per CLAUDE.md guidelines,
high-risk specs count as 2 toward the session total (1 + 2 + 2 + 2 = 7).
This exceeds the typical 4-5 session limit. However:
- Spec D (JS split) has zero logic changes — it is a mechanical restructure
- Spec A is docs-only
- The actual new logic is concentrated in Specs B and C

If CC encounters quality degradation (agent scores trending below 8.0 on
Spec D), stop after committing Specs B and C and defer Spec D to Session 144.

---

## EXPECTED FINAL STATE

| Item | Expected |
|------|----------|
| Tests | 1203+ passing (1193 + 4 from B + 6 from C), 12 skipped, 0 failures |
| CLAUDE.md | Safeguard Section D + Key Learnings + Quota architecture |
| tasks.py | D1 sweep, D3 delay, quota routing, quota notification helper |
| openai_provider.py | Quota detection in RateLimitError handler |
| bulk_generation.py | 'Quota exceeded' separate from 'Rate limit reached' |
| models.py | `openai_quota_alert` in NOTIFICATION_TYPES |
| Migration | 0074 (or next sequential) for notification type change |
| bulk-generator-config.js | 'Quota exceeded' in reasonMap |
| bulk-generator.js | ~750 lines with BulkGenInput namespace |
| bulk-generator-generation.js | NEW — ~620 lines |
| bulk-generator-autosave.js | NEW — ~360 lines |
| bulk_generator.html | 5 script tags (utils, paste, main, generation, autosave) |

---

## REMINDER FOR DEVELOPER (Mateo)

**BEFORE this session runs, set in Heroku:**
```
heroku config:set BULK_GEN_MAX_CONCURRENT=1 --app mj-project-4
```
This is the immediate mitigation for the rate limit breach. Do NOT wait
for D3 — set it now.

**After Session 143, test:**
1. Run a 4-prompt job → verify all 4 complete or show "Not generated" (no blank "queued")
2. Check Heroku logs for `[D1-SWEEP]` entries if any images fail
3. Check Heroku logs for `[D3-RATE-LIMIT]` entries between batches
4. Exhaust a test key's quota → verify "Quota exceeded" in gallery (not "Rate limit")
5. Check bell notification for quota alert
6. Load bulk generator input page → verify all UI works after JS split

---

**END OF RUN INSTRUCTIONS**
