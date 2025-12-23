# Complete App-Wide Icon Inventory

**Created:** December 21, 2025
**Purpose:** Comprehensive inventory of ALL Font Awesome icons for SVG replacement planning
**Total Icon Instances:** 308+
**Total Unique Icons:** 82

---

## Executive Summary

This report provides a complete inventory of every Font Awesome icon used across the PromptFinder application. The user plans to replace ALL Font Awesome icons with custom SVG icons. This inventory enables efficient planning of that migration.

### Quick Statistics

| Metric | Count |
|--------|-------|
| Total Icon Instances | 308+ |
| Unique Icon Types | 82 |
| Solid Icons (fas) | 74 |
| Regular/Outlined Icons (far) | 6 |
| Brand Icons (fab) | 4 |
| Files with Icons | 27 |
| JavaScript-modified Icons | 12 |

---

## Icons by Category

### 1. Navigation Icons (16 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-search` | fas | 4 | base.html |
| `fa-home` | fas | 7 | base.html, account/, prompts/ |
| `fa-chevron-down` | fas | 4 | base.html |
| `fa-chevron-left` | fas | 5 | account/, user_profile.html |
| `fa-chevron-right` | fas | 2 | user_profile.html, inspiration_index.html |
| `fa-arrow-left` | fas | 5 | prompt_list.html, edit_profile.html, 404.html, 429.html |
| `fa-arrow-right` | fas | 1 | inspiration_index.html |
| `fa-arrow-up` | fas | 1 | base.html, _prompt_card.html |
| `fa-arrow-down` | fas | 1 | _prompt_card.html |
| `fa-external-link-alt` | fas | 4 | prompt_list.html, prompt_detail.html, ai_generator_category.html |
| `fa-ellipsis-h` | fas | 1 | base.html |
| `fa-layer-group` | fas | 1 | base.html |
| `fa-bars` | fas | 0 | (mobile menu - if used) |
| `fa-times` | fas | 9 | base.html, account/, prompts/ |
| `fa-sign-in-alt` | fas | 2 | base.html, prompt_detail.html |
| `fa-sign-out-alt` | fas | 6 | base.html, account/ |

### 2. Action Icons (18 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-heart` | fas/far | 12 | prompt_list.html, prompt_detail.html, _prompt_card.html (JS toggle) |
| `fa-copy` | far | 2 | prompt_detail.html (JS toggle to fa-check) |
| `fa-edit` | fas/far | 7 | prompt_detail.html, user_profile.html, trash_bin.html |
| `fa-trash` | fas | 14 | base.html, user_profile.html, trash_bin.html, _prompt_card.html |
| `fa-trash-alt` | far/fas | 6 | prompt_detail.html, user_profile.html, trash_bin.html |
| `fa-save` | fas | 4 | prompt_list.html, prompt_detail.html, settings_notifications.html |
| `fa-upload` | fas | 6 | base.html, inspiration_index.html, ai_generator_category.html, prompt_create.html |
| `fa-plus-circle` | fas | 4 | prompt_list.html, _masonry_grid.html |
| `fa-check` | fas | 5 | prompt_list.html, unsubscribe.html (JS) |
| `fa-check-circle` | fas | 12 | account/, upload_step1.html, unsubscribe.html, prompts/ |
| `fa-undo` | fas | 1 | _prompt_card.html |
| `fa-flag` | fas/far | 4 | base.html, prompt_detail.html |
| `fa-globe` | fas | 7 | edit_profile.html, user_profile.html, trash_bin.html, prompt_edit.html |
| `fa-pen` | fas | 1 | user_profile.html |
| `fa-cog` | fas | 4 | prompt_list.html, unsubscribe.html |
| `fa-grip-horizontal` | fas | 1 | _prompt_card.html |
| `fa-arrows-alt` | fas | 1 | prompt_list.html (JS toggle) |
| `fa-cloud-upload-alt` | fas | 1 | prompt_create.html |

