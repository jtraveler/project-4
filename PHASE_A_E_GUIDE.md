# Phase A-E Implementation Guide
## PromptFinder Upload Page Improvements

**Purpose:** This document provides complete context for implementing the two-step Pexels-style upload flow with AI auto-population. Paste this entire guide into your new Claude Code conversation to continue seamlessly.

---

## 🎯 Context Summary

### Where We Are
- **Phase 1 of 4** - Pre-Launch Development
- **Current Task:** Upload Page Improvements (Phase A-E)
- **Goal:** Two-step Pexels-style upload with AI-powered content analysis and SEO optimization

### What's Already Complete ✅
1. **Content Moderation System**
   - OpenAI Vision API for instant moderation
   - Text moderation (profanity + OpenAI)
   - Cost: ~$0.00255 per upload
   - Status: Fully deployed and working

2. **Admin Panel Enhancements**
   - 950px image/video previews
   - Summernote WYSIWYG editor working
   - Clean organized layout
   - Status: Complete

3. **Cloudinary Asset Cleanup**
   - Django signals auto-delete assets when prompts deleted
   - Handles images and videos
   - Status: Complete and tested

### What We're Building Now (Phase A-E)
**Two-step upload flow inspired by Pexels:**
- **Step 1:** Drag-and-drop upload screen with counter
- **Step 2:** Details form with AI auto-populated fields
- **AI Analysis:** Combined moderation + content generation + relevance scoring
- **SEO:** Automatic filename and alt-tag generation
- **Tags:** 209 tags with autocomplete, AI suggests 5, user can edit

---

## 📊 Tag Strategy (CRITICAL CONTEXT)

### Why We Expanded from 27 to 209 Tags

**Previous Approach:**
- 27 core tags (too generic)
- Limited SEO value
- Not enough variety for AI suggestions

**New Approach:**
- 209 specific tags across 19 categories
- Better SEO ("Abandoned Buildings" > "Architecture")
- Richer vocabulary for AI
- Transparent to users (no hidden mapping)

### Complete Tag List (209 Tags)

**1. People & Portraits (15 tags)**
Portraits, Men, Women, Children, Families, Couples, Groups, Close-ups, Profiles, Silhouettes, Body Parts, Hands, Eyes, Fashion Models, Senior Citizens

**2. Nature & Landscapes (18 tags)**
Mountains, Forests, Beaches, Deserts, Oceans, Lakes, Rivers, Waterfalls, Caves, Cliffs, Valleys, Meadows, Jungles, Islands, Horizons, Seascapes, Wilderness, Rolling Hills

**3. Architecture & Structures (12 tags)**
Modern Architecture, Historic Buildings, Skyscrapers, Bridges, Castles, Ruins, Urban Landscapes, Abandoned Buildings, Minimalist Architecture, Gothic Architecture, Brutalist Architecture, Cathedrals

**4. Interiors & Design (10 tags)**
Interior Design, Living Rooms, Bedrooms, Kitchens, Offices, Cafes, Restaurants, Hotels, Minimalist Interiors, Industrial Design

**5. Fashion & Beauty (9 tags)**
Fashion Photography, Street Fashion, Editorial Fashion, Makeup, Hair Styling, Jewelry, Accessories, Beauty Portraits, Magazine Covers

**6. Animals & Wildlife (12 tags)**
Wild Animals, Domestic Animals, Birds, Marine Life, Insects, Reptiles, Cats, Dogs, Horses, Exotic Animals, Animal Close-ups, Animal Behavior

**7. Action & Movement (10 tags)**
Sports, Dancing, Running, Jumping, Flying, Extreme Sports, Water Sports, Winter Sports, Action Shots, Dynamic Movement

**8. Art & Design (12 tags)**
Poster Design, Graphic Design, Typography, Illustrations, Digital Art, 3D Renders, Logos, Patterns, Textures, Collages, Mixed Media, Album Covers

**9. Sci-Fi & Fantasy (12 tags)**
Science Fiction, Space, Aliens, Robots, Cyberpunk, Futuristic Cities, Fantasy Worlds, Dragons, Magic, Spaceships, Dystopian, Post-Apocalyptic

**10. Mythology & Legends (8 tags)**
Greek Mythology, Norse Mythology, Egyptian Mythology, Mythical Creatures, Gods and Goddesses, Ancient Civilizations, Folklore, Legendary Heroes

**11. Concept Art (8 tags)**
Character Design, Environment Design, Vehicle Design, Creature Design, Prop Design, Storyboards, Visual Development, Game Art

**12. Abstract & Artistic (10 tags)**
Abstract Art, Surrealism, Geometric Patterns, Color Studies, Fractal Art, Psychedelic, Optical Illusions, Experimental, Avant-Garde, Minimalism

**13. Emotions & Expressions (10 tags)**
Joy, Sadness, Anger, Fear, Surprise, Contemplation, Serenity, Tension, Love, Melancholy

**14. Lighting & Atmosphere (12 tags)**
Golden Hour, Blue Hour, Dramatic Lighting, Soft Lighting, Neon Lights, Candlelight, Backlit, Silhouettes, High Contrast, Low Key, Atmospheric, Moody

**15. Seasons & Events (8 tags)**
Spring, Summer, Autumn, Winter, Celebrations, Festivals, Ceremonies, Weddings

**16. Holidays (6 tags)**
Christmas, Halloween, Thanksgiving, New Year, Valentine's Day, Easter

**17. Texture & Detail (8 tags)**
Close-up Details, Macro Photography, Textures, Surfaces, Materials, Patterns, Weathered, Organic Textures

**18. Magic & Wonder (6 tags)**
Magical Realism, Enchanted, Whimsical, Dreamlike, Ethereal, Mystical

**19. Luxury & Elegance (6 tags)**
Luxury Lifestyle, Elegance, Opulence, High Fashion, Fine Dining, Premium Products

**20. Humor & Playful (5 tags)**
Humorous, Playful, Quirky, Satirical, Cartoon Style

**21. Culture & History (12 tags)**
Black History, Civil Rights, Indigenous Cultures, Asian Cultures, Latin American Cultures, Middle Eastern Cultures, African Cultures, European History, Cultural Heritage, Traditional Costumes, Cultural Celebrations, Historical Events

**Total: 209 tags**

### Tag Behavior

**AI Suggestion:**
- AI analyzes image + prompt text
- Suggests 5 most relevant tags from 209 options
- User sees: "Suggested tags (you can edit or add your own)"

**User Control:**
- Can remove AI-suggested tags
- Can add from autocomplete (shows all 209 options)
- Can type custom tags (not in the 209 list)
- Max 7 tags per prompt (SEO best practice: 3-7)

**Dynamic Tag Creation (Future):**
- If AI confidence < 0.7 on all 209 tags: Can suggest 1 NEW tag
- New tag → "Pending Tags" admin queue
- Admin reviews within 2-4 days
- If approved: added to master list
- User's prompt still publishes immediately with best-match existing tags

**Silent Validation:**
- After user submits, AI validates tags match image
- If mismatch (confidence >0.8): Flag for admin review
- Prompt publishes anyway (no delay)
- Admin reviews within 2-4 days, corrects if needed
- **User never knows validation happened**

---

## 🤖 AI Vision Implementation Specs

### Cost Optimization Strategy

**Single API Call Does Everything:**
- Moderation checks (violations)
- Title generation (5-10 words)
- Description generation (50-100 words, SEO-optimized)
- Tag suggestions (5 from 209 tags)
- Relevance scoring (does prompt match image? 0-1)

**Cost:** ~$0.00255 per upload (gpt-4o-mini with "low" detail)

**Why One Call?**
- Previous approach: 3 separate calls (~$0.008 per upload)
- New approach: 1 call (50% cost savings)
- Faster (synchronous, no webhooks)
- Simpler to maintain

### Analyze Both Image AND Prompt Text

**Critical:** AI must analyze:
1. **Visual content:** What's literally in the image
2. **Prompt text:** User's description of intent, style, mood
3. **Synthesis:** Match visual + text to suggest best tags

**Example:**
- Image shows: Person in cave
- Vision alone suggests: "Nature, Landscapes, Person"
- But prompt says: "Mysterious explorer discovering ancient ruins"
- Combined analysis suggests: "Adventure, Exploration, Mystery, Caves, Ancient Civilizations"

### OpenAI Vision API Prompt Structure

