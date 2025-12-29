# MICRO-SPEC #11.1 INVESTIGATION REPORT
## Collections Profile Page UI/UX Audit

**Date:** December 28, 2025
**Investigator:** Claude Code
**File Under Investigation:** `prompts/templates/prompts/collections_profile.html`
**Reference File:** `prompts/templates/prompts/user_profile.html` (Gallery page)
**Total Lines:** 784

---

## SUMMARY TABLE

| Issue # | Description | Status | Priority | Fix Complexity |
|---------|-------------|--------|----------|----------------|
| #1 | Header missing "Member since" + social icons | **BROKEN** | High | Low |
| #2 | Sort dropdown wrong classes | **OK** | - | - |
| #3 | Collections grid wrong spacing | **NEEDS VERIFY** | Medium | Low |
| #4 | Thumbnail aspect ratio | **NEEDS VERIFY** | Medium | Medium |
| #5 | Create button wrong styling | **BROKEN** | High | Low |
| #6 | Create uses modal not overlay | **BROKEN** | High | Medium |
| #7 | Missing hover overlay on collection cards | **PARTIAL** | Low | Low |

---

## INVESTIGATION COMMANDS EXECUTED

### Command 1: Profile Header Check
```bash
grep -n "profile-header\|profile-avatar\|Member since\|social" prompts/templates/prompts/collections_profile.html | head -30
```

**Output:**
```
19:.profile-header-wrapper {
26:.profile-identity {
33:.profile-avatar-container {
39:.profile-avatar {
45:.profile-avatar-placeholder {
452:.profile-header-wrapper
```

**Finding:** Found profile-avatar and profile-header-wrapper classes but NO "Member since" or "social" matches.

---

### Command 2: Sort Dropdown Classes Check
```bash
grep -n "profile-sort-dropdown\|sort-dropdown\|dropdown-menu" prompts/templates/prompts/collections_profile.html
```

**Output:**
```
233:    <div class="profile-sort-dropdown" id="sortDropdown">
234:        <button class="profile-sort-dropdown-btn" id="sortDropdownBtn" ...>
241:        <div class="profile-sort-dropdown-menu">
243:                <button class="profile-sort-dropdown-item {% if sort_order == 'recent' %}active{% endif %}" ...>
247:                <button class="profile-sort-dropdown-item {% if sort_order == 'most' %}active{% endif %}" ...>
251:                <button class="profile-sort-dropdown-item {% if sort_order == 'fewest' %}active{% endif %}" ...>
```

**Finding:** Uses CORRECT classes: `.profile-sort-dropdown`, `.profile-sort-dropdown-btn`, `.profile-sort-dropdown-menu`, `.profile-sort-dropdown-item`

---

### Command 3: Create Button Location & Styling Check
```bash
grep -n "btn-create\|Create.*Collection\|btn-outline-standard" prompts/templates/prompts/collections_profile.html
```

**Output:**
```
616:<button type="button" class="btn-create-collection" data-action="show-create-form" id="openCreateCollectionBtn">
620:    Create New Collection
726:                Create Your First Collection
```

**Finding:** Button uses `.btn-create-collection` instead of `.btn-outline-standard`. This creates inconsistent styling with the rest of the site.

---

### Command 4: Modal vs Overlay Pattern Check
```bash
grep -n "modal\|overlay\|data-bs-toggle\|include.*collection" prompts/templates/prompts/collections_profile.html
```

**Output:**
```
737:{% include 'prompts/partials/_collection_modal.html' %}
```

**Finding:** Uses modal pattern (includes `_collection_modal.html`) instead of overlay on grid.

---

### Command 5: File Structure Overview
```bash
wc -l prompts/templates/prompts/collections_profile.html
head -80 prompts/templates/prompts/collections_profile.html
tail -40 prompts/templates/prompts/collections_profile.html
```

**Output (Line Count):** 784 lines

**First 80 Lines Summary:**
- Lines 1-5: Template extends, loads
- Lines 6-12: Title block, CSRF token
- Lines 13-80: Inline CSS copied from user_profile.html (profile header styles)

**Last 40 Lines Summary:**
- Sort dropdown JavaScript event handlers
- Create collection button opens CollectionsModal
- Script closes, endblock

---

### Command 6: Compare to Gallery Page Header
```bash
grep -n "profile-header\|Member since\|social\|profile-tabs\|profile-filters" prompts/templates/prompts/user_profile.html | head -50
```

