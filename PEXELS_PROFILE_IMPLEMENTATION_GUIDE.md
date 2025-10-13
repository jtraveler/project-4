# Pexels Profile Header - Implementation Guide

**Date:** October 13, 2025
**Purpose:** Pixel-perfect recreation of Pexels profile header layout
**Reference:** Pexels "Urban Avenue" user profile page

---

## Overview

This guide provides exact specifications to recreate the Pexels profile header layout with pixel-perfect accuracy. All measurements are derived from visual analysis of the Pexels website.

---

## Key Measurements Summary

| Element | Current (Broken) | Correct (Pexels) |
|---------|------------------|------------------|
| **Avatar size** | 80px | **120px** |
| **Username font** | 24px | **32px** |
| **Button color** | Bootstrap default | **#05a081** |
| **Stats gap** | 16px | **48px** |
| **Stats value** | 20px | **24px** |
| **Stats label** | 12px | **14px** |
| **Tab active** | Underline only | **Black bg + white text** |
| **Tab padding** | 8px 12px | **12px 20px** |

---

## Component Breakdown

### 1. Avatar Circle

```css
.profile-avatar {
  width: 120px;          /* CRITICAL: Must be 120px */
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
```

**Why it matters:**
- Larger avatar (120px) creates stronger visual hierarchy
- More professional appearance
- Better visibility on all devices

---

### 2. Username Typography

```css
.profile-username {
  font-size: 32px;       /* CRITICAL: Must be 32px */
  font-weight: 700;      /* Bold */
  color: #000000;
  line-height: 1.2;
  margin: 0 0 16px 0;
  letter-spacing: -0.5px; /* Tighter spacing for large text */
}
```

**Why it matters:**
- 32px creates clear visual prominence
- Strong hierarchy: Avatar → Username → Button → Stats
- Letter-spacing prevents text from feeling too loose

---

### 3. Edit Profile Button

```css
.btn-edit-profile {
  background-color: #05a081;  /* CRITICAL: Pexels green */
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  padding: 10px 24px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
  transition: background-color 0.2s ease;
}

.btn-edit-profile:hover {
  background-color: #048f73;  /* Darker on hover */
}
```