```
Analyze this image and the user's prompt text: "{user_prompt_text}".

First, check for policy violations:
- Explicit nudity or sexual content
- Violence, gore, blood, graphic injuries  
- Minors or children (anyone appearing under 18 years old)
- Hate symbols or extremist content
- Satanic, occult, or demonic imagery
- Medical/graphic content (surgery, corpses, wounds, childbirth)
- Visually disturbing content (self-harm, hanging, emaciated bodies)

If violations found, return:
{
  "violations": ["list of violation types"],
  "violation_severity": "critical"
}

If clean, provide:
{
  "violations": [],
  "title": "Short, descriptive title (5-10 words)",
  "description": "SEO-optimized description (50-100 words) that describes the image and how to use this prompt",
  "suggested_tags": ["5 most relevant tags from the provided list"],
  "relevance_score": 0.85,
  "relevance_explanation": "Brief explanation of how well the prompt matches the image"
}

Important:
- Analyze BOTH the visual content AND the user's prompt text
- Suggested tags should capture: subject, style, mood, composition
- Title should be keyword-rich for SEO
- Description should be unique, valuable, and include usage tips
- Relevance score: 1.0 = perfect match, 0.0 = completely unrelated

Tag list to choose from: [provide all 209 tags as comma-separated list]
```

### Status Logic (Critical)

```python
if response["violations"]:
    # Block upload, show error
    status = "blocked"
    message = f"Content violates our guidelines: {', '.join(response['violations'])}"
    # Don't save to database
    
elif response["relevance_score"] >= 0.8:
    # High relevance - auto-publish
    status = 1  # Published
    message = "Your prompt has been created and published successfully! It is now live."
    
elif response["relevance_score"] >= 0.5:
    # Medium relevance - pending review
    status = 0  # Draft/Pending
    message = "Your upload is under review. Our team will verify the prompt matches your image within 24-48 hours."
    
else:
    # Low relevance - block with message
    status = "blocked"
    message = "Your prompt doesn't accurately describe the image. Please provide a description that matches what's shown."
    # Don't save to database
```

### Video Handling

**For videos:**
1. Upload video to Cloudinary
2. Extract middle frame using Cloudinary transformation:
   ```python
   # Get video duration from Cloudinary
   duration = video_info['duration']
   middle_second = duration / 2
   
   # Generate middle frame URL
   thumbnail_url = cloudinary.CloudinaryVideo(video_public_id).build_url(
       transformation=[
           {'start_offset': f'{middle_second}s'},
           {'fetch_format': 'jpg'},
           {'quality': 'auto'}
       ]
   )
   ```
3. Send thumbnail URL to Vision API (same as images)
4. AI analyzes the frame for tags/title/description

---

## 🔍 SEO Automation (Python, Not AI)

### Why Python Handles SEO Formatting

**Separation of Concerns:**
- AI analyzes content (what it's good at)
- Python formats for web (deterministic, cheap, reliable)

**Don't pay AI to:**
- Extract keywords from title
- Build filename strings
- Format alt tags
- Add timestamps

### Filename Generation Process

**Input from AI:**
- Title: "Cyberpunk Neon Cityscape at Night"
- AI Generator (user dropdown): "Midjourney"

**Python Processing:**
```python
import time
import re

def generate_seo_filename(title, ai_generator):
    # Remove common words
    stop_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    
    # Convert to lowercase, remove punctuation
    cleaned_title = re.sub(r'[^\w\s-]', '', title.lower())
    
    # Split into words, remove stop words
    words = [w for w in cleaned_title.split() if w not in stop_words]
    
    # Take first 2-3 meaningful words (max 30 chars combined)
    keywords = []
    char_count = 0
    for word in words:
        if char_count + len(word) <= 30:
            keywords.append(word)
            char_count += len(word) + 1  # +1 for hyphen
        if len(keywords) >= 3:
            break
    
    # Build filename
    keyword_string = '-'.join(keywords)
    ai_gen_slug = ai_generator.lower().replace(' ', '-')
    timestamp = int(time.time())
    
    filename = f"{keyword_string}-{ai_gen_slug}-prompt-{timestamp}.jpg"
    return filename

# Example:
# generate_seo_filename("Cyberpunk Neon Cityscape at Night", "Midjourney")
# Returns: "cyberpunk-neon-cityscape-midjourney-prompt-1696598400.jpg"
```

**Result:**
- Keyword-rich
- Includes AI generator (captures "midjourney prompt [topic]" searches)
- Timestamp prevents collisions
- Clean, readable URL

### Alt Tag Generation

```python
def generate_alt_tag(title, ai_generator):
    # Format: "[Title] - [AI Generator] Prompt - AI-generated image"
    alt_tag = f"{title} - {ai_generator} Prompt - AI-generated image"
    
    # Truncate if too long (max 125 characters)
    if len(alt_tag) > 125:
        max_title_length = 125 - len(f" - {ai_generator} Prompt - AI-generated image")
        truncated_title = title[:max_title_length].rsplit(' ', 1)[0]  # Don't cut mid-word
        alt_tag = f"{truncated_title}... - {ai_generator} Prompt - AI-generated image"
    
    return alt_tag

# Example:
# generate_alt_tag("Cyberpunk Neon Cityscape at Night", "Midjourney")
# Returns: "Cyberpunk Neon Cityscape at Night - Midjourney Prompt - AI-generated image"
```

### When to Apply SEO Formatting

**Timeline:**
1. User uploads image → Cloudinary (temporary, no SEO filename yet)
2. AI Vision analyzes → returns title, description, tags, relevance
3. **If clean + high relevance:**
   - Python generates SEO filename + alt tag
   - Re-upload to Cloudinary with new `public_id` (SEO filename)
   - Delete temporary upload
   - Save to database with all SEO metadata
4. **If violations or low relevance:**
   - Delete temporary upload
   - Show error, don't save

**Implementation Note:**
Cloudinary allows setting `public_id` on upload, which becomes the filename in the URL. Use the generated SEO filename as the `public_id`.

---

## 🎨 UI Specifications (Pexels-Style)

### Two-Step Flow Overview

**Step 1: Upload Screen**
- Clean, minimal design
- Centered drag-and-drop area with icon
- "Browse" button
- Upload counter at top
- Guidelines checklist
- Progress bar during upload

**Step 2: Details Form**
- Two-column layout (image left, form right)
- Large image preview (60% width)
- Form fields (40% width)
- AI pre-populated values
- Tag autocomplete
- Submit button
- Navigation-away confirmation

### Step 1: Upload Screen Layout

**Wireframe:**
```
┌─────────────────────────────────────────────────────────┐
│  PromptFinder Logo          [Search]    [Profile]       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│            Share your prompts and let the                │
│            world discover them.                          │
│                                                          │
│  Share your first 10 prompts to introduce yourself to   │
│  millions of Prompt Finders.                             │
│                                                          │
│                           (7/10)                         │
│                                                          │
│      ┌───────────────────────────────────────┐          │
│      │                                       │          │
│      │         [Image Icon]                  │          │
│      │                                       │          │
│      │    Drag and drop to upload, or       │          │
│      │                                       │          │
│      │          [Browse]                     │          │
│      │                                       │          │
│      │  (You have 7 uploads left this week) │          │
│      │                                       │          │
│      └───────────────────────────────────────┘          │
│                                                          │
│      ✓ Original content you captured                    │
│      ✓ Mindful of the rights of others                  │
│      ✓ High quality images and videos                   │
│      ✓ Excludes nudity, violence, or hate               │
│      ✓ To be downloaded and used for free               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Bootstrap Classes:**
- Container: `container`
- Drag-drop area: `border border-3 border-dashed rounded-3 p-5 text-center`
- Upload counter: `badge bg-secondary`
- Guidelines: `list-unstyled` with green checkmark icons
- Browse button: `btn btn-success btn-lg`

**File Validation (JavaScript):**
```javascript
// On file select
function validateFile(file) {
    const maxImageSize = 10 * 1024 * 1024;  // 10MB
    const maxVideoSize = 100 * 1024 * 1024;  // 100MB
    const maxVideoDuration = 20;  // seconds
    
    if (file.type.startsWith('image/')) {
        if (file.size > maxImageSize) {
            showError('Image must be under 10MB');
            return false;
        }
    } else if (file.type.startsWith('video/')) {
        if (file.size > maxVideoSize) {
            showError('Video must be under 100MB');
            return false;
        }
        // Check duration after upload (can't check before)
    } else {
        showError('Please upload an image or video');
        return false;
    }
    
    return true;
}
```

**Upload Progress:**
```javascript
// Show progress bar during upload
function uploadToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', 'your_preset');
    
    fetch('https://api.cloudinary.com/v1_1/your_cloud/auto/upload', {
        method: 'POST',
        body: formData
    }).then(response => {
        // On success, proceed to Step 2
        showDetailsForm(response.data);
    }).catch(error => {
        showError('Upload failed. Please try again.');
    });
}
```

### Step 2: Details Form Layout

**Wireframe:**
```
┌──────────────────────────────────────────────────────────────────┐
│  [< Back]                                  Make your prompts easy │
│                                            to find and be seen.   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────┐  ┌──────────────────────────────────┐   │
│  │                    │  │ Title (optional)                 │   │
│  │                    │  │ ┌────────────────────────────┐   │   │
│  │                    │  │ │ Cyberpunk Neon Cityscape   │   │   │
│  │   [Large Image     │  │ └────────────────────────────┘   │   │
│  │    Preview]        │  │                                  │   │
│  │                    │  │ Tags (optional)                  │   │
│  │    950px wide      │  │ Suggested tags (you can edit     │   │
│  │                    │  │ or add your own)                 │   │
│  │                    │  │ ┌────────────────────────────┐   │   │
│  │                    │  │ │ Cyberpunk ×  Neon ×  City ×│   │   │
│  │                    │  │ └────────────────────────────┘   │   │
│  │                    │  │                                  │   │
│  │                    │  │ Prompt Content (required)        │   │
│  │                    │  │ ┌────────────────────────────┐   │   │
│  │                    │  │ │ A futuristic cyberpunk      │   │
│  │                    │  │ │ cityscape at night...       │   │
│  │  [Delete Photo]    │  │ │                             │   │
│  │                    │  │ └────────────────────────────┘   │   │
│  │                    │  │                                  │   │
│  │                    │  │ AI Generator (required)          │   │
│  │                    │  │ ┌────────────────────────────┐   │   │
│  │                    │  │ │ Midjourney            ▼    │   │   │
│  │                    │  │ └────────────────────────────┘   │   │
│  └────────────────────┘  └──────────────────────────────────┘   │
│                                                                   │
│  (1/1)                                           [Submit]         │
└──────────────────────────────────────────────────────────────────┘
```

**Layout (Bootstrap Grid):**
```html
<div class="container-fluid">
    <div class="row">
        <!-- Left column: Image preview (60%) -->
        <div class="col-md-7">
            <img src="cloudinary_url" class="img-fluid rounded" style="max-width: 950px;">
            <button class="btn btn-outline-danger mt-3">Delete this photo</button>
        </div>
        
        <!-- Right column: Form (40%) -->
        <div class="col-md-5">
            <form id="prompt-details-form">
                <!-- Title -->
                <div class="mb-3">
                    <label class="form-label">Title <span class="text-muted">(optional)</span></label>
                    <input type="text" class="form-control" id="title" value="{{ ai_suggested_title }}">
                </div>
                
                <!-- Tags -->
                <div class="mb-3">
                    <label class="form-label">Tags <span class="text-muted">(optional)</span></label>
                    <p class="small text-muted">Suggested tags (you can edit or add your own)</p>
                    <div id="tags-container">
                        <!-- Tag pills with X buttons -->
                    </div>
                    <input type="text" class="form-control" id="tag-input" placeholder="Add tags...">
                    <div id="tag-autocomplete" class="dropdown-menu" style="display:none;">
                        <!-- Autocomplete suggestions -->
                    </div>
                </div>
                
                <!-- Prompt Content -->
                <div class="mb-3">
                    <label class="form-label">Prompt Content <span class="text-danger">*</span></label>
                    <textarea class="form-control" id="content" rows="6" required>{{ ai_suggested_description }}</textarea>
                </div>
                
                <!-- AI Generator -->
                <div class="mb-3">
                    <label class="form-label">AI Generator <span class="text-danger">*</span></label>
                    <select class="form-select" id="ai_generator" required>
                        <option value="">Select AI generator...</option>
                        <option value="midjourney">Midjourney</option>
                        <option value="dalle3">DALL-E 3</option>
                        <option value="dalle2">DALL-E 2</option>
                        <option value="stable-diffusion">Stable Diffusion</option>
                        <option value="leonardo">Leonardo AI</option>
                        <option value="flux">Flux</option>
                        <option value="firefly">Adobe Firefly</option>
                        <option value="bing">Bing Image Creator</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <button type="submit" class="btn btn-success btn-lg w-100">Submit</button>
            </form>
        </div>
    </div>
