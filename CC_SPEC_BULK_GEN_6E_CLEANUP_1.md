# CC_SPEC_BULK_GEN_6E_CLEANUP_1 — Python Micro-Cleanup + CLAUDE.md Forward Reference Fix

**Spec ID:** BULK-GEN-6E-CLEANUP-1
**Created:** March 12, 2026
**Type:** Code Quality / Docs Fix — no migration, no new tests
**Template Version:** v2.5
**Modifies UI/Templates:** No
**Requires Migration:** No
**Depends On:** 6E-HARDENING-1 and 6E-HARDENING-2 both committed (`3b42114`, `7b1ff65`)

> ⚠️ **ISOLATED TESTING ONLY** — Run only the targeted tests listed below.
> Do NOT run the full suite. Full suite runs after CLEANUP-3.

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`**
2. **Read this entire specification**
3. **Confirm both HARDENING commits are in `git log`** — run `git log --oneline -5` and verify `3b42114` and `7b1ff65` before starting
4. **Read all four target files in full** before writing any code
5. **Use both required agents** — @django-pro and @code-reviewer are MANDATORY

**Work is REJECTED if HARDENING commits not confirmed, agents skipped, or any test failures introduced.**

---

## 📋 OVERVIEW

This spec closes four small issues flagged by agents during HARDENING-1 and HARDENING-2 that were documented but not acted on. They are pure code quality improvements — no behaviour changes, no migrations, no new test logic required.

**Four items:**

1. **`frozenset` hardening** — `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` are mutable `set` objects. Convert to `frozenset` for defence-in-depth. Three one-line changes.
2. **`total_images_estimate` rename** — Post-6E-C this variable holds an exact resolved count, not an estimate. Rename to `resolved_total_images` in `create_job()`.
3. **`or` → explicit `> 0` guard** — `job.actual_total_images or job.total_images` in `get_job_status()` treats `0` as "not set". Replace with explicit `if job.actual_total_images > 0` for semantic clarity.
4. **CLAUDE.md Section B forward reference fix** — Section B references "see Bulk Job Deletion section" but Section A (the deletion section) appears later in the file. Add the section heading name so the reader knows where to look.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` are `frozenset` at module level
- ✅ `total_images_estimate` renamed to `resolved_total_images` in `create_job()` — all three usages updated
- ✅ `get_job_status()` uses `if job.actual_total_images > 0` guard — not `or`
- ✅ CLAUDE.md Section B forward reference updated to name the target section
- ✅ Isolated tests pass with no failures introduced
- ✅ Both agents score 8+/10

---

## 🔍 TOUCH POINTS — Complete in Order

---

### Touch Point 1 — `frozenset` Hardening

**File:** `prompts/views/bulk_generator_views.py`

Read the file to find the three module-level constant definitions added in HARDENING-1. Convert each from `set` to `frozenset`:

```python
# Before:
VALID_SIZES = set(SUPPORTED_IMAGE_SIZES)
VALID_QUALITIES = {choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES}
VALID_COUNTS = {1, 2, 3, 4}

# After:
VALID_SIZES = frozenset(SUPPORTED_IMAGE_SIZES)
VALID_QUALITIES = frozenset(choice[0] for choice in BulkGenerationJob.QUALITY_CHOICES)
VALID_COUNTS = frozenset({1, 2, 3, 4})
```

The `in` operator works identically on `frozenset` — no callers need updating.

---

### Touch Point 2 — `total_images_estimate` Rename

**File:** `prompts/services/bulk_generation.py`

Read `create_job()` to find all usages of `total_images_estimate`. There are exactly three: the assignment, the `estimated_cost` calculation, and the `actual_total_images=` field on `BulkGenerationJob.objects.create()`. Rename all three occurrences to `resolved_total_images`.

Do not rename any other variables. Do not change any logic. This is a pure rename.

```python
# Before (three occurrences):
total_images_estimate = sum(resolved_counts)
...estimated_cost=Decimal(str(cost_per_image * total_images_estimate))...
...actual_total_images=total_images_estimate...

# After:
resolved_total_images = sum(resolved_counts)
...estimated_cost=Decimal(str(cost_per_image * resolved_total_images))...
...actual_total_images=resolved_total_images...
```

---

### Touch Point 3 — `or` → `> 0` Guard in `get_job_status()`

**File:** `prompts/services/bulk_generation.py`

Read `get_job_status()` to find the line returning `actual_total_images`. Replace the `or` fallback with an explicit guard:

```python
# Before:
'actual_total_images': job.actual_total_images or job.total_images,

# After:
'actual_total_images': job.actual_total_images if job.actual_total_images > 0 else job.total_images,
```

This is semantically clearer — `0` is explicitly treated as "field not yet populated" (pre-migration jobs) rather than relying on Python's falsy evaluation of `0`.

---

### Touch Point 4 — CLAUDE.md Section B Forward Reference Fix

**File:** `CLAUDE.md`

Read CLAUDE.md to find Section B ("Orphan Detection — B2 Migration Gap"). Find the bullet point that reads:

```
- Understands the shared-file window (see Bulk Job Deletion section) — does not
  flag shared files as orphans
```

Update it to name the target section heading:

```
- Understands the shared-file window (see 'Bulk Job Deletion — Pre-Build Reference' below) — does not
  flag shared files as orphans
```

This is the only change to CLAUDE.md. Do not touch any other content.

---

## ✅ DO / DO NOT

### DO
- ✅ Confirm both HARDENING commits in `git log` before starting
- ✅ Read each target file in full before editing
- ✅ Rename ALL three occurrences of `total_images_estimate` — not just the assignment
- ✅ Run isolated tests after changes

### DO NOT
- ❌ Do not change any logic — these are pure quality improvements
- ❌ Do not add or remove any tests
- ❌ Do not touch any other files not listed in this spec
- ❌ Do not run the full test suite

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Both HARDENING commits confirmed in `git log`
- [ ] `VALID_SIZES`, `VALID_QUALITIES`, `VALID_COUNTS` are `frozenset`
- [ ] All three occurrences of `total_images_estimate` renamed to `resolved_total_images`
- [ ] `get_job_status()` uses `if job.actual_total_images > 0 else` — not `or`
- [ ] CLAUDE.md Section B forward reference names the target heading
- [ ] Only CLAUDE.md changed in CLAUDE.md — no other content touched
- [ ] Isolated tests pass

---

## 🤖 AGENT REQUIREMENTS

**@django-pro — MANDATORY**
- Focus: Is the `frozenset` conversion correct for all three constants? Is the `total_images_estimate` rename complete — all three occurrences updated? Is the `> 0` guard semantically correct for the fallback intent?
- Rating: 8+/10

**@code-reviewer — MANDATORY**
- Focus: Is there any caller of `VALID_SIZES`, `VALID_QUALITIES`, or `VALID_COUNTS` that relies on set mutability? Are there any other usages of `total_images_estimate` in the file beyond the three listed? Does the `> 0` guard handle all edge cases (negative values, None) correctly?
- Rating: 8+/10

### ⛔ REJECTION CRITERIA
- Any HARDENING commit not confirmed before starting
- Any of the three constants still a mutable `set`
- Any occurrence of `total_images_estimate` remaining in the file
- `get_job_status()` still uses `or` for the fallback
- Any agent below 8.0/10
- Full suite run (prohibited until CLEANUP-3)

---

## 🧪 ISOLATED TESTING

```bash
python manage.py test prompts.tests.test_bulk_generator_views -v 2
python manage.py test prompts.tests.test_bulk_generation_tasks -v 2
# Expected: all existing tests pass, 0 failures, 0 new tests
```

---

## 📊 CC COMPLETION REPORT

```
═══════════════════════════════════════════════════════════════
BULK-GEN-6E-CLEANUP-1 — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

HARDENING commits confirmed: ✅/❌

TP1 frozenset — VALID_SIZES:     ✅/❌
TP1 frozenset — VALID_QUALITIES: ✅/❌
TP1 frozenset — VALID_COUNTS:    ✅/❌
TP2 total_images_estimate renamed (all 3 occurrences): ✅/❌
TP3 get_job_status() uses > 0 guard:                  ✅/❌
TP4 CLAUDE.md forward reference updated:              ✅/❌

Agent: @django-pro     Score: X/10  Findings:  Action:
Agent: @code-reviewer  Score: X/10  Findings:  Action:

Isolated tests: all passing, 0 failures
Full suite: NOT RUN

Commit hash:
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
refactor(bulk-gen): 6E-CLEANUP-1 — frozenset hardening, variable rename, > 0 guard, docs fix

- VALID_SIZES, VALID_QUALITIES, VALID_COUNTS converted to frozenset
- total_images_estimate renamed to resolved_total_images in create_job()
- get_job_status() actual_total_images fallback uses explicit > 0 guard
- CLAUDE.md Section B forward reference names target section heading

Agents: @django-pro X/10, @code-reviewer X/10
```