### 3. Media Type Icons (7 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-image` | fas | 18 | base.html, user_profile.html, trash_bin.html, _prompt_card.html, ai_generator_category.html |
| `fa-video` | fas | 5 | base.html, prompt_detail.html |
| `fa-images` | fas | 2 | upload_step1.html, ai_generator_category.html |
| `fa-play-circle` | fas | 2 | _prompt_card.html |
| `fa-eye` | fas | 9 | base.html, prompt_list.html, prompt_detail.html, 404.html, _prompt_card.html |
| `fa-eye-slash` | fas | 3 | base.html, prompt_list.html, upload_step2.html |
| `fa-th-large` | fas | 1 | _generator_dropdown.html |

### 4. User/Profile Icons (6 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-user` | fas | 7 | base.html, _prompt_card.html |
| `fa-user-edit` | fas | 2 | base.html, edit_profile.html |
| `fa-user-circle` | fas | 3 | account/login.html, account/signup.html |
| `fa-user-plus` | fas | 1 | base.html |
| `fa-users` | fas | 2 | leaderboard.html, settings_notifications.html |
| `fa-bell` | far | 4 | base.html |

### 5. Status/Feedback Icons (12 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-info-circle` | fas | 16 | base.html, account/, edit_profile.html, prompts/ |
| `fa-exclamation-triangle` | fas | 13 | account/, user_profile.html, trash_bin.html, _prompt_card.html, prompt_detail.html |
| `fa-exclamation-circle` | fas | 10 | prompt_create.html, edit_profile.html, prompt_detail.html |
| `fa-spinner` | fas | 6 | prompt_list.html, _masonry_grid.html, edit_profile.html, prompt_create.html, prompt_detail.js |
| `fa-clock` | fas/far | 7 | base.html, user_profile.html, trash_bin.html, _prompt_card.html, 429.html |
| `fa-calendar` | fas | 3 | user_profile.html, trash_bin.html |
| `fa-calendar-alt` | fas | 2 | user_profile.html, style.css |
| `fa-hourglass-half` | fas | 2 | 429.html, _prompt_card.html |
| `fa-hourglass-bottom` | fas | 1 | upload_step2.html |
| `fa-question-circle` | far | 2 | ai_generator_category.html, unsubscribe.html |
| `fa-shield-alt` | fas | 1 | 429.html |
| `fa-archive` | fas | 1 | prompt_gone.html |

### 6. Content Icons (8 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-comment` | far | 2 | prompt_detail.html |
| `fa-robot` | fas | 3 | prompt_detail.html, _generator_dropdown.html |
| `fa-tag` | fas | 2 | prompt_temporarily_unavailable.html, prompt_gone.html |
| `fa-lightbulb` | fas | 3 | base.html, edit_profile.html, unsubscribe.html |
| `fa-fire` | fas | 1 | inspiration_index.html |
| `fa-fire-alt` | fas | 1 | inspiration_index.html |
| `fa-newspaper` | fas | 1 | base.html |
| `fa-file-alt` | fas | 1 | base.html |

### 7. Social/Brand Icons (4 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-twitter` | fab | 3 | base.html, edit_profile.html, user_profile.html |
| `fa-instagram` | fab | 3 | base.html, edit_profile.html, user_profile.html |
| `fa-facebook-f` | fab | 1 | base.html |
| `fa-link` | fas | 1 | edit_profile.html |

### 8. Misc Icons (10 unique)

| Icon | Class | Count | Files Used In |
|------|-------|-------|---------------|
| `fa-trophy` | fas | 2 | base.html |
| `fa-bolt` | fas | 1 | leaderboard.html |
| `fa-chart-line` | fas | 1 | base.html |
| `fa-envelope` | fas | 3 | base.html, unsubscribe.html |
| `fa-map-marker-alt` | fas | 1 | base.html |
| `fa-unlock` | fas | 1 | account/login.html |
| `fa-align-left` | fas | 1 | edit_profile.html |
| `fa-lock` | fas | 1 | prompt_edit.html |
| `fa-times-circle` | fas | 1 | prompt_edit.html |