</div>
```

**Tag Autocomplete (JavaScript):**
```javascript
const ALL_TAGS = [/* all 209 tags */];

document.getElementById('tag-input').addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase();
    
    if (query.length < 2) {
        hideAutocomplete();
        return;
    }
    
    // Filter tags that start with or contain query
    const matches = ALL_TAGS.filter(tag => 
        tag.toLowerCase().includes(query)
    ).slice(0, 10);  // Show max 10
    
    showAutocomplete(matches);
});

function showAutocomplete(tags) {
    const dropdown = document.getElementById('tag-autocomplete');
    dropdown.innerHTML = tags.map(tag => 
        `<a class="dropdown-item" href="#" data-tag="${tag}">${tag}</a>`
    ).join('');
    dropdown.style.display = 'block';
}

// On tag click, add to selected tags (max 7)
document.getElementById('tag-autocomplete').addEventListener('click', function(e) {
    e.preventDefault();
    if (e.target.classList.contains('dropdown-item')) {
        const tag = e.target.dataset.tag;
        addTag(tag);
        document.getElementById('tag-input').value = '';
        hideAutocomplete();
    }
});

function addTag(tag) {
    const container = document.getElementById('tags-container');
    const currentTags = container.querySelectorAll('.tag-pill').length;
    
    if (currentTags >= 7) {
        alert('Maximum 7 tags allowed');
        return;
    }
    
    // Check if tag already added
    const existing = Array.from(container.querySelectorAll('.tag-pill'))
        .find(pill => pill.dataset.tag === tag);
    if (existing) return;
    
    // Add tag pill
    const pill = document.createElement('span');
    pill.className = 'badge bg-light text-dark me-2 mb-2 tag-pill';
    pill.dataset.tag = tag;
    pill.innerHTML = `${tag} <button type="button" class="btn-close btn-close-sm" aria-label="Remove"></button>`;
    
    pill.querySelector('.btn-close').addEventListener('click', function() {
        pill.remove();
    });
    
    container.appendChild(pill);
}
```

### Navigation-Away Modal

**Trigger:**
```javascript
let hasUnsavedChanges = false;

// Set flag when form is modified
document.getElementById('prompt-details-form').addEventListener('input', function() {
    hasUnsavedChanges = true;
});

// Prevent navigation if unsaved changes
window.addEventListener('beforeunload', function(e) {
    if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';  // Chrome requires this
    }
});
```

**Modal HTML:**
```html
<div class="modal" id="unsaved-changes-modal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-body text-center p-4">
                <p class="mb-4">You have unsubmitted uploads. Would you like to stay on the page and continue uploading?</p>
                <button type="button" class="btn btn-danger me-2" id="discard-btn">Discard</button>
                <button type="button" class="btn btn-secondary" id="stay-btn">Stay on the page</button>
            </div>
        </div>
    </div>
</div>
```

**Modal Actions:**
```javascript
document.getElementById('discard-btn').addEventListener('click', function() {
    hasUnsavedChanges = false;
    window.location.href = '/';  // Go to homepage
});

document.getElementById('stay-btn').addEventListener('click', function() {
    // Close modal, stay on page
    bootstrap.Modal.getInstance(document.getElementById('unsaved-changes-modal')).hide();
});
```

### Upload Counter Display

**At Top of Upload Screen:**
```html
<div class="text-end mb-3">
    <span class="text-muted">({{ uploads_used }}/{{ uploads_limit }})</span>
</div>
```

**Or more prominent:**
```html
<div class="alert alert-info" role="alert">
    You have <strong>{{ uploads_remaining }}</strong> uploads left this week.
</div>
```

**When approaching limit (2 left):**
```html
<div class="alert alert-warning" role="alert">
    ⚠️ Only <strong>2</strong> uploads remaining this week! Upgrade to Premium for unlimited uploads.
    <a href="/pricing" class="alert-link">Learn more</a>
</div>
```

**When limit reached:**
```html
<div class="alert alert-danger" role="alert">
    You've reached your weekly upload limit (10). 
    <a href="/pricing" class="btn btn-success btn-sm ms-2">Upgrade to Premium</a>
</div>
<!-- Disable upload form -->
```

---

## 📋 Phase A-E Breakdown

### Phase A: Tag Infrastructure (2 hours)

**Goal:** Create 209 tags in database, manageable via admin

**Tasks:**
1. Create Django migration to add 209 tags
2. Organize tags by category (use tag slugs + category field)
3. Add category field to Tag model (if doesn't exist)
4. Make tags fully manageable in Django admin
5. Test queries work properly

**Migration Example:**
```python
from django.db import migrations

