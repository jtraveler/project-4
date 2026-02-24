# PromptFinder UI Redesign - Style Guide

**Based on:** Pexels.com + Vimeo.com Design Systems
**Created:** November 8, 2025
**Last Updated:** February 24, 2026 (v2.0 Accessibility Alignment — Session 88)
**Purpose:** Reference guide for complete UI redesign
**Project:** PromptFinder - AI Prompt Sharing Platform

---

## 📋 Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Visual Aesthetic](#visual-aesthetic)
3. [Layout & Structure](#layout--structure)
4. [Color System](#color-system)
5. [Typography](#typography)
6. [Component Library](#component-library)
7. [Interaction Patterns](#interaction-patterns)
8. [Responsive Design](#responsive-design)
9. [Spacing System](#spacing-system)
10. [Performance Optimization](#performance-optimization)
11. [Accessibility Standards](#accessibility-standards)
12. [Implementation Checklist](#implementation-checklist)

---

## 🎯 Design Philosophy

### Core Principles (Pexels + Vimeo)

**1. Content-First Minimalism**
- Images/videos are the hero - UI fades into background
- Remove all unnecessary chrome and decoration
- Let content breathe with generous whitespace

**2. Effortless Sophistication**
- Looks simple but highly refined in every detail
- Professional enough for agencies, approachable for hobbyists
- Quality over quantity in every interaction

**3. Discovery-Driven**
- Search is primary navigation method
- Visual browsing with minimal friction
- Clear categorization without overwhelming

**4. Performance Matters**
- Fast loading with progressive enhancement
- Smooth animations (60fps)
- Optimized images with lazy loading

### The One-Sentence Goal

> **"Create a sophisticated, minimalist platform where stunning AI prompts breathe freely on a clean canvas, with thoughtful interactions that feel effortless and professional."**

---

## 🎨 Visual Aesthetic

### Overall Look & Feel

**Keywords:** Clean, Modern, Spacious, Professional, Content-Focused, Breathable

**What to Avoid:**
- ❌ Cluttered interfaces with too many elements
- ❌ Aggressive colors or busy backgrounds
- ❌ Decorative elements that don't serve function
- ❌ Small, cramped layouts
- ❌ Inconsistent spacing or alignment
- ❌ Horizontal scrollbars (CRITICAL)

**What to Embrace:**
- ✅ Generous whitespace everywhere
- ✅ Content as the visual interest
- ✅ Subtle, purposeful interactions
- ✅ High contrast for accessibility
- ✅ Consistent, predictable patterns
- ✅ Box-sizing: border-box globally

---

## 📐 Layout & Structure

### Grid Systems

#### Masonry Grid (Pexels Style)
**When to use:** Homepage feed, search results, user profiles

```
┌─────────────────────────────────────────────────────┐
│  [Image - tall]   [Image - wide]    [Image - tall]  │
│                                                      │
│  [Image - wide]   [Image - tall]                    │
│                                     [Image - square] │
│  [Image - square] [Image - wide]                    │
│                   [Image - tall]    [Image - wide]  │
└─────────────────────────────────────────────────────┘
```

**Characteristics:**
- Multi-column layout (3-5 columns on desktop)
- Variable height cards based on content
- Consistent gap between items (16-24px)
- Fluid adaptation to viewport width
- No rigid rows - natural flow

**Implementation:**
- CSS Grid with `grid-template-columns: repeat(auto-fill, minmax(300px, 1fr))`
- Or JavaScript masonry library (Masonry.js, Isotope)
- Maintains aspect ratio of original images

**⚠️ CRITICAL: Prevent Horizontal Scroll**
```css
/* Apply globally to prevent overflow */
*, *::before, *::after {
  box-sizing: border-box;
}

html, body {
  overflow-x: hidden;
  max-width: 100vw;
  margin: 0;
  padding: 0;
}

.masonry-container {
  max-width: 100%;
  padding: 20px 40px;
  width: 100%;
  box-sizing: border-box;
}

/* Mobile responsive padding */
@media (max-width: 768px) {
  .masonry-container {
    padding: 20px 15px;  /* Reduced to prevent overflow */
  }
}
```

#### Fixed Grid (Vimeo Style)
**When to use:** Collections, curated content, categories

```
┌─────────────────────────────────────────────────────┐
│  [Image 16:9]  [Image 16:9]  [Image 16:9]  [Image]  │
│                                                      │
│  [Image 16:9]  [Image 16:9]  [Image 16:9]  [Image]  │
│                                                      │
│  [Image 16:9]  [Image 16:9]  [Image 16:9]  [Image]  │
└─────────────────────────────────────────────────────┘
```

**Characteristics:**
- Uniform card dimensions (maintains aspect ratio)
- Equal height rows
- Predictable, organized appearance
- Better for categorized browsing

**PromptFinder Recommendation:**
- **Primary:** Masonry grid (more visual interest, varied content)
- **Secondary:** Fixed grid for curated collections, admin views

### Page Structure Template

```
┌──────────────────────────────────────────────────────┐
│  NAVIGATION BAR (64-70px height)                     │
│  [Logo]    [Search Bar]           [Upload] [Profile] │
├──────────────────────────────────────────────────────┤
│                                                       │
│  HERO/BREADCRUMB (optional, 120-200px)              │
│  Large headline, search, or context                  │
│                                                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  FILTERS/TABS (if needed, 60-80px)                  │
│  [All] [Images] [Videos] [Filter▼] [Sort▼]         │
│                                                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  MAIN CONTENT AREA                                   │
│  (Masonry grid with generous gaps)                  │
│                                                       │
│  [card] [card] [card] [card]                        │
│  [card]        [card] [card]                        │
│         [card]        [card]                        │
│  [card] [card] [card]                               │
│                                                       │
│  (Infinite scroll or pagination)                    │
│                                                       │
├──────────────────────────────────────────────────────┤
│  FOOTER (minimal, 80-120px)                          │
│  Links, copyright, social                            │
└──────────────────────────────────────────────────────┘
```

### Container Widths

**Desktop:**
- **Max width:** 1400-1600px (wide screens)
- **Comfortable width:** 1200-1400px (standard)
- **Padding:** 24-48px on sides
- **Box-sizing:** border-box (REQUIRED)

**Tablet:**
- **Full width** with 16-24px padding
- **Box-sizing:** border-box

**Mobile:**
- **Full width** with 16px padding
- **Box-sizing:** border-box

**Rule:** Content should flow to viewport edges (no rigid containers that create tunnels)

---

## 🎨 Color System

### Primary Palette

#### Brand Colors (Neutral Gray Accent - CURRENT)

**Option Selected: Neutral Gray (Professional, Content-Focused)**
```css
--accent-color: var(--gray-800);            /* #262626 - Dark gray */
--accent-color-hover: var(--gray-900);      /* #171717 - Darker on hover */
--accent-color-light: rgba(38, 38, 38, 0.1); /* Gray background tint */

/* Bright green for visual elements (backgrounds, borders, icons on dark) */
--accent-color-primary: rgb(73, 242, 100);  /* High visibility, excellent contrast */

/* Darker green for text/icons on light backgrounds (WCAG AA compliant) */
--accent-color-for-text-icons: #16ba31;     /* Better readability on white */
```

**Rationale:** Content-first approach - neutral UI lets prompts be the hero

#### Neutral Colors (Foundation)

```css
/* Whites & Light Grays */
--white: #FFFFFF;
--gray-50: #FAFAFA;   /* Page backgrounds */
--gray-100: #F5F5F5;  /* Card backgrounds, subtle sections */
--gray-200: #EBEBEB;  /* Borders, dividers */

/* Medium Grays */
--gray-300: #D4D4D4;  /* Disabled states, placeholders */
--gray-400: #A3A3A3;  /* Secondary text, icons */
--gray-500: #737373;  /* Body text, less important */
--gray-600: #525252;  /* Secondary headings */

/* Dark Grays & Black */
--gray-700: #404040;  /* Primary body text */
--gray-800: #262626;  /* Headings, emphasis */
--gray-900: #171717;  /* High contrast text */
--black: #000000;     /* Rare, only for critical emphasis */
```

#### Semantic Colors

```css
/* Success */
--success: #10B981;       /* Green - positive actions */
--success-light: #D1FAE5; /* Backgrounds */

/* Error */
--error: #EF4444;         /* Red - errors, warnings */
--error-light: #FEE2E2;   /* Backgrounds */

/* Warning */
--warning: #F59E0B;       /* Orange - cautions */
--warning-light: #FEF3C7; /* Backgrounds */

/* Info - UPDATED FOR ACCESSIBILITY */
--info: #1d4ed8;          /* Darker blue - WCAG AA compliant (4.5:1 contrast) */
--info-light: #DBEAFE;    /* Backgrounds */
```

#### Notification/Alert Colors (Flash Messages)

These colors are used for Django flash messages and alert banners throughout the application.

| Message Type | Django Tag | Background | Border | Text Color | Use Case |
|--------------|------------|------------|--------|------------|----------|
| **Success** | `success` | `#d1e7dd` | `#badbcc` | `#0f5132` | Published successfully, action completed |
| **Info** | `info` | `#cff4fc` | `#b6effb` | `#055160` | Informational notices, pending review |
| **Warning** | `warning` | `#fff3cd` | `#ffeaa7` | `#856404` | Draft mode, awaiting approval, cautions |
| **Error** | `error`/`danger` | `#fee2e2` | `#fca5a5` | `#991b1b` | Validation errors, content violations |

**CSS Variables (add to styles.css):**
```css
/* Notification/Alert System */
--alert-success-bg: #d1e7dd;
--alert-success-border: #badbcc;
--alert-success-text: #0f5132;

--alert-info-bg: #cff4fc;
--alert-info-border: #b6effb;
--alert-info-text: #055160;

--alert-warning-bg: #fff3cd;
--alert-warning-border: #ffeaa7;
--alert-warning-text: #856404;

--alert-error-bg: #fee2e2;
--alert-error-border: #fca5a5;
--alert-error-text: #991b1b;
```

**Usage in Templates:**
```html
<div class="alert alert-{{ message.tags }}"
     style="background-color: var(--alert-{{ message.tags }}-bg);
            border-color: var(--alert-{{ message.tags }}-border);
            color: var(--alert-{{ message.tags }}-text);">
    {{ message }}
</div>
```

**Note:** Django uses `error` tag but Bootstrap uses `danger` class. Handle both in templates.

### Color Usage Rules

**90% Neutral (Gray Scale)**
- Page backgrounds: `--gray-50` or `--white`
- Card backgrounds: `--white`
- Text: `--gray-700` (body), `--gray-800` (headings)
- Borders: `--gray-200`

**8% Content (Images/Videos)**
- Let user-uploaded content provide color
- Don't compete with content

**2% Brand Accent**
- Primary buttons: `--accent-color` (gray-800)
- Links: `--accent-color-for-text-icons` (green)
- Active states: `--accent-color-primary` (bright green)
- Highlights: `--accent-color-light`

**Contrast Requirements (WCAG AA):**
- ✅ Text on white: Minimum 4.5:1 ratio
- ✅ Headings: Minimum 3:1 ratio
- ✅ Interactive elements: Minimum 3:1 ratio
- ✅ Media filter tabs: `#1d4ed8` (was `#3b82f6` - fixed for accessibility)
- Use tools: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- ⛔ **Hard rule:** Text on white/light backgrounds MUST use `--gray-500` (#737373) or darker
- ❌ **NEVER** use `--gray-400` (#A3A3A3) for text — fails WCAG AA (2.7:1 ratio)
- ✅ Decorative elements (borders, icons with labels) are exempt from this rule

---

## ✍️ Typography

### Font Stack

**Current Implementation: Google Fonts + System Stack**

```css
/* Logo Font */
--font-logo: 'Pattaya', 'Roboto', system-ui, sans-serif;

/* Headings & Navigation */
font-family: 'Roboto', -apple-system, BlinkMacSystemFont,
             'Segoe UI', system-ui, sans-serif;

/* Body Text */
font-family: 'Open Sans', -apple-system, BlinkMacSystemFont,
             'Segoe UI', system-ui, sans-serif;
```

**Performance Optimization (Nov 12, 2025):**
```html
<!-- Reduced font weights from 10 to 4 variants for faster loading -->
<link href="https://fonts.googleapis.com/css2?family=Pattaya&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
```

**Font Weights Used:**
- 300 (Light) - Rarely used
- 400 (Regular) - Body text
- 500 (Medium) - Emphasis, buttons
- 700 (Bold) - Headings

**Removed Weights (Performance):**
- ❌ 900 (Black) - Not used
- ❌ Italic variants - Not used

### Type Scale

```css
/* Display / Hero */
--text-6xl: 60px;   /* Large hero headlines (rare) */
--text-5xl: 48px;   /* Hero headlines */
--text-4xl: 36px;   /* Page titles */

/* Headings */
--text-3xl: 30px;   /* H1 - Main headings */
--text-2xl: 24px;   /* H2 - Section headings */
--text-xl: 20px;    /* H3 - Subsection headings */
--text-lg: 18px;    /* H4 - Small headings */

/* Body */
--text-base: 16px;  /* Body text (PRIMARY) */
--text-sm: 14px;    /* Secondary text, captions */
--text-xs: 12px;    /* Labels, metadata, fine print */
```

### Font Weights

```css
--font-light: 300;    /* Light emphasis */
--font-normal: 400;   /* Body text (PRIMARY) */
--font-medium: 500;   /* Emphasis, buttons, labels */
--font-semibold: 600; /* Headings (not loaded, use 500 or 700) */
--font-bold: 700;     /* Headings, strong emphasis */
```

### Line Heights

```css
--leading-tight: 1.25;   /* Headings, large text */
--leading-normal: 1.5;   /* Body text (PRIMARY) */
--leading-relaxed: 1.75; /* Long-form content */
```

### Typography Guidelines

**Headings:**
- Use semantic HTML (`<h1>`, `<h2>`, etc.)
- One `<h1>` per page
- Don't skip heading levels
- Font weight: 500 (medium) or 700 (bold)
- Color: `--gray-800` or `--gray-900`
- Line height: `--leading-tight`

**Body Text:**
- Font size: 16px (never smaller than 14px)
- Font weight: 400 (normal)
- Color: `--gray-700`
- Line height: 1.5-1.6
- Max width: 65-75 characters (optimal readability)

**Links:**
- Color: `--accent-color-for-text-icons` (green)
- Hover: Underline or darken 10%
- Visited: Same as default (don't change)
- Focus: Clear outline for keyboard navigation

**Labels/Metadata:**
- Font size: 12-14px
- Font weight: 500 (medium)
- Color: `--gray-500` or `--gray-600`
- Letter spacing: +0.5px (optional, aids readability)
- Text transform: None (avoid all-caps except sparingly)

---

## 🧩 Component Library

### Navigation Bar

**Desktop Version:**

```
┌────────────────────────────────────────────────────────────┐
│                                                             │
│  [Logo]         [Search Bar (500px wide)]     [Upload]    │
│                                                [Profile ▼]  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**Specifications:**
- Height: 70px (desktop), 64px (mobile)
- Background: `--white` with 1px border-bottom
- Fixed/sticky on scroll (remains visible)
- Z-index: 1000 (navbar), 2000 (dropdowns), 999 (mobile menu)
- Border: 1px solid `--gray-200`
- Padding: 0 `--space-4` (with box-sizing: border-box)

**Components:**
1. **Logo**
   - Font: Pattaya (400 weight)
   - Size: 28px (desktop), 24px (mobile)
   - Color: `--black`
   - Letter-spacing: -0.5px
   - Right margin: 25px (desktop), 15px (mobile)

2. **Search Bar**
   - Width: Flexible (flex: 1 1 auto, min-width: 0)
   - Height: 48px
   - Background: `--gray-100`
   - Border: 1px solid transparent
   - Border radius: 12px (--radius-standard)
   - Focus: Border color `#767676` (WCAG AA compliant)

3. **Icon Buttons**
   - Size: 40x40px
   - **Border radius: 50% (perfect circle)** ← UPDATED
   - Background: transparent
   - Hover background: `--gray-100`
   - Color: `--gray-700`
   - Icon size: 20px

**Mobile Version:**

```
┌──────────────────────────────┐
│  [☰]  [Logo]    [🔔] [Upload] │
├──────────────────────────────┤
│  [Mobile Menu - Overlay]     │
│  (Fixed position overlay)    │
└──────────────────────────────┘
```

**Mobile Menu Specifications:**
```css
.pexels-mobile-menu {
  position: fixed;
  top: 64px;  /* Below navbar */
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--white);
  z-index: 999;  /* Below navbar (1000) */

  /* Slide animation */
  opacity: 0;
  visibility: hidden;
  transform: translateY(-20px);
  transition: opacity 0.3s ease, visibility 0.3s ease, transform 0.3s ease;
}

.pexels-mobile-menu.show {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

/* Animated top border - CRITICAL IMPLEMENTATION */
.pexels-mobile-menu::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--gray-200);
  opacity: 0;
  transition: opacity 0.5s ease 0s;  /* Instant fade-out when closing */
}

.pexels-mobile-menu.show::before {
  opacity: 1;
  transition: opacity 0.3s ease 0.5s;  /* 0.5s delay, then 0.3s fade-in */
}
```

**Why Animated Border:**
- Prevents visual overlap with navbar (z-index issue)
- Creates smooth, delayed appearance
- Fades out instantly when closing
- Professional, polished interaction

---

### Content Cards

**Card Structure (Prompt Card):**

```
┌──────────────────────────┐
│                          │
│  [Featured Image]        │ ← Aspect ratio: Natural or 3:4 / 4:3
│  (hover: overlay)        │
│                          │
├──────────────────────────┤
│  Prompt Title            │ ← 1-2 lines, truncate
│  by @username            │ ← Small, gray
│  ♡ 24  💬 5  👁 120     │ ← Stats (subtle)
└──────────────────────────┘
```

**Card Styles:**
```css
.prompt-card {
  background: var(--white);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.prompt-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.2);
}

.prompt-card img {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}

/* Overlay on hover */
.prompt-card-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    transparent 90%,
    rgba(0,0,0,0.5) 100%
  );
  opacity: 1;
  transition: opacity 0.3s ease;
}
```

---

### Buttons

**Primary Button:**
```css
.btn-primary {
  background: var(--accent-color);  /* gray-800 */
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover {
  background: var(--accent-color-hover);  /* gray-900 */
}
```

**Icon Buttons:**
```css
.pexels-icon-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;  /* ← UPDATED: Perfect circle (was var(--radius-md)) */
  color: var(--gray-700);
  cursor: pointer;
  transition: all var(--transition-base);
  border: none;
  background: transparent;
  font-size: 20px;
}

.pexels-icon-btn:hover {
  background: var(--gray-100);
  color: var(--gray-900);
}
```

**Button Sizes:**
- **Small**: padding 8px 16px, font-size 14px
- **Medium**: padding 12px 24px, font-size 16px (DEFAULT)
- **Large**: padding 16px 32px, font-size 18px

**Touch Targets (Mobile):**
- Minimum: 44x44px (WCAG AAA compliance)
- Spacing between: 8px minimum

---

### Forms & Inputs

**Text Input:**
```css
.input-text {
  width: 100%;
  height: 48px;
  padding: 12px 16px;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  font-size: 16px;
  color: var(--gray-800);
  background: var(--white);
  transition: border-color 0.2s ease;
  box-sizing: border-box;  /* CRITICAL */
}

.input-text:focus {
  outline: none;
  border-color: var(--accent-color-for-text-icons);
  box-shadow: 0 0 0 3px rgba(22, 186, 49, 0.1);
}
```

**Toggle Switch (Custom Component):**

Modern, accessible toggle switch component for binary choices (draft/published, on/off, etc.)

**Size:** 52x28px (larger than Bootstrap default for better touch targets)
**Colors:**
- Off state: `#e5e7eb` (gray)
- On state: `#16ba31` (brand green)
- Focus ring: `rgba(22, 186, 49, 0.25)`

**HTML Structure:**
```html
<div class="mb-4">
    <label class="form-label fw-bold">Visibility</label>
    <div class="form-check form-switch form-switch-lg">
        <input class="form-check-input" type="checkbox" role="switch"
               id="save_as_draft" name="save_as_draft" value="1">
        <label class="form-check-label" for="save_as_draft">
            <i class="fas fa-eye-slash me-1" aria-hidden="true"></i>
            Save as draft
            <span class="toggle-status draft" id="draft-status-text">
                (private, only you can see)
            </span>
        </label>
    </div>
    <div class="toggle-helper-text">
        <span id="visibility-helper">
            Leave unchecked to publish immediately after moderation review.
        </span>
    </div>
</div>
```

**CSS Classes:**
- `.form-switch-lg` - Larger switch size (52x28px vs Bootstrap's 32x20px)
- `.toggle-status` - Status indicator text with dynamic color
- `.toggle-status.draft` - Orange/gray color for draft state
- `.toggle-status.published` - Green color for published state
- `.toggle-helper-text` - Small gray helper text below toggle

**JavaScript Pattern:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('save_as_draft');
    const helperText = document.getElementById('visibility-helper');
    const statusText = document.getElementById('draft-status-text');

    if (toggle && helperText && statusText) {
        toggle.addEventListener('change', function() {
            if (this.checked) {
                helperText.textContent = 'Your prompt will be saved privately.';
                statusText.textContent = '(private, only you can see)';
                statusText.className = 'toggle-status draft';
            } else {
                helperText.textContent = 'Your prompt will be published after review.';
                statusText.textContent = '(public, visible to everyone)';
                statusText.className = 'toggle-status published';
            }
        });
    }
});
```

**Accessibility:**
- `role="switch"` for screen reader context
- `aria-hidden="true"` on decorative icons
- Focus ring with 3px offset and 25% opacity
- Large touch target (52x28px minimum)
- Color contrast ratio >4.5:1 (WCAG AA)

**States:**
- **Default (unchecked):** Gray background, circle on left, helper text for "publish"
- **Checked:** Green background, circle on right, helper text for "draft"
- **Disabled:** 50% opacity, no hover effects, cursor not-allowed
- **Focus:** Green ring around switch (0 0 0 3px rgba(22, 186, 49, 0.25))

**Use Cases:**
- Upload page: "Save as Draft" toggle
- Edit page: "Published" toggle
- Settings page: Notification preferences
- Any binary choice requiring clear visual feedback

---

### Draft Mode Banner (Status Banner)

Contextual banner displayed at top of page for prompts in draft or pending review states.

**Two Variants:**

| Variant | Background | Icon | Message | Button |
|---------|------------|------|---------|--------|
| **User Draft** | `#fff3cd` | `fa-eye-slash` | "This prompt is in draft mode and only visible to you" | "Publish Now" (primary) |
| **Pending Review** | `#fff3cd` | `fa-clock` | "This prompt is pending admin review" | None |

**HTML Structure:**
```html
<!-- User Draft Variant -->
<div class="alert alert-warning draft-mode-banner mb-0 text-center" role="alert">
    <i class="fas fa-eye-slash me-2" aria-hidden="true"></i>
    <strong>Draft Mode:</strong> This prompt is only visible to you.
    <a href="{% url 'prompts:prompt_publish' prompt.slug %}"
       class="btn btn-success btn-sm ms-3">
        <i class="fas fa-globe me-1"></i> Publish Now
    </a>
</div>

<!-- Pending Review Variant -->
<div class="alert alert-warning pending-review-banner mb-0 text-center" role="alert">
    <i class="fas fa-clock me-2" aria-hidden="true"></i>
    <strong>Pending Review:</strong> This prompt is awaiting admin approval.
</div>
```

**CSS Classes:**
```css
.draft-mode-banner,
.pending-review-banner {
    background-color: #fff3cd;
    border-color: #ffeaa7;
    color: #856404;
    border-radius: 0;  /* Full-width, no rounded corners */
    margin-bottom: 0;
}

.draft-mode-banner .btn-success {
    background-color: #28a745;
    border-color: #28a745;
}
```

**Display Logic:**
```python
# Show banner if:
# 1. Prompt status is 0 (draft)
# 2. Current user is the prompt owner
# 3. NOT on edit page (banner shows on detail page only)

if prompt.status == 0 and request.user == prompt.author:
    if prompt.requires_manual_review:
        show_pending_review_banner()
    else:
        show_draft_mode_banner()
```

**Placement:**
- Below navbar, above page content
- Full width (no container padding)
- Sticky: No (scrolls with page)
- Z-index: Below navbar (999)

**Accessibility:**
- `role="alert"` for screen reader announcement
- `aria-hidden="true"` on decorative icons
- Color contrast: 4.5:1 minimum (WCAG AA)

---

## 🎭 Interaction Patterns

### Hover Effects

**Cards:**
- Lift: `translateY(-4px)`
- Shadow deepens: `0 8px 24px rgba(0,0,0,0.12)`
- Transition: `0.25-0.3s ease`

**Buttons:**
- Background darkens 10% (primary)
- Background appears (ghost)
- No scale effects (removed for subtlety)

**Icon Buttons:**
- Background: transparent → `--gray-100`
- Color: `--gray-700` → `--gray-900`
- Border-radius: 50% (maintains circular shape)

### Focus States

**Keyboard Navigation:**
```css
:focus-visible {
  outline: 2px solid var(--accent-color-for-text-icons);
  outline-offset: 2px;
}
```

**Form Inputs:**
```css
input:focus {
  border-color: #767676;  /* WCAG AA compliant */
  box-shadow: unset;
}
```

**Focus Management After DOM Removal:**
```css
/* When an element is removed from DOM, focus the next logical element */
/* Never leave focus on a removed element — keyboard users lose their place */
/* Announce removal via aria-live="polite" with 150ms stagger for multiple updates */
```

### Animations & Transitions

**Timing Functions:**
- **Ease:** Default, natural motion
- **Ease-out:** Quick start, slow end (preferred for UI)

**Duration Guidelines:**
- **Very fast:** 100-150ms (hover, focus)
- **Fast:** 200-300ms (buttons, icons) ← MOST COMMON
- **Medium:** 300-500ms (modals, mobile menu, borders)
- **Slow:** 600-800ms (page transitions, large movements)

**Mobile Menu Border Animation:**
- Menu slide: 0.3s (opacity, visibility, transform)
- Border fade-in: 0.5s delay + 0.3s duration
- Border fade-out: 0.5s (immediate, no delay)

**Rules:**
- Prefer `transform` and `opacity` (GPU accelerated)
- Avoid animating `width`, `height`, `top`, `left` (layout thrashing)
- Use `transition` for simple effects, `@keyframes` for complex

---

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile First Approach */

/* Extra Small (Mobile) */
@media (max-width: 400px) {
  .masonry-container {
    padding: 20px 12px;  /* Prevent horizontal scroll */
  }
}

/* Small (Large Mobile) */
@media (max-width: 768px) {
  .masonry-container {
    padding: 20px 15px;  /* Reduced from 40px */
  }
}

/* Medium (Tablet) */
@media (min-width: 768px) {
  /* 2-3 columns */
}

/* Large (Desktop) */
@media (min-width: 1024px) {
  /* 3-4 columns */
}

/* Extra Large (Wide Desktop) */
@media (min-width: 1440px) {
  /* 4-5 columns */
}
```

### Mobile Considerations

**Navigation:**
- Hamburger menu (overlay, not drawer)
- Fixed positioning with `top: 64px`
- Z-index: 999 (below navbar)
- Animated border using `::before` pseudo-element
- Full-width search bar (optional second row)

**Touch Targets:**
- Minimum size: 44x44px (WCAG AAA)
- Spacing between: 8px minimum

**Grid:**
- 1 column on mobile
- Responsive padding to prevent horizontal scroll
- Box-sizing: border-box on all elements

**Typography:**
- Slightly smaller on mobile (14-16px body)
- Logo: 24px (mobile) vs 28px (desktop)
- Maintain readability at all sizes

---

## 📏 Spacing System

### 8px Base Unit

**Scale:** Multiples of 8

```css
--space-1: 4px;    /* 0.5 × base (rare) */
--space-2: 8px;    /* 1 × base */
--space-3: 12px;   /* 1.5 × base */
--space-4: 16px;   /* 2 × base */
--space-5: 20px;   /* 2.5 × base */
--space-6: 24px;   /* 3 × base */
--space-8: 32px;   /* 4 × base */
--space-10: 40px;  /* 5 × base */
--space-12: 48px;  /* 6 × base */
--space-16: 64px;  /* 8 × base */
```

### Usage Guidelines

**Component Padding:**
- Navbar: 0 `--space-4` (with box-sizing)
- Cards: `--space-4` to `--space-6`
- Buttons: 12px 24px (medium)

**Grid Gaps:**
- Mobile: 15px (masonry containers)
- Desktop: 15px (masonry grid)
- Consistent spacing prevents layout shift

**Container Padding:**
- Mobile: 15px (prevents horizontal scroll)
- Tablet: 20px
- Desktop: 40px

---

## ⚡ Performance Optimization

### Font Loading Strategy

**1. Reduce Font Weights**
```html
<!-- BEFORE: 10 variants (heavy) -->
<link href="...Roboto:ital,wght@0,300;0,400;0,500;0,700;0,900;1,300;1,400;1,500;1,700;1,900&display=swap">

<!-- AFTER: 4 variants (optimized) -->
<link href="...Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
```

**Benefits:**
- Smaller font file size
- Faster loading time
- Removed unused weights (900, italics)

**2. Defer Non-Critical CSS**
```html
<!-- Font Awesome: Prevent 1033ms render blocking -->
<link rel="stylesheet" href="...all.min.css" media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" href="...all.min.css">
</noscript>
```

**Benefits:**
- Eliminates render blocking
- Icons load after initial paint
- Improves LCP (Largest Contentful Paint)

**3. Preconnect to External Resources**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://res.cloudinary.com">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
```

### CSS Optimization

**1. Global Box-Sizing**
```css
*, *::before, *::after {
  box-sizing: border-box;  /* Prevent padding overflow */
}
```

**2. Prevent Horizontal Scroll**
```css
html, body {
  overflow-x: hidden;
  max-width: 100vw;
  margin: 0;
  padding: 0;
}
```

**3. Container Constraints**
```css
.container {
  max-width: 100%;
  box-sizing: border-box;
  padding: 20px 15px;  /* Mobile: prevents overflow */
}

@media (min-width: 768px) {
  .container {
    padding: 20px 40px;  /* Desktop: more generous */
  }
}
```

### Performance Targets

**Lighthouse Scores (After Optimization):**
- Performance: 70-75% (limited by dev server)
- Accessibility: 100% (WCAG AA compliant)
- Best Practices: 100%
- SEO: 100%

**Production Expectations:**
- Performance: 85-90% (Heroku production server)
- Server response time: <600ms (was 4293ms in dev)

---

## ♿ Accessibility Standards

### WCAG AA Compliance

**Color Contrast (Fixed Nov 12, 2025):**
- ✅ Media filter tabs: `#1d4ed8` (was `#3b82f6`)
- ✅ Contrast ratio: 4.5:1 minimum (WCAG AA)
- ✅ Text on backgrounds: 4.5:1 minimum
- ✅ Headings: 3:1 minimum

**Focus Indicators:**
```css
:focus-visible {
  outline: 2px solid var(--accent-color-for-text-icons);
  outline-offset: 2px;
}

input:focus {
  border-color: #767676;  /* 4.5:1 contrast ratio */
}
```

**Touch Targets:**
- Minimum size: 44x44px (mobile icon buttons)
- Spacing: 8px minimum between interactive elements

**Keyboard Navigation:**
- All interactive elements accessible via Tab
- Focus visible on all focusable elements
- Skip links for main content (z-index: 9999)

**Screen Reader Support:**
- Semantic HTML (`<nav>`, `<main>`, `<article>`)
- ARIA labels on icon buttons
- Alt text on all images
- Role attributes on custom components

### ⛔ Hard Contrast Rules (v2.0)

**Added:** February 2026 — Aligned with CC_SPEC_TEMPLATE v2.0 accessibility requirements.

These rules are **non-negotiable** and are enforced by agent rejection criteria in the CC spec template.

#### Minimum Text Color: `--gray-500` (#737373)

| Context | Minimum Color | Contrast on White | Status |
|---------|---------------|-------------------|--------|
| Body text | `--gray-700` (#404040) | 9.7:1 | ✅ Preferred |
| Secondary text | `--gray-600` (#525252) | 7.4:1 | ✅ Acceptable |
| Tertiary text (timestamps, metadata) | `--gray-500` (#737373) | 4.6:1 | ✅ Minimum allowed |
| **NEVER for text** | `--gray-400` (#A3A3A3) | 2.7:1 | ❌ FAILS WCAG AA |
| **NEVER for text** | `--gray-300` (#D4D4D4) | 1.6:1 | ❌ FAILS WCAG AA |

**Rule:** Any text element rendered on a white or `--gray-50` background MUST use `--gray-500` (#737373) or darker. This includes:
- Timestamps and dates
- Metadata labels
- Helper text
- Category labels
- Notification text
- "X days ago" text

**Exempt elements** (decorative, not conveying text information):
- Border colors
- Background tints
- Decorative icons that have adjacent text labels
- Placeholder text in focused inputs (has separate WCAG treatment)

**Agent enforcement:** The @ux-reviewer and @accessibility agents will auto-reject (score below 6) any implementation that uses `--gray-400` or lighter for text content.

#### Focus Management on Element Removal

When JavaScript removes an element from the DOM (e.g., deleting a notification card, removing a list item):

1. **Move focus to the next logical element** — the next sibling card, the previous card if last, or a heading/container if the list is now empty
2. **Announce the removal** — use `aria-live="polite"` region with status message (e.g., "Notification deleted")
3. **If two updates fire simultaneously** (e.g., badge count update + status message), add a **150ms delay** to the second to avoid ARIA live region collision
4. **Never leave focus on a removed element** — this causes keyboard users to lose their place

```css
/* Example: scroll to and focus next card after deletion */
.notif-card:focus-visible {
    outline: 2px solid var(--accent-color-for-text-icons);
    outline-offset: 2px;
}
```

```javascript
// Example: focus management after card deletion
// Note: target elements must have tabindex="-1" for programmatic focus
function deleteCard(card) {
    const liveRegion = document.getElementById('notif-live-region');
    const nextCard = card.nextElementSibling || card.previousElementSibling;
    card.remove();

    if (nextCard) {
        nextCard.setAttribute('tabindex', '-1');
        nextCard.focus();
    } else {
        document.querySelector('.notifications-heading')?.focus();
    }

    // Delayed announcement to avoid live region collision
    setTimeout(() => {
        liveRegion.textContent = 'Notification deleted';
    }, 150);
}
```

#### ARIA Live Region Collision Prevention

When multiple ARIA live regions update simultaneously, screen readers may drop one announcement. Rule:

- **Never update two `aria-live` regions within 150ms of each other**
- If two updates are triggered by the same action (e.g., "item deleted" + "3 items remaining"), stagger them with `setTimeout`
- Primary status message fires immediately; secondary badge/count update fires after 150ms delay

---

## 🎬 Implementation Checklist

### ✅ Phase 1: Foundation (COMPLETE)

#### Setup
- [x] Create `/design-references/` folder
- [x] Add style guide to folder
- [x] Choose brand color (Neutral gray accent)

#### Design System Foundations
- [x] Create CSS variables file
- [x] Define all color variables
- [x] Define typography scale
- [x] Define spacing scale
- [x] Set up base styles (resets, body)
- [x] Implement box-sizing: border-box globally

#### Typography
- [x] Implement Google Fonts (Roboto, Pattaya, Open Sans)
- [x] Optimize font loading (reduce variants)
- [x] Create heading classes
- [x] Test readability across devices

### ✅ Phase 2: Core Components (COMPLETE)

#### Navigation
- [x] Redesign navigation bar (Pexels style)
- [x] Implement search bar styling
- [x] Add logo/branding
- [x] Create mobile hamburger menu
- [x] Add animated mobile menu border
- [x] Add sticky scroll behavior
- [x] Test across breakpoints
- [x] Fix horizontal scroll issues

#### Buttons
- [x] Create primary button styles
- [x] Create icon button styles (circular)
- [x] Implement hover/active/focus states
- [x] Test accessibility (keyboard navigation)

#### Performance
- [x] Defer Font Awesome loading
- [x] Reduce Google Fonts variants
- [x] Fix color contrast issues
- [x] Optimize CSS for performance

### 🚧 Phase 3: Content Cards (IN PROGRESS)

#### Card Component
- [x] Create base card styles (masonry)
- [x] Implement hover effects (lift, shadow)
- [x] Add overlay component
- [x] Test grid responsiveness
- [ ] Optimize image loading (lazy load)
- [ ] Add skeleton loading states

### 📋 Phase 4: Remaining Work

#### Forms
- [ ] Style remaining form inputs
- [ ] Create validation states
- [ ] Test form accessibility

#### Pages
- [ ] Finalize homepage layout
- [ ] Polish prompt detail page
- [ ] Update user profile design
- [ ] Optimize upload flow

#### Final Polish
- [ ] Add loading animations
- [ ] Polish all micro-interactions
- [ ] Review all spacing
- [ ] Cross-browser testing
- [ ] Accessibility audit
- [ ] Performance testing

---

## 📚 Additional Resources

### Design Inspiration
- [Pexels.com](https://www.pexels.com) - Photo sharing platform
- [Vimeo.com](https://www.vimeo.com) - Video sharing platform
- [Unsplash.com](https://unsplash.com) - Similar aesthetic

### Tools
- [Coolors.co](https://coolors.co) - Color palette generator
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) - Accessibility
- [PageSpeed Insights](https://pagespeed.web.dev) - Performance testing
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Audit tool

### CSS Frameworks
- [Bootstrap 5](https://getbootstrap.com) - Component library (currently used)
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)

---

## 📝 Recent Changes (Session 28: Dec 27-28, 2025)

### Collections Modal - Reference Implementation ✅

The Collections Modal established key UI patterns that serve as reference implementations for future features. This session completed 11 micro-specs with comprehensive validation and accessibility.

### Validation States Pattern

**Three-State Validation System:**

| State | Border Color | Background | Behavior |
|-------|--------------|------------|----------|
| **Error** | `--collection-error-color` (#dc3545) | None | Blocking - form submit disabled |
| **Warning** | `--collection-warning-color` (#ffc107) | `--collection-warning-bg` (#fff3cd) | Confirmable - user can proceed |
| **Success** | `--collection-success-color` (#28a745) | None | Auto-clear after 2 seconds |

**Key Implementation:**
- Levenshtein distance algorithm detects similar collection names
- Warnings are confirmable (user can ignore and proceed)
- Errors are blocking (requires user action)
- ARIA live regions announce validation changes

### Staggered Animation Pattern

**Card Entrance Animation:**
```css
.collection-card {
    animation: collectionCardFadeIn 150ms ease-out forwards;
    animation-delay: calc(var(--card-index) * 50ms);
}

@keyframes collectionCardFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
```

**Pattern Benefits:**
- Natural "cascade" effect when modal opens
- 50ms delay per card creates smooth visual flow
- Total animation time scales with card count
- JavaScript sets `--card-index` custom property per card

### Thumbnail Grid Pattern

**Responsive Layout by Item Count:**

| Items | Layout | Description |
|-------|--------|-------------|
| 0 | Placeholder | Icon-only centered placeholder |
| 1 | Full-width | Single image spans container |
| 2 | 50/50 split | Two images side-by-side |
| 3+ | 60/40 grid | Left column (main), right column (stacked) |

### Optimistic UI Pattern

**Implementation for Toggle Actions:**
1. Update count immediately on click (visual feedback)
2. Send API request in background
3. On success: count stays updated
4. On failure: revert count, show error message

**CSS for Optimistic Feedback:**
```css
.collection-card-count.updating {
    transition: color 0.2s ease;
    color: var(--collection-accent);
}
```

### Input Shake Animation

**For Validation Errors:**
```css
@keyframes inputShake {
    0%, 100% { transform: translateX(0); }
    20%, 60% { transform: translateX(-10px); }
    40%, 80% { transform: translateX(10px); }
}

.collection-form-input.shake {
    animation: inputShake 400ms ease;
}
```

### Accessibility Patterns

**Button Reset for Icon-Only Buttons:**
```css
.collection-modal-close,
.collection-create-back {
    appearance: none;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 8px;
}

.collection-modal-close:focus-visible,
.collection-create-back:focus-visible {
    outline: 2px solid var(--collection-accent);
    outline-offset: 2px;
}
```

**ARIA Live Regions:**
```html
<div class="collection-name-error" role="alert" aria-live="polite"></div>
<div class="collection-name-warning" role="status" aria-live="polite"></div>
```

### CSS Variables Added (8 new)

| Variable | Value | Purpose |
|----------|-------|---------|
| `--collection-error-color` | `#dc3545` | Error state red |
| `--collection-warning-color` | `#ffc107` | Warning state amber |
| `--collection-warning-bg` | `#fff3cd` | Warning background |
| `--collection-success-color` | `#28a745` | Success state green |
| `--collection-card-animation-duration` | `150ms` | Card fade-in |
| `--collection-card-animation-delay` | `50ms` | Staggered delay |
| `--collection-input-shake-duration` | `400ms` | Shake animation |
| `--collection-thumbnail-size` | `120px` | Thumbnail height |

### Agent Validation
- @frontend-developer: 9.5/10 - Clean JavaScript architecture
- @ui-ux-designer: 9.0/10 - Consistent interaction patterns
- **Average: 9.25/10** (exceeds 8+ threshold)

---

## 📝 Previous Session Changes (Session: Nov 17, 2025)

### Navigation Dropdown Performance Optimization ✅
- **Replaced Complex Caching with Event Delegation**
  - Initial approach (MutationObserver caching) rejected at 4.5/10 rating
  - Final solution (event delegation pattern) approved at 9.3/10 average
  - Agent-validated by @code-reviewer (9/10), @performance-expert (9.5/10), @security (9.5/10)

### Performance Improvements
- **51% faster** overall (125ms vs 255ms per session)
- **97% memory reduction** (1KB vs 15-30KB)
- **2-3ms per click** (optimal for 5-50 dropdowns)
- Zero cache invalidation overhead
- Works automatically with dynamic content

### Code Quality Enhancements
- **80% less code** (30 lines vs 150 lines)
- Wrapped in IIFE with `'use strict'` mode
- Added `event.isTrusted` security check (defense-in-depth)
- Private state variables (prevents DOM clobbering)
- Hardcoded selectors (prevents injection attacks)

### Implementation Details
**File:** `templates/base.html` (lines 909-958)
```javascript
(function() {
    'use strict';
    let currentOpenDropdown = null;
    let clickLockedDropdown = null;

    document.addEventListener('click', function(event) {
        if (!event.isTrusted) return;
        const clickedInsideDropdown = event.target.closest('.pexels-dropdown, .search-dropdown-menu');
        if (clickedInsideDropdown) {
            event.stopPropagation();
            return;
        }
        // Close all open dropdowns...
    });
})();
```

### Security Assessment ✅
- **Zero vulnerabilities found**
- XSS Risk: 2/10 (Very Low)
- DOM Clobbering: 3/10 (Low)
- Event Hijacking: 2/10 (Very Low)
- Clickjacking: 1/10 (Negligible)
- Compatible with Django security model, CSP, CSRF

### Challenges Overcome
1. **Premature Optimization** - Initial caching 25x-50x slower than original problem
2. **Memory Leak Detection** - Agent testing caught event listener accumulation
3. **Performance Paradox** - Always benchmark "optimizations" against baseline

### Lessons Learned
- "The best code is no code" - Simpler solution performed better
- Measure first, optimize later - Don't assume complexity equals performance
- Agent testing catches subtle bugs manual testing misses

---

## 📝 Previous Session Changes (Nov 13, 2025)

### Load More Button - Critical Fix ✅
- **Fixed ReferenceError:** `dragModeEnabled is not defined`
- Added `typeof` check before using variable (line 1301)
- Load More button now works without errors
- No more "Failed to load more prompts" modal

### Layout Refinements (Ultrawide/Desktop)
- **`.container` (Bootstrap override):** `max-width: 1600px` only on screens ≥1700px
- **`.masonry-container`:** Updated padding to `40px 0` (40px top/bottom, 0px left/right)
  - Removed mobile overrides (768px, 400px) - consistent across all views
  - Updated `max-width: 1600px`, `margin: 0 auto` (centered)
  - Fixed inline styles in 3 templates (prompt_list, trash_bin, _masonry_grid)
- **`.main-bg`:** Added flexbox centering (`display: flex; flex-direction: column; align-items: center`)
- **`.pexels-navbar`:** Added `width: 100%` for full viewport span
- **`.media-filter-container`:** Added `width: 100%`

### CSS Audit Completed 🔍
- Comprehensive audit across 20+ files
- Identified 7 critical issues, 30+ hardcoded colors, 150+ inline styles
- Full audit report created for next session roadmap
- See: Session report for detailed findings and fix strategy

---

## 📝 Previous Session Changes (Nov 12, 2025)

### Horizontal Scroll Fixes
- Added universal `box-sizing: border-box`
- Fixed `.masonry-container` padding (40px → 15px mobile)
- Added `overflow-x: hidden` globally
- Removed unnecessary `max-width: 100%` from nav container

### Mobile Menu Animation
- Implemented animated border using `::before` pseudo-element
- Timing: 0.5s delay → 0.3s fade-in (opening)
- Timing: 0.5s fade-out (closing, no delay)
- Prevents z-index overlap with navbar

### Performance Optimizations
- Reduced Google Fonts from 10 to 4 variants
- Deferred Font Awesome loading (eliminated 1033ms blocking)
- Font file size reduction: ~40% smaller

### Accessibility Improvements
- Fixed media filter tabs contrast: `#3b82f6` → `#1d4ed8`
- Now WCAG AA compliant (4.5:1 contrast ratio)
- Expected accessibility score: 96% → 100%

### UI Refinements
- Changed icon buttons to perfect circles (`border-radius: 50%`)
- Consistent circular design across all icon buttons

---

## ✅ Success Criteria

### Current Status (Nov 12, 2025)
- [x] Lighthouse Performance: 70-75% (dev server limited)
- [x] Lighthouse Accessibility: 100% (WCAG AA)
- [x] Lighthouse Best Practices: 100%
- [x] Lighthouse SEO: 100%
- [x] No horizontal scrollbar on any screen size
- [x] Mobile menu animation polished
- [x] Font loading optimized
- [x] Color contrast compliant

### Production Targets
- [ ] Lighthouse Performance: >85% (Heroku production)
- [ ] Server response time: <600ms
- [ ] Cross-browser tested (Chrome, Firefox, Safari, Edge)
- [ ] Mobile tested (iOS Safari, Android Chrome)

---

**END OF STYLE GUIDE**

*This document is a living reference. Update as design evolves and new patterns emerge.*

**Version:** 1.4
**Last Updated:** February 24, 2026
**Maintainer:** PromptFinder Design Team
**Next Review:** April 2026
