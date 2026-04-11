# CC_SPEC_152_A_VISION_QUALITY_AND_PROGRESS.md
# Vision Quality + Two-Step Direction + Progress Bar Fix

**Spec Version:** 1.0 (written after file review)
**Date:** April 2026
**Session:** 152
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** Small — `bulk_generator_views.py` only (4 targeted changes)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk_generator_views.py` is ✅ Safe** — no line constraints

**Work will be REJECTED if:**
- `detail` is still `'low'` after this spec
- Direction text is still passed INTO the Vision image analysis call
- Progress bar still shows 0% when images are in `generating` state
- Vision direction is silently dropped after this change
  (it must be routed to the text edit step instead)

---

## 📋 OVERVIEW

### Fix 1 — Progress bar shows 0% during active generation

**Root cause confirmed via browser DevTools:**
`data-completed-count="0"` even when images are actively generating.
The query `job.images.filter(status='completed').count()` only counts
`status='completed'`. Images in `status='generating'` are not counted.
Mid-generation the count is always 0 — the bar snaps to 0% on refresh.

**Fix:** Count both `'completed'` and `'generating'` as having started.

### Fix 2 — Vision uses `detail: 'low'` → upgrade to `detail: 'high'`

At `detail: 'low'`, OpenAI internally resizes the source image to ~85×85
pixels before Vision analysis. At this resolution the model cannot
reliably determine spatial positions (who is left/right/front/back),
background people, or fine clothing details. This is why composition
was wrong even with a well-written system prompt.

`detail: 'high'` uses the full image resolution for analysis. Cost per
Vision call goes from ~$0.003 to ~$0.009 — less than a cent. For a
premium paid feature where accuracy is the selling point, this is
the correct trade-off.

### Fix 3 — Decouple direction from Vision analysis (two-step approach)

**Current (broken) approach:**
Direction text is passed into `_generate_prompt_from_image()` as
`direction_block` appended to the user message. The Vision model then
tries to simultaneously describe the image AND apply creative direction.
This causes it to reinterpret rather than describe — changing ethnicity,
composition, clothing, and subject positions.

**New two-step approach:**
1. **Step 1 (Vision):** Pure description — no direction. The Vision model
   describes ONLY what it sees, faithfully and accurately.
2. **Step 1.5 (Text edit):** Apply direction as a targeted edit to the
   Vision-generated description. Same GPT-4o-mini text edit pipeline
   already used for text prompt boxes.

This cleanly separates "describe what is there" from "now modify it".
The direction edit reuses existing `Step 1.5` infrastructure — no new
code paths needed, just routing.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm progress bar query
grep -n "live_completed_count\|filter.*status.*completed" \
    prompts/views/bulk_generator_views.py | head -5

# 2. Confirm detail:low location
grep -n "'detail'" prompts/views/bulk_generator_views.py | head -3

# 3. Confirm direction_block is passed into user message
grep -n "direction_block\|direction.*strip\|Incorporate" \
    prompts/views/bulk_generator_views.py | head -10

# 4. Confirm Step 1.5 skips Vision boxes (the guard to remove)
grep -n "vision_enabled\[i\]\|if.*vision.*continue\|Only apply.*non-Vision" \
    prompts/views/bulk_generator_views.py | head -5

# 5. Confirm direction is passed to _generate_prompt_from_image
grep -n "_generate_prompt_from_image\|vision_directions\[i\]" \
    prompts/views/bulk_generator_views.py | head -10
```

**Do not proceed until all greps are complete.**
**Read Steps 1–5 in this spec carefully before making any changes.**

---

## 📁 STEP 1 — Fix progress bar: count generating + completed

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 1, find line ~98:

**CURRENT:**
```python
    live_completed_count = job.images.filter(status='completed').count()
```

**REPLACE WITH:**
```python
    # Count both completed and actively generating images so the progress
    # bar reflects real work in progress on page refresh — not just finished
    # images. 'generating' images have started and will complete shortly.
    live_completed_count = job.images.filter(
        status__in=['completed', 'generating']
    ).count()
```

