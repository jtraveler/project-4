# Prompt Detail Page Analysis Report

**Analysis Date:** December 18, 2025
**Template:** `prompts/templates/prompts/prompt_detail.html`
**View Function:** `prompts/views/prompt_views.py:303-561`
**Purpose:** Baseline analysis before PromptHero-inspired redesign
**Total Template Lines:** 819

---

## 1. Executive Summary

The `prompt_detail.html` template is the primary page for displaying individual AI prompts. It's a mature, feature-rich template with approximately **819 lines** combining HTML structure, inline CSS (~63 lines), and inline JavaScript (~325 lines).

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Lines | 819 |
| Inline CSS Lines | ~63 (lines 28-91) |
| Inline JS Lines | ~325 (lines 491-818) |
| Template Tags Used | 4 (static, cloudinary_tags, crispy_forms_tags, block) |
| Modals | 2 (delete confirmation, report prompt) |
| AJAX Endpoints | 2 (like toggle, report submit) |
| Context Variables | 7 |

### Complexity Assessment

- **Layout Complexity:** Medium - Bootstrap grid with 8/4 column split
- **Feature Density:** High - Multiple interactive elements
- **JavaScript Complexity:** Medium-High - 8+ distinct functions
- **Maintainability:** Medium - Inline styles/scripts increase coupling

---

## 2. Layout Structure Analysis

### Template Inheritance

```
base.html
└── prompt_detail.html
    ├── {% block extra_head %} - DNS prefetch, preloads, critical CSS
    ├── {% block content %} - Main page content
    └── {% block extras %} - JavaScript
```

