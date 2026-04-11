# CC_SPEC_153_A_GPT_IMAGE_15_UPGRADE.md
# Upgrade Image Generation to GPT-Image-1.5 — Full Metadata Update

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** Yes (`bulk_generator.html` — dropdown option)
**Migration Required:** Yes (choices-only + field defaults, no DDL)
**Agents Required:** 4 minimum
**Estimated Scope:** 7 production files + 3 test files + migration

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`tasks.py` is 🔴 CRITICAL (3500+ lines)** — use `sed` only, NO str_replace
4. **`models.py` is 🔴 CRITICAL (2000+ lines)** — maximum 2 str_replace calls
5. **DO NOT COMMIT** until developer confirms browser test and full suite passes
6. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

### GPT-Image-1.5 Upgrade (Option B — Full Metadata Update)

GPT-Image-1.5 was released by OpenAI on December 16, 2025. It is 4× faster,
20% cheaper, and has significantly better instruction following and spatial
accuracy than GPT-Image-1. This spec upgrades all image generation calls AND
ensures metadata (model choices, field defaults, task assignments, template
options) accurately reflects the model in use.

This is a full Option B upgrade — not a minimal API-call-only change. All
content seeded during Phase 1 must be tagged with the correct model.

### Context

- Current state: all generation calls use `model='gpt-image-1'`; all metadata
  fields, defaults, and task assignments reference `'gpt-image-1'`
- Desired state: all active generation uses `gpt-image-1.5`; old
  `gpt-image-1` remains as a valid choice for backward compatibility with
  existing records — it is NOT removed

### Confirmed Current State

- `openai_provider.py` lines ~132 and ~140: `model='gpt-image-1'` in both
  `images.edit()` and `images.generate()` calls ❌ → needs update
- `models.py` line ~693: `AI_GENERATOR_CHOICES` missing `gpt-image-1.5` ❌
- `models.py` lines ~2949, ~2960: `model_name` and `generator_category`
  defaults are `'gpt-image-1'` ❌ → need updating
- `tasks.py` lines ~3280, ~3317, ~3528, ~3585: `ai_generator='gpt-image-1'` ❌
- `bulk_generator_views.py` lines ~173, ~421, ~1308: hardcoded `'gpt-image-1'` ❌
- `bulk_generation.py` line ~144: default parameter `'gpt-image-1'` ❌
- `bulk_generator.html` line ~44: `gpt-image-1` option has `selected` ❌

---

## 🎯 OBJECTIVES

### Primary Goal

All image generation calls use `gpt-image-1.5`. All metadata accurately
reflects the model in use. `gpt-image-1` remains available as a backward-
compatible choice for existing records.

### Success Criteria

- ✅ `images.edit()` and `images.generate()` both use `model='gpt-image-1.5'`
- ✅ `('gpt-image-1.5', 'GPT-Image-1.5')` added to `AI_GENERATOR_CHOICES`
- ✅ `model_name` field default updated to `'gpt-image-1.5'`
- ✅ `generator_category` field default updated to `'gpt-image-1.5'`
- ✅ All 4 `ai_generator='gpt-image-1'` references in `tasks.py` updated
- ✅ All 3 hardcoded `'gpt-image-1'` defaults in `bulk_generator_views.py` updated
- ✅ `bulk_generation.py` default parameter updated
- ✅ Template dropdown shows `GPT-Image-1.5` as selected default; `GPT-Image-1` still present
- ✅ Migration applied cleanly — choices-only + default changes, no DDL
- ✅ All Category A default-assertion tests updated to `'gpt-image-1.5'`
- ✅ Category B backward-compatibility tests left unchanged
- ✅ 2 new choice tests added for `gpt-image-1.5`
- ✅ Full suite passes (1215+ tests)

---

## 📁 STEP 0 — MANDATORY GREPS (Do Before Any Edit)

⛔ **Never skip Step 0. Read existing state before writing anything.**

