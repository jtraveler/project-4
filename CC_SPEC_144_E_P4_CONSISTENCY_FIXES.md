# CC_SPEC_144_E_P4_CONSISTENCY_FIXES.md
# P4 Consistency Fixes — `deleteBox` warn, Delay Hoist, CLAUDE.md Capitalisation

**Spec Version:** 1.0 (written after file review)
**Date:** March 2026
**Session:** 144
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 4 minimum
**Estimated Scope:** ~5 lines across 3 files

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`tasks.py` is 🔴 CRITICAL (~3691 lines)** — max 2 str_replace calls
4. **Plan both `tasks.py` str_replace calls BEFORE making the first edit**

**Work will be REJECTED if:**
- `tasks.py` has more than 2 str_replace calls
- `deleteBox` `.catch` is still silent (no `console.warn`)
- `OPENAI_INTER_BATCH_DELAY` is still read inside the loop body
- CLAUDE.md still contains `"quota exhausted"` (lowercase)

---

## 📋 OVERVIEW

Three small consistency fixes:

1. **`deleteBox` `.catch` console.warn** — the fetch in `deleteBox`
   swallows errors silently. The equivalent handler in the paste-clear
   button (now fixed in Spec 144-A) already logs. Add matching `console.warn`
   to `deleteBox`.

2. **Hoist `OPENAI_INTER_BATCH_DELAY`** — the setting is read on every
   loop iteration inside `_run_generation_loop()`. It is a static Django
   setting and should be read once before the loop.

3. **CLAUDE.md capitalisation** — `"quota exhausted"` (lowercase) is
   inconsistent with `"Quota exceeded"` used in `_sanitise_error_message()`
   in `bulk_generation.py`. Fix to match.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm deleteBox .catch exact text
sed -n '268,274p' static/js/bulk-generator.js

# 2. Confirm OPENAI_INTER_BATCH_DELAY location in loop
grep -n "OPENAI_INTER_BATCH_DELAY\|for batch_start in range" prompts/tasks.py

# 3. Read the full delay block inside the loop
sed -n '2820,2837p' prompts/tasks.py

# 4. Read the line just before the for loop (for hoist anchor)
sed -n '2734,2742p' prompts/tasks.py

# 5. Find CLAUDE.md quota capitalisation issue
grep -n "quota exhausted\|Quota exceeded" CLAUDE.md
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Add `console.warn` to `deleteBox` `.catch`

**File:** `static/js/bulk-generator.js`
**str_replace: 1 call**

From Step 0 grep 1, read the exact current `.catch` block in `deleteBox`.

**CURRENT:**
```javascript
            }).catch(function() {
                // Non-critical — ignore, proceed with box deletion
            });
```

**REPLACE WITH:**
```javascript
            }).catch(function(err) {
                console.warn('[PASTE-DELETE] deleteBox fetch failed:', err);
            });
```

---

## 📁 STEP 2 — Hoist `OPENAI_INTER_BATCH_DELAY` above loop

**File:** `prompts/tasks.py`
**str_replace calls: 2 of 2 (use both here — no remaining budget)**

From Step 0 greps 2, 3, and 4, read the exact text of both anchor points.

**str_replace call 1 of 2 — Remove from inside loop body:**

From Step 0 grep 3, read the full delay block. Find the exact text
starting from the comment `# D3: Inter-batch delay...` through to
`time.sleep(_inter_batch_delay)`.

Replace the full block (retaining all lines EXCEPT the `_inter_batch_delay`
assignment):

**CURRENT (inside loop, lines ~2821–2835):**
```python
        # D3: Inter-batch delay for OpenAI rate limit compliance.
        # Tier 1 allows 5 images/min. With max_workers=4 and no delay,
        # throughput exceeds the limit. Set OPENAI_INTER_BATCH_DELAY=12
        # in Heroku config vars to comply with Tier 1 (one image every 12s).
        # Skip the delay after the last batch.
        _inter_batch_delay = getattr(settings, 'OPENAI_INTER_BATCH_DELAY', 0)
        _is_last_batch = (
            batch_start + MAX_CONCURRENT_IMAGE_REQUESTS >= len(images_list)
        )
        if _inter_batch_delay > 0 and not _is_last_batch:
            logger.info(
                "[D3-RATE-LIMIT] Sleeping %ds between batches (job %s)",
                _inter_batch_delay, job.id,
            )
            time.sleep(_inter_batch_delay)
```

**REPLACE WITH (assignment removed — now read from hoisted variable):**
```python
        # D3: Inter-batch delay for OpenAI rate limit compliance.
        # Skip the delay after the last batch.
        _is_last_batch = (
            batch_start + MAX_CONCURRENT_IMAGE_REQUESTS >= len(images_list)
        )
        if _inter_batch_delay > 0 and not _is_last_batch:
            logger.info(
                "[D3-RATE-LIMIT] Sleeping %ds between batches (job %s)",
                _inter_batch_delay, job.id,
            )
            time.sleep(_inter_batch_delay)
```

**str_replace call 2 of 2 — Hoist assignment above loop:**

