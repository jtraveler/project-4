# Phase 2B-2: AI Prompt Updates — CC Specification

---

## ⛔ STOP — READ BEFORE STARTING ⛔

```
╔══════════════════════════════════════════════════════════════════╗
║  MANDATORY: Read docs/CC_COMMUNICATION_PROTOCOL.md FIRST        ║
║  MANDATORY: Use wshobson/agents (minimum 3 agents)              ║
║  MANDATORY: All agent ratings must be 8+/10                     ║
║  Work will be REJECTED if agents are not used and reported      ║
╚══════════════════════════════════════════════════════════════════╝
```

**DO NOT start coding until you have:**
1. Read `docs/CC_COMMUNICATION_PROTOCOL.md`
2. Read this entire specification end to end
3. Read the current `prompts/tasks.py` file completely
4. Identified which wshobson/agents you will use

---

## 📋 OVERVIEW

### Task: Phase 2B-2 — AI Prompt Update (tasks.py Rewrite)

Replace the OpenAI Vision prompt in `tasks.py` with the new three-tier taxonomy prompt. Update all parsing, validation, caching, and database assignment logic to handle the new `descriptors` field alongside expanded categories.

### Context

Phase 2B-1 (COMPLETE) created the `SubjectDescriptor` model (109 descriptors across 10 types), expanded `SubjectCategory` from 25 to 46 entries, and added the `Prompt.descriptors` M2M field.

Now we need the AI to actually ASSIGN those descriptors and new categories. The current `tasks.py` has an old OpenAI prompt that references removed/renamed categories and has no concept of descriptors.

### Reference Document

Full design: `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` — Sections 7.2, 7.3

### Why This Is Urgent

The current AI prompt (in `_build_analysis_prompt()`) still references OLD category names:
- "Animals & Wildlife" → renamed to "Wildlife & Nature Animals"
- "Seasonal & Holiday" → REMOVED
- "Meme & Humor" → renamed to "Comedy & Humor"

Any upload right now will silently drop these categories via the `filter(name__in=...)` safety net. The new prompt fixes this.

---

## 🎯 OBJECTIVES

### Primary Goal

Update `tasks.py` so that every new upload receives:
- Correct category assignments (from the new 46-category list)
- Descriptor assignments (from the new 109-descriptor taxonomy)
- SEO-optimized descriptions with synonym rules
- Up to 10 tags (previously 5)
- Up to 5 categories (previously 3)

### Success Criteria

- ✅ `_build_analysis_prompt()` replaced with new structured prompt from design doc Section 7.3
- ✅ `max_tokens` increased from 1000 to 1500 (new response is larger)
- ✅ `_parse_ai_response()` handles nested `descriptors` JSON object
- ✅ `_validate_ai_result()` validates descriptors field
- ✅ `generate_ai_content_cached()` includes descriptors in cache writes (at 90% and 100%)
- ✅ `_update_prompt_with_ai_content()` assigns descriptors to prompt (Layer 4 validation)
- ✅ Category limit updated from 3 to 5 in cache path
- ✅ Tag limit confirmed as 10 (already correct in cache path)
- ✅ No other functions in tasks.py are changed
- ✅ All existing error handling, SSRF protection, and fail-closed patterns preserved

---

## 🔍 CURRENT STATE vs DESIRED STATE

### What Changes

| Area | Current | New |
|------|---------|-----|
| AI prompt | Old 25-category list, no descriptors, old ethnicity approach | New 46-category list + 109 descriptors + SEO synonym rules |
| `max_tokens` | 1000 | 1500 |
| Category limit (cache) | `[:3]` on line ~988 | `[:5]` |
| Category limit (direct) | 3 implicit | 5 explicit |
| Descriptors in cache | Not present | `descriptors` dict included at 90% and 100% |
| Descriptors in DB | Not assigned | Assigned via Layer 4 validation in `_update_prompt_with_ai_content` |
| `_parse_ai_response` regex | `\{[^{}]*"title"[^{}]*\}` — can't match nested objects | New approach that handles nested `{}` in descriptors |
| `_validate_ai_result` | Only checks title, tags | Also checks descriptors is dict |
| Fallback content | No descriptors | Includes empty `descriptors: {}` |

### What Does NOT Change

