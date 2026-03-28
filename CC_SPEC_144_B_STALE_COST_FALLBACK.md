# CC_SPEC_144_B_STALE_COST_FALLBACK.md
# Stale Cost Fallback — `0.034` → `0.042` in `bulk_generator_views.py`

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 144
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** 1 line in `prompts/views/bulk_generator_views.py`

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **This was flagged as Medium severity** by `@security-auditor` in the
   Session 143-H retroactive review. It must be resolved this session.

**Work will be REJECTED if `0.034` remains in `bulk_generator_views.py`
after this spec.**

---

## 📋 OVERVIEW

In Session 143, `IMAGE_COST_MAP` in `prompts/constants.py` was corrected:
- medium square: `0.034` → `0.042`
- high square: `0.067` → `0.167`
- high portrait: `0.092` → `0.250`

`openai_provider.py` already uses `0.042` as its fallback (confirmed).
`bulk_generator_views.py` line 77 still carries the old `0.034` fallback.

This fallback is only hit if a job's quality/size combination is absent
from `IMAGE_COST_MAP` (edge case), but it must be consistent with the
single source of truth.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm the stale fallback location
grep -n "0\.034\|0\.042" prompts/views/bulk_generator_views.py

# 2. Read the full function for context
sed -n '70,100p' prompts/views/bulk_generator_views.py

# 3. Confirm openai_provider.py already uses 0.042 (for consistency check)
grep -n "0\.034\|0\.042" prompts/services/image_providers/openai_provider.py

# 4. Confirm IMAGE_COST_MAP in constants.py
grep -n "IMAGE_COST_MAP\|0\.042\|medium" prompts/constants.py | head -10
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Update stale fallback

**File:** `prompts/views/bulk_generator_views.py`
**str_replace: 1 call**

**CURRENT:**
```python
    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
```

**REPLACE WITH:**
```python
    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.042)
```

No other changes to this file.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm 0.034 is gone
grep -n "0\.034" prompts/views/bulk_generator_views.py

# 2. Confirm 0.042 is present
grep -n "0\.042" prompts/views/bulk_generator_views.py
```

**Expected results:**
- Grep 1: 0 results
- Grep 2: 1 result

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 2 verification greps pass (shown in report)
- [ ] `grep -n "0.034" prompts/views/bulk_generator_views.py` → 0 results
- [ ] `grep -n "0.042" prompts/views/bulk_generator_views.py` → 1 result
- [ ] `openai_provider.py` also uses `0.042` (confirmed consistent)
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.
If any score below 8.0 → fix and re-run. No projected scores.

### 1. @django-pro
**Verify the view context calculation is correct.**
- Verify `IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.042)` is
  the correct pattern — fallback only fires on unknown quality/size
- Verify the `estimated_total_cost` calculation downstream uses this value
- Show Step 2 verification grep outputs
- Rating requirement: 8+/10

### 2. @python-pro
**Verify test coverage is adequate.**
- Verify or add a test that asserts `0.042` is used as fallback when
  quality/size is not in `IMAGE_COST_MAP`
- Test must use BOTH a positive assertion (value equals expected amount
  calculated with `0.042`) AND a negative assertion (does not equal
  amount calculated with `0.034`)
- Rating requirement: 8+/10

### 3. @security-auditor
**Confirm the flagged issue from Session 143-H is resolved.**
- Confirm `0.034` no longer exists anywhere in `bulk_generator_views.py`
- Confirm fallback is now consistent with `openai_provider.py`
- Explicitly state: "Session 143-H medium severity fallback issue is resolved"
- Rating requirement: 8+/10

### 4. @code-reviewer
**Overall quality.**
- Verify Step 2 verification outputs are shown in report
- Verify no other stale cost values exist in views or templates
  (`grep -rn "0\.034" prompts/` to confirm)
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `0.034` still present in `bulk_generator_views.py`
- Step 2 verification greps not shown in report
- `@security-auditor` closure statement missing

---

## 🧪 TESTING

```bash
# Targeted test
python manage.py test prompts.tests.test_bulk_generator_views --verbosity=1 2>&1 | tail -5

# If test file doesn't exist, run the broader views test
python manage.py test prompts.tests --verbosity=1 2>&1 | tail -5

# Django check
python manage.py check
```

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): update stale 0.034 cost fallback to 0.042 in job view
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_144_B_STALE_COST_FALLBACK.md`

**Section 3 MUST include:**
- All Step 2 verification grep outputs
- `@security-auditor` explicit closure statement

---

**END OF SPEC**
