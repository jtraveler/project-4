# CC_SPEC_153_H_NEEDS_SEO_REVIEW.md
# Fix: Set needs_seo_review=True on Bulk-Created Prompt Pages

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** 1 file — `prompts/tasks.py` (sed only)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`prompts/tasks.py` is 🔴 CRITICAL (3500+ lines)** — sed ONLY, NO str_replace
4. **DO NOT COMMIT** until full suite passes
5. **WORK IS REJECTED** if any agent scores below 8/10

---

## 📋 OVERVIEW

### `needs_seo_review` Not Set on Bulk-Created Pages

When bulk generation creates prompt pages via `create_prompt_pages_from_job`,
the `Prompt` object is created WITHOUT `needs_seo_review=True`. This means
bulk-created pages are never flagged for the SEO review queue, and content
seeded at scale will silently bypass the SEO workflow.

The single-upload pipeline correctly sets `needs_seo_review=True` at lines
1437 and 1538 of `tasks.py`. The bulk pipeline does not.

### Confirmed Current State

In `create_prompt_pages_from_job` (~line 3284):
```python
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1.5',
    status=1 if job.visibility == 'public' else 0,
    moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy
    processing_complete=True,      # bulk-gen prompts are fully processed at creation time
)
```

`needs_seo_review=True` is missing. Also the comment says "GPT-Image-1"
which is stale — should be GPT-Image-1.5.

---

## 🎯 OBJECTIVES

- ✅ `needs_seo_review=True` set on all Prompt objects created by the bulk pipeline
- ✅ Stale "GPT-Image-1" comment at line ~3323 updated to "GPT-Image-1.5"
- ✅ All Prompt creation sites in the bulk pipeline verified and fixed
- ✅ Full suite passes

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find ALL Prompt( instantiation sites in tasks.py
grep -n "prompt_page = Prompt(" prompts/tasks.py

# 2. Read the full Prompt constructor in create_prompt_pages_from_job
sed -n '3280,3310p' prompts/tasks.py

# 3. Find publish_prompt_pages_from_job — does it also create Prompt objects?
sed -n '3466,3530p' prompts/tasks.py

# 4. Confirm needs_seo_review field exists on Prompt model
grep -n "needs_seo_review" prompts/models.py | head -5

# 5. Confirm single-upload pipeline sets it correctly (reference pattern)
grep -n "needs_seo_review" prompts/tasks.py | head -10

# 6. File size
wc -l prompts/tasks.py
```

**Do not proceed until all greps are complete.**

After Step 0 grep 3: determine whether `publish_prompt_pages_from_job`
also creates new `Prompt` objects. If yes, it also needs `needs_seo_review=True`.
If it only publishes already-created pages, no change needed there.

---

## 📁 STEP 1 — Add `needs_seo_review=True` to Prompt constructor

**File:** `prompts/tasks.py`
**Strategy: sed ONLY — CRITICAL tier**

### Change 1 — Add `needs_seo_review=True` after `processing_complete=True`

The anchor is the unique `processing_complete=True,      # bulk-gen prompts`
line in `create_prompt_pages_from_job`:

```bash
sed -i "s/                processing_complete=True,      # bulk-gen prompts are fully processed at creation time/                processing_complete=True,      # bulk-gen prompts are fully processed at creation time\n                needs_seo_review=True,             # bulk-created pages always require SEO review/" prompts/tasks.py
```

### Change 2 — Fix stale "GPT-Image-1" comment on the same Prompt constructor

```bash
sed -i "s/moderation_status='approved',  # staff-created; GPT-Image-1 already applied content policy/moderation_status='approved',  # staff-created; GPT-Image-1.5 content policy applied at generation time/" prompts/tasks.py
```

### Change 3 — If `publish_prompt_pages_from_job` also creates Prompt objects

From Step 0 grep 3: if it creates new Prompt objects, apply the same
`needs_seo_review=True` fix there too using a separate sed command with
the appropriate anchor. Document in Section 3 of the report whether this
was needed.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm needs_seo_review=True added
grep -n "needs_seo_review" prompts/tasks.py
# Expected: includes the new True assignment in the bulk pipeline

# 2. Confirm stale comment fixed
grep -n "GPT-Image-1 already applied\|GPT-Image-1.5 content policy" prompts/tasks.py
# Expected: no "GPT-Image-1 already applied" remains at that location

# 3. Confirm processing_complete line still intact
grep -n "processing_complete=True" prompts/tasks.py | head -5

# 4. System check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — ALL Prompt creation sites identified
- [ ] `needs_seo_review=True` added to every Prompt creation site in bulk pipeline
- [ ] Stale "GPT-Image-1" comment fixed
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @django-security
- Confirm `needs_seo_review=True` is set at the model level, not in a
  separate save — so it cannot be missed by a failed save
- Confirm the fix covers ALL Prompt creation sites in the bulk pipeline
- Rating requirement: **8+/10**

### 2. @tdd-coach
- Verify a test exists (or is added) that asserts `needs_seo_review=True`
  on prompts created by `create_prompt_pages_from_job`
- If no test exists, add one: create a job, run the pipeline, assert
  `prompt_page.needs_seo_review is True`
- Rating requirement: **8+/10**

### 3. @code-reviewer
- Verify Step 2 verification outputs shown in report
- Verify the fix is consistent with how `needs_seo_review` is set in
  the single-upload pipeline (lines 1437, 1538)
- Verify stale comment correctly updated
- Rating requirement: **8+/10**

### ⛔ MINIMUM REJECTION CRITERIA
- `needs_seo_review` not set on every Prompt creation site
- No test covering this behaviour
- Step 2 verification greps not shown in report

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): set needs_seo_review=True on bulk-created prompt pages

All Prompt objects created by create_prompt_pages_from_job now have
needs_seo_review=True. Previously bulk-created pages silently bypassed
the SEO review queue. Also fixes stale 'GPT-Image-1' comment.
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_153_H_NEEDS_SEO_REVIEW.md`

---

**END OF SPEC**
