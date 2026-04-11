# CC_SPEC_152_B_PROGRESS_AND_VISION_COMPOSITION.md
# Progress Bar Permanent Fix + Vision Composition System Prompt

**Spec Version:** 1.0 (written after file review)
**Date:** April 2026
**Session:** 152
**Modifies UI/Templates:** No
**Migration Required:** No
**Agents Required:** 3 minimum
**Estimated Scope:** Small — `bulk_generator_views.py` only (2 changes)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — gate sequence applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **`bulk_generator_views.py` is ✅ Safe** — no line constraints
4. **This spec runs AFTER 152-A** — baseline state includes
   `status__in=['completed', 'generating']` from 152-A and
   `detail: 'high'` from 152-A

**Work will be REJECTED if:**
- Progress bar query still uses `filter(status__in=[...])`
   instead of `exclude(status='failed')`
- Vision system prompt still missing frame-position language
- Vision system prompt still missing depth/layering instruction
- Vision system prompt still missing background crowd instruction
- "RECREATE" instruction removed or weakened

---

## 📋 OVERVIEW

### Fix 1 — Progress bar: permanent fix via exclude

**Current state (post-152-A):**
```python
live_completed_count = job.images.filter(
    status__in=['completed', 'generating']
).count()
```

**Problem:** Still shows 0% when all images are `queued` — which is
their state immediately after job creation, before Django-Q picks them
up. Refreshing the page in the first few seconds shows 0%.

**Root cause confirmed via DevTools:**
`data-completed-count="0"` even on an active job. Images are still
`queued` at the moment of refresh.

**Permanent fix:** Use `exclude(status='failed')` — counts everything
that is part of the job and hasn't failed. This covers all states:
`queued`, `generating`, `completed`. Future-proof: any new status
added later (e.g. `retrying`) is automatically counted.

### Fix 2 — Vision system prompt: spatial accuracy improvements

**Current issues from production testing:**
- Woman appears on LEFT of frame, should be on RIGHT
- Man appears beside woman at equal depth, should be BEHIND her
- Background crowd of people not described or generated
- Decorative accessories (gold embroidery, teal gems, hair decorations)
  not captured
- Background described as blurred when source has sharp background

**Root cause:** The system prompt says "be spatially accurate" and
"if a person is on the left, say so" — but does not:
- Distinguish between LEFT/RIGHT **of the image frame** vs relative
  to other subjects
- Instruct the model to describe **depth layers** (foreground,
  midground, background)
- Instruct the model to describe ALL people visible including
  background crowd
- Explicitly warn against adding depth-of-field blur that isn't there

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Confirm current progress bar query (post-152-A baseline)
grep -n "live_completed_count\|status__in\|exclude.*failed" \
    prompts/views/bulk_generator_views.py | head -5

# 2. Read full current Vision system prompt
sed -n '747,786p' prompts/views/bulk_generator_views.py

# 3. Confirm detail:high is in place (post-152-A)
grep -n "'detail'" prompts/views/bulk_generator_views.py | head -3

# 4. Confirm direction_block is always empty (post-152-A)
grep -n "direction_block" prompts/views/bulk_generator_views.py | head -5
```

**Do not proceed until all greps are complete.**
**Read the full system prompt output from grep 2 before replacing.**

---

## 📁 STEP 1 — Progress bar permanent fix

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 1, find the `live_completed_count` line (~line 98):

**CURRENT (post-152-A):**
```python
    live_completed_count = job.images.filter(
        status__in=['completed', 'generating']
    ).count()
```

**REPLACE WITH:**
```python
    # Exclude only failed images — counts queued + generating + completed.
    # This ensures the progress bar shows >0% immediately on page refresh
    # even when images are still queued (job just started).
    # Future-proof: any new status added later is automatically counted.
    live_completed_count = job.images.exclude(status='failed').count()