---

## Detailed Inventory by File

### templates/base.html (56 instances)

| Line | Icon | Class | Context/Purpose |
|------|------|-------|-----------------|
| 92 | fa-image | fas | Search type icon (default) |
| 94 | fa-chevron-down | fas | Search dropdown arrow |
| 102 | fa-image | fas | Images search option |
| 106 | fa-video | fas | Videos search option |
| 125 | fa-search | fas | Search submit button |
| 144 | fa-chevron-down | fas | Explore dropdown arrow |
| 151 | fa-layer-group | fas | Collections link |
| 157 | fa-trophy | fas | Leaderboard link |
| 163 | fa-lightbulb | fas | Inspiration link |
| 169 | fa-newspaper | fas | Blog link |
| 188 | fa-chevron-down | fas | Media dropdown arrow |
| 195 | fa-image | fas | Photos link |
| 202 | fa-video | fas | Videos link |
| 221 | fa-ellipsis-h | fas | More dropdown trigger |
| 228 | fa-chart-line | fas | Analytics link |
| 234 | fa-info-circle | fas | About link |
| 240 | fa-flag | fas | Report link |
| 246 | fa-file-alt | fas | Terms link |
| 253 | fa-info-circle | fas | Privacy link |
| 259 | fa-envelope | fas | Contact link |
| 270 | fa-bell | far | Notification bell |
| 289 | fa-user | fas | Profile button icon |
| 307 | fa-user | fas | Profile dropdown - Profile |
| 313 | fa-user-edit | fas | Profile dropdown - Edit Profile |
| 319 | fa-bell | far | Profile dropdown - Notifications |
| 325 | fa-trash | fas | Profile dropdown - Trash |
| 332 | fa-sign-out-alt | fas | Profile dropdown - Sign Out |
| 349 | fa-search | fas | Mobile search icon |
| 355 | fa-bell | far | Mobile notification bell |
| 363 | fa-arrow-up | fas | Upload button arrow |
| 380 | fa-user | fas | Mobile profile icon |
| 401 | fa-home | fas | Mobile nav - Home |
| 405 | fa-image | fas | Mobile nav - Photos |
| 409 | fa-video | fas | Mobile nav - Videos |
| 413 | fa-trophy | fas | Mobile nav - Leaderboard |
| 418 | fa-user | fas | Mobile nav - Profile |
| 422 | fa-upload | fas | Mobile nav - Upload |
| 426 | fa-sign-out-alt | fas | Mobile nav - Sign Out |
| 431 | fa-sign-in-alt | fas | Mobile nav - Sign In |
| 453-485 | Various | fas | Mobile search dropdown |
| 510 | fa-clock | fas | Pending review banner |
| 519 | fa-eye-slash | fas | Draft mode banner |
| 525 | fa-globe | fas | Publish button |
| 583-593 | Various | fas | Hero CTA buttons |
| 698-704 | Various | fab | Footer social icons |
| 771-772 | Various | fas | Footer contact info |

### templates/account/*.html (20 instances)

| File | Line | Icon | Class | Purpose |
|------|------|------|-------|---------|
| login.html | 18 | fa-info-circle | fas | Alert icon |
| login.html | 90 | fa-unlock | fas | Forgot password |
| login.html | 93 | fa-user-circle | fas | Sign in button |
| logout.html | 17 | fa-exclamation-triangle | fas | Warning icon |
| logout.html | 40 | fa-times | fas | Cancel button |
| logout.html | 43 | fa-sign-out-alt | fas | Sign out button |
| signup.html | 17 | fa-info-circle | fas | Alert icon |
| signup.html | 112 | fa-user-circle | fas | Sign in link |
| signup.html | 115 | fa-sign-out-alt | fas | Create account |
| password_reset.html | 17 | fa-info-circle | fas | Alert icon |
| password_reset.html | 55 | fa-chevron-left | fas | Back to login |
| password_reset.html | 58 | fa-sign-out-alt | fas | Send reset link |
| password_reset_done.html | 16 | fa-check-circle | fas | Success icon |
| password_reset_done.html | 30 | fa-info-circle | fas | Info icon |
| password_reset_done.html | 43 | fa-chevron-left | fas | Back to sign in |
| password_reset_done.html | 46 | fa-home | fas | Return home |

