# PromptFinder UI Redesign - Style Guide

**Based on:** Pexels.com + Vimeo.com Design Systems
**Created:** November 8, 2025
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
10. [Implementation Checklist](#implementation-checklist)

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

**What to Embrace:**
- ✅ Generous whitespace everywhere
- ✅ Content as the visual interest
- ✅ Subtle, purposeful interactions
- ✅ High contrast for accessibility
- ✅ Consistent, predictable patterns

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
│  NAVIGATION BAR (60-80px height)                     │
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

**Tablet:**
- **Full width** with 16-24px padding

**Mobile:**
- **Full width** with 16px padding

**Rule:** Content should flow to viewport edges (no rigid containers that create tunnels)

---

## 🎨 Color System

### Primary Palette

#### Brand Colors (Choose One for PromptFinder)

**Option 1: Pexels Green Inspired**
```css
--brand-primary: #05A081;      /* Primary brand color */
--brand-primary-hover: #048770; /* Hover state (10% darker) */
--brand-primary-active: #037060; /* Active state (20% darker) */
--brand-primary-light: #E6F7F4; /* Backgrounds, subtle highlights */
```

**Option 2: Vimeo Blue Inspired**
```css
--brand-primary: #1AB7EA;      /* Primary brand color */
--brand-primary-hover: #1599C9; /* Hover state */
--brand-primary-active: #127BA7; /* Active state */
--brand-primary-light: #E6F7FD; /* Backgrounds */
```

**Option 3: Custom Purple (Unique to PromptFinder)**
```css
--brand-primary: #7C3AED;      /* Purple - AI/Tech feel */
--brand-primary-hover: #6D28D9; /* Hover */
--brand-primary-active: #5B21B6; /* Active */
--brand-primary-light: #F5F3FF; /* Backgrounds */
```

**Recommendation:** Purple (#7C3AED) - Unique, tech-forward, not overused

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

/* Info */
--info: #3B82F6;          /* Blue - informational */
--info-light: #DBEAFE;    /* Backgrounds */
```

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
- Primary buttons: `--brand-primary`
- Links: `--brand-primary`
- Active states: `--brand-primary`
- Highlights: `--brand-primary-light`

**Contrast Requirements:**
- Text on white: Minimum 4.5:1 ratio (WCAG AA)
- Headings: Minimum 3:1 ratio
- Interactive elements: Minimum 3:1 ratio
- Use tools: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

---

## ✍️ Typography

### Font Stack

**Recommendation: System Font Stack (Performance + Clarity)**

```css
font-family: -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu',
             'Cantarell', 'Fira Sans', 'Droid Sans',
             'Helvetica Neue', sans-serif;
```

**Why System Fonts:**
- ✅ Zero load time (already on user's device)
- ✅ Native appearance per platform
- ✅ Excellent readability
- ✅ Consistent with modern web standards

**Alternative: Google Fonts (If Custom Font Needed)**
- **Inter** - Modern, clean, excellent at small sizes
- **Work Sans** - Friendly, professional
- **DM Sans** - Geometric, minimal

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
--font-light: 300;    /* Rarely used */
--font-normal: 400;   /* Body text (PRIMARY) */
--font-medium: 500;   /* Emphasis, buttons, labels */
--font-semibold: 600; /* Headings, strong emphasis */
--font-bold: 700;     /* Very strong emphasis (rare) */
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
- Font weight: 600 (semibold) or 700 (bold)
- Color: `--gray-800` or `--gray-900`
- Line height: `--leading-tight`

**Body Text:**
- Font size: 16px (never smaller than 14px)
- Font weight: 400 (normal)
- Color: `--gray-700`
- Line height: 1.5-1.6
- Max width: 65-75 characters (optimal readability)

**Links:**
- Color: `--brand-primary`
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
- Height: 64-72px
- Background: `--white` with subtle shadow or 1px border-bottom
- Fixed/sticky on scroll (remains visible)
- Z-index: 1000
- Shadow: `0 2px 8px rgba(0,0,0,0.06)` (subtle)

**Components:**
1. **Logo**
   - Max height: 36-40px
   - Left-aligned with 24px padding
   - Links to homepage

2. **Search Bar**
   - Width: 400-600px (centered)
   - Height: 40-48px
   - Border: 1px solid `--gray-200`
   - Border radius: 24px (pill shape) or 8px (rounded)
   - Placeholder: "Search AI prompts..." (gray-400)
   - Icon: Magnifying glass (left side, 20px)
   - Focus: Border color changes to `--brand-primary`

3. **Upload Button**
   - Style: Primary button
   - Text: "Upload" or "+ Upload Prompt"
   - Right side, 16px from profile

4. **Profile**
   - Avatar (32px circle) or username
   - Dropdown menu on click
   - Icon: Down chevron (if logged in)
   - Login/Signup links (if logged out)

**Mobile Version:**

```
┌──────────────────────────────┐
│  [☰]  [Logo]       [Upload]  │ ← Hamburger menu
├──────────────────────────────┤
│  [Search Bar - Full Width]   │ ← Second row
└──────────────────────────────┘
```

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
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.25s ease;
  cursor: pointer;
}

.prompt-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}

.prompt-card img {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}

.prompt-card:hover img {
  transform: scale(1.05);
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
    rgba(0,0,0,0) 0%,
    rgba(0,0,0,0.6) 100%
  );
  opacity: 0;
  transition: opacity 0.25s ease;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 16px;
}

.prompt-card:hover .prompt-card-overlay {
  opacity: 1;
}
```

**Overlay Content (Appears on Hover):**
- Prompt title (white text)
- Author name (white text, smaller)
- AI generator badge (e.g., "Midjourney")
- Download/Like/Share buttons
- Stats (likes, views, comments)

**Variations:**
- **Grid card**: Uniform size, fixed aspect ratio
- **Masonry card**: Variable height, natural aspect ratio
- **Featured card**: Larger size, more prominent

---

### Buttons

**Primary Button:**
```css
.btn-primary {
  background: var(--brand-primary);
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
  background: var(--brand-primary-hover);
}

.btn-primary:active {
  background: var(--brand-primary-active);
}
```

**Secondary Button:**
```css
.btn-secondary {
  background: transparent;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  border-color: var(--gray-400);
  background: var(--gray-50);
}
```

**Ghost Button:**
```css
.btn-ghost {
  background: transparent;
  color: var(--gray-700);
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-ghost:hover {
  background: var(--gray-100);
}
```

**Button Sizes:**
- **Small**: padding 8px 16px, font-size 14px
- **Medium**: padding 12px 24px, font-size 16px (DEFAULT)
- **Large**: padding 16px 32px, font-size 18px

**Icon Buttons:**
- Size: 40x40px (minimum touch target)
- Border radius: 50% (circle) or 8px (rounded square)
- Icon size: 20-24px
- Padding: 8-10px

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
}

.input-text:focus {
  outline: none;
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 3px var(--brand-primary-light);
}

.input-text::placeholder {
  color: var(--gray-400);
}
```

**Textarea:**
```css
.input-textarea {
  /* Same as text input but... */
  min-height: 120px;
  resize: vertical;
  line-height: 1.5;
}
```

**Select Dropdown:**
```css
.input-select {
  /* Same as text input */
  appearance: none;
  background-image: url('chevron-down.svg');
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 40px;
}
```

**Checkbox/Radio:**
- Size: 20x20px (minimum)
- Custom styling with `:checked` pseudo-class
- Label: 16px text, 8px left margin

**Form Labels:**
```css
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 8px;
}
```

**Form Validation:**
- Error state: Red border, error message below
- Success state: Green border (optional)
- Helper text: Gray, 14px, below input

---

### Modals/Dialogs

**Structure:**
```
┌─────────────────────────────────────┐
│  ×                                  │ ← Close button (top-right)
│                                     │
│  Modal Title                        │ ← H2, 24-30px
│                                     │
│  Modal content goes here...         │ ← Body text
│  Forms, images, etc.                │
│                                     │
│  [Cancel]  [Primary Action]        │ ← Button group
└─────────────────────────────────────┘
```

**Specifications:**
- Max width: 600px (small), 800px (medium), 1000px (large)
- Background: `--white`
- Border radius: 12-16px
- Shadow: `0 20px 60px rgba(0,0,0,0.3)` (prominent)
- Padding: 24-32px
- Overlay: `rgba(0,0,0,0.5)` backdrop
- Animation: Fade in + scale from 0.95 to 1.0

---

### Tags/Badges

**Tag Styles:**
```css
.tag {
  display: inline-block;
  padding: 6px 12px;
  background: var(--gray-100);
  color: var(--gray-700);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s ease;
}