```bash
# 1. Verify both API call model strings
grep -n "model='gpt-image-1'" prompts/services/image_providers/openai_provider.py

# 2. Verify AI_GENERATOR_CHOICES location and exact content
grep -n "gpt-image-1" prompts/models.py | head -20

# 3. Verify model_name and generator_category defaults
grep -n "model_name\|generator_category" prompts/models.py | grep "default"

# 4. Verify tasks.py ai_generator references (expect 4 hits)
grep -n "ai_generator='gpt-image-1'" prompts/tasks.py

# 5. Verify views hardcoded defaults (expect 3 hits)
grep -n "gpt-image-1" prompts/views/bulk_generator_views.py

# 6. Verify bulk_generation.py default parameter
grep -n "gpt-image-1" prompts/services/bulk_generation.py

# 7. Verify template option line
grep -n "gpt-image-1" prompts/templates/prompts/bulk_generator.html

# 8. Check file sizes before editing
wc -l prompts/models.py prompts/tasks.py prompts/views/bulk_generator_views.py \
   prompts/services/image_providers/openai_provider.py \
   prompts/services/bulk_generation.py

# 9. Baseline test count
python manage.py test --verbosity=0 2>&1 | tail -3
```

**Do not proceed until all greps are complete and line numbers are verified.**

---

## 📁 FILES TO MODIFY

### File 1: `prompts/services/image_providers/openai_provider.py`

**Tier: ✅ SAFE — normal editing**

**Change 1 — `images.edit()` call (line ~132):**
```python
# BEFORE
                response = client.images.edit(
                    image=ref_file,
                    model='gpt-image-1',

# AFTER
                response = client.images.edit(
                    image=ref_file,
                    model='gpt-image-1.5',
```

**Change 2 — `images.generate()` call (line ~140):**
```python
# BEFORE
                response = client.images.generate(
                    model='gpt-image-1',

# AFTER
                response = client.images.generate(
                    model='gpt-image-1.5',
```

⚠️ **Both calls must be updated.** The `edit()` call is the reference-image
path; the `generate()` call is the text-only path. Upgrading only one means
half your jobs run on the old model.

---

### File 2: `prompts/models.py`

**Tier: 🔴 CRITICAL — 2000+ lines. Maximum 2 str_replace calls. Use 5+ line anchors.**

**Change 1 — Add `gpt-image-1.5` to `AI_GENERATOR_CHOICES` (str_replace call 1 of 2):**

Use the exact surrounding lines from Step 0 grep 2 as the anchor.
Add the new entry immediately AFTER the existing `gpt-image-1` entry:

```python
# BEFORE
    ('gpt-image-1', 'GPT-Image-1'),
    ('other', 'Other'),

# AFTER
    ('gpt-image-1', 'GPT-Image-1'),
    ('gpt-image-1.5', 'GPT-Image-1.5'),
    ('other', 'Other'),
```

**Change 2 — Update `model_name` default (str_replace call 2 of 2):**

Use the exact line from Step 0 grep 3. Update both `model_name` and
`generator_category` in a single str_replace call by anchoring across
both lines:

```python
# BEFORE
    model_name = models.CharField(max_length=100, default='gpt-image-1')

# AFTER
    model_name = models.CharField(max_length=100, default='gpt-image-1.5')
```

Then for `generator_category` — since models.py is CRITICAL tier with 2
str_replace max, and both calls are already used above, use `sed` for this
one remaining change:

```bash
sed -i "s/generator_category = models.CharField(max_length=50, default='gpt-image-1')/generator_category = models.CharField(max_length=50, default='gpt-image-1.5')/" prompts/models.py
```

Verify:
```bash
grep -n "generator_category.*default" prompts/models.py
```

⛔ **STOP if you cannot complete all 3 models.py changes within the
2 str_replace budget. Use sed for any overflow. Report to developer.**

---

### File 3: `prompts/tasks.py`

**Tier: 🔴 CRITICAL — 3500+ lines. DO NOT use str_replace. Use sed only.**

```bash
sed -i "s/ai_generator='gpt-image-1'/ai_generator='gpt-image-1.5'/g" prompts/tasks.py
```

**Verify 0 old occurrences remain:**
```bash
grep -n "ai_generator='gpt-image-1'" prompts/tasks.py
# Expected: no output
```

**Verify exactly 4 new occurrences:**
```bash
grep -n "ai_generator='gpt-image-1.5'" prompts/tasks.py
# Expected: exactly 4 lines (~3280, ~3317, ~3528, ~3585)
```

---

### File 4: `prompts/services/bulk_generation.py`

**Tier: ✅ SAFE — normal editing**

**Change 1 — default parameter (line ~144):**
```python
# BEFORE
        model_name: str = 'gpt-image-1',

# AFTER
        model_name: str = 'gpt-image-1.5',
```

---