```

---

## 📁 STEP 2 — Replace Vision system prompt with improved version

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep 2, find and completely replace the `system_prompt`
construction inside `_generate_prompt_from_image()`.

**REPLACE the entire `system_prompt = (...)` block WITH:**

```python
        system_prompt = (
            'You are an expert AI image prompt writer. Your goal is to RECREATE '
            'the attached image as accurately as possible — not to reinterpret, '
            'enhance, or improve it. Describe only what you actually see.\n\n'

            'Before writing, carefully analyse these elements:\n'
            '- Genre and art style (photorealistic, digital painting, '
            'illustration, etc.)\n'
            '- Composition: describe positions using image-frame coordinates. '
            'State whether subjects appear on the LEFT side, RIGHT side, or '
            'CENTRE of the image frame. This is critical — left/right must '
            'be from the viewer\'s perspective, not the subjects\'.\n'
            '- Depth and layering: explicitly describe who or what is in the '
            'FOREGROUND (closest to viewer), MIDGROUND, and BACKGROUND. If one '
            'person is behind another, state this clearly.\n'
            '- Camera angle and perspective\n'
            '- Lighting: direction, colour temperature, quality (soft/hard). '
            'State whether it is a warm sunset glow, cold overcast, etc.\n'
            '- Main subjects: for every person visible, describe their exact '
            'age range, ethnicity, hair style and colour, clothing details, '
            'accessories, jewellery, decorations, pose, and expression.\n'
            '- ALL people in the scene: do not skip background figures. '
            'If there are people in the background, describe them — how many, '
            'what they appear to be doing, their approximate position.\n'
            '- Background and environment: describe what is actually visible '
            'with precise detail. State explicitly whether the background is '
            'IN SHARP FOCUS or BLURRED. Do not add blur that is not in the '
            'image. Do not remove detail that is there.\n'
            '- Decorative details: describe ALL visible accessories, patterns, '
            'embroidery, jewellery, and ornamental details on clothing and in '
            'the scene. These are often what makes an image distinctive.\n'
            '- Colour palette and materials\n'
            '- Mood and atmosphere\n\n'

            'Then write a single, continuous, high-quality prompt that covers '
            'all of the above with precision. The prompt must be thorough '
            'enough to reproduce the image faithfully — do not cut corners. '
            'This is a premium feature and the prompt quality must reflect '
            'that.\n\n'

            'Rules:\n'
            '- RECREATE, do not reinterpret. Describe what is there.\n'
            '- Frame position is absolute: LEFT, RIGHT, CENTRE refers to the '
            'image frame from the viewer\'s perspective — never relative to '
            'another subject.\n'
            '- Describe depth explicitly: who is in front of whom. '
            '"The man stands slightly behind and to the right of the woman" '
            'is correct. "The man and woman stand together" loses depth.\n'
            '- If the background is sharp and detailed, say so explicitly. '
            'NEVER add depth-of-field blur or bokeh unless it is clearly '
            'present in the source image.\n'
            '- Describe ALL people visible in the scene — including background '
            'crowd, bystanders, and distant figures.\n'
            '- Describe clothing, accessories, and decorative details '
            'specifically. "White flowing dress with intricate gold and teal '
            'embroidery at the neckline" not "white dress".\n'
            '- Describe hair decorations, jewellery, and accessories on every '
            'person — do not omit them.\n'
            '- Do not invent details that are not visible in the image.\n'
            '- Do not add suggestions, improvements, or creative additions.\n'
            '- Write in English only.\n'
            + ignore_watermark_rule
            + no_watermark_output_rule +
            '- Output ONLY the prompt text — no labels, no sections, '
            'no preamble, no explanations.'
        )
```

---

## 📁 STEP 3 — MANDATORY VERIFICATION

```bash
# 1. Confirm exclude(status='failed') in place
grep -n "exclude.*failed\|live_completed_count" \
    prompts/views/bulk_generator_views.py | head -5

# 2. Confirm new system prompt key phrases
grep -n "image frame\|FOREGROUND\|MIDGROUND\|BACKGROUND\|ALL people\|depth.*blur\|bokeh" \
    prompts/views/bulk_generator_views.py | head -10

# 3. Confirm RECREATE still present
grep -n "RECREATE" prompts/views/bulk_generator_views.py | head -3

# 4. Confirm watermark rules still conditional
grep -n "ignore_watermark_rule\|no_watermark_output_rule" \
    prompts/views/bulk_generator_views.py | head -5

# 5. Confirm detail:high still in place (not accidentally reverted)
grep -n "'detail'" prompts/views/bulk_generator_views.py | head -3
```

**Show all outputs in Section 3.**

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] `exclude(status='failed')` replaces `filter(status__in=[...])`
- [ ] System prompt completely replaced (not appended to)
- [ ] Frame-position instruction uses LEFT/RIGHT/CENTRE from
      viewer's perspective
- [ ] Depth/layering instruction: FOREGROUND/MIDGROUND/BACKGROUND
- [ ] All background people instruction present
- [ ] Explicit "no bokeh unless present" instruction present
- [ ] Decorative details (accessories, embroidery, jewellery) instruction
- [ ] "RECREATE" instruction still present and prominent
- [ ] `ignore_watermark_rule` and `no_watermark_output_rule` still
      correctly placed and conditional
- [ ] `detail: 'high'` not accidentally reverted
- [ ] Step 3 verification greps pass
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @django-pro
- Verify `exclude(status='failed')` is the correct ORM expression
- Verify it correctly counts queued + generating + completed
- Verify placement relative to `live_progress_percent` calculation
  (exclude count feeds into percent calculation — must come first)
- Show Step 3 grep 1
- Rating requirement: 8+/10

### 2. @python-pro
- Verify system prompt completely replaced (no stale sentences)
- Verify watermark rules still conditional and correctly placed
- Verify string concatenation syntax is correct (no missing `+`)
- Show Step 3 greps 2, 3, 4
- Rating requirement: 8+/10

### 3. @code-reviewer
- Verify `detail: 'high'` not accidentally reverted
- Verify new prompt accurately addresses all five identified failures:
  frame position, depth, background crowd, decorative details,
  background sharpness
- Show Step 3 grep 5
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- `filter(status__in=[...])` still present (not replaced with exclude)
- "RECREATE" instruction removed or weakened
- Frame-position instruction missing (LEFT/RIGHT from viewer perspective)
- Depth layering instruction missing
- Background crowd instruction missing
- `detail: 'high'` accidentally reverted to `detail: 'low'`
- Step 3 greps not shown

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=1 2>&1 | tail -5
```

**Manual browser checks (Mateo):**

1. **Progress bar** — Start generation → refresh page IMMEDIATELY
   (before any images finish) → bar should show >0% right away
   (all images are queued = counted)

2. **Vision frame position** — Paste family painting → Vision="Yes",
   no direction → Generate → verify:
   - Woman appears on the RIGHT side of the frame ✅
   - Man is BEHIND the woman (not beside) ✅
   - Background people/crowd visible ✅
   - Background is sharp (not blurred) ✅
   - Child's hair decorations described ✅

---

## 💾 COMMIT MESSAGE

```
fix(bulk-gen): progress bar exclude-failed query, Vision composition accuracy
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_152_B_PROGRESS_AND_VISION_COMPOSITION.md`

**Section 3 MUST include all Step 3 verification grep outputs.**

---

**END OF SPEC**