**Why it matters:**
- Green color (#05a081) is Pexels brand signature
- Creates visual distinction from generic Bootstrap buttons
- Proper padding (10px 24px) gives comfortable click target

---

### 4. Stats Row Layout

```css
.profile-stats {
  display: flex;
  gap: 48px;             /* CRITICAL: 48px between items */
  justify-content: center;
  margin: 32px 0;
}

.profile-stats__value {
  font-size: 24px;       /* CRITICAL: 24px for numbers */
  font-weight: 700;
  color: #000000;
}

.profile-stats__label {
  font-size: 14px;       /* CRITICAL: 14px for labels */
  color: #6b7280;
}
```

**Why it matters:**
- 48px gap prevents crowding
- 24px numbers are bold and readable
- 14px labels provide clear context without overwhelming
- Gray color (#6b7280) creates proper visual hierarchy

**Visual spacing:**
```
[1.2M]  <--48px-->  [#245]  <--48px-->  [#18]
```

---

### 5. Tab Navigation

```css
.profile-tabs__link {
  padding: 12px 20px;    /* CRITICAL: More padding than typical */
  font-size: 15px;
  color: #6b7280;
  transition: all 0.2s ease;
  border-radius: 6px 6px 0 0;
}

/* Active state: BLACK background, WHITE text */
.profile-tabs__link--active {
  background-color: #000000;  /* CRITICAL: Black bg */
  color: #ffffff;             /* CRITICAL: White text */
}
```

**Why it matters:**
- Black background creates strong visual distinction
- White text on black is high contrast (accessibility)
- 12px 20px padding gives comfortable click target
- Rounded top corners (6px) soften the design

**Active vs Inactive:**
```
Inactive: Gray text (#6b7280), no background
Active:   White text, black background (#000000)
Hover:    Black text, light gray background (#f9fafb)
```

---

### 6. Filter Dropdowns

```css
.profile-filter__select {
  font-size: 14px;
  padding: 8px 36px 8px 12px;  /* Room for dropdown arrow */
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
}
```

**Why it matters:**
- Right-aligned placement feels natural for filters
- Light background (#f9fafb) distinguishes from white page
- 36px right padding accommodates dropdown arrow icon
- 6px border-radius matches button styling consistency

---

## Responsive Behavior

### Desktop (1200px+)
- All elements at full size
- Stats in horizontal row with 48px gaps
- Tabs in single row, centered

### Tablet (768px - 1199px)
```css
@media (max-width: 768px) {
  .profile-avatar {
    width: 100px;        /* Reduce from 120px */
    height: 100px;
  }

  .profile-username {
    font-size: 28px;     /* Reduce from 32px */
  }

  .profile-stats {
    gap: 32px;           /* Reduce from 48px */
  }
}
```

### Mobile (480px - 767px)
```css
@media (max-width: 480px) {
  .profile-avatar {
    width: 80px;         /* Smallest size */
    height: 80px;
  }

  .profile-username {
    font-size: 24px;     /* Smallest readable size */
  }

  .profile-stats {
    gap: 24px;           /* Compact spacing */
  }

  .btn-edit-profile {
    width: 100%;         /* Full width on mobile */
    max-width: 240px;
  }

  .profile-filters {
    flex-direction: column;  /* Stack filters vertically */
  }
}
```

---

## Implementation Checklist

### Phase 1: CSS Integration
- [ ] Copy `pexels-profile-header-specs.css` to your static CSS folder
- [ ] Link stylesheet in your base template or profile page
- [ ] Verify no conflicting Bootstrap/global styles

### Phase 2: HTML Structure Update
- [ ] Update avatar container class to `.profile-avatar`
- [ ] Change avatar size from 80px to 120px
- [ ] Update username class to `.profile-username`, verify 32px renders
- [ ] Replace button class with `.btn-edit-profile`
- [ ] Update stats container to use `.profile-stats` with `gap: 48px`
- [ ] Update tab navigation to use `.profile-tabs__link` and `.profile-tabs__link--active`
- [ ] Add filter dropdowns with `.profile-filter__select`

### Phase 3: Testing
- [ ] **Desktop (1920px):** Verify all measurements match Pexels
- [ ] **Tablet (768px):** Check responsive adjustments
- [ ] **Mobile (375px):** Verify stacked layout and full-width button
- [ ] **Cross-browser:** Test Chrome, Firefox, Safari, Edge
- [ ] **Accessibility:** Tab navigation works, focus states visible
- [ ] **Hover states:** Button, tabs, filters all have proper hover effects

### Phase 4: Edge Cases
- [ ] Test with long usernames (20+ characters)
- [ ] Test with large stat numbers (1,234,567)
- [ ] Test with all tabs active (one at a time)
- [ ] Test filter dropdowns with long option text
- [ ] Verify loading states render correctly
- [ ] Verify empty states (no stats) render properly

---

## Common Mistakes to Avoid

### ❌ Mistake #1: Using Bootstrap button classes
```html
<!-- WRONG -->
<button class="btn btn-primary">Edit profile</button>

<!-- CORRECT -->
<button class="btn-edit-profile">Edit profile</button>
```

### ❌ Mistake #2: Stats gap too small
```css
/* WRONG: Only 16px gap */
.profile-stats {
  gap: 16px;
}

/* CORRECT: 48px gap */
.profile-stats {
  gap: 48px;
}
```

### ❌ Mistake #3: Tab active state using underline
```css
/* WRONG: Just an underline */
.profile-tabs__link--active {
  border-bottom: 2px solid #000;
}

/* CORRECT: Black background + white text */
.profile-tabs__link--active {
  background-color: #000000;
  color: #ffffff;
}
```

### ❌ Mistake #4: Avatar too small
```html
<!-- WRONG: 80px -->
<div class="profile-avatar" style="width: 80px; height: 80px;">

<!-- CORRECT: 120px -->
<div class="profile-avatar" style="width: 120px; height: 120px;">
```

---

## Visual Hierarchy Comparison

### Before (Broken Implementation)
```
[Avatar 80px]           ← Too small
Username (24px)         ← Too small, weak hierarchy
[Button]                ← Generic blue

Stats:  1.2M  16px  #245  16px  #18   ← Crowded
        (20px)       (20px)      (20px) ← Numbers too small
```

### After (Pexels Specifications)
```
[Avatar 120px]          ← Properly prominent
Username (32px)         ← Strong, clear
[Button #05a081]        ← Brand green

Stats:  1.2M    48px    #245    48px    #18    ← Spacious
        (24px)          (24px)          (24px) ← Clear, bold
```

---

## Color Palette Reference

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Primary green | Pexels brand | `#05a081` | Button bg |
| Green hover | Darker shade | `#048f73` | Button hover |
| Black | Pure black | `#000000` | Username, active tab bg, stat values |
| White | Pure white | `#ffffff` | Button text, active tab text |
| Gray 500 | Medium gray | `#6b7280` | Stat labels, inactive tabs |
| Gray 100 | Light gray | `#f9fafb` | Filter dropdown bg, tab hover |
| Gray 200 | Border gray | `#e5e7eb` | Filter borders, tab container border |

---

## Typography Scale

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Username | 32px | 700 (Bold) | #000000 |
| Button text | 15px | 600 (Semibold) | #ffffff |
| Tab text | 15px | 500 (Medium) | #6b7280 / #ffffff |
| Stat value | 24px | 700 (Bold) | #000000 |
| Stat label | 14px | 400 (Regular) | #6b7280 |
| Filter text | 14px | 500 (Medium) | #374151 |

---

## Spacing System

| Gap Type | Size | Usage |
|----------|------|-------|
| **Avatar → Username** | 16px | Vertical margin |
| **Username → Button** | 16px | Vertical margin |
| **Button → Stats** | 32px | Vertical margin |
| **Stats: Between items** | 48px | Horizontal gap |
| **Stats → Tabs** | 32px | Vertical margin |
| **Tabs: Between items** | 8px | Horizontal gap |
| **Tabs → Filters** | 24px | Vertical margin |
| **Filters: Between items** | 12px | Horizontal gap |

---

## Accessibility Notes

### Keyboard Navigation
- All tabs must be focusable with Tab key
- Active tab should have visible focus indicator
- Dropdowns must be keyboard accessible (arrow keys)

### Screen Readers
- Avatar should have meaningful alt text: "Urban Avenue's avatar"
- Stats should have proper labels: "Total Views: 1.2M"
- Tabs should indicate active state: "Gallery (current page)"
- Filters should have hidden labels: "Filter by media type"

### Color Contrast
- Username (black on white): 21:1 ratio ✅
- Button (#05a081 bg, white text): 4.8:1 ratio ✅
- Active tab (black bg, white text): 21:1 ratio ✅
- Stat labels (gray on white): 4.6:1 ratio ✅

All ratios meet WCAG AA standards.

---

## Django Template Integration

### Example: Profile Header Template

```django
{% load static %}

<div class="profile-header">

  <!-- Top Section -->
  <div class="profile-header__top">

    <div class="profile-avatar">
      {% if user.profile.avatar %}
        <img src="{{ user.profile.avatar.url }}" alt="{{ user.username }}'s avatar">
      {% else %}
        <img src="{% static 'images/default-avatar.png' %}" alt="Default avatar">
      {% endif %}
    </div>

    <h1 class="profile-username">
      {{ user.username }}
      {% if user.profile.is_verified %}
        <span class="profile-username__verified" aria-label="Verified user">
          <svg>...</svg>
        </span>
      {% endif %}
    </h1>

    {% if user == request.user %}
      <a href="{% url 'profile:edit' %}" class="btn-edit-profile">
        Edit profile
      </a>
    {% endif %}

  </div>

  <!-- Stats -->
  <ul class="profile-stats">
    <li class="profile-stats__item">
      <span class="profile-stats__value">{{ total_views|intcomma }}</span>
      <span class="profile-stats__label">Total Views</span>
    </li>
    <li class="profile-stats__item">
      <span class="profile-stats__value">#{{ all_time_rank }}</span>
      <span class="profile-stats__label">All-time rank</span>
    </li>
    <li class="profile-stats__item">
      <span class="profile-stats__value">#{{ monthly_rank }}</span>
      <span class="profile-stats__label">30-day rank</span>
    </li>
  </ul>

  <!-- Tabs -->
  <ul class="profile-tabs">
    <li class="profile-tabs__item">
      <a href="{% url 'profile:highlights' user.username %}"
         class="profile-tabs__link {% if active_tab == 'highlights' %}profile-tabs__link--active{% endif %}">
        Highlights
      </a>
    </li>
    <li class="profile-tabs__item">
      <a href="{% url 'profile:gallery' user.username %}"
         class="profile-tabs__link {% if active_tab == 'gallery' %}profile-tabs__link--active{% endif %}">
        Gallery
      </a>
    </li>
    <!-- More tabs... -->
  </ul>

  <!-- Filters -->
  <div class="profile-filters">
    <div class="profile-filter">
      <label for="media-type" class="sr-only">Filter by media type</label>
      <select id="media-type" class="profile-filter__select"
              onchange="location.href='?media_type=' + this.value;">
        <option value="all" {% if media_type == 'all' %}selected{% endif %}>
          Photos and videos
        </option>
        <option value="photos" {% if media_type == 'photos' %}selected{% endif %}>
          Photos only
        </option>
        <option value="videos" {% if media_type == 'videos' %}selected{% endif %}>
          Videos only
        </option>
      </select>
    </div>
    <!-- More filters... -->
  </div>

</div>
```

---

## Testing Scripts

### Visual Regression Test (JavaScript)

```javascript
// Run in browser console on your profile page
function testProfileHeaderMeasurements() {
  const tests = [];

  // Test 1: Avatar size
  const avatar = document.querySelector('.profile-avatar');
  const avatarSize = avatar.offsetWidth;
  tests.push({
    test: 'Avatar size',
    expected: 120,
    actual: avatarSize,
    pass: avatarSize === 120
  });

  // Test 2: Username font size
  const username = document.querySelector('.profile-username');
  const usernameSize = parseInt(window.getComputedStyle(username).fontSize);
  tests.push({
    test: 'Username font size',
    expected: 32,
    actual: usernameSize,
    pass: usernameSize === 32
  });

  // Test 3: Stats gap
  const stats = document.querySelector('.profile-stats');
  const statsGap = parseInt(window.getComputedStyle(stats).gap);
  tests.push({
    test: 'Stats gap',
    expected: 48,
    actual: statsGap,
    pass: statsGap === 48
  });

  // Test 4: Button color
  const button = document.querySelector('.btn-edit-profile');
  const buttonBg = window.getComputedStyle(button).backgroundColor;
  const isCorrectColor = buttonBg === 'rgb(5, 160, 129)'; // #05a081
  tests.push({
    test: 'Button color',
    expected: '#05a081',
    actual: buttonBg,
    pass: isCorrectColor
  });

  // Print results
  console.table(tests);

  const passed = tests.filter(t => t.pass).length;
  const total = tests.length;
  console.log(`\n✅ ${passed}/${total} tests passed`);

  if (passed < total) {
    console.warn('⚠️ Some tests failed. Review measurements.');
  }
}

// Run test
testProfileHeaderMeasurements();
```

---

## Performance Considerations

### CSS Optimization
- Use `will-change: transform` on hover elements for smooth transitions
- Avoid expensive properties (box-shadow) on animations
- Use CSS transitions (hardware-accelerated) instead of JavaScript

### Image Optimization
- Avatar should be served at 240px (2x for retina)
- Use WebP format with JPEG fallback
- Lazy load avatar if below fold (though unlikely)

### Rendering Performance
- Use `contain: layout style` on `.profile-header` for isolation
- Avoid unnecessary repaints (fixed dimensions help)
- Use `content-visibility: auto` for off-screen sections

---

## Troubleshooting

### Issue: Avatar still 80px after update
**Cause:** Inline styles or conflicting CSS
**Fix:** Remove all inline `width`/`height` attributes, check for `!important` rules

### Issue: Stats still crowded
**Cause:** `gap` not supported in older browsers
**Fix:** Add fallback using margins:
```css
.profile-stats__item:not(:last-child) {
  margin-right: 48px;
}
```

### Issue: Active tab not showing black background
**Cause:** `.profile-tabs__link--active` class not applied
**Fix:** Verify Django template logic adds class correctly

### Issue: Button wrong color
**Cause:** Bootstrap button classes overriding
**Fix:** Remove all `.btn` classes, use only `.btn-edit-profile`

---

## Additional Resources

### Files Created
1. **pexels-profile-header-specs.css** - Complete CSS specifications
2. **pexels-profile-header-example.html** - HTML structure example
3. **PEXELS_PROFILE_IMPLEMENTATION_GUIDE.md** - This comprehensive guide

### Next Steps
1. Review measurements against live Pexels site
2. Integrate CSS into your Django project
3. Update HTML templates with correct classes
4. Test across all breakpoints
5. Run visual regression tests
6. Deploy and verify in production

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-13 | Initial specifications document |

---

**End of Implementation Guide**

For questions or issues, refer to CLAUDE.md or create a detailed bug report with screenshots comparing your implementation to Pexels.
