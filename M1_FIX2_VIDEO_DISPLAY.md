# M1-FIX2: Fix Video Display in prompt_detail.html

═══════════════════════════════════════════════════════════════
⛔ MANDATORY REQUIREMENTS - READ BEFORE STARTING
═══════════════════════════════════════════════════════════════

1. **READ FIRST:** `docs/CC_COMMUNICATION_PROTOCOL.md`
2. **USE AGENTS:** @frontend-developer and @code-review are MANDATORY
3. **RATING THRESHOLD:** All agents must rate 8.0/10 or higher
4. **WORK REJECTED** if agent ratings below 8.0/10

═══════════════════════════════════════════════════════════════

## Overview

| Field | Value |
|-------|-------|
| **Task ID** | M1-FIX2 |
| **Priority** | 🔴 HIGH (MVP Blocker) |
| **Estimated Time** | 15-20 minutes |
| **File to Modify** | `prompts/templates/prompts/prompt_detail.html` |

## Problem

Video URLs ARE being saved to the database correctly:
- `b2_video_url` = `https://media.promptfinder.net/media/videos/.../video.mp4`
- `b2_video_thumb_url` = `https://media.promptfinder.net/media/videos/.../thumb.jpg`

**BUT** the `prompt_detail.html` template shows "Media Missing" because it's NOT checking for `b2_video_url`. It only checks:
- `featured_video` (Cloudinary - legacy)
- `featured_image` (Cloudinary - legacy)

## Root Cause

The template media display logic doesn't include B2 video fields in its conditional checks.

## The Fix

Update `prompt_detail.html` to check for B2 video URL first (B2-first pattern), then fall back to Cloudinary.

### Current Logic (Broken)

The template likely has something like:
```django
{% if prompt.featured_video %}
    <video src="{{ prompt.featured_video.url }}">
{% elif prompt.featured_image %}
    <img src="{{ prompt.featured_image.url }}">
{% else %}
    <!-- Media Missing -->
{% endif %}
```

### Required Logic (Fixed)

```django
{% if prompt.b2_video_url %}
    {# B2 Video (new uploads) #}
    <video 
        src="{{ prompt.b2_video_url }}"
        poster="{{ prompt.b2_video_thumb_url }}"
        controls
        playsinline
        preload="metadata"
    >
        Your browser does not support video playback.
    </video>
{% elif prompt.featured_video %}
    {# Cloudinary Video (legacy) #}
    <video src="{{ prompt.featured_video.url }}" controls>
    </video>
{% elif prompt.b2_image_url or prompt.display_medium_url %}
    {# B2 Image (new uploads) #}
    <img src="{{ prompt.display_medium_url|default:prompt.b2_image_url }}" alt="{{ prompt.title }}">
{% elif prompt.featured_image %}
    {# Cloudinary Image (legacy) #}
    <img src="{{ prompt.featured_image.url }}" alt="{{ prompt.title }}">
{% else %}
    {# No media #}
    <div class="media-missing">
        Media Missing
    </div>
{% endif %}
```

## Step-by-Step Implementation

### Step 1: Find the media display section

Search in `prompt_detail.html` for:
- "Media Missing"
- "No Image Available"
- `featured_video`
- `featured_image`

### Step 2: Update the conditional logic

Add `b2_video_url` check BEFORE `featured_video` check:

```django
{% if prompt.b2_video_url %}
    <video 
        src="{{ prompt.b2_video_url }}"
        poster="{{ prompt.b2_video_thumb_url }}"
        controls
        playsinline
        preload="metadata"
        class="prompt-video"
    >
    </video>
{% elif prompt.featured_video %}
    ... existing Cloudinary video code ...
```

### Step 3: Also check the "is video" indicator

If there's a place showing "Image" vs "Video" media type, update it to check `b2_video_url`:

```django
{% if prompt.b2_video_url or prompt.featured_video %}
    <span>Video</span>
{% else %}
    <span>Image</span>
{% endif %}
```

## Files to Modify

| File | Changes |
|------|---------|
| `prompts/templates/prompts/prompt_detail.html` | Add B2 video URL checks to media display |

## Verification Steps

1. Restart server (if needed)
2. Navigate to the video prompt you just created
3. **VERIFY:** Video displays and plays (not "Media Missing")
4. **VERIFY:** Video thumbnail shows as poster image
5. **VERIFY:** Media type shows "Video" not "Image"

## Secondary Issue Found (Non-Blocking)

The AI suggestions endpoint is failing for videos:
```
ERROR: You uploaded an unsupported image. Please make sure your image has one of the following formats: ['png', 'jpeg', 'gif', 'webp']
```

This is expected - OpenAI Vision doesn't accept video files. The fix should use the **video thumbnail** for AI analysis instead of the video file itself. This is a separate issue for later.

---

## Agent Requirements

| Agent | Purpose |
|-------|---------|
| `@frontend-developer` | Review template changes |
| `@code-review` | Final review |

---

## Acceptance Criteria

- [ ] Video displays on prompt detail page (not "Media Missing")
- [ ] Video has playback controls
- [ ] Video thumbnail shows as poster
- [ ] Media type indicator shows "Video"
- [ ] Existing image prompts still display correctly
- [ ] Existing Cloudinary video prompts still work (legacy)

---

## Commit Message

```
fix(phase-m): Add B2 video display to prompt_detail.html (M1-FIX2)

- Add b2_video_url check before featured_video in media display
- Use b2_video_thumb_url as video poster image
- Maintains backward compatibility with Cloudinary videos
- Fixes "Media Missing" for B2 video uploads

Agent ratings: @frontend-developer X/10, @code-review X/10
```

---

## Agent Rating Table

| Agent | Rating | Notes |
|-------|--------|-------|
| @frontend-developer | /10 | |
| @code-review | /10 | |

⛔ **Work REJECTED if any rating < 8.0/10**

---

## ✅ DO / ❌ DO NOT

### ✅ DO:
- Add B2 video check FIRST (B2-first pattern)
- Keep Cloudinary fallback for legacy prompts
- Use `b2_video_thumb_url` as poster image
- Test both video AND image display

### ❌ DO NOT:
- Remove Cloudinary video/image support (legacy data)
- Change the video player styling (just make it work first)
- Try to fix the AI suggestions error (separate issue)

---

═══════════════════════════════════════════════════════════════
⛔ CRITICAL REMINDERS - READ BEFORE SUBMITTING
═══════════════════════════════════════════════════════════════

1. **B2-first pattern** - Check B2 fields before Cloudinary fields
2. **Test BOTH video and image prompts** - No regressions
3. **The video URL is already in the database** - This is purely a template fix
4. **Provide agent rating table** in response

═══════════════════════════════════════════════════════════════

**END OF SPEC**