.tag:hover {
  background: var(--gray-200);
  cursor: pointer;
}

.tag-primary {
  background: var(--brand-primary-light);
  color: var(--brand-primary);
}
```

**Badge (Notification Count):**
```css
.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: var(--error);
  color: white;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
```

---

### Loading States

**Skeleton Screens:**
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--gray-200) 0%,
    var(--gray-100) 50%,
    var(--gray-200) 100%
  );
  background-size: 200% 100%;
  animation: loading 1.5s ease-in-out infinite;
  border-radius: 8px;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

**Spinner:**
```css
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--gray-200);
  border-top-color: var(--brand-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## 🎭 Interaction Patterns

### Hover Effects

**Cards:**
- Lift: `translateY(-4px)`
- Shadow deepens: `0 8px 24px rgba(0,0,0,0.12)`
- Image zoom: `scale(1.05)` with `overflow: hidden` on container
- Overlay fades in: `opacity: 0 → 1`
- Transition: `0.25s ease`

**Buttons:**
- Background darkens 10% (primary)
- Border color darkens (secondary)
- Background appears (ghost)
- Scale slightly: `scale(1.02)` (optional, subtle)

**Links:**
- Color change or underline
- No color change on visited (consistency)

**Images:**
- Slight zoom: `scale(1.05)`
- Or brightness increase: `brightness(1.1)`

### Focus States

**Keyboard Navigation:**
```css
:focus-visible {
  outline: 3px solid var(--brand-primary);
  outline-offset: 2px;
}
```

**Form Inputs:**
```css
input:focus {
  border-color: var(--brand-primary);
  box-shadow: 0 0 0 3px var(--brand-primary-light);
}
```

### Active States

**Buttons:**
```css
.btn-primary:active {
  transform: scale(0.98);
  background: var(--brand-primary-active);
}
```

### Animations & Transitions

**Timing Functions:**
- **Ease:** Default, natural motion
- **Ease-in-out:** Smooth start and end
- **Ease-out:** Quick start, slow end (preferred for UI)

**Duration Guidelines:**
- **Very fast:** 100-150ms (hover, focus)
- **Fast:** 200-300ms (cards, buttons) ← MOST COMMON
- **Medium:** 400-500ms (modals, dropdowns)
- **Slow:** 600-800ms (page transitions, large movements)

**Rules:**
- Prefer `transform` and `opacity` (GPU accelerated)
- Avoid animating `width`, `height`, `top`, `left` (layout thrashing)
- Use `will-change` sparingly (memory intensive)

**Example - Card Hover:**
```css
.card {
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
```

### Scroll Behavior

**Smooth Scrolling:**
```css
html {
  scroll-behavior: smooth;
}
```

**Sticky Elements:**
- Navigation bar sticks to top
- Filters/tabs stick below nav (optional)

**Infinite Scroll:**
- Load more content when user reaches 80% of page height
- Show loading indicator (spinner or skeleton)
- Smooth insertion of new content
- Maintain scroll position

**Scroll to Top Button:**
- Appears after scrolling 300-500px
- Fixed position: bottom-right, 24px from edges
- Circular button with up arrow icon
- Smooth scroll animation

---

## 📱 Responsive Design

### Breakpoints

```css
/* Mobile First Approach */

/* Extra Small (Mobile) */
@media (min-width: 320px) {
  /* 1 column */
}

/* Small (Large Mobile) */
@media (min-width: 480px) {
  /* 1-2 columns */
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
- Hamburger menu (if needed)
- Full-width search bar
- Bottom navigation bar (optional, for key actions)

**Touch Targets:**
- Minimum size: 44x44px (Apple) or 48x48px (Material)
- Spacing between: 8px minimum

**Grid:**
- 1 column on mobile
- 2 columns on large mobile (480px+)
- Increase gaps on larger screens

**Typography:**
- Slightly smaller on mobile (14-16px body)
- Larger line heights (1.6-1.7)
- Reduce heading sizes by 20-30%

**Forms:**
- Full-width inputs on mobile
- Larger touch targets (48px height)
- Stack labels above inputs (not side-by-side)

**Images:**
- Use `srcset` for responsive images
- Lazy load below-fold images
- Serve WebP with JPEG fallback

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
--space-20: 80px;  /* 10 × base */
--space-24: 96px;  /* 12 × base */
```

### Usage Guidelines

**Component Padding:**
- Small: 12-16px
- Medium: 16-24px (most common)
- Large: 24-32px

**Section Spacing:**
- Between sections: 48-64px
- Within sections: 24-32px

**Grid Gaps:**
- Mobile: 16px
- Tablet: 20-24px
- Desktop: 24-32px

**Text Spacing:**
- Paragraph margin-bottom: 16px
- Heading margin-bottom: 8-12px
- List item spacing: 8px

**Button Padding:**
- Small: 8px 16px
- Medium: 12px 24px
- Large: 16px 32px

---

## 🎬 Implementation Checklist

### Phase 1: Foundation (Week 1)

#### Setup
- [ ] Create `/design-references/` folder
- [ ] Add this style guide to folder
- [ ] Review with team/stakeholders
- [ ] Choose brand color (Purple recommended)

#### Design System Foundations
- [ ] Create CSS variables file (`design-system.css`)
- [ ] Define all color variables
- [ ] Define typography scale
- [ ] Define spacing scale
- [ ] Set up base styles (resets, body)

#### Typography
- [ ] Implement system font stack
- [ ] Create heading classes (h1-h6)
- [ ] Create text size utilities
- [ ] Create font weight utilities
- [ ] Test readability across devices

### Phase 2: Core Components (Week 2)

#### Navigation
- [ ] Redesign navigation bar
- [ ] Implement search bar styling
- [ ] Add logo/branding
- [ ] Create mobile hamburger menu
- [ ] Add sticky scroll behavior
- [ ] Test across breakpoints

#### Buttons
- [ ] Create primary button styles
- [ ] Create secondary button styles
- [ ] Create ghost button styles
- [ ] Create icon button styles
- [ ] Implement hover/active/focus states
- [ ] Test accessibility (keyboard navigation)

#### Forms
- [ ] Style text inputs
- [ ] Style textareas
- [ ] Style select dropdowns
- [ ] Style checkboxes/radios
- [ ] Create validation states
- [ ] Test form accessibility

### Phase 3: Content Cards (Week 3)

#### Card Component
- [ ] Create base card styles
- [ ] Implement masonry grid layout
- [ ] Add hover effects (lift, shadow, overlay)
- [ ] Create overlay component
- [ ] Add metadata display (author, stats)
- [ ] Test grid responsiveness
- [ ] Optimize image loading (lazy load)

#### Grid System
- [ ] Implement CSS Grid or Masonry.js
- [ ] Test with varied image sizes
- [ ] Add skeleton loading states
- [ ] Implement infinite scroll
- [ ] Test performance with 100+ cards

### Phase 4: Pages (Week 4)

#### Homepage
- [ ] Redesign hero section
- [ ] Implement new card grid
- [ ] Add filtering/sorting UI
- [ ] Update footer
- [ ] Test loading performance
- [ ] Mobile optimization

#### Prompt Detail Page
- [ ] Redesign layout (image + content)
- [ ] Style prompt information section
- [ ] Update author card
- [ ] Style comments section
- [ ] Add related prompts
- [ ] Test responsiveness

#### User Profile
- [ ] Redesign profile header
- [ ] Implement user prompts grid
- [ ] Style stats/bio section
- [ ] Update edit profile form
- [ ] Mobile optimization

#### Upload Flow
- [ ] Update Step 1 (drag & drop)
- [ ] Update Step 2 (form styling)
- [ ] Polish progress indicators
- [ ] Test entire flow
- [ ] Mobile optimization

### Phase 5: Polish & Launch (Week 5)

#### Final Touches
- [ ] Add loading animations
- [ ] Implement micro-interactions
- [ ] Polish all hover states
- [ ] Review all spacing
- [ ] Check color contrast (WCAG AA)
- [ ] Test keyboard navigation

#### Performance
- [ ] Optimize CSS (remove unused)
- [ ] Minify assets
- [ ] Test Lighthouse scores (>90)
- [ ] Optimize images (WebP, compression)
- [ ] Test load times

#### Cross-Browser Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

#### Accessibility Audit
- [ ] Screen reader testing
- [ ] Keyboard navigation testing
- [ ] Color contrast verification
- [ ] ARIA labels review
- [ ] Focus indicator visibility

#### Launch
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Fix critical bugs
- [ ] Deploy to production
- [ ] Monitor analytics
- [ ] Gather user feedback

---

## 📚 Additional Resources

### Design Inspiration
- [Pexels.com](https://www.pexels.com) - Photo sharing platform
- [Vimeo.com](https://www.vimeo.com) - Video sharing platform
- [Unsplash.com](https://unsplash.com) - Similar aesthetic
- [Dribbble.com](https://dribbble.com) - Design inspiration

### Tools
- [Coolors.co](https://coolors.co) - Color palette generator
- [Google Fonts](https://fonts.google.com) - Free web fonts
- [Hero Patterns](https://heropatterns.com) - SVG background patterns
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) - Accessibility
- [PageSpeed Insights](https://pagespeed.web.dev) - Performance testing

### CSS Frameworks (Optional)
- [Tailwind CSS](https://tailwindcss.com) - Utility-first framework
- [Bootstrap 5](https://getbootstrap.com) - Component library (currently used)
- [CSS Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)

### JavaScript Libraries
- [Masonry.js](https://masonry.desandro.com) - Grid layout
- [Isotope](https://isotope.metafizzy.co) - Filtering + layout
- [Infinite Scroll](https://infinite-scroll.com) - Load more content
- [Lottie](https://airbnb.design/lottie/) - Animations

---

## 📝 Notes for Implementation

### Current State (Bootstrap 5)
- PromptFinder currently uses Bootstrap 5
- Can gradually migrate components
- Keep Bootstrap utilities, replace components
- Or full rewrite with custom CSS

### Migration Strategy

**Option 1: Gradual (Recommended)**
1. Keep Bootstrap grid system
2. Override Bootstrap component styles
3. Add custom components alongside
4. Remove Bootstrap once comfortable

**Option 2: Full Rewrite**
1. Remove Bootstrap entirely
2. Build custom CSS from scratch
3. More control, steeper learning curve
4. Longer timeline (6-8 weeks)

### Recommendation
- **Start with Option 1** (gradual migration)
- Keep Bootstrap grid utilities
- Override component styles with custom CSS
- Test each component in isolation
- Deploy incrementally (page by page)

---

## ✅ Success Criteria

### Before Launch
- [ ] All components match style guide
- [ ] Lighthouse score >90 (mobile + desktop)
- [ ] WCAG AA accessibility compliance
- [ ] Cross-browser tested
- [ ] Mobile-responsive (all breakpoints)
- [ ] Loading states implemented
- [ ] Hover/focus states polished
- [ ] No console errors
- [ ] Stakeholder approval

### Post-Launch Metrics
- [ ] User feedback positive (>80% approval)
- [ ] Bounce rate decreased
- [ ] Time on site increased
- [ ] Conversion rate improved
- [ ] Mobile usage improved
- [ ] SEO rankings maintained/improved

---

**END OF STYLE GUIDE**

*This document is a living reference. Update as design evolves and new patterns emerge.*

**Version:** 1.0
**Last Updated:** November 8, 2025
**Maintainer:** PromptFinder Design Team
**Next Review:** January 2026
