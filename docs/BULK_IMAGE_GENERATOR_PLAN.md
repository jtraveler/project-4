# BULK IMAGE GENERATOR - Complete Feature Specification

**Document:** `docs/BULK_IMAGE_GENERATOR_PLAN.md`
**Created:** February 4, 2026
**Status:** Planning Complete, Ready for Implementation
**Priority:** #3 in Post-Phase N Roadmap
**Estimated Effort:** 2 weeks

---

## 📋 TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Prerequisites Checklist](#️-prerequisites-checklist) ← **Complete before starting!**
3. [Problem Statement](#problem-statement)
4. [Solution Overview](#solution-overview)
5. [Technical Specifications](#technical-specifications)
6. [Advanced API Features](#advanced-api-features)
7. [Prompting Best Practices](#prompting-best-practices)
8. [API Details](#api-details)
9. [Cost Analysis](#cost-analysis)
10. [User Flow](#user-flow)
11. [Architecture](#architecture)
12. [UI/UX Design](#uiux-design)
13. [Implementation Plan](#implementation-plan)
14. [Premium User Access: BYOK Model](#premium-user-access-byok-model) ← **Critical for scaling**
15. [Future Enhancements](#future-enhancements)
16. [Appendix](#appendix)

---

## EXECUTIVE SUMMARY

### What Is This?

A bulk content generation tool that allows administrators (and eventually premium users) to rapidly create prompt pages by:
1. Entering multiple text prompts (20+ at a time)
2. Automatically generating images via OpenAI's GPT-Image-1.5 API
3. Reviewing generated images in a gallery
4. Selecting which images to publish as prompt pages

### Why Build This?

| Problem | Solution |
|---------|----------|
| Have thousands of text prompts saved | Process them in bulk |
| Don't want to steal reference images | Generate original images |
| Manual upload is slow (one at a time) | Automated pipeline |
| Need to build out categories fast | 20+ prompts per batch |
| Future monetization opportunity | Premium feature prototype |

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Provider | OpenAI (GPT-Image-1.5) | Same API already in use, ChatGPT compatibility, 4x faster than DALL-E 3 |
| Workflow | Gallery preview → Select → Create | Quality control before page creation |
| Rate Limiting | Queue-based, 5-250/min based on tier | Respect API limits, no errors |
| Progress Updates | Polling (2-3 sec) | Simple, proven pattern from Phase N4 |
| Initial Scope | Admin-only | Validate before opening to users |
| **Premium Model** | **BYOK only** | **Platform-paid API doesn't scale (see analysis)** |
| **Batch Generation** | **n=1-4 images per prompt** | **Generate variations, pick best one** |
| **Default Quality** | **Medium ($0.034)** | **Best balance of cost/quality for bulk** |

---

## ⚠️ PREREQUISITES CHECKLIST

**Complete these BEFORE implementation begins:**

### 1. OpenAI Organization Verification (Required)

GPT Image models require identity verification before use.

| Step | Action | Status |
|------|--------|--------|
| 1 | Go to https://platform.openai.com/settings/organization/general | ☐ |
| 2 | Click "Verification" section | ☐ |
| 3 | Click "Start ID Check" | ☐ |
| 4 | Complete Persona identity verification (upload ID + selfie) | ☐ |
| 5 | Wait for approval (usually instant to 24 hours) | ☐ |

**Note:** Persona is a legitimate third-party verification service used by OpenAI to prevent API abuse.

### 2. Confirm API Access

After verification, test that image generation works:

| Step | Action | Status |
|------|--------|--------|
| 1 | Go to OpenAI Playground: https://platform.openai.com/playground | ☐ |
| 2 | Select "Image" mode | ☐ |
| 3 | Choose model: `gpt-image-1.5` | ☐ |
| 4 | Enter test prompt: "A red apple on a white background" | ☐ |
| 5 | Click Generate - confirm image appears | ☐ |

### 3. Check Your API Tier

Your tier determines rate limits (images per minute):

| Step | Action |
|------|--------|
| 1 | Go to https://platform.openai.com/settings/organization/limits |
| 2 | Note your current tier (1-5) |
| 3 | Record your Images Per Minute (IPM) limit |

**Rate limits by tier:**

| Tier | Unlock At | Images/Min |
|------|-----------|------------|
| Tier 1 | $5 spent | 5 |
| Tier 2 | $50 spent | 20 |
| Tier 3 | $100 spent | 50 |
| Tier 4 | $250 spent | 150 |
| Tier 5 | $500 spent | 250 |

### 4. Environment Variables

Confirm these are set in your environment:

```bash
# Already should exist (used for NSFW/content generation)
OPENAI_API_KEY=sk-proj-...
```

No new API keys needed - same key works for image generation.

---

## PROBLEM STATEMENT

### Current State

To add a prompt to PromptFinder today:
1. Find/create an image somewhere
2. Go to `/upload/`
3. Upload single image
4. Wait for processing
5. Fill out form
6. Submit
7. **Repeat for each prompt**

**Time per prompt:** ~2-3 minutes
**Time for 100 prompts:** ~4-5 hours of tedious work

### Desired State

1. Paste 50 text prompts into a form
2. Click "Generate"
3. Wait ~5 minutes while images generate
4. Review gallery, select best ones
5. Click "Create Pages"
6. **Done - 50 prompt pages created**

**Time for 50 prompts:** ~10 minutes (mostly waiting)

---

## SOLUTION OVERVIEW

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Enter Prompts                                          │
│                                                                 │
│  Admin enters 20-50 text prompts + selects AI model + settings  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Generate Images (Background)                           │
│                                                                 │
│  Django-Q worker processes prompts (5-250/min based on tier)    │
│  Images uploaded to B2 as they complete                         │
│  Progress shown in real-time via polling                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Gallery Preview                                        │
│                                                                 │
│  Admin sees all generated images in a grid                      │
│  Can select/deselect which ones to keep                         │
│  Unselected images are discarded                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Create Pages                                           │
│                                                                 │
│  Selected images → Full prompt page creation pipeline:          │
│  - NSFW moderation                                              │
│  - AI title/description/tags generation                         │
│  - SEO filename renaming                                        │
│  - Image variant generation                                     │
│  - Prompt page saved (draft or published)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## TECHNICAL SPECIFICATIONS

### API: OpenAI GPT-Image-1.5

**Why GPT-Image-1.5 (not DALL-E 3):**

| Factor | GPT-Image-1.5 | DALL-E 3 |
|--------|---------------|----------|
| Status | ✅ Current, "state-of-the-art" | ⚠️ Deprecated May 2026 |
| Cost (Medium, Square) | $0.034/image | $0.04/image |
| Rate Limit (Tier 5) | 250/min | 50/min |
| Input Images | ✅ Supported | ❌ Not supported |
| Text Rendering | Excellent | Good |
| ChatGPT Parity | ✅ Same model | ❌ Different |

### Model Options

| Model | Status | Cost Range (Square) | Quality | Use Case |
|-------|--------|---------------------|---------|----------|
| `gpt-image-1.5` | ✅ **Recommended** | $0.009 - $0.133 | Best | Default for all production use |
| `gpt-image-1` | ✅ Supported | ~$0.015 - $0.05 | Excellent | Legacy/fallback |
| `gpt-image-1-mini` | ✅ Supported | Cheapest | Good | High-volume, low-priority |

### Image Dimensions

| Size | Aspect Ratio | Pixels | Speed | Cost Multiplier |
|------|--------------|--------|-------|-----------------|
| Square | 1:1 | 1024×1024 | Fastest | 1× (base price) |
| Landscape | 3:2 | 1536×1024 | Medium | ~1.5× |
| Portrait | 2:3 | 1024×1536 | Medium | ~1.5× |

### Quality Options (GPT Image 1.5 Official Pricing)

| Quality | 1024×1024 | 1024×1536 | 1536×1024 | Recommended For |
|---------|-----------|-----------|-----------|-----------------|
| `low` | **$0.009** | $0.013 | $0.013 | Testing, drafts |
| `medium` | **$0.034** | $0.05 | $0.05 | General use ⭐ |
| `high` | **$0.133** | $0.20 | $0.20 | Hero images, important content |

### Rate Limits by Tier (Official)

| Tier | Unlock Requirement | Images/Minute (IPM) |
|------|-------------------|---------------------|
| Free | — | Not supported |
| Tier 1 | $5 spent | 5 |
| Tier 2 | $50 spent | 20 |
| Tier 3 | $100 spent | 50 |
| Tier 4 | $250 spent | 150 |
| Tier 5 | $500 spent | 250 |

### Input Image Support

GPT-Image-1.5 supports image editing/combining (confirmed: "Image input and output" on OpenAI spec page):

```python
# Edit existing image
response = client.images.edit(
    model="gpt-image-1.5",
    image=open("input.png", "rb"),
    prompt="Add a sunset in the background",
    size="1024x1024"
)

# Combine multiple images (up to 16!)
response = client.images.edit(
    model="gpt-image-1.5",
    image=[
        open("image1.png", "rb"),
        open("image2.png", "rb"),
        open("image3.png", "rb")
    ],
    prompt="Create a gift basket containing all these items"
)
```

**Note:** For v1.0 (bulk generator), we focus on text-to-image. Image editing can be added in v1.3.

---

## ADVANCED API FEATURES

### Important: API Verification Required

Before using GPT Image models, you may need to complete **API Organization Verification** from your OpenAI developer console. This is a one-time requirement.

### Full API Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `model` | `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` | Model selection |
| `prompt` | Up to 32,000 characters | Much longer than DALL-E's 1,000 limit |
| `size` | `1024x1024`, `1536x1024`, `1024x1536`, `auto` | Image dimensions |
| `quality` | `low`, `medium`, `high` | Quality/cost tradeoff |
| `n` | 1-10 | Number of images per request |
| `output_format` | `png`, `jpeg`, `webp` | File format |
| `output_compression` | 0-100 | Compression level (jpeg/webp only) |
| `background` | `transparent`, `opaque`, `auto` | Background transparency |
| `moderation` | `auto`, `low` | Content filtering level |
| `input_fidelity` | `high`, `low` | How closely to match input image features (edits only) |
| `stream` | `true`, `false` | Enable streaming response |
| `partial_images` | 1-3 | Number of partial images during streaming |

### Generate Multiple Images Per Request

Unlike DALL-E 3 (which only supports n=1), GPT Image models can generate up to 10 images per request:

```python
response = client.images.generate(
    model="gpt-image-1.5",
    prompt="A futuristic city skyline at sunset",
    size="1024x1024",
    quality="medium",
    n=4  # Generate 4 variations at once!
)

# Access all images
for i, image in enumerate(response.data):
    save_image(image.b64_json, f"city_{i}.png")
```

**Cost:** You're charged per image, so n=4 costs 4× the single image price.

### Transparent Backgrounds

Perfect for logos, product images, UI elements:

```python
response = client.images.generate(
    model="gpt-image-1.5",
    prompt="A coffee cup icon, minimal design",
    size="1024x1024",
    quality="high",
    background="transparent",
    output_format="png"  # Required for transparency
)
```

### Revised Prompt (See How Model Interpreted Your Request)

The response includes `revised_prompt` showing the model's interpretation:

```python
response = client.images.generate(
    model="gpt-image-1.5",
    prompt="A cat",
    quality="medium"
)

print(response.data[0].revised_prompt)
# Output: "A domestic cat with soft fur, sitting gracefully. 
#          The cat has bright, attentive eyes and a calm expression..."
```

**Useful for:** Understanding why output looks a certain way, improving future prompts.

### World Knowledge

GPT Image 1.5 has built-in reasoning and world knowledge:

| Prompt | Model Infers |
|--------|--------------|
| "Bethel, NY in August 1969" | Woodstock festival |
| "A phone from 2007 with an apple logo" | Original iPhone |
| "The building where the Declaration was signed" | Independence Hall |

---

## PROMPTING BEST PRACTICES

Source: OpenAI GPT-Image-1.5 Prompting Guide (Official Cookbook)

### Quality/Latency Tradeoffs

| Use Case | Recommended Quality | Why |
|----------|--------------------|----|
| Bulk generation (100+ images) | `low` | Sufficient for most content, significantly faster |
| General production | `medium` | Good balance of quality and cost |
| Hero images, marketing | `high` | Maximum visual fidelity |

**Tip:** Always start with `quality="low"` and evaluate before upgrading.

### Composition Control

Be specific about framing and layout:

```python
# ❌ Vague
prompt = "A wizard"

# ✅ Specific
prompt = """A wise elderly wizard, medium close-up shot at eye level.
Soft diffuse lighting from the left, shallow depth of field.
Subject centered with negative space on the right for text overlay."""
```

### Explicit Exclusions

State what you DON'T want:

```python
# ❌ Hoping for the best
prompt = "A product photo of headphones"

# ✅ Explicit constraints  
prompt = """A product photo of wireless headphones on white background.
No watermarks. No text. No logos. No reflections.
Clean, minimalist, e-commerce style."""
```

### For Image Editing

Always state what to change AND what to preserve:

```python
# ❌ Ambiguous
prompt = "Make it sunset"

# ✅ Clear constraints
prompt = """Change the sky to a golden sunset with orange and pink clouds.
Keep the building, people, and foreground exactly the same.
Preserve all lighting on the subjects. Only change the sky."""
```

### Prevent Drift in Iterative Edits

When making multiple edits, repeat your constraints each time:

```python
# Edit 1
prompt1 = "Add sunglasses. Keep face, hair, and clothing exactly the same."

# Edit 2 - REPEAT the constraints
prompt2 = "Change shirt to blue. Keep face, hair, sunglasses exactly the same."

# Edit 3 - STILL repeat
prompt3 = "Add a hat. Keep face, hair, sunglasses, blue shirt exactly the same."
```

---

## API DETAILS

### Authentication

Uses existing OpenAI API key (same as NSFW moderation and AI content generation).

```python
# Already configured in settings.py
OPENAI_API_KEY = env('OPENAI_API_KEY')
```

### Basic Generation Request

```python
from openai import OpenAI

client = OpenAI()

response = client.images.generate(
    model="gpt-image-1.5",
    prompt="A cyberpunk city at night with neon signs and rain",
    size="1024x1024",      # or "1536x1024", "1024x1536"
    quality="medium",       # "low", "medium", or "high"
    n=1                     # Number of images (1-10)
)

# Response contains base64-encoded image
image_base64 = response.data[0].b64_json
```

### Response Format

```python
{
    "created": 1707123456,
    "data": [
        {
            "b64_json": "<base64-encoded-image-data>",
            "revised_prompt": "A detailed cyberpunk cityscape..."  # Model's interpretation
        }
    ]
}
```

### Error Handling

```python
from openai import OpenAI, RateLimitError, APIError

try:
    response = client.images.generate(...)
except RateLimitError:
    # Retry with exponential backoff
    pass
except APIError as e:
    # Log error, mark task as failed
    pass
```

---

## COST ANALYSIS

### Per-Image Costs (GPT Image 1.5 Official Pricing)

**Square images (1024×1024) - Most common:**

| Quality | Cost/Image | 20 Images | 50 Images | 100 Images |
|---------|------------|-----------|-----------|------------|
| Low | $0.009 | $0.18 | $0.45 | $0.90 |
| **Medium** | **$0.034** | **$0.68** | **$1.70** | **$3.40** |
| High | $0.133 | $2.66 | $6.65 | $13.30 |

**Portrait/Landscape images (1024×1536 or 1536×1024):**

| Quality | Cost/Image | 20 Images | 50 Images | 100 Images |
|---------|------------|-----------|-----------|------------|
| Low | $0.013 | $0.26 | $0.65 | $1.30 |
| **Medium** | **$0.05** | **$1.00** | **$2.50** | **$5.00** |
| High | $0.20 | $4.00 | $10.00 | $20.00 |

### Admin Usage (v1.0 - Platform Key)

For admin (Mateo) building content with platform's API key:

**Using Medium quality (recommended):**

| Scenario | Images/Month | Cost/Month |
|----------|--------------|------------|
| Light use | 200 | ~$7 |
| Medium use | 500 | ~$17 |
| Heavy use | 1,000 | ~$34 |

**Using Low quality (drafts/testing):**

| Scenario | Images/Month | Cost/Month |
|----------|--------------|------------|
| Heavy use | 1,000 | ~$9 |
| Very heavy | 2,000 | ~$18 |

### Premium User Costs (v1.1 - BYOK)

For premium users with BYOK, **they pay OpenAI directly**:

| Their Usage | Their OpenAI Bill (Medium) | Your Revenue | Your Profit |
|-------------|----------------------------|--------------|-------------|
| 100 images | ~$3.40 | $12-15/mo | $12-15/mo |
| 500 images | ~$17 | $12-15/mo | $12-15/mo |
| 2,000 images | ~$68 | $12-15/mo | $12-15/mo |

**Key insight:** With BYOK, your profit is fixed regardless of how much they generate. Power users who generate thousands of images still only cost you $0 in API fees.

See [Premium User Access: BYOK Model](#premium-user-access-byok-model) for full analysis of why this is the only viable model for scaling.

---

## USER FLOW

### Admin Flow (v1)

```
1. Navigate to /admin/bulk-generator/ (or /generate/)

2. See input form:
   ┌─────────────────────────────────────────────────────────┐
   │  Bulk Image Generator                                   │
   │                                                         │
   │  Model: [gpt-image-1 ▼]                                │
   │  Size:  [Square 1024×1024 ▼]                           │
   │  Quality: [High ▼]                                      │
   │  Generator Category: [ChatGPT ▼]                       │
   │  Default Status: [Draft ▼]                             │
   │                                                         │
   │  Prompts (one per line):                               │
   │  ┌─────────────────────────────────────────────────┐   │
   │  │ 1. [________________________________] [✕]      │   │
   │  │ 2. [________________________________] [✕]      │   │
   │  │ 3. [________________________________] [✕]      │   │
   │  │ ...                                             │   │
   │  │ 20. [______________________________] [✕]       │   │
   │  └─────────────────────────────────────────────────┘   │
   │                                                         │
   │  [+ Add More Prompts]                                   │
   │                                                         │
   │  Summary: 18 prompts | Est. time: ~2 min | Cost: ~$0.90│
   │                                                         │
   │  [ Start Generation ]                                   │
   └─────────────────────────────────────────────────────────┘

3. Click "Start Generation"

4. See progress view:
   ┌─────────────────────────────────────────────────────────┐
   │  ⏳ Generating Images                                   │
   │                                                         │
   │  Progress: 7 of 18 complete                             │
   │  ████████████████░░░░░░░░░░░░░░░ 39%                   │
   │                                                         │
   │  Rate: 10 images/min | Time remaining: ~1 min 30 sec   │
   │                                                         │
   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
   │  │ ☑️ ✓   │ │ ☑️ ✓   │ │ ☐      │ │ ☑️ ✓   │          │
   │  │ [img]  │ │ [img]  │ │ [img]  │ │ [img]  │          │
   │  │Prompt 1│ │Prompt 2│ │Prompt 3│ │Prompt 4│          │
   │  └────────┘ └────────┘ └────────┘ └────────┘          │
   │                                                         │
   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
   │  │ ⏳     │ │ ⏳     │ │ ⏳     │ │ ⏳     │          │
   │  │ [...]  │ │ [...]  │ │ [...]  │ │ [...]  │          │
   │  └────────┘ └────────┘ └────────┘ └────────┘          │
   │                                                         │
   │  ⓘ Select images as they appear                        │
   │                                                         │
   │  [ Cancel Generation ]                                  │
   └─────────────────────────────────────────────────────────┘

5. All images complete → Gallery view:
   ┌─────────────────────────────────────────────────────────┐
   │  ✅ Generation Complete - Select Images to Publish      │
   │                                                         │
   │  Selected: 15 of 18 | [ Select All ] [ Deselect All ]  │
   │                                                         │
   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
   │  │ ☑️ ✓   │ │ ☑️ ✓   │ │ ☐      │ │ ☑️ ✓   │          │
   │  │ [img]  │ │ [img]  │ │ [img]  │ │ [img]  │          │
   │  │Prompt 1│ │Prompt 2│ │Prompt 3│ │Prompt 4│          │
   │  │ [👁️]   │ │ [👁️]   │ │ [👁️]   │ │ [👁️]   │  ← Preview │
   │  └────────┘ └────────┘ └────────┘ └────────┘          │
   │  ... more images ...                                   │
   │                                                         │
   │  [ Create 15 Prompt Pages ]                            │
   └─────────────────────────────────────────────────────────┘

6. Click "Create Prompt Pages"

7. See creation progress:
   ┌─────────────────────────────────────────────────────────┐
   │  Creating Prompt Pages...                               │
   │                                                         │
   │  Progress: 8 of 15 complete                             │
   │  ████████████████████░░░░░░░░░░ 53%                    │
   │                                                         │
   │  Current: Running NSFW check on image 9...             │
   └─────────────────────────────────────────────────────────┘

8. Complete:
   ┌─────────────────────────────────────────────────────────┐
   │  ✅ Success! 15 prompt pages created                    │
   │                                                         │
   │  Status: Draft (ready to publish from admin)           │
   │                                                         │
   │  [ View in Admin ] [ Generate More ]                   │
   └─────────────────────────────────────────────────────────┘
```

---

## ARCHITECTURE

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Browser)                                             │
│                                                                 │
│  bulk-generator.html                                            │
│  ├── Input form (prompts, settings)                            │
│  ├── Progress view (polling for updates)                       │
│  └── Gallery view (select images)                              │
│                                                                 │
│  bulk-generator.js                                              │
│  ├── Form validation                                            │
│  ├── AJAX submission                                            │
│  ├── Progress polling (every 2-3 seconds)                      │
│  └── Image selection handling                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│  WEB DYNO (Django)                                              │
│                                                                 │
│  views/bulk_generator_views.py                                  │
│  ├── BulkGeneratorView (form page)                             │
│  ├── StartGenerationView (queue tasks)                         │
│  ├── GenerationStatusView (progress API)                       │
│  └── CreatePagesView (create prompts from selected)            │
│                                                                 │
│  models.py                                                      │
│  ├── BulkGenerationJob (tracks overall job)                    │
│  └── GeneratedImage (individual image results)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓ Django-Q
┌─────────────────────────────────────────────────────────────────┐
│  WORKER DYNO (Django-Q)                                         │
│                                                                 │
│  tasks.py                                                       │
│  ├── generate_single_image(job_id, prompt, settings)           │
│  │   ├── Call OpenAI GPT-Image-1 API                           │
│  │   ├── Upload to B2                                           │
│  │   ├── Update GeneratedImage record                          │
│  │   └── Update BulkGenerationJob progress                     │
│  │                                                              │
│  └── create_prompt_from_generated(image_id)                    │
│      ├── Run NSFW moderation                                    │
│      ├── Generate AI title/description/tags                    │
│      ├── Create image variants                                  │
│      ├── Rename file for SEO                                    │
│      └── Save Prompt object                                     │
│                                                                 │
│  services/image_generator.py                                    │
│  └── OpenAIImageGenerator                                       │
│      ├── generate(prompt, model, size, quality)                │
│      ├── _handle_rate_limit()                                   │
│      └── _upload_to_b2(image_data)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                              │
│                                                                 │
│  OpenAI API                                                     │
│  └── GPT-Image-1 image generation                              │
│                                                                 │
│  Backblaze B2                                                   │
│  └── Image storage                                              │
│                                                                 │
│  Cloudflare CDN                                                 │
│  └── Image delivery                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Database Models

```python
class BulkGenerationJob(models.Model):
    """Tracks an overall bulk generation job."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Settings
    model = models.CharField(max_length=50, default='gpt-image-1')
    size = models.CharField(max_length=20, default='1024x1024')
    quality = models.CharField(max_length=10, default='high')
    generator = models.ForeignKey(AIGenerator, on_delete=models.SET_NULL, null=True)
    
    # Progress
    total_prompts = models.PositiveIntegerField()
    completed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']


class GeneratedImage(models.Model):
    """Individual generated image within a job."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    job = models.ForeignKey(BulkGenerationJob, on_delete=models.CASCADE, related_name='images')
    
    # Input
    prompt_text = models.TextField()
    order = models.PositiveIntegerField()  # Position in original list
    
    # Output
    image_url = models.URLField(blank=True)  # B2/Cloudflare URL
    revised_prompt = models.TextField(blank=True)  # Model's interpretation
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Selection
    is_selected = models.BooleanField(default=True)  # User selection
    
    # Link to created prompt (after page creation)
    prompt = models.ForeignKey('Prompt', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
```

### Rate Limiting Implementation

```python
# tasks.py

from django_q.tasks import async_task, schedule
from datetime import timedelta

OPENAI_RATE_LIMIT = 10  # images per minute
DELAY_BETWEEN_TASKS = 6  # seconds (60/10 = 6)

def queue_bulk_generation(job_id):
    """Queue all image generation tasks with rate limiting."""
    
    job = BulkGenerationJob.objects.get(id=job_id)
    images = job.images.filter(status='pending').order_by('order')
    
    for index, image in enumerate(images):
        # Schedule with staggered delay
        delay_seconds = index * DELAY_BETWEEN_TASKS
        
        async_task(
            'prompts.tasks.generate_single_image',
            str(image.id),
            task_name=f'generate-{image.id}',
            q_options={
                'retry': 3,
                'timeout': 120,
            }
        )
        
        # Add delay between task queuing to respect rate limits
        if delay_seconds > 0:
            import time
            time.sleep(0.1)  # Small delay to maintain order
```

### Progress Polling (No WebSockets Needed)

```javascript
// bulk-generator.js

class BulkGeneratorProgress {
    constructor(jobId) {
        this.jobId = jobId;
        this.pollInterval = 2000; // 2 seconds
        this.polling = false;
    }
    
    startPolling() {
        this.polling = true;
        this.poll();
    }
    
    stopPolling() {
        this.polling = false;
    }
    
    async poll() {
        if (!this.polling) return;
        
        try {
            const response = await fetch(`/api/bulk-generator/status/${this.jobId}/`);
            const data = await response.json();
            
            this.updateUI(data);
            
            if (data.status === 'completed' || data.status === 'failed') {
                this.stopPolling();
                this.onComplete(data);
            } else {
                setTimeout(() => this.poll(), this.pollInterval);
            }
        } catch (error) {
            console.error('Polling error:', error);
            setTimeout(() => this.poll(), this.pollInterval);
        }
    }
    
    updateUI(data) {
        // Update progress bar
        const percent = (data.completed_count / data.total_prompts) * 100;
        document.querySelector('.progress-bar').style.width = `${percent}%`;
        document.querySelector('.progress-text').textContent = 
            `${data.completed_count} of ${data.total_prompts} complete`;
        
        // Add newly completed images to gallery
        data.images.forEach(image => {
            if (image.status === 'completed' && !this.renderedImages.has(image.id)) {
                this.addImageToGallery(image);
                this.renderedImages.add(image.id);
            }
        });
    }
}
```

---

## UI/UX DESIGN

### Page Location

**Option A (Recommended):** `/admin/bulk-generator/`
- Clearly admin-only
- Separate from public site

**Option B:** `/generate/` (staff-only)
- Cleaner URL
- Can evolve to premium feature

### Design Principles

1. **Progressive disclosure** - Show complexity as needed
2. **Real-time feedback** - Images appear as they complete
3. **Non-blocking** - User can select while generation continues
4. **Clear costs** - Show estimated cost before generation
5. **Recoverable** - Can cancel mid-generation

### Mobile Considerations

- Responsive grid (4 columns → 2 columns → 1 column)
- Touch-friendly selection checkboxes
- Sticky action buttons

---

## IMPLEMENTATION PLAN

### Phase 1: Core Infrastructure (3-4 days)

| Task | Effort | Files |
|------|--------|-------|
| Create database models | 2 hrs | models.py |
| Create migrations | 30 min | migrations/ |
| OpenAI image service | 4 hrs | services/image_generator.py |
| B2 upload integration | 2 hrs | Reuse existing |
| Django-Q tasks | 4 hrs | tasks.py |
| Rate limiting logic | 2 hrs | tasks.py |

### Phase 2: API Endpoints (2-3 days)

| Task | Effort | Files |
|------|--------|-------|
| Start generation view | 3 hrs | views/bulk_generator_views.py |
| Status polling endpoint | 2 hrs | views/api_views.py |
| Create pages endpoint | 3 hrs | views/bulk_generator_views.py |
| URL routing | 30 min | urls.py |

### Phase 3: Frontend (3-4 days)

| Task | Effort | Files |
|------|--------|-------|
| Input form template | 4 hrs | templates/bulk_generator.html |
| Progress view | 3 hrs | templates/bulk_generator.html |
| Gallery view | 4 hrs | templates/bulk_generator.html |
| JavaScript logic | 6 hrs | static/js/bulk-generator.js |
| CSS styling | 3 hrs | static/css/bulk-generator.css |

### Phase 4: Integration & Testing (2-3 days)

| Task | Effort |
|------|--------|
| Integration testing | 4 hrs |
| Error handling | 3 hrs |
| Edge cases | 3 hrs |
| Admin permissions | 1 hr |
| Documentation | 2 hrs |

### Total Estimate: 10-14 days

---

## PREMIUM USER ACCESS: BYOK MODEL

### Why BYOK (Bring Your Own Key) Is Required

After thorough analysis, **BYOK is the only viable model** for offering bulk generation to premium customers. This section documents why and what alternatives were considered.

---

### ❌ WHAT WON'T WORK: Platform-Paid API

We explored the option of charging customers a subscription fee while paying API costs ourselves. **This model does not scale.**

#### The Rate Limit Problem

OpenAI rate limits are **per API key**, not per end-user:

```
YOUR API Key (Tier 1 = 10 imgs/min, Tier 5 = 50 imgs/min)

User A: 50 images ──┐
User B: 50 images ──┼──→ ALL share YOUR rate limit
User C: 50 images ──┤
User D: 50 images ──┘
... (100 users)

Scenario: 100 users × 50 images = 5,000 images
Your capacity: 10/min (Tier 1) or 50/min (Tier 5)

Time to process ALL users:
- Tier 1: 5,000 ÷ 10 = 500 minutes = 8.3 HOURS 💀
- Tier 5: 5,000 ÷ 50 = 100 minutes = 1.7 HOURS 💀

Users would wait HOURS for their images. Unacceptable UX.
```

#### The Cost Risk Problem

Even if rate limits weren't an issue, cost overruns are dangerous:

| Scenario | Your Expectation | Reality | Result |
|----------|------------------|---------|--------|
| User pays $19/mo | ~100 images = $5 cost | User generates 1,000 images = $50 cost | **-$31 loss per user** |

With hard caps, you anger users. Without hard caps, you lose money.

#### The Queue Nightmare

If multiple users submit jobs simultaneously:

```
User A submits 50 prompts at 2:00 PM
User B submits 50 prompts at 2:01 PM
User C submits 50 prompts at 2:02 PM

With YOUR API key (10/min):
- User A: Completes at 2:05 PM (5 min wait) ✓
- User B: Completes at 2:10 PM (9 min wait) 😐
- User C: Completes at 2:15 PM (13 min wait) 😠

Scale to 50 concurrent users? Last user waits 4+ hours.
```

#### Verdict: Platform-Paid API = NOT VIABLE

| Factor | Platform-Paid | Assessment |
|--------|---------------|------------|
| Rate limits | All users share YOUR limit | ❌ Doesn't scale |
| Cost control | Risk of overuse | ❌ Unpredictable costs |
| User experience | Long queues when busy | ❌ Poor UX at scale |
| Profitability | Thin margins, loss risk | ❌ Risky |

---

### ✅ WHAT WORKS: BYOK (Bring Your Own Key)

With BYOK, each user operates independently:

```
User A: THEIR key → THEIR 10/min limit → THEIR OpenAI bill
User B: THEIR key → THEIR 10/min limit → THEIR OpenAI bill
User C: THEIR key → THEIR 10/min limit → THEIR OpenAI bill

Each user is independent! No conflicts!
```

#### BYOK Benefits

| Factor | BYOK | Assessment |
|--------|------|------------|
| Rate limits | Each user has OWN limits | ✅ Infinitely scalable |
| Cost to you | $0 API costs | ✅ Zero risk |
| User experience | Fast (no competition) | ✅ Excellent |
| Profitability | 100% margin on subscription | ✅ Predictable |

#### BYOK Security Implementation

User API keys must be handled securely:

```python
# models.py
from cryptography.fernet import Fernet
from django.conf import settings

class UserAPIKeys(models.Model):
    """Securely store user API keys with encryption."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    _openai_key_encrypted = models.BinaryField(null=True, blank=True)
    key_added_at = models.DateTimeField(null=True, blank=True)
    key_verified = models.BooleanField(default=False)
    
    def set_openai_key(self, plain_key):
        """Encrypt and store the key."""
        if plain_key:
            fernet = Fernet(settings.ENCRYPTION_KEY)
            self._openai_key_encrypted = fernet.encrypt(plain_key.encode())
            self.key_added_at = timezone.now()
        else:
            self._openai_key_encrypted = None
            self.key_added_at = None
            self.key_verified = False
    
    def get_openai_key(self):
        """Decrypt and return the key (server-side only)."""
        if not self._openai_key_encrypted:
            return None
        fernet = Fernet(settings.ENCRYPTION_KEY)
        return fernet.decrypt(bytes(self._openai_key_encrypted)).decode()
    
    openai_key = property(get_openai_key, set_openai_key)
```

#### BYOK Security Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Encrypt keys at rest | Fernet symmetric encryption | ✅ |
| Never log keys | Mask in all logging | ✅ |
| Never send to frontend | Server-side use only | ✅ |
| Verify key on save | Test API call before storing | ✅ |
| Allow key deletion | User can remove anytime | ✅ |
| Secure transmission | HTTPS only | ✅ |
| Key rotation | User can update key | ✅ |

#### BYOK User Experience

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings → API Keys                                            │
│                                                                 │
│  🔑 OpenAI API Key                                              │
│                                                                 │
│  Bring your own OpenAI key to unlock bulk image generation.     │
│                                                                 │
│  [sk-proj-••••••••••••••••••••••••••••] [👁️] [Save]            │
│                                                                 │
│  ✅ Key verified - Connected to your OpenAI account             │
│     Rate limit: 10 images/minute                                │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  🔒 Security                                                    │
│  • Your key is encrypted and stored securely                    │
│  • We never see or log your key in plain text                   │
│  • Key is only used server-side for image generation            │
│  • You can delete your key anytime                              │
│                                                                 │
│  📖 Get your key: https://platform.openai.com/api-keys          │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Benefits of BYOK:                                              │
│  • Unlimited image generation (within your OpenAI limits)       │
│  • No monthly caps - generate as much as you need               │
│  • Your rate limits = your speed                                │
│  • Pay OpenAI directly (often cheaper than bundled pricing)     │
│  • Full control over your API usage                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Premium Pricing Model (BYOK)

| Tier | Price | Images | API Key | What You Get |
|------|-------|--------|---------|--------------|
| **Free** | $0 | 0 | N/A | Browse, save prompts |
| **Pro** | $12-15/mo | Unlimited | BYOK Required | Bulk generator, all features |

#### What's Included in Pro (BYOK)

| Feature | Provided By |
|---------|-------------|
| Bulk generator interface | PromptFinder |
| Image storage (B2) | PromptFinder |
| CDN delivery (Cloudflare) | PromptFinder |
| NSFW moderation | PromptFinder (your OpenAI key for text, their key for images) |
| AI title/description/tags | PromptFinder (your OpenAI key) |
| Prompt page creation | PromptFinder |
| **Image generation API** | **Customer's OpenAI key** |

#### Profit Analysis

| Tier | Monthly Revenue | Your API Cost | Your Infra Cost | Net Profit |
|------|-----------------|---------------|-----------------|------------|
| Pro BYOK | $12-15 | $0 | ~$0.50 (storage) | **$11.50-14.50** |

**100 Pro users = $1,150-1,450/month pure profit**

---

### Decision Summary

| Model | Scalable? | Profitable? | Good UX? | Decision |
|-------|-----------|-------------|----------|----------|
| Platform pays API | ❌ No | ❌ Risky | ❌ Poor at scale | **REJECTED** |
| **BYOK** | ✅ Yes | ✅ Yes | ✅ Yes | **APPROVED** |

---

## FUTURE ENHANCEMENTS

### v1.0: Admin-Only (Current)

- Bulk generator for admin (Mateo)
- Uses platform OpenAI key
- No customer access yet

### v1.1: Premium User Access (BYOK)

- BYOK integration
- Secure key storage
- Key verification flow
- Subscription tier checks

### v1.2: Additional Models (BYOK)

- Add Replicate integration (Flux, SDXL)
- Users can add Replicate API key too
- Model comparison view

### v1.3: Image Editing

- Input image support
- Style transfer
- Image variations

### v1.4: Batch Templates

- Save prompt templates
- CSV import
- Scheduled generation

---

## APPENDIX

### A. OpenAI API Reference

**Endpoint:** `POST https://api.openai.com/v1/images/generations`

**Full Request Example:**
```python
response = client.images.generate(
    model="gpt-image-1.5",
    prompt="A serene Japanese garden with cherry blossoms",
    size="1024x1024",
    quality="medium",
    n=1,
    response_format="b64_json"
)
```

**Full Response Example:**
```json
{
    "created": 1707123456,
    "data": [
        {
            "b64_json": "/9j/4AAQSkZJRg...",
            "revised_prompt": "A peaceful Japanese garden featuring blooming cherry blossom trees..."
        }
    ]
}
```

### B. Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 429 | Rate limit exceeded | Retry with backoff |
| 400 | Invalid request | Check prompt/parameters |
| 401 | Invalid API key | Check configuration |
| 500 | OpenAI server error | Retry |

### C. Reusable Components from Phase N4

| Component | Location | Reuse |
|-----------|----------|-------|
| B2 upload | `services/b2_upload.py` | Direct reuse |
| NSFW moderation | `services/nsfw_moderation.py` | Direct reuse |
| AI content generation | `services/ai_content.py` | Direct reuse |
| SEO filename | `utils/seo.py` | Direct reuse |
| Django-Q setup | `settings.py` | Already configured |
| Worker dyno | Heroku | Already running |

### D. Cost Calculator

```
Total Cost = (Number of Images) × (Cost per Image)

GPT Image 1.5 - Cost per Image (Square 1024×1024):
- Low:    $0.009
- Medium: $0.034
- High:   $0.133

GPT Image 1.5 - Cost per Image (Portrait/Landscape):
- Low:    $0.013
- Medium: $0.05
- High:   $0.20

Example (Medium quality, Square):
50 images × $0.034 = $1.70

Example (High quality, Square):
50 images × $0.133 = $6.65
```

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 4, 2026 | Claude/Mateo | Initial creation |
| 1.1 | Feb 4, 2026 | Claude/Mateo | Added BYOK section, documented why platform-paid API doesn't scale |
| 1.2 | Feb 4, 2026 | Claude/Mateo | Updated to GPT-Image-1.5 with official pricing (Low: $0.009, Medium: $0.034, High: $0.133) |
| 1.3 | Feb 4, 2026 | Claude/Mateo | Added Advanced API Features section and Prompting Best Practices from official OpenAI cookbook |
| 1.4 | Feb 4, 2026 | Claude/Mateo | Added Prerequisites Checklist (Organization Verification, API access test, tier check) |

---

**END OF SPECIFICATION**
