# CC_SPEC_139_D_NEW_FEATURES_DOCS.md
# Document Planned New Features in CLAUDE.md

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 139
**Type:** Docs — commits immediately per protocol v2.1
**Agents Required:** 1 (@docs-architect)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.1** — docs gate re-run rule applies
2. **Documentation changes only** — no code
3. **Per v2.1:** if agent scores below 8.0 → fix and re-run before committing

---

## 📋 OVERVIEW

Four new features have been scoped and discussed but not yet specced for
implementation. They must be documented in `CLAUDE.md` with full context —
benefits, pros, cons, risks, and architectural notes — so the information
is not lost between sessions.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find a good location in CLAUDE.md (after Deferred P3 Items, before end)
grep -n "Deferred P3\|On the horizon\|Future\|Planned" CLAUDE.md | head -10

# 2. Find current bulk generator section
grep -n "Bulk\|bulk.*gen\|BYOK\|GPT-Image" CLAUDE.md | head -10
```

---

## 📁 CHANGES REQUIRED

### `CLAUDE.md`

Add a new section **"🚀 Planned New Features"** after the Deferred P3 Items
table. Include the following four features:

---

#### Feature 1: Translate Prompts to English

**Summary:** Before generation starts, send all non-English prompts to GPT-4o
in a single batch call to translate them to English. Fires during the
"Starting generation…" phase — invisible to the user.

**Benefits:**
- OpenAI's image models perform significantly better with English prompts
- Users who copy prompts from non-English sources get better outputs without
  manual translation
- Zero user friction — happens automatically

**Implementation approach:**
- One GPT-4o call with all prompts batched
- System prompt: detect language of each prompt, translate to English if not
  already English, return array of cleaned prompts in same order
- Runs after validation, before `service.create_job()`
- Estimated latency: 1-3 seconds added to "Starting…" phase

**Pros:** High value, low cost (text is cheap), one API call, no UI changes

**Cons:** Adds latency to generation start, GPT-4o translation is not perfect
for highly technical or stylistic prompts

**Risks:** Translated prompt may lose nuance from the original language.
Mitigation: only translate if detected language is not English (skip if already
English)

**Priority:** High — relatively simple, high impact

---

#### Feature 2: Generate Prompt from Source Image (Vision API)

**Summary:** A per-prompt checkbox option ("Generate prompt from source image")
that, when ticked, uses GPT-4o Vision to generate a concise image-generation
prompt from the attached source image. The Vision-generated prompt replaces
the text field content and is used for both the generation and the result page
display.

**UX behaviour:**
- Checkbox appears below the source image URL field in each prompt box
- When ticked: text field disabled (strike-through on existing text), source
  image URL field becomes required
- When ticked + Character Description is filled: Character Description still
  applies and is NOT struck through
- Vision API call fires per ticked prompt during the "Starting…" phase
- Generated prompt appears in the results page alongside the generated image

**Vision API prompt strategy:**
- Instruct GPT-4o Vision to output exactly 1-2 sentences
- Cover: subject, style, composition, lighting, technical quality
- No narrative, no filler — generation-ready format
- Example output: "Hyperrealistic cinematic portrait of a woman in a red
  dress standing in a neon-lit alley at night, dramatic side lighting,
  shallow depth of field, 8K."

**Implementation approach:**
- New `generate_prompt_from_image(image_url)` helper in tasks.py using
  GPT-4o Vision API
- Called per image during job preparation, results stored on GeneratedImage
  as `vision_generated_prompt`
- Front-end: new checkbox per prompt box, JS disables/strikes text field

**Pros:** Major differentiator, solves "I have an image but no prompt" problem,
high accuracy with Vision API

**Cons:** One Vision API call per ticked prompt (costs ~$0.01 each), adds
latency per checked prompt, requires source image URL to be accessible

**Risks:** Vision API may not always produce concise output — requires careful
system prompt tuning. Source image must be HTTPS and accessible (already
validated by existing SSRF hardening)

**Priority:** High — genuine differentiator

---

#### Feature 3: Remove Watermark Text from Prompts

**Summary:** Before generation, automatically detect and strip "watermark
instructions" from prompts — text that instructs the AI to add a brand name
or logo to the generated image. This runs invisibly in the "Starting…" phase.

**Watermark text pattern:**
Typically appears as an instruction wrapped in quotes at the end of a prompt,
e.g.: `"Add The name 'IA Arte& Promts' in a clean, professional and elegant
font in the bottom left corner. The font should follow the color and picture theme."`