---

## 📁 STEP 2 — Upgrade Vision detail from low to high

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 2, find the `detail` key inside `_generate_prompt_from_image`
(line ~792):

**CURRENT:**
```python
                    'detail': 'low',  # Low detail = cheaper + faster for prompt generation
```

**REPLACE WITH:**
```python
                    'detail': 'high',  # High detail preserves spatial accuracy for faithful recreation
```

---

## 📁 STEP 3 — Remove direction from Vision analysis call

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 3, find `direction_block` inside `_generate_prompt_from_image`.

The function signature currently accepts `direction: str`. We keep the
parameter to avoid breaking the call site, but stop using it in the
Vision analysis. Remove the `direction_block` construction and its
usage in the user message:

**CURRENT:**
```python
        direction_block = ''
        if direction and direction.strip():
            direction_block = (
                f'\n\nUser direction: "{direction.strip()}"\n'
                f'Incorporate these instructions into the prompt.'
            )
```

**REPLACE WITH:**
```python
        # Direction is intentionally NOT passed to Vision analysis.
        # Vision's job is to purely describe what it sees — accurate
        # and faithful. Direction is applied as a separate edit step
        # after Vision generates its base description (see Step 1.5
        # in api_prepare_prompts). Keeping the parameter for backwards
        # compatibility but not using it here.
        direction_block = ''
```

Also update the user message to remove `direction_block` since it is
now always empty. Find:

**CURRENT:**
```python
                    'Analyse this image carefully and write a high-quality, '
                    'accurate prompt that would recreate it faithfully.'
                    + direction_block
```

**REPLACE WITH:**
```python
                    'Analyse this image carefully and write a high-quality, '
                    'accurate prompt that would recreate it faithfully.'
```

---

## 📁 STEP 4 — Route Vision direction to Step 1.5 text edit

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 greps 4 and 5, find two locations in `api_prepare_prompts`:

**Change A — Pass empty direction to Vision call (Step 1 loop):**

In the Vision loop (Step 0 grep 5), find where direction is extracted
and passed to `_generate_prompt_from_image`:

**CURRENT:**
```python
        direction = vision_directions[i] if i < len(vision_directions) else ''
        generated = _generate_prompt_from_image(
            src_url, direction, platform_api_key,
            remove_watermarks=remove_watermarks,
        )
```

**REPLACE WITH:**
```python
        # Direction is NOT passed to Vision — pure description only.
        # The direction will be applied as a text edit in Step 1.5.
        generated = _generate_prompt_from_image(
            src_url, '', platform_api_key,
            remove_watermarks=remove_watermarks,
        )
```

**Change B — Remove Vision exclusion from Step 1.5 text edit loop:**

From Step 0 grep 4, find the guard in Step 1.5 that skips Vision boxes:

**CURRENT:**
```python
        # Only apply to non-Vision prompts (Vision directions handled separately)
        if vision_enabled[i]:
            continue
```

**REPLACE WITH:**
```python
        # Apply to both Vision and non-Vision prompts.
        # For Vision boxes: direction is applied to the Vision-generated
        # description as a targeted edit (two-step approach).
        # For text boxes: direction edits the written prompt as before.
```

Also update the direction source for Vision boxes. Currently Step 1.5
reads from `text_directions`. Vision directions live in `vision_directions`.
We need Step 1.5 to use whichever is relevant per box:

After the existing `text_directions` extraction, add:

```python
    # Merge vision_directions into the direction source for Step 1.5.
    # For Vision boxes, use vision_directions; for text boxes, use text_directions.
    # This routes all direction instructions through the same edit pipeline.
    combined_directions = []
    for i in range(len(prompts)):
        is_vis = vision_enabled[i] if i < len(vision_enabled) else False
        if is_vis:
            combined_directions.append(
                vision_directions[i] if i < len(vision_directions) else ''
            )
        else:
            combined_directions.append(
                text_directions[i] if i < len(text_directions) else ''
            )
```

Then update the Step 1.5 loop to iterate `combined_directions` instead
of `text_directions`:

**CURRENT:**
```python
    for i, direction in enumerate(text_directions):
```

**REPLACE WITH:**
```python
    for i, direction in enumerate(combined_directions):
```

---

## 📁 STEP 5 — MANDATORY VERIFICATION

```bash
# 1. Confirm progress bar counts generating + completed
grep -n "status__in.*completed.*generating\|generating.*completed" \
    prompts/views/bulk_generator_views.py | head -3

# 2. Confirm detail is now high
grep -n "'detail'" prompts/views/bulk_generator_views.py | head -3

# 3. Confirm direction_block is always empty in _generate_prompt_from_image
grep -n "direction_block\|Incorporate" \
    prompts/views/bulk_generator_views.py | head -5

# 4. Confirm Vision call passes empty string for direction
grep -n "_generate_prompt_from_image" \
    prompts/views/bulk_generator_views.py | head -5

# 5. Confirm Vision exclusion removed from Step 1.5
grep -n "Only apply.*non-Vision\|vision_enabled\[i\].*continue" \
    prompts/views/bulk_generator_views.py | head -5

# 6. Confirm combined_directions used in Step 1.5 loop
grep -n "combined_directions\|for.*combined" \
    prompts/views/bulk_generator_views.py | head -5
```

**Show all outputs in Section 3.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `live_completed_count` counts `generating` AND `completed`
- [ ] `detail` is `'high'` not `'low'`
- [ ] `direction_block` is always `''` in `_generate_prompt_from_image`
- [ ] `direction_block` is NOT appended to user message
- [ ] Vision call passes empty string `''` as direction
- [ ] Step 1.5 no longer skips Vision boxes
- [ ] `combined_directions` merges `vision_directions` and `text_directions`
- [ ] Step 1.5 loop iterates `combined_directions`
- [ ] Vision direction still works — just applied after not during analysis
- [ ] Step 5 verification greps pass
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @django-pro
- Verify `combined_directions` logic correctly routes per box type
- Verify Step 1.5 loop change doesn't break existing text box direction
- Verify progress bar query counts both states correctly
- Show Step 5 greps 1, 5, 6
- Rating requirement: 8+/10

### 2. @python-pro
- Verify `_generate_prompt_from_image` no longer uses direction
- Verify `direction_block` is always empty — not conditional
- Verify Vision call passes `''` not the direction variable
- Show Step 5 greps 3, 4
- Rating requirement: 8+/10

### 3. @code-reviewer
- Verify no direction is silently dropped — all directions now flow
  through `combined_directions` to Step 1.5
- Verify `detail: 'high'` change is correct and comment updated
- Show Step 5 greps 2, 6
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `detail` still `'low'`
- `direction_block` still conditionally built from direction parameter
- Vision boxes still skipped in Step 1.5
- `combined_directions` missing — directions silently dropped
- Progress bar still only counts `completed` not `generating`
- Step 5 greps not shown

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=1 2>&1 | tail -5
```

**Manual browser checks (Mateo):**

1. **Progress bar** — Start generation → let 1 image begin generating
   (not complete) → refresh page → bar should show >0% immediately

2. **Vision quality (no direction)** — Paste family painting → Vision="Yes",
   no direction → Generate → verify:
   - Man is BEHIND the woman (not opposite side)
   - Background people are present (not removed)
   - Background is sharp (not blurred)
   - Child ethnicity matches source

3. **Vision + direction (two-step)** — Same source image → Vision="Yes" →
   Add Direction: "Futuristic. Inspired by Tomorrowland." → Generate →
   verify direction was applied to the accurate base description without
   corrupting ethnicity, composition, or positions

4. **Text box direction (regression)** — Write a text prompt → tick
   "Add AI Direction" → add direction → Generate → confirm direction
   still applies correctly to text prompts (no regression)

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): Vision detail high, two-step direction, progress bar generating state
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_152_A_VISION_QUALITY_AND_PROGRESS.md`

**Section 3 MUST include all Step 5 verification grep outputs.**

---

**END OF SPEC**
