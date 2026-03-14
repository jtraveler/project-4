# REPORT_129_C_SRC1_MODEL_FIELDS.md
# Session 129 — March 14, 2026

---

## Section 1 — Overview

Spec 129-C (SRC-1) adds the database foundation for the Source Image feature — an optional reference image URL that users can attach to each prompt row in the bulk generator. This spec adds 3 new fields across 2 models and creates migration 0076.

The feature spans 5 specs (SRC-1 through SRC-5). This spec is the data layer only — no UI, no backend processing, no publish pipeline changes.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `GeneratedImage` has `source_image_url` | ✅ Met | URLField, max_length=2000, blank=True, default='' |
| `GeneratedImage` has `b2_source_image_url` | ✅ Met | URLField, max_length=2000, blank=True, default='' |
| `Prompt` has `b2_source_image_url` | ✅ Met | URLField, max_length=2000, blank=True, default='' |
| All 3 fields use blank=True, default='' (not null=True) | ✅ Met | Correct pattern for URL fields in this project's newer convention |
| All 3 fields have descriptive help_text | ✅ Met | Each describes purpose and lifecycle |
| Migration is AddField only | ✅ Met | 3 AddField operations, no other operations |
| No existing fields or methods modified | ✅ Met | Only additive changes |
| `python manage.py check` passes | ✅ Met | 0 issues |
| `python manage.py migrate --check` clean | ✅ Met | Migration 0076 applied |
| No source_image field existed before this spec | ✅ Met | Step 0 grep returned no output |

---

## Section 3 — Changes Made

### Migration Number
`0076_add_source_image_fields.py`

### prompts/models.py — GeneratedImage model
After `source_credit` field (line ~2982), added:
```python
    # Source Image (SRC feature — optional reference image URL)
    source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='External URL of the source/reference image entered by the user'
    )
    b2_source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='B2 CDN URL of source image after download and re-upload (set by SRC-3)'
    )
```

### prompts/models.py — Prompt model
After `b2_video_thumb_url` field (line ~944), added:
```python
    # Source Image B2 URL (SRC feature — copied from GeneratedImage on publish)
    b2_source_image_url = models.URLField(
        max_length=2000,
        blank=True,
        default='',
        help_text='B2 CDN URL of source/reference image (admin-only display on prompt detail)'
    )
```

### Existing data
No existing data affected. All 3 fields have `default=''` — fully optional, no backfill needed.

---

## Section 4 — Issues Encountered and Resolved

No issues. Step 0 greps confirmed no pre-existing `source_image` fields. Migration generated cleanly with 3 `AddField` operations only.

---

## Section 5 — Remaining Issues

**Issue:** `Prompt.b2_source_image_url` uses `blank=True, default=''` while all existing `Prompt.b2_*` URL fields use `blank=True, null=True`. This creates a minor convention split — new field stores `''` for absent values while existing fields store `NULL`.
**Impact:** Non-functional. Both `None` and `''` are falsy, so `if prompt.b2_source_image_url:` behaves correctly in both cases.
**Priority:** P3
**Reason not resolved:** The newer `default=''` pattern is Django's recommended approach for text/URL fields and avoids two representations of "no data." The inconsistency is with legacy fields that predate this convention. No migration is warranted.

---

## Section 6 — Concerns and Areas for Improvement

**Note for future code:** `Prompt.b2_source_image_url` is `''` when absent; existing `Prompt.b2_image_url` etc. are `None` when absent. Any future code that checks `is None` rather than truthiness on B2 URL fields would silently fail for `b2_source_image_url`. Use `if prompt.b2_source_image_url:` (truthiness) not `if prompt.b2_source_image_url is not None:` for this field.

**max_length=2000:** New fields use `max_length=2000` vs `max_length=500` on existing B2 URL fields. This is intentional — `source_image_url` stores arbitrary external URLs (potentially long), and 2000 is consistent with `GeneratedImage.source_credit_url` pattern elsewhere in the codebase.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.2/10 | Fields correct. Migration clean (3 AddField only). null vs default='' convention split noted (non-blocking — newer pattern is better). max_length=2000 intentional. | N/A — no blocking issues |
| 1 | @code-reviewer | 8.5/10 | Naming follows b2_*_url convention. Placement semantically correct (after source_credit on GeneratedImage, after b2_video_thumb_url on Prompt). Help text clear and distinguishes all 3 fields. Same null vs default='' note. | N/A — no blocking issues |
| **Average** | | **8.85/10** | | **PASS (≥8.0)** |

---

## Section 8 — Recommended Additional Agents

No additional agents needed. This is a pure data migration with no logic implications.

---

## Section 9 — How to Test

```bash
python manage.py check
# Expected: 0 issues

python manage.py migrate --check
# Expected: clean (no pending migrations)

# Verify fields exist on models:
python manage.py shell -c "
from prompts.models import GeneratedImage, Prompt
gi = GeneratedImage.__dict__
print('source_image_url' in gi, 'b2_source_image_url' in gi)
p = Prompt.__dict__
print('b2_source_image_url' in p)
"
# Expected: True True / True
```

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD | `feat(src-1): add source_image_url fields to GeneratedImage and Prompt models` |

---

## Section 11 — What to Work on Next

1. **SRC-2 (Spec D):** Add source image URL input field to bulk generator UI (JS-rendered prompt boxes), client-side validation, include in generation payload
2. **SRC-3 (future):** Backend — download source image from URL, re-upload to B2, set `b2_source_image_url` on GeneratedImage
3. **SRC-4 (future):** Publish pipeline — copy `b2_source_image_url` from GeneratedImage to Prompt on publish; delete from B2 on prompt delete
4. **SRC-5 (future):** Prompt detail page — admin-only display with lightbox