def create_tags(apps, schema_editor):
    Tag = apps.get_model('taggit', 'Tag')
    
    tags_by_category = {
        'people-portraits': [
            'Portraits', 'Men', 'Women', 'Children', # etc...
        ],
        'nature-landscapes': [
            'Mountains', 'Forests', 'Beaches', # etc...
        ],
        # ... all 19 categories
    }
    
    for category, tag_names in tags_by_category.items():
        for tag_name in tag_names:
            Tag.objects.get_or_create(
                name=tag_name,
                defaults={'category': category}
            )

class Migration(migrations.Migration):
    dependencies = [
        ('prompts', '0021_replace_rekognition_with_openai_vision'),
    ]
    
    operations = [
        migrations.RunPython(create_tags),
    ]
```

**Admin Enhancement:**
```python
# prompts/admin.py
from taggit.models import Tag

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'prompt_count']
    list_filter = ['category']
    search_fields = ['name', 'slug']
    ordering = ['category', 'name']
    
    def prompt_count(self, obj):
        return obj.taggit_taggeditem_items.count()
    prompt_count.short_description = 'Used in prompts'
```

**Deliverable:**
- Migration file created
- All 209 tags in database
- Category field added
- Admin interface enhanced
- Tags queryable by category

---

### Phase B: AI Service - Combined Analysis (4-6 hours)

**Goal:** Build service that handles moderation + content generation + relevance scoring in one call

**Tasks:**
1. Create `VisionModerationService` class (or rename existing)
2. Update to handle combined analysis
3. Python generates SEO filenames + alt tags
4. Implement status logic (publish/pending/block)
5. Handle videos (extract middle frame)
6. Unit tests with sample images

**Service Structure:**
```python
# prompts/services/vision_moderation.py

class VisionModerationService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.all_tags = list(Tag.objects.values_list('name', flat=True))
    
    def analyze_upload(self, image_url, prompt_text, ai_generator):
        """
        Analyze image + prompt text in one API call.
        Returns dict with: violations, title, description, tags, relevance_score
        """
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": self._build_prompt(prompt_text)},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}
                ]
            }],
            max_tokens=500
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Generate SEO assets in Python
        if not result.get('violations'):
            result['seo_filename'] = self._generate_filename(
                result['title'], ai_generator
            )
            result['alt_tag'] = self._generate_alt_tag(
                result['title'], ai_generator
            )
        
        return result
    
    def _build_prompt(self, user_prompt_text):
        """Build the AI prompt with all 209 tags"""
        return f"""
        Analyze this image and the user's prompt text: "{user_prompt_text}".
        
        First, check for policy violations:
        - Explicit nudity or sexual content
        - Violence, gore, blood, graphic injuries
        - Minors or children (anyone appearing under 18)
        - Hate symbols or extremist content
        - Satanic, occult, or demonic imagery
        - Medical/graphic content (surgery, corpses, wounds)
        - Visually disturbing content (self-harm, hanging)
        
        If violations found, return:
        {{
          "violations": ["list of violation types"],
          "violation_severity": "critical"
        }}
        
        If clean, provide:
        {{
          "violations": [],
          "title": "Short, descriptive title (5-10 words)",
          "description": "SEO-optimized description (50-100 words)",
          "suggested_tags": ["5 most relevant tags"],
          "relevance_score": 0.85,
          "relevance_explanation": "Brief explanation"
        }}
        
        Analyze BOTH visual content AND prompt text.
        Tag options: {', '.join(self.all_tags)}
        """
    
    def _generate_filename(self, title, ai_generator):
        """Generate SEO-optimized filename with timestamp"""
        import time
        import re
        
        stop_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        cleaned = re.sub(r'[^\w\s-]', '', title.lower())
        words = [w for w in cleaned.split() if w not in stop_words]
        
        keywords = []
        char_count = 0
        for word in words:
            if char_count + len(word) <= 30 and len(keywords) < 3:
                keywords.append(word)
                char_count += len(word) + 1
        
        keyword_string = '-'.join(keywords) if keywords else 'prompt'
        ai_gen_slug = ai_generator.lower().replace(' ', '-')
        timestamp = int(time.time())
        
        return f"{keyword_string}-{ai_gen_slug}-prompt-{timestamp}.jpg"
    
    def _generate_alt_tag(self, title, ai_generator):
        """Generate alt tag (max 125 chars)"""
        alt_tag = f"{title} - {ai_generator} Prompt - AI-generated image"
        
        if len(alt_tag) > 125:
            max_title_len = 125 - len(f" - {ai_generator} Prompt - AI-generated image")
            truncated = title[:max_title_len].rsplit(' ', 1)[0]
            alt_tag = f"{truncated}... - {ai_generator} Prompt - AI-generated image"
        
        return alt_tag
    
    def extract_video_middle_frame(self, video_public_id):
        """Get middle frame URL from video"""
        # Implementation using Cloudinary transformations
        pass
```

**Orchestrator Update:**
```python
# prompts/services/orchestrator.py

def moderate_prompt(prompt_instance):
    """Main moderation function"""
    vision_service = VisionModerationService()
    
    # Get image URL (or video middle frame)
    if prompt_instance.featured_video:
        image_url = vision_service.extract_video_middle_frame(
            prompt_instance.featured_video.public_id
        )
    else:
        image_url = prompt_instance.featured_image.url
    
    # Analyze
    result = vision_service.analyze_upload(
        image_url=image_url,
        prompt_text=prompt_instance.content,
        ai_generator=prompt_instance.ai_generator
    )
    
    # Determine status
    if result['violations']:
        return {
            'status': 'blocked',
            'message': f"Content violates guidelines: {', '.join(result['violations'])}"
        }
    
    elif result['relevance_score'] >= 0.8:
        return {
            'status': 1,  # Published
            'message': 'Your prompt has been created and published successfully!',
            'ai_data': result
        }
    
    elif result['relevance_score'] >= 0.5:
        return {
            'status': 0,  # Pending
            'message': 'Your upload is under review. We will verify within 24-48 hours.',
            'ai_data': result
        }
    
    else:
        return {
            'status': 'blocked',
            'message': "Your prompt doesn't match the image. Please provide accurate description."
        }
```

**Deliverable:**
- Combined AI service working
- SEO filename/alt-tag generation in Python
- Status logic implemented
- Video middle frame extraction
- Unit tests passing

---

### Phase C: Upload UI - Step 1 (3-4 hours)

**Goal:** Build Pexels-style drag-and-drop upload screen

**Tasks:**
1. Create new upload template (or update existing)
2. Drag-and-drop area with styling
3. Upload counter display (dynamically from user's data)
4. File validation (size, type)
5. Progress bar during upload
6. Handle Cloudinary upload response
7. Transition to Step 2 on success

**Template Structure:**
```html
<!-- templates/prompts/upload_step1.html -->
{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <div class="text-center mb-5">
        <h1>Share your prompts and let the world discover them.</h1>
        <p class="text-muted">
            Share your first 10 prompts to introduce yourself to millions of Prompt Finders.
        </p>
    </div>
    
    <!-- Upload counter -->
    <div class="text-end mb-3">
        <span class="badge bg-secondary">({{ user.uploads_this_week }}/{{ user.weekly_limit }})</span>
    </div>
    
    <!-- Drag-drop area -->
    <div id="drop-zone" class="border border-3 border-dashed rounded-3 p-5 text-center mb-4" 
         style="min-height: 400px;">
        <div class="my-5">
            <!-- Icon -->
            <svg width="80" height="80" class="mb-3"><!-- Upload icon SVG --></svg>
            
            <h3>Drag and drop to upload, or</h3>
            <button type="button" class="btn btn-success btn-lg mt-3" id="browse-btn">Browse</button>
            <input type="file" id="file-input" accept="image/*,video/*" style="display:none;">
            
            <p class="text-muted mt-3">
                (You have <strong>{{ uploads_remaining }}</strong> uploads left this week)
            </p>
        </div>
    </div>
    
    <!-- Guidelines -->
    <div class="row justify-content-center">
        <div class="col-md-8">
            <ul class="list-unstyled">
                <li class="mb-2">✓ Original content you captured</li>
                <li class="mb-2">✓ Mindful of the rights of others</li>
                <li class="mb-2">✓ High quality images and videos</li>
                <li class="mb-2">✓ Excludes nudity, violence, or hate</li>
                <li class="mb-2">✓ To be downloaded and used for free</li>
            </ul>
        </div>
    </div>
    
    <!-- Progress bar (hidden initially) -->
    <div id="upload-progress" class="mt-4" style="display:none;">
        <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%"></div>
        </div>
        <p class="text-center mt-2">Uploading... <span id="progress-percent">0%</span></p>
    </div>
</div>

<script>
// Drag-and-drop handling
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const browseBtn = document.getElementById('browse-btn');

browseBtn.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-success');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-success');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-success');
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    handleFileUpload(file);
});

