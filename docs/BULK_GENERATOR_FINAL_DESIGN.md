# BULK AI IMAGE GENERATOR — Final Design Specification

**Document Purpose:** Finalized UX/UI design for the bulk generator feature
**Created:** February 27, 2026 (Session 92)
**Status:** APPROVED — Ready for CC spec writing
**Source:** Interactive design session between Mateo and Claude
**References:** `BULK_AI_GENERATOR_BLUEPRINT.md`, `docs/BULK_IMAGE_GENERATOR_PLAN.md` (v1.4)

---

## SCOPE: v1.0 (Admin-Only)

### What's IN v1.0

- Bulk image generation tool at `/staff/bulk-generator/`
- Two input modes: Batch Paste (delimiter) + Custom Boxes
- Master settings with optional per-box overrides
- Reference image upload with face/person validation (OpenAI Vision)
- Character description prefix (prepended to all prompts)
- Configurable 1-4 images per prompt
- Gallery review with prompt grouping and selection
- Page creation pipeline (skip NSFW for OpenAI, keep AI titles/descriptions/tags)
- Provider abstraction layer (OpenAI now, Replicate later)
- Public/Private visibility mode
- Profanity/content validation adapted for bulk
- Responsive layout (sidebar → stacked on mobile)

### What's DEFERRED to v1.1+

- Upload gallery (reuse previously uploaded images)
- Premium/free user gating (diamond icons, subscription checks)
- BYOK (Bring Your Own Key) integration
- Presets system
- Single-prompt generator page (separate feature)
- Replicate/Grok provider integrations
- Image-to-image variations (beyond reference image)

---

## STRUCTURAL DECISIONS

| Decision | Choice | Rationale |
|----------|--------|-----------|
| URL | `/staff/bulk-generator/` | Consistent with `/staff/system-notifications/`; full design control |
| State management | Single page, JS state transitions | Smoother UX, no page reloads between states |
| Layout | Sidebar controls + center content area | Industry standard (all 8 reference platforms use this) |
| Input modes | Batch Paste + Custom Boxes | Speed for bulk, control for per-prompt tuning |
| Settings model | Master defaults + per-box overrides | Fast for bulk, flexible when needed |
| Action area | Sticky sidebar (desktop), sticky bottom (mobile) | Generate button always accessible |
| Images per prompt | Configurable 1-4 in master settings | Trial and error to find sweet spot |
| NSFW pipeline | Skip for OpenAI (built-in), run for lenient providers | Saves ~2-5 sec/image; provider flag controls this |
| Face validation | OpenAI Vision API | Already integrated, handles edge cases well |
| Gallery grouping | Images grouped by prompt with expandable prompt text | Users know which images belong to which prompt |
| Selection behavior | Whole-card click target (not tiny checkbox) | Faster selection workflow |
| Unselected images | Permanently deleted (trashed) | No orphaned images |
| Selected images | Published through pipeline as normal | Draft mode, review in admin |

---

## PAGE LAYOUT

### Overall Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│  Staff > Bulk Image Generator                                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──── MAIN CONTENT AREA (~70%) ────────┐  ┌─ STICKY SIDEBAR (~30%) │
│  │                                      │  │                        │
│  │  [Content changes per state]         │  │  [Master Settings]     │
│  │                                      │  │  [Summary]             │
│  │                                      │  │  [Action Button]       │
│  │                                      │  │                        │
│  └──────────────────────────────────────┘  └────────────────────────┘
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Responsive Behavior

| Breakpoint | Layout |
|-----------|--------|
| Desktop (>1024px) | Side-by-side: main content + sticky sidebar |
| Tablet (768-1024px) | Master settings at top, content below, sticky bottom bar for generate |
| Mobile (<768px) | Full stack: master settings → content → sticky bottom generate bar |

---

## STICKY SIDEBAR — Master Settings (All States)