**Key distinction:** Watermark instructions tell the AI to *add text to the
image*. Legitimate scene text describes *text that already exists in the scene*
(signs, license plates, storefronts). GPT-4o is reliable at distinguishing these.

**Implementation approach:**
- Batch GPT-4o call alongside translation (or combined into one call)
- System prompt: for each prompt, identify and remove any instruction to add
  watermark/branding text. Do not remove descriptions of existing scene text.
  Return cleaned prompt.
- Can be combined with the translation feature into a single "prepare prompts"
  GPT-4o call to minimise API calls and latency

**Pros:** High value for users who copy prompts from watermarked sources,
zero user friction, one batch API call

**Cons:** GPT-4o may occasionally misidentify legitimate text as watermark
(low risk with careful prompt). Users may want to know their prompt was modified.

**Risks:** If combined with translation in one call, complexity of the
system prompt increases — test carefully

**Priority:** High — easy to implement, high value

---

#### Feature 4: Save Prompt Draft (Premium)

**Summary:** Allow users to save named prompt drafts server-side, persisting
prompt text, source image URLs, pasted images, and all micro-settings.
Currently drafts are saved to localStorage only and are lost on "Generate All".

**UX behaviour:**
- "Save Prompt Draft" button in the sticky bar (same style as Generate All)
- First click: modal prompts for draft name → user submits → button removed,
  replaced by auto-save indicator + draft name
- Subsequent edits auto-save every 500ms (same debounce as current localStorage)
- Draft can be loaded from a "My Drafts" page (future)

**Implementation approach:**
- New `PromptDraft` model: `user`, `name`, `prompts_json`, `settings_json`,
  `created_at`, `updated_at`
- Pasted images (B2 paste URLs) must be marked as "draft-pinned" so orphan
  cleanup does not delete them
- New API endpoints: `save_draft`, `load_draft`, `list_drafts`, `delete_draft`
- Front-end: replaces localStorage on save, loads from server on page load

**Pros:** High value for power users, premium tier justification, prevents
loss of complex prompt sets

**Cons:** Significant server storage implications (especially with paste images),
requires new model + migrations + API endpoints + UI — 2-3 sessions of work

**Risks:** Paste image pinning conflicts with orphan cleanup logic (must
coordinate). Premium feature requires subscription/tier gating.

**Priority:** Medium — valuable but complex. Build after features 1-3.

**Status:** Deferred — do not spec until other new features are stable.

---

#### Combined "Prepare Prompts" Architecture

Features 1, 2, and 3 all fire before generation starts. They should be
combined into a single "prepare prompts" step with one GPT-4o call (or two
calls max — one for text-only cleaning, one for Vision):

```
User clicks Generate →
1. Validate API key
2. Validate prompts (existing)
3. Prepare prompts (NEW single step):
   a. Strip watermark text from all prompts
   b. Translate non-English prompts to English
   c. For prompts with "generate from image" checked:
      → Vision API call per image → replace prompt text
4. Start generation job
```

The UI shows a single "Preparing prompts…" status rather than separate
spinners for each step.

---

### Add to `PROJECT_FILE_STRUCTURE.md`

No changes needed — these are planned features, not built ones.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] All 4 features documented in CLAUDE.md
- [ ] Each feature has: summary, benefits, implementation approach, pros, cons, risks, priority
- [ ] Combined architecture section included
- [ ] Save Prompt Draft marked as deferred
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 1 agent. Must score 8.0+.
Per v2.1: if below 8.0 → fix and re-run before committing.

### 1. @docs-architect
- Verify all 4 features are present with all required fields
- Verify combined architecture section is clear and accurate
- Verify risks are realistic and not exaggerated
- Rating requirement: 8+/10

---

## 🧪 TESTING

```bash
python manage.py check
```
Commits immediately after confirmed 8.0+ score.

---

## 💾 COMMIT MESSAGE

```
docs: planned new features — translate, vision prompt gen, watermark removal, save draft
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_139_D_NEW_FEATURES_DOCS.md`

---

**END OF SPEC**
