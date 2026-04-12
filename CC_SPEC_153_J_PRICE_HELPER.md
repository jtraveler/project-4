# CC_SPEC_153_J_PRICE_HELPER.md
# Refactor: Introduce get_image_cost() Helper to Eliminate Duplicated Price Lookups

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** 4 files — constants.py, openai_provider.py, tasks.py (sed), views

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompts/tasks.py` is 🔴 CRITICAL** — sed ONLY, NO str_replace
4. **DO NOT COMMIT** until full suite passes
5. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

### Eliminate Duplicated Price Lookups

`IMAGE_COST_MAP.get(quality, {}).get(size, 0.034)` appears in 3 Python
call sites. When pricing changes, all 3 must be updated together — and
153-C showed this is error-prone (the view fallback was missed until
agents caught it).

A `get_image_cost(quality, size)` helper in `constants.py` centralises
the lookup. All call sites import and use the helper instead of the
pattern directly.

### Confirmed Current Call Sites

1. `openai_provider.py:302` — `return IMAGE_COST_MAP.get(quality, {}).get(size, 0.034)`
2. `tasks.py:2663` — `cost = IMAGE_COST_MAP.get(image.quality or job.quality or 'medium', {}).get(image.size or job.size, 0.034)`
3. `views/bulk_generator_views.py:82` — `cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)`

### Scope Note

This spec covers Python call sites only. The JS `I.COST_MAP` in
`bulk-generator.js` is a separate concern (template context injection)
deferred to a future spec. The JS copy was updated in 153-F and is
consistent with the Python constant for now.

---

## 🎯 OBJECTIVES

- ✅ `get_image_cost(quality, size)` helper added to `constants.py`
- ✅ All 3 Python call sites updated to use the helper
- ✅ `IMAGE_COST_MAP` import removed from `openai_provider.py` `get_cost_per_image`
  (helper is imported from constants instead)
- ✅ Full suite passes

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read current constants.py IMAGE_COST_MAP and surrounding area
sed -n '420,465p' prompts/constants.py

# 2. Read get_cost_per_image in openai_provider.py
sed -n '290,310p' prompts/services/image_providers/openai_provider.py

# 3. Read _apply_generation_result cost calc in tasks.py
sed -n '2649,2680p' prompts/tasks.py

# 4. Read bulk_generator_job_view cost calc in views
sed -n '78,90p' prompts/views/bulk_generator_views.py

# 5. Check existing imports in views
grep -n "from prompts.constants import" prompts/views/bulk_generator_views.py | head -5

# 6. File sizes
wc -l prompts/constants.py prompts/services/image_providers/openai_provider.py \
    prompts/views/bulk_generator_views.py prompts/tasks.py
```

**Do not proceed until all greps are complete.**

---

## 📁 STEP 1 — Add `get_image_cost()` to `constants.py`

**File:** `prompts/constants.py` — ✅ SAFE

From Step 0 grep 1, find the end of the `IMAGE_COST_MAP` dict (after
the closing `}`). Add the helper immediately after it:

```python
def get_image_cost(quality: str, size: str, fallback: float = 0.034) -> float:
    """Return cost per image for the given quality and size.

    Single source of truth for all image cost lookups. Call sites should
    use this helper instead of IMAGE_COST_MAP.get().get() directly, so
    future pricing changes only need to update IMAGE_COST_MAP.

    Args:
        quality: Quality tier string ('low', 'medium', 'high').
        size: Size string ('1024x1024', '1024x1536', '1536x1024').
        fallback: Price to return if quality/size not in map (default: 0.034
                  — the medium square price as of GPT-Image-1.5 pricing).

    Returns:
        Cost per image as a float.
    """
    return IMAGE_COST_MAP.get(quality, {}).get(size, fallback)
```

---

## 📁 STEP 2 — Update `openai_provider.py` call site

**File:** `prompts/services/image_providers/openai_provider.py` — ✅ SAFE

From Step 0 grep 2, the current `get_cost_per_image` method:

```python
    def get_cost_per_image(
        self, size: str = '1024x1024', quality: str = 'medium'
    ) -> float:
        """Return cost per image based on quality and size.

        Delegates to IMAGE_COST_MAP in prompts.constants — single source of
        truth for all pricing. Falls back to medium square price if the
        quality/size combination is not found.
        """
        from prompts.constants import IMAGE_COST_MAP
        return IMAGE_COST_MAP.get(quality, {}).get(size, 0.034)
```

Replace with:

```python
    def get_cost_per_image(
        self, size: str = '1024x1024', quality: str = 'medium'
    ) -> float:
        """Return cost per image based on quality and size.

        Delegates to get_image_cost() in prompts.constants — single source of
        truth for all pricing. Falls back to medium square price if the
        quality/size combination is not found.
        """
        from prompts.constants import get_image_cost
        return get_image_cost(quality, size)
```

Use the exact text from Step 0 grep 2 as the str_replace anchor.

---

## 📁 STEP 3 — Update `tasks.py` call site

**File:** `prompts/tasks.py` — 🔴 CRITICAL (sed only)

From Step 0 grep 3, the current cost calculation inside
`_apply_generation_result` at line ~2663:

```python
        cost = IMAGE_COST_MAP.get(
            image.quality or job.quality or 'medium', {}
        ).get(image.size or job.size, 0.034)
```

This spans 3 lines. Since `IMAGE_COST_MAP` is passed as a parameter to
`_apply_generation_result`, we need to add a local import of
`get_image_cost` instead. Use sed carefully with a multi-line approach:

Since the 3-line pattern is complex for sed, use Python to do the
replacement instead (safe for this targeted change):

```bash
python3 - << 'PYEOF'
import re

with open('prompts/tasks.py', 'r') as f:
    content = f.read()

old = (
    "        cost = IMAGE_COST_MAP.get(\n"
    "            image.quality or job.quality or 'medium', {}\n"
    "        ).get(image.size or job.size, 0.034)"
)
new = (
    "        from prompts.constants import get_image_cost\n"
    "        cost = get_image_cost(\n"
    "            image.quality or job.quality or 'medium',\n"
    "            image.size or job.size,\n"
    "        )"
)

assert old in content, "ANCHOR NOT FOUND — stop and report"
content = content.replace(old, new, 1)

with open('prompts/tasks.py', 'w') as f:
    f.write(content)

print("Done — 1 replacement made")
PYEOF
```

⚠️ The assertion will stop the script if the anchor is not found —
stop and report to developer if this happens.

Verify:
```bash
grep -n "get_image_cost\|IMAGE_COST_MAP.get" prompts/tasks.py | head -10
# Expected: get_image_cost used at the call site; IMAGE_COST_MAP.get
# still used for the IMAGE_COST_MAP import at line ~2915 (that's fine —
# the parameter passing can be cleaned up in a future spec)
```

---

## 📁 STEP 4 — Update `bulk_generator_views.py` call site

**File:** `prompts/views/bulk_generator_views.py` — Check tier from Step 0

From Step 0 grep 4, current line ~82:

```python
    cost_per_image = IMAGE_COST_MAP.get(job.quality, {}).get(job.size, 0.034)
```

Replace with:

```python
    cost_per_image = get_image_cost(job.quality, job.size)
```

Also update the import at the top of the file. From Step 0 grep 5, the
current import is:
```python
from prompts.constants import IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES
```

Add `get_image_cost` to the import:
```python
from prompts.constants import IMAGE_COST_MAP, SUPPORTED_IMAGE_SIZES, get_image_cost
```

⚠️ Keep `IMAGE_COST_MAP` in the import — it may be used elsewhere in
the views file. Only add `get_image_cost` to the existing import line.

---

## 📁 STEP 5 — MANDATORY VERIFICATION

```bash
# 1. Helper exists in constants.py
grep -n "def get_image_cost" prompts/constants.py

# 2. All 3 call sites updated
grep -n "get_image_cost" prompts/services/image_providers/openai_provider.py \
    prompts/tasks.py prompts/views/bulk_generator_views.py

# 3. No more bare IMAGE_COST_MAP.get().get() at the call sites
grep -n "IMAGE_COST_MAP\.get.*\.get" prompts/services/image_providers/openai_provider.py \
    prompts/views/bulk_generator_views.py
# Expected: 0 results (the call sites now use get_image_cost)

# 4. Import added to views
grep -n "get_image_cost" prompts/views/bulk_generator_views.py

# 5. System check
python manage.py check

# 6. Targeted test
python manage.py test prompts.tests.test_bulk_generator_job \
    prompts.tests.test_bulk_generator --verbosity=1 2>&1 | tail -10
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] `get_image_cost()` helper added to `constants.py` with docstring
- [ ] `openai_provider.py`: uses `get_image_cost`, imports updated
- [ ] `tasks.py`: uses `get_image_cost` at the cost calc site
- [ ] `views/bulk_generator_views.py`: uses `get_image_cost`, import updated
- [ ] No bare `IMAGE_COST_MAP.get().get()` at the 3 call sites
- [ ] `python manage.py check` returns 0 issues
- [ ] Targeted tests pass

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. Both must score 8.0+.

### 1. @code-reviewer
- Verify all 3 call sites updated — show Step 5 grep 2 output
- Verify no bare `IMAGE_COST_MAP.get().get()` at the 3 call sites
- Verify the helper docstring accurately describes the fallback behaviour
- Verify `IMAGE_COST_MAP` import retained where still needed in views
- Rating requirement: **8+/10**

### 2. @tdd-coach
- Verify existing price tests still pass with the helper
- Verify the helper itself is tested (either directly or via call site tests)
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- Any of the 3 call sites still using bare `IMAGE_COST_MAP.get().get()`
- `get_image_cost` not in `constants.py`
- Import missing from views
- Step 5 verification greps not shown

---

## 💾 COMMIT MESSAGE

```
refactor(bulk-gen): introduce get_image_cost() helper, eliminate duplicated price lookups

- constants.py: add get_image_cost(quality, size) helper — single call
  site for IMAGE_COST_MAP lookups
- openai_provider.py: get_cost_per_image() uses get_image_cost()
- tasks.py: _apply_generation_result() uses get_image_cost()
- bulk_generator_views.py: job view uses get_image_cost()
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_153_J_PRICE_HELPER.md`

---

**END OF SPEC**