### File 5: `prompts/views/bulk_generator_views.py`

**Tier: Check `wc -l` from Step 0 and apply appropriate editing strategy.**

Three references to update. From Step 0 grep 5, verify exact context for
each line before editing. All three use the same pattern:

**Change 1 — line ~173 (form default dict):**
```python
# BEFORE
        "model": "gpt-image-1",
# AFTER
        "model": "gpt-image-1.5",
```

**Change 2 — line ~421 (model_name fallback on job creation):**
```python
# BEFORE
        model_name=data.get('model', 'gpt-image-1'),
# AFTER
        model_name=data.get('model', 'gpt-image-1.5'),
```

**Change 3 — line ~1308 (read context from Step 0 grep 5 to confirm exact form):**
```python
# BEFORE
            model='gpt-image-1',
# AFTER
            model='gpt-image-1.5',
```

⚠️ Read the exact context of line ~1308 from Step 0 before editing. If the
context differs from a simple model string default, document the exact change
made in the completion report Section 3.

---

### File 6: `prompts/templates/prompts/bulk_generator.html`

**Tier: ✅ SAFE — template file**

**Change 1 — line ~44 (remove `selected` from 1.0, add 1.5 option as selected):**

```html
<!-- BEFORE -->
<option value="gpt-image-1" selected>GPT-Image-1</option>

<!-- AFTER -->
<option value="gpt-image-1">GPT-Image-1</option>
<option value="gpt-image-1.5" selected>GPT-Image-1.5</option>
```

⚠️ **Keep the `gpt-image-1` option in the list.** Removing it would break
form submissions that still pass `gpt-image-1` from saved state or external
sources.

---

## 🔄 MIGRATION

After editing `models.py`, run:

```bash
python manage.py makemigrations --name upgrade_gpt_image_15
```

Expected migration content:
- `AlterField` on `BulkGenerationJob.model_name` (default change)
- `AlterField` on `BulkGenerationJob.generator_category` (default change)
- `AlterField` on the `ai_generator` choices field (choices-only, no DDL)

Inspect the migration file and confirm no unexpected DDL before running:

```bash
python manage.py migrate
```

⚠️ **DO NOT backfill existing `BulkGenerationJob` records.** Old jobs were
generated with `gpt-image-1` and their `model_name` field must remain
accurate. Only new jobs get the 1.5 default.

---

## 🧪 TEST UPDATES

⛔ **Read ALL instructions before touching any test file.**

### Category A — Tests to UPDATE (default behaviour assertions)

These tests assert what the DEFAULT model is. Change expected values to
`'gpt-image-1.5'`.

**`prompts/tests/test_bulk_generator.py`**
- Line ~71: `self.assertEqual(job.model_name, 'gpt-image-1')` → `'gpt-image-1.5'`
- Line ~76: `self.assertEqual(job.generator_category, 'gpt-image-1')` → `'gpt-image-1.5'`

**`prompts/tests/test_bulk_generation_tasks.py`**
- Line ~174: `self.assertEqual(job.model_name, 'gpt-image-1')` → `'gpt-image-1.5'`

**`prompts/tests/test_bulk_page_creation.py`**
- Lines ~1150–1155: test checking `BulkGenerationJob` default `generator_category`
  → change expected value to `'gpt-image-1.5'`
- Lines ~717–725: test checking `ai_generator` on created `PromptPage`
  → change expected value to `'gpt-image-1.5'`
- Lines ~757–766: test checking `_call_openai_vision` called with `ai_generator=`
  → change expected value to `'gpt-image-1.5'`

### Category B — Tests to LEAVE UNCHANGED

Do NOT change these. They test backward compatibility or use explicit fixture
data, not defaults.

- `test_bulk_generation_tasks.py` lines ~1920, ~1960, ~2020, ~2055 — explicit
  `model_name='gpt-image-1'` in test setup data
- `test_bulk_page_creation.py` lines ~991–994 — asserts `'gpt-image-1'` is
  still in `AI_GENERATOR_CHOICES` (it still is — do NOT change)
- `test_bulk_page_creation.py` lines ~997–1000 — asserts `'gpt-image-1'`
  display label is `'GPT-Image-1'` (still true — do NOT change)
- `test_bulk_page_creation.py` lines ~1160–1179 — historical migration test
- `test_bulk_gen_rename.py` — all `ai_generator='gpt-image-1'` are fixtures
- `test_src6_source_image_upload.py` — `model_name='gpt-image-1'` is explicit
  fixture data