### Grid Layout (Bootstrap 5)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Header Section (pt-5)                        │
│  ┌──────────────────────────────┬──────────────────────────┐   │
│  │     col-lg-8                 │      col-lg-4            │   │
│  │  • Title + Video indicator   │  • Action buttons        │   │
│  │  • Author link               │    (Comment, Edit,       │   │
│  │                              │     Delete, Like, View,  │   │
│  │                              │     Report)              │   │
│  └──────────────────────────────┴──────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                    Main Content (mt-5)                          │
│  ┌──────────────────────────────┬──────────────────────────┐   │
│  │     col-lg-8                 │      col-lg-4            │   │
│  │  • hero-image-shell          │  • Sidebar               │   │
│  │    - Video (if video)        │    - Prompt Description  │   │
│  │    - Image (if image)        │    - Prompt Content      │   │
│  │    - Placeholder (fallback)  │      + Copy button       │   │
│  │                              │    - Metadata (AI gen,   │   │
│  │                              │      date, video badge)  │   │
│  │                              │    - Tags                │   │
│  └──────────────────────────────┴──────────────────────────┘   │
│  ┌──────────────────────────────┬──────────────────────────┐   │
│  │     col-lg-8                 │      col-lg-4            │   │
│  │  • Comments Section          │  • Comment Form          │   │
│  │    - Comment list            │    (authenticated only)  │   │
│  │    - Edit/Delete buttons     │  • Login CTA             │   │
│  │      (for own comments)      │    (anonymous users)     │   │
│  └──────────────────────────────┴──────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                    Modals (Hidden)                              │
│  • deleteModal - Delete confirmation                            │
│  • reportModal - Report prompt form                             │
└─────────────────────────────────────────────────────────────────┘
```

### Responsive Behavior

- **Desktop (lg+):** 8/4 column split
- **Mobile (<lg):** Full-width stacking (single column)
- **No explicit breakpoint handling** in template - relies on Bootstrap defaults

---

## 3. Feature Inventory

### 3.1 Header Section (Lines 99-190)

| Feature | Implementation | Conditional Logic |
|---------|---------------|-------------------|
| Title Display | `{{ prompt.title }}` | Always shown |
| Video Indicator | `.media-type-indicator` with FA icon | `{% if prompt.is_video %}` |
| Author Link | Links to user profile | Always shown |
| Comment Button | Scrolls to comments | Always shown |
| Edit Button | Links to edit page | Owner only |
| Delete Button | Opens delete modal | Owner only |
| Like Button | AJAX toggle | Authenticated users |
| Like Count | Login link for anonymous | Different for auth/anon |
| View Count | Badge display | `{% if can_see_views %}` |
| Report Button | Opens report modal | Auth users, not owner |

### 3.2 Media Display (Lines 196-242)

| Media Type | Element | Attributes |
|------------|---------|------------|
| Video | `<video>` | controls, poster, preload="metadata", autoplay, loop, muted |
| Image | `<img>` | Cloudinary transform (`w_824,c_limit,f_webp,q_90`), loading="eager" |
| Placeholder | `<img>` | Static SVG, gray background |
| Missing Media | Alert + placeholder | Owner gets edit link |

### 3.3 Sidebar Content (Lines 244-300)

| Section | Content | CSS Class |
|---------|---------|-----------|
| Description | `{{ prompt.excerpt }}` or "No description" | `.sidebar-title` |
| Prompt Content | `{{ prompt.content\|safe }}` | `.prompt-content` |
| Copy Button | Clipboard API | `.copy-btn` |
| Metadata | AI generator, date, video badge | `.prompt-metadata` |
| Tags | Clickable tag badges | `.tag-badge` |

### 3.4 Comments Section (Lines 302-387)

| Feature | Implementation |
|---------|---------------|
| Comment Count | Header with count |
| Comment List | Loop with conditional approval warning |
| Author Links | Profile links for comment authors |
| Edit Button | Toggle inline edit form |
| Delete Button | Opens delete modal |
| Inline Edit Form | Hidden by default, toggled via JS |
| Comment Form | Crispy forms rendering |
| Login CTA | Shown to anonymous users |

### 3.5 Modals (Lines 390-486)

| Modal | Purpose | Key Elements |
|-------|---------|--------------|
| deleteModal | Confirm prompt/comment deletion | Dynamic title/message based on delete type |
| reportModal | Submit prompt report | Reason dropdown, comment textarea, character counter, AJAX submit |

---

## 4. CSS Analysis

### 4.1 Inline Critical CSS (Lines 28-91)

Located in `{% block extra_head %}`, the template includes ~63 lines of critical CSS:

```css
/* Key classes defined inline */
.hero-image-shell     /* Container for media - light blue bg, rounded corners */
.hero-image           /* Image styling - max 824px, rounded, shadow */
.hero-video           /* Video styling - similar to image */
.action-buttons       /* Action button container */
.sidebar-title        /* Sidebar section headers */
.media-type-indicator /* Video badge styling */
```

### 4.2 External CSS Dependencies (from style.css)

| Class | Line # | Purpose |
|-------|--------|---------|
| `.hero-title` | 391 | Title text styling |
| `.hero-meta` | 397 | Meta information styling |
| `.sidebar-card` | 415 | Card container |
| `.sidebar-title` | 424 | Section headers |
| `.prompt-metadata .fa-calendar-alt` | 431 | Calendar icon positioning |
| `.tag-badge` | 442 | Tag pill styling |
| `.tag-badge:hover` | 455 | Tag hover effect |
| `.comment-card` | 468 | Comment container |
| `.comment-form` | 474 | Form styling |
| `.action-btn` | 771 | Action button base |
| `.action-btn:hover` | 790 | Hover states |
| `.action-btn i` | 797 | Icon styling |

### 4.3 CSS Variables Used

From `static/css/style.css`:
- `--light-blue` - Background colors
- `--main-blue` - Accent colors

### 4.4 Duplicate/Redundant CSS Concerns

- `.sidebar-title` defined both inline (line 74-77) and in style.css (line 424)
- Potential conflict between inline `.hero-image-shell` and external definitions

---

## 5. JavaScript Functionality Analysis

### 5.1 Function Inventory (Lines 491-818)

| Function | Lines | Purpose | Dependencies |
|----------|-------|---------|--------------|
| `scrollToComments()` | 494-502 | Smooth scroll to comments | Native `scrollIntoView` |
| `toggleLike(button)` | 504-533 | AJAX like/unlike | fetch API, CSRF token |
| `toggleEditForm(commentId)` | 535-546 | Show/hide edit form | DOM manipulation |
| `confirmDelete(deleteUrl)` | 548-570 | Dynamic delete modal | Bootstrap Modal |
| `handleCommentSubmit(event)` | 572-584 | Form submit handler | DOM manipulation |
| `addValidationFeedback()` | 586-617 | Form validation | Custom validation |
| `showValidationMessage(element, message, type)` | 619-631 | Validation feedback | DOM manipulation |
| `copyPromptText()` | 649-674 | Copy to clipboard | Clipboard API |
| `fallbackCopyTextToClipboard(text)` | 676-694 | Clipboard fallback | execCommand |
| Report Form Handler | 696-816 | AJAX report submission | fetch API, Bootstrap Modal |

### 5.2 Event Listeners

| Event | Element | Handler |
|-------|---------|---------|
| `DOMContentLoaded` | document | Main initialization |
| `submit` | `#commentForm` | `handleCommentSubmit` + validation |
| `click` | `.tag-badge` | Tag navigation |
| `input`/`change` | `#id_comment` | Character counter |
| `submit` | `#reportForm` | AJAX submission |
| `hidden.bs.modal` | `#reportModal` | Form reset |

### 5.3 AJAX Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/prompt/<slug>/like/` | POST | Toggle like status |
| `{% url 'prompts:report_prompt' prompt.slug %}` | POST | Submit report |

### 5.4 External Dependencies

- **Bootstrap 5:** Modal, form-control, btn classes
- **Font Awesome:** Icons (fas/far fa-* classes)
- **Crispy Forms:** Comment form rendering

---

## 6. Context Variables (View Function)

### Variables Passed to Template

| Variable | Type | Purpose | Source |
|----------|------|---------|--------|
| `prompt` | Prompt | The prompt object | `get_object_or_404()` |
| `comments` | list | Filtered comment list | Filtered in view |
| `comment_count` | int | Approved comment count | Calculated |
| `comment_form` | CommentForm | Form for new comments | `CommentForm()` |
| `number_of_likes` | int | Total likes | `prompt.likes.count()` |
| `prompt_is_liked` | bool | Current user's like status | Calculated |
| `view_count` | int | Total views | `prompt.get_view_count()` |
| `can_see_views` | bool | View visibility permission | `prompt.can_see_view_count()` |

### View Function Features (Lines 303-561)

1. **SEO Redirect Handling:** 301 redirect for deleted prompts with strong matches
2. **410 Gone Handling:** For weak matches, shows category suggestions
3. **Deleted Prompt Handling:**
   - Owner → Redirect to trash
   - Staff → Redirect to admin
   - Others → "Temporarily Unavailable" page
4. **Draft Protection:** Only author can view unpublished prompts
5. **Comment Filtering:** Show approved + user's own pending
6. **Comment Auto-Approval:** Respects SiteSettings
7. **View Tracking:** Records unique views via PromptView model
8. **Cache-Control Headers:** Prevents browser caching (for back button)

---

## 7. Template Tags & Filters

### Template Tags Loaded

| Tag Library | Usage |
|-------------|-------|
| `{% load static %}` | Static file URLs |
| `{% load cloudinary_tags %}` | Cloudinary image transforms |
| `{% load crispy_forms_tags %}` | Form rendering |

### Custom Filters Used

| Filter | Location | Purpose |
|--------|----------|---------|
| `cloudinary_transform` | Image src | Apply Cloudinary transformations |
| `safe` | prompt.content | Allow HTML in content |
| `linebreaks` | comment.body | Convert newlines to `<br>` |
| `date` | prompt.created_on | Date formatting |

---

## 8. Mobile Responsiveness Assessment

### Current Implementation

- **Grid System:** Bootstrap `col-lg-8`/`col-lg-4` - stacks on mobile
- **Media Display:**
  - `max-width: 824px` for hero images
  - `max-height: 800px` prevents viewport overflow
  - `object-fit: scale-down` maintains aspect ratio
- **No explicit mobile CSS:** Relies entirely on Bootstrap breakpoints

### Potential Issues

1. **Action buttons:** May overflow on narrow viewports
2. **Long titles:** No truncation or wrapping control
3. **Comment editing:** Inline forms may be cramped on mobile
4. **Modals:** Bootstrap handles, but content may overflow
5. **Video autoplay:** May drain battery on mobile

### Missing Mobile Optimizations

- No touch-specific interactions
- No mobile-specific layouts for comments
- No lazy loading for comments (all loaded at once)

---

## 9. Redesign Considerations

### Current Pain Points

1. **Inline Code:**
   - 63 lines CSS in template (not cached separately)
   - 325 lines JS in template (not minified/cached)
   - Maintenance difficulty when styles scattered

2. **Layout Rigidity:**
   - Fixed 8/4 split regardless of content
   - Media always left, sidebar always right
   - No "media-focused" variant

3. **Feature Clustering:**
   - Action buttons clustered in header (away from content)
   - Copy button buried in sidebar
   - Tags at bottom of sidebar

