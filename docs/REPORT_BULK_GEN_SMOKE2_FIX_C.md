# SMOKE2-FIX-C: Bulk-Gen Published Prompts Missing b2_large_url
**Spec ID:** SMOKE2-FIX-C | **Commit:** `523586d` | **Type:** P0 Bug Fix | **Date:** 2026-03-11

---

## 1. Title + Spec ID + Commit Hash

| Field | Value |
|-------|-------|
| **Title** | Bulk-Gen Published Prompts Missing b2_large_url |
| **Spec ID** | SMOKE2-FIX-C |
| **Commit** | `523586d` |
| **Type** | P0 Bug Fix |
| **Date** | 2026-03-11 |
| **Series** | Third fix in SMOKE2 production smoke test series |

---

## 2. Executive Summary

Prompt detail pages for bulk-gen published prompts were rendering a "Media Missing" fallback state despite `processing_complete=True` being set correctly by SMOKE2-FIX-A. The root cause was that both bulk-gen publish functions set `b2_image_url`, `b2_thumb_url`, and `b2_medium_url` on the created prompt, but never set `b2_large_url` — and `display_large_url` (the property the template checks first) returns `None` when `b2_large_url` is unset with no fallback to `b2_image_url`. The fix adds `prompt_page.b2_large_url = gen_image.image_url` to both constructor sites in `prompts/tasks.py`, with a pending backfill query to repair already-published prompts in production.

---

## 3. Problem Analysis

### What Was Broken

After SMOKE2-FIX-A confirmed `processing_complete=True` was being set correctly, prompt detail pages for bulk-gen published prompts still rendered a "Media Missing" error state. The image was stored correctly in B2 and referenced by `b2_image_url` on the `Prompt` model — the data was present. The display layer simply never reached it.

### Root Cause Chain

```
prompt_detail.html
  └── {% elif prompt.display_large_url %}   ← primary image condition
        └── display_large_url (models.py)
              └── if self.b2_large_url: → None (never set!)
              └── (no fallback to b2_image_url)
              └── return None
  └── {% else %} → "Media Missing"          ← rendered instead
```

`display_large_url` is a model property that checks `b2_large_url` first and returns it if set. Unlike some other display properties, it does not fall back to `b2_image_url` when `b2_large_url` is `None`. Both bulk-gen publish functions (`create_prompt_pages_from_job` and `publish_prompt_pages_from_job` in `prompts/tasks.py`) correctly set the three other B2 URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`), but `b2_large_url` was never assigned.

### Scope of Impact

`display_large_url` is consumed in at least 5 places in `prompt_detail.html`:
- Main `<img>` element
- OG meta tag (`og:image`)
- Twitter card meta tag
- `<link rel="preload">` with `imagesrcset`
- JSON-LD Schema.org structured data

All five resolving to `None` meant the template fell through entirely to the `{% else %}` "Media Missing" branch, producing a completely broken detail page for every bulk-gen published prompt.

### Why It Wasn't Caught Earlier

The three-field pattern (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`) was established before `display_large_url` was the primary template condition. When the publish functions were written in Phases 6A–6B, the pattern was copied consistently across both sites — but `b2_large_url` was silently omitted from both. Unit tests mock the model fields and do not exercise the full template render path, so the gap was invisible until a live production smoke test.

---

## 4. Solution Overview

Add `prompt_page.b2_large_url = gen_image.image_url` to both bulk-gen prompt constructor sites in `prompts/tasks.py`:

1. `create_prompt_pages_from_job` — the original (non-concurrent) publish path, ~line 2860
2. `publish_prompt_pages_from_job` — the concurrent ThreadPoolExecutor publish path, ~line 3107

Both assignments use `gen_image.image_url` as the value, consistent with the existing thumb/medium fallback pattern. This is an acknowledged temporary fallback: all four URL fields point to the same full-resolution image until a dedicated thumbnail generation phase (Phase 7 scope note) produces properly sized variants.

No model changes, no migration, no new dependencies. The fix is surgical: two one-line additions, one in each constructor block.

A separate backfill query (documented in Section 8) is required to repair prompts already published to production before this fix was deployed.

---

## 5. Implementation Details

### File Modified

`prompts/tasks.py`

### Change 1 — `create_prompt_pages_from_job` (~line 2860)

**Before:**
```python
# Set B2 image URLs (thumb/medium are fallbacks until Phase 7 generates real thumbnails)
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url   # fallback — real thumbnails in Phase 7
prompt_page.b2_medium_url = gen_image.image_url  # fallback — real thumbnails in Phase 7
```

