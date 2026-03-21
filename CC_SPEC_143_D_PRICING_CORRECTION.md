# CC_SPEC_143_D_PRICING_CORRECTION.md
# GPT-Image-1 Pricing Correction — IMAGE_COST_MAP + COST_MAP + Docs

**Session:** 143
**Spec Type:** Code — commit after full test suite passes
**Report Path:** `docs/REPORT_143_D_PRICING_CORRECTION.md`
**Commit Message:** `fix: correct GPT-Image-1 pricing in IMAGE_COST_MAP and openai_provider (Session 143)`

---

## ⛔ STOP — READ BEFORE STARTING

```
╔══════════════════════════════════════════════════════════════╗
║  BOTH CODE FILES IN THIS SPEC ARE ✅ SAFE TIER               ║
║                                                              ║
║  constants.py          ✅ Safe (~452 lines)                  ║
║  openai_provider.py    ✅ Safe (~280 lines)                  ║
║                                                              ║
║  THIS IS A FINANCIAL INTEGRITY FIX.                          ║
║  Wrong prices mean users cannot trust their spend tracking.  ║
║  Every number change must be verified against the            ║
║  authoritative table in this spec. Do NOT use other          ║
║  sources or approximations.                                  ║
║                                                              ║
║  Work is REJECTED if:                                        ║
║  • Any agent scores below 8.0                                ║
║  • Any price value differs from the AUTHORITATIVE TABLE below ║
║  • COST_MAP in openai_provider.py is not refactored to       ║
║    delegate to IMAGE_COST_MAP (duplication must be removed)  ║
║  • The two maps can still drift out of sync after this spec  ║
║  • Tests are not updated to expect the new prices            ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📋 OVERVIEW

**Modifies UI/Templates:** No
**Modifies Code:** Yes — `prompts/constants.py`,
  `prompts/services/image_providers/openai_provider.py`
**Modifies Docs:** Yes — `BULK_IMAGE_GENERATOR_PLAN.md`

### What This Spec Does

Corrects a financial integrity bug: GPT-Image-1 pricing has been wrong in
two separate places since the feature launched. Users see the wrong estimated
cost on the bulk generator input page, and the actual cost recorded on the
job results page is also wrong — meaning users cannot accurately track their
real OpenAI API spend through the app.

Additionally, the current architecture has TWO separate cost maps that can
silently drift apart:
1. `openai_provider.py` — `COST_MAP` (flat, no size dimension)
2. `prompts/constants.py` — `IMAGE_COST_MAP` (size-aware, used for billing)

This spec fixes both maps AND eliminates the duplication by making
`openai_provider.py` delegate to `IMAGE_COST_MAP` instead of maintaining
its own stale copy.

### Why This Is a Financial Integrity Issue

The app is BYOK — OpenAI charges the user's own API key directly. But the
`actual_cost` field on `BulkGenerationJob` is the only way users can track
what they've spent through PromptFinder. If the `IMAGE_COST_MAP` in
`constants.py` is wrong, `actual_cost` is a lie — and users have no other
way to verify it within the app.

---

## 🔍 STEP 0 — MANDATORY GREPS BEFORE ANY CHANGES

Run ALL of these before touching any file. Record all findings in the report.

```bash
# 1. Confirm IMAGE_COST_MAP location and current values in constants.py
grep -n "IMAGE_COST_MAP\|'low'\|'medium'\|'high'\|0\.0" prompts/constants.py

# 2. Confirm COST_MAP location and current values in openai_provider.py
grep -n "COST_MAP\|get_cost_per_image\|'low'\|'medium'\|'high'" \
    prompts/services/image_providers/openai_provider.py

# 3. Find every call site of get_cost_per_image() across the codebase
grep -rn "get_cost_per_image\|COST_MAP" prompts/ --include="*.py"

# 4. Find every import of IMAGE_COST_MAP across the codebase
grep -rn "IMAGE_COST_MAP" prompts/ --include="*.py"

