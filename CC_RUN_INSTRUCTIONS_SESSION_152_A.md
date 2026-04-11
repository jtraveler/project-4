# CC_RUN_INSTRUCTIONS_SESSION_152_A.md
# Session 152-A — Run Instructions for Claude Code

**Date:** April 2026
**Specs:** 1 code spec
**Full suite runs:** 1
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_152_A.md, then run: CC_SPEC_152_A_VISION_QUALITY_AND_PROGRESS.md`

---

## 📋 BASELINE STATE

- **Tests:** 1213+ passing, 12 skipped, 0 failures
- **Migration:** 0079
- **Protocol:** CC_MULTI_SPEC_PROTOCOL.md v2.2

---

## 📋 WHAT THIS FIXES

Three issues in `bulk_generator_views.py` only:

**1. Progress bar shows 0% on refresh mid-generation**
Root cause confirmed: `data-completed-count="0"` because query only
counts `status='completed'`. Images in `status='generating'` not counted.
Fix: `status__in=['completed', 'generating']`.

**2. Vision uses `detail: 'low'` — loses spatial accuracy**
At 85×85 pixel compression, the model cannot reliably determine who is
left/right/front/back, background people, or clothing detail. Upgrade
to `detail: 'high'` (~$0.009 vs $0.003 per call — justified for a paid feature).

**3. Direction corrupts Vision analysis**
Passing direction INTO the Vision call causes the model to reinterpret
rather than describe — wrong ethnicities, wrong positions, wrong composition.
Fix: two-step approach:
- Step 1: Vision describes image purely (no direction)
- Step 1.5: Direction applied as text edit to Vision output (same pipeline
  already used for text boxes)

---

## ⚠️ FILE BUDGET

| File | Tier | Budget |
|------|------|--------|
| `bulk_generator_views.py` | ✅ Safe | No constraint |

**Only one file changes this session.**

---

## ⚠️ CRITICAL NOTES

### Step 4 is the most complex change
Read Step 0 grep 4 and 5 outputs CAREFULLY before implementing.
The key changes are:
1. Vision loop: pass `''` not `direction` to `_generate_prompt_from_image`
2. Step 1.5: remove `if vision_enabled[i]: continue`
3. Add `combined_directions` that routes `vision_directions[i]` for
   Vision boxes and `text_directions[i]` for text boxes
4. Change `for i, direction in enumerate(text_directions):` to use
   `combined_directions`

**NO direction should be silently dropped.** Every direction the user
entered must flow through to the text edit step — just after Vision
analysis, not during it.

### Regression test for text boxes
Text box direction (Step 1.5 existing behaviour) must not regress.
Manual browser test 4 confirms this.

---

## 🔁 EXECUTION

1. Read spec fully
2. Complete ALL Step 0 greps
3. Fix progress bar query (Step 1)
4. Change `detail: 'low'` to `detail: 'high'` (Step 2)
5. Remove direction_block from Vision analysis (Step 3)
6. Route Vision directions to Step 1.5 via combined_directions (Step 4)
7. Step 5 verification greps — show ALL outputs
8. PRE-AGENT SELF-CHECK
9. 3 agents: @django-pro, @python-pro, @code-reviewer
10. Full suite: `python manage.py test`
11. Commit on pass

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): Vision detail high, two-step direction, progress bar generating state
```

---

**END OF RUN INSTRUCTIONS**
