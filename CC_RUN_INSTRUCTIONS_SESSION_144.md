# CC_RUN_INSTRUCTIONS_SESSION_144.md
# Session 144 — Run Instructions for Claude Code

**Date:** March 2026
**Specs this session:** 5 code specs + 1 docs spec
**Full test suite runs:** 1 (after all code specs agent-approved, before docs)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_144.md, then run these specs in order: CC_SPEC_144_A_PASTE_DELETE_FIX.md, CC_SPEC_144_B_STALE_COST_FALLBACK.md, CC_SPEC_144_C_THUMBNAIL_PROXY_HARDENING.md, CC_SPEC_144_D_P3_CLEANUP_BATCH.md, CC_SPEC_144_E_P4_CONSISTENCY_FIXES.md, CC_SPEC_144_F_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 BASELINE STATE

- **Tests:** 1209 passing, 12 skipped, 0 failures
- **Migration:** 0077
- **Protocol:** CC_MULTI_SPEC_PROTOCOL.md v2.2

---

## 📋 SPEC QUEUE

| Order | Spec | Files | P-Level |
|-------|------|-------|---------|
| **1** | `CC_SPEC_144_A_PASTE_DELETE_FIX.md` | `bulk-generator.js` | 🔴 P1 |
| **2** | `CC_SPEC_144_B_STALE_COST_FALLBACK.md` | `bulk_generator_views.py` | 🔴 P1 |
| **3** | `CC_SPEC_144_C_THUMBNAIL_PROXY_HARDENING.md` | `upload_api_views.py` | 🟡 P2 |
| **4** | `CC_SPEC_144_D_P3_CLEANUP_BATCH.md` | `bulk-generator-generation.js`, `bulk-generator.js`, `lightbox.css`, `openai_provider.py` | ⚪ P3 |
| **5** | `CC_SPEC_144_E_P4_CONSISTENCY_FIXES.md` | `bulk-generator.js`, `tasks.py`, `CLAUDE.md` | ⚪ P4 |
| **6** | `CC_SPEC_144_F_DOCS_UPDATE.md` | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` | — |

---

## ⚠️ FILE BUDGETS

| File | Tier | Spec | Budget |
|------|------|------|--------|
| `bulk-generator.js` | ✅ Safe (725 lines) | A, E | No constraint |
| `bulk_generator_views.py` | ✅ Safe | B | No constraint |
| `upload_api_views.py` | 🟡 Caution (~1097 lines) | C | **Max 3 str_replace** |
| `bulk-generator-generation.js` | ✅ Safe (625 lines) | D | No constraint |
| `lightbox.css` | ✅ Safe | D | No constraint |
| `openai_provider.py` | ✅ Safe | D | No constraint |
| `tasks.py` | 🔴 Critical (~3691 lines) | E | **Max 2 str_replace** |

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_144_A_PASTE_DELETE_FIX.md`
1. Read spec fully
2. Complete Step 0 greps
3. Fix `.classList.contains()` → `.closest()` pattern (1 str_replace)
4. Step 2 verification greps — show outputs
5. PRE-AGENT SELF-CHECK
6. 4 agents: @frontend-developer, @javascript-pro, @code-reviewer, @accessibility-expert
7. Targeted test: `python manage.py test prompts.tests.test_bulk_generator`
8. `python manage.py check`
9. **DO NOT COMMIT**

---

### SPEC 2 — `CC_SPEC_144_B_STALE_COST_FALLBACK.md`
1. Read spec fully
2. Complete Step 0 greps
3. Update `0.034` → `0.042` (1 str_replace)
4. Step 2 verification greps — show outputs
5. PRE-AGENT SELF-CHECK
6. 4 agents: @django-pro, @python-pro, @security-auditor, @code-reviewer
7. Targeted test: `python manage.py test prompts.tests`
8. `python manage.py check`
9. **DO NOT COMMIT**

---

### SPEC 3 — `CC_SPEC_144_C_THUMBNAIL_PROXY_HARDENING.md`
1. Read spec fully
2. Complete Step 0 greps
3. Add rate limit constants (str_replace 1 of 3)
4. Add rate limit block after staff guard (str_replace 2 of 3)
5. Add `request.user.pk` to all 7 logger calls (str_replace 3 of 3)
6. Step 4 verification greps — show outputs
7. PRE-AGENT SELF-CHECK
8. 4 agents: @security-auditor (Opus), @backend-security-coder (Opus), @django-pro, @code-reviewer
9. Targeted test: `python manage.py test prompts.tests`
10. `python manage.py check`
11. **DO NOT COMMIT**

---