# 5. Find pricing-related tests that will need updating
grep -rn "IMAGE_COST_MAP\|get_cost_per_image\|0\.034\|0\.067\|0\.092\|0\.050\|0\.030\|0\.015" \
    prompts/tests/ --include="*.py"

# 6. Confirm current line count for both files
wc -l prompts/constants.py
wc -l prompts/services/image_providers/openai_provider.py

# 7. Confirm BULK_IMAGE_GENERATOR_PLAN.md exists and find the pricing table
grep -n "Cost per Image\|Low\|Medium\|High\|0\.0" BULK_IMAGE_GENERATOR_PLAN.md | head -20
```

**Gates:**
- If `get_cost_per_image()` is called from more than 2 places, list ALL call
  sites in the report before making any changes — the delegation refactor must
  update them all.
- If any existing test explicitly asserts a price value that this spec changes,
  that test MUST be updated in this spec. Do NOT leave tests asserting stale prices.
- Read `get_cost_per_image()` in full before touching it.

---

## 📐 AUTHORITATIVE PRICING TABLE — SOURCE OF TRUTH

These are the correct GPT-Image-1 prices as of March 2026 (official OpenAI
pricing page). **Every price in every file must match this table exactly.**
Do not use any other source.

| Quality | Size | Correct Price (USD) |
|---------|------|-------------------|
| `low` | `1024x1024` | `0.011` |
| `low` | `1536x1024` | `0.016` |
| `low` | `1024x1536` | `0.016` |
| `low` | `1792x1024` | `0.016` *(unsupported — historical only)* |
| `medium` | `1024x1024` | `0.042` |
| `medium` | `1536x1024` | `0.063` |
| `medium` | `1024x1536` | `0.063` |
| `medium` | `1792x1024` | `0.063` *(unsupported — historical only)* |
| `high` | `1024x1024` | `0.167` |
| `high` | `1536x1024` | `0.250` |
| `high` | `1024x1536` | `0.250` |
| `high` | `1792x1024` | `0.250` *(unsupported — historical only)* |

**Note on `low` quality:** The current `low` prices in `constants.py`
(`0.011`, `0.016`) are already correct. Do NOT change them.

---

## 📁 FILES TO MODIFY

### File 1: `prompts/constants.py`
**Tier:** ✅ Safe

Update the `medium` and `high` blocks in `IMAGE_COST_MAP`. The `low` block
is already correct — do NOT touch it.

**Find this exact block:**
```python
IMAGE_COST_MAP = {
    'low': {
        '1024x1024': 0.011,
        '1536x1024': 0.016,
        '1024x1536': 0.016,
        '1792x1024': 0.016,  # unsupported — retained for historical lookups
    },
    'medium': {
        '1024x1024': 0.034,
        '1536x1024': 0.046,
        '1024x1536': 0.046,
        '1792x1024': 0.046,  # unsupported — retained for historical lookups
    },
    'high': {
        '1024x1024': 0.067,
        '1536x1024': 0.092,
        '1024x1536': 0.092,
        '1792x1024': 0.092,  # unsupported — retained for historical lookups
    },
}
```

**Replace with:**
```python
IMAGE_COST_MAP = {
    'low': {
        '1024x1024': 0.011,
        '1536x1024': 0.016,
        '1024x1536': 0.016,
        '1792x1024': 0.016,  # unsupported — retained for historical lookups
    },
    'medium': {
        '1024x1024': 0.042,
        '1536x1024': 0.063,
        '1024x1536': 0.063,
        '1792x1024': 0.063,  # unsupported — retained for historical lookups
    },
    'high': {
        '1024x1024': 0.167,
        '1536x1024': 0.250,
        '1024x1536': 0.250,
        '1792x1024': 0.250,  # unsupported — retained for historical lookups
    },
}
```

Also update the comment above the map to document the change:

**Find:**
```python
# Cost per image by quality and size (as of March 2026)
```

**Replace with:**
```python
# Cost per image by quality and size (corrected March 2026 — Session 143)
# Source: https://openai.com/api/pricing/ (GPT-Image-1 per-image equivalents)
# Low: already correct. Medium and High were significantly under-estimated.
# High quality was off by ~2.5x (was $0.067/$0.092, now $0.167/$0.250).
```

**Verification grep after change:**
```bash
grep -n "0\.034\|0\.046\|0\.067\|0\.092" prompts/constants.py
# Expected: 0 results (all stale values removed)