### New Tests to ADD

Add these two tests near the existing `gpt-image-1` choice tests (~line 991)
in `test_bulk_page_creation.py`:

```python
def test_gpt_image_15_in_ai_generator_choices(self):
    """'gpt-image-1.5' must be present in AI_GENERATOR_CHOICES."""
    valid_values = [c[0] for c in AI_GENERATOR_CHOICES]
    self.assertIn('gpt-image-1.5', valid_values)

def test_gpt_image_15_choice_display_label(self):
    """'gpt-image-1.5' choice must have display label 'GPT-Image-1.5'."""
    choices_dict = dict(AI_GENERATOR_CHOICES)
    self.assertEqual(choices_dict.get('gpt-image-1.5'), 'GPT-Image-1.5')
```

---

## 📁 STEP 1 — MANDATORY VERIFICATION

```bash
# 1. Both API call strings updated
grep -n "model='gpt-image-1.5'" prompts/services/image_providers/openai_provider.py
# Expected: 2 lines (images.edit and images.generate)

# 2. No old API call strings remain
grep -n "model='gpt-image-1'" prompts/services/image_providers/openai_provider.py
# Expected: 0 results

# 3. AI_GENERATOR_CHOICES has both entries
grep -n "gpt-image-1\|gpt-image-1.5" prompts/models.py | grep "CHOICES\|'gpt-image"

# 4. tasks.py fully updated
grep -n "ai_generator='gpt-image-1'" prompts/tasks.py
# Expected: 0 results
grep -n "ai_generator='gpt-image-1.5'" prompts/tasks.py
# Expected: 4 results

# 5. Template has both options, 1.5 selected
grep -n "gpt-image-1" prompts/templates/prompts/bulk_generator.html

# 6. Migration created
ls prompts/migrations/ | grep "gpt_image\|upgrade"

# 7. All tests pass
python manage.py test prompts --verbosity=0 2>&1 | tail -5
```

**Show all outputs in Section 3 of the report.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] All Step 0 greps completed and line numbers verified
- [ ] Step 1 verification greps all return expected results (shown in report)
- [ ] `images.edit()` uses `model='gpt-image-1.5'`
- [ ] `images.generate()` uses `model='gpt-image-1.5'`
- [ ] `gpt-image-1.5` added to `AI_GENERATOR_CHOICES` after `gpt-image-1`
- [ ] `model_name` default is `'gpt-image-1.5'`
- [ ] `generator_category` default is `'gpt-image-1.5'`
- [ ] `tasks.py` sed: 0 old occurrences, 4 new occurrences
- [ ] `bulk_generation.py` default parameter updated
- [ ] All 3 `bulk_generator_views.py` hardcoded defaults updated
- [ ] Template: `gpt-image-1.5` option present and `selected`; `gpt-image-1` still present without `selected`
- [ ] Migration created and applied cleanly
- [ ] `python manage.py check` returns 0 issues
- [ ] Category A tests updated; Category B tests unchanged
- [ ] 2 new choice tests added
- [ ] All tests pass

---

## 🤖 AGENT REQUIREMENTS

Minimum 4 agents. All must score 8.0+. Average must be ≥ 8.0.

### 1. @code-reviewer
**Verify all 8 model string locations are correct.**
- Confirm both `openai_provider.py` paths updated (edit AND generate)
- Confirm migration is choices-only with no unexpected DDL
- Confirm `gpt-image-1` option still present in template dropdown
- Show Step 1 verification outputs
- Rating requirement: **8+/10**

### 2. @django-security
**Security and correctness of the upgrade.**
- Confirm BYOK key handling unchanged — new model string does not affect
  key routing
- Confirm new model string is passed correctly to the OpenAI client in
  both `images.edit()` and `images.generate()` code paths
- Confirm no security regressions in any modified file
- Rating requirement: **8+/10**

### 3. @tdd-coach
**Test correctness and completeness.**
- Verify Category A tests updated and Category B tests left unchanged
- Verify 2 new choice tests added and assertions are valid (positive +
  explicit value checks — no vacuous assertions)
- Confirm test count has increased by exactly 2
- Rating requirement: **8+/10**