### SPEC 4 — `CC_SPEC_144_D_P3_CLEANUP_BATCH.md`
1. Read spec fully
2. Complete Step 0 greps — check `urlValidateRef` zero-reference result
3. Replace `.finally()` with `.then()` chain
4. Remove `I.urlValidateRef` (if zero refs confirmed)
5. Move `.container` max-width out of `lightbox.css`
6. Sniff Content-Type for `ref_file.name`
7. Step 5 verification greps — show outputs
8. PRE-AGENT SELF-CHECK
9. 4 agents: @javascript-pro, @frontend-developer, @django-pro, @code-reviewer
10. Targeted test: `python manage.py test prompts.tests`
11. `python manage.py check`
12. **DO NOT COMMIT**

---

### SPEC 5 — `CC_SPEC_144_E_P4_CONSISTENCY_FIXES.md`
1. Read spec fully
2. Complete Step 0 greps
3. Add `console.warn` to `deleteBox` `.catch`
4. Hoist `OPENAI_INTER_BATCH_DELAY` above loop (2 str_replace on `tasks.py`)
5. Fix CLAUDE.md quota capitalisation
6. Step 4 verification greps — show outputs
7. PRE-AGENT SELF-CHECK
8. 4 agents: @javascript-pro, @django-pro, @docs-architect, @code-reviewer
9. Targeted test: `python manage.py test prompts.tests.test_bulk_generator`
10. `python manage.py check`
11. **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after Specs 1–5 all agent-approved)

```bash
python manage.py test
```

Expected: 1209+ passing, 0 failures, 12 skipped.

- **Passes** → commit all 5 specs in order (see commit order below)
- **Fails** → identify which spec caused the failure → fix in place,
  max 2 attempts → if unresolved, stop and report

---

### SPEC 6 — `CC_SPEC_144_F_DOCS_UPDATE.md` (after code specs committed)
1. Read spec fully
2. Complete Step 0 greps
3. Add Session 144 changelog entry
4. Update CLAUDE.md resolved items and test count
5. Update PROJECT_FILE_STRUCTURE.md
6. 2 agents: @docs-architect, @api-documenter
7. Per v2.2: if below 8.0 → fix and re-run
8. **Commit immediately after confirmed scores**

---

## 💾 COMMIT ORDER

```
1. fix(bulk-gen): paste-clear button uses .closest() — fixes click miss on SVG child
2. fix(bulk-gen): update stale 0.034 cost fallback to 0.042 in job view
3. fix(proxy): add user.pk to all IMAGE-PROXY log lines, add 60 req/min rate limit
4. fix(bulk-gen): .finally() removed, dead urlValidateRef removed, container CSS moved, ref_file.name sniffs Content-Type
5. fix(bulk-gen): deleteBox .catch logs warn, inter-batch delay hoisted, CLAUDE.md quota capitalisation
6. END OF SESSION DOCS UPDATE: session 144 — P1 fixes, proxy hardening, P3/P4 cleanup batch
```

---

## ⛔ HARD RULES

1. `upload_api_views.py` — max 3 str_replace calls total (Spec C)
2. `tasks.py` — max 2 str_replace calls total (Spec E)
3. Do NOT fix issues outside scope — log in DEFERRED section of report
4. Full suite must pass before committing any code spec
5. Docs spec commits immediately after confirmed agent scores
6. Per v2.2: no projected agent scores — re-run if below 8.0

---

## 🔢 EXPECTED FINAL STATE

| Item | Expected |
|------|----------|
| Tests | 1209+ passing, 12 skipped, 0 failures |
| PASTE-DELETE ✕ button | Uses `.closest()` — fires on SVG child click |
| Cost fallback | `0.042` in `bulk_generator_views.py` |
| Proxy logging | All 7 `[IMAGE-PROXY]` lines include `user.pk` |
| Proxy rate limit | 60 req/min, `cache.add`/`cache.incr` |
| `.finally()` | Removed from `validateApiKey` |
| `I.urlValidateRef` | Removed from `bulk-generator.js` |
| `.container` rule | In global CSS file — not in `lightbox.css` |
| `ref_file.name` | Sniffs Content-Type header |
| `deleteBox` `.catch` | Logs `console.warn` |
| `OPENAI_INTER_BATCH_DELAY` | Read once above loop |
| CLAUDE.md | `"Quota exceeded"` consistent throughout |

---

## 🔔 BROWSER TESTS FOR MATEO (after session)

1. **PASTE-DELETE fix** — Paste image → click SVG icon inside the ✕ button
   (not just the edge) → clear action fires reliably
2. **D3 delay** — Run 3+ prompt job → Heroku logs show
   `[D3-RATE-LIMIT] Sleeping 12s` between batches
3. **Cost estimate** — High-quality job → `actual_cost` reflects ~$0.167/image

---

**END OF RUN INSTRUCTIONS**
