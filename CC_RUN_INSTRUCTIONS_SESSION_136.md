# CC_RUN_INSTRUCTIONS_SESSION_136.md
# Session 136 — Run Instructions for Claude Code

**Date:** March 16, 2026
**Specs in this session:** 3 code specs + 2 docs specs
**Full test suite runs:** 1 (after all 3 code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_136.md, then run these specs in order: CC_SPEC_136_A_CSS_MIGRATION.md, CC_SPEC_136_B_PASTE_MODULE_EXTRACTION.md, CC_SPEC_136_C_P3_BATCH.md, CC_SPEC_136_D_VIEWS_STRUCTURE_DOCS.md, CC_SPEC_136_E_DOCS_UPDATE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_136_A_CSS_MIGRATION.md` | Code | `bulk-generator.css`, `bulk_generator.html` |
| **2** | `CC_SPEC_136_B_PASTE_MODULE_EXTRACTION.md` | Code | `bulk-generator.js`, `bulk-generator-utils.js`, `bulk-generator-paste.js` (NEW), `bulk_generator.html` |
| **3** | `CC_SPEC_136_C_P3_BATCH.md` | Code | `bulk-generator.js`, `bulk-generator-utils.js` |
| **4** | `CC_SPEC_136_D_VIEWS_STRUCTURE_DOCS.md` | Docs | `prompts/views/STRUCTURE.txt`, `prompts/views/README.md` |
| **5** | `CC_SPEC_136_E_DOCS_UPDATE.md` | Docs | `CLAUDE.md`, `CLAUDE_CHANGELOG.md`, `PROJECT_FILE_STRUCTURE.md` |

---

## ⚠️ CRITICAL ORDERING RULE

**Spec A must run before Spec B.** Spec A removes the inline CSS from
`bulk_generator.html`. Spec B adds a new script tag to `bulk_generator.html`.
If run in reverse order, the script tag str_replace anchor may conflict.

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_136_A_CSS_MIGRATION.md`
1. Read spec in full
2. Complete all Step 0 greps
3. Append CSS to `bulk-generator.css` verbatim
4. Remove paste/badge CSS from `bulk_generator.html`
5. Complete PRE-AGENT SELF-CHECK
6. Run 2 agents: @frontend-developer, @code-reviewer
7. Run: `python manage.py check` — 0 issues
8. **DO NOT COMMIT YET**

---

### SPEC 2 — `CC_SPEC_136_B_PASTE_MODULE_EXTRACTION.md`
1. Read spec in full
2. Complete all Step 0 greps
3. Move helpers to `bulk-generator-utils.js`
4. Create `bulk-generator-paste.js`
5. Update `bulk-generator.js` (remove helpers + listener, update call sites, add init)
6. Add script tag to `bulk_generator.html`
7. Complete PRE-AGENT SELF-CHECK
8. Run 3 agents: @frontend-developer, @code-reviewer, @security-auditor
9. Run: `python manage.py check` — 0 issues
10. **DO NOT COMMIT YET**

---

### SPEC 3 — `CC_SPEC_136_C_P3_BATCH.md`
1. Read spec in full
2. Complete all Step 0 greps
3. Fix prefers-reduced-motion scroll
4. Fix IMAGE_EXT_RE regex
5. Complete PRE-AGENT SELF-CHECK
6. Run 2 agents: @frontend-developer, @accessibility
7. Run: `python manage.py check` — 0 issues
8. **DO NOT COMMIT YET**

---

## ⛔ FULL SUITE GATE (after Specs 1–3 agent-approved)

```bash
python manage.py test
```

Expected: 1193+ tests, 0 failures, 12 skipped.

- If suite passes → fill Sections 9–10 on all 3 reports → commit in order
- If suite fails → most likely Spec B (module extraction) — identify and fix
  (max 2 attempts) → if still failing, stop and report to developer

---

### SPEC 4 — `CC_SPEC_136_D_VIEWS_STRUCTURE_DOCS.md` (after code specs committed)
1. Read spec in full
2. Complete Step 0 greps — get accurate line counts
3. Rewrite both files
4. Complete PRE-AGENT SELF-CHECK
5. Run 1 agent: @docs-architect
6. **Commit immediately**

---

### SPEC 5 — `CC_SPEC_136_E_DOCS_UPDATE.md` (after Spec D committed)
1. Read spec in full
2. Complete Step 0 greps
3. Update CLAUDE.md, changelog, PROJECT_FILE_STRUCTURE.md
4. Complete PRE-AGENT SELF-CHECK
5. Run 1 agent: @docs-architect
6. **Commit immediately**

---

## 💾 COMMIT ORDER

```
1. refactor(css): move paste/badge inline CSS from bulk_generator.html to bulk-generator.css
2. refactor(js): extract paste feature to bulk-generator-paste.js module
3. fix(a11y): prefers-reduced-motion scroll, IMAGE_EXT_RE anchor, accessibility review
4. docs(views): rewrite STRUCTURE.txt and README.md for current 22-module state
5. END OF SESSION DOCS UPDATE: session 136 — CSS migration, paste module, P3 fixes, views docs
```

---

## ⛔ HARD RULES

1. `bulk-generator.css` is 🟠 High Risk — append to end ONLY, no existing rule edits
2. `bulk-generator.js` is 🟠 High Risk — max 2 str_replace calls per spec
3. Spec A before Spec B — ordering is critical
4. `bulk-generator-paste.js` must load AFTER utils and BEFORE main JS
5. Docs specs (D and E) commit immediately — do not wait for suite

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected |
|--------|----------|
| Tests | 1193+ passing, 12 skipped, 0 failures |
| `bulk-generator.js` | ~1,485 lines (down from 1,605) |
| `bulk-generator-paste.js` | NEW — ~80 lines ✅ Safe |
| `bulk-generator.css` | ~1,570 lines (paste/badge rules appended) |
| `bulk_generator.html` inline CSS | Flush button only |
| STRUCTURE.txt + README.md | Accurate 22-module state |
| Deferred P3 Items | 3 resolved (reduced-motion, regex, a11y) |

---

**END OF RUN INSTRUCTIONS**