4. **Performance:**
   - All comments loaded at once (no pagination)
   - No image lazy loading for related content
   - Inline JS blocks rendering

### PromptHero-Inspired Changes to Consider

| Current | PromptHero Style | Impact |
|---------|------------------|--------|
| Sidebar layout | Full-width media with overlay actions | Major restructure |
| Copy button in sidebar | Floating copy button on media | UX improvement |
| Tags at bottom | Tags prominent near title | SEO/discoverability |
| Comments inline | Collapsible/modal comments | Cleaner layout |
| Static metadata | Interactive metadata cards | Engagement |

### Migration Complexity Estimate

| Component | Complexity | Risk |
|-----------|------------|------|
| Layout restructure | High | Medium - Core functionality |
| Move CSS external | Medium | Low - No logic changes |
| Move JS external | Medium | Low - Event binding may need adjustment |
| Action button repositioning | Low | Low - HTML only |
| Comment system changes | High | Medium - Form handling |

---

## 10. Dependencies & Integrations

### External Services

| Service | Integration Point |
|---------|-------------------|
| Cloudinary | Image/video hosting, transformations |
| Font Awesome | Icons throughout |
| Bootstrap 5 | Grid, modals, forms, buttons |

### Internal Model Dependencies

| Model | Usage |
|-------|-------|
| `Prompt` | Main content object |
| `Comment` | Comments list |
| `User` | Author info, likes |
| `PromptView` | View tracking |
| `SiteSettings` | Auto-approve comments |
| `DeletedPrompt` | SEO redirect handling |

### URL Dependencies

| URL Pattern | Purpose |
|-------------|---------|
| `prompts:user_profile` | Author profile links |
| `prompts:prompt_edit` | Edit button |
| `prompts:prompt_delete` | Delete action |
| `prompts:comment_edit` | Edit comment |
| `prompts:comment_delete` | Delete comment |
| `prompts:report_prompt` | Report submission |
| `account_login` | Login redirects |

---

## 11. Complexity Metrics Summary

### Template Metrics

| Metric | Value | Assessment |
|--------|-------|------------|
| Total Lines | 819 | High - consider splitting |
| Inline CSS | 63 lines | Should externalize |
| Inline JS | 325 lines | Should externalize |
| Template Logic Blocks | ~35 | Moderate complexity |
| Conditional Displays | ~15 | Manageable |
| Loop Constructs | 3 | Appropriate |
| Modal Components | 2 | Standard |
| Form Components | 2 | Standard |

### Coupling Assessment

| Factor | Level | Notes |
|--------|-------|-------|
| View-Template | Tight | 7 context variables |
| Template-CSS | Mixed | Both inline and external |
| Template-JS | Tight | All JS inline |
| JS-Backend | Moderate | 2 AJAX endpoints |

### Maintainability Score: 6/10

**Positives:**
- Well-organized section structure
- Good use of template inheritance
- Clear naming conventions
- Comprehensive feature set

**Negatives:**
- Inline CSS/JS increases maintenance burden
- Some CSS duplicated between files
- No component separation
- Testing difficulty due to tight coupling

---

## 12. Recommendations for Redesign

### Phase 1: Preparation (Low Risk)

1. **Extract CSS to external file** (`static/css/pages/prompt-detail.css`)
2. **Extract JS to external file** (`static/js/prompt-detail.js`)
3. **Create component partials** for modals

### Phase 2: Layout Changes (Medium Risk)

1. **Restructure grid** for media-focused design
2. **Reposition action buttons** closer to media
3. **Relocate copy button** for better visibility
4. **Elevate tags** in visual hierarchy

### Phase 3: Enhancement (Higher Risk)

1. **Add comment pagination** or lazy loading
2. **Implement collapsible sections**
3. **Add related prompts section**
4. **Enhance mobile experience**

---

## Appendix A: File References

- **Template:** `prompts/templates/prompts/prompt_detail.html`
- **View:** `prompts/views/prompt_views.py` (lines 303-561)
- **CSS:** `static/css/style.css` (multiple class definitions)
- **Forms:** `prompts/forms.py` (CommentForm)
- **Models:** `prompts/models.py` (Prompt, Comment, PromptView, etc.)

---

**Report Generated:** December 18, 2025
**Analysis By:** Claude Code
**Version:** 1.0
