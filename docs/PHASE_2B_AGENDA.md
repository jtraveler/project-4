# PHASE 2B COMPLETE AGENDA

**Date:** February 9, 2026
**Status:** Ready to begin next session
**Reference Doc:** `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md`

---

## Pre-Requisite (Done)

- [x] Remove `[CAT DEBUG]` logging from `upload_views.py`

---

## Phase 2B-1: Model + Data Setup (1 CC session)

**Foundation — everything else depends on this.**

- Create `SubjectDescriptor` model (10 descriptor types, ~108 entries)
- Add `descriptors` M2M field to Prompt model
- Populate ~108 descriptors via data migration
- Add 19 new subject categories via data migration
- Remove "Seasonal & Holiday" category
- Rename "Animals & Wildlife" → "Wildlife & Nature Animals"
- Rename "Wedding & Bridal" → "Wedding & Engagement"
- Register `SubjectDescriptorAdmin` in admin

**Deliverables:** 3 migrations (`0048`, `0049`, `0050`), updated `models.py`, updated `admin.py`

---

## Phase 2B-2: AI Prompt Updates (1 CC session)

**Depends on:** 2B-1

- Replace OpenAI prompt in `tasks.py` with new structured prompt (Section 7.3 of design doc)
- Parse new `descriptors` JSON object from AI response
- Store descriptors in cache alongside categories (at 90% progress)
- Update description generation with SEO synonym rules
- Update tag generation with 10-tag limit and synonym rules
- Include anti-hallucination reinforcement instructions

**Deliverables:** Updated `tasks.py`

---

## Phase 2B-3: Upload Flow (1 CC session)

**Depends on:** 2B-2

- Update `upload_views.py` to read descriptors from cache/session
- Assign descriptors to prompt on save (same pattern as categories)
- Backend validation safety net — `SubjectDescriptor.objects.filter(name__in=...)` silently drops any hallucinated values
- Update tag limit validation from 5 to 10 throughout codebase
- Update any forms or templates that reference old tag limit

**Deliverables:** Updated `upload_views.py`, any form/template changes

---

## Phase 2B-4: Scoring Update (1 CC session)

**Depends on:** 2B-1

- Update `prompts/utils/related.py` weights to 20/25/25/10/10/10
- Add descriptor Jaccard similarity calculation
- Update pre-filter to include descriptor overlap as candidate criteria
- Update `DESIGN_RELATED_PROMPTS.md` to reflect new weights and descriptor scoring

**Deliverables:** Updated `related.py`, updated `DESIGN_RELATED_PROMPTS.md`

---

## Phase 2B-5: Backfill — AI Content (1 CC session + ~30-60 min runtime)

**Depends on:** 2B-1 through 2B-4 all complete

Updates ALL existing prompts (~800) with one OpenAI Vision call each:

| Field | What Changes |
|-------|-------------|
| Categories | Assigned (up to 5) — currently 0 on old prompts |
| Descriptors | Assigned (up to 10) — currently 0 on all prompts |
| Description | Regenerated with SEO synonym rules |
| Tags | Regenerated with 10-tag limit and synonym coverage |
| Title | Regenerated with better SEO keywords |
| Slug | Auto-updated from new title |
| Meta description | Auto-updated from new description |
| Schema/structured data | Auto-updated from new title + description + tags |

**Process:**
1. `heroku run python manage.py backfill_categories --dry-run --batch-size=5` — verify output
2. Review to confirm sensible categories, descriptors, descriptions
3. `heroku run python manage.py backfill_categories --batch-size=10` — real run

**Cost:** ~$8-24 (one OpenAI Vision API call per prompt)
**Runtime:** ~30-60 minutes for ~800 prompts

**Deliverables:** Updated backfill management command, all existing prompts updated

---

## Phase 2B-6: Media Migration — Cloudinary → B2 (1 CC session + ~1-2 hours runtime)

**Independent — can run before or after 2B-5, no AI dependency**

Migrates old prompt image/video files from Cloudinary to B2/Cloudflare CDN:

1. Download original image/video from Cloudinary
2. Generate B2 variants (thumb, medium, large, webp)
3. Upload all variants to B2
4. Update database URL fields (`b2_image_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`, `b2_webp_url`)
5. Verify CDN serving works for migrated files

**Cost:** Free (just bandwidth)
**Runtime:** ~1-2 hours for ~800 prompts

**Deliverables:** New `manage.py migrate_media_to_b2` command, all old prompts served from B2/Cloudflare

---

## Phase 2B-7: Browse/Filter UI (2-3 CC sessions)

**Depends on:** 2B-1 through 2B-5

- Multi-axis filter sidebar with checkbox groups by descriptor type
- URL-based filtering: `/browse/?gender=female&ethnicity=african-american&mood=cinematic`
- Category landing pages: `/categories/portrait/`
- Descriptor landing pages: `/browse/african-american/`
- Responsive filter UI (drawer on mobile, sidebar on desktop)
- SEO-optimized landing page titles and meta tags

**Deliverables:** New views, templates, URLs, CSS

---

## Separate Task: Deleted Prompt Pages Redesign (1-2 CC sessions)

**Independent of Phase 2B — can be done anytime**

Three issues identified from current pages:

| Issue | Current State | Fix |
|-------|--------------|-----|
| Grid layout | Flat 3-column, not masonry | Apply masonry CSS used everywhere else |
| Recommendation logic | Simple tag/generator match | Use new weighted scoring system (20/25/25/10/10/10) |
| UI design | Looks like an error page | Redesign to feel like a gentle redirect with polished UI |

Pages to redesign:
1. **"Prompt Temporarily Unavailable"** — prompt is in user's trash
2. **"Prompt No Longer Available"** — prompt permanently deleted

Additional requirement: Store tombstone metadata (generator, tags, categories, descriptors) before hard-delete so recommendations still work for permanently deleted prompts.

---

## End-of-Phase Docs Update

After all phases complete:
- Update `CLAUDE.md` with new models, commands, and features
- Update `PROJECT_FILE_STRUCTURE.md` with new files
- Update `DESIGN_RELATED_PROMPTS.md` with final scoring weights

---

## Suggested Execution Order (Next Sessions)

| Session | Task | Why This Order |
|---------|------|---------------|
| Next | Deleted prompt pages redesign | Visual impact, independent, quick win |
| Next | Phase 2B-1: Models + migrations | Foundation for everything |
| +1 | Phase 2B-2: AI prompt updates | Needs models |
| +1 | Phase 2B-3: Upload flow | Needs AI prompts |
| +2 | Phase 2B-4: Scoring update | Needs models |
| +2 | Phase 2B-5: Backfill AI content | Needs all of 2B-1 through 2B-4 |
| +3 | Phase 2B-6: Media migration to B2 | Independent, can run anytime |
| +4-6 | Phase 2B-7: Browse/filter UI | Needs all data in place |

**Total estimate: ~8-10 CC sessions across 4-6 chat sessions**

---

**END OF AGENDA**