```
┌─ STICKY SIDEBAR ─────────────────────────┐
│                                           │
│  Master Settings                          │
│  ─────────────────────                    │
│                                           │
│  AI Model                                 │
│  [GPT-Image-1            ▼]              │
│                                           │
│  Reference Image (optional)               │
│  ┌──────────────────────────────────┐     │
│  │  [Drag & drop or click to upload]│     │
│  └──────────────────────────────────┘     │
│  ⓘ Must be a clear photo of a person     │
│                                           │
│  — OR after successful upload: —          │
│                                           │
│  ┌──────────┐                             │
│  │  [photo] │  ✅ Face detected           │
│  └──────────┘  [✕ Remove]                │
│                                           │
│  Character Description (optional)         │
│  ┌──────────────────────────────────┐     │
│  │ A chubby woman with green eyes   │     │
│  │ and curly blond hair, mid-30s,   │     │
│  │ warm smile                       │     │
│  └──────────────────────────────────┘     │
│  ⓘ Prepended to every prompt             │
│                                           │
│  Quality                                  │
│  [Medium                  ▼]             │
│                                           │
│  Dimensions                               │
│  [□] [▪] [▬] [▯]                        │
│  1:1  3:4  16:9  4:3                      │
│                                           │
│  Images per Prompt                        │
│  [1] [2] [3] [4]                         │
│                                           │
│  Visibility                               │
│  [◉ Public] [○ Private]                  │
│                                           │
│  Generator Category                       │
│  [ChatGPT             ▼]                 │
│  (applied as tag on created pages)        │
│                                           │
│  ─────────────────────                    │
│                                           │
│  📊 18 prompts × 4 images = 72 images    │
│  ⏱️  ~14 min (at 5 img/min)              │
│  💰 ~$2.16 (72 × $0.03)                  │
│                                           │
│  [ ✨ Generate All ]                      │
│  ─────────────────                        │
│  ⚠️ Generated by AI. Use responsibly.     │
│                                           │
└───────────────────────────────────────────┘
```

### Master Settings Fields

| Setting | Type | Default | Per-Box Override? |
|---------|------|---------|-------------------|
| AI Model | Dropdown | GPT-Image-1 | No (v1.0) |
| Reference Image | Upload + validation | None | Yes |
| Character Description | Textarea (optional) | Empty | No (master only) |
| Quality | Dropdown (Low/Medium/High) | Medium | Yes |
| Dimensions | Visual button group | 1:1 | Yes |
| Images per Prompt | Button group (1-4) | 1 | Yes |
| Visibility | Radio (Public/Private) | Public | No (master only) |
| Generator Category | Dropdown | ChatGPT | No (master only) |

---

## STATE 1: INPUT

### Mode Tabs

```
┌─ MODE TABS ────────────────────────────────────────┐
│  [📋 Batch Paste]  [🎛️ Custom Boxes]              │
└────────────────────────────────────────────────────┘
```

### Batch Paste Mode (Active by Default)

For rapidly entering multiple multi-line prompts. Uses `---` delimiter.

