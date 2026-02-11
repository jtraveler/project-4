# Related Prompts — System Reference

**File:** `prompts/utils/related.py`
**Feature:** "You Might Also Like" section on prompt detail pages
**Status:** Phase 2B-9 complete (IDF-weighted scoring, stop-word infrastructure, published-only counting)
**Last Updated:** February 10, 2026

---

## Scoring Algorithm

Six weighted factors, split 90% content similarity / 10% tiebreakers:

| Factor | Weight | Method | Notes |
|--------|--------|--------|-------|
| Tag overlap | 30% | IDF-weighted similarity | Rare tags worth more |
| Category overlap | 25% | IDF-weighted similarity | Rare categories worth more |
| Descriptor overlap | 35% | IDF-weighted similarity | Key content signals: ethnicity, mood, setting |
| Same AI generator | 5% | Binary match | Tiebreaker only |
| Similar engagement | 3% | Inverse normalized like difference | Tiebreaker only |
| Recency | 2% | Linear decay over 90 days | Tiebreaker only |

Content similarity (tags + categories + descriptors) = 90% of score.
Non-relevance factors (generator + engagement + recency) = 10% tiebreakers.

---

## IDF Weighting

All three content factors use inverse document frequency weighting:

```
weight = 1 / log(prompt_count + 1)
```

- Items appearing on 1 prompt: weight = 1.44
- Items appearing on 5 prompts: weight = 0.56
- Items appearing on 20 prompts: weight = 0.33
- Items appearing on 50 prompts: weight = 0.26

**Effect:** A tag shared by 2 prompts contributes ~2.5x more than a tag shared by 20 prompts. Rare, meaningful signals (e.g., "giraffe", "motorcycle") dominate over ubiquitous ones (e.g., "portrait", "ai-art").

**Published-only counting:** IDF functions filter to `status=1, deleted_at__isnull=True` so drafts and soft-deleted prompts don't inflate frequency counts. Tags use a `published_ids` subquery (taggit generic relations), while categories and descriptors use `Count('prompts', filter=Q(...))`.

### Scoring Formula (per content factor)

```python
shared_items = source_set & candidate_set
weighted_shared = sum(idf_weight[item] for item in shared_items)
max_possible = sum(idf_weight[item] for item in source_set)
score = weighted_shared / max_possible  # 0.0 to 1.0
```

When `max_possible == 0` (all source items are stop-words), falls back to:
```python
score = len(shared_items) / len(source_set)
```

---

## Stop-Word Infrastructure

**Current status:** DISABLED (`STOP_WORD_THRESHOLD = 1.0`)

Items appearing on more than `STOP_WORD_THRESHOLD * total_prompts` published prompts get zero weight. Infrastructure is in place but disabled because the 25% threshold was too aggressive at 51 prompts (zeroing items on just 13+ prompts), causing random noise to dominate.

**Re-enable at:** 200+ published prompts, set `STOP_WORD_THRESHOLD = 0.25`.

At 51 prompts with 25% threshold, these were zeroed:
- Tags: portrait (60.8%), ai-art (54.9%), female (43.1%), woman (39.2%), photorealistic (39.2%), fashion (33.3%)
- Categories: Photorealistic (78.4%), Portrait (66.7%), Fashion & Style (49.0%), Digital Art (39.2%)
- Descriptors: Warm Tones (72.5%), Young Adult (52.9%), Female (47.1%), Outdoor/Nature (33.3%), Cool Tones (29.4%), Cinematic (29.4%), Caucasian/White (29.4%), Whimsical (25.5%)

---

## Pre-filtering

Only scores prompts sharing at least 1 tag, 1 category, OR 1 descriptor with the source prompt. Generator is excluded from the pre-filter to avoid pulling in irrelevant candidates that only match on platform (e.g., all Midjourney prompts).

Falls back to same AI generator only when prompt has zero tags, zero categories, AND zero descriptors.

**Safety cap:** If pre-filter returns >500 candidates, limits to 500 most recent before scoring.

---

## Performance

| Optimization | Details |
|-------------|---------|
| IDF caching | 3 IDF weight dictionaries built once, reused for all candidates |
| Prefetch | `prefetch_related('tags', 'categories', 'descriptors', 'likes')` |
| Set operations | Tag/category/descriptor IDs converted to Python sets for O(1) intersection |
| Annotated likes | `Count('likes')` annotated on queryset, not N+1 per candidate |
| Published count | Single `COUNT(*)` query for `total_prompts` |
| Total queries | ~7 fixed queries (candidates + 3 IDF lookups + total count + prefetches), not N+1 |

---

## Weight Evolution

| Factor | Phase 1 | Phase 2 | Phase 2B | 2B-9a | 2B-9c (final) |
|--------|---------|---------|----------|-------|---------------|
| Tag overlap | 60% | 35% | 20% | 35% | **30%** |
| Category overlap | -- | 35% | 25% | 30% | **25%** |
| Descriptor overlap | -- | -- | 25% | 25% | **35%** |
| Same AI generator | 15% | 10% | 10% | 5% | **5%** |
| Similar engagement | 15% | 10% | 10% | 3% | **3%** |
| Recency | 10% | 10% | 10% | 2% | **2%** |

---

## Phase 2B-9 Sub-Phases

| Sub-Phase | What Changed | Commit |
|-----------|-------------|--------|
| 2B-9a | Rebalanced weights to 90/10 content/tiebreaker split | `5bba5a6` |
| 2B-9b | Added IDF weighting to tags and categories | `1104f08` |
| 2B-9c | Extended IDF to descriptors, rebalanced 30/25/35 | `450110b` |
| 2B-9c (revised) | AI prompt subject-accuracy rules for better data quality | `38e0eef` |
| 2B-9d | Stop-word filtering (implemented then disabled at 51 prompts) | `4d56fdb`, `5a07245` |
| 2B-9d (fix) | Published-only IDF counting (drafts/trash excluded) | `87476e7` |

---

## Frontend Integration

| Component | Details |
|-----------|---------|
| AJAX endpoint | `/prompt/<slug>/related/` — 18 per page, 60 max |
| Layout | CSS `column-count` responsive grid (4/3/2/1 columns) |
| Video autoplay | IntersectionObserver on desktop (skip mobile/reduced-motion) |
| Load More | Reinitializes video observer after appending new cards |
| Section heading | "You Might Also Like" (justifies showing loosely related content) |

---

## Files

| File | Purpose |
|------|---------|
| `prompts/utils/related.py` | Scoring algorithm (275 lines) |
| `prompts/views/prompt_views.py` | `related_prompts_ajax` view |
| `prompts/urls.py` | `/prompt/<slug>/related/` endpoint |
| `prompts/templates/prompts/prompt_detail.html` | "You Might Also Like" section |
| `prompts/templates/prompts/partials/_prompt_card_list.html` | AJAX partial for Load More |
| `static/css/pages/prompt-detail.css` | Related prompts section styles |

---

**END OF DESIGN DOCUMENT**