grep -n "0\.042\|0\.063\|0\.167\|0\.250" prompts/constants.py
# Expected: 4 results each for medium and high (including the historical unsupported size)
```

---

### File 2: `prompts/services/image_providers/openai_provider.py`
**Tier:** ✅ Safe

**The Problem:** `openai_provider.py` has its own `COST_MAP` (flat, no size):
```python
COST_MAP = {
    'low': 0.015,
    'medium': 0.03,
    'high': 0.05,
}
```
And `get_cost_per_image()` uses it:
```python
def get_cost_per_image(self, size: str = '1024x1024', quality: str = 'medium') -> float:
    return self.COST_MAP.get(quality, 0.03)
```

This is wrong in two ways:
1. The prices are stale and don't match `IMAGE_COST_MAP`
2. It ignores the `size` parameter entirely, returning the same price for
   square and portrait/landscape

**The Fix:** Remove `COST_MAP` entirely. Update `get_cost_per_image()` to
delegate to `IMAGE_COST_MAP` from `prompts/constants.py`, which is already
size-aware and will now be the single source of truth.

**Change 1 — Remove `COST_MAP` class attribute:**

⛔ **IMPORTANT:** `openai_provider.py` has TWO class-level dicts:
- `COST_MAP` — remove this one entirely
- `TIER_RATE_LIMITS` — DO NOT touch this one, it is unrelated

Find and remove ONLY this block (use str_replace with the full block as anchor):
```python
    # Cost per image by quality (1024x1024 square)
    COST_MAP = {
        'low': 0.015,
        'medium': 0.03,
        'high': 0.05,
    }
```

Replace with: *(nothing — delete the entire block including the comment)*

**Change 2 — Update `get_cost_per_image()` to delegate to `IMAGE_COST_MAP`:**

**Find:**
```python
    def get_cost_per_image(
        self, size: str = '1024x1024', quality: str = 'medium'
    ) -> float:
        """Return cost per image based on quality."""
        return self.COST_MAP.get(quality, 0.03)
```

**Replace with:**
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
        return IMAGE_COST_MAP.get(quality, {}).get(size, 0.042)
```

**Why local import:** `openai_provider.py` is inside `prompts/services/image_providers/`
and importing from `prompts.constants` at module level risks circular imports.
The local import pattern is already established in this codebase (see tasks.py).

**Verification grep after change:**
```bash
# Confirm COST_MAP is gone
grep -n "COST_MAP" prompts/services/image_providers/openai_provider.py
# Expected: 0 results

# Confirm IMAGE_COST_MAP delegation is present
grep -n "IMAGE_COST_MAP\|get_cost_per_image" \
    prompts/services/image_providers/openai_provider.py
# Expected: IMAGE_COST_MAP appears in get_cost_per_image body
```

---

### File 3: `BULK_IMAGE_GENERATOR_PLAN.md`
**Tier:** Docs — no test suite gate needed

Find the pricing table in the Cost Calculator section. It currently shows
stale prices. Update it to match the authoritative table in this spec.

**Find the section with:**
```
GPT Image 1.5 - Cost per Image (Square 1024×1024):
- Low:    $0.009
- Medium: $0.034
- High:   $0.133
```

**Replace with:**
```
GPT-Image-1 - Cost per Image (Square 1024×1024):
- Low:    $0.011
- Medium: $0.042
- High:   $0.167

GPT-Image-1 - Cost per Image (Portrait 1024×1536 / Landscape 1536×1024):
- Low:    $0.016
- Medium: $0.063
- High:   $0.250

(Prices as of March 2026. Source: openai.com/api/pricing)
```

---

## 🔄 DATA MIGRATION

**No migration required.**

`actual_cost` on existing `BulkGenerationJob` records will remain as
historically recorded. These are already-spent amounts — correcting them
retroactively would be misleading. Only future jobs will use the new prices.

**Recommended manual note for Mateo:** If you want to understand actual past
spend, compare job `actual_cost` values against your OpenAI usage dashboard
at `platform.openai.com/usage` — the dashboard is authoritative.

---

## 🧪 TESTS TO WRITE / UPDATE

### Step 1 — Find existing pricing tests (Step 0 grep #5)

Any test that asserts specific price values must be updated to the new values.
Common patterns to search for and update:
- `0.034` → `0.042` (medium square)
- `0.046` → `0.063` (medium portrait/landscape)
- `0.067` → `0.167` (high square)
- `0.092` → `0.250` (high portrait/landscape)
- `0.050`, `0.030`, `0.015` → these were `openai_provider.py` COST_MAP values;
  any tests using them must be updated to use the new `IMAGE_COST_MAP` values

### Step 2 — New tests for `get_cost_per_image()` delegation

Add to the appropriate test file (find via Step 0 grep):

```python
# Test: get_cost_per_image() now returns size-aware prices
def test_get_cost_per_image_high_square(self):
    provider = OpenAIImageProvider(api_key='test')
    cost = provider.get_cost_per_image(size='1024x1024', quality='high')
    self.assertAlmostEqual(cost, 0.167)

def test_get_cost_per_image_high_portrait(self):
    provider = OpenAIImageProvider(api_key='test')
    cost = provider.get_cost_per_image(size='1024x1536', quality='high')
    self.assertAlmostEqual(cost, 0.250)

def test_get_cost_per_image_medium_landscape(self):
    provider = OpenAIImageProvider(api_key='test')
    cost = provider.get_cost_per_image(size='1536x1024', quality='medium')
    self.assertAlmostEqual(cost, 0.063)

def test_get_cost_per_image_low_square(self):
    provider = OpenAIImageProvider(api_key='test')
    cost = provider.get_cost_per_image(size='1024x1024', quality='low')
    self.assertAlmostEqual(cost, 0.011)

def test_get_cost_per_image_unknown_quality_falls_back(self):
    provider = OpenAIImageProvider(api_key='test')
    cost = provider.get_cost_per_image(size='1024x1024', quality='unknown')
    self.assertAlmostEqual(cost, 0.042)  # fallback is medium square

def test_get_cost_per_image_no_longer_ignores_size(self):
    """Regression: old COST_MAP ignored size entirely."""
    provider = OpenAIImageProvider(api_key='test')
    square_cost = provider.get_cost_per_image(size='1024x1024', quality='high')
    portrait_cost = provider.get_cost_per_image(size='1024x1536', quality='high')
    self.assertNotEqual(square_cost, portrait_cost)  # must differ by size
```

**All new tests must have BOTH positive and negative assertions.**
The regression test above (`assertNotEqual`) is the most critical —
it proves the old flat-COST_MAP bug cannot return.

---

## ✅ PRE-AGENT SELF-CHECK

Before running agents, verify ALL of the following:

- [ ] Every value in `IMAGE_COST_MAP` matches the AUTHORITATIVE PRICING TABLE
  in this spec exactly — no rounding, no approximations
- [ ] `low` values in `IMAGE_COST_MAP` are UNCHANGED (`0.011`, `0.016`) —
  they were already correct
- [ ] `COST_MAP` class attribute is completely removed from `openai_provider.py`
  — no references to it remain
- [ ] `get_cost_per_image()` now accepts `size` AND `quality` and looks up
  both in `IMAGE_COST_MAP`
- [ ] `TIER_RATE_LIMITS` class attribute in `openai_provider.py` is NOT removed
  — only `COST_MAP` is removed
- [ ] `get_cost_per_image()` gracefully handles `size=None` — `.get(size, 0.042)`
  returns the fallback when size is None (dict key lookup on None returns None
  which is not in IMAGE_COST_MAP, so fallback fires correctly)
- [ ] Fallback value in `get_cost_per_image()` is `0.042` (medium square —
  the most common generation size)
- [ ] All existing tests that referenced stale prices have been updated
- [ ] 6 new tests added for `get_cost_per_image()` including the regression test
- [ ] `BULK_IMAGE_GENERATOR_PLAN.md` pricing table updated
- [ ] Comment above `IMAGE_COST_MAP` updated with correction note
- [ ] Step 0 verification greps all ran and results documented in report
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 REQUIRED AGENTS

All agents must score 8.0+. Average must be ≥ 8.0.

| Agent | Model | Role | Focus |
|-------|-------|------|-------|
| `@python-pro` | sonnet | Python code quality | Local import correctness, dict `.get()` chain safety, fallback value is sensible, no `COST_MAP` references leak through |
| `@django-pro` | sonnet | Django correctness | Confirm constants import pattern is safe (no circular import risk), verify existing call sites of `get_cost_per_image()` all still work correctly |
| `@security-auditor` | opus | Financial integrity | Confirm wrong prices cannot be injected via env vars or request params; verify the fallback price is not exploitable (e.g. zero-cost fallback); confirm `actual_cost` write path uses the correct map |
| `@backend-security-coder` | opus | Backend security | Verify the `actual_cost` tracking in `tasks.py` correctly reads `IMAGE_COST_MAP` after this change; confirm no path bypasses the updated map; verify the local import cannot be monkey-patched at runtime to return zero |
| `@code-reviewer` | sonnet | Correctness + tests | Verify all 6 new tests are correct and non-vacuous; confirm all stale price assertions updated; regression test is meaningful; no test asserts old wrong values |
| `@api-documenter` | sonnet | Docs accuracy | Verify `BULK_IMAGE_GENERATOR_PLAN.md` pricing table matches the authoritative table in this spec; confirm no other doc files contain stale pricing references |

### Agent Ratings Table (Required)

```
| Round | Agent                    | Score | Key Findings              | Acted On? |
|-------|--------------------------|-------|---------------------------|-----------|
| 1     | @python-pro              | X/10  | summary                   | Yes/No    |
| 1     | @django-pro              | X/10  | summary                   | Yes/No    |
| 1     | @security-auditor        | X/10  | summary                   | Yes/No    |
| 1     | @backend-security-coder  | X/10  | summary                   | Yes/No    |
| 1     | @code-reviewer           | X/10  | summary                   | Yes/No    |
| 1     | @api-documenter          | X/10  | summary                   | Yes/No    |
| Avg   |                          | X.X/10| —                         | Pass/Fail |
```

**If average is below 8.0:** Fix ALL flagged issues and re-run. Do NOT
commit until a confirmed round scores 8.0+. Work is REJECTED otherwise.

---

## ⛔ BOTTOM REMINDERS

```
╔══════════════════════════════════════════════════════════════╗
║  TIER_RATE_LIMITS in openai_provider.py must NOT be removed  ║
║  EVERY PRICE VALUE must match the AUTHORITATIVE TABLE exactly ║
║  DO NOT change the 'low' prices — they are already correct   ║
║  COST_MAP in openai_provider.py must be COMPLETELY REMOVED   ║
║  get_cost_per_image() MUST use IMAGE_COST_MAP, not hardcoded ║
║  Fallback in get_cost_per_image() must be 0.042 (not 0.03)   ║
║  Regression test must prove size is no longer ignored        ║
║  All stale price assertions in tests must be updated         ║
║  Full test suite passes BEFORE commit                        ║
║  All 6 agents must score 8.0+ before commit                  ║
╚══════════════════════════════════════════════════════════════╝
```