```
┌─ BATCH PASTE MODE ─────────────────────────────────────────────┐
│                                                                 │
│  Paste prompts separated by --- on its own line:               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Cinematic Holi scene of the same couple from the          │ │
│  │ reference image, standing close together during a         │ │
│  │ dramatic explosion of bright pink, blue and orange        │ │
│  │ powder. Strong backlight outlining their silhouettes.     │ │
│  │ ---                                                       │ │
│  │ A photo of a Thai woman cooking at a vibrant Bangkok      │ │
│  │ street food cart at night. She stands confidently behind  │ │
│  │ a weathered steel cart, mid-motion as she tosses          │ │
│  │ ingredients into a sizzling wok.                          │ │
│  │ ---                                                       │ │
│  │ Minimalist coffee shop logo, clean vector lines,          │ │
│  │ morning light aesthetic                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ✅ 3 prompts detected                                         │
│                                                                 │
│  ┌─ Preview ───────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │  Prompt 1: "Cinematic Holi scene of the same coup..."  │   │
│  │  Prompt 2: "A photo of a Thai woman cooking at a ..."   │   │
│  │  Prompt 3: "Minimalist coffee shop logo, clean ve..."   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [ Convert to Custom Boxes → ]                                 │
│  ⓘ Convert to edit individual prompts or customize settings    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key behaviors:**
- Live prompt count updates as user types/pastes
- Preview shows truncated first line of each detected prompt
- "Convert to Custom Boxes" transforms all detected prompts into individual boxes
- Prompts inherit ALL master settings (no per-prompt overrides in this mode)
- Delimiter: `---` on its own line (three hyphens, nothing else on that line)

### Custom Boxes Mode

For per-prompt control. Boxes can be populated from Batch Paste conversion or created manually.

```
┌─ CUSTOM BOXES MODE ────────────────────────────────────────────┐
│                                                                 │
│  ┌─ Box 1 ──────────────────────────────────────────────────┐  │
│  │  Prompt:                                                  │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ Cinematic Holi scene of the same couple from the │     │  │
│  │  │ reference image, standing close together during  │     │  │
│  │  │ a dramatic explosion of bright pink, blue and    │     │  │
│  │  │ orange powder.                                   │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  │  Combined preview:                                        │  │
│  │  "A chubby woman with green eyes and curly blond hair,   │  │
│  │   mid-30s, warm smile. Cinematic Holi scene of the same  │  │
│  │   couple from the reference image, standing close..."     │  │
│  │                                                           │  │
│  │  Using master settings  [✏️ Customize]             [🗑️]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Box 2 ──────────────────────────────────────────────────┐  │
│  │  Prompt:                                                  │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ A photo of a Thai woman cooking at a vibrant     │     │  │
│  │  │ Bangkok street food cart at night.                │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  │  Combined preview:                                        │  │
│  │  "A chubby woman with green eyes and curly blond hair,   │  │
│  │   mid-30s, warm smile. A photo of a Thai woman cook..."   │  │
│  │                                                           │  │
│  │  Using master settings  [✏️ Customize]             [🗑️]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Box 3 (customized) ──── ⚙️ ────────────────────────────┐  │
│  │  Prompt:                                                  │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ Minimalist coffee shop logo, clean vector lines  │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  │                                                           │  │
│  │  Combined preview:                                        │  │
│  │  "A chubby woman with green eyes and curly blond hair,   │  │
│  │   mid-30s, warm smile. Minimalist coffee shop logo..."    │  │
│  │                                                           │  │
│  │  Quality: [Low ▼]  Dims: [▪ 3:4]  Imgs: [1]             │  │
│  │                                                           │  │
│  │  Overrides master  [↩️ Reset to master]            [🗑️]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Box 4 (validation error) ──── ❌ ───────────────────────┐  │
│  │  Prompt:                                          RED     │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │ [problematic prompt text]                        │     │  │
│  │  └──────────────────────────────────────────────────┘     │  │
│  │  ⚠️ Content flagged — please revise this prompt           │  │
│  │                                                           │  │
│  │  Using master settings  [✏️ Customize]             [🗑️]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│              [ + Add 4 More Boxes ]                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Custom Box behaviors:**
- Initially loads 4-8 empty boxes
- "Add 4 More Boxes" button adds more (no upper limit, but practical max ~50)
- Each box shows its reference number (Box 1, Box 2, etc.)
- "Customize" toggle expands per-box settings (quality, dimensions, images per prompt)
- "Reset to master" collapses overrides back to master settings
- Delete button (🗑️) removes the box with confirmation if prompt has content
- Combined preview shows character description prefix + individual prompt (truncated)
- Combined preview only shows when character description is set in master
- Validation errors: red border, red ❌ icon, error message, blocks generation until fixed
- Tab from one prompt textarea creates/focuses the next box for fast entry

### Validation (Runs on "Generate All" Click)

| Check | Scope | Error Display |
|-------|-------|---------------|
| Empty prompts | Per box | "Box 3: Prompt cannot be empty" |
| Profanity/content policy | Per box | Red border + "Box 2: Content flagged — please revise" |
| Duplicate prompts | Across all boxes | "Box 5 is identical to Box 2" |
| Minimum prompts | Global | "At least 1 prompt required" |
| Reference image (if uploaded) | Global | Face/person validation errors |

Validation uses existing prompt validation adapted for bulk. Errors are displayed both inline (on the specific box) and as a summary banner at the top.

---

## STATE 2: GENERATING

Triggered after validation passes and user confirms generation.

