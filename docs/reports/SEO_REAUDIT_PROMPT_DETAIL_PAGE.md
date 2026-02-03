# SEO Re-Audit Report: Prompt Detail Page (Post-Fix Verification)

**Date:** February 3, 2026
**Session:** 66
**Audited File:** `prompts/templates/prompts/prompt_detail.html`
**Supporting Files:** `templates/base.html`
**Agents Used:** seo-structure-architect, code-reviewer
**Previous Report:** `docs/reports/SEO_AUDIT_PROMPT_DETAIL_PAGE.md`

---

## Executive Summary

All 13 Critical and High priority fixes from the initial audit have been implemented and verified. The page has improved from 72/100 to **88/100**. Three new HIGH issues were identified by the code-reviewer that were not in the original audit scope, primarily around JSON-LD correctness and domain consistency.

---

## Score Comparison

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Overall Score** | 72/100 | 88/100 | +16 |
| Critical Issues | 3 | 0 | -3 |
| High Issues | 8 | 2 | -6 |
| Medium Issues | 6 | 6 | 0 |

---

## Agent Ratings

| Agent | Score | Summary |
|-------|-------|---------|
| **seo-structure-architect** | **8.1/10** | All previous fixes verified. Identified breadcrumb item URL gap, missing og:image:alt, and noindex for drafts. |
| **code-reviewer** | **7.5/10** | Found 3 HIGH runtime correctness issues: `escapejs|truncatechars` filter ordering, `contentUrl` rendering "None", hardcoded domain mismatch in JSON-LD. |
| **Average** | **7.8/10** | Below 8+/10 threshold. HIGH issues need resolution. |

---

## Verified Fixes (All 13 Confirmed)

| # | Fix | File:Line | Status |
|---|-----|-----------|--------|
| 1 | Canonical URL strips query params | `prompt_detail.html:67` | Verified |
| 2 | og:url strips query params | `prompt_detail.html:25` | Verified |
| 3 | og:image guarded with `{% if %}` | `prompt_detail.html:14-18` | Verified |
| 4 | og:image:width/height added | `prompt_detail.html:16-17` | Verified |
| 5 | twitter:image guarded with `{% if %}` | `prompt_detail.html:35-37` | Verified |
| 6 | Heading hierarchy h4 changed to h3 | `prompt_detail.html:366,399,420,437` | Verified |
| 7 | Tags converted from `<span>` to `<a>` links | `prompt_detail.html:422-428` | Verified |
| 8 | og:video tags for video prompts | `prompt_detail.html:19-23` | Verified |
| 9 | twitter:site handle added | `prompt_detail.html:32` | Verified |
| 10 | BreadcrumbList JSON-LD schema added | `prompt_detail.html:96-120` | Verified |
| 11 | Author URL added to JSON-LD Person | `prompt_detail.html:82` | Verified |
| 12 | Hero image width/height attributes | `prompt_detail.html:171-172` | Verified |
| 13 | `decoding="async"` removed from hero | `prompt_detail.html:164-174` | Verified |
| 14 | Copyright year uses `{% now "Y" %}` | `base.html:789` | Verified |

---

## Remaining Issues

### HIGH Priority (New Findings)

#### 1. `escapejs` before `truncatechars` can produce invalid JSON

**File:** `prompt_detail.html:116`
**Current:** `{{ prompt.title|escapejs|truncatechars:50 }}`
**Problem:** `escapejs` expands characters (e.g., `'` becomes `\u0027`, 6 chars instead of 1). Then `truncatechars:50` counts expanded characters and can cut mid-escape sequence, producing invalid JSON like `\u00`.
**Fix:** Swap filter order to `truncatechars:50|escapejs`.

#### 2. JSON-LD `contentUrl` / `thumbnailUrl` can render "None"

**File:** `prompt_detail.html:76-77`
**Current:**
```django
"contentUrl": "{% if prompt.is_video %}{{ prompt.display_video_url }}{% else %}{{ prompt.display_large_url }}{% endif %}",
"thumbnailUrl": "{% if prompt.is_video %}...{% else %}{{ prompt.display_medium_url }}{% endif %}",
```
**Problem:** If media properties return `None`, Django renders the string `"None"` into JSON-LD, which Google will reject as an invalid URL.
**Fix:** Wrap in conditional guards or use `|default:""` filter.