- `run_nsfw_moderation()` — untouched
- `_is_safe_image_url()` — untouched
- `_download_and_encode_image()` — untouched
- `_sanitize_content()` — untouched
- `_generate_unique_slug_with_retry()` — untouched
- `_handle_ai_failure()` — untouched (it doesn't set categories either, just generic tags)
- `rename_prompt_files_for_seo()` — untouched
- `update_ai_job_progress()` / `get_ai_job_status()` — untouched
- All SSRF protection, base64 encoding, URL validation — untouched
- `response_format={"type": "json_object"}` — keep this, it helps

---

## 📁 FILES TO MODIFY

### File 1: `prompts/tasks.py`

This is the ONLY file modified in this spec. There are **8 specific changes** within it.

---

#### CHANGE 1: Replace `_build_analysis_prompt()` function (lines ~366-531)

**Replace the ENTIRE function** with the new version below. The new prompt is taken directly from `docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md` Section 7.3.

**IMPORTANT:** The new prompt does NOT use `prompt_text`, `ai_generator`, or `available_tags` parameters. However, **keep the function signature identical** so callers don't break. The parameters are simply unused in the new version (they were already barely used — `ai_generator` was only in the fallback text, and `available_tags` was just a suggestion list).

```python
def _build_analysis_prompt(prompt_text: str, ai_generator: str, available_tags: list) -> str:
    """
    Build the prompt for OpenAI Vision API.

    Phase 2B: Three-tier taxonomy prompt with anti-hallucination design.
    Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md Section 7.3

    Args kept for backwards compatibility but ai_generator and available_tags
    are no longer interpolated into the prompt to reduce hallucination risk.
    """
    return '''Analyze this image and return a JSON object with the following fields.

VALIDATION RULE: You MUST only return values that appear EXACTLY as written in the
lists below. Do NOT invent, modify, combine, or abbreviate any value. If you are unsure
about any assignment, OMIT it entirely. An omission is always better than an incorrect
assignment.

═══════════════════════════════════════════════════
FIELD 1: "title" (string)
═══════════════════════════════════════════════════
A concise, SEO-optimized title for this image. Max 60 characters.
Include the most important subject and style keywords.

═══════════════════════════════════════════════════
FIELD 2: "description" (string)
═══════════════════════════════════════════════════
A detailed, SEO-optimized description. 2-4 sentences. Follow these CRITICAL SEO RULES:

ETHNICITY SYNONYMS — when describing ethnicity, ALWAYS include multiple search terms:
  * "Black" → also include "African-American" (or "African" if clearly African context)
  * "Hispanic" → also include "Latino" or "Latina"
  * "Indian" → also include "South Asian" and "Desi"
  * "Asian" → specify "East Asian," "Southeast Asian," etc. when identifiable
  * "Arab" → also include "Middle Eastern"
  * "White" → also include "Caucasian" or "European" if contextually appropriate

GENDER SYNONYMS — include both specific and general:
  * Include "woman" AND "female," "man" AND "male"

NICHE TERMS — include when applicable:
  * AI Influencer images: "AI influencer," "AI avatar," "virtual influencer," "digital influencer"
  * Person + business/smart-casual attire + professional mood: "LinkedIn headshot," "LinkedIn profile photo,"
    "professional headshot," "corporate portrait" (any framing — not limited to headshots)
  * Boudoir: "boudoir photography," "intimate portrait," "sensual portrait"
  * Styled portraits: naturally mention "virtual photoshoot" when applicable
  * Holiday images: include holiday name AND season AND mood keywords

SPELLING VARIANTS — always include both US and UK spellings in descriptions and tags:
  * "coloring book" AND "colouring book"
  * "watercolor" AND "watercolour"
  * "color" AND "colour" (when color is a key term)
  * "gray" AND "grey"
  * "center" AND "centre" (when relevant)
  * "favor" AND "favour" (when relevant)

Naturally weave in 2-3 synonym variants of key terms without keyword stuffing.

═══════════════════════════════════════════════════
FIELD 3: "tags" (array of strings, up to 10)
═══════════════════════════════════════════════════
SEO-optimized keyword tags. Use hyphens for multi-word tags (e.g., "african-american").

Include:
- Primary subject (e.g., "portrait", "landscape")
- Demographic synonyms (e.g., both "african-american" AND "black-woman")
- Mood/atmosphere keywords
- Art style (e.g., "photorealistic", "oil-painting")
- Specific elements (e.g., "coffee", "red-car", "neon-lights")
- LinkedIn photos: include "linkedin-headshot", "linkedin-profile-photo", "professional-headshot",
  "corporate-portrait", "business-portrait" (triggered by professional attire + corporate mood,
  ANY framing — not limited to shoulders-up headshots)
- Other niche terms when applicable: "ai-influencer", "ai-avatar", "virtual-photoshoot",
  "boudoir", "burlesque", "pin-up", "glamour-photography"
- YouTube thumbnails: include "youtube-thumbnail", "thumbnail-design", "cover-art",
  "video-thumbnail", "podcast-cover", "social-media-graphic"
- Maternity shoots: include "maternity-shoot", "maternity-photography", "pregnancy-photoshoot",
  "baby-bump", "expecting-mother", "maternity-portrait"
- 3D/forced perspective: include "3d-photo", "forced-perspective", "facebook-3d", "3d-effect",
  "fisheye-portrait", "pop-out-effect", "parallax-photo"
- Photo restoration: include "photo-restoration", "ai-restoration", "restore-old-photo",
  "colorized-photo", "ai-colorize", "vintage-restoration"
- US/UK spelling variants: include BOTH spellings when applicable, e.g. "coloring-book" AND
  "colouring-book", "watercolor" AND "watercolour"

═══════════════════════════════════════════════════
FIELD 4: "categories" (array of strings, up to 5)
═══════════════════════════════════════════════════
Choose from this EXACT list only:

Portrait, Fashion & Style, Landscape & Nature, Urban & City, Sci-Fi & Futuristic,
Fantasy & Mythical, Wildlife & Nature Animals, Interior & Architecture, Abstract & Artistic,
Food & Drink, Vehicles & Transport, Horror & Dark, Anime & Manga, Photorealistic,
Digital Art, Illustration, Product & Commercial, Sports & Action, Music & Entertainment,
Retro & Vintage, Minimalist, Macro & Close-up, Text & Typography, Comedy & Humor,
Wedding & Engagement, Couple & Romance, Group & Crowd, Cosplay, Tattoo & Body Art,
Underwater, Aerial & Drone View, Concept Art, Wallpaper & Background, Character Design,
Pixel Art, 3D Render, Watercolor & Traditional, Surreal & Dreamlike,
AI Influencer / AI Avatar, Headshot, Boudoir, YouTube Thumbnail / Cover Art,
Pets & Domestic Animals, Maternity Shoot, 3D Photo / Forced Perspective,
Photo Restoration

SPECIAL RULES:
- "AI Influencer / AI Avatar": ONLY if single person + polished/glamorous + fashion-styled
  + luxury/aspirational setting or social-media-ready framing.
- "Headshot": Shoulders-up + single person + clean background.
- "Boudoir": Lingerie/revealing clothing + intimate setting + sensual posing/lighting.
  Based on styling, NOT body type.
- "YouTube Thumbnail / Cover Art": Designed composition with at least 2 of: bold text overlay,
  exaggerated expression, bright saturated colors, landscape orientation, split composition,
  arrow/circle graphics. Must be intentionally designed as a clickable cover/preview.
- "Maternity Shoot": Pregnant subject + styled photoshoot elements (flowing gowns, belly poses,
  dreamy lighting, partner involvement, baby props). Genre intent, not just pregnancy visible.
- "3D Photo / Forced Perspective": At least 2 of: fisheye/wide-angle distortion, object projected
  toward viewer in extreme foreground, three-layer depth separation, breaking frame boundaries,
  worm's-eye perspective, dramatic scale distortion.
- "Photo Restoration": At least 2 of: before/after layout, colorized B&W, enhanced old photo
  with period-specific context, old format borders with modern clarity, visible damage repair.
  NOT new images in vintage style (that's "Retro & Vintage").
- "Comedy & Humor": Intentionally comedic — memes, parody, satire, caricature, absurd humor,
  funny juxtapositions. NOT merely playful or whimsical.

═══════════════════════════════════════════════════
FIELD 5: "descriptors" (object with typed arrays)
═══════════════════════════════════════════════════
Return an object with these EXACT keys. Each value is an array of strings.
Choose ONLY from the options listed under each key.
Leave an array empty [] if nothing applies or if you are not confident.

"gender" (0-1 values, ONLY if person clearly visible):
  Male, Female, Androgynous

"ethnicity" (0-1 values, ONLY if >90% confident — OMIT if ANY doubt):
  African-American / Black, African, Hispanic / Latino, East Asian,
  South Asian / Indian / Desi, Southeast Asian, Middle Eastern / Arab,
  Caucasian / White, Indigenous / Native, Pacific Islander, Mixed / Multiracial

"age" (0-1 values, ONLY if person clearly visible):
  Baby / Infant, Child, Teen, Young Adult, Middle-Aged, Senior / Elderly

"features" (0-3 values, ONLY visually prominent intentional features):
  Vitiligo, Albinism, Heterochromia, Freckles, Natural Hair / Afro,
  Braids / Locs, Hijab / Headscarf, Bald / Shaved Head, Glasses / Eyewear,
  Beard / Facial Hair, Colorful / Dyed Hair, Wheelchair User, Prosthetic,
  Scarring, Plus Size / Curvy, Athletic / Muscular, Pregnancy / Maternity

"profession" (0-2 values, ONLY if identifiable through uniform/equipment/context):
  Military / Armed Forces, Healthcare / Medical, First Responder,
  Chef / Culinary, Business / Executive, Scientist / Lab, Artist / Creative,
  Teacher / Education, Athlete / Sports, Construction / Blue Collar,
  Pilot / Aviation, Musician / Performer, Royal / Regal, Warrior / Knight,
  Astronaut, Cowboy / Western, Ninja / Samurai

"mood" (1-2 values, almost every image has a mood):
  Dark & Moody, Bright & Cheerful, Dreamy / Ethereal, Cinematic, Dramatic,
  Peaceful / Serene, Romantic, Mysterious, Energetic, Melancholic, Whimsical,
  Eerie / Unsettling, Sensual / Alluring, Professional / Corporate,
  Vintage / Aged Film

"color" (1-2 values, almost every image has a color palette):
  Warm Tones, Cool Tones, Monochrome, Neon / Vibrant, Pastel, Earth Tones,
  High Contrast, Muted / Desaturated, Dark / Low-Key, Gold & Luxury

"holiday" (0-1 values, ONLY if clearly related to a specific holiday):
  Valentine's Day, Christmas, Halloween, Easter, Thanksgiving, New Year,
  Independence Day, St. Patrick's Day, Lunar New Year, Día de los Muertos,
  Mother's Day, Father's Day, Pride, Holi, Diwali, Eid, Hanukkah

"season" (0-1 values, ONLY if clear seasonal visual cues):
  Spring, Summer, Autumn / Fall, Winter

"setting" (0-1 values, if primary setting is determinable):
  Studio / Indoor, Outdoor / Nature, Urban / Street, Beach / Coastal,
  Mountain, Desert, Forest / Woodland, Space / Cosmic, Underwater

═══════════════════════════════════════════════════
EXAMPLE RESPONSE
═══════════════════════════════════════════════════
{
  "title": "Cinematic African-American Woman Golden Hour Portrait",
  "description": "A stunning cinematic portrait of a young African-American woman bathed in golden hour light. This photorealistic image captures the Black female subject with natural afro hair, wearing elegant gold jewelry against a warm urban backdrop. The dramatic lighting and rich warm tones create a powerful, aspirational mood perfect for AI avatar and virtual photoshoot inspiration. Ideal for creators seeking diverse, high-quality portrait prompts featuring African-American beauty and cinematic photography techniques.",
  "tags": ["african-american", "black-woman", "portrait", "cinematic", "golden-hour", "photorealistic", "natural-hair", "afro", "urban-portrait", "ai-avatar"],
  "categories": ["Portrait", "AI Influencer / AI Avatar", "Photorealistic"],
  "descriptors": {
    "gender": ["Female"],
    "ethnicity": ["African-American / Black"],
    "age": ["Young Adult"],
    "features": ["Natural Hair / Afro"],
    "profession": [],
    "mood": ["Cinematic", "Dramatic"],
    "color": ["Warm Tones", "Gold & Luxury"],
    "holiday": [],
    "season": [],
    "setting": ["Urban / Street"]
  }
}

RESPOND WITH ONLY THE JSON OBJECT. No markdown, no backticks, no preamble.'''
```

---

#### CHANGE 2: Increase `max_tokens` (line ~263)

In `_call_openai_vision()`, find:
```python
max_tokens=1000,
```

Replace with:
```python
max_tokens=1500,
```

The new response includes the `descriptors` object which adds ~200-400 tokens.

---

#### CHANGE 3: Update `_parse_ai_response()` regex fallback (lines ~534-563)

The current last-resort regex (`\{[^{}]*"title"[^{}]*\}`) uses `[^{}]*` which cannot match the nested `{}` inside the `descriptors` object.

**Replace the ENTIRE `_parse_ai_response()` function** with:

```python
def _parse_ai_response(content: str) -> dict:
    """
    Parse the AI response JSON.

    Handles cases where AI adds markdown code blocks or extra text.
    Updated in Phase 2B to handle nested objects (descriptors).
    """
    try:
        # Try direct JSON parse first (works with response_format=json_object)
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find outermost JSON object (handles nested braces in descriptors)
    # Find first { and last } to get the complete JSON object
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(content[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.error(f"[AI Generation] Failed to parse AI response: {content[:200]}")
    return {'error': 'Failed to parse AI response'}
```

---

#### CHANGE 4: Update `_validate_ai_result()` (lines ~566-587)

Add validation for the new `descriptors` field.

**Replace the ENTIRE `_validate_ai_result()` function** with:

```python
def _validate_ai_result(result: dict) -> dict:
    """
    Validate that parsed AI result has required fields.

    Returns the result if valid, or an error dict if invalid.
    Phase 2B: Also validates descriptors and categories fields.
    """
    if 'error' in result:
        return result

    # Check for required fields
    if 'title' not in result:
        logger.warning("[AI Generation] AI response missing 'title' field")
        result['title'] = None

    if 'tags' not in result:
        result['tags'] = []

    # Ensure tags is a list
    if not isinstance(result.get('tags'), list):
        result['tags'] = []

    # Ensure categories is a list
    if not isinstance(result.get('categories'), list):
        result['categories'] = []

    # Ensure descriptors is a dict with expected structure
    if not isinstance(result.get('descriptors'), dict):
        result['descriptors'] = {}

    # Validate each descriptor type is a list (not a string or other type)
    valid_types = {'gender', 'ethnicity', 'age', 'features', 'profession',
                   'mood', 'color', 'holiday', 'season', 'setting'}
    cleaned_descriptors = {}
    for dtype in valid_types:
        value = result['descriptors'].get(dtype, [])
        if isinstance(value, list):
            # Ensure all items are strings
            cleaned_descriptors[dtype] = [str(v) for v in value if v]
        else:
            cleaned_descriptors[dtype] = []
    result['descriptors'] = cleaned_descriptors

    return result
```

---

#### CHANGE 5: Update category limit in `generate_ai_content_cached()` (line ~988)

Find:
```python
        # Clean categories - trimmed, unique, max 3
        clean_categories = []
        cat_seen = set()
        for cat in categories[:3]:  # Max 3 categories
```

Replace with:
```python
        # Clean categories - trimmed, unique, max 5
        clean_categories = []
        cat_seen = set()
        for cat in categories[:5]:  # Max 5 categories (Phase 2B)
```

---

#### CHANGE 6: Add descriptors to cache writes in `generate_ai_content_cached()`

This change has **5 sub-parts** within the `generate_ai_content_cached()` function.

**6a.** After the line that extracts `categories` from `ai_result` (around line 974), add descriptor extraction:

Find:
```python
        categories = ai_result.get('categories', [])
```

Add directly after:
```python
        descriptors = ai_result.get('descriptors', {})
```

**6b.** After the existing category cleaning block (the `clean_categories` / `cat_seen` loop), add descriptor cleaning. Add this block directly after the category cleaning:

```python
        # Clean descriptors - ensure dict of lists with string values
        clean_descriptors = {}
        valid_descriptor_types = {'gender', 'ethnicity', 'age', 'features', 'profession',
                                  'mood', 'color', 'holiday', 'season', 'setting'}
        for dtype in valid_descriptor_types:
            values = descriptors.get(dtype, [])
            if isinstance(values, list):
                clean_descriptors[dtype] = [str(v).strip()[:100] for v in values[:5] if v]
            else:
                clean_descriptors[dtype] = []
```

**6c.** Update the 90% cache write to include descriptors:

Find:
```python
        # 90% - Storing partial results (categories available even if user submits early)
        # Write data to cache at 90% so categories are available before complete=True
        update_ai_job_progress(
            job_id, 90,
            complete=False,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            error=None
        )
```

Replace with:
```python
        # 90% - Storing partial results (categories + descriptors available even if user submits early)
        # Write data to cache at 90% so categories/descriptors are available before complete=True
        update_ai_job_progress(
            job_id, 90,
            complete=False,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            descriptors=clean_descriptors,
            error=None
        )
```

**6d.** Update the 100% cache write to include descriptors:

Find:
```python
        # 100% - Complete (marks job as done)
        update_ai_job_progress(
            job_id, 100, complete=True,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            error=None
        )
```

Replace with:
```python
        # 100% - Complete (marks job as done)
        update_ai_job_progress(
            job_id, 100, complete=True,
            title=title,
            description=description,
            tags=clean_tags,
            categories=clean_categories,
            descriptors=clean_descriptors,
            error=None
        )
```

**6e.** Update the return dict at the end of the success path:

Find:
```python
        return {
            'status': 'success',
            'job_id': job_id,
            'title': title,
            'description': description,
            'tags': clean_tags,
            'categories': clean_categories
        }
```

Replace with:
```python
        return {
            'status': 'success',
            'job_id': job_id,
            'title': title,
            'description': description,
            'tags': clean_tags,
            'categories': clean_categories,
            'descriptors': clean_descriptors
        }
```

---

#### CHANGE 7: Add descriptors to ALL error/fallback cache writes in `generate_ai_content_cached()`

There are **4 error paths** in `generate_ai_content_cached()` that write to cache. Each one needs `descriptors={}` added.

**7a.** The `no_image_url` error (around line ~916):

Find:
```python
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[]
            )
            return {'status': 'error', 'error': 'no_image_url'}
```

Replace with:
```python
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
            return {'status': 'error', 'error': 'no_image_url'}
```

**7b.** The `domain_not_allowed` error (around line ~930):

Find:
```python
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[]
            )
            return {'status': 'error', 'error': 'domain_not_allowed'}
```

Replace with:
```python
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
            return {'status': 'error', 'error': 'domain_not_allowed'}
```

**7c.** The OpenAI error (around line ~960):

Find:
```python
                error=ai_result['error'],
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[]
            )
```

Replace with:
```python
                error=ai_result['error'],
                title='Untitled Prompt',
                description='',
                tags=[],
                categories=[],
                descriptors={}
            )
```

**7d.** The exception handler (around line ~1029):

Find:
```python
            error=str(e),
            title='Untitled Prompt',
            description='',
            tags=[],
            categories=[]
        )
```

Replace with:
```python
            error=str(e),
            title='Untitled Prompt',
            description='',
            tags=[],
            categories=[],
            descriptors={}
        )
```

---

#### CHANGE 8: Update `_update_prompt_with_ai_content()` to assign descriptors (lines ~590-654)

This is the direct-to-DB path used by the backfill command. Add descriptor assignment alongside the existing category assignment.

Find the categories block inside `_update_prompt_with_ai_content()`:

```python
        # Add categories (Phase 2 - Subject Categories)
        if categories:
            from prompts.models import SubjectCategory
            existing_cats = SubjectCategory.objects.filter(name__in=categories)
            prompt.categories.set(existing_cats)

            # Log if any categories were skipped
            skipped_cats = set(categories) - set(existing_cats.values_list('name', flat=True))
            if skipped_cats:
                logger.info(f"[AI Generation] Skipped non-existent categories for prompt {prompt.pk}: {skipped_cats}")
```

Add this block DIRECTLY AFTER the categories block (still inside the `transaction.atomic()` context):

```python
        # Add descriptors (Phase 2B - Subject Descriptors — Layer 4 validation)
        descriptors_dict = ai_result.get('descriptors', {})
        if descriptors_dict and isinstance(descriptors_dict, dict):
            from prompts.models import SubjectDescriptor
            # Flatten all descriptor names from all types
            all_descriptor_names = []
            for dtype_values in descriptors_dict.values():
                if isinstance(dtype_values, list):
                    all_descriptor_names.extend(
                        str(v).strip() for v in dtype_values if v
                    )
            if all_descriptor_names:
                # Layer 4: Only valid descriptors from DB are stored
                existing_descs = SubjectDescriptor.objects.filter(
                    name__in=all_descriptor_names
                )
                prompt.descriptors.set(existing_descs)

                # Log if any descriptors were skipped (hallucinated)
                skipped_descs = set(all_descriptor_names) - set(
                    existing_descs.values_list('name', flat=True)
                )
                if skipped_descs:
                    logger.info(
                        f"[AI Generation] Skipped non-existent descriptors "
                        f"for prompt {prompt.pk}: {skipped_descs}"
                    )
```

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents (Minimum 3)

**1. @django-expert**
- Task: Review M2M assignment patterns and transaction safety
- Focus: The descriptor assignment in `_update_prompt_with_ai_content` — confirm `.set()` is safe inside `transaction.atomic()`, verify no N+1 queries
- Rating requirement: 8+/10

**2. @code-review**
- Task: Review all 8 changes for correctness, edge cases, and consistency
- Focus: All error paths include `descriptors={}`, regex change handles edge cases, no missed locations
- Verify: Search for ALL instances of `categories=[]` or `categories=clean_categories` to confirm no missed descriptors additions
- Rating requirement: 8+/10

**3. @security**
- Task: Verify SSRF protection still intact, no injection vectors in new prompt
- Focus: The new prompt is a static string (no f-string interpolation of user input), URL validation untouched, cache key validation untouched
- Rating requirement: 8+/10

### Agent Reporting Format

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. @django-expert - [Rating]/10 - [Brief findings]
2. @code-review - [Rating]/10 - [Brief findings]
3. @security - [Rating]/10 - [Brief findings]
[Additional agents if used]

Critical Issues Found: [Number]
High Priority Issues: [Number]
Recommendations Implemented: [Number]

Overall Assessment: [APPROVED/NEEDS REVIEW]
```

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation

- [ ] Read current `prompts/tasks.py` completely
- [ ] Confirm `SubjectDescriptor` model exists: `from prompts.models import SubjectDescriptor; SubjectDescriptor.objects.count()`
- [ ] Confirm 109 descriptors and 46 categories present

### Post-Implementation — Code Verification

- [ ] `_build_analysis_prompt()` returns the new prompt text (no old category names)
- [ ] `max_tokens` is 1500
- [ ] `_parse_ai_response()` uses `find('{')`/`rfind('}')` pattern (not old `[^{}]*` regex)
- [ ] `_validate_ai_result()` validates descriptors as dict with list values
- [ ] Category limit is `[:5]` in the cache path
- [ ] **Search verification:** `grep -n "descriptors" prompts/tasks.py` should show descriptors referenced in:
  - `_validate_ai_result` (validation)
  - `generate_ai_content_cached` (extraction, cleaning, 90%, 100%, return, all 4 error paths)
  - `_update_prompt_with_ai_content` (DB assignment)
- [ ] **Search verification:** `grep -n "categories=\[\]" prompts/tasks.py` — every line that has `categories=[]` should also have `descriptors={}` on the next line or nearby
- [ ] No references to old category names remain: `grep -n "Animals & Wildlife\|Seasonal & Holiday\|Meme & Humor" prompts/tasks.py` should return ZERO results

### Post-Implementation — Functional (manual test after deploy)

- [ ] Upload a test image on the site
- [ ] Check Heroku logs for AI generation output
- [ ] Verify prompt gets categories assigned (admin check)
- [ ] Verify prompt gets descriptors assigned (admin check or Django shell)

### Regression Testing

- [ ] Homepage loads normally
- [ ] Existing prompts display correctly (no impact from tasks.py changes)
- [ ] NSFW moderation still works (untouched code)

---

## 📊 CC COMPLETION REPORT FORMAT

**After implementation, CC MUST provide a completion report in this EXACT format:**

```markdown
═══════════════════════════════════════════════════════════════════
PHASE 2B-2: AI PROMPT UPDATES — COMPLETION REPORT
═══════════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

[Agent report — ALL 3 AGENTS REQUIRED]

## 📁 FILES MODIFIED

| File | Changes | Lines Added/Modified |
|------|---------|---------------------|
| prompts/tasks.py | 8 changes as specified | +XX / -XX |

## 🔎 CHANGE VERIFICATION

| Change # | Description | Status |
|----------|-------------|--------|
| 1 | _build_analysis_prompt replaced | ✅/❌ |
| 2 | max_tokens → 1500 | ✅/❌ |
| 3 | _parse_ai_response regex updated | ✅/❌ |
| 4 | _validate_ai_result descriptors validation | ✅/❌ |
| 5 | Category limit 3→5 | ✅/❌ |
| 6 | Descriptors in cache writes (90%, 100%, return, extract, clean) | ✅/❌ |
| 7 | Descriptors in all 4 error paths | ✅/❌ |
| 8 | _update_prompt_with_ai_content descriptor assignment | ✅/❌ |

## 🧪 TESTING PERFORMED

| Test | Result |
|------|--------|
| No old category names in file | ✅/❌ |
| grep descriptors shows all locations | ✅/❌ |
| All categories=[] have descriptors={} | ✅/❌ |
| No syntax errors | ✅/❌ |

## ✅ SUCCESS CRITERIA MET

[Checklist]

## 📝 NOTES

[Any observations or edge cases]

═══════════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT STRATEGY

**DO NOT commit yet.** Report results to the developer first. When approved, use this commit message:

```
feat(categories): Phase 2B-2 — AI prompt update for three-tier taxonomy

- Replace OpenAI Vision prompt with new 46-category + 109-descriptor prompt
- Add SEO synonym rules for ethnicity, gender, niche terms, spelling variants
- Parse and validate new descriptors JSON object from AI response
- Store descriptors in cache at 90% and 100% progress alongside categories
- Assign descriptors to prompts via Layer 4 DB validation (anti-hallucination)
- Increase max_tokens 1000→1500 for larger response payload
- Increase category limit 3→5 per prompt
- Update JSON regex fallback to handle nested descriptor objects
- Add descriptors={} to all error/fallback cache writes

Reference: docs/DESIGN_CATEGORY_TAXONOMY_REVAMP.md Section 7.3
Phase: 2B-2 (AI Prompt Updates)
```

---

## ⚠️ DO / DO NOT LISTS

### DO ✅

- DO read `docs/CC_COMMUNICATION_PROTOCOL.md` first
- DO read the ENTIRE current `prompts/tasks.py` before making changes
- DO replace `_build_analysis_prompt()` completely — do not try to patch the old prompt
- DO keep the function signature of `_build_analysis_prompt()` identical (3 params)
- DO add `descriptors={}` to ALL error cache writes (there are 4 of them)
- DO keep `response_format={"type": "json_object"}` — it helps prevent hallucination
- DO verify with grep that no old category names remain in the file
- DO verify with grep that every `categories=[]` has a matching `descriptors={}` nearby

### DO NOT ❌

- DO NOT change `run_nsfw_moderation()` or any NSFW-related code
- DO NOT change `_is_safe_image_url()`, `_download_and_encode_image()`, or any security functions
- DO NOT change `update_ai_job_progress()` or `get_ai_job_status()` — these are generic and already accept `**kwargs`
- DO NOT change `rename_prompt_files_for_seo()` — unrelated
- DO NOT change `_sanitize_content()` or `_generate_unique_slug_with_retry()`
- DO NOT change `_handle_ai_failure()` (it doesn't set categories either, just adds generic tags)
- DO NOT use f-string interpolation of user input in the new prompt (the new prompt is a static string — this is intentional for security)
- DO NOT modify `upload_views.py` — that's Phase 2B-3
- DO NOT modify `related.py` — that's Phase 2B-4
- DO NOT commit without reporting results first

---

## ⛔ FINAL REMINDER ⛔

```
╔══════════════════════════════════════════════════════════════════╗
║  Work will be REJECTED if:                                      ║
║  • Fewer than 3 wshobson/agents used                            ║
║  • Any agent rates below 8/10                                   ║
║  • Agent report not included in completion summary              ║
║  • Old category names still in the file                         ║
║  • Any error path missing descriptors={}                        ║
║  • Completion report not in the specified format                 ║
╚══════════════════════════════════════════════════════════════════╝
```

**END OF SPECIFICATION**
