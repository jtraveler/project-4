# Future Feature: Multi-Image Reference Upload (Bulk Generator)

**Status:** Planned (not yet started)
**Priority:** After Phase 5-7 completion
**Depends on:** File upload infrastructure, Backblaze B2 integration for reference images

---

## Feature Description

Allow users to upload up to 4 reference images per bulk generation job. Currently the Reference Image section is a single upload zone placeholder (no-op). This feature would make it fully functional with multi-image support.

## UX Design (Approved Direction)

### Upload Flow
1. Dotted upload zone shows "Drop files or click to upload" initially
2. User uploads first image → thumbnail appears inside the dotted zone on the left
3. A "+" icon box appears to the right of the thumbnail for the next upload
4. Up to 4 images can be uploaded in a horizontal row within the dotted zone
5. After 4th image, the "+" icon disappears (max reached)
6. If images overflow the dotted zone width, horizontal auto-scroll within the container

### Thumbnail Interactions (on hover)
- **Swap/Change icon** (rotate arrows icon) — top-left of thumbnail, allows replacing the image
- **Trash icon** — top-right of thumbnail, removes the image
- Both icons appear on a semi-transparent dark overlay on hover (see saved mockup reference)
- Each thumbnail has a numbered badge (1, 2, 3, 4) in the top-left corner

### NSFW Validation
- NSFW checks are NOT done on upload — they happen when user clicks "Generate All"
- All reference images are validated in a batch of OpenAI Vision API calls BEFORE generation starts
- If any image fails NSFW check, generation is blocked and the specific image is flagged with an error
- This keeps the flow to one validation pass at generate time rather than per-upload

## Technical Requirements

### Model Changes
- Current: `BulkGenerationJob.reference_image_url` (single URLField)
- Future: Need to support multiple reference images per job
- Options:
  a. JSONField storing array of image URLs/paths
  b. Separate `ReferenceImage` model with FK to BulkGenerationJob
  c. Reuse GeneratedImage model with a `is_reference=True` flag
- Recommendation: JSONField is simplest for v1 since we don't need to query reference images independently

### Storage
- **For now:** Reference images are temporary (session-only, not persisted after generation)
- **Future:** When "Saved Image Library" feature is built, reference images will be stored permanently in Backblaze B2
- Temp storage approach: Upload to B2 with a `temp/` prefix and TTL-based cleanup, OR use client-side File API to hold images in memory until generation

### File Upload Infrastructure
- Client-side: FileReader API for thumbnails, FormData for upload
- Accept: PNG, JPG, JPEG, WebP — max 10MB per image
- Server endpoint needed: `POST /tools/bulk-ai-generator/api/upload-reference/` returning a temporary URL
- Or: Send images as base64 in the generation request (simpler but larger payload)

### API Changes
- `api_start_generation`: Accept array of reference image URLs instead of single URL
- `api_validate_reference_image`: Batch endpoint accepting multiple images, returns per-image results
- OpenAI Vision API calls: One per image (cannot be combined with Image-1 generation calls — different endpoints/formats)

### Related Future Feature: Saved Image Library
- Persistent storage of reference images in Backblaze B2
- User can save frequently-used reference photos to their library
- Library picker in the Reference Image section (similar to Character Selection)
- Eliminates re-uploading the same photos repeatedly

## Files That Will Need Changes
- `prompts/models.py` — BulkGenerationJob reference image field(s)
- `prompts/views/bulk_generator_views.py` — Upload endpoint, batch validation
- `prompts/services/bulk_generation.py` — Multi-image reference handling
- `prompts/templates/prompts/bulk_generator.html` — Upload zone UI
- `static/js/bulk-generator.js` — File upload, thumbnail preview, hover overlay
- `static/css/pages/bulk-generator.css` — Thumbnail grid, hover overlay, scroll container
- New migration for model changes