```
┌─ MAIN CONTENT AREA ──────────────────────────────────────────────┐
│                                                                   │
│  ⏳ Generating Images                                            │
│                                                                   │
│  ████████████████████░░░░░░░░░░░░░░░░░  7/18 prompts (39%)      │
│  Rate: 5 images/min · ~2 min 15 sec remaining                    │
│                                                                   │
│  ┌─ Prompt #1 ───────────────────────────────────────────────┐   │
│  │  "Cinematic Holi scene of the same coup..."  [▼ Expand]   │   │
│  │                                                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │   │
│  │  │ ☑  ✓  │ │ ☑  ✓  │ │ ☑  ✓  │ │ ☑  ✓  │            │   │
│  │  │ [img]  │ │ [img]  │ │ [img]  │ │ [img]  │            │   │
│  │  │  1/4   │ │  2/4   │ │  3/4   │ │  4/4   │            │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘            │   │
│  │                                       4 of 4 selected     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─ Prompt #2 ───────────────────────────────────────────────┐   │
│  │  "A photo of a Thai woman cooking at..."  [▼ Expand]      │   │
│  │                                                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │   │
│  │  │ ☑  ✓  │ │ ☑  ✓  │ │ ⏳     │ │  ···   │            │   │
│  │  │ [img]  │ │ [img]  │ │ [spin] │ │        │            │   │
│  │  │  1/4   │ │  2/4   │ │  3/4   │ │  4/4   │            │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘            │   │
│  │                                       2 of 2 selected     │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─ Prompt #3 ───────────────────────────────────────────────┐   │
│  │  "Minimalist coffee shop logo, clean ve..."  [▼ Expand]   │   │
│  │                                                           │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │   │
│  │  │  ···   │ │  ···   │ │  ···   │ │  ···   │            │   │
│  │  │        │ │        │ │        │ │        │            │   │
│  │  │  1/4   │ │  2/4   │ │  3/4   │ │  4/4   │            │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘            │   │
│  │                                       Queued...           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ⓘ Images appear as they complete. Click images to deselect.     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Sidebar during generation:**

```
┌─ STICKY SIDEBAR ─────────────┐
│                               │
│  Progress                     │
│  ─────────────                │
│                               │
│  ✅ 7 completed               │
│  ⏳ 1 processing              │
│  ⏸️  10 queued                │
│  ❌ 0 failed                  │
│                               │
│  ─────────────                │
│                               │
│  Selection                    │
│  ☑ Select All                 │
│  ☐ Deselect All               │
│                               │
│  28 of 28 selected            │
│  (across 7 prompts)           │
│                               │
│  ─────────────                │
│                               │
│  [ Cancel Job ]               │
│                               │
└───────────────────────────────┘
```

**Generating state behaviors:**
- Progress bar updates via polling (every 2-3 seconds)
- Images appear in the grid as they complete (within their prompt group)
- Prompt groups are shown in order (Prompt #1, #2, #3...)
- Completed images default to selected (checked)
- User can deselect images while generation continues (non-blocking)
- Failed images show error icon + error message within their slot
- Cancel button stops queued tasks (already-completed images preserved)
- Prompt text truncated with [▼ Expand] toggle to see full text
- Image cards use same styling as main PromptFinder gallery grid

---

## STATE 3: GALLERY (Review & Select)

Identical layout to Generating state, but:
- Progress bar replaced with completion summary
- All prompt groups fully populated
- Sidebar action button changes to "Create Pages (X selected)"

```
┌─ COMPLETION BANNER ──────────────────────────────────────────────┐
│  ✅ Generation complete: 70 images from 18 prompts (2 failed)   │
└──────────────────────────────────────────────────────────────────┘
```

**Sidebar in Gallery state:**

```
┌─ STICKY SIDEBAR ─────────────┐
│                               │
│  Results                      │
│  ─────────────                │
│                               │
│  ✅ 70 images generated       │
│  ❌ 2 failed                  │
│                               │
│  ─────────────                │
│                               │
│  Selection                    │
│  ☑ Select All                 │
│  ☐ Deselect All               │
│                               │
│  58 of 70 selected            │
│  (across 18 prompts)          │
│                               │
│  ─────────────                │
│                               │
│  [ Create 58 Pages ]          │
│                               │
│  Pages will be created as     │
│  drafts in Public mode.       │
│                               │
│  [ ← Back to Edit ]           │
│  (returns to input state)     │
│                               │
└───────────────────────────────┘
```

**Gallery state behaviors:**
- Click any image card to toggle selection (whole card is click target)
- Deselected images show dimmed/grayed overlay
- Per-group counter: "2 of 4 selected"
- Global counter in sidebar: "58 of 70 selected"
- Select All / Deselect All applies globally
- Failed image slots show: error icon, prompt text, retry button
- "Back to Edit" returns to input state with original prompts preserved
- "Create X Pages" button shows exact count, disabled if 0 selected

---

## STATE 4: CREATING PAGES

Pipeline progress for selected images.

```
┌─ MAIN CONTENT AREA ──────────────────────────────────────────────┐
│                                                                   │
│  📦 Creating Prompt Pages                                        │
│                                                                   │
│  ████████████████████████░░░░░░░░░  34/58 pages (59%)            │
│                                                                   │
│  Current: AI titles & descriptions for image #35...              │
│                                                                   │
│  Pipeline: Generate titles → SEO filenames → Upload to B2 → Save │
│            ████████████████  ████████░░░░░    ░░░░░░░    ░░░░    │
│                                                                   │
│  ⓘ This may take a few minutes. Pages are saved as drafts.      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Note:** NSFW check is SKIPPED for OpenAI provider (built-in filtering).
The `requires_nsfw_check` flag on the provider class controls this.