### templates/404.html (2 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 35 | fa-arrow-left | fas | Go back button |
| 38 | fa-eye | fas | Browse prompts button |

### templates/429.html (5 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 14 | fa-hourglass-half | fas | Rate limit icon (4x) |
| 29 | fa-shield-alt | fas | Security message |
| 37 | fa-clock | fas | Wait time message |
| 45 | fa-home | fas | Return home button |
| 49 | fa-arrow-left | fas | Go back button |

### prompts/templates/prompts/prompt_list.html (28 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 29 | fa-cog | fas | Admin settings gear |
| 39 | fa-external-link-alt | fas | Open admin panel |
| 42 | fa-eye | fas | Show order numbers |
| 45 | fa-arrows-alt | fas | Drag mode toggle |
| 412 | fa-arrow-left | fas | Back to all prompts |
| 427 | fa-search | fas | Search results icon |
| 440 | fa-arrow-left | fas | Back link |
| 473 | fa-plus-circle | fas | Load more button |
| 481 | fa-check-circle | fas | All loaded state |
| 562 | fa-save | fas | Unsaved changes modal |
| 566 | fa-check | fas | Save button |
| 569 | fa-times | fas | Cancel button |
| 1022+ | fa-heart | fas/far | JS: Like toggle (multiple) |
| 1073 | fa-spinner | fas | JS: Loading state |
| 1178 | fa-eye-slash | fas | JS: Hide order numbers |
| 1192+ | Various | fas | JS: Dynamic content |

### prompts/templates/prompts/prompt_detail.html (28 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 82 | fa-exclamation-triangle | fas | Missing media warning |
| 87 | fa-edit | fas | Edit prompt link |
| 105 | fa-video | fas | Video type badge |
| 172 | fa-eye | fas | Views count |
| 182 | fa-comment | far | Comments count |
| 192 | fa-heart | fas/far | Like button (conditional) |
| 197 | fa-heart | far | Like button (guest) |
| 205 | fa-edit | far | Edit button |
| 212 | fa-trash-alt | far | Delete button |
| 222 | fa-flag | far | Report button |
| 234 | fa-robot | fas | AI generator icon |
| 239 | fa-video | fas | Video type |
| 242 | fa-image | fas | Image type |
| 253 | fa-external-link-alt | fas | Generator link |
| 266 | fa-copy | far | Copy prompt button |
| 271 | fa-sign-in-alt | fas | Login to copy |
| 414 | fa-edit | fas | Comment edit |
| 418 | fa-trash | fas | Comment delete |
| 430 | fa-save | fas | Update comment |
| 433 | fa-times | fas | Cancel edit |
| 463 | fa-info-circle | fas | Delete modal info |
| 469 | fa-times | fas | Cancel delete |
| 472 | fa-trash | fas | Confirm delete |
| 485 | fa-flag | fas | Report modal header |
| 496-543 | Various | fas | Report form elements |

### prompts/templates/prompts/user_profile.html (32 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 865 | fa-calendar-alt | fas | Member since |
| 879 | fa-twitter | fab | Twitter link |
| 885 | fa-instagram | fab | Instagram link |
| 891 | fa-globe | fas | Website link |
| 900 | fa-pen | fas | Edit profile button |
| 953 | fa-chevron-left | fas | Tab scroll left |
| 984 | fa-trash-alt | fas | Trash tab icon |
| 993 | fa-chevron-right | fas | Tab scroll right |
| 1105 | fa-info-circle | fas | Trash info |
| 1113 | fa-trash-alt | fas | Empty trash button |
| 1147-1151 | fa-image | fas | Placeholder images |
| 1160 | fa-clock | far | Deleted time |
| 1165 | fa-exclamation-triangle | fas | Expiring warning |
| 1170 | fa-calendar | fas | Days remaining |
| 1183 | fa-globe | fas | Restore & publish |
| 1193 | fa-edit | fas | Restore as draft |
| 1201 | fa-trash | fas | Delete forever |
| 1217 | fa-exclamation-triangle | fas | Delete modal warning |
| 1232 | fa-trash | fas | Confirm delete |
| 1245 | fa-exclamation-triangle | fas | Empty trash warning |
| 1261 | fa-trash | fas | Confirm empty |
| 1275 | fa-trash-alt | fas | Empty state icon |
| 1293 | fa-image | fas | No prompts state |