function handleFileUpload(file) {
    // Validate file
    if (!validateFile(file)) return;
    
    // Show progress
    document.getElementById('upload-progress').style.display = 'block';
    
    // Upload to Cloudinary
    uploadToCloudinary(file);
}

function validateFile(file) {
    const maxImageSize = 10 * 1024 * 1024;  // 10MB
    const maxVideoSize = 100 * 1024 * 1024;  // 100MB
    
    if (file.type.startsWith('image/')) {
        if (file.size > maxImageSize) {
            alert('Image must be under 10MB');
            return false;
        }
    } else if (file.type.startsWith('video/')) {
        if (file.size > maxVideoSize) {
            alert('Video must be under 100MB');
            return false;
        }
    } else {
        alert('Please upload an image or video');
        return false;
    }
    
    return true;
}

function uploadToCloudinary(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('upload_preset', '{{ cloudinary_preset }}');
    
    fetch('https://api.cloudinary.com/v1_1/{{ cloudinary_cloud }}/auto/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Success - proceed to Step 2
        window.location.href = `/upload/details?cloudinary_id=${data.public_id}&resource_type=${data.resource_type}`;
    })
    .catch(error => {
        alert('Upload failed. Please try again.');
        console.error(error);
    });
}
</script>
{% endblock %}
```

**View:**
```python
# prompts/views.py

@login_required
def upload_step1(request):
    """Upload screen - Step 1"""
    user = request.user
    
    # Calculate uploads remaining
    uploads_this_week = Prompt.objects.filter(
        author=user,
        created_at__gte=get_week_start()
    ).count()
    
    weekly_limit = 10  # Or get from user.profile
    uploads_remaining = weekly_limit - uploads_this_week
    
    # Check if limit reached
    if uploads_remaining <= 0 and not user.is_premium:
        messages.error(request, 'You have reached your weekly upload limit. Upgrade to Premium for unlimited uploads.')
        return redirect('pricing')
    
    context = {
        'uploads_this_week': uploads_this_week,
        'weekly_limit': weekly_limit,
        'uploads_remaining': uploads_remaining,
        'cloudinary_preset': settings.CLOUDINARY_UPLOAD_PRESET,
        'cloudinary_cloud': settings.CLOUDINARY_CLOUD_NAME,
    }
    
    return render(request, 'prompts/upload_step1.html', context)
```

**Deliverable:**
- Upload screen fully functional
- Drag-and-drop working
- File validation working
- Upload counter displaying correctly
- Cloudinary upload working
- Transitions to Step 2

---

### Phase D: Upload UI - Step 2 (4-5 hours)

**Goal:** Build details form with AI pre-population and tag autocomplete

**Tasks:**
1. Create details form template (two-column layout)
2. Large image preview (left side)
3. Form fields (right side): Title, Tags, Prompt, AI Generator
4. Tag autocomplete with 209 options
5. AI pre-population (call Vision API on page load)
6. Navigation-away modal
7. Form submission handling

**Template:**
```html
<!-- templates/prompts/upload_step2.html -->
{% extends "base.html" %}

{% block content %}
<div class="container-fluid mt-4">
    <div class="row mb-3">
        <div class="col">
            <a href="{% url 'upload_step1' %}" class="btn btn-link">← Back</a>
        </div>
        <div class="col text-end">
            <h5>Make your prompts easy to find and be seen.</h5>
            <p class="text-muted small">Add keywords that describe your prompt</p>
        </div>
    </div>
    
    <form method="post" id="prompt-details-form">
        {% csrf_token %}
        <input type="hidden" name="cloudinary_id" value="{{ cloudinary_id }}">
        <input type="hidden" name="resource_type" value="{{ resource_type }}">
        
        <div class="row">
            <!-- Left: Image Preview -->
            <div class="col-md-7">
                <img src="{{ image_url }}" class="img-fluid rounded" style="max-width: 950px;">
                <button type="button" class="btn btn-outline-danger mt-3" id="delete-btn">
                    Delete this photo
                </button>
            </div>
            
            <!-- Right: Form Fields -->
            <div class="col-md-5">
                <!-- Title -->
                <div class="mb-4">
                    <label for="title" class="form-label">
                        Title <span class="text-muted">(optional)</span>
                    </label>
                    <input type="text" class="form-control form-control-lg" 
                           id="title" name="title" value="{{ ai_title }}">
                </div>
                
                <!-- Tags -->
                <div class="mb-4">
                    <label class="form-label">
                        Tags <span class="text-muted">(optional)</span>
                    </label>
                    <p class="small text-muted mb-2">
                        Suggested tags (you can edit or add your own)
                    </p>
                    <div id="tags-container" class="mb-2">
                        {% for tag in ai_tags %}
                        <span class="badge bg-light text-dark me-2 mb-2 tag-pill" data-tag="{{ tag }}">
                            {{ tag }}
                            <button type="button" class="btn-close btn-close-sm ms-1" aria-label="Remove"></button>
                        </span>
                        {% endfor %}
                    </div>
                    <input type="text" class="form-control" id="tag-input" 
                           placeholder="Add tags..." autocomplete="off">
                    <div id="tag-autocomplete" class="list-group" style="display:none; position:absolute; z-index:1000; max-height:300px; overflow-y:auto;">
                        <!-- Autocomplete items -->
                    </div>
                    <input type="hidden" name="tags" id="tags-hidden">
                </div>
                
                <!-- Prompt Content -->
                <div class="mb-4">
                    <label for="content" class="form-label">
                        Prompt Content <span class="text-danger">*</span>
                    </label>
                    <textarea class="form-control" id="content" name="content" 
                              rows="8" required>{{ ai_description }}</textarea>
                </div>
                
                <!-- AI Generator -->
                <div class="mb-4">
                    <label for="ai_generator" class="form-label">
                        AI Generator <span class="text-danger">*</span>
                    </label>
                    <select class="form-select form-select-lg" id="ai_generator" 
                            name="ai_generator" required>
                        <option value="">Select AI generator...</option>
                        <option value="midjourney">Midjourney</option>
                        <option value="dalle3">DALL-E 3</option>
                        <option value="dalle2">DALL-E 2</option>
                        <option value="stable-diffusion">Stable Diffusion</option>
                        <option value="leonardo">Leonardo AI</option>
                        <option value="flux">Flux</option>
                        <option value="firefly">Adobe Firefly</option>
                        <option value="bing">Bing Image Creator</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <!-- Submit -->
                <div class="d-flex justify-content-between align-items-center">
                    <span class="text-muted">(1/1)</span>
                    <button type="submit" class="btn btn-success btn-lg px-5">
                        Submit
                    </button>
                </div>
            </div>
        </div>
    </form>
</div>

<!-- Navigation-away modal -->
<div class="modal fade" id="unsaved-modal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-body text-center p-5">
                <p class="mb-4">
                    You have unsubmitted uploads. Would you like to stay on the page and continue uploading?
                </p>
                <button type="button" class="btn btn-danger me-2" id="discard-btn">Discard</button>
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Stay on the page</button>
            </div>
        </div>
    </div>
</div>

<script>
const ALL_TAGS = {{ all_tags|safe }};  // Pass from backend as JSON
let hasUnsavedChanges = false;

// Track changes
document.getElementById('prompt-details-form').addEventListener('input', () => {
    hasUnsavedChanges = true;
});

// Prevent navigation
window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
    }
});

// Tag autocomplete
const tagInput = document.getElementById('tag-input');
const tagAutocomplete = document.getElementById('tag-autocomplete');

tagInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    
    if (query.length < 2) {
        tagAutocomplete.style.display = 'none';
        return;
    }
    
    const matches = ALL_TAGS.filter(tag => 
        tag.toLowerCase().includes(query)
    ).slice(0, 10);
    
    if (matches.length > 0) {
        tagAutocomplete.innerHTML = matches.map(tag => 
            `<button type="button" class="list-group-item list-group-item-action" data-tag="${tag}">${tag}</button>`
        ).join('');
        tagAutocomplete.style.display = 'block';
    } else {
        tagAutocomplete.style.display = 'none';
    }
});

// Add tag on click
tagAutocomplete.addEventListener('click', (e) => {
    if (e.target.dataset.tag) {
        addTag(e.target.dataset.tag);
        tagInput.value = '';
        tagAutocomplete.style.display = 'none';
    }
});