**After:**
```python
# Set B2 image URLs (thumb/medium/large are fallbacks until Phase 7 generates real thumbnails)
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url   # fallback — real thumbnails in Phase 7
prompt_page.b2_medium_url = gen_image.image_url  # fallback — real thumbnails in Phase 7
prompt_page.b2_large_url = gen_image.image_url   # fallback — real thumbnails in Phase 7
```

### Change 2 — `publish_prompt_pages_from_job` (~line 3107)

**Before:**
```python
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url
prompt_page.b2_medium_url = gen_image.image_url
```

**After:**
```python
prompt_page.b2_image_url = gen_image.image_url
prompt_page.b2_thumb_url = gen_image.image_url
prompt_page.b2_medium_url = gen_image.image_url
prompt_page.b2_large_url = gen_image.image_url   # fallback — real thumbnails in Phase 7
```

### Verification

```bash
grep -n "b2_large_url = gen_image" prompts/tasks.py
# → exactly 2 matches (lines 2860 and 3107) ✅
```

### IntegrityError Retry Path Safety

The `IntegrityError` slug-collision retry path in `publish_prompt_pages_from_job` reuses the same in-memory `prompt_page` object from the outer `transaction.atomic()` block. Because Django rolls back the DB transaction but does not reset the Python object's attributes, `b2_large_url` remains set on the in-memory object when the retry block's second `transaction.atomic()` executes. The value is therefore correctly persisted on retry without any additional assignment. Both agents confirmed this behaviour.

### Field Metadata

`b2_large_url` is a `URLField(null=True, blank=True)` added in migration `0040`. No schema change is needed — the field already exists on the `Prompt` model; the bug was purely a missing assignment.

---

## 6. Agent Usage Report

Two agents reviewed the fix prior to commit.

### @django-pro — 9/10

- Confirmed `b2_large_url` is the correct field name (`URLField`, `null=True`, migration `0040`); no migration required.
- Confirmed the backfill query using `F('b2_image_url')` is safe and idempotent for same-table column copy in `update()`.
- Confirmed `IntegrityError` retry paths are safe — in-memory object retains the assigned value across transaction rollback.
- Identified `b2_webp_url` as also unset in both functions. Flagged as a future risk if WebP delivery is added, but not currently a bug (no template property calls `display_webp_url`).
- Confirmed `display_large_url` is consumed in 5+ distinct locations in `prompt_detail.html` (OG meta, Twitter card, preload `imagesrcset`, JSON-LD schema, main `<img>`).

### @code-reviewer — 9/10

- Confirmed exactly 2 constructor sites exist in `tasks.py`, and both are fixed.
- Confirmed retry path correctness (same-object attribute persistence after rollback).
- Confirmed `F('b2_image_url')` is the correct Django ORM expression for same-table column copy in `update()`.
- Noted `display_large_url` is only consumed in detail/edit/admin contexts, not in listing grids, so the bug had no impact on gallery or homepage cards.
- Confirmed no templates reference `b2_large_url` directly — all access is through the `display_large_url` model property.
- Noted admin preview at `admin.py:323` will also now display correctly for bulk-gen prompts.

Both agents cleared the fix without requiring changes.

---

## 7. Test Results

| Metric | Result |
|--------|--------|
| **Total tests** | 1112 |
| **Passed** | 1100 |
| **Skipped** | 12 |
| **Failures** | 0 |
| **Errors** | 0 |
| **Exit code** | 0 ✅ |

No new tests were added for this fix. The change is a one-line field assignment at two known constructor sites; the correctness of the field name and model property were verified by agent review and `grep` confirmation rather than new unit tests. Existing `PublishTaskTests` and `PublishFlowTests` continue to pass.

---

## 8. Data Migration Status

### Schema Migration

None required. `b2_large_url` already exists on `Prompt` as a nullable `URLField` (migration `0040`).

```bash
python manage.py makemigrations --check
# → "No changes detected" ✅
```

### Data Backfill (Pending — Production)

Prompts published to production before this fix was deployed have `b2_large_url = NULL`. These must be backfilled after deployment. The following query is idempotent and safe to re-run.