### prompts/templates/prompts/_prompt_card.html (15 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 20 | fa-play-circle | fas | Video play overlay |
| 26 | fa-image | fas | Image placeholder |
| 35 | fa-clock | far | Deleted time (trash) |
| 40 | fa-exclamation-triangle | fas | Expiring soon |
| 45 | fa-hourglass-half | fas | Time remaining |
| 54 | fa-undo | fas | Restore button |
| 62 | fa-trash | fas | Delete button |
| 75 | fa-exclamation-triangle | fas | Delete confirm |
| 90 | fa-trash | fas | Confirm delete |
| 110 | fa-grip-horizontal | fas | Drag handle |
| 114 | fa-arrow-up | fas | Move up |
| 117 | fa-arrow-down | fas | Move down |
| 150 | fa-play-circle | fas | Video indicator |
| 197 | fa-eye | fas | View count |
| 214 | fa-user | fas | Author avatar fallback |
| 226-238 | fa-heart | fas/far | Like button |

### prompts/templates/prompts/trash_bin.html (17 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 17 | fa-trash | fas | Page title icon |
| 37 | fa-info-circle | fas | Info message |
| 48 | fa-trash-alt | fas | Empty trash button |
| 87-91 | fa-image | fas | Placeholder images |
| 100 | fa-clock | far | Deleted time |
| 105 | fa-exclamation-triangle | fas | Expiring warning |
| 110 | fa-calendar | fas | Days remaining |
| 123 | fa-globe | fas | Restore & publish |
| 133 | fa-edit | fas | Restore as draft |
| 141 | fa-trash | fas | Delete forever |
| 157 | fa-exclamation-triangle | fas | Delete warning |
| 172 | fa-trash | fas | Confirm delete |
| 186 | fa-exclamation-triangle | fas | Empty warning |
| 202 | fa-trash | fas | Confirm empty |
| 217 | fa-trash | fas | Empty state icon |

### prompts/templates/prompts/edit_profile.html (17 instances)

| Line | Icon | Class | Purpose |
|------|------|-------|---------|
| 13 | fa-user-edit | fas | Page title |
| 16 | fa-arrow-left | fas | Back to profile |
| 43 | fa-image | fas | Avatar section |
| 62 | fa-exclamation-circle | fas | Error icon |
| 67 | fa-info-circle | fas | Help text |
| 76 | fa-align-left | fas | Bio label |
| 81 | fa-info-circle | fas | Bio help |
| 88 | fa-exclamation-circle | fas | Error icon |
| 98 | fa-link | fas | Social links section |
| 104 | fa-twitter | fab | Twitter label |
| 113 | fa-exclamation-circle | fas | Error icon |
| 122 | fa-instagram | fab | Instagram label |
| 131 | fa-exclamation-circle | fas | Error icon |
| 140 | fa-globe | fas | Website label |
| 149 | fa-exclamation-circle | fas | Error icon |
| 161 | fa-exclamation-triangle | fas | Form error |
| 169 | fa-save | fas | Save button |
| 172 | fa-times | fas | Cancel button |
| 182 | fa-lightbulb | fas | Tips section |
| 237 | fa-spinner | fas | JS: Saving state |

### Other Template Files