// Add tag function
function addTag(tagName) {
    const container = document.getElementById('tags-container');
    const currentTags = container.querySelectorAll('.tag-pill').length;
    
    if (currentTags >= 7) {
        alert('Maximum 7 tags allowed');
        return;
    }
    
    // Check duplicate
    const existing = Array.from(container.querySelectorAll('.tag-pill'))
        .find(pill => pill.dataset.tag === tagName);
    if (existing) return;
    
    // Create pill
    const pill = document.createElement('span');
    pill.className = 'badge bg-light text-dark me-2 mb-2 tag-pill';
    pill.dataset.tag = tagName;
    pill.innerHTML = `${tagName} <button type="button" class="btn-close btn-close-sm ms-1"></button>`;
    
    pill.querySelector('.btn-close').addEventListener('click', () => pill.remove());
    container.appendChild(pill);
}

// Remove tag pills
document.querySelectorAll('.tag-pill .btn-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.target.closest('.tag-pill').remove();
    });
});

// On form submit, collect tags
document.getElementById('prompt-details-form').addEventListener('submit', (e) => {
    const tags = Array.from(document.querySelectorAll('.tag-pill'))
        .map(pill => pill.dataset.tag);
    document.getElementById('tags-hidden').value = JSON.stringify(tags);
    hasUnsavedChanges = false;
});

// Delete button
document.getElementById('delete-btn').addEventListener('click', () => {
    if (confirm('Are you sure you want to delete this upload?')) {
        // Delete from Cloudinary and redirect
        fetch('/upload/delete', {
            method: 'POST',
            headers: {'X-CSRFToken': '{{ csrf_token }}'},
            body: JSON.stringify({
                cloudinary_id: '{{ cloudinary_id }}',
                resource_type: '{{ resource_type }}'
            })
        }).then(() => {
            hasUnsavedChanges = false;
            window.location.href = '/';
        });
    }
});

// Discard button in modal
document.getElementById('discard-btn').addEventListener('click', () => {
    hasUnsavedChanges = false;
    window.location.href = '/';
});
</script>
{% endblock %}
```

**View:**
```python
# prompts/views.py

@login_required
def upload_step2(request):
    """Details form - Step 2"""
    cloudinary_id = request.GET.get('cloudinary_id')
    resource_type = request.GET.get('resource_type', 'image')
    
    if not cloudinary_id:
        return redirect('upload_step1')
    
    # Get Cloudinary URL
    if resource_type == 'video':
        image_url = cloudinary.CloudinaryVideo(cloudinary_id).build_url()
    else:
        image_url = cloudinary.CloudinaryImage(cloudinary_id).build_url()
    
    # Run AI analysis
    vision_service = VisionModerationService()
    
    # For videos, extract middle frame for analysis
    if resource_type == 'video':
        analysis_url = vision_service.extract_video_middle_frame(cloudinary_id)
    else:
        analysis_url = image_url
    
    # Analyze (without prompt text yet - use empty string)
    ai_result = vision_service.analyze_upload(
        image_url=analysis_url,
        prompt_text="",  # No user prompt yet
        ai_generator=""  # Will be selected by user
    )
    
    # Check for violations
    if ai_result.get('violations'):
        messages.error(request, f"Content violates our guidelines: {', '.join(ai_result['violations'])}")
        # Delete from Cloudinary
        cloudinary.uploader.destroy(cloudinary_id, resource_type=resource_type)
        return redirect('upload_step1')
    
    # Get all tags for autocomplete
    all_tags = list(Tag.objects.values_list('name', flat=True))
    
    context = {
        'cloudinary_id': cloudinary_id,
        'resource_type': resource_type,
        'image_url': image_url,
        'ai_title': ai_result.get('title', ''),
        'ai_description': ai_result.get('description', ''),
        'ai_tags': ai_result.get('suggested_tags', []),
        'all_tags': json.dumps(all_tags),  # For JavaScript
    }
    
    return render(request, 'prompts/upload_step2.html', context)

@login_required
def upload_submit(request):
    """Handle form submission"""
    if request.method != 'POST':
        return redirect('upload_step1')
    
    cloudinary_id = request.POST.get('cloudinary_id')
    resource_type = request.POST.get('resource_type')
    title = request.POST.get('title', '')
    content = request.POST.get('content')
    ai_generator = request.POST.get('ai_generator')
    tags_json = request.POST.get('tags', '[]')
    tags = json.loads(tags_json)
    
    # Re-run AI analysis with user's prompt text
    vision_service = VisionModerationService()
    
    if resource_type == 'video':
        analysis_url = vision_service.extract_video_middle_frame(cloudinary_id)
    else:
        analysis_url = cloudinary.CloudinaryImage(cloudinary_id).build_url()
    
    ai_result = vision_service.analyze_upload(
        image_url=analysis_url,
        prompt_text=content,
        ai_generator=ai_generator
    )
    
    # Check violations again
    if ai_result.get('violations'):
        messages.error(request, "Content violates our guidelines")
        cloudinary.uploader.destroy(cloudinary_id, resource_type=resource_type)
        return redirect('upload_step1')
    
    # Check relevance score
    relevance = ai_result.get('relevance_score', 0)
    
    if relevance < 0.5:
        messages.error(request, "Your prompt doesn't match the image. Please provide an accurate description.")
        return redirect(f'/upload/details?cloudinary_id={cloudinary_id}&resource_type={resource_type}')
    
    # Create Prompt object
    prompt = Prompt(
        author=request.user,
        title=title or ai_result['title'],
        content=content,
        ai_generator=ai_generator,
        status=1 if relevance >= 0.8 else 0,  # Published or Pending
    )
    
    # Re-upload to Cloudinary with SEO filename
    seo_filename = ai_result['seo_filename']
    
    if resource_type == 'video':
        # Copy video with new public_id
        result = cloudinary.uploader.upload(
            cloudinary.CloudinaryVideo(cloudinary_id).build_url(),
            public_id=seo_filename.replace('.jpg', ''),
            resource_type='video',
            overwrite=True
        )
        prompt.featured_video = CloudinaryField().from_existing_remote_url(result['secure_url'])
        # Delete old
        cloudinary.uploader.destroy(cloudinary_id, resource_type='video')
    else:
        # Copy image with new public_id
        result = cloudinary.uploader.upload(
            cloudinary.CloudinaryImage(cloudinary_id).build_url(),
            public_id=seo_filename.replace('.jpg', ''),
            overwrite=True
        )
        prompt.featured_image = CloudinaryField().from_existing_remote_url(result['secure_url'])
        # Delete old
        cloudinary.uploader.destroy(cloudinary_id)
    
    # Save prompt
    prompt.save()
    
    # Add tags
    for tag_name in tags:
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        prompt.tags.add(tag)
    
    # Show message based on status
    if prompt.status == 1:
        messages.success(request, 'Your prompt has been created and published successfully!')
        return redirect('prompt_detail', slug=prompt.slug)
    else:
        messages.info(request, 'Your upload is under review. We will verify within 24-48 hours.')
        return redirect('dashboard')
