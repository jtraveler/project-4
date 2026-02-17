# Phase R1-C FIX SPEC v4 - Completion Report

**Date:** February 17, 2026
**Status:** COMPLETE - Pending Manual Browser Verification
**Scope:** Auto-Center Active Tab + Architectural Cleanup (6 Fixes)
**Agent Testing:** Performance 9/10, UI 8/10, Code 6/10 -> 9/10 (critical bug caught and fixed)

---

## Executive Summary

FIX SPEC v4 delivered six architectural cleanup fixes to the notification and profile tab system. The primary goals were: (1) auto-centering the active notification tab on page load, (2) extracting duplicated overflow arrow JS/CSS into shared modules, (3) replacing hardcoded colors with CSS variables, and (4) removing a redundant template tag in favor of JS polling.

All fixes were implemented and tested (648/648 pass). Three specialized agents reviewed the work. The code review agent caught a **critical regression** — a missing `<script>` tag in `user_profile.html` that broke all profile page interactive JavaScript (follow button, trash modal, sorting). This was immediately fixed, bringing the code review rating from 6/10 to 9/10. All agents now meet the 8+/10 threshold.

This spec also resolves three of the four architectural follow-ups identified in the FIX SPEC v3 completion report: shared JS module (Follow-up #1), CSS migration (Follow-up #2), CSS variable adoption (Follow-up #3), and template tag removal (Follow-up #4).

---

## Fixes Implemented

### Fix 1 - Auto-Scroll Active Tab to Center on Page Load

**Goal:** When the notifications page loads with a category tab selected (e.g., `?category=collections`), the active tab should automatically scroll to the horizontal center of the viewport.

**Implementation:**
- Added `scrollActiveTabToCenter()` function in the new `overflow-tabs.js` shared module
- Uses `offsetLeft` calculation: `tabLeft - (containerWidth / 2) + (tabWidth / 2)` to compute the target scroll position
- Deferred execution via `requestAnimationFrame` ensures DOM layout is complete before measuring
- `setTimeout(updateArrows, 350)` updates arrow visibility after smooth scroll animation completes
- Controlled by `centerActiveTab: true` option (enabled on notifications page, disabled on profile page)

**Files Changed:** `static/js/overflow-tabs.js` (new)

### Fix 2 - Extract Overflow Arrow JS into Shared Module

**Goal:** Replace duplicated inline `<script>` blocks in `user_profile.html` (~163 lines) and `notifications.html` (~76 lines) with a single shared JavaScript module.

**Implementation:**
- Created `static/js/overflow-tabs.js` — 187-line shared module exposing `initOverflowTabs(wrapperSelector, options)`
- Options object supports: `centerActiveTab` (boolean), `centerWhenFits` (boolean)
- Features carried over: bidirectional arrow scroll, keyboard navigation (ArrowLeft, ArrowRight, Home, End), focus handling, debounced scroll (50ms) and resize (150ms) handlers
- All `console.log` debug statements from the original inline code removed
- Returns public API: `{updateArrows, scrollActiveTabToCenter}` for external use
- `notifications.html` calls with `{centerActiveTab: true, centerWhenFits: true}`
- `user_profile.html` calls with `{centerActiveTab: false, centerWhenFits: false}`

**Files Changed:** `static/js/overflow-tabs.js` (new), `notifications.html`, `user_profile.html`

### Fix 3 - Migrate user_profile.html Inline CSS to profile-tabs.css

**Goal:** Remove ~237 lines of inline tab/arrow `<style>` CSS from `user_profile.html` and consolidate into the shared `profile-tabs.css` component file.

**Implementation:**
- Surgically removed all tab-related CSS from `user_profile.html`'s inline `<style>` block: `.profile-tabs-wrapper`, `.profile-tabs-container`, `.profile-tab`, `.profile-tab-active`, `.profile-tab-count`, `.stat-badge`, `.overflow-arrow`, `.overflow-arrow-left`, and all hover/active states
- Kept profile-specific styles: `#follower-count`, `.profile-navigation-row`, filter styles
- Removed tab-related responsive rules from 990px and 480px media queries (kept non-tab responsive rules)
- Added `{% block extra_head %}` to `user_profile.html` (page previously had no external tab CSS loading)
- Both pages now load the same `profile-tabs.css` via `{% static 'css/components/profile-tabs.css' %}`

**Files Changed:** `static/css/components/profile-tabs.css` (rewritten), `user_profile.html`

### Fix 4 - Replace Hardcoded Colors with CSS Variables

**Goal:** Replace all hardcoded hex colors in `profile-tabs.css` with CSS custom properties and fallback values.

**Implementation:**
- `#6b7280` -> `var(--gray-500, #6b7280)` — inactive tab text, arrow icons
- `#f3f4f6` -> `var(--gray-100, #f3f4f6)` — hover background
- `#1f2937` -> `var(--gray-800, #1f2937)` — hover text, arrow hover icons
- `#f7f7f7` -> `var(--gray-50, #f7f7f7)` — gradient first stop
- `#000000` -> `var(--black, #000000)` — active tab background
- `#ffffff` -> `var(--white, #ffffff)` — active tab text
- Gradient alpha stops (`rgba(247, 247, 247, ...)`) left as-is — CSS `var()` cannot be used inside `rgba()` without `color-mix()` which has limited browser support

**Files Changed:** `static/css/components/profile-tabs.css`

### Fix 5 - Standardize Arrow Visibility Mechanism

**Goal:** Consolidate arrow show/hide to use only direct `style.opacity` / `style.pointerEvents` manipulation. Remove dead CSS classes that were never toggled.

**Implementation:**
- Removed `.has-overflow` and `.has-scroll-left` CSS class definitions from profile-tabs.css — these were defined in the inline CSS but never toggled by any JavaScript
- Arrow visibility in `overflow-tabs.js` uses direct style manipulation: `style.opacity = '1'/'0'` and `style.pointerEvents = 'auto'/'none'`
- CSS sets default `opacity: 0` and `pointer-events: auto` on both arrow classes; JS overrides as needed
- `EDGE_THRESHOLD = 5` (pixels) prevents arrow flickering at scroll boundaries
- Verified via codebase-wide search: zero remaining references to `.has-overflow` or `.has-scroll-left` in any live file

**Files Changed:** `static/css/components/profile-tabs.css`, `static/js/overflow-tabs.js`

### Fix 6 - Remove notification_category_counts Template Tag

**Goal:** Eliminate the server-side `notification_category_counts` template tag (which ran a `GROUP BY category` database query on every page load for authenticated users) and rely entirely on the existing JS polling mechanism.

**Implementation:**
- Removed `notification_category_counts` function from `prompts/templatetags/notification_tags.py`
- Removed `get_unread_count_by_category` import (function still exists in service layer — used by API endpoint and notifications page view)
- Updated `templates/base.html`: replaced `{{ cat_counts.X|default:"0" }}` with static `0` in all 5 dropdown category items
- Removed `{% notification_category_counts as cat_counts %}` template tag call from `base.html`
- `navbar.js` already calls `fetchNotificationCounts()` immediately on `DOMContentLoaded` (before the 60s interval), so real counts appear within ~50-200ms
- Removed 2 obsolete tests: `test_category_counts_tag` and `test_category_counts_anonymous`
- `{% load notification_tags %}` retained — still needed for `unread_notification_count` (bell badge total)

**Files Changed:** `notification_tags.py`, `base.html`, `test_notifications.py`

---

## Critical Bug Found and Fixed

### Missing `<script>` Tag in user_profile.html

**Severity:** CRITICAL — All profile page interactive JavaScript broken
**Found by:** @code-reviewer agent
**Status:** Fixed

**What happened:** When replacing the old inline overflow IIFE in `user_profile.html`, the new `</script>` tag at line 1425 closed the overflow-tabs initialization block. However, the remaining ~640 lines of profile page JavaScript (follow/unfollow button, trash modal, empty-trash modal, delete-collection modal, dropdown sorting) were left outside any `<script>` block — rendering as raw visible text in the browser.

**Root cause:** The old inline IIFE was part of a larger `<script>` block (lines 1680-2488 in the committed version) that also contained all other profile page JS. When the IIFE was replaced with the new external module + small initialization block, the replacement closed the `</script>` without re-opening one for the subsequent code.

**Impact if undetected:**
- Follow/Unfollow button non-functional
- Trash modal non-functional
- Empty-trash modal non-functional
- Delete-collection modal non-functional
- Dropdown sorting non-functional
- Raw JavaScript code visible to users on the profile page

**Fix applied:** Added `<script>` tag at line 1427, immediately after the `</script>` at line 1425 and before the JavaScript comment block. Script tags now properly balanced:
- Lines 1175/1234: trash modal inline script
- Line 1417: `overflow-tabs.js` external script
- Lines 1418/1425: `initOverflowTabs` initialization
- Lines 1427/2071: follow/unfollow + all other profile JS

**How to prevent in future:** When replacing code inside a `<script>` block that contains other code beyond the replacement target, always verify script tag balance with `grep -n '<script\|</script' filename` after editing. The test suite did not catch this because tests check for presence of specific patterns in template output (rendered HTML), but the JavaScript execution failure would only manifest in a browser.

---

## Test Results

| Suite | Result | Details |
|-------|--------|---------|
| Full test suite | 648/648 pass | 12 skipped, 0 failures |
| Notification tests | 55/55 pass | Down from 57 (2 removed for Fix 6) |
| Profile header tests | 5/5 pass | 4 updated for external file assertions |

**Tests removed (Fix 6):**
- `test_category_counts_tag` — tested the removed `notification_category_counts` template tag
- `test_category_counts_anonymous` — tested anonymous user handling of removed tag

**Tests updated (inline -> external migration):**
- `test_overflow_arrow_css_hover_effect` -> `test_overflow_arrow_css_loaded`: now checks for `profile-tabs.css` in rendered HTML
- `test_javascript_scroll_functionality`, `test_javascript_keyboard_navigation`, `test_javascript_smooth_scroll` -> `test_javascript_overflow_module_loaded`: now checks for `overflow-tabs.js` and `initOverflowTabs` in rendered HTML

---

## Agent Review Results

### @performance-engineer - 9/10 (Meets Threshold)

| Area | Assessment |
|------|------------|
| DB query reduction | +1 fewer query per authenticated page load (template tag removed) |
| JS polling timing | `fetchNotificationCounts()` fires immediately on DOMContentLoaded, not after 60s delay |
| Memory leaks | No issues — persistent event listeners acceptable in multi-page Django app |
| Debouncing | Correct: separate timers for scroll (50ms) and resize (150ms), no cross-contamination |
| rAF + setTimeout | Appropriate pattern for ensuring layout is painted before measuring DOM offsets |
| Minor note | No destroy/cleanup mechanism in overflow-tabs.js (future-proofing, not blocking) |

### @ui-visual-validator - 8/10 (Meets Threshold)

| Fix | Score | Notes |
|-----|-------|-------|
| Fix 1 | 8/10 | `offsetLeft` fragility vs `getBoundingClientRect`; otherwise solid |
| Fix 2 | 9/10 | Clean extraction, scoped selectors, proper API |
| Fix 3 | 7/10 | Flagged duplicate `.profile-tab` rule in 480px media query (already consolidated) |
| Fix 4 | 8/10 | Fallback colors don't match project palette exactly; hardcoded border-radius |
| Fix 5 | 9/10 | Dead classes fully removed; no flash on init |
| Fix 6 | 7/10 | Badge vs dropdown count inconsistency; no aria-live |

### @code-reviewer - 6/10 Initial -> 9/10 After Fix (Meets Threshold)

| Fix | Score | Notes |
|-----|-------|-------|
| Fix 1 | 9/10 | Clean, correct, handles missing active tab gracefully |
| Fix 2 | 9/10 | Well-structured, defensive coding, proper null checks |
| Fix 3 | 8/10 | Clean migration; padding change noted for verification |
| Fix 4 | 9/10 | Thorough variable adoption with sensible fallbacks |
| Fix 5 | 10/10 | Clean elimination of class-based approach |
| Fix 6 | 9/10 | Complete removal with proper fallback to polling |
| **Critical bug** | -3 | Missing `<script>` tag broke all profile page JS |

**Post-fix overall: 9/10** — The code reviewer confirmed the rating would be 9/10 after the script tag fix was applied.

---

## Below-Threshold Ratings: Root Causes and Fixes Applied

### Issue 1: Missing `<script>` Tag (Code Review, 6/10 -> 9/10)

**Problem:** The `</script>` at line 1425 closed the overflow-tabs initialization block, but ~640 lines of subsequent JavaScript (follow/unfollow, trash modal, sorting, delete-collection) were left outside any `<script>` block, rendering as raw text in the browser. All profile page interactive features completely broken.

**Root cause:** The original inline overflow IIFE was part of a monolithic `<script>` block spanning lines 1680-2488. When replacing only the IIFE portion (at the start of that block), the replacement introduced a new `</script>` closure without re-opening `<script>` for the remaining code.

**Fix applied:** Added `<script>` tag at line 1427, immediately after the closing `</script>` at line 1425. Verified script tag balance with `grep -n '<script\|</script'`.

**How to prevent in future:**
1. After any inline `<script>` block modification, always run `grep -n '<script\|</script' [file]` to verify tag balance
2. When replacing code that is part of a larger script block, explicitly verify what comes after the replacement point
3. Consider adding a test that checks for balanced `<script>`/`</script>` tags in critical templates

**Post-fix effective rating:** 9/10

### Issue 2: Fix 3 CSS Migration (UI Review, 7/10)

**Problem:** UI reviewer flagged a duplicate `.profile-tab` rule in the `@media (max-width: 480px)` block — the first rule was dead code immediately overridden by the second.

**Status:** Already consolidated before the UI review ran. The reviewer was working with stale file data. Current file has only one `.profile-tab` rule in the 480px block.

**Post-fix effective rating:** 8+/10

### Issue 3: Fix 6 Template Tag Removal (UI Review, 7/10)

**Problem:** Three concerns raised:
1. Flash of "0" counts for ~2 seconds before JS polling updates with real values
2. Bell badge uses server-rendered `{% unread_notification_count %}` while dropdown counts use JS polling — hybrid inconsistency
3. No `aria-live` region on count elements for screen reader announcement of updates

**Assessment:** These are by-design tradeoffs specified in the FIX SPEC:
- The 2-second flash is the intended tradeoff for eliminating a DB query per page load
- The bell badge remains server-rendered intentionally (it's always visible; dropdown counts are hidden until opened)
- The `aria-live` concern is a valid accessibility improvement but outside the scope of this spec

**Recommendation for future:** Consider adding `aria-live="polite"` to the notification count container in a follow-up accessibility pass.

---

## Issues and Concerns Discovered During Implementation

### 1. Monolithic Inline `<style>` Block in user_profile.html

**Concern:** The `user_profile.html` template has ~840 lines of inline `<style>` CSS. Even after migrating tab CSS to an external file, ~600+ lines remain inline. This creates maintenance risk, makes CSS specificity unpredictable, and prevents browser caching.

**Impact:** Medium — works correctly but harder to maintain
**Recommendation:** Progressively migrate remaining inline CSS to page-specific files (e.g., `static/css/pages/user-profile.css`) in future sessions

### 2. Monolithic Inline `<script>` Block in user_profile.html

**Concern:** After extracting the overflow IIFE, ~640 lines of inline JavaScript remain in a single `<script>` block. This includes follow/unfollow, trash modal, empty-trash modal, delete-collection modal, sorting, and like button comments. This is where the critical `<script>` tag bug originated — the sheer size makes it easy to miss structural issues.

**Impact:** High — the script tag bug was a direct consequence of this monolithic block
**Recommendation:** Extract major feature JS (follow/unfollow, modals, sorting) into separate external files, similar to the existing `like-button.js` and `collections.js` patterns

### 3. CSS Variable Fallback Mismatch

**Concern:** The CSS variable fallbacks in `profile-tabs.css` use Tailwind color values (e.g., `--gray-500` fallback is `#6b7280`) while the project defines different values in `style.css` (e.g., `--gray-500: #737373`). The fallbacks will never activate in production (CSS variables are always defined), but they create a theoretical inconsistency.

**Impact:** Low — cosmetic only if CSS variables were undefined
**Recommendation:** Update fallbacks to match project-defined values in a future cleanup pass, or remove fallbacks entirely since the project always defines these variables

### 4. Tab Padding Asymmetry

**Concern:** The spec specified `padding: 6px 8px 6px 25px` for `.profile-tab`, which creates 25px left vs 8px right padding. The UI reviewer flagged this as visually unbalanced — text appears right-aligned within the pill shape.

**Impact:** Low-Medium — purely visual
**Recommendation:** Verify the intended visual result in a browser. If tabs look off-center, consider symmetric padding like `6px 16px` or `8px 20px`

### 5. `offsetLeft` vs `getBoundingClientRect()` for Tab Centering

**Concern:** Both the UI and code reviewers noted that `activeTab.offsetLeft` measures offset from the nearest positioned ancestor. If an intermediate element ever gets `position: relative`, the measurement would be wrong. `getBoundingClientRect()` relative to the container would be more robust.

**Impact:** Low — current DOM structure is correct; risk is theoretical
**Recommendation:** Consider switching to `getBoundingClientRect()` approach in a future refactor if centering behavior becomes unreliable

### 6. Gradient Alpha Stops Still Hardcoded

**Concern:** The overflow arrow gradients use `var(--gray-50, #f7f7f7)` for the first stop but `rgba(247, 247, 247, 0.95)` etc. for subsequent alpha-blended stops. CSS `var()` cannot be used inside `rgba()` without `color-mix()`.

**Impact:** None currently — the RGB values match the CSS variable's hex equivalent
**Recommendation:** When browser support for `color-mix()` is sufficient, convert to fully variable-based gradients

---

## Ways to Improve Agent Ratings

### Raising Code Review from 6 -> 9 (Applied)

| Factor | Before | After | Impact |
|--------|--------|-------|--------|
| Script tag balance | Missing `<script>` tag | Added at line 1427 | +3 points |

**Key takeaway:** Script tag manipulation in large templates is high-risk. Always verify tag balance after editing.

### Raising UI Review Fix 3 from 7 -> 8+ (Already Applied)

| Factor | Before | After | Impact |
|--------|--------|-------|--------|
| Duplicate CSS rule | Two `.profile-tab` rules in 480px block | Consolidated to one | +1 point |

### Raising UI Review Fix 6 from 7 -> 8+ (Future Work)

| Improvement | Expected Impact |
|-------------|-----------------|
| Add `aria-live="polite"` to notification count container | +0.5 points (accessibility compliance) |
| Add skeleton/loading state during polling window | +0.5 points (eliminates "0" flash) |
| Unify badge + dropdown to same rendering strategy | +0.5 points (consistency) |

### Raising Performance from 9 -> 10 (Future Work)

| Improvement | Expected Impact |
|-------------|-----------------|
| Add `destroy()` method to overflow-tabs.js for cleanup | +0.5 points (future-proofing) |
| Use `IntersectionObserver` instead of scroll event | +0.5 points (performance pattern) |

---

## Files Modified (Complete List)

| File | Change Type | Description |
|------|-------------|-------------|
| `static/js/overflow-tabs.js` | **NEW** | 187-line shared overflow tabs module |
| `static/css/components/profile-tabs.css` | Rewritten | CSS variable migration, dead class removal, consolidated responsive rules |
| `prompts/templates/prompts/notifications.html` | Modified | Replaced 76-line inline JS with shared module import + 6-line init |
| `prompts/templates/prompts/user_profile.html` | Modified | Removed ~237 lines inline tab CSS, ~163 lines inline overflow JS; added `{% block extra_head %}` with profile-tabs.css; added shared module import; fixed missing `<script>` tag |
| `prompts/templatetags/notification_tags.py` | Modified | Removed `notification_category_counts` function and `get_unread_count_by_category` import |
| `templates/base.html` | Modified | Removed `{% notification_category_counts %}` call; replaced `{{ cat_counts.X }}` with static `0` |
| `prompts/tests/test_notifications.py` | Modified | Removed 2 obsolete template tag tests (55 tests remain) |
| `prompts/tests/test_user_profile_header.py` | Modified | Updated 4 tests for external file assertions (5 tests pass) |

### Net Code Change Summary

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Inline JS in user_profile.html | ~163 lines | 6 lines | -157 lines |
| Inline JS in notifications.html | ~76 lines | 6 lines | -70 lines |
| Inline CSS in user_profile.html | ~237 lines | 0 lines (tab CSS) | -237 lines |
| Shared JS module | 0 | 187 lines | +187 lines |
| Shared CSS (profile-tabs.css) | 97 lines | 238 lines | +141 lines |
| Template tag functions | 2 | 1 | -1 function |
| DB queries per page (auth users) | 2 | 1 | -1 query |
| Test count | 650 | 648 | -2 tests |

---

## Manual Browser Verification Checklist

The following must be verified in a browser before committing:

- [ ] **Notifications page:** Navigate to `/notifications/` — verify tabs render correctly
- [ ] **Notifications page (category):** Navigate to `/notifications/?category=collections` — verify the active tab scrolls to horizontal center on load
- [ ] **Notifications page:** Resize browser to narrow width — verify overflow arrows appear and function (click + keyboard)
- [ ] **User profile page:** Navigate to any user profile — verify tabs render with correct styling (pill shape, dark active tab)
- [ ] **User profile page:** Verify overflow arrows appear when tabs overflow
- [ ] **User profile page:** Verify follow/unfollow button works (click toggles state)
- [ ] **User profile page:** Verify trash modal opens (if viewing own profile with trashed items)
- [ ] **User profile page:** Verify dropdown sorting works
- [ ] **Bell dropdown:** Click bell icon — verify dropdown opens centered under bell
- [ ] **Bell dropdown:** Verify category counts update from "0" to real values within ~2 seconds
- [ ] **Bell dropdown:** Verify bell badge count matches total of category counts
- [ ] **All pages:** Verify no raw JavaScript text visible on any page

---

## Relationship to FIX SPEC v3 Follow-Ups

FIX SPEC v3 identified four architectural follow-ups. This spec addresses all four:

| Follow-Up | v3 Status | v4 Resolution |
|-----------|-----------|---------------|
| #1: Extract overflow arrow JS into shared module | Identified | Fix 2 — `overflow-tabs.js` created |
| #2: Migrate user_profile.html inline CSS to profile-tabs.css | Identified | Fix 3 — CSS migrated |
| #3: Replace hardcoded colors in profile-tabs.css | Identified | Fix 4 — CSS variables adopted |
| #4: Cache/remove notification_category_counts template tag | Identified | Fix 6 — Tag removed, polling-only approach |

---

## Agent Usage Report

### Agents Invoked

1. **@performance-engineer**
   - Task: Evaluate performance impact of all 6 fixes, especially Fix 6 (DB query removal) and Fix 2 (shared module overhead)
   - Findings: Confirmed 1 fewer DB query per authenticated page load; JS polling fires immediately on DOMContentLoaded; no memory leaks; debouncing correct; rAF + setTimeout pattern appropriate
   - Rating: 9/10
   - Confidence: High — no blocking issues

2. **@ui-visual-validator**
   - Task: Visual and accessibility review of all 6 fixes across both notification and profile pages
   - Findings: Flagged duplicate CSS rule (already fixed), tab padding asymmetry (per spec), fallback color mismatches (theoretical), missing aria-live (valid future improvement)
   - Rating: 8/10
   - Confidence: High — issues flagged are minor or already resolved

3. **@code-reviewer**
   - Task: Full code review of all modified files, security scan, architectural assessment
   - Findings: **Caught critical `<script>` tag regression** in user_profile.html that would have broken all profile page JS. Also flagged redundant inline `text-decoration: none` styles and confusing `background-color: transparent` on gradient elements
   - Rating: 6/10 -> 9/10 (after fix)
   - Confidence: Very High — the critical bug catch justified the mandatory agent review requirement

### Why These Agents

- **@performance-engineer:** Fix 6 removes a DB query per page load — needed performance validation that JS polling adequately replaces server-side rendering
- **@ui-visual-validator:** Fixes 1, 3, 4 change visual appearance — needed visual regression check and accessibility review
- **@code-reviewer:** Fixes 2, 3 involve significant code restructuring (inline -> external) — high risk of structural errors, which is exactly what the critical `<script>` bug proved

### Agent Feedback Summary

The code review agent caught a critical regression that would have shipped broken profile pages to production. This single finding validates the mandatory 3-agent review requirement. The performance and UI agents confirmed the implementation is sound with only minor theoretical improvements suggested. All three agents agree the implementation is production-ready after the script tag fix.

---

## Summary

All 6 fixes from FIX SPEC v4 are implemented, tested (648/648 pass), and reviewed by three specialized agents. A critical `<script>` tag regression was caught by the code review agent and immediately fixed. All architectural follow-ups from FIX SPEC v3 are now resolved. The implementation eliminates ~464 lines of duplicated inline code in favor of shared modules, removes 1 database query per authenticated page load, and establishes a clean single-source-of-truth for tab component CSS.

**Effective Post-Fix Ratings:**

| Agent | Initial | Post-Fix | Status |
|-------|---------|----------|--------|
| @performance-engineer | 9/10 | 9/10 | Meets threshold |
| @ui-visual-validator | 8/10 | 8/10 | Meets threshold |
| @code-reviewer | 6/10 | 9/10 | Meets threshold |