### 4. @accessibility-auditor
**Template change review.**
- Verify new dropdown option has correct `value` attribute (`gpt-image-1.5`)
- Verify label is human-readable (`GPT-Image-1.5`)
- Verify `selected` attribute is correctly placed on the new option
- Verify the old option is accessible and selectable
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- Either `openai_provider.py` API path still uses `gpt-image-1`
- `gpt-image-1` option removed from template (must be kept)
- Category B tests modified (must be unchanged)
- Migration contains unexpected DDL
- Step 1 verification outputs not shown in report

---

## 🖥️ TEMPLATE / UI CHANGE DETECTION

This spec modifies `bulk_generator.html`. The MANUAL BROWSER CHECK is MANDATORY.

After implementation, Mateo must:
1. Navigate to `/tools/bulk-ai-generator/`
2. Confirm `GPT-Image-1.5` is present in the model dropdown and selected by default
3. Confirm `GPT-Image-1` is still present in the dropdown (not removed)
4. Start a 1-image generation job — confirm it completes successfully

**Do NOT commit until Mateo confirms this browser check.**

---

## 🧪 TESTING CHECKLIST

### Post-Implementation

- [ ] `python manage.py check` — 0 issues
- [ ] Migration applied cleanly — no errors
- [ ] `python manage.py test prompts.tests.test_bulk_page_creation` — all pass
- [ ] `python manage.py test prompts.tests.test_bulk_generation_tasks` — all pass
- [ ] `python manage.py test prompts.tests.test_bulk_generator` — all pass

### ⛔ FULL SUITE GATE

This spec modifies `views/`, `models.py`, `tasks.py`, and `services/`.
The full test suite is MANDATORY:

```bash
python manage.py test
```

Expected: 1215+ tests passing, 0 failures.

---

## 📊 CC COMPLETION REPORT FORMAT

```markdown
═══════════════════════════════════════════════════════════════
SPEC 153-A: GPT-IMAGE-1.5 UPGRADE — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | X/10 | [findings] | Yes/No |
| 1 | @django-security | X/10 | [findings] | Yes/No |
| 1 | @tdd-coach | X/10 | [findings] | Yes/No |
| 1 | @accessibility-auditor | X/10 | [findings] | Yes/No |
| Average | | X.X/10 | — | Pass ≥8.0 / Fail |

## 📁 FILES MODIFIED

[List every file changed with line counts]

## 🧪 TESTING PERFORMED

[Full suite output — total count, failures, skipped]

## ✅ SUCCESS CRITERIA MET

[Checklist against all items in OBJECTIVES section]

## 🔄 MIGRATION STATUS

[Migration filename, what it contains, confirmation it applied cleanly]

## 🔄 DATA MIGRATION STATUS

N/A — no backfill required. Old BulkGenerationJob records retain 'gpt-image-1'.

## 🔁 SELF-IDENTIFIED FIXES APPLIED

[Any issues found and fixed during implementation. If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[Issues found but not in spec scope. If none: "None identified."]

## 📝 NOTES

[Step 1 verification grep outputs must be shown here]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT MESSAGE

```
feat(bulk-gen): upgrade image generation to GPT-Image-1.5

- openai_provider.py: update both images.edit() and images.generate() model strings
- models.py: add gpt-image-1.5 to AI_GENERATOR_CHOICES; update model_name and
  generator_category field defaults to gpt-image-1.5
- tasks.py: update all 4 ai_generator= assignments to gpt-image-1.5
- bulk_generation.py: update default parameter to gpt-image-1.5
- views/bulk_generator_views.py: update 3 hardcoded model defaults
- bulk_generator.html: add gpt-image-1.5 option as selected default; keep gpt-image-1
- tests: update 6 default-assertion tests; add 2 new gpt-image-1.5 choice tests
- migration 00XX: choices-only + default changes, no DDL
```

---

## ⛔ CRITICAL REMINDERS (Repeated)

- **DO NOT use str_replace on `tasks.py`** — use `sed` (CRITICAL tier)
- **DO NOT exceed 2 str_replace calls on `models.py`** — use sed for overflow
- **DO NOT remove `gpt-image-1` from the template dropdown** — keep it as non-default
- **DO NOT backfill existing `BulkGenerationJob` records**
- **DO NOT modify Category B tests** — they test backward compatibility
- **DO NOT commit until developer confirms browser test AND full suite passes**
- **BOTH `openai_provider.py` API paths must be updated** — missing either one means half your generation jobs still run on the old model

---

**END OF SPEC**
