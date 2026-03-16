# CC_RUN_INSTRUCTIONS_SESSION_137.md
# Session 137 — Run Instructions for Claude Code

**Date:** March 16, 2026
**Specs in this session:** 1 docs spec + 1 code spec + 1 docs spec
**Full test suite runs:** 1 (after Spec B, the only code spec)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_137.md, then run these specs in order: CC_SPEC_137_A_PROTOCOL_UPDATE.md, CC_SPEC_137_B_P3_CLEANUP_BATCH.md, CC_SPEC_137_C_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_137_A_PROTOCOL_UPDATE.md` | Docs | `CC_MULTI_SPEC_PROTOCOL.md` |
| **2** | `CC_SPEC_137_B_P3_CLEANUP_BATCH.md` | Code | `bulk-generator-utils.js`, `bulk-generator.js`, `bulk-generator.css` |
| **3** | `CC_SPEC_137_C_DOCS_UPDATE.md` | Docs | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` |

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_137_A_PROTOCOL_UPDATE.md` (Docs — commits immediately)

1. Read spec in full
2. Complete Step 0 greps
3. Update `CC_MULTI_SPEC_PROTOCOL.md` to v2.1
4. Complete PRE-AGENT SELF-CHECK
5. Run 1 agent: @docs-architect
6. **If agent scores below 8.0 → fix and re-run (new v2.1 rule)**
7. Commit immediately after confirmed 8.0+ score

⚠️ This spec updates the protocol you are currently reading.
After committing, the new v2.1 rule applies to all subsequent specs in this session.

---

### SPEC 2 — `CC_SPEC_137_B_P3_CLEANUP_BATCH.md` (Code — hold until suite)

1. Read spec in full
2. Complete all Step 0 greps — especially debounce caller check
3. Step 1: Remove `BulkGenUtils.debounce`
4. Step 2: Fix banner text to use `err.message`
5. Step 3: Replace inline opacity/cursor with `.bg-paste-locked` CSS class
6. Complete PRE-AGENT SELF-CHECK
7. Run 2 agents: @frontend-developer, @code-reviewer
8. **If any agent scores below 8.0 → fix and re-run per v2.1**
9. Run: `python manage.py check` — 0 issues
10. **DO NOT COMMIT YET**

---

## ⛔ FULL SUITE GATE (after Spec 2 agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests, 0 failures, 12 skipped.

- If passes → fill Sections 9–10 on Spec 2 report → commit
- If fails → identify regression (most likely Spec 2 banner text change) →
  fix in-place (max 2 attempts) → re-run

---

### SPEC 3 — `CC_SPEC_137_C_DOCS_UPDATE.md` (Docs — commits immediately)

1. Read spec in full
2. Complete Step 0 greps — verify 136-E and 134-D items before agent runs
3. Fix any missing items found during verification
4. Add Session 137 changelog entry
5. Update Deferred P3 Items
6. Complete PRE-AGENT SELF-CHECK
7. Run 1 agent: @docs-architect
8. **If agent scores below 8.0 → fix and re-run per v2.1 (mandatory)**
9. Commit immediately after confirmed 8.0+ score

---

## 💾 COMMIT ORDER

```
1. docs(protocol): CC_MULTI_SPEC_PROTOCOL.md v2.1 — docs gate re-run rule
2. refactor(bulk-gen): debounce dead code removal, banner text from err.message, paste lock CSS class
3. END OF SESSION DOCS UPDATE: session 137 + close 134-D and 136-E unconfirmed scores
```

---

## ⛔ HARD RULES

1. `bulk-generator.js` is 🟠 High Risk — max 2 str_replace calls
2. `bulk-generator.css` is 🟠 High Risk — append only
3. Never remove `BulkGenUtils.debounce` if Step 0 grep finds any caller
4. **v2.1 rule applies immediately after Spec 1 commits** — all subsequent
   specs must re-run agents if below 8.0
5. Spec 3 must produce a confirmed (not projected) agent score before committing

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected |
|--------|----------|
| Tests | 1193+ passing, 12 skipped, 0 failures |
| Protocol | v2.1 — docs gate re-run rule in effect |
| `BulkGenUtils.debounce` | Removed |
| Banner link text | Reads from `err.message` |
| Paste lock | `.bg-paste-locked` CSS class (no inline styles) |
| 134-D + 136-E | Confirmed closed in Spec 3 report |
| Deferred P3 Items | 3 items resolved |

---

## 🔔 REMINDER FOR DEVELOPER (Mateo)

After Session 137 is complete, please manually test the following from Session 136:

1. **Spec B paste flow** — click a prompt row → Cmd+V with a copied image →
   verify upload, thumbnail, URL lock, and clear all work → check browser
   console for zero errors
2. **Spec A visual check** — paste preview and error badges look identical to
   before the CSS migration
3. **Spec C scroll** — enter invalid URL → Generate → click "Prompt N" error
   link → verify the prompt box is visible above the sticky bottom bar

---

**END OF RUN INSTRUCTIONS**
