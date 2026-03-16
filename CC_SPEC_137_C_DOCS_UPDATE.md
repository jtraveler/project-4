# CC_SPEC_137_C_DOCS_UPDATE.md
# End of Session 137 — Documentation Update + 136-E Verification

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 137
**Type:** Docs — commits immediately per protocol (v2.1)
**Agents Required:** 1 (@docs-architect)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — new docs gate rule applies here
3. **Documentation changes only** — no Python, no JS, no migrations
4. **Per v2.1 protocol:** if @docs-architect scores below 8.0, fix and re-run
   before committing. Do NOT commit on a projected or unconfirmed score.

---

## 📋 OVERVIEW

Three tasks:

1. **136-E verification** — Sessions 134-D and 136-E both committed with
   unconfirmed agent scores. This spec closes both gaps with a fresh
   @docs-architect review of the current state of all four core doc files.

2. **Session 137 changelog entry** — add entries for Specs A, B, and the
   docs update itself.

3. **Deferred P3 Items table update** — remove resolved items, add any new
   ones from Session 137 agent reports.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm 136-E changes are present
grep -n "bulk-generator-paste\|bulk-generator-utils" PROJECT_FILE_STRUCTURE.md | head -5
grep -n "Session 136" CLAUDE_CHANGELOG.md | head -3

# 2. Confirm 134-D changes are present
grep -n "prompt_list_views\|prompt_edit_views\|prompt_comment_views\|prompt_trash_views" \
    PROJECT_FILE_STRUCTURE.md | head -8

# 3. Get current test count
python manage.py test --verbosity=0 2>&1 | tail -3

# 4. Find Deferred P3 Items table in CLAUDE.md
grep -n "Deferred P3\|debounce\|opacity.*0\.6\|paste-locked\|banner.*link" CLAUDE.md | head -15

# 5. Find current file tier entry for bulk-generator.js
grep -n "bulk-generator\.js\|bulk-generator-paste\|1542\|1605" CLAUDE.md | head -10
```

**Do not proceed until greps are complete.**

---

## 📁 CHANGES REQUIRED

### 136-E + 134-D Verification

The @docs-architect agent must explicitly verify the following before scoring:

**From 136-E (unconfirmed):**
- `bulk-generator-paste.js` listed in `PROJECT_FILE_STRUCTURE.md` ✓/✗
- `bulk-generator-utils.js` listed in `PROJECT_FILE_STRUCTURE.md` ✓/✗
- Session 136 changelog entry present ✓/✗
- "Working on Bulk Generator?" section updated ✓/✗

**From 134-D (unconfirmed):**
- All 4 prompt domain modules in both tree diagrams ✓/✗
- Module count is 21+ ✓/✗
- `prompt_views.py` noted as shim ✓/✗

If any item fails, fix it in this spec before the agent runs.

### `CLAUDE_CHANGELOG.md`

Add Session 137 entry:
```
### Session 137 — March 16, 2026

**Focus:** Protocol hardening, P3 cleanup

**Specs:** 137-A (protocol v2.1), 137-B (P3 cleanup batch), 137-C (docs)

**Key outcomes:**
- CC_MULTI_SPEC_PROTOCOL.md v2.1 — docs gate re-run rule added
- BulkGenUtils.debounce dead code removed
- Banner error text reads from err.message (no duplicate copy)
- Paste lock state replaced with .bg-paste-locked CSS class
- 136-E and 134-D unconfirmed scores closed
```

### `CLAUDE.md`

1. **Update test count** to current value from Session 137 suite
2. **Update Deferred P3 Items table:**
   - Mark resolved: `BulkGenUtils.debounce` dead code ✅ Session 137
   - Mark resolved: Banner link text hardcoded separately ✅ Session 137
   - Mark resolved: `opacity: 0.6` inline style ✅ Session 137 (CSS class)
   - Add new item if any surfaced from Session 137 agents
3. **Update `bulk-generator.js` file tier** if line count changed after
   Spec B's debounce removal

### `PROJECT_FILE_STRUCTURE.md`

- Increment version header date to March 16, 2026
- Update test count

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] 136-E verification items checked — all present or fixed
- [ ] 134-D verification items checked — all present or fixed
- [ ] Session 137 changelog entry added
- [ ] Deferred P3 Items table updated (3 items resolved)
- [ ] Test count updated
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 1 agent. Must score 8.0+.
Per v2.1 protocol: if score is below 8.0, fix and re-run. Do NOT commit
on a projected score — a confirmed re-run is required.

### 1. @docs-architect
**Primary task — verification pass:**
- Confirm `bulk-generator-paste.js` in `PROJECT_FILE_STRUCTURE.md`
- Confirm `bulk-generator-utils.js` in `PROJECT_FILE_STRUCTURE.md`
- Confirm Session 136 changelog entry accurate
- Confirm all 4 prompt domain modules in tree diagrams
- Confirm module count 21+

**Secondary task — Session 137:**
- Verify Session 137 changelog entry accurate
- Verify Deferred P3 Items correctly shows 3 resolved items
- Verify test count updated

Rating requirement: 8+/10
**If score is below 8.0: fix all findings and run a second round.**

---

## 🧪 TESTING

```bash
python manage.py check
```
Commits immediately after confirmed 8.0+ agent score.

---

## 💾 COMMIT MESSAGE

```
END OF SESSION DOCS UPDATE: session 137 + close 134-D and 136-E unconfirmed scores
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_137_C_DOCS_UPDATE.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

**Section 7 must include:**
- Round 1 agent score
- If below 8.0: Round 2 score after fixes
- Final confirmed average ≥ 8.0
- Explicit statement: "134-D and 136-E unconfirmed scores now closed"

---

**END OF SPEC**
