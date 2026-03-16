# CC_SPEC_137_A_PROTOCOL_UPDATE.md
# CC_MULTI_SPEC_PROTOCOL.md — v2.1 Update

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 137
**Type:** Docs/Protocol — commits immediately per protocol
**Agents Required:** 1 (@docs-architect)
**Estimated Scope:** 1 targeted addition to `CC_MULTI_SPEC_PROTOCOL.md`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Documentation changes only** — no Python, no JS, no migrations

---

## 📋 OVERVIEW

Sessions 134-D and 136-E both had the same failure pattern: a docs spec scored
below 8.0, fixes were applied, but no second agent round was run to confirm the
fixes resolved the issues. Both sessions committed with an unconfirmed final score.

The root cause is a gap in the docs gate sequence: it says "all must score 8.0+"
but does not explicitly state what to do when they don't. The code spec gate has
"Fix any blocking issues → re-run agents if needed" — the docs gate is missing
an equivalent rule.

This spec adds that rule to close the gap permanently.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the current docs gate sequence
sed -n '59,77p' CC_MULTI_SPEC_PROTOCOL.md

# 2. Read the version header
sed -n '1,10p' CC_MULTI_SPEC_PROTOCOL.md

# 3. Read the version history line at the bottom
tail -5 CC_MULTI_SPEC_PROTOCOL.md
```

---

## 📁 CHANGES REQUIRED

### `CC_MULTI_SPEC_PROTOCOL.md`

**Change 1 — Update version to 2.1**

Find the version header:
```
**Version:** 2.0
**Date:** March 15, 2026
```

Replace with:
```
**Version:** 2.1
**Date:** March 16, 2026
```

**Change 2 — Add re-run rule to docs gate sequence**

Find the docs gate sequence (step 6):
```
6. Run required agents → all must score 8.0+
7. Write FULL completion report (all 11 sections)
8. Commit immediately (report + any doc changes in same commit)
```

Replace with:
```
6. Run required agents → all must score 8.0+
7. If ANY agent scores below 8.0 → fix issues and re-run that agent.
   Do NOT commit until a confirmed round scores 8.0+ average.
   Fixes applied without a re-run do not count as passing.
8. Write FULL completion report (all 11 sections)
9. Commit immediately (report + any doc changes in same commit)
```

⚠️ Step numbers 8 and 9 shift — check the full sequence block for correct
numbering. Do not leave duplicate step numbers.

**Change 3 — Update version history line**

Find:
```
Version history: v1.0 initial, v1.1 added universal rules + PRE-AGENT reminder,
v2.0 hold-all-commits until full suite, two-pass report, Step 0 research rule,
corrected file size guidance, restored PRE-AGENT section.
```

Replace with:
```
Version history: v1.0 initial, v1.1 added universal rules + PRE-AGENT reminder,
v2.0 hold-all-commits until full suite, two-pass report, Step 0 research rule,
corrected file size guidance, restored PRE-AGENT section.
v2.1 docs gate re-run rule: agent scores below 8.0 require a confirmed re-run
before committing. Fixes without re-run verification do not count as passing.
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Version updated to 2.1
- [ ] Date updated to March 16, 2026
- [ ] Docs gate step 6 has re-run rule added
- [ ] Step numbers in docs gate are sequential with no gaps or duplicates
- [ ] Version history line updated
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 1 agent. Must score 8.0+.
If agent scores below 8.0 — fix and re-run per the new rule being added.

### 1. @docs-architect
- Verify version is 2.1 and date is correct
- Verify docs gate re-run rule is unambiguous
- Verify step numbers are sequential
- Verify version history accurately describes the change
- Rating requirement: 8+/10

---

## 🧪 TESTING

```bash
python manage.py check
```
Commits immediately after agents pass.

---

## 💾 COMMIT MESSAGE

```
docs(protocol): CC_MULTI_SPEC_PROTOCOL.md v2.1 — docs gate re-run rule
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_137_A_PROTOCOL_UPDATE.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