#### upload_step1.html (5 instances)
- fa-images (line 41): Upload dropzone icon
- fa-check-circle (lines 97, 101, 111, 115, 125): Guidelines checkmarks

#### upload_step2.html (8 instances)
- fa-arrow-left (207): Back button
- fa-eye-slash (308): NSFW warning
- fa-trash (323): Delete upload
- fa-clock (340): Session warning
- fa-check-circle (351): Extend time
- fa-exclamation-triangle (367): Session expired
- fa-hourglass-bottom (372): Timeout icon
- fa-home (379): Go home

#### prompt_create.html (12 instances)
- fa-info-circle (17): Info alert
- fa-exclamation-circle (multiple): Form errors
- fa-cloud-upload-alt (104): Upload icon
- fa-times (148): Cancel button
- fa-upload (151): Submit button
- fa-check-circle (211): JS success
- fa-exclamation-circle (214): JS error
- fa-spinner (234): JS loading

#### prompt_edit.html (8 instances)
- fa-info-circle (17): Info alert
- fa-globe (166): Published toggle
- fa-lock (175): Pending review
- fa-check-circle (177): Admin approved
- fa-times-circle (179): Rejected
- fa-times (195): Cancel button
- fa-sign-out-alt (198): Update button

#### settings_notifications.html (4 instances)
- fa-bell (25): Activity notifications
- fa-users (57): Social notifications
- fa-envelope (100): Digest section
- fa-save (141): Save button

#### unsubscribe.html (17 instances)
- Multiple status icons and action buttons

#### ai_generator_category.html (6 instances)
- fa-image, fa-eye, fa-external-link-alt, fa-question-circle, fa-images, fa-upload

#### leaderboard.html (3 instances)
- fa-eye, fa-bolt, fa-users

#### inspiration_index.html (7 instances)
- fa-robot, fa-chevron-right, fa-fire, fa-arrow-right, fa-fire-alt, fa-upload (x2)

#### _masonry_grid.html (4 instances)
- fa-plus-circle, fa-spinner, fa-check-circle, fa-image (dynamic)

#### _generator_dropdown.html (2 instances)
- fa-robot, fa-th-large

#### prompt_temporarily_unavailable.html (5 instances)
- fa-clock, fa-info-circle, fa-heart, fa-tag, fa-home, fa-search

#### prompt_gone.html (5 instances)
- fa-archive, fa-heart, fa-tag, fa-home, fa-search

#### collaborate.html (4 instances)
- fa-check-circle, fa-info-circle, fa-home, fa-sign-out-alt

---

## JavaScript-Modified Icons

These icons are dynamically changed via JavaScript and require special attention during SVG migration:

| File | Icon(s) | Behavior |
|------|---------|----------|
| prompt_list.html | fa-heart | Toggles between fas/far on like |
| prompt_list.html | fa-eye / fa-eye-slash | Toggle visibility |
| prompt_list.html | fa-arrows-alt / fa-times | Drag mode toggle |
| prompt_list.html | fa-spinner | Loading state |
| prompt_list.html | fa-plus-circle / fa-check-circle | Load more states |
| prompt_detail.html | fa-heart | Like toggle (fas/far) |
| prompt_detail.html | fa-copy / fa-check | Copy feedback |
| prompt_detail.html | fa-spinner | Loading states |
| _masonry_grid.html | fa-check-circle | All loaded state |
| static/js/prompt-detail.js | fa-heart | Like toggle |
| static/js/prompt-detail.js | fa-copy / fa-check | Copy toggle |
| static/js/prompt-detail.js | fa-trash | Delete button |
| static/js/prompt-detail.js | fa-spinner | Loading state |
| static/js/prompt-detail.js | fa-flag | Report button |
| static/js/navbar.js | fa-image / fa-video | Search type toggle |
| edit_profile.html | fa-spinner | Save state |
| prompt_create.html | fa-spinner / fa-check-circle / fa-exclamation-circle | Upload states |

---

## Icons by Style Type

### Regular (Outlined) Icons - `far` (6 unique)