```

**Deliverable:**
- Details form fully functional
- Image preview displaying
- AI pre-population working
- Tag autocomplete working
- Navigation-away modal working
- Form submission creates Prompt with SEO filename
- Status logic (publish/pending) working

---

## Phase D.5: Trash Bin + Orphaned File Management ✅ COMPLETE

**Total Duration:** 3 days (October 12-13, 2025)
**Commits:** 10 (5d512bc → 48725a8)
**Status:** Production-ready

### Day 1 Summary ✅ (October 12, 2025)
**Duration:** 4-5 hours
**Commits:** 4 (5d512bc → ff4aa85)

**What Was Built:**
- Soft delete implementation with `deleted_at`, `deleted_by`, `deletion_reason`
- Trash bin page (`/trash/`) with masonry grid layout
- Restore and undo functionality
- Alert system with proper positioning
- Smart redirects (referer-based routing)
- Custom managers: `objects` (active only), `all_objects` (includes deleted)

**Key Methods:**
- `prompt.soft_delete(user)` - Move to trash
- `prompt.restore()` - Restore from trash
- `prompt.hard_delete()` - Permanent delete + Cloudinary cleanup

**Challenges Overcome:**
- Grid layout complexity (masonry vs Bootstrap)
- Alert positioning (protected with HTML comments)
- CC reverting manual changes (protected critical sections)

### Day 2 Summary ✅ (October 12, 2025)
**Duration:** 4-5 hours
**Commits:** 3 (73878df → fb93ee0)

#### Commit 5: Cleanup Management Command (73878df)
**Duration:** 2-3 hours
**Agents Used:** django-expert, backend-architect

**What Was Built:**
- Django management command: `cleanup_deleted_prompts`
- Automatically deletes expired prompts:
  - Free users: 5 days retention
  - Premium users: 30 days retention
- Features:
  - `--dry-run` flag for safe testing
  - Email summaries to admins
  - Comprehensive error handling
  - Detailed logging (INFO, WARNING, ERROR)
  - Continues on individual failures
  - Statistics tracking (total, successful, failed, by tier)

**Files Created:**
- `prompts/management/commands/cleanup_deleted_prompts.py` (271 lines)
- `prompts/management/commands/README_cleanup_deleted_prompts.md`

**Files Modified:**
- `prompts_manager/settings.py` - Added ADMINS configuration

**Testing:**
- Local dry-run: ✅ Passed
- Heroku dry-run: ✅ Passed
- Execution time: ~10-30 seconds

**Key Implementation Details:**
- Uses `Prompt.all_objects` to include soft-deleted prompts
- Premium detection: `hasattr(user, 'is_premium') and user.is_premium`
- Calls existing `prompt.hard_delete()` method
- Sends email via Django's `send_mail()`
- Gracefully handles missing ADMINS configuration

#### Commit 6: Orphaned File Detection (b6510bb)
**Duration:** 2-3 hours
**Agents Used:** python-pro, backend-architect

**What Was Built:**
- Django management command: `detect_orphaned_files`
- Scans Cloudinary for files without database entries
- Features:
  - `--days N` - Scan last N days (default: 30)
  - `--all` - Scan all files
  - `--verbose` - Detailed progress (default: True)
  - `--output PATH` - Custom CSV location
  - API usage tracking and warnings
  - Rate limit protection (warns at 80%, stops at 95%)
  - CSV report generation
  - Email summaries to admins

**Files Created:**
- `prompts/management/commands/detect_orphaned_files.py` (524 lines)
- `prompts/management/commands/README_detect_orphaned_files.md` (462 lines)
- `reports/` directory with `.gitkeep`

**Files Modified:**
- `.gitignore` - Added `reports/*.csv`

**Initial Scan Results:**
- Total files: 56 (40 images, 16 videos)
- Valid files: 42 (75%)
- Orphaned files: 14 (25%)
- Total orphan size: 8.5 MB
- API calls used: 2/500 (0.4%)
- Execution time: 0.7-4.5 seconds

**Testing:**
- Local scan (1 day): ✅ Passed
- Local scan (90 days): ✅ Passed (found 14 orphans)
- Heroku scan (7 days): ✅ Passed
- CSV report: ✅ Generated correctly
- Email summary: ✅ Sent to console (development)

**Key Implementation Details:**
- Uses `cloudinary.api.resources()` with pagination
- Scans both 'image' and 'video' resource types
- Configures Cloudinary from `settings.CLOUDINARY_STORAGE`
- Efficient set-based lookups: O(1) complexity
- Extracts `public_id` from CloudinaryField safely
- Small delays (0.1s) between API calls
- Rich terminal output with emojis and formatting

**Bug Fix:**
- Initial error: "Must supply cloud_name"
- Solution: Added explicit Cloudinary configuration in `handle()` method
- Fixed by configuring from settings before making API calls

#### Commit 7: Heroku Scheduler Setup (fb93ee0)
**Duration:** 30-60 minutes
**Agents Used:** deployment-engineer

**What Was Built:**
- Comprehensive Heroku Scheduler setup guide (758 lines)
- Environment variable: `ADMIN_EMAIL` set on Heroku
- Job configurations documented:
  - Job 1: Daily cleanup at 03:00 UTC
  - Job 2: Daily detection at 04:00 UTC (7 days scan)
  - Job 3: Weekly deep scan at 05:00 UTC Sunday (90 days, optional)

**Files Created:**
- `HEROKU_SCHEDULER_SETUP.md` (758 lines)

**Files Modified:**
- Heroku config: Added `ADMIN_EMAIL=matthew.jtraveler@gmail.com` (Release v347)

**Guide Contents:**
- Installation instructions (CLI and web dashboard)
- Job configuration details with recommendations
- Cost analysis ($0/month breakdown)
- Monitoring and logs commands
- Testing procedures
- Troubleshooting section (6 common issues)
- Configuration checklist (34 items)
- Quick reference commands

**Cost Analysis:**
- Heroku Scheduler: $0/month (free tier)
- Dyno hours: ~0.48 hours/month (0.17% of allocation)
- Cloudinary API: 92-198 calls/month (well within free tier)
- Total: $0/month

**Remaining Tasks:**
- Configure actual Heroku Scheduler jobs (awaiting dashboard access)
- Test scheduled runs for 24-48 hours
- Verify email notifications work
- Monitor for any errors

### Day 3: Missing Image Detection ✅ (October 13, 2025)
**Duration:** 2 hours
**Commits:** 3 (d730b19, 27aacf0, 48725a8)

#### Commit 8: Documentation Update (d730b19)
**Duration:** 30 minutes

**What Was Updated:**
- `CLAUDE.md` - Updated with Phase D.5 completion summary
- `PHASE_A_E_GUIDE.md` - Added comprehensive Day 2 implementation details
- `PHASE_E_SPEC.md` - Created detailed Phase E specification (NEW, 256 lines)

**Documentation Changes:**
- Marked Phase D.5 as complete with all 7 commits
- Added Day 2 summary with detailed commit descriptions
- Added Phase E planning (User Profiles & Social Foundation)
- Reorganized future phases (F: Social, G: Premium, H: Admin, I: Performance)
- Updated technology stack sections
- Added lessons learned and performance metrics

#### Commit 9: Missing Image Detection (27aacf0)
**Duration:** 1-2 hours
**Agents Used:** Auto-selected by Claude Code

**What Was Built:**
- Enhanced `detect_orphaned_files` command to also detect missing images
- **Reverse check:** Prompts in database → Check if Cloudinary file exists
- **Critical UX fix** for broken images on homepage feed

**Features Added:**
- `_detect_missing_images()` method (95 lines)
- Checks both `featured_image` and `featured_video` fields
- Uses `cloudinary.api.resource()` to verify file existence (NotFound exception = missing)
- Differentiates ACTIVE vs DELETED prompts
- Flags ACTIVE prompts as critical (showing broken icons on site)
- Two new command flags:
  - `--missing-only` - Quick check for broken images (skip orphan detection)
  - `--orphans-only` - Storage cleanup without checking all prompts
- Enhanced CSV report with two sections (orphaned files + missing images)
- Enhanced email summary with missing images alert section

**Files Modified:**
- `prompts/management/commands/detect_orphaned_files.py` (+375 lines, -148 lines)

**Initial Scan Results:**
- Total prompts checked: 45
- Missing images found: 3
- Status: All 3 are ACTIVE (showing broken icons on site)
- Prompt IDs: #149, #146, #145
- All are admin-owned prompts (test uploads with manually deleted Cloudinary files)

**Testing:**
- Local scan: ✅ Passed (found 3 broken prompts)
- CSV report: ✅ Two-section format working correctly
- Email summary: ✅ Includes missing images section with action items
- Console output: ✅ Shows ACTIVE vs DELETED breakdown

**Key Implementation Details:**
- Uses `Prompt.all_objects` to check soft-deleted prompts too
- Progress indicators every 50 prompts
- 0.05s delay between Cloudinary API checks (avoid rate limits)
- Graceful `cloudinary.exceptions.NotFound` exception handling
- Continues on individual check failures (robust error handling)
- No additional API rate limit impact (uses same Cloudinary calls)
- Console highlights ACTIVE prompts in red (critical UX issue)

**Output Enhancement:**
```
🔍 Checking for prompts with missing images...
  - Prompt #149: 'Test Upload 1' by admin [ACTIVE]
  - Prompt #146: 'Test Upload 2' by admin [ACTIVE]
  - Prompt #145: 'Test Upload 3' by admin [ACTIVE]
  ⚠️  Found 3 prompts with missing images!
  🚨 3 are ACTIVE (showing broken images on site!)

Results Summary:
============================================================
🚨 CRITICAL: 3 prompts with missing images!
   ⚠️  3 are ACTIVE (showing broken images on site!)
```

#### Commit 10: Documentation Update (48725a8)
**Duration:** 30 minutes

**What Was Updated:**
- `README_detect_orphaned_files.md` - Comprehensive update (+179 lines, -37 lines)

**Documentation Changes:**
- Renamed title to "Cloudinary Asset Detection" (reflects dual functionality)
- Added "What Are Missing Images?" section (causes and impact)
- Added usage examples for `--missing-only` and `--orphans-only` flags
- Updated CSV format documentation with two-section structure
- Updated email template example with both sections
- Added "What to Do with Missing Images" troubleshooting guide:
  - **Critical:** ACTIVE prompts (immediate action required)
  - **Low Priority:** DELETED prompts (already in trash)
  - Investigation tips for common causes
  - Prevention best practices
  - Quick reference for soft-delete and hard-delete commands
- Updated Heroku Scheduler recommendations

### Phase D.5 Key Achievements:
1. ✅ Complete trash bin system with restore functionality
2. ✅ Automated cleanup preserves storage costs
3. ✅ Orphaned file detection prevents asset bloat
4. ✅ Missing image detection prevents broken images on homepage
5. ✅ Two-section reporting (orphaned files + missing images)
6. ✅ ACTIVE vs DELETED prompt differentiation
7. ✅ Zero cost automation via Heroku Scheduler
8. ✅ Professional documentation for all commands
9. ✅ Production-ready error handling
10. ✅ Email notifications to admins
11. ✅ API usage monitoring prevents rate limit issues

### Lessons Learned:
1. **Protect Critical Code:** Use HTML comments to prevent CC from reverting manual changes
2. **Test Incrementally:** Start with small scans (--days 1) before full scans
3. **Explicit Configuration:** Django management commands need explicit Cloudinary setup
4. **Documentation Is Key:** Comprehensive guides prevent future confusion
5. **Safe Defaults:** Always include --dry-run flags for destructive operations
6. **API Monitoring:** Track usage to prevent hitting rate limits
7. **Reverse Checks Matter:** Detecting both directions (orphans + missing) provides complete asset health
8. **Prioritize by Impact:** ACTIVE broken prompts need immediate action vs DELETED ones in trash
9. **Combined Reporting:** Single command for multiple checks reduces complexity and improves maintainability

### Performance Metrics:
- Cleanup command: 10-30 seconds
- Detection command (orphans, 7 days): 10-20 seconds
- Detection command (orphans, 90 days): 30-60 seconds
- Detection command (missing images): 10-30 seconds (checks 40-50 prompts)
- Initial missing image scan: Found 3 broken prompts (all ACTIVE, admin-owned)
- Monthly dyno usage: 0.17% of allocation
- API efficiency: <1% of daily limit

### Next Phase Ready:
Phase D.5 provides the foundation for:
- Premium user system (30-day retention already coded)
- User activity tracking (deletion patterns)
- Storage optimization (orphan cleanup)
- Reliable automated maintenance

---

## Phase E: User Profiles & Social Foundation 🔄 IN PLANNING

**Status:** Planning (October 2025)
**Estimated Duration:** 2-3 days (10-12 hours)
**Difficulty:** 🔥🔥 Medium
**Priority:** High - Foundation for community

### Overview
Build the social foundation by implementing user profiles, enhanced prompt details with reporting, and email preferences. This phase enables users to discover creators, follow interesting users, and control notifications.

### Why Phase E (Before Premium)?
1. **User Experience Gap:** No way to see a user's other prompts
2. **Foundation Needed:** Follow system requires profiles
3. **Notification Control:** Need preferences before increasing email volume
4. **Community First:** Build engagement before monetization
5. **Natural Progression:** From content management (D) to social features (E) to revenue (F)

### Goals:
- Users can view any creator's public profile
- Profiles display all prompts and statistics
- Users can report inappropriate content
- Users control their email preferences
- Foundation for follow system (Phase F)

### Part 1: Public User Profiles (Day 1 - 4-5 hours)

**Commits Planned:** 2-3

#### Commit 9: User Profile Model & View
**What to Build:**
- UserProfile model (or extend User)
- Profile view at `/users/<username>/`
- Profile template with responsive design
- Query optimization

**Database Model:**
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    avatar = CloudinaryField('image', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    instagram = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Profile Page Features:**
- Username and display name
- Avatar (default if not set)
- Bio
- Member since date
- Statistics:
  - Total prompts (count)
  - Total likes received (aggregate)
  - Followers (placeholder for Phase F)
  - Following (placeholder for Phase F)
- Grid of user's public prompts (masonry layout)
- Social links (if provided)
- Follow button (placeholder for Phase F)

**URL Structure:**
- `/users/<username>/` - Public profile
- `/users/<username>/prompts/` - All prompts (paginated)
- `/users/<username>/liked/` - Liked prompts (Phase F)

#### Commit 10: Profile Edit & Avatar Upload
**What to Build:**
- Profile settings page at `/settings/profile/`
- Edit form (bio, avatar, location, social links)
- Cloudinary avatar upload
- Form validation

**Features:**
- Edit bio (500 char limit with counter)
- Upload avatar (Cloudinary)
- Add location
- Add social media links
- Preview changes before saving
- Success/error messaging

### Part 2: Enhanced Prompt Detail (Day 2 - 2-3 hours)

#### Commit 11: Report Feature
**What to Build:**
- Report button on prompt detail page
- Report modal with form
- PromptReport model
- Admin notification email

**Database Model:**
```python
class PromptReport(models.Model):
    REASON_CHOICES = [
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam or Misleading'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ]

    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
```

**Report Flow:**
1. User clicks "Report" button
2. Modal appears with reason dropdown
3. Optional comment field
4. Submit sends report
5. Email notification to admins
6. Thank you confirmation
7. Admin reviews in Django Admin

#### Commit 12: Prompt Detail Enhancements
**What to Build:**
- "View Profile" link next to author name
- "More from this user" section (3-6 prompts)
- Author info card (avatar, username, stats)
- Improved layout and spacing

### Part 3: Email Preferences (Day 3 - 3-4 hours)

#### Commit 13: Email Preferences Model & Settings Page
**What to Build:**
- EmailPreferences model
- Settings page at `/settings/notifications/`
- Preference toggles
- Unsubscribe token system

**Database Model:**
```python
class EmailPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    notify_comments = models.BooleanField(default=True)
    notify_replies = models.BooleanField(default=True)
    notify_follows = models.BooleanField(default=True)
    notify_likes = models.BooleanField(default=True)
    notify_mentions = models.BooleanField(default=True)
    notify_weekly_digest = models.BooleanField(default=True)
    notify_updates = models.BooleanField(default=True)
    notify_marketing = models.BooleanField(default=False)
    unsubscribe_token = models.CharField(max_length=64, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Settings Page Features:**
- Toggle switches for each notification type
- "Unsubscribe from all" button
- Save confirmation
- Explanatory text for each option
- Mobile-responsive design

#### Commit 14: Update Notification Logic
**What to Build:**
- Update existing notification sends to check preferences
- Add unsubscribe links to all emails
- Unsubscribe handler view (`/unsubscribe/<token>/`)
- Email template updates

**Implementation:**
- Check preferences before sending any email
- Generate unique unsubscribe tokens
- Handle token-based unsubscribe
- Update email templates with footer links

### Success Criteria:
- [ ] Users can view any public profile
- [ ] Profiles show all prompts and stats
- [ ] Users can edit their own profile
- [ ] Avatar upload works (Cloudinary)
- [ ] Report button functional on prompt detail
- [ ] Admin receives report emails
- [ ] Email preferences page works
- [ ] All emails respect preferences
- [ ] Unsubscribe links work correctly
- [ ] No N+1 query issues
- [ ] Mobile-responsive
- [ ] All pages have proper error handling

### Files to Create:
- `prompts/models.py` - Add UserProfile, PromptReport, EmailPreferences
- `prompts/views.py` - Profile, settings, report views
- `prompts/forms.py` - Profile form, report form, settings form
- `prompts/urls.py` - New URL patterns
- `templates/users/profile.html`
- `templates/users/profile_edit.html`
- `templates/users/settings_notifications.html`
- `templates/prompts/report_modal.html`
- `templates/emails/` - Email templates with unsubscribe
- `prompts/admin.py` - Admin for new models
- Migration files

### Testing Checklist:
- [ ] View any user's profile
- [ ] Profile shows correct stats
- [ ] Edit own profile
- [ ] Upload avatar
- [ ] Report a prompt
- [ ] Receive report email (admin)
- [ ] Change email preferences
- [ ] Test each notification type respects preferences
- [ ] Click unsubscribe link
- [ ] Verify all forms validate correctly
- [ ] Test on mobile devices
- [ ] Check query performance (Django Debug Toolbar)

### Leads to Phase F:
- Follow button becomes functional
- Personalized feeds (need follow data)
- In-app notifications (use email preferences as model)
- User discovery features

---

### Phase F: Integration & Testing (3-4 hours)

**Goal:** Connect all pieces, test end-to-end, fix bugs

**Tasks:**
1. Test complete upload flow (Step 1 → Step 2 → Submit)
2. Test AI analysis with various images (clean, violations, low relevance)
3. Test tag autocomplete with all 209