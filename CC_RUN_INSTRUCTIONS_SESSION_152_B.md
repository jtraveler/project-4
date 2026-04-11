# CC_RUN_INSTRUCTIONS_SESSION_152_B.md
# Session 152-B — Run Instructions for Claude Code

**Date:** April 2026
**Specs:** 1 code spec
**Full suite runs:** 1
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_152_B.md, then run: CC_SPEC_152_B_PROGRESS_AND_VISION_COMPOSITION.md`

---

## 📋 BASELINE STATE (post-152-A)

- **Tests:** 1213+ passing, 12 skipped, 0 failures
- **Migration:** 0079
- **Progress bar:** currently `filter(status__in=['completed', 'generating'])`
- **Vision detail:** `detail: 'high'` ✅ (from 152-A)
- **Vision direction:** decoupled from Vision call ✅ (from 152-A)

---

## 📋 WHAT THIS FIXES

**1. Progress bar still shows 0% on refresh**

Root cause confirmed via DevTools: images are `queued` when user
refreshes immediately after starting a job. The 152-A fix counted
`generating + completed` but missed `queued`. Fix: use
`exclude(status='failed')` which counts everything that isn't failed —
covers queued, generating, and completed in one expression. Future-proof.

**2. Vision composition still inaccurate**

Production testing shows: woman on wrong side of frame, man at same
depth as woman instead of behind her, background crowd missing,
decorative accessories missing, background incorrectly blurred.

Root cause: system prompt instructs "be spatially accurate" but
doesn't give explicit frame-position (LEFT/RIGHT from viewer
perspective), depth-layer (FOREGROUND/MIDGROUND/BACKGROUND), or
background-sharpness language. GPT-4o-mini needs explicit vocabulary
to describe these correctly.

---

## ⚠️ FILE BUDGET

| File | Tier | Budget |
|------|------|--------|
| `bulk_generator_views.py` | ✅ Safe | No constraint |

**Only one file changes this session.**

---

## ⚠️ CRITICAL NOTES

### Step 0 is mandatory
The progress bar query in production is `status__in=['completed', 'generating']`
(from 152-A). CC must grep first to confirm this before replacing.

### Step 2 — full replacement
The system prompt must be COMPLETELY replaced — not appended to.
Read the Step 0 grep 2 output (current system prompt) carefully before
replacing. Verify `ignore_watermark_rule` and `no_watermark_output_rule`
are still correctly placed at the end of the rules list.

### Do not revert detail:high
Step 0 grep 3 must confirm `detail: 'high'` is in place from 152-A.
Do NOT change it — it must stay as `'high'`.

---

## 🔁 EXECUTION

1. Read spec fully
2. Complete ALL Step 0 greps — confirm 152-A baseline
3. Replace progress bar query with `exclude(status='failed')` (Step 1)
4. Replace Vision system prompt completely (Step 2)
5. Step 3 verification greps — show ALL outputs
6. PRE-AGENT SELF-CHECK
7. 3 agents: @django-pro, @python-pro, @code-reviewer
8. Full suite: `python manage.py test`
9. Commit on pass

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): progress bar exclude-failed query, Vision composition accuracy
```

---

**END OF RUN INSTRUCTIONS**