From Step 0 grep 4, read the exact text of the `for batch_start in range`
line including the line immediately before it.

**CURRENT:**
```python
    for batch_start in range(0, len(images_list), MAX_CONCURRENT_IMAGE_REQUESTS):
```

**REPLACE WITH:**
```python
    # D3: Read once — OPENAI_INTER_BATCH_DELAY is a static setting,
    # no need to look it up on every batch iteration.
    _inter_batch_delay = getattr(settings, 'OPENAI_INTER_BATCH_DELAY', 0)

    for batch_start in range(0, len(images_list), MAX_CONCURRENT_IMAGE_REQUESTS):
```

⚠️ This is str_replace call 2 of 2 on `tasks.py`. No further edits to
this file are permitted in this spec.

---

## 📁 STEP 3 — Fix CLAUDE.md capitalisation

**File:** `CLAUDE.md`

From Step 0 grep 5, find the exact location of `"quota exhausted"`.
Replace with `"Quota exceeded"` to match the string used in
`_sanitise_error_message()` in `prompts/services/bulk_generation.py`.

---

## 📁 STEP 4 — MANDATORY VERIFICATION

```bash
# 1. Confirm deleteBox .catch now has console.warn
grep -n "PASTE-DELETE.*deleteBox\|Non-critical.*ignore" static/js/bulk-generator.js

# 2. Confirm OPENAI_INTER_BATCH_DELAY appears exactly twice in tasks.py
# (once hoisted above loop, once used inside loop condition)
grep -n "OPENAI_INTER_BATCH_DELAY" prompts/tasks.py

# 3. Confirm hoisted variable is ABOVE the for loop
# (line number of hoist must be lower than line number of for loop)
grep -n "_inter_batch_delay = getattr\|for batch_start in range" prompts/tasks.py

# 4. Confirm CLAUDE.md capitalisation fixed
grep -n "quota exhausted\|Quota exceeded" CLAUDE.md
```

**Expected results:**
- Grep 1: shows `[PASTE-DELETE] deleteBox fetch failed` — no `Non-critical`
- Grep 2: exactly 2 results for `OPENAI_INTER_BATCH_DELAY`
- Grep 3: `_inter_batch_delay = getattr` line number is LOWER than
  `for batch_start in range` line number
- Grep 4: 0 results for `quota exhausted`, ≥1 for `Quota exceeded`

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed and read
- [ ] Step 4 verification greps all pass (shown in report)
- [ ] `deleteBox` `.catch` now has `console.warn('[PASTE-DELETE] deleteBox fetch failed:', err)`
- [ ] `tasks.py` str_replace count is exactly 2
- [ ] `_inter_batch_delay` hoisted ABOVE the `for batch_start` loop
- [ ] `_inter_batch_delay` assignment removed from inside loop body
- [ ] CLAUDE.md `"quota exhausted"` replaced with `"Quota exceeded"`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+.
If any score below 8.0 → fix and re-run. No projected scores.

### 1. @javascript-pro
**Verify `deleteBox` `.catch` change.**
- Verify `err` parameter added to the catch function signature
- Verify log prefix `[PASTE-DELETE]` matches existing pattern from
  the single-box handler (now fixed in Spec 144-A)
- Show Step 4 grep 1 output
- Rating requirement: 8+/10

### 2. @django-pro
**Verify `OPENAI_INTER_BATCH_DELAY` hoist is correct.**
- Verify the hoisted variable is read before the loop starts
- Verify the behaviour is identical to before (same value, same logic)
- Verify `tasks.py` str_replace count is exactly 2 — confirm in report
- Show Step 4 grep 2 and grep 3 outputs
- Rating requirement: 8+/10

### 3. @docs-architect
**Verify CLAUDE.md capitalisation fix.**
- Verify `"quota exhausted"` (lowercase) is gone
- Verify `"Quota exceeded"` (capitalised) is present and consistent
  with `_sanitise_error_message()` in `bulk_generation.py`
- Show Step 4 grep 4 output
- Rating requirement: 8+/10

### 4. @code-reviewer
**Overall quality.**
- Verify Step 4 verification outputs are all shown in report
- Verify `tasks.py` str_replace budget was respected (exactly 2 calls)
- Verify all three changes are minimal and correctly scoped
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `tasks.py` has more than 2 str_replace calls
- `_inter_batch_delay` still assigned inside the loop body
- `deleteBox` `.catch` still silent
- Step 4 verification greps not shown in report

---

## 🧪 TESTING

No new tests required. All three changes are:
- A console.warn addition (not testable in Python suite)
- A pure refactor with identical runtime behaviour
- A documentation-only fix

```bash
# Run full targeted test to confirm no regressions
python manage.py test prompts.tests.test_bulk_generator --verbosity=1 2>&1 | tail -5

# Django check
python manage.py check
```

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): deleteBox .catch logs warn, inter-batch delay hoisted, CLAUDE.md quota capitalisation
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_144_E_P4_CONSISTENCY_FIXES.md`

**Section 3 MUST include all Step 4 verification grep outputs.**

---

**END OF SPEC**
