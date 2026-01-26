# PHASE N4: OPTIMISTIC UPLOAD FLOW - COMPREHENSIVE REPORT

**Document Version:** 1.0  
**Created:** January 26, 2026  
**Author:** Claude AI (in collaboration with Mateo Johnson)  
**Project:** PromptFinder  
**Status:** Planning Complete - Ready for Implementation

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Philosophy & Goals](#2-philosophy--goals)
3. [Technical Architecture Overview](#3-technical-architecture-overview)
4. [Complete User Journey](#4-complete-user-journey)
5. [Upload Page Flow (Step 1)](#5-upload-page-flow-step-1)
6. [Processing Page Flow (Step 2)](#6-processing-page-flow-step-2)
7. [AI Content Generation](#7-ai-content-generation)
8. [Failure Scenarios & Fallback Handling](#8-failure-scenarios--fallback-handling)
9. [Cancel & Delete Handling](#9-cancel--delete-handling)
10. [Storage & File Cleanup](#10-storage--file-cleanup)
11. [SEO Strategy](#11-seo-strategy)
12. [Performance Optimizations](#12-performance-optimizations)
13. [User Experience (UX) Design](#13-user-experience-ux-design)
14. [Background Task System (Django-Q)](#14-background-task-system-django-q)
15. [Polling System](#15-polling-system)
16. [Future Upgrades & Improvements](#16-future-upgrades--improvements)
17. [Database Schema Changes](#17-database-schema-changes)
18. [API Endpoints](#18-api-endpoints)
19. [File Structure](#19-file-structure)
20. [Implementation Checklist](#20-implementation-checklist)
21. [Glossary](#21-glossary)

---

## 1. EXECUTIVE SUMMARY

### What Is This Document?

This document describes the complete upload flow for PromptFinder, from the moment a user drops an image file until they see their fully-processed prompt on the website. It covers every step, every edge case, and every decision made along the way.

### Why Are We Building This?

**The Problem:**
Previously, users had to wait 15-20 seconds staring at a loading spinner while their image was uploaded, processed, and analyzed. This felt slow and frustrating.

**The Solution:**
We're rebuilding the upload flow to feel "instant" by:
1. Showing previews immediately (before upload completes)
2. Processing images in the background while users fill out forms
3. Using a dedicated "processing page" so users aren't blocked
4. Running AI analysis after the user submits (when we have all the data)

### Key Numbers

| Metric | Before Phase N4 | After Phase N4 |
|--------|-----------------|----------------|
| Time to see preview | 3-5 seconds | **Instant** (from browser memory) |
| Time to submit form | 15-20 seconds wait | **0 seconds** (processing happens after) |
| Time on processing page | N/A | **5-10 seconds** |
| Total perceived wait | 15-20 seconds | **5-10 seconds** |

### Technology Choices

| Component | Technology | Why |
|-----------|------------|-----|
| Background Tasks | Django-Q2 | Free, uses existing PostgreSQL, reliable |
| Status Updates | Polling (HTTP) | Simple, works everywhere, good enough for 5-10s waits |
| Image Storage | Backblaze B2 + Cloudflare CDN | Cost-effective, fast, no content restrictions |
| AI Analysis | OpenAI GPT-4o-mini Vision | Best price/quality ratio for image analysis |

---

## 2. PHILOSOPHY & GOALS

### The Restaurant Analogy

> "At a restaurant, we don't ask customers to wash their own dishes. They're customers, not employees."

**Applied to PromptFinder:**

| What Customers (Users) Do | What We (The Platform) Handle |
|---------------------------|-------------------------------|
| Upload their image/video | Store it securely on B2 |
| Write their prompt text | Generate SEO-optimized title |
| Select the AI generator | Generate SEO-optimized description |
| Click submit | Generate relevant tags |
| | Create SEO-friendly URL slug |
| | Rename files for image SEO |
| | Check for NSFW content |
| | Create multiple image sizes |

**Key Insight:** Users are here to share their AI art, not to become SEO experts. We handle all the optimization automatically.

### Core UX Principles

1. **Never make users wait for things they don't need to see**
   - Thumbnails can generate while they type
   - AI analysis can run after they submit

2. **Always show something immediately**
   - Preview from browser memory (instant)
   - Their prompt text (they just typed it)
   - Their generator selection

3. **Give users control**
   - They can cancel at any time
   - They can edit after processing completes
   - They see clear status indicators

4. **Fail gracefully**
   - If AI fails, use fallback content
   - If processing hangs, show helpful message
   - Always save the user's work

### Success Metrics

- **Primary:** Processing page → Final prompt in under 10 seconds (typical)
- **Secondary:** User can submit and close browser; prompt still completes
- **Tertiary:** Zero data loss on failures

---

## 3. TECHNICAL ARCHITECTURE OVERVIEW

### System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S BROWSER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │   Upload Page   │───▶│ Processing Page │───▶│ Prompt Detail   │     │
│  │   /upload/      │    │ /prompt/proc/   │    │ /prompt/slug/   │     │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘     │
│           │                      │                                      │
│           │ JavaScript           │ JavaScript                           │
│           │ - File preview       │ - Polling (every 3s)                │
│           │ - B2 direct upload   │ - Modal display                     │
│           │ - NSFW status        │                                      │
│           │ - Form handling      │                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                    │                      │
                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DJANGO APPLICATION                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │  Upload Views   │    │  API Views      │    │  Django-Q       │     │
│  │                 │    │                 │    │  Worker         │     │
│  │ - upload_step1  │    │ - presign       │    │                 │     │
│  │ - upload_submit │    │ - complete      │    │ - AI task       │     │
│  │                 │    │ - moderate      │    │ - Rename task   │     │
│  │                 │    │ - variants      │    │                 │     │
│  │                 │    │ - poll status   │    │                 │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                    │                      │
                    ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │  Backblaze B2   │    │  OpenAI API     │    │  Cloudflare CDN │     │
│  │                 │    │                 │    │                 │     │
│  │ - Store images  │    │ - NSFW check    │    │ - Serve images  │     │
│  │ - Store videos  │    │ - AI generation │    │ - Global cache  │     │
│  │ - Store thumbs  │    │                 │    │                 │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Request Flow Diagram

```
USER ACTION                    SERVER PROCESS                 RESULT
───────────────────────────────────────────────────────────────────────────

1. User drops image
        │
        ▼
2. Browser shows preview ────────────────────────────────▶ INSTANT
   (from local memory,                                     (no server)
    no upload yet)
        │
        ▼
3. JS requests presign URL ──▶ Django generates ─────────▶ ~500ms
                               presigned B2 URL
        │
        ▼
4. Browser uploads to B2 ────▶ B2 receives file ─────────▶ ~1-2s
   (direct, bypasses Django)
        │
        ▼
5. JS calls /complete/ ──────▶ Django verifies ──────────▶ ~300ms
                               upload exists
        │
        ▼
6. JS calls /moderate/ ──────▶ Django calls OpenAI ──────▶ ~2-4s
                               Vision for NSFW
        │
        ▼
7. JS calls /variants/ ──────▶ Django generates ─────────▶ ~2-4s
   (background)                thumb, medium,               (parallel with
                               large, webp                   user typing)
        │
        ▼
8. User fills form ──────────────────────────────────────▶ User time
   (while variants                                          (variants
    generate)                                                done by now)
        │
        ▼
9. User clicks Submit ───────▶ Django creates ───────────▶ ~200ms
                               Prompt record
        │
        ▼
10. Redirect to ─────────────▶ Processing page ──────────▶ Instant
    /prompt/processing/{uuid}   loads
        │
        ▼
11. Django-Q task starts ────▶ Download image ───────────▶ ~1-2s
                               for Vision
        │
        ▼
12. OpenAI Vision API ───────▶ Analyze image + ──────────▶ ~3-8s
                               prompt text
        │
        ▼
13. Save AI results ─────────▶ Update Prompt ────────────▶ ~100ms
                               record
        │
        ▼
14. Polling detects ─────────▶ Modal appears ────────────▶ Instant
    completion
        │
        ▼
15. User clicks ─────────────▶ Redirect to ──────────────▶ Instant
    "View Prompt"              /prompt/{slug}/
        │
        ▼
16. Django-Q rename task ────▶ Rename B2 files ──────────▶ ~3-6s
    (background)               for SEO                      (user doesn't
                                                            wait)
```

---

## 4. COMPLETE USER JOURNEY

This section walks through exactly what a user experiences, step by step.

### Step 1: User Arrives at Upload Page

**URL:** `/upload/`

**What they see:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                    ┌─────────────────────────────────┐                  │
│                    │                                 │                  │
│                    │    📁 Drag and drop to upload   │                  │
│                    │           - or -                │                  │
│                    │        [ Browse ]               │                  │
│                    │                                 │                  │
│                    │    Images: JPG, PNG, GIF, WebP  │                  │
│                    │    Videos: MP4, WebM, MOV       │                  │
│                    │    Max: 3MB images, 15MB videos │                  │
│                    │                                 │                  │
│                    └─────────────────────────────────┘                  │
│                                                                         │
│    ┌─────────────────────────────────────────────────────────────┐     │
│    │  FORM (disabled, grayed out)                                │     │
│    │                                                             │     │
│    │  Prompt * [____________________________] (disabled)         │     │
│    │  Generator * [Select...              ▼] (disabled)          │     │
│    │  ☐ Save as draft                        (disabled)          │     │
│    │                                                             │     │
│    │  [ Submit ] (disabled)                                      │     │
│    │                                                             │     │
│    │  "Select an image or video to enable the form"              │     │
│    └─────────────────────────────────────────────────────────────┘     │
│                                                                         │
│    Uploads this week: 3 of 100                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Technical details:**
- Form is disabled until file is selected
- Weekly upload counter shows usage
- Rate limits enforced (100/week free, unlimited premium)

---

### Step 2: User Drops an Image

**What happens INSTANTLY (< 100ms):**

1. JavaScript reads file from browser memory
2. Creates preview using `URL.createObjectURL(file)`
3. Shows preview image immediately (NO upload yet!)
4. Enables form fields

**What they see:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │                    │  │                                         │   │
│  │  [Preview Image]   │  │  Prompt *                               │   │
│  │                    │  │  ┌─────────────────────────────────┐    │   │
│  │  From your device  │  │  │ Enter the prompt you used...   │    │   │
│  │  (not uploaded yet)│  │  └─────────────────────────────────┘    │   │
│  │                    │  │                                         │   │
│  │  [ Change Image ]  │  │  Generator *                            │   │
│  │                    │  │  ┌─────────────────────────────────┐    │   │
│  └────────────────────┘  │  │ Select generator...          ▼ │    │   │
│                          │  └─────────────────────────────────┘    │   │
│  ┌────────────────────┐  │                                         │   │
│  │ ⏳ Uploading...    │  │  ☐ Save as draft                       │   │
│  │ ████████░░░░ 67%   │  │                                         │   │
│  └────────────────────┘  │  [ Submit ] (enabled after checks)      │   │
│                          │                                         │   │
│                          └─────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Step 3: Background Upload (User Doesn't Wait)

**What happens in background (user is typing their prompt):**

```
TIMELINE (all in background):
─────────────────────────────────────────────────────────────────────────

0.0s  User drops file
      │
0.1s  ├── Preview shown (from browser memory) ✅
      │
0.2s  ├── Request presigned URL from Django
      │
0.7s  ├── Start direct upload to B2 ──────────────────┐
      │                                                │
      │   User is typing their prompt text...          │ B2 Upload
      │                                                │ (~1-2s)
2.0s  ├── B2 upload complete ◄────────────────────────┘
      │
2.1s  ├── Call /complete/ to verify
      │
2.4s  ├── Start NSFW moderation ──────────────────────┐
      │                                                │
      │   User is still typing...                      │ NSFW Check
      │                                                │ (~2-4s)
5.0s  ├── NSFW check passed ✅ ◄──────────────────────┘
      │
5.1s  ├── Start variant generation ───────────────────┐
      │                                                │
      │   User is selecting generator...               │ Variants
      │                                                │ (~2-4s)
8.0s  ├── Variants complete ✅ ◄──────────────────────┘
      │
      │   User clicks Submit (whenever ready)
      │   └── Everything is already done!
```

**Key insight:** By the time the user finishes typing their prompt and selecting a generator, all the background processing is usually complete.

---

### Step 4: NSFW Check Results

**If NSFW check PASSES:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌────────────────────┐                                                 │
│  │                    │  Status: ✅ Content verified                    │
│  │  [Preview Image]   │                                                 │
│  │                    │  Your image passed our content guidelines.      │
│  │                    │                                                 │
│  └────────────────────┘                                                 │
│                                                                         │
│  [ Submit ] ← NOW ENABLED                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**If NSFW check FAILS (critical violation):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ⛔ UPLOAD REJECTED                                                     │
│                                                                         │
│  This image contains content that violates our community guidelines.    │
│                                                                         │
│  Prohibited content includes:                                           │
│  • Explicit nudity or sexual content                                    │
│  • Violence or gore                                                     │
│  • Content involving minors in any suggestive context                   │
│                                                                         │
│  [ Upload Different Image ]                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**If NSFW check FLAGS (high severity - needs review):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ⚠️ CONTENT FLAGGED FOR REVIEW                                         │
│                                                                         │
│  Your image may contain content that needs admin review before          │
│  it can be published.                                                   │
│                                                                         │
│  You can still submit, but your prompt will be saved as a draft         │
│  until approved by our team (usually within 24 hours).                  │
│                                                                         │
│  [ Submit as Draft ]  [ Upload Different Image ]                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Step 5: User Fills Out Form

**Required fields:**

| Field | Required | Notes |
|-------|----------|-------|
| Prompt | ✅ Yes | The actual prompt text they used |
| Generator | ✅ Yes | Midjourney, DALL-E, Stable Diffusion, etc. |
| Save as draft | ❌ No | Checkbox, default unchecked |

**What they see while filling out:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │                    │  │                                         │   │
│  │  [Preview Image]   │  │  Prompt *                               │   │
│  │                    │  │  ┌─────────────────────────────────┐    │   │
│  │  ✅ Uploaded       │  │  │ a cinematic vertical frame of a │    │   │
│  │  ✅ Content OK     │  │  │ stylish young woman in the      │    │   │
│  │  ✅ Ready          │  │  │ early 1980s standing beside a   │    │   │
│  │                    │  │  │ classic yellow Jaguar E-Type... │    │   │
│  │                    │  │  └─────────────────────────────────┘    │   │
│  └────────────────────┘  │                                         │   │
│                          │  Generator *                            │   │
│                          │  ┌─────────────────────────────────┐    │   │
│                          │  │ Midjourney                    ▼ │    │   │
│                          │  └─────────────────────────────────┘    │   │
│                          │                                         │   │
│                          │  ☐ Save as draft                       │   │
│                          │                                         │   │
│                          │  [ Submit ] ← ENABLED                   │   │
│                          │                                         │   │
│                          └─────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Step 6: User Clicks Submit

**What happens:**

1. JavaScript gathers form data
2. POST request to `/upload/submit/`
3. Django creates Prompt record with:
   - `processing_uuid` = new UUID (e.g., `a7b3c9d1-...`)
   - `title` = "Processing..." (placeholder)
   - `slug` = None (not generated yet)
   - `status` = 0 (DRAFT)
   - `b2_image_url`, `b2_thumb_url`, etc. (already have these)
   - `content` = user's prompt text
   - `ai_generator` = selected generator
4. Django queues AI generation task in Django-Q
5. Redirect to `/prompt/processing/{uuid}/`

**Total time:** ~200ms (very fast - just database insert and redirect)

---

### Step 7: Processing Page

**URL:** `/prompt/processing/a7b3c9d1-e2f4-4a5b-8c9d-1234567890ab/`

**What they see immediately:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌────────────────────────────────┐  ┌───────────────────────────────┐ │
│  │                                │  │                               │ │
│  │                                │  │  @username                    │ │
│  │                                │  │  Just now                     │ │
│  │      [PREVIEW IMAGE]           │  │                               │ │
│  │                                │  │  ─────────────────────────    │ │
│  │      (Using existing B2        │  │                               │ │
│  │       thumbnail URL)           │  │  Title                        │ │
│  │                                │  │  ⏳ Generating...             │ │
│  │                                │  │                               │ │
│  │                                │  │  Description                  │ │
│  └────────────────────────────────┘  │  ⏳ Generating...             │ │
│                                      │                               │ │
│  ┌────────────────────────────────┐  │  Tags                         │ │
│  │  PROMPT                        │  │  ⏳ Generating...             │ │
│  │  ┌──────────────────────────┐  │  │                               │ │
│  │  │ a cinematic vertical     │  │  │  ─────────────────────────    │ │
│  │  │ frame of a stylish       │  │  │                               │ │
│  │  │ young woman in the       │  │  │  Actions:                     │ │
│  │  │ early 1980s standing     │  │  │  [🗑️ Delete]  [📋 Copy]      │ │
│  │  │ beside a classic yellow  │  │  │  [✏️ Edit] (disabled)        │ │
│  │  │ Jaguar E-Type parked...  │  │  │                               │ │
│  │  └──────────────────────────┘  │  │                               │ │
│  │  [ 📋 Copy Prompt ]            │  │                               │ │
│  └────────────────────────────────┘  └───────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  MORE FROM @username                                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │   │
│  │  │  thumb  │ │  thumb  │ │  thumb  │ │  +3     │               │   │
│  │  │   1     │ │   2     │ │   3     │ │  more   │               │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**What's happening in background:**

```
DJANGO-Q TASK: generate_ai_content
──────────────────────────────────────────────────────────────────────────

1. Task picked up by worker        (~0.5-1s after submit)

2. Check if prompt was deleted     (exit early if user cancelled)
   └── If prompt.is_deleted: return

3. Download image from B2/CDN      (~1-2s)
   └── Store in memory for Vision API

4. Call OpenAI Vision API          (~3-8s)
   ┌─────────────────────────────────────────────────────────────────┐
   │  INPUT:                                                        │
   │  • Image (as base64)                                           │
   │  • User's prompt text                                          │
   │  • Available tags from database                                │
   │                                                                │
   │  ANALYSIS RATIO:                                               │
   │  • 80% based on VISION (what's literally in the image)        │
   │  • 20% based on USER TEXT (intent, keywords, context)         │
   │                                                                │
   │  OUTPUT:                                                       │
   │  • title: "Vintage Fashion Against Urban Backdrop"            │
   │  • description: "This captivating image features..."          │
   │  • tags: ["Photography", "Women", "Fashion Models", ...]      │
   │  • relevance_score: 0.85                                      │
   └─────────────────────────────────────────────────────────────────┘

5. Generate slug from title        (~50ms)
   └── "vintage-fashion-against-urban-backdrop"

6. Update Prompt record            (~100ms)
   └── title, description, tags, slug, processing_complete=True

7. If user wanted to publish:
   └── Set status = 1 (published)
```

---

### Step 8: Polling Detects Completion

**JavaScript on processing page:**

```javascript
// Polls every 3 seconds
setInterval(async () => {
    const response = await fetch(`/api/prompt/status/${uuid}/`);
    const data = await response.json();
    
    if (data.processing_complete) {
        showCompletionModal(data);
    }
}, 3000);
```

**Server response when complete:**

```json
{
    "processing_complete": true,
    "success": true,
    "title": "Vintage Fashion Against Urban Backdrop",
    "description": "This captivating image features...",
    "tags": ["Photography", "Women", "Fashion Models", "Urban", "Vintage"],
    "slug": "vintage-fashion-against-urban-backdrop",
    "final_url": "/prompt/vintage-fashion-against-urban-backdrop/"
}
```

---

### Step 9: Completion Modal

**What they see:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ╔═══════════════════════════════════════════════════════════════════╗ │
│  ║                                                                   ║ │
│  ║   ✅ Your prompt is ready!                                        ║ │
│  ║                                                                   ║ │
│  ║   "Vintage Fashion Against Urban Backdrop"                        ║ │
│  ║                                                                   ║ │
│  ║   Your prompt has been published and is now live.                 ║ │
│  ║                                                                   ║ │
│  ║                     [ View Your Prompt ]                          ║ │
│  ║                                                                   ║ │
│  ╚═══════════════════════════════════════════════════════════════════╝ │
│                                                                         │
│  (background page still visible, slightly dimmed)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why a modal instead of auto-redirect?**

If we auto-redirected, the user might:
- Be reading "More from @username" section
- Be in the middle of copying their prompt
- Feel jarred by unexpected navigation

The modal respects their attention and gives them control.

---

### Step 10: Final Prompt Detail Page

**URL:** `/prompt/vintage-fashion-against-urban-backdrop/`

User clicks "View Your Prompt" and sees the full prompt detail page with:
- ✅ AI-generated title
- ✅ AI-generated description  
- ✅ AI-generated tags
- ✅ All action buttons enabled (Edit, Delete, Share, etc.)
- ✅ Comments section
- ✅ Like button
- ✅ Save to collection

**Background task (user doesn't wait):**
- B2 files get renamed for SEO
- `vintage-fashion-midjourney-thumb-1234.jpg` → proper SEO name
- URLs update silently on next page load

---

## 5. UPLOAD PAGE FLOW (STEP 1)

### File Selection & Validation

**Accepted file types:**

| Type | Extensions | Max Size |
|------|------------|----------|
| Images | .jpg, .jpeg, .png, .gif, .webp | 3 MB |
| Videos | .mp4, .webm, .mov | 15 MB |

**Validation errors (shown as modal):**

| Error | Message |
|-------|---------|
| File too large (image) | "Image must be under 3MB. Your file is X MB." |
| File too large (video) | "Video must be under 15MB. Your file is X MB." |
| Invalid type | "File type not supported. Please upload JPG, PNG, GIF, WebP, MP4, WebM, or MOV." |

### Presigned URL Flow

**Why presigned URLs?**

Instead of uploading through Django (slow, uses server memory), we upload directly to B2:

```
WITHOUT presigned URLs:
Browser → Django → B2
         (bottleneck)

WITH presigned URLs:
Browser → B2 (direct, fast)
    ↑
    └── Django just provides the URL
```

**Presigned URL request:**

```javascript
// Frontend
const response = await fetch('/api/upload/b2/presign/', {
    method: 'POST',
    body: JSON.stringify({
        filename: file.name,
        content_type: file.type,
        file_size: file.size
    })
});
const { presigned_url, file_key } = await response.json();
```

**Backend generates URL:**

```python
# b2_presign_service.py (simplified)
def generate_presigned_url(filename, content_type, file_size):
    # Validate
    if file_size > MAX_SIZE:
        raise ValidationError("File too large")
    
    # Generate unique key
    file_key = f"uploads/{uuid4()}/{filename}"
    
    # Create presigned URL (valid for 1 hour)
    presigned_url = b2_client.generate_presigned_url(
        bucket=BUCKET_NAME,
        key=file_key,
        expires_in=3600,
        content_type=content_type
    )
    
    return presigned_url, file_key
```

### Direct Upload to B2

```javascript
// Frontend - direct upload
const uploadResponse = await fetch(presigned_url, {
    method: 'PUT',
    headers: {
        'Content-Type': file.type
    },
    body: file  // Raw file bytes
});

if (uploadResponse.ok) {
    // File is now in B2!
    await notifyDjangoUploadComplete(file_key);
}
```

### NSFW Moderation

**Service:** OpenAI GPT-4o-mini with Vision

**How it works:**

```python
# cloudinary_moderation.py (simplified)
def check_nsfw(image_url):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": NSFW_CHECK_PROMPT},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }]
    )
    
    result = json.loads(response.choices[0].message.content)
    return {
        'severity': result['severity'],  # 'none', 'low', 'medium', 'high', 'critical'
        'violations': result.get('violations', [])
    }
```

**Severity levels:**

| Severity | Meaning | Action |
|----------|---------|--------|
| `none` | Completely safe | ✅ Allow upload |
| `low` | Minor concern | ✅ Allow upload |
| `medium` | Borderline | ✅ Allow, note internally |
| `high` | Likely problematic | ⚠️ Flag for admin review |
| `critical` | Clearly prohibited | ❌ Reject upload |

### Variant Generation

**After NSFW passes, generate image variants:**

| Variant | Size | Purpose |
|---------|------|---------|
| `thumb` | 300×300 max | Cards, grids, thumbnails |
| `medium` | 600×600 max | Detail page (mobile) |
| `large` | 1200×1200 max | Detail page (desktop) |
| `webp` | 600×600 max | Modern browsers, smaller file |

**Generated using Pillow:**

```python
# image_processor.py (simplified)
def process_upload(image_file):
    results = {}
    
    for size_name, (max_w, max_h) in SIZES.items():
        img = Image.open(image_file)
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        results[size_name] = buffer.getvalue()
    
    # WebP version
    img = Image.open(image_file)
    img.thumbnail((600, 600), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=80)
    results['webp'] = buffer.getvalue()
    
    return results
```

### Rate Limiting

**Two types of rate limits:**

| Limit | Value | Window | Purpose |
|-------|-------|--------|---------|
| Weekly uploads | 100 (free) / unlimited (premium) | Rolling 7 days | Prevent abuse |
| B2 API calls | 20 | 1 hour | Prevent rapid-fire uploads |

**Rate limit modal:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ⏳ Upload Limit Reached                                    │
│                                                             │
│  You've reached the maximum of 20 uploads per hour.         │
│  Please wait a bit before uploading more.                   │
│                                                             │
│  Upgrade to Premium for higher limits.                      │
│                                                             │
│  [ OK ]                                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. PROCESSING PAGE FLOW (STEP 2)

### URL Structure

**Processing page URL:**
```
/prompt/processing/{processing_uuid}/
```

Example: `/prompt/processing/a7b3c9d1-e2f4-4a5b-8c9d-1234567890ab/`

**Why UUID instead of ID or slug?**

| Option | Example | Problem |
|--------|---------|---------|
| Database ID | `/prompt/processing/1234/` | Guessable, security risk |
| Slug | `/prompt/processing/vintage-fashion/` | Doesn't exist yet! |
| **UUID** | `/prompt/processing/a7b3c9d1.../` | ✅ Secure, immediate |

### Page Elements

**SHOWN during processing:**

| Element | Source | Why |
|---------|--------|-----|
| Preview image | B2 thumbnail URL | User uploaded it |
| Prompt text | Prompt.content | User typed it |
| Generator | Prompt.ai_generator | User selected it |
| Author avatar/name | request.user | It's them |
| Copy prompt button | JavaScript | Useful while waiting |
| Delete button | Existing trash | User might want to cancel |
| "More from author" | Prompt.objects.filter(author=user) | Something to look at |

**SHOWN with loading state:**

| Element | Loading State | Final State |
|---------|---------------|-------------|
| Title | "⏳ Generating..." | AI-generated title |
| Description | "⏳ Generating..." | AI-generated description |
| Tags | "⏳ Generating..." | AI-generated tags |

**HIDDEN during processing:**

| Element | Why Hidden |
|---------|------------|
| Comments section | No comments yet, clutters page |
| Like button | Can't like without final URL |
| Save to collection | Same reason |
| Share buttons | No final URL to share |
| View count | It's 0 |
| Edit button | Disabled, not hidden (show as grayed out) |

### Action Buttons State

| Button | During Processing | After Complete |
|--------|-------------------|----------------|
| 🗑️ Delete | ✅ Enabled | ✅ Enabled |
| 📋 Copy Prompt | ✅ Enabled | ✅ Enabled |
| ✏️ Edit | ❌ Disabled (grayed) | ✅ Enabled |
| ❤️ Like | ❌ Hidden | ✅ Shown |
| 🔖 Save | ❌ Hidden | ✅ Shown |

### Security

**Who can view the processing page?**

Only the author. This is enforced in the view:

```python
def processing_page(request, processing_uuid):
    prompt = get_object_or_404(Prompt, processing_uuid=processing_uuid)
    
    # Only author can view processing page
    if prompt.author != request.user:
        raise Http404("Not found")
    
    return render(request, 'prompts/processing.html', {'prompt': prompt})
```

---

## 7. AI CONTENT GENERATION

### The 80/20 Analysis Ratio

**Why not 100% Vision?**

If we only used Vision, we might miss the user's intent:
- Image shows: woman, car, building
- Vision might title it: "Woman Standing By Vehicle"
- But user's prompt was about: "1980s vintage fashion aesthetic"
- Better title: "Vintage Fashion Against Urban Backdrop"

**Why not 100% User Text?**

Users often write incomplete or "garbage" prompts:
- "fashion shoot downtown" (too vague)
- "test image 3" (not useful)
- "asdfasdf" (keyboard mashing)

**The 80/20 balance:**

```
ANALYSIS COMPOSITION:
──────────────────────────────────────────────────────────

80% VISION (What's Literally In The Image)
├── Objects: woman, vintage dress, yellow car, brownstone building
├── Style: cinematic, golden hour lighting, soft shadows
├── Composition: vertical frame, symmetry, urban backdrop
├── Colors: pastel dress, yellow car, warm tones
└── Quality: high resolution, professional photography style

20% USER TEXT (Intent & Keywords)
├── Keywords mentioned: "1980s", "stylish", "Jaguar E-Type"
├── Style intent: "Wes Anderson aesthetic"
├── Subject emphasis: "young woman" (main subject)
└── Context: This is AI-generated art, not a real photo

COMBINED OUTPUT:
├── Title: "Vintage Fashion Against Urban Backdrop"
│   └── (Captures both visual + user intent)
├── Description: "This captivating image features a stylish woman
│                 in a vintage dress standing beside a classic
│                 yellow Jaguar E-Type..."
│   └── (Describes visuals + incorporates user keywords)
└── Tags: ["Photography", "Women", "Fashion Models", "Urban", "Vintage"]
    └── (Matched against available tags in database)
```

### AI Prompt Template

```python
CONTENT_GENERATION_PROMPT = """
Analyze this image and the user's prompt text: "{user_prompt_text}".

Provide:
{
  "violations": [],
  "title": "Short, descriptive title (5-10 words)",
  "description": "SEO-optimized description (50-100 words) that describes the image and how to use this prompt",
  "suggested_tags": ["5 most relevant tags from the provided list"],
  "relevance_score": 0.85,
  "relevance_explanation": "Brief explanation of how well the prompt matches the image"
}

IMPORTANT:
- Analyze BOTH the visual content AND the user's prompt text
- Give 80% weight to what you SEE in the image
- Give 20% weight to keywords and intent from user's text
- Suggested tags should capture: subject, style, mood, composition
- Title should be keyword-rich for SEO
- Description should be unique, valuable, and include usage tips
- Relevance score: 1.0 = perfect match, 0.0 = completely unrelated
- You MUST respond with valid JSON only

Tag options (choose 5): {available_tags}
"""
```

### SEO Asset Generation

**Generated in Python (not AI) for efficiency:**

```python
def _generate_filename(title, ai_generator):
    """
    Generate SEO-optimized filename.
    Example: "vintage-fashion-midjourney-prompt-1706299200.jpg"
    """
    # Remove stop words
    stop_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of']
    words = [w for w in title.lower().split() if w not in stop_words]
    
    # Take first 2-3 keywords (max 30 chars)
    keywords = '-'.join(words[:3])
    ai_slug = ai_generator.lower().replace(' ', '-')
    timestamp = int(time.time())
    
    return f"{keywords}-{ai_slug}-prompt-{timestamp}.jpg"


def _generate_alt_tag(title, ai_generator):
    """
    Generate alt text for accessibility (max 125 chars).
    Example: "Vintage Fashion Against Urban Backdrop - Midjourney Prompt - AI-generated image"
    """
    alt = f"{title} - {ai_generator} Prompt - AI-generated image"
    
    if len(alt) > 125:
        # Truncate title, keep rest
        max_title = 125 - len(f" - {ai_generator} Prompt - AI-generated image")
        alt = f"{title[:max_title]}... - {ai_generator} Prompt - AI-generated image"
    
    return alt
```

### Token Usage & Costs

| Component | Tokens (approx) | Cost |
|-----------|-----------------|------|
| System prompt | ~500 | - |
| Image (low detail) | ~85 | - |
| User prompt text | ~100 | - |
| Response | ~200 | - |
| **Total** | ~885 | **~$0.0013** |

**Monthly cost estimate:**

| Uploads/month | Cost |
|---------------|------|
| 100 | $0.13 |
| 1,000 | $1.30 |
| 10,000 | $13.00 |

Very affordable!

---

## 8. FAILURE SCENARIOS & FALLBACK HANDLING

### Scenario 1: OpenAI API Timeout

**Trigger:** API doesn't respond within 30 seconds

**What happens:**

```python
try:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        timeout=30  # 30 second timeout
    )
except APITimeoutError:
    # Fallback mode
    return {
        'success': False,
        'error': 'timeout',
        'title': user_prompt[:50] + "...",
        'description': '',
        'tags': []
    }
```

**User experience:**

```
Modal shown:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ⚠️ Your prompt was saved with limited details              │
│                                                             │
│  We couldn't automatically generate the title, description, │
│  and tags for your prompt. This sometimes happens due to    │
│  high demand.                                               │
│                                                             │
│  Your prompt has been saved as a DRAFT and our team has     │
│  been notified to complete it shortly.                      │
│                                                             │
│  [ View Draft ]  [ Edit Now ]  [ Try Again ]                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Database state:**

| Field | Value |
|-------|-------|
| `title` | "a cinematic vertical frame of a stylish young..." (first 50 chars) |
| `excerpt` | "" (empty) |
| `tags` | [] (empty) |
| `slug` | "a-cinematic-vertical-frame-of-a-stylish-young" |
| `status` | 0 (DRAFT) |
| `needs_seo_review` | True |
| `processing_complete` | True |

### Scenario 2: OpenAI API Error

**Trigger:** API returns error (rate limit, server error, etc.)

**Handling:** Same as timeout - fallback mode

### Scenario 3: Image Download Failure

**Trigger:** Can't download image from B2/CDN for Vision analysis

**What happens:**

```python
def _download_image_as_base64(image_url):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return base64.b64encode(response.content).decode()
    except requests.RequestException as e:
        logger.error(f"Failed to download image: {e}")
        return None  # Triggers fallback
```

**User experience:** Same fallback modal as timeout

### Scenario 4: Task Crashes Mid-Execution

**Trigger:** Server restart, out of memory, unexpected exception

**What happens:**

1. Prompt record exists with `processing_complete = False`
2. Django-Q task never finishes
3. User's polling keeps checking but never gets completion
4. After ~60 seconds, show different message:

```
After 60 seconds:
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Taking longer than expected...                          │
│                                                             │
│  Your prompt is still being processed. This sometimes       │
│  takes a bit longer during busy periods.                    │
│                                                             │
│  You can:                                                   │
│  • Wait a bit longer                                        │
│  • Close this page - your prompt will still be processed    │
│  • Check back later from your profile                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

After 120 seconds:
┌─────────────────────────────────────────────────────────────┐
│  ❌ Something went wrong                                    │
│                                                             │
│  We're having trouble processing your prompt. Your image    │
│  has been saved and our team has been notified.             │
│                                                             │
│  [ Try Again ]  [ Delete & Start Over ]  [ Contact Support ]│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scenario 5: Partial Success

**Trigger:** AI returns some but not all fields

**Example:** AI returns title but no tags

```python
def handle_ai_response(response, prompt):
    # Use AI values if present, fallback otherwise
    prompt.title = response.get('title') or prompt.content[:50]
    prompt.excerpt = response.get('description') or ''
    
    tags = response.get('suggested_tags') or []
    if not tags:
        prompt.needs_seo_review = True  # Flag for admin
    
    # Always mark complete so user isn't stuck
    prompt.processing_complete = True
    prompt.save()
```

### Admin Notification for Failures

**When failures occur:**

1. `needs_seo_review` flag set to True
2. Prompt appears in SEO Review Queue (`/admin/seo-review/`)
3. Admin can manually enter title/description/tags
4. Admin clicks "Complete Review" to publish

**Admin queue view:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SEO REVIEW QUEUE (3 prompts need attention)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  #1 - Uploaded 2 hours ago by @jake                                    │
│  ┌─────────┐                                                           │
│  │  thumb  │  Current title: "a cinematic vertical frame of a..."     │
│  └─────────┘  Prompt: "a cinematic vertical frame of a stylish..."    │
│               Reason: AI timeout                                        │
│               [ Edit & Complete ]                                       │
│                                                                         │
│  #2 - Uploaded 5 hours ago by @sarah                                   │
│  ...                                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. CANCEL & DELETE HANDLING

### User Wants to Cancel During Processing

**Method:** Click trash icon on processing page

**Confirmation modal:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🗑️ Cancel this upload?                                    │
│                                                             │
│  This prompt will be moved to your trash.                   │
│  You can restore it within 5 days if you change your mind.  │
│                                                             │
│  [ Keep It ]  [ Move to Trash ]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**What happens when confirmed:**

```python
def delete_prompt(request, prompt_id):
    prompt = get_object_or_404(Prompt, id=prompt_id, author=request.user)
    
    # Soft delete (move to trash)
    prompt.is_deleted = True
    prompt.deleted_at = timezone.now()
    prompt.save()
    
    # AI task will check this and exit early
    # (see Django-Q task section)
    
    messages.success(request, "Upload cancelled. You can restore it from trash within 5 days.")
    return redirect('prompts:upload_step1')
```

**In Django-Q task:**

```python
def generate_ai_content_task(prompt_id):
    prompt = Prompt.objects.get(id=prompt_id)
    
    # CHECK FIRST: Did user cancel?
    if prompt.is_deleted:
        logger.info(f"Prompt {prompt_id} was deleted, skipping AI generation")
        return  # Exit early, don't process
    
    # Continue with normal processing...
```

### File Cleanup Timing

**Current behavior (Phase D.5 trash system):**

```
User cancels upload
    ↓
Prompt moves to trash (is_deleted = True, deleted_at = now)
    ↓
B2 files remain in storage (not deleted yet)
    ↓
Daily cleanup job runs: cleanup_deleted_prompts
    ↓
Job finds prompts where:
    • is_deleted = True
    • deleted_at > 5 days ago (free users)
    • deleted_at > 30 days ago (premium users)
    ↓
Job deletes B2 files + hard deletes prompt
```

**Why files linger for 5-30 days:**

| Reason | Explanation |
|--------|-------------|
| Restore option | User might change their mind and restore from trash |
| Simplicity | Uses existing trash system, no new code needed |
| Cost | B2 free tier is 10GB; 1000 cancelled 3MB uploads = 3GB (fine) |

**Cost analysis:**

```
B2 Storage Pricing:
• First 10GB: FREE
• Over 10GB: $0.006/GB/month

Example scenario:
• 100 cancelled uploads per month (generous estimate)
• Average 15MB per upload (with variants)
• = 1.5GB of lingering files
• Cost if over free tier: $0.009/month (negligible)
```

### Future Optimization: Immediate Cleanup for Cancels

**Document for future implementation:**

```
FUTURE ENHANCEMENT: Immediate B2 Cleanup for Cancelled Uploads
──────────────────────────────────────────────────────────────

WHEN TO IMPLEMENT:
• When storage costs become meaningful (1000+ cancels/month)
• When we want cleaner storage management

HOW IT WOULD WORK:
1. User cancels on processing page
2. Prompt moves to trash (existing behavior)
3. ALSO queue separate Django-Q task: delete_b2_files_task
4. Task deletes all B2 files for this prompt within minutes
5. Trash record kept (for audit trail) but files gone

WHY NOT NOW:
• Current scale doesn't justify complexity
• Files don't cost anything in free tier
• Simpler system is easier to maintain

PRIORITY: Low (only at scale)
```

---

## 10. STORAGE & FILE CLEANUP

### B2 Storage Structure

**Bucket organization:**

```
promptfinder-media/
├── uploads/
│   └── {uuid}/
│       ├── original.jpg          (user's upload)
│       ├── thumb.jpg             (300×300)
│       ├── medium.jpg            (600×600)
│       ├── large.jpg             (1200×1200)
│       └── webp.webp             (600×600 WebP)
├── videos/
│   └── {uuid}/
│       ├── original.mp4
│       └── thumb.jpg             (extracted frame)
└── renamed/                      (after SEO renaming)
    └── vintage-fashion-midjourney-prompt-{timestamp}/
        ├── thumb.jpg
        ├── medium.jpg
        └── ...
```

### File Lifecycle

```
STAGE 1: Upload (on upload page)
────────────────────────────────────────────────────────────────────────
• Files uploaded to: uploads/{uuid}/original.jpg
• Variants generated: uploads/{uuid}/thumb.jpg, medium.jpg, etc.
• Names are temporary UUIDs

STAGE 2: Processing Complete (after AI)
────────────────────────────────────────────────────────────────────────
• Files renamed for SEO (separate background task)
• Old files: uploads/{uuid}/thumb.jpg
• New files: renamed/vintage-fashion-midjourney-thumb-123.jpg
• Old files deleted after rename succeeds

STAGE 3: Normal Lifecycle
────────────────────────────────────────────────────────────────────────
• Files served via Cloudflare CDN
• URLs like: https://media.promptfinder.net/renamed/vintage-fashion-...
• Files remain as long as prompt exists

STAGE 4: Deletion (if user deletes prompt)
────────────────────────────────────────────────────────────────────────
• Prompt moves to trash
• Files linger for 5-30 days
• Daily cleanup job removes files + prompt record
```

### Cleanup Jobs

**Existing job: `cleanup_deleted_prompts`**

```python
# management/commands/cleanup_deleted_prompts.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Find prompts in trash past retention period
        cutoff_free = timezone.now() - timedelta(days=5)
        cutoff_premium = timezone.now() - timedelta(days=30)
        
        prompts_to_delete = Prompt.objects.filter(
            is_deleted=True
        ).filter(
            Q(author__is_premium=False, deleted_at__lt=cutoff_free) |
            Q(author__is_premium=True, deleted_at__lt=cutoff_premium)
        )
        
        for prompt in prompts_to_delete:
            # Delete B2 files
            delete_b2_files(prompt)
            # Hard delete record
            prompt.delete()
```

**Schedule:** Daily at 3:00 UTC via Heroku Scheduler

### Future Enhancement: Stuck Prompt Detection

```
FUTURE ENHANCEMENT: Detect and Recover Stuck Prompts
──────────────────────────────────────────────────────────────

PROBLEM:
If Django-Q task crashes mid-execution, prompt stays in
processing_complete=False state forever.

SOLUTION:
Scheduled job runs every hour:
1. Find prompts where:
   • processing_complete = False
   • created_at > 30 minutes ago
2. For each stuck prompt:
   • Option A: Retry AI generation task
   • Option B: Apply fallback values, set needs_seo_review
3. Log incident for monitoring

IMPLEMENTATION:
# management/commands/recover_stuck_prompts.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(minutes=30)
        
        stuck = Prompt.objects.filter(
            processing_complete=False,
            created_at__lt=cutoff
        )
        
        for prompt in stuck:
            logger.warning(f"Recovering stuck prompt {prompt.id}")
            # Apply fallback
            prompt.title = prompt.content[:50] + "..."
            prompt.needs_seo_review = True
            prompt.processing_complete = True
            prompt.status = 0  # Draft
            prompt.save()

PRIORITY: Medium (edge case but important for reliability)
```

---

## 11. SEO STRATEGY

### On-Page SEO Elements

**Generated automatically by AI:**

| Element | Source | Max Length | Example |
|---------|--------|------------|---------|
| Title tag | AI title | 60 chars | "Vintage Fashion Against Urban Backdrop" |
| Meta description | AI description | 155 chars | "This captivating image features a stylish woman..." |
| H1 tag | AI title | N/A | Same as title |
| Alt text | Python-generated | 125 chars | "Vintage Fashion... - Midjourney Prompt - AI-generated" |
| URL slug | From AI title | N/A | "vintage-fashion-against-urban-backdrop" |

### Image SEO

**File naming:**

```
BEFORE (temporary):
uploads/a7b3c9d1-e2f4-4a5b-8c9d/thumb.jpg

AFTER (SEO-optimized):
vintage-fashion-midjourney-prompt-1706299200-thumb.jpg

Components:
• vintage-fashion = keywords from title
• midjourney = AI generator
• prompt = identifies as prompt image
• 1706299200 = timestamp (uniqueness)
• thumb = variant type
```

**Alt text template:**

```
{Title} - {Generator} Prompt - AI-generated image

Example:
"Vintage Fashion Against Urban Backdrop - Midjourney Prompt - AI-generated image"
```

**Srcset for responsive images:**

```html
<img src="{{medium_url}}"
     srcset="{{thumb_url}} 300w,
             {{medium_url}} 600w,
             {{large_url}} 1200w"
     sizes="(max-width: 768px) 100vw, 60vw"
     alt="{{alt_text}}"
     loading="eager"
     fetchpriority="high">
```

### Structured Data (JSON-LD)

**To be added to prompt detail page:**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ImageObject",
  "name": "{{ prompt.title }}",
  "description": "{{ prompt.excerpt }}",
  "contentUrl": "{{ prompt.display_large_url }}",
  "thumbnailUrl": "{{ prompt.display_thumb_url }}",
  "creator": {
    "@type": "Person",
    "name": "{{ prompt.author.username }}",
    "url": "{{ profile_url }}"
  },
  "datePublished": "{{ prompt.created_on|date:'c' }}",
  "dateModified": "{{ prompt.updated_on|date:'c' }}",
  "interactionStatistic": [
    {
      "@type": "InteractionCounter",
      "interactionType": "https://schema.org/LikeAction",
      "userInteractionCount": {{ prompt.likes.count }}
    },
    {
      "@type": "InteractionCounter",
      "interactionType": "https://schema.org/ViewAction",
      "userInteractionCount": {{ view_count }}
    }
  ],
  "keywords": "{% for tag in prompt.tags.all %}{{ tag.name }}{% if not forloop.last %}, {% endif %}{% endfor %}"
}
</script>
```

### XML Sitemap

**To be implemented:**

```python
# sitemaps.py
from django.contrib.sitemaps import Sitemap
from prompts.models import Prompt

class PromptSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        return Prompt.objects.filter(
            status=1,  # Published only
            is_deleted=False
        ).order_by('-created_on')
    
    def lastmod(self, obj):
        return obj.updated_on
    
    def location(self, obj):
        return f'/prompt/{obj.slug}/'
```

**URL configuration:**

```python
# urls.py
from django.contrib.sitemaps.views import sitemap
from .sitemaps import PromptSitemap

sitemaps = {
    'prompts': PromptSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}),
    # ...
]
```

### Internal Linking

**Current (existing):**
- ✅ Link to generator page (e.g., "More Midjourney prompts")
- ✅ Link to author profile
- ✅ "More from @author" section

**To be added:**
- 🔲 Tags link to tag pages
- 🔲 Related prompts section
- 🔲 Breadcrumbs with schema markup

**Breadcrumb structure:**

```
Home > Midjourney Prompts > Vintage Fashion Against Urban Backdrop
```

### Social Sharing Meta Tags

**Open Graph (Facebook/LinkedIn):**

```html
<meta property="og:title" content="{{ prompt.title }}">
<meta property="og:description" content="{{ prompt.excerpt }}">
<meta property="og:image" content="{{ prompt.display_medium_url }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta property="og:type" content="article">
```

**Twitter Card:**

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ prompt.title }}">
<meta name="twitter:description" content="{{ prompt.excerpt }}">
<meta name="twitter:image" content="{{ prompt.display_medium_url }}">
<meta name="twitter:image:alt" content="{{ alt_text }}">
```

---

## 12. PERFORMANCE OPTIMIZATIONS

### Optimization 1: Variant Generation During User Typing

**Problem:** Users wait for thumbnail generation after clicking submit.

**Solution:** Generate variants immediately after NSFW passes, while user types.

```
BEFORE:
File drop → B2 upload → NSFW → User types → Submit → Variants → Done
                                                      ^^^^^^^^
                                                      Wait here!

AFTER:
File drop → B2 upload → NSFW → Start variants (background)
                               User types → Submit → Done (variants ready!)
```

**Time saved:** ~2-4 seconds

### Optimization 2: Deferred File Renaming

**Problem:** SEO file renaming adds 3-6 seconds to processing time.

**Solution:** Rename files in separate background task after user sees "ready" modal.

```
MAIN TASK (user waits):
AI generation → Save to DB → processing_complete = True → Modal shown
                                                          ~~~~~~~~~~~
                                                          ~5-10 seconds

DEFERRED TASK (user doesn't wait):
Rename thumb → Rename medium → Rename large → Rename webp → Update URLs
                                                             ~~~~~~~~~~~~
                                                             Runs in background
```

**Time saved:** ~3-6 seconds off perceived wait

### Optimization 3: Image Byte Caching

**Problem:** We download the image twice:
1. For NSFW moderation (on upload page)
2. For AI generation (after submit)

**Solution:** Cache image bytes after NSFW check, reuse for AI generation.

```python
# After NSFW check passes
cache_key = f"ai_image_cache:{user_id}:{md5(b2_url)}"
cache.set(cache_key, image_bytes, timeout=1800)  # 30 min TTL

# In AI generation task
cached = cache.get(cache_key)
if cached:
    image_bytes = cached
else:
    image_bytes = download_image(b2_url)  # Fallback
```

**Time saved:** ~1-2 seconds

### Optimization 4: Django-Q Worker Tuning

**Default Django-Q poll interval:** 1 second

**Tuned for faster pickup:** 0.5 seconds

```python
# settings.py
Q_CLUSTER = {
    'name': 'promptfinder',
    'workers': 2,
    'recycle': 500,
    'timeout': 60,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'poll': 0.5,  # Check for tasks every 0.5 seconds
}
```

**Time saved:** ~0.5 seconds (task picked up faster)

### Summary: Processing Time Budget

| Step | Before Optimization | After Optimization |
|------|--------------------|--------------------|
| Django-Q pickup | ~1s | ~0.5s |
| Download image | ~1-2s | ~0s (cached) |
| OpenAI Vision | ~3-8s | ~3-8s (can't optimize) |
| Save to DB | ~0.1s | ~0.1s |
| File renaming | ~3-6s | ~0s (deferred) |
| **Total** | **~8-17s** | **~4-9s** |

---

## 13. USER EXPERIENCE (UX) DESIGN

### Progress Communication

**Clear status indicators:**

| State | Visual | Message |
|-------|--------|---------|
| Uploading | Progress bar | "Uploading... 67%" |
| Checking content | Spinner | "Checking content safety..." |
| Generating variants | Spinner | "Optimizing images..." |
| Ready to submit | Green checkmark | "Ready to submit" |
| Processing AI | Loading dots | "Generating title..." |
| Complete | Success modal | "Your prompt is ready!" |
| Error | Warning modal | "Something went wrong..." |

### Never Leave User Wondering

**Every state has feedback:**

```
File dropped         → "Preview loaded"
Upload started       → Progress bar appears
Upload complete      → Checkmark appears
NSFW checking       → "Checking content safety..."
NSFW passed         → "✓ Content verified"
Variants generating → (hidden, user doesn't need to know)
Submit clicked      → Immediate redirect (no delay)
Processing page     → Loading indicators + content to browse
AI complete         → Modal notification
```

### Graceful Degradation

**If something fails, always:**

1. Show clear error message (not technical jargon)
2. Provide actionable next step
3. Never lose user's work

**Examples:**

| Failure | User-Friendly Message | Action Offered |
|---------|----------------------|----------------|
| AI timeout | "We couldn't generate title/tags automatically" | "Edit manually" or "Try again" |
| Network error | "Connection lost during upload" | "Retry" |
| NSFW rejected | "This image violates content guidelines" | "Upload different image" |
| Task stuck | "Taking longer than expected" | "Wait", "Close & check later", "Delete & retry" |

### Respect User Attention

**Why modal instead of auto-redirect:**

```
BAD UX:
User is reading "More from @author" section
    ↓
Page suddenly redirects
    ↓
User: "Wait, I was looking at something!" 😤

GOOD UX:
User is reading "More from @author" section
    ↓
Modal gently appears: "Your prompt is ready!"
    ↓
User finishes what they're doing
    ↓
User clicks "View Your Prompt" when ready 😊
```

### Mobile Considerations

**Processing page responsive design:**

```
DESKTOP:
┌─────────────────┬────────────────────┐
│                 │                    │
│  Preview Image  │  Title, Tags, etc. │
│                 │                    │
└─────────────────┴────────────────────┘

MOBILE:
┌────────────────────────────────────┐
│                                    │
│         Preview Image              │
│                                    │
├────────────────────────────────────┤
│                                    │
│        Title, Tags, etc.           │
│                                    │
└────────────────────────────────────┘
```

---

## 14. BACKGROUND TASK SYSTEM (DJANGO-Q)

### Why Django-Q?

| Option | Cost | Complexity | Heroku Compatible |
|--------|------|------------|-------------------|
| Threading | Free | Low | ⚠️ Risky (dyno restarts) |
| Celery + Redis | ~$3/mo | High | ✅ Yes |
| **Django-Q** | **Free** | **Medium** | **✅ Yes** |

**Django-Q uses your existing PostgreSQL database** as the task queue. No extra services needed.

### Installation

```bash
pip install django-q2
```

**Add to settings.py:**

```python
INSTALLED_APPS = [
    # ...
    'django_q',
]

Q_CLUSTER = {
    'name': 'promptfinder',
    'workers': 2,
    'recycle': 500,
    'timeout': 60,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
    'poll': 0.5,  # Fast task pickup
    'save_limit': 250,
    'sync': False,  # Async by default
}
```

**Run migrations:**

```bash
python manage.py migrate django_q
```

### Starting Workers

**Local development:**

```bash
python manage.py qcluster
```

**Heroku (Procfile):**

```
web: gunicorn prompts_manager.wsgi
worker: python manage.py qcluster
```

**Note:** Requires worker dyno on Heroku ($7/mo for Eco) or can run on same dyno with `release` phase.

### Creating Tasks

**Task definition:**

```python
# prompts/tasks.py
from django_q.tasks import async_task

def generate_ai_content(prompt_id):
    """
    Background task to generate AI content for a prompt.
    Called after user submits on upload page.
    """
    from prompts.models import Prompt
    from prompts.services.content_generation import ContentGenerationService
    
    prompt = Prompt.objects.get(id=prompt_id)
    
    # Check if cancelled
    if prompt.is_deleted:
        return {'status': 'cancelled'}
    
    # Generate content
    service = ContentGenerationService()
    result = service.generate_content(
        image_url=prompt.b2_image_url,
        prompt_text=prompt.content,
        ai_generator=prompt.get_ai_generator_display()
    )
    
    # Update prompt
    if result.get('success', True):
        prompt.title = result['title']
        prompt.excerpt = result['description']
        # ... apply tags, generate slug, etc.
    else:
        # Fallback mode
        prompt.title = prompt.content[:50] + "..."
        prompt.needs_seo_review = True
    
    prompt.processing_complete = True
    prompt.save()
    
    return {'status': 'success', 'title': prompt.title}
```

**Queueing a task:**

```python
# In upload_submit view
from django_q.tasks import async_task

def upload_submit(request):
    # ... create prompt ...
    
    # Queue AI generation task
    async_task(
        'prompts.tasks.generate_ai_content',
        prompt.id,
        task_name=f'ai_content_{prompt.id}'
    )
    
    return redirect('prompts:processing_page', uuid=prompt.processing_uuid)
```

### Task Chaining (for deferred file renaming)

```python
from django_q.tasks import async_task, async_chain

# After AI generation completes, queue rename task
def generate_ai_content(prompt_id):
    # ... AI generation ...
    
    prompt.processing_complete = True
    prompt.save()
    
    # Queue rename as follow-up task
    async_task(
        'prompts.tasks.rename_b2_files_for_seo',
        prompt.id
    )
    
    return {'status': 'success'}
```

### Monitoring Tasks

**Django Admin integration:**

Django-Q adds admin views for:
- Queued tasks
- Successful tasks
- Failed tasks
- Task timing/duration

Access at `/admin/django_q/`

---

## 15. POLLING SYSTEM

### How Polling Works

```javascript
// processing.js

const POLL_INTERVAL = 3000;  // 3 seconds
const MAX_POLL_TIME = 120000;  // 2 minutes
const WARNING_TIME = 60000;  // 1 minute

let pollCount = 0;
let pollStartTime = Date.now();

async function pollForCompletion(uuid) {
    try {
        const response = await fetch(`/api/prompt/status/${uuid}/`);
        const data = await response.json();
        
        pollCount++;
        
        if (data.processing_complete) {
            if (data.success) {
                showSuccessModal(data);
            } else {
                showPartialSuccessModal(data);
            }
            return;  // Stop polling
        }
        
        // Check for timeout
        const elapsed = Date.now() - pollStartTime;
        
        if (elapsed > MAX_POLL_TIME) {
            showErrorState();
            return;  // Stop polling
        }
        
        if (elapsed > WARNING_TIME) {
            showWarningState();
        }
        
        // Continue polling
        setTimeout(() => pollForCompletion(uuid), POLL_INTERVAL);
        
    } catch (error) {
        console.error('Poll error:', error);
        setTimeout(() => pollForCompletion(uuid), POLL_INTERVAL);
    }
}

// Start polling when page loads
document.addEventListener('DOMContentLoaded', () => {
    const uuid = document.querySelector('[data-processing-uuid]').dataset.processingUuid;
    pollForCompletion(uuid);
});
```

### Server Endpoint

```python
# api_views.py

@login_required
def prompt_processing_status(request, uuid):
    """
    API endpoint for polling processing status.
    Returns current state of prompt processing.
    """
    try:
        prompt = Prompt.objects.get(
            processing_uuid=uuid,
            author=request.user  # Security: only author can poll
        )
    except Prompt.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    
    if not prompt.processing_complete:
        return JsonResponse({
            'processing_complete': False,
            'elapsed_seconds': (timezone.now() - prompt.created_on).total_seconds()
        })
    
    # Processing complete
    return JsonResponse({
        'processing_complete': True,
        'success': not prompt.needs_seo_review,
        'title': prompt.title,
        'description': prompt.excerpt,
        'tags': list(prompt.tags.values_list('name', flat=True)),
        'slug': prompt.slug,
        'final_url': reverse('prompts:prompt_detail', kwargs={'slug': prompt.slug}),
        'is_draft': prompt.status == 0
    })
```

### Why Polling (Not WebSockets)?

**WebSocket pros:**
- Real-time updates (instant)
- No wasted requests

**WebSocket cons:**
- Connection limits on Heroku Eco dynos
- More complex server code
- Connection state management
- More failure modes

**Polling pros:**
- Simple to implement
- Works everywhere
- Easy to debug
- Stateless (no connections to manage)

**Polling cons:**
- Slight delay (up to 3 seconds)
- Small number of "wasted" requests

**For 5-10 second waits, polling is perfect:**
- 2-4 poll requests total
- Negligible server load
- Simple, reliable, maintainable

### Future: Upgrade to WebSockets

```
FUTURE ENHANCEMENT: WebSocket-Based Real-Time Updates
─────────────────────────────────────────────────────────────────────────

WHEN TO IMPLEMENT:
• When we upgrade to Heroku Standard dynos (more connections)
• When we have many concurrent processing users
• When we want instant updates (not 3-second delay)

TECHNOLOGY OPTIONS:
• Django Channels + Redis
• Server-Sent Events (SSE) - simpler, one-way only
• Third-party: Pusher, Ably (managed service)

COMPLEXITY:
• Channels: Medium-High (Redis required, new concepts)
• SSE: Low (HTTP-based, easier transition from polling)
• Pusher: Low (managed, but adds dependency + cost)

RECOMMENDATION:
Start with Server-Sent Events (SSE) as middle ground:
• No Redis required
• One-way updates (server → client) is all we need
• Native browser support
• Easy fallback to polling for old browsers

PRIORITY: Low (polling works fine for current scale)
```

---

## 16. FUTURE UPGRADES & IMPROVEMENTS

This section documents options we considered but deferred, so future developers know what's available.

### Upgrade: WebSockets / Server-Sent Events

**Current:** HTTP polling every 3 seconds

**Upgrade path:**
1. Server-Sent Events (simpler)
2. Django Channels + WebSockets (more powerful)

**Trigger to upgrade:** Many concurrent users processing prompts

### Upgrade: Immediate B2 Cleanup

**Current:** Cancelled files linger 5-30 days

**Upgrade:** Queue immediate deletion on cancel

**Trigger to upgrade:** Storage costs > $10/month or >10GB used

### Upgrade: Stuck Prompt Auto-Recovery

**Current:** Stuck prompts stay stuck until manual intervention

**Upgrade:** Hourly job to detect and recover stuck prompts

**Trigger to upgrade:** First report of stuck prompt from user

### Upgrade: AI Content Retry Queue

**Current:** Failed AI → fallback immediately, admin fixes manually

**Upgrade:** Retry queue with exponential backoff

**Trigger to upgrade:** AI failure rate > 5%

### Upgrade: Parallel Variant Generation

**Current:** Variants generated sequentially (thumb → medium → large → webp)

**Upgrade:** Generate all variants in parallel threads

**Trigger to upgrade:** Variant generation time > 5 seconds consistently

### Upgrade: CDN-Level File Renaming

**Current:** Copy + delete files in B2

**Upgrade:** Use Cloudflare Workers to rewrite URLs (no B2 operations)

**Trigger to upgrade:** B2 API costs become significant

### Upgrade: Pre-computed Related Prompts

**Current:** No related prompts section

**Upgrade:** Nightly job to compute related prompts based on tags/generator

**Trigger to upgrade:** SEO priority increases

---

## 17. DATABASE SCHEMA CHANGES

### New Field: processing_uuid

**Add to Prompt model:**

```python
# models.py
import uuid

class Prompt(models.Model):
    # ... existing fields ...
    
    # Phase N4: Processing page support
    processing_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="UUID for processing page URL (security)"
    )
    processing_complete = models.BooleanField(
        default=False,
        help_text="True when AI generation is complete"
    )
```

**Migration:**

```python
# Generated migration
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', 'previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='prompt',
            name='processing_uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='prompt',
            name='processing_complete',
            field=models.BooleanField(default=False),
        ),
    ]
```

### Existing Fields Used

| Field | Type | Usage in N4 |
|-------|------|-------------|
| `title` | CharField | Updated by AI task |
| `slug` | SlugField | Generated from AI title |
| `excerpt` | TextField | Updated by AI task (description) |
| `content` | TextField | User's prompt text (input to AI) |
| `status` | IntegerField | 0=draft during processing, 1=published after |
| `needs_seo_review` | BooleanField | True on AI failure |
| `is_deleted` | BooleanField | Checked by AI task (exit if True) |
| `b2_image_url` | URLField | Input to AI Vision |
| `b2_thumb_url` | URLField | Displayed on processing page |

---

## 18. API ENDPOINTS

### New Endpoints for Phase N4

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/prompt/status/<uuid>/` | GET | Poll for processing completion |
| `/prompt/processing/<uuid>/` | GET | Processing page (HTML) |

### Processing Status Endpoint

**URL:** `/api/prompt/status/<uuid>/`

**Method:** GET

**Authentication:** Required (must be prompt author)

**Response (processing):**
```json
{
    "processing_complete": false,
    "elapsed_seconds": 4.5
}
```

**Response (success):**
```json
{
    "processing_complete": true,
    "success": true,
    "title": "Vintage Fashion Against Urban Backdrop",
    "description": "This captivating image features...",
    "tags": ["Photography", "Women", "Fashion Models", "Urban", "Vintage"],
    "slug": "vintage-fashion-against-urban-backdrop",
    "final_url": "/prompt/vintage-fashion-against-urban-backdrop/",
    "is_draft": false
}
```

**Response (partial success / fallback):**
```json
{
    "processing_complete": true,
    "success": false,
    "title": "a cinematic vertical frame of a stylish young...",
    "description": "",
    "tags": [],
    "slug": "a-cinematic-vertical-frame-of-a-stylish-young",
    "final_url": "/prompt/a-cinematic-vertical-frame-of-a-stylish-young/",
    "is_draft": true,
    "needs_review": true
}
```

### Existing Endpoints (Unchanged)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload/b2/presign/` | POST | Get presigned URL for B2 upload |
| `/api/upload/b2/complete/` | POST | Confirm upload complete |
| `/api/upload/b2/moderate/` | POST | Run NSFW check |
| `/api/upload/b2/variants/` | POST | Generate image variants |
| `/upload/submit/` | POST | Create prompt, start processing |

---

## 19. FILE STRUCTURE

### New Files to Create

```
prompts/
├── tasks.py                          # NEW: Django-Q tasks
│   ├── generate_ai_content()
│   └── rename_b2_files_for_seo()
├── templates/prompts/
│   └── processing.html               # NEW: Processing page template
└── sitemaps.py                       # NEW: XML sitemap

static/
└── js/
    └── processing.js                 # NEW: Polling logic
```

### Files to Modify

```
prompts/
├── models.py                         # Add processing_uuid, processing_complete
├── views/
│   ├── upload_views.py               # Modify upload_submit
│   └── api_views.py                  # Add processing status endpoint
├── urls.py                           # Add new routes

prompts_manager/
├── settings.py                       # Add django_q config
└── urls.py                           # Add sitemap

templates/prompts/
└── prompt_detail.html                # Add JSON-LD schema

requirements.txt                      # Add django-q2
Procfile                              # Add worker process
```

---

## 20. IMPLEMENTATION CHECKLIST

### Phase N4a: Variant Generation After NSFW
- [ ] Modify upload-core.js to trigger variant generation after NSFW passes
- [ ] Ensure variants complete before submit is allowed
- [ ] Test: variants ready when user clicks submit

### Phase N4b: Database Changes
- [ ] Add processing_uuid field to Prompt model
- [ ] Add processing_complete field to Prompt model
- [ ] Run migration
- [ ] Test: new prompts get UUID automatically

### Phase N4c: Install Django-Q
- [ ] Add django-q2 to requirements.txt
- [ ] Configure Q_CLUSTER in settings.py
- [ ] Run django_q migrations
- [ ] Add worker to Procfile
- [ ] Test: qcluster starts without errors

### Phase N4d: Processing Page
- [ ] Create processing.html template
- [ ] Create processing page view
- [ ] Add URL route for /prompt/processing/<uuid>/
- [ ] Create processing.js with polling logic
- [ ] Test: page shows prompt content and loading states

### Phase N4e: AI Generation Task
- [ ] Create generate_ai_content task in tasks.py
- [ ] Implement fallback handling for failures
- [ ] Add is_deleted check at task start
- [ ] Test: task generates content correctly

### Phase N4f: Polling Endpoint
- [ ] Create prompt_processing_status API endpoint
- [ ] Add URL route
- [ ] Test: returns correct status during and after processing

### Phase N4g: Modal & Redirect
- [ ] Create success modal in processing.html
- [ ] Create partial success modal
- [ ] Create error states
- [ ] Test: correct modal shows based on result

### Phase N4h: Modify Upload Submit
- [ ] Change submit to create prompt with processing state
- [ ] Queue AI generation task
- [ ] Redirect to processing page
- [ ] Test: end-to-end flow works

### Phase N4i: Deferred File Renaming
- [ ] Create rename_b2_files_for_seo task
- [ ] Queue after AI generation completes
- [ ] Update prompt URLs after rename
- [ ] Test: files get renamed, URLs update

### Phase N4j: SEO Additions
- [ ] Add JSON-LD schema to prompt_detail.html
- [ ] Create sitemaps.py
- [ ] Add sitemap URL route
- [ ] Test: schema validates, sitemap accessible

### Phase N4k: Testing & Polish
- [ ] Test happy path end-to-end
- [ ] Test AI failure → fallback
- [ ] Test cancel during processing
- [ ] Test network errors
- [ ] Test mobile responsive design
- [ ] Performance test processing time

---

## 21. GLOSSARY

| Term | Definition |
|------|------------|
| **B2** | Backblaze B2 - cloud storage service where images/videos are stored |
| **CDN** | Content Delivery Network - Cloudflare serves files globally for speed |
| **Django-Q** | Background task queue library that uses PostgreSQL |
| **Fallback mode** | When AI fails, use basic content instead (user's prompt as title) |
| **NSFW** | "Not Safe For Work" - content moderation for inappropriate images |
| **Polling** | Repeatedly checking server for updates (every 3 seconds) |
| **Presigned URL** | Temporary URL that allows direct upload to B2 without Django |
| **Processing page** | Intermediate page shown while AI generates content |
| **Slug** | URL-friendly version of title (e.g., "vintage-fashion-urban") |
| **UUID** | Universally Unique Identifier - secure random ID for processing page |
| **Variant** | Different sizes of the same image (thumb, medium, large, webp) |
| **Vision API** | OpenAI's ability to analyze images using GPT-4o-mini |
| **WebSocket** | Real-time two-way communication (not used, polling instead) |
| **Worker** | Background process that executes Django-Q tasks |

---

## DOCUMENT HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | January 26, 2026 | Claude AI | Initial comprehensive documentation |

---

**END OF PHASE N4 COMPREHENSIVE REPORT**

*This document should be read in conjunction with:*
- *CLAUDE.md - Core project reference*
- *CLAUDE_PHASES.md - Phase specifications*
- *PROJECT_FILE_STRUCTURE.md - File locations*