---

## STATE 5: COMPLETE

```
┌─ MAIN CONTENT AREA ──────────────────────────────────────────────┐
│                                                                   │
│  ✅ Success!                                                     │
│                                                                   │
│  58 prompt pages created as Draft                                │
│                                                                   │
│  📊 Summary:                                                     │
│  ─────────────────────────────────                                │
│  · 18 prompts processed                                          │
│  · 70 images generated (2 failed)                                │
│  · 58 images selected → 58 draft pages created                   │
│  · 12 images discarded (permanently deleted)                     │
│  · Total API cost: $2.10                                         │
│  · Visibility: Public                                            │
│  · Generator tag: ChatGPT                                        │
│                                                                   │
│  [ View Pages in Admin ]  [ Generate More ]                      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Complete state behaviors:**
- "View Pages in Admin" → links to Django admin filtered to show these draft pages
- "Generate More" → resets to State 1 (Input) with empty form
- Discarded images are permanently deleted from B2 storage
- Summary persists until user navigates away

---

## REFERENCE IMAGE VALIDATION (OpenAI Vision)

When a user uploads a reference image, before accepting it:

### Validation Criteria

| Check | Requirement | Error Message |
|-------|-------------|---------------|
| Contains face/person | At least one person detected | "No face detected — please upload a clear photo of a person" |
| Not blurry | Image is sufficiently sharp | "Image appears blurry — please upload a sharper photo" |
| Face prominence | Face/person occupies ≥20% of frame | "Person is too small in the frame — use a closer crop" |

### Implementation

- Use existing OpenAI Vision API integration
- Send image with validation prompt asking about face clarity, blur, and prominence
- Return structured response: pass/fail + specific issue
- Standard upload validation (file type, size, dimensions) runs FIRST, then Vision check
- Loading state while Vision API processes: "Validating image..."

### UI States

```
[Uploading...]  → [Validating...] → ✅ "Face detected" / ❌ "Error message"
```

---

## NSFW PIPELINE — Provider-Based Configuration

```python
class ImageProvider(ABC):
    requires_nsfw_check: bool = True  # Default: run NSFW check

class OpenAIImageProvider(ImageProvider):
    requires_nsfw_check = False  # OpenAI has built-in filtering

class ReplicateImageProvider(ImageProvider):  # Future
    requires_nsfw_check = True  # Lenient filtering, check needed
