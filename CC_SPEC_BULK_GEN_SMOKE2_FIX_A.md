# CC_SPEC_BULK_GEN_SMOKE2_FIX_A — Published Bulk-Gen Prompt Pages Show Media Missing

**Spec ID:** SMOKE2-FIX-A
**Created:** March 10, 2026
**Type:** Micro-Spec — P0 Bug Fix
**Template Version:** v2.5
**Modifies UI/Templates:** No

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Use required agents** — @django-pro and @code-reviewer are MANDATORY
4. **Report agent usage** — Include ratings and findings in completion summary

**Work is REJECTED if agents are not run or average score is below 8.0/10.**

---

## 📋 OVERVIEW

### Publish Flow Creates Prompt Pages With No Visible Image

When a user publishes images from the Bulk Generator, the resulting Prompt detail pages show a "Media Missing" warning and "No Image Available" placeholder — despite the image URL being correctly stored in the database.

### Context

- Root cause was confirmed via production database audit on March 10, 2026
- `Prompt.b2_image_url` is correctly set to a valid CDN URL (e.g. `https://media.promptfinder.net/bulk-gen/...`)
- `Prompt.has_b2_media` returns `True`
- `Prompt.display_medium_url` resolves correctly
- **But `Prompt.processing_complete` is `False`**
- The `prompt_detail.html` template gates image display on `processing_complete` — prompts where it is `False` show the Media Missing state regardless of whether B2 URLs are set
- `publish_prompt_pages_from_job` in `tasks.py` never sets `processing_complete=True` when constructing the Prompt
- `create_prompt_pages_from_job` in `tasks.py` has the same omission
- Both functions were written before `processing_complete` was understood as a display gate — not just an upload-flow progress indicator
- A small number of already-published bulk-gen prompts in production have this field as `False` and need a one-time backfill

---

## 🎯 OBJECTIVES

### Primary Goal

All Prompt pages published through the Bulk Generator display their image correctly on the prompt detail page.

### Success Criteria

- ✅ `publish_prompt_pages_from_job` sets `processing_complete=True` in the Prompt constructor
- ✅ `create_prompt_pages_from_job` sets `processing_complete=True` in the Prompt constructor
- ✅ Both IntegrityError retry blocks are also correct (they reuse the same `prompt_page` object so no separate fix needed — but CC must verify this)
- ✅ Existing broken prompts in production are backfilled via the provided shell command
- ✅ All existing tests pass
- ✅ No new migrations required (no schema change)

---

## 🔍 PROBLEM ANALYSIS

### Current State

In `prompts/tasks.py`, `publish_prompt_pages_from_job` (~line 3101) constructs a Prompt like this:

```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',
)
```

`processing_complete` is not set, so it defaults to `False`.

`create_prompt_pages_from_job` (~line 2843) has the identical omission:

```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',
)
```

### Root Cause

`processing_complete` was designed for the single-image upload flow, where AI content generation happens asynchronously after the prompt is first saved. During that async window, `processing_complete=False` prevents the detail page from rendering incomplete content. The upload flow's background task sets it to `True` when processing finishes.

Bulk-gen prompts are fully processed before the Prompt record is ever created — the AI content, image URL, title, tags, and description are all complete at construction time. There is no async window. The field should always be `True` from the moment these prompts are created.

---

## 🔧 SOLUTION

### Approach

Add `processing_complete=True` to the `Prompt(...)` constructor in both functions. Then run a one-time backfill to fix existing broken records in production.

### Implementation Details

#### Change 1 — `publish_prompt_pages_from_job` in `prompts/tasks.py`

Find the Prompt constructor inside `publish_prompt_pages_from_job`. It currently ends with `moderation_status='approved',`. Add `processing_complete=True` as the next line.

**Before:**
```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 content policy applied at gen time
)
```

**After:**
```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 content policy applied at gen time
    processing_complete=True,      # bulk-gen prompts are fully processed at creation time
)
```

#### Change 2 — `create_prompt_pages_from_job` in `prompts/tasks.py`

Find the Prompt constructor inside `create_prompt_pages_from_job`. Apply the identical change.

**Before:**
```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy
)
```

**After:**
```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy
    processing_complete=True,      # bulk-gen prompts are fully processed at creation time
)
```

#### Verification Step

After making both changes, run:

```bash
grep -n "processing_complete=True" prompts/tasks.py
```

This must return exactly **2 matches** — one per function. If it returns 0 or 1, the change is incomplete.

### ♿ ACCESSIBILITY

No accessibility impact. This is a pure backend data fix with no template or UI changes.

---

## 📁 FILES TO MODIFY

### File 1: `prompts/tasks.py`

**Changes:**
- Add `processing_complete=True` to Prompt constructor in `publish_prompt_pages_from_job`
- Add `processing_complete=True` to Prompt constructor in `create_prompt_pages_from_job`

**No other files need to be modified.**

---