#### 3. Hardcoded domain in JSON-LD vs dynamic canonical/og:url

**File:** `prompt_detail.html:82, 105, 111`
**Current:** `"url": "https://www.promptfinder.net{% url ... %}"`
**Problem:** Canonical URL (line 67) and og:url (line 25) use `request.get_host` (dynamic), but all JSON-LD URLs are hardcoded to `https://www.promptfinder.net`. On the Heroku staging domain, this creates a host mismatch that confuses crawlers.
**Impact:** Acceptable if promptfinder.net is the canonical production domain. Problematic if the site is still on the Heroku domain.

### MEDIUM Priority

| # | Issue | Details | Impact |
|---|-------|---------|--------|
| 4 | Missing `og:image:alt` | Accessibility for social platform screen readers | Low SEO, medium accessibility |
| 5 | Missing `twitter:image:alt` | Same as above for Twitter/X | Low SEO, medium accessibility |
| 6 | Missing `article:modified_time` | Helps crawlers detect freshly updated content | Low |
| 7 | BreadcrumbList last item missing `item` URL | More spec-compliant to include current page URL | Low |
| 8 | DNS prefetch targets outdated | Prefetches Cloudinary but not B2/Cloudflare CDN domain | Low performance |
| 9 | Missing `noindex` for draft prompts | Draft content could be indexed by search engines | Medium (if drafts are accessible) |

### LOW Priority

| # | Issue | Details |
|---|-------|---------|
| 10 | `floatformat:0` on `IntegerField` (video_duration) | Unnecessary but harmless |
| 11 | Hardcoded `1200x1200` assumes square aspect ratio | CSS `object-fit: contain` prevents visual issues, but browser reserves square space |
| 12 | Mixed icon systems (Font Awesome + Lucide SVG) | Two icon libraries loaded |

---

## Recommendations for 95+/100

### Tier 1: Fix HIGH Issues (~92/100)

1. **Swap filter order in BreadcrumbList** (1-line fix)
   ```django
   <!-- Before: -->
   "name": "{{ prompt.title|escapejs|truncatechars:50 }}"
   <!-- After: -->
   "name": "{{ prompt.title|truncatechars:50|escapejs }}"
   ```

2. **Guard JSON-LD contentUrl/thumbnailUrl** (add conditionals)
   ```django
   {% if prompt.is_video and prompt.display_video_url %}
   "contentUrl": "{{ prompt.display_video_url }}",
   {% elif prompt.display_large_url %}
   "contentUrl": "{{ prompt.display_large_url }}",
   {% endif %}
   ```

3. **Decide on domain strategy** for JSON-LD URLs:
   - If `promptfinder.net` is live: keep hardcoded (consistent canonical)
   - If still on Heroku: switch to dynamic `{{ request.scheme }}://{{ request.get_host }}`

### Tier 2: Add Missing Meta (~95/100)

4. Add `og:image:alt` and `twitter:image:alt` meta tags
5. Add `article:modified_time` meta tag
6. Add `item` URL to BreadcrumbList last item
7. Add `noindex` meta for draft prompts

### Tier 3: Polish (~97+/100)

8. Update DNS prefetch to target B2/Cloudflare CDN
9. Add `interactionStatistic` to JSON-LD (views, likes)
10. Store actual image dimensions in model for accurate width/height

---

## Projected Score After Fixes

| Fix Tier | Score Impact |
|----------|-------------|
| Current | 88/100 |
| After Tier 1 (HIGH fixes) | ~92/100 |
| After Tier 1 + Tier 2 | ~95/100 |
| After all tiers | ~97/100 |

---

## Next Steps

1. Implement Tier 1 fixes (3 HIGH issues) to pass 8+/10 threshold
2. Consider Tier 2 for pre-launch polish
3. Tier 3 can be deferred to post-launch optimization

---

**Report Version:** 1.0
**Generated:** February 3, 2026 (Session 66)
**Previous Report:** SEO_AUDIT_PROMPT_DETAIL_PAGE.md (Score: 72/100)