**Output:**
```
17:.profile-header-wrapper {
174:.profile-tabs-wrapper {
182:.profile-tabs-container {
408:.profile-filters-container {
840:<div class="profile-header-wrapper">
871:            Member since {{ profile.created_at|date:"F Y" }}
881:            <div class="profile-social-links" style="display: flex; gap: 12px; justify-content: center; margin-top: 16px;">
883:                    <a href="{{ profile.twitter_url }}" target="_blank" rel="noopener noreferrer" class="social-link" style="color: #1DA1F2; font-size: 24px;" title="Twitter">
889:                    <a href="{{ profile.instagram_url }}" target="_blank" rel="noopener noreferrer" class="social-link" style="color: #E4405F; font-size: 24px;" title="Instagram">
895:                    <a href="{{ profile.website_url }}" target="_blank" rel="noopener noreferrer" class="social-link" style="color: #6b7280; font-size: 24px;" title="Website">
955:        <div class="profile-tabs-wrapper">
962:            <div class="profile-tabs-container">
1007:        <div class="profile-filters-container">
```

**Finding:** Gallery page has:
- Line 871: `Member since {{ profile.created_at|date:"F Y" }}`
- Line 881-895: Social links (Twitter, Instagram, Website)

Collections page is MISSING both of these elements.

---

### Command 7: Check Hover Overlay CSS
```bash
grep -n "collection-card.*hover\|\.collection-card:hover\|overlay\|rgba" static/css/style.css | grep -i "collection"
```

**Output:**
```
94:  --collection-overlay-saved: rgba(22, 163, 74, 0.75);   /* Green - saved state */
95:  --collection-overlay-remove: rgba(239, 68, 68, 0.75);  /* Red - hover to remove */
96:  --collection-overlay-add: rgba(0, 0, 0, 0.6);          /* Dark - hover to add */
3252:.collection-card-overlay {
3269:.collection-card-overlay .icon {
3292:.collection-card:not(.has-prompt):not(.collection-card-create) .collection-card-thumbnail:hover .collection-card-overlay {
3295:    background-color: var(--collection-overlay-add);
3310:.collection-card.has-prompt .collection-card-overlay {
3313:    background-color: var(--collection-overlay-saved);
3322:.collection-card.has-prompt .collection-card-thumbnail:hover .collection-card-overlay {
3323:    background-color: var(--collection-overlay-remove);
3349:/* Simple dimmed overlay on hover for profile page collection cards */
3363:.collection-card-link:hover .collection-card-thumbnail::after {
```

**Finding:** CSS for hover overlay EXISTS in style.css (lines 3349-3363). If overlays are not appearing, the issue is likely in the template HTML structure.

---

## DETAILED FINDINGS

### Issue #1: Profile Header Missing Elements
**Status:** ❌ BROKEN

**Evidence:**
- Collections page header grep shows NO "Member since" or "social" matches
- Gallery page (user_profile.html) has these at lines 871, 881-895
- Header was copied incompletely from user_profile.html

**Missing Elements:**
1. "Member since" text with join date
2. Social media icons (Twitter, Instagram, Website)

**Root Cause:** Incomplete copy of header section from Gallery page template.

---

### Issue #2: Sort Dropdown Wrong Classes
**Status:** ✅ OK

**Evidence:**
- Uses correct classes: `.profile-sort-dropdown`, `.profile-sort-dropdown-btn`, `.profile-sort-dropdown-menu`, `.profile-sort-dropdown-item`
- Matches expected styling pattern

**Diagnosis:** Sort dropdown is correctly styled. No fix needed.

---

### Issue #3: Collections Grid Wrong Spacing
**Status:** ⚠️ NEEDS VISUAL VERIFICATION

**Evidence:**
- Inline styles copy profile header CSS (first 80 lines)
- No explicit grid container CSS visible in first 80 lines
- Cannot determine grid gap/spacing from grep alone

**Diagnosis:** Requires visual inspection or reading the full grid section of the template.

---

### Issue #4: Thumbnail Aspect Ratio Wrong
**Status:** ⚠️ NEEDS VISUAL VERIFICATION

**Evidence:**
- Collection card hover overlay CSS exists in style.css
- Line 3349: "Simple dimmed overlay on hover for profile page collection cards"
- Aspect ratio cannot be verified from grep commands

**Diagnosis:** Requires visual inspection to confirm thumbnail proportions.

---

### Issue #5: Create Button Wrong Styling
**Status:** ❌ BROKEN