| Icon | Count | Files |
|------|-------|-------|
| fa-bell | 4 | base.html |
| fa-heart | 6 | prompt_list.html, prompt_detail.html, _prompt_card.html |
| fa-clock | 4 | user_profile.html, trash_bin.html, _prompt_card.html |
| fa-comment | 2 | prompt_detail.html |
| fa-copy | 2 | prompt_detail.html |
| fa-edit | 1 | prompt_detail.html |
| fa-trash-alt | 1 | prompt_detail.html |
| fa-flag | 1 | prompt_detail.html |
| fa-question-circle | 2 | ai_generator_category.html, unsubscribe.html |

### Brand Icons - `fab` (4 unique)

| Icon | Count | Files |
|------|-------|-------|
| fa-twitter | 3 | base.html, edit_profile.html, user_profile.html |
| fa-instagram | 3 | base.html, edit_profile.html, user_profile.html |
| fa-facebook-f | 1 | base.html |

### Solid Icons - `fas` (74 unique)

All remaining icons use the solid (`fas`) style.

---

## CSS References

Only one CSS file references Font Awesome:

| File | Line | Icon | Purpose |
|------|------|------|---------|
| static/css/style.css | 431 | .fa-calendar-alt | Styling for metadata icon |

---

## SVG Migration Notes

### High Priority Icons (Most Used)

| Icon | Instances | Priority Reason |
|------|-----------|-----------------|
| fa-image | 18+ | Core media type |
| fa-info-circle | 16+ | UX feedback |
| fa-trash | 14+ | Critical action |
| fa-exclamation-triangle | 13+ | Warnings |
| fa-heart | 12+ | Social engagement |
| fa-check-circle | 12+ | Success states |

### Icons with State Changes

These require both filled and outlined SVG versions:

| Icon | States Needed |
|------|---------------|
| fa-heart | Filled (liked), Outlined (not liked) |
| fa-bell | Filled (notifications), Outlined (no notifications) |
| fa-copy | Changes to fa-check on success |
| fa-eye | Changes to fa-eye-slash |
| fa-spinner | Needs CSS animation |

### Brand Icons (Require Official SVGs)

| Icon | Source |
|------|--------|
| fa-twitter | Twitter brand guidelines |
| fa-instagram | Instagram brand guidelines |
| fa-facebook-f | Facebook brand guidelines |

### Icons That May Need Custom Design

| Icon | Reason |
|------|--------|
| fa-robot | AI theme - may want custom design |
| fa-layer-group | Collections - may want custom design |
| fa-grip-horizontal | Drag handle - ensure accessibility |

---

## Recommendations for SVG Migration

### Phase 1: Create Core Icon Set (40 icons)
1. Navigation: search, home, chevron-*, arrow-*, times, external-link-alt
2. Actions: heart (2 states), edit, trash, save, upload, copy, check
3. Media: image, video, play-circle, eye (2 states)
4. Status: info-circle, exclamation-triangle, exclamation-circle, check-circle, spinner

### Phase 2: Create Extended Icon Set (30 icons)
1. User: user, user-edit, user-circle, users, bell (2 states)
2. Content: comment, robot, tag, lightbulb, newspaper, flag
3. UI: cog, globe, calendar, clock, hourglass

### Phase 3: Brand Icons (4 icons)
1. twitter, instagram, facebook-f (use official SVGs)
2. Create fallback if brand icons unavailable

### Phase 4: Remaining Icons (8 icons)
1. Specialized: trophy, bolt, chart-line, archive, etc.

---

## Summary

This inventory documents all 308+ Font Awesome icon instances across 82 unique icon types used in the PromptFinder application. The migration to custom SVG icons should prioritize:

1. **High-frequency icons** (fa-image, fa-heart, fa-trash, etc.)
2. **State-changing icons** (require multiple SVG versions)
3. **JavaScript-modified icons** (require code updates)
4. **Brand icons** (require official SVG sources)

The detailed file-by-file breakdown enables efficient batch replacement during the SVG migration process.