## 🔄 DATA MIGRATION

### Does this change affect existing data?

- [x] **YES** — Prompts already published via the bulk generator have `processing_complete=False` and need to be backfilled.

### Backfill Strategy — Option C: Django Shell

Run this command in production **after deploying the code change**:

```bash
heroku run python manage.py shell --app mj-project-4
```

Then in the shell:

```python
from prompts.models import Prompt
from django.db.models import Q

# Find all bulk-gen prompts with processing_complete=False
broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    processing_complete=False,
)
count = broken.count()
print(f"Found {count} broken bulk-gen prompts")

# Fix them
updated = broken.update(processing_complete=True)
print(f"Updated {updated} prompts")

# Verify
still_broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    processing_complete=False,
).count()
print(f"Remaining broken: {still_broken} (should be 0)")
```

### Records to Backfill

| Model | Filter | Field to Update | Expected Count |
|-------|--------|-----------------|----------------|
| `Prompt` | `ai_generator='gpt-image-1'` AND `b2_image_url IS NOT NULL` AND `processing_complete=False` | `processing_complete` → `True` | Small (< 20 during testing phase) |

**IMPORTANT:** Run the backfill shell command immediately after deploying the code change to production. Include the output in the completion report.

---

## ✅ PRE-AGENT SELF-CHECK

⛔ **Before invoking ANY agent, verify all of the following:**

- [ ] `grep -n "processing_complete=True" prompts/tasks.py` returns exactly 2 matches
- [ ] Both matches are in `publish_prompt_pages_from_job` and `create_prompt_pages_from_job` respectively
- [ ] No other files were modified
- [ ] `python manage.py makemigrations --check` reports no changes needed (no schema change)
- [ ] Full test suite passes: `python manage.py test`

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents

**1. @django-pro**
- Task: Review the Prompt constructor change in both task functions
- Focus: Confirm `processing_complete=True` is the correct field name, confirm it's in the right position in the constructor, confirm no migration is needed, verify the backfill query is safe and idempotent
- Rating requirement: 8+/10

**2. @code-reviewer**
- Task: Review the overall change for correctness and completeness
- Focus: Are there any other places in the bulk gen pipeline where a Prompt is constructed that also need this fix? Is the backfill query correct? Are there edge cases (e.g. prompts with no b2_image_url that might also need fixing)?
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- Change was applied to only one of the two functions (both are required)
- A Django migration was generated (there should be none — this is a default value change, not a schema change)
- Backfill query was not provided or is not idempotent

### Agent Reporting Format

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. @django-pro - [X/10] - [findings]
2. @code-reviewer - [X/10] - [findings]

Critical Issues Found: [N]
High Priority Issues: [N]
Recommendations Implemented: [N]

Overall Assessment: [APPROVED / NEEDS REVIEW]
```

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation

- [ ] Confirm `processing_complete` field exists on Prompt model: `grep -n "processing_complete" prompts/models.py`
- [ ] Confirm current default value is `False`: it should be `default=False`

### Post-Implementation

- [ ] `grep -n "processing_complete=True" prompts/tasks.py` returns exactly 2 matches
- [ ] `python manage.py makemigrations --check` — must report **No changes detected**
- [ ] Full test suite passes: `python manage.py test` (report total count)

### ⛔ FULL SUITE GATE

`tasks.py` was modified → **Full test suite is mandatory.**

Run: `python manage.py test`
All tests must pass. Report total count in completion report.

---

## 📊 CC COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
SMOKE2-FIX-A: PUBLISHED BULK-GEN PROMPT IMAGES - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY
[agent report]

## 📁 FILES MODIFIED
[list with line numbers of changes]

## 🧪 TESTING PERFORMED
[test output — total tests, pass/fail]

## ✅ SUCCESS CRITERIA MET
- [ ] processing_complete=True in publish_prompt_pages_from_job
- [ ] processing_complete=True in create_prompt_pages_from_job
- [ ] grep confirms exactly 2 matches
- [ ] makemigrations --check reports no changes
- [ ] Full test suite passes

## 🔄 DATA MIGRATION STATUS
[Output of backfill shell command — total found, updated, remaining]

## 📝 NOTES
[Any observations]

═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
fix(bulk-gen): set processing_complete=True on published prompt pages

Prompt pages created by publish_prompt_pages_from_job and
create_prompt_pages_from_job were defaulting to processing_complete=False,
causing prompt_detail.html to show "Media Missing" despite b2_image_url
being correctly set.

Bulk-gen prompts are fully processed at creation time — there is no
async processing window — so processing_complete must be True from birth.

Also run backfill to fix existing published prompts.

Fixes: publish and create task constructors (2 changes in tasks.py)
Backfill: Prompt.objects.filter(ai_generator='gpt-image-1',
          b2_image_url__isnull=False, processing_complete=False)

Agent ratings: @django-pro X/10, @code-reviewer X/10
```
