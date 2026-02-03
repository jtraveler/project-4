# SEO Audit Report: Prompt Detail Page

**Date:** February 3, 2026
**Session:** 66
**Audited File:** `prompts/templates/prompts/prompt_detail.html`
**Supporting Files:** `templates/base.html`, `prompts/models.py`, `prompts/services/content_generation.py`
**Agents Used:** seo-structure-architect, code-reviewer

---

## Executive Summary

The prompt detail page has solid SEO fundamentals — JSON-LD structured data, OG/Twitter cards, preloading, and good accessibility attributes. However, there are several correctness bugs (canonical URL leaking query params, `og:image` rendering "None"), missing elements (breadcrumbs, `og:video`, tag links), and a broken heading hierarchy that collectively reduce search performance and social sharing effectiveness.

## Score: 72/100

Based on weighted critical/high priority items. Strong foundation, but the canonical URL bug and missing internal linking from tags are significant gaps.

---

## Agent Ratings

| Agent | Score | Summary |
|-------|-------|---------|
| **seo-structure-architect** | **78/100** | Thorough analysis with ready-to-use code snippets. Identified all major gaps. |
| **code-reviewer** | **6/10** | Found critical bugs (canonical query params, `og:image` None, `default` filter chain, `decoding` conflict) that the SEO agent missed or flagged differently. Strict but accurate. |

---

## ✅ Implemented Correctly

| Category | Element | Notes |
|----------|---------|-------|
| Title Tag | `{{ prompt.title }} - {{ prompt.ai_generator }} AI Prompt \| PromptFinder` | Unique, keyword-rich, good format |
| Meta Description | `{{ prompt.description\|default:prompt.excerpt\|truncatechars:160 }}` | 160-char truncation, dynamic |
| OG: Core Tags | `og:title`, `og:description`, `og:image`, `og:type`, `og:url`, `og:site_name` | All present |
| OG: Article | `article:author`, `article:published_time` | Correct ISO 8601 via `date:'c'` |
| Twitter Card | `summary_large_image` with title, description, image | Correct card type for visual content |
| JSON-LD | Conditional `ImageObject`/`VideoObject` with author, dates, keywords | Well-structured |
| JSON-LD: Video | Conditional `duration` in ISO 8601 (`PT{n}S`) | Correct format |
| Hero Image | `srcset` (600w/1200w), `sizes`, `loading="eager"`, `fetchpriority="high"` | Good LCP optimization |
| Hero Video | `poster`, `aria-label`, `preload="metadata"`, conditional `width`/`height`/`aspect-ratio` | Prevents CLS for videos |
| Thumbnail Images | `loading="lazy"`, `decoding="async"` | Correct deferred loading |
| Alt Tags | `{{ prompt.title }} - {{ prompt.ai_generator }} AI Art Prompt for Image Generation` | Keyword-rich, descriptive |
| Preloading | Hero image/video poster preloaded in `<head>` | Good LCP strategy |
| DNS Prefetch | Cloudinary, Cloudflare, jsdelivr | Performance optimization |
| Viewport | `width=device-width, initial-scale=1` in base.html | Correct responsive setup |

---

## ⚠️ Needs Improvement

| Category | Element | Current State | Recommendation | Priority |
|----------|---------|---------------|----------------|----------|
| Canonical | `<link rel="canonical">` (line 55) | Uses `request.build_absolute_uri` — includes query params (`?utm_source=...`) | Use `request.scheme + request.get_host + request.path` to strip query params | **Critical** |
| OG URL | `og:url` (line 16) | Same `request.build_absolute_uri` bug as canonical | Same fix — strip query params | **Critical** |
| OG Image | `og:image` (line 14) | Can render as `content="None"` if `display_large_url` returns None | Wrap in `{% if prompt.display_large_url %}` guard | **Critical** |
| Headings | H4 rail cards (lines 324, 357, 378, 391) | h1→h2→**h4** (skips h3), then h3 for comments | Change rail card `<h4>` to `<h3>` | **High** |
| Performance | Hero image `decoding` (line 133) | `decoding="async"` contradicts `fetchpriority="high"` on LCP element | Remove `decoding="async"` or use `decoding="sync"` on hero image | **High** |
| Performance | Hero image CLS (lines 124-133) | No `width`/`height` attributes on `<img>` (videos have them) | Add `width`/`height` attributes or CSS `aspect-ratio` | **High** |
| Meta | `default` filter chain (lines 8, 13, 24, 63) | `description\|default:prompt.excerpt\|truncatechars:160` — empty string `""` won't trigger fallback | Use `description\|default_if_none:prompt.excerpt` or custom tag | **Medium** |
| Prefetch | DNS prefetch (line 30) | Prefetches Cloudinary but not B2/Cloudflare CDN domain | Add B2 CDN prefetch, make Cloudinary conditional | **Low** |

---

## ❌ Missing (Should Add)

| Category | Element | Why It Matters | Implementation Suggestion | Priority |
|----------|---------|----------------|---------------------------|----------|
| OG | `og:image:width`, `og:image:height` | Platforms render cards faster with known dimensions | Add `<meta property="og:image:width" content="1200">` etc. | **Critical** |
| OG | `og:video` tags for video prompts | Videos appear as static images on social platforms without these | Add `og:video`, `og:video:type`, `og:video:width/height` | **High** |
| Twitter | `twitter:site` | Enables brand attribution on Twitter/X cards | Add `<meta name="twitter:site" content="@promptfinder">` | **High** |
| Schema | Author `url` property | Strengthens Person entity for Knowledge Graph | Add `"url": "https://promptfinder.net{% url 'prompts:user_profile' ... %}"` to JSON-LD | **High** |
| Schema | `BreadcrumbList` | Enables breadcrumb rich results in SERPs | Add second JSON-LD block: Home → Generator Category → Prompt | **High** |
| Internal Linking | Tag links | Tags are `<span>` — zero internal linking value | Convert to `<a href="{% url 'prompts:home' %}?search={{ tag.name }}">` | **High** |
| Semantics | `<article>` wrapper | Better content boundary signals for search engines | Wrap prompt content in `<article>` | **Medium** |
| Semantics | `<time datetime="">` | Machine-readable dates in visible HTML reinforce JSON-LD signals | Wrap comment dates and post time in `<time>` elements | **Medium** |
| Model | `get_absolute_url()` on Prompt | Enables clean canonical URLs without query params | Add method returning `reverse('prompts:prompt_detail', kwargs={'slug': self.slug})` | **Medium** |
| Schema | `interactionStatistic` | View/like counts in schema enable richer SERP display | Add `InteractionCounter` for likes and views | **Low** |
| Footer | Copyright year | Shows "2025" in base.html line 789 | Use `{% now "Y" %}` template tag | **Low** |

---

## 📋 Action Items (Prioritized)

### Critical (Do First)

1. **Fix canonical URL to strip query parameters** — `prompt_detail.html:55` and `prompt_detail.html:16`
   - Replace `{{ request.build_absolute_uri }}` with `{{ request.scheme }}://{{ request.get_host }}{{ request.path }}`
   - Affects both `<link rel="canonical">` and `og:url`

2. **Guard `og:image` against None** — `prompt_detail.html:14`
   - Wrap in `{% if prompt.display_large_url %}` conditional

3. **Add `og:image:width` and `og:image:height`** — after `prompt_detail.html:14`
   - Add dimension meta tags for faster social card rendering

### High Priority

4. **Fix heading hierarchy (h4 → h3)** — `prompt_detail.html:324, 357, 378, 391`
   - Change all `<h4 class="rail-card-title">` to `<h3 class="rail-card-title">`

5. **Convert tags from `<span>` to `<a>` links** — `prompt_detail.html:381`
   - Link each tag to filtered search results

6. **Add `og:video` tags for video prompts** — `prompt_detail.html:10-19`
   - Add `og:video`, `og:video:type`, `og:video:width`, `og:video:height`

7. **Add `twitter:site` handle** — after `prompt_detail.html:22`
   - `<meta name="twitter:site" content="@promptfinder">`

8. **Add BreadcrumbList schema** — after `prompt_detail.html:80`
   - Home → AI Generator Category → Prompt Title

9. **Add author URL to JSON-LD Person** — `prompt_detail.html:69`
   - `"url": "https://promptfinder.net{% url 'prompts:user_profile' prompt.author.username %}"`

10. **Add `width`/`height` to hero image** — `prompt_detail.html:124-133`
    - Prevents CLS; hero video already has this

11. **Remove `decoding="async"` from hero image** — `prompt_detail.html:133`
    - Contradicts `fetchpriority="high"` on LCP element

### Medium Priority (Nice to Have)

12. Add `<article>` semantic wrapper around prompt content
13. Add `<time datetime="">` elements for comment dates and post time
14. Add `get_absolute_url()` to Prompt model for cleaner URL generation
15. Update copyright year to `{% now "Y" %}` in `base.html:789`
16. Add `interactionStatistic` to JSON-LD schema (likes, views)
17. Update DNS prefetch to include B2/Cloudflare CDN domain

---

## Code Snippets for Missing Elements

### Critical #1: Fix Canonical URL (strip query params)

**File:** `prompts/templates/prompts/prompt_detail.html` — line 55

```html
<!-- BEFORE: -->
<link rel="canonical" href="{{ request.build_absolute_uri }}">

<!-- AFTER: -->
<link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
```

Apply same fix to `og:url` on line 16:

```html
<!-- BEFORE: -->
<meta property="og:url" content="{{ request.build_absolute_uri }}">

<!-- AFTER: -->
<meta property="og:url" content="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
```

### Critical #2: Guard og:image Against None

**File:** `prompts/templates/prompts/prompt_detail.html` — line 14