```

### Pipeline per provider type:

**OpenAI (v1.0):**
```
Generate → Upload to B2 → AI titles/descriptions/tags → SEO filename → Create draft page
```

**Replicate/Grok (future):**
```
Generate → NSFW check → Upload to B2 → AI titles/descriptions/tags → SEO filename → Create draft page
```

---

## CHARACTER DESCRIPTION PREFIX

### How It Works

1. User enters character description in master settings (optional)
2. Description is prepended to EVERY individual prompt
3. Combined prompt is what gets sent to the AI API
4. Each Custom Box shows a "Combined preview" of the final prompt

### Concatenation Format

```
Final API prompt = "{character_description}. {individual_prompt}"
```

### Example

- Character description: "A chubby woman with green eyes and curly blond hair, mid-30s, warm smile"
- Individual prompt: "Dancing in a field of sunflowers at golden hour"
- Combined: "A chubby woman with green eyes and curly blond hair, mid-30s, warm smile. Dancing in a field of sunflowers at golden hour"

### UI: Combined preview in each Custom Box

Shows truncated combined prompt. Only visible when character description has content.
Gray text, smaller font, clearly labeled "Combined preview:" to distinguish from the actual prompt input.

---

## COST ESTIMATION (Sidebar Summary)

The sidebar dynamically calculates and displays:

```
📊 {prompt_count} prompts × {images_per_prompt} images = {total_images} images
⏱️  ~{estimated_minutes} min (at {rate_limit} img/min)
💰 ~${estimated_cost} ({total_images} × ${cost_per_image})
```

### Cost per image by quality (1024×1024):

| Quality | Cost/Image |
|---------|-----------|
| Low | $0.015 |
| Medium | $0.03 |
| High | $0.05 |

Updates in real-time as user changes: prompt count, images per prompt, quality level.

Rate limit is determined by OpenAI tier (recorded after verification).

---

## IMPLEMENTATION PHASES (Revised)

### Phase 1: Database Models + Provider Layer (CC Spec 1)
- BulkGenerationJob model
- GeneratedImage model
- Migrations
- ImageProvider abstract base class
- OpenAIImageProvider implementation (with mock mode for testing)
- Provider registry/factory

### Phase 2: Django-Q Tasks + Backend Logic (CC Spec 2)
- generate_single_image task
- queue_bulk_generation orchestrator
- Rate limiting logic
- create_prompt_from_generated task (page creation pipeline)
- Error handling + retry logic
- Cancel job functionality

### Phase 3: Views + API Endpoints (CC Spec 3)
- Start generation view (POST)
- Status polling endpoint (GET → JSON)
- Create pages endpoint (POST)
- Cancel job endpoint (POST)
- Reference image upload + validation endpoint
- URL routing
- Staff-only permissions

### Phase 4: Frontend — Input State (CC Spec 4)
- Page template with sidebar + main content layout
- Batch Paste mode (textarea + delimiter parsing + preview)
- Custom Boxes mode (dynamic box creation/deletion)
- Mode switching with prompt carry-over
- Master settings sidebar
- Per-box override UI
- Profanity/content validation
- Cost estimation display
- Responsive layout

### Phase 5: Frontend — Generating + Gallery States (CC Spec 5)
- Progress polling JavaScript
- Image grid with prompt grouping
- Expandable prompt text
- Selection toggle (whole-card click)
- Select All / Deselect All
- Generating → Gallery state transition
- Cancel job UI

### Phase 6: Frontend — Creating + Complete States (CC Spec 6)
- Page creation progress display
- Complete state summary
- "View in Admin" / "Generate More" actions
- Cleanup of discarded images

### Phase 7: Integration Testing + Polish (CC Spec 7)
- End-to-end testing
- Edge cases (network errors, API failures, rate limit hits)
- Accessibility review
- Browser testing
- Documentation updates

### Total Estimate: 10-14 days (same as blueprint)

---

## FILES TO CREATE/MODIFY

### New Files

| File | Purpose |
|------|---------|
| `prompts/services/image_providers/__init__.py` | Provider package |
| `prompts/services/image_providers/base.py` | Abstract ImageProvider class |
| `prompts/services/image_providers/openai_provider.py` | OpenAI GPT-Image-1 implementation |
| `prompts/tasks.py` | Django-Q tasks (or add to existing) |
| `prompts/views/bulk_generator_views.py` | Views for bulk generator |
| `prompts/templates/prompts/bulk_generator.html` | Page template |
| `static/js/bulk-generator.js` | JavaScript for all 5 states |
| `static/css/pages/bulk-generator.css` | Page-specific styles |
| `prompts/tests/test_bulk_generator.py` | Test suite |

### Modified Files

| File | Change |
|------|--------|
| `prompts/models.py` | Add BulkGenerationJob + GeneratedImage models |
| `prompts/urls.py` | Add bulk generator URL patterns |
| `prompts/admin.py` | Register new models for Django admin |

---

## EXISTING COMPONENTS TO REUSE

| Component | Location | How It's Used |
|-----------|----------|---------------|
| Django-Q2 task queue | settings.py | Task scheduling |
| Worker dyno | Heroku | Task execution |
| B2 upload service | services/b2_upload.py | Image storage |
| NSFW moderation | services/nsfw_moderation.py | For non-OpenAI providers (future) |
| AI content generation | services/ai_content.py | Titles, descriptions, tags |
| SEO filename generation | utils/seo.py | SEO-friendly filenames |
| OpenAI API key | settings.py | Image generation API |
| Upload validation | Existing validators | File type, size, dimensions |
| Prompt validation | Existing validators | Profanity, content policy |
| Gallery card styling | Existing CSS | Image grid in gallery state |
| Staff page pattern | system_notifications template | Page structure, auth |

---

**END OF FINAL DESIGN SPECIFICATION**

**Next step:** Write Phase 1 CC Spec (Database Models + Provider Layer)