```python
from django.db.models import F
from prompts.models import Prompt

broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    b2_large_url__isnull=True,
)
count = broken.count()
print(f"Found {count} bulk-gen prompts missing b2_large_url")

updated = broken.update(b2_large_url=F('b2_image_url'))
print(f"Updated {updated} prompts")

still_broken = Prompt.objects.filter(
    ai_generator='gpt-image-1',
    b2_image_url__isnull=False,
    b2_large_url__isnull=True,
).count()
print(f"Remaining broken: {still_broken} (should be 0)")
```

**Run via:** `heroku run python manage.py shell --app mj-project-4` then paste the above.

**Expected output** (assuming a small number of pre-fix published prompts):
```
Found N bulk-gen prompts missing b2_large_url
Updated N prompts
Remaining broken: 0 (should be 0)
```

**Idempotency:** The filter requires `b2_image_url__isnull=False` and `b2_large_url__isnull=True`. Prompts already backfilled will not match the second condition and will not be touched on re-run.

---

## 9. Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| `b2_large_url` added to `publish_prompt_pages_from_job` (~line 3107) | ✅ Done |
| `b2_large_url` added to `create_prompt_pages_from_job` (~line 2860) | ✅ Done |
| `grep` confirms exactly 2 matches for `b2_large_url = gen_image` | ✅ Verified |
| `python manage.py makemigrations --check` reports no changes | ✅ Confirmed |
| Full test suite passes (1112 tests, exit code 0) | ✅ Passed |
| @django-pro agent score ≥ 8/10 | ✅ 9/10 |
| @code-reviewer agent score ≥ 8/10 | ✅ 9/10 |
| Production data backfill query written and documented | ✅ Done |
| Production backfill executed | ⏳ Pending deploy |

---

## 10. Files Modified

| File | Change | Lines Affected |
|------|--------|----------------|
| `prompts/tasks.py` | Added `prompt_page.b2_large_url = gen_image.image_url` to `create_prompt_pages_from_job` | ~2860 |
| `prompts/tasks.py` | Added `prompt_page.b2_large_url = gen_image.image_url` to `publish_prompt_pages_from_job` | ~3107 |

No other files were modified. No new files were created.

---

## 11. Notes / Follow-up

### SMOKE2 Series Context

This is the third fix in the SMOKE2 production smoke test series:

| Fix | What It Did |
|-----|-------------|
| **SMOKE2-FIX-A** | Set `processing_complete=True` on bulk-gen published prompts — resolves "Media Processing" state |
| **SMOKE2-FIX-B** | Removed unwanted focus ring on page load |
| **SMOKE2-FIX-C** (this fix) | Set `b2_large_url` on bulk-gen published prompts — resolves "Media Missing" state |

SMOKE2-FIX-A was a necessary precondition but insufficient on its own: even with `processing_complete=True`, the template could not display the image because `display_large_url` returned `None`. Both fixes together are required for a fully functional detail page.

### b2_webp_url — Not a Bug Today, Future Risk

`b2_webp_url` is also not set in either publish function. Neither agent flagged this as a current bug because no template property calls `display_webp_url` (the property exists in the model but is not referenced in any template). If WebP delivery is added to the template layer in a future phase, `b2_webp_url` will need to be added to both constructor sites using the same pattern. This risk is noted here as a reference for that future work.

### Thumbnail Debt

All four B2 URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`) are currently set to the same full-resolution `gen_image.image_url` value. This is an acknowledged temporary fallback: the image is served at full resolution everywhere, including thumbnail contexts. Proper size variants (thumb, medium, large) require a dedicated post-generation processing step (resize + B2 upload). This was noted as Phase 7 scope in earlier planning and remains unimplemented. It is a performance concern, not a correctness bug.

### display_large_url Usage Coverage

After this fix, `display_large_url` resolves correctly for all bulk-gen prompts. The 5+ locations in `prompt_detail.html` that depend on it are now all functional:
- Main `<img>` element (primary image display)
- `og:image` meta tag (social sharing preview)
- Twitter card `twitter:image` meta tag
- `<link rel="preload">` with `imagesrcset` (LCP performance hint)
- JSON-LD Schema.org `image` property (structured data / SEO)
- Admin preview at `admin.py:323` (staff admin view)

### Production Deployment Checklist

1. Deploy commit `523586d`
2. Run backfill query via `heroku run python manage.py shell`
3. Confirm `Remaining broken: 0` in backfill output
4. Smoke test: visit a bulk-gen published prompt detail page and confirm image renders
5. Verify OG meta tag contains a valid image URL (use browser inspector or social card validator)