**Evidence from Command 3:**
```html
<button type="button" class="btn-create-collection" data-action="show-create-form">
    <svg class="icon" aria-hidden="true">
        <use href="{% static 'icons/sprite.svg' %}#icon-circle-plus"></use>
    </svg>
    Create New Collection
</button>
```

**Expected Pattern (from prompt_detail.html):**
```html
class="btn-outline-standard action-icon-btn"
```

**Root Cause:** Button uses custom `.btn-create-collection` class instead of standard `.btn-outline-standard` pattern used throughout the site.

---

### Issue #6: Create Uses Modal Instead of Overlay
**Status:** ❌ BROKEN (Architectural Mismatch)

**Evidence from Command 4:**
```
collections_profile.html:737: {% include 'prompts/partials/_collection_modal.html' %}
```

**Evidence from JavaScript (last 40 lines):**
```javascript
const createBtns = document.querySelectorAll('[data-action="show-create-form"]');
createBtns.forEach(function(btn) {
    btn.addEventListener('click', function() {
        if (typeof CollectionsModal !== 'undefined') {
            CollectionsModal.open();
            // ...
        }
    });
});
```

**Diagnosis:** Collections Profile page uses a **modal pattern** for creating new collections. The spec stated it should use an **overlay on the grid** (like the "Create new collection" card in the modal itself).

**Note:** This is an architectural decision that may need user confirmation before changing.

---

### Issue #7: Missing Hover Overlay on Collection Cards
**Status:** ⚠️ PARTIAL (CSS Exists)

**Evidence from Command 7:**
```css
/* Lines 3349-3363 in style.css */
/* Simple dimmed overlay on hover for profile page collection cards */
.collection-card-link:hover .collection-card-thumbnail::after {
    /* overlay styles exist */
}
```

**Diagnosis:** CSS for hover overlay EXISTS in style.css. If overlays are not appearing, the issue is likely:
1. Missing `::after` pseudo-element in HTML structure
2. Missing CSS class on collection cards in template
3. Template may not use `.collection-card-link` wrapper

---

## ADDITIONAL VERIFICATION: Missing Header Elements

**Grep for specific missing elements:**
```bash
grep -n "Member since\|profile-social\|social-link\|created_at" prompts/templates/prompts/collections_profile.html
```

**Output:** No matches found

**Conclusion:** Collections profile page is definitively missing:
- "Member since" date display
- Social media links section

---

## RECOMMENDATIONS

### Immediate Fixes (Low Effort, High Impact)

#### 1. Issue #1 - Add Missing Header Elements
**Priority:** High
**Effort:** 20 minutes
**Action:** Copy from user_profile.html (lines 871-895):
- "Member since" section
- Social links section with Twitter, Instagram, Website icons

#### 2. Issue #5 - Fix Button Class
**Priority:** High
**Effort:** 5 minutes
**Action:** Change:
```html
class="btn-create-collection"
```
To:
```html
class="btn-outline-standard action-icon-btn"
```

### Medium Effort Fixes

#### 3. Issue #6 - Modal vs Overlay Pattern
**Priority:** Medium
**Effort:** 2-4 hours
**Options:**
- **Option A:** Keep modal pattern (current) - requires no changes
- **Option B:** Convert to overlay pattern - significant JS/template rework

**Recommendation:** Get user decision on which pattern is preferred before implementing.

#### 4. Issue #7 - Verify Hover Overlay
**Priority:** Low
**Effort:** 30 minutes
**Action:**
- Check if collection cards use `.collection-card-link` wrapper
- Verify `::after` pseudo-element structure matches CSS expectations
- Add wrapper class if missing

### Visual Verification Needed

#### 5. Issues #3 & #4 - Grid Spacing & Aspect Ratio
**Priority:** Medium
**Effort:** Browser testing required
**Action:** Cannot fully diagnose from grep commands alone. Requires:
- Browser testing at various viewport widths
- Comparison screenshots vs Gallery page

---

## FILES TO MODIFY

| File | Changes Needed | Priority |
|------|----------------|----------|
| `collections_profile.html` | Add Member since, social links, fix button class | High |
| `static/css/style.css` | Possibly add/modify collection card styles | Low |

---

## NEXT STEPS

1. **User Decision Required:** Modal vs Overlay pattern for Create functionality (Issue #6)
2. **Visual Testing Required:** Issues #3, #4, #7 need browser verification
3. **Create Micro-Spec #11.2:** Implementation spec for confirmed fixes

---

## APPENDIX: Raw Command Outputs

All command outputs are documented in the findings sections above.

---

**Report Complete.**

*Generated by Micro-Spec #11.1 Investigation Protocol*