```html
<!-- BEFORE: -->
<meta property="og:image" content="{{ prompt.display_large_url }}">

<!-- AFTER: -->
{% if prompt.display_large_url %}
<meta property="og:image" content="{{ prompt.display_large_url }}">
{% endif %}
```

### Critical #3: Add OG Image Dimensions

**File:** `prompts/templates/prompts/prompt_detail.html` — after og:image line

```html
{% if prompt.display_large_url %}
<meta property="og:image" content="{{ prompt.display_large_url }}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="1200">
{% endif %}
```

### High #4: Fix Heading Hierarchy

**File:** `prompts/templates/prompts/prompt_detail.html` — lines 324, 357, 378, 391

Replace all `<h4 class="rail-card-title">` with `<h3 class="rail-card-title">`.

Corrected heading outline:
```
H1: {{ prompt.title }} - AI Prompt Details (visually-hidden)
├── H2: {{ prompt.title }}
├── H3: Model Used          (was H4)
├── H3: Prompt               (was H4)
├── H3: Tags                 (was H4)
├── H3: More from @author    (was H4)
└── H3: Comments
```

### High #5: Convert Tags to Links

**File:** `prompts/templates/prompts/prompt_detail.html` — lines 380-382

```html
<!-- BEFORE: -->
{% for tag in prompt.tags.all %}
    <span class="tag-badge" data-tag="{{ tag.name }}">{{ tag.name }}</span>
{% endfor %}

<!-- AFTER: -->
{% for tag in prompt.tags.all %}
    <a href="{% url 'prompts:home' %}?search={{ tag.name|urlencode }}&type={% if prompt.is_video %}videos{% else %}images{% endif %}"
       class="tag-badge"
       title="Search prompts tagged with {{ tag.name }}">
        {{ tag.name }}
    </a>
{% endfor %}
```

### High #6: Add og:video Tags

**File:** `prompts/templates/prompts/prompt_detail.html` — in og_tags block

```html
{% if prompt.is_video and prompt.display_video_url %}
<meta property="og:video" content="{{ prompt.display_video_url }}">
<meta property="og:video:type" content="video/mp4">
{% if prompt.video_width and prompt.video_height %}
<meta property="og:video:width" content="{{ prompt.video_width }}">
<meta property="og:video:height" content="{{ prompt.video_height }}">
{% endif %}
{% if prompt.video_duration %}
<meta property="og:video:duration" content="{{ prompt.video_duration }}">
{% endif %}
{% endif %}
```

### High #7: Add twitter:site

**File:** `prompts/templates/prompts/prompt_detail.html` — in twitter_tags block

```html
<meta name="twitter:site" content="@promptfinder">
```

### High #8: Add BreadcrumbList Schema

**File:** `prompts/templates/prompts/prompt_detail.html` — after line 80 (before `{% endblock %}`)

```html
<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": "https://promptfinder.net/"
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": "{{ prompt.get_ai_generator_display|escapejs }}",
            "item": "https://promptfinder.net{% url 'prompts:ai_generator_category' prompt.get_generator_url_slug %}"
        },
        {
            "@type": "ListItem",
            "position": 3,
            "name": "{{ prompt.title|escapejs }}"
        }
    ]
}
</script>
```

### High #9: Add Author URL to Schema

**File:** `prompts/templates/prompts/prompt_detail.html` — lines 67-70

```json
"author": {
    "@type": "Person",
    "name": "{{ prompt.author.username|escapejs }}",
    "url": "https://promptfinder.net{% url 'prompts:user_profile' prompt.author.username %}"
},
```

### High #11: Fix decoding on Hero Image

**File:** `prompts/templates/prompts/prompt_detail.html` — line 133

```html
<!-- BEFORE: -->
decoding="async">

<!-- AFTER (remove entirely, or use sync): -->
decoding="sync">
```

### Medium #13: Add time Elements

**File:** `prompts/templates/prompts/prompt_detail.html` — line 534

```html
<!-- BEFORE: -->
<span class="font-weight-normal text-muted">
    on {{ comment.created_on }}
</span>

<!-- AFTER: -->
<span class="font-weight-normal text-muted">
    on <time datetime="{{ comment.created_on|date:'c' }}">{{ comment.created_on|date:'M d, Y' }}</time>
</span>
```

### Medium #15: Auto-Update Copyright Year

**File:** `templates/base.html` — line 789

```html
<!-- BEFORE: -->
© 2025 Copyright:

<!-- AFTER: -->
© {% now "Y" %} Copyright:
```

---

## Projected Score After Fixes

| Fix Tier | Score Impact |
|----------|-------------|
| Current | 72/100 |
| After Critical fixes | ~82/100 |
| After Critical + High fixes | ~90/100 |
| After all fixes | ~95/100 |

---

## Next Steps

1. Review findings and prioritize based on impact vs effort
2. Create micro-specs for each fix group (Critical, High, Medium)
3. Implement in order, with agent validation (8+/10) before committing

---

**Report Version:** 1.0
**Generated:** February 3, 2026 (Session 66)
