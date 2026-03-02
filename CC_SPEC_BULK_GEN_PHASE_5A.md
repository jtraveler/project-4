# CC_SPEC_BULK_GEN_PHASE_5A — Job Page Foundation

**Date:** March 2, 2026
**Phase:** Bulk AI Image Generator — Phase 5A
**Depends On:** Phases 1-4 (complete)
**Estimated Effort:** 3-4 hours

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Read `prompts/views/bulk_generator_views.py`** — Understand existing API endpoints
4. **Read `prompts/models.py`** — Understand BulkGenerationJob and GeneratedImage models
5. **Read `static/js/bulk-generator.js`** — Understand existing patterns (DO NOT modify this file)
6. **Use required agents** — Minimum 3 agents appropriate for the task
7. **Report agent usage** — Include ratings and findings in completion summary

**This is non-negotiable per the project's CC Communication Protocol.**

---

## ⛔ STOP — MANDATORY REQUIREMENTS

> **Work will be REJECTED if ANY of the following are missing:**
>
> 1. New view `bulk_generator_job_view` in `bulk_generator_views.py`
> 2. New URL pattern at `tools/bulk-ai-generator/job/<uuid:job_id>/`
> 3. New template `bulk_generator_job.html`
> 4. New JS file `static/js/bulk-generator-job.js` (separate from existing bulk-generator.js)
> 5. New CSS file `static/css/pages/bulk-generator-job.css`
> 6. Progress polling that calls existing status API endpoint
> 7. Cancel button that calls existing cancel API endpoint
> 8. All existing 914 tests still passing
> 9. Agent ratings 8+/10

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### Task: Bulk Generator Job Progress Page

Create a new page that displays the progress of a bulk image generation job. When a user clicks "Generate" on the bulk generator input page (Phase 4), they will be redirected to this new job page where they can monitor progress, see cost tracking, cancel the job, and eventually (in Phases 5B-5D) see generated images.

### Context

- Phases 1-4 built the backend (models, tasks, API endpoints) and the input UI
- The input page collects prompts + settings and calls `POST /api/bulk-generator/start/` which returns a `job_id`
- The status endpoint `GET /api/bulk-generator/status/<job_id>/` already returns progress data
- The cancel endpoint `POST /api/bulk-generator/cancel/<job_id>/` already works
- This spec creates the PAGE that consumes those existing APIs
- This is the foundation — Phases 5B-5D will add gallery rows, image selection, and publish controls ON TOP of this page

### What This Spec Does NOT Cover (Future Phases)

- ❌ Gallery image rows (Phase 5B)
- ❌ Image lightbox (Phase 5C)
- ❌ Image selection / publish toggles (Phase 5D)
- ❌ "Create Pages" button (Phase 6)
- ❌ In-app notifications (Phase 5D)

---

## 🎯 OBJECTIVES

### Primary Goal

A functional job progress page at `/tools/bulk-ai-generator/job/<job_id>/` that shows real-time progress of bulk image generation with cost tracking, estimated time, and cancel functionality.

### Success Criteria

- ✅ Page loads with job summary header showing settings used
- ✅ Progress bar updates in real-time via polling (every 3 seconds)
- ✅ Progress shows "X of Y complete" with percentage
- ✅ Cost tracker shows "Spent: $X.XX / Estimated: $Y.YY"
- ✅ Estimated time remaining displayed and updates
- ✅ Cancel button sends cancel request and updates page state
- ✅ Page is accessible via URL directly (bookmark/refresh safe)
- ✅ Staff-only access enforced (same as input page)
- ✅ Page handles all job states: pending, processing, completed, cancelled, failed
- ✅ Responsive layout (desktop + tablet + mobile)
- ✅ All 914+ existing tests pass + new tests added

---

## 🔍 PROBLEM ANALYSIS

### Current State

After Phase 4, the input page exists at `/tools/bulk-ai-generator/` where users enter prompts and settings. The "Generate" button currently has no connected frontend flow — it validates inputs but there's no page to redirect to after starting generation. The backend APIs (start, status, cancel) exist and work, but no UI consumes them yet.

### Issues/Challenges

1. The existing `bulk-generator.js` is ~900 lines — adding progress logic there would exceed maintainability limits
2. The job page needs to work independently (user can close browser, come back later)
3. Cost calculation depends on quality/size settings stored on the BulkGenerationJob model
4. Time estimation needs to improve as more images complete (calibration)

### Root Cause

Phase 4 built the input half of the UX. Phase 5A builds the output/progress half as a separate page with its own JS/CSS, keeping files modular and under size limits.

---

## 🔧 SOLUTION

### Approach

1. Create a new Django view that serves the job page, passing job data as template context
2. Create a new template extending `base.html` with the progress UI
3. Create a new JS file that handles polling, progress updates, cost tracking, and cancel
4. Create a new CSS file for job page styles
5. Wire up URL routing
6. Add redirect from input page after successful job start

### Implementation Details

#### Step 1: URL Pattern

Add to `prompts/urls.py`:
```
path('tools/bulk-ai-generator/job/<uuid:job_id>/', views.bulk_generator_job_view, name='bulk_generator_job')
```

#### Step 2: View Function

The view must:
- Require staff login (`@staff_member_required`)
- Look up the BulkGenerationJob by ID (404 if not found)
- Pass job data + settings to template as context
- Calculate cost-per-image based on job settings for the cost tracker

#### Step 3: Cost Calculation

The view should pass a `cost_per_image` value to the template based on the job's quality and size settings. Use this pricing table (GPT-Image-1 as of March 2026):

| Quality | Square (1024×1024) | Landscape (1536×1024) | Portrait (1024×1536) |
|---------|-------------------|----------------------|---------------------|
| Low     | $0.011            | $0.016               | $0.016              |
| Medium  | $0.034            | $0.046               | $0.046              |
| High    | $0.067            | $0.092               | $0.092              |

**IMPORTANT:** These prices should be stored as a Python dict constant in the view file (e.g., `IMAGE_COST_MAP`), NOT hardcoded into JavaScript. The view passes `cost_per_image` and `estimated_total_cost` as template context variables that the JS reads from a data attribute.

#### Step 4: Template Structure

The template has three main sections:
1. **Job Summary Header** — Always visible, shows settings used
2. **Progress Section** — Active during generation, shows bar + stats
3. **Gallery Container** — Empty placeholder div for Phase 5B to populate

#### Step 5: JavaScript Polling

The JS file handles:
- Reading job config from data attributes on a root element
- Polling `/api/bulk-generator/status/<job_id>/` every 3 seconds
- Updating progress bar width + text
- Updating cost display (completed_count × cost_per_image)
- Updating time estimate (based on average time per completed image)
- Handling terminal states (completed, cancelled, failed) — stop polling, update UI
- Cancel button click → POST to cancel endpoint → update UI

#### Step 6: State-Specific UI

The page must handle these states on initial load AND during polling:

| Job Status | Progress Bar | Cancel Button | Message |
|------------|-------------|---------------|---------|
| `pending` | 0%, animated pulse | Enabled | "Starting generation..." |
| `processing` | X%, animated | Enabled | "Generating X of Y..." |
| `completed` | 100%, green | Hidden | "All images generated!" |
| `cancelled` | X%, orange | Hidden | "Cancelled — X of Y generated" |
| `failed` | X%, red | Hidden | "Generation failed — see details" |

#### Step 7: Connect Input Page

Modify `static/js/bulk-generator.js` to redirect to the job page after a successful start API call. This is the ONE change to the existing file: in the generate button handler, after receiving a successful response with `job_id`, do `window.location.href = '/tools/bulk-ai-generator/job/' + data.job_id + '/';`

### ♿ ACCESSIBILITY — BUILD THESE IN FROM THE START

⛔ **Do NOT bolt accessibility on after implementation. Build it in from line one.**

1. **Progress Bar:** Use `role="progressbar"` with `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Generation progress"`. Update `aria-valuenow` on every poll.

2. **Live Region for Status:** Wrap the status text ("Generating 8 of 20...") in a `<div aria-live="polite">`. This announces progress changes to screen readers. Do NOT make the progress bar itself a live region (too noisy with 3-second updates) — only the text status.

3. **Cancel Button:** Standard `<button>` with clear text "Cancel Generation". After cancel, move focus to the status message area.

4. **Contrast:** All text must be `--gray-500` (#737373) minimum on white backgrounds. The progress bar fill color must have 3:1 contrast against its track. Use `--accent-color-primary` for the active progress fill.

5. **Cost Display:** Use `aria-label` on the cost section to provide context: `aria-label="Cost tracking: $X spent of $Y estimated"`.

6. **Keyboard Navigation:** Cancel button reachable via Tab. No keyboard traps.

---

## 🏗️ DOM STRUCTURE (Required for UI/Layout Changes)

⛔ **CC must implement the EXACT nesting shown here. Do not reorganize, flatten, or restructure.**

### Required Structure

```
#bulk-generator-job (data-job-id, data-cost-per-image, data-total-images, data-job-status)
├── .job-summary-header
│     ├── .job-summary-title
│     │     ├── h1 "Bulk Generation"
│     │     └── .job-id-badge (small monospace job ID)
│     └── .job-summary-settings
│           ├── .setting-chip (AI Model)
│           ├── .setting-chip (Dimensions)
│           ├── .setting-chip (Quality)
│           ├── .setting-chip (Images per Prompt)
│           └── .setting-chip (Prompt Count)
│
├── .job-progress-section
│     ├── .progress-stats-row (flex, space-between)
│     │     ├── .progress-text-left
│     │     │     ├── span.progress-count "8 of 20 complete"
│     │     │     └── span.progress-percent "(40%)"
│     │     └── .progress-text-right
│     │           └── span.progress-time "~2 min remaining"
│     │
│     ├── .progress-bar-container (role="progressbar", aria attributes)
│     │     └── .progress-bar-fill (width set by JS)
│     │
│     ├── .progress-details-row (flex, space-between)
│     │     ├── .cost-tracker
│     │     │     ├── span.cost-spent "Spent: $0.27"
│     │     │     └── span.cost-estimated "/ Est. total: $0.68"
│     │     └── .progress-actions
│     │           └── button.btn-cancel "Cancel Generation"
│     │
│     └── .progress-status-message (aria-live="polite")
│           └── p "Generating images... You can leave this page and come back."
│
└── .job-gallery-container
      └── (empty — Phase 5B will populate this)
```

### ⛔ Common Mistake to Avoid

```
WRONG: .cost-tracker nested inside .progress-bar-container
RIGHT: .cost-tracker inside .progress-details-row, which is a SIBLING of .progress-bar-container
```

**Agent rejection criteria:** If the implemented DOM nesting does not match this tree diagram, the UI agent score MUST be below 6.

---

## 📁 FILES TO MODIFY

### File 1: `prompts/urls.py`

**Current State:** Has URL patterns for bulk generator input page and API endpoints.

**Changes Needed:**
- Add one new URL pattern for the job page view

**Add this pattern** (near the existing bulk generator URLs):
```python
path('tools/bulk-ai-generator/job/<uuid:job_id>/', views.bulk_generator_job_view, name='bulk_generator_job'),
```

---

### File 2: `prompts/views/bulk_generator_views.py`

**Current State:** Has `bulk_generator_view` (input page) and 7 API endpoint views.

**Changes Needed:**
- Add `IMAGE_COST_MAP` constant at top of file
- Add `bulk_generator_job_view` function
- Import `get_object_or_404`

**IMAGE_COST_MAP constant:**
```python
# GPT-Image-1 pricing per image (as of March 2026)
IMAGE_COST_MAP = {
    'low': {'1024x1024': 0.011, '1536x1024': 0.016, '1024x1536': 0.016},
    'medium': {'1024x1024': 0.034, '1536x1024': 0.046, '1024x1536': 0.046},
    'high': {'1024x1024': 0.067, '1536x1024': 0.092, '1024x1536': 0.092},
}
```

**View function requirements:**
- Decorator: `@staff_member_required`
- Look up `BulkGenerationJob` by `job_id` using `get_object_or_404`
- Calculate `cost_per_image` from `IMAGE_COST_MAP` using `job.quality` and `job.size`
- Calculate `total_images` = `job.total_prompts * job.images_per_prompt`
- Calculate `estimated_total_cost` = `total_images * cost_per_image`
- Pass context: `job`, `cost_per_image`, `total_images`, `estimated_total_cost`
- Template: `prompts/bulk_generator_job.html`

**IMPORTANT:** Check what field names exist on BulkGenerationJob model. Read `prompts/models.py` to get the exact field names for quality, size, images_per_prompt, etc. Do NOT guess field names. If the model uses different field names than this spec assumes, use the actual model field names and note the difference in your completion report.

---

### File 3: `prompts/templates/prompts/bulk_generator_job.html`

**Current State:** Does not exist (new file).

**This is the main template for the job progress page.**

Requirements:
- Extends `base.html`
- Loads `static` template tag
- Links to `bulk-generator-job.css`
- Includes `bulk-generator-job.js` at bottom (deferred)
- Root element `#bulk-generator-job` with data attributes:
  - `data-job-id="{{ job.id }}"`
  - `data-cost-per-image="{{ cost_per_image }}"`
  - `data-total-images="{{ total_images }}"`
  - `data-job-status="{{ job.status }}"`
  - `data-status-url="{% url 'bulk_generator_status' job.id %}"`
  - `data-cancel-url="{% url 'bulk_generator_cancel' job.id %}"`
- Page title: "Bulk Generation — PromptFinder"
- Summary header showing job settings as chips
- Progress section with all elements from DOM structure above
- Empty gallery container div
- The "You can leave this page" message should display on initial load for pending/processing states

**Setting chips** should display:
- AI Model (from job data)
- Dimensions (e.g., "1024×1024")
- Quality (e.g., "Medium")
- Images per Prompt (e.g., "2 per prompt")
- Total Prompts (e.g., "20 prompts")

**IMPORTANT:** Check the actual BulkGenerationJob model fields to determine what data is available. Use the actual field names from the model. If certain display values need formatting (e.g., "1024x1024" → "1024×1024"), do that in the view context, not the template.

---

### File 4: `static/js/bulk-generator-job.js`

**Current State:** Does not exist (new file).

**This is a NEW file — do NOT modify `static/js/bulk-generator.js`.**

**Structure:**
```
(function() {
    'use strict';

    // --- Constants ---
    const POLL_INTERVAL = 3000;  // 3 seconds
    const TERMINAL_STATES = ['completed', 'cancelled', 'failed'];

    // --- DOM References ---
    // Read from #bulk-generator-job data attributes

    // --- State ---
    let polling = false;
    let pollTimer = null;
    let completedTimes = [];  // Track completion times for ETA calculation

    // --- Functions ---
    // initPage() — read data attributes, set initial state, start polling if needed
    // startPolling() — setInterval for poll()
    // stopPolling() — clearInterval
    // poll() — fetch status endpoint, call updateProgress()
    // updateProgress(data) — update bar, text, cost, ETA
    // updateProgressBar(completed, total) — width + aria
    // updateCostDisplay(completed) — calculate and display costs
    // updateTimeEstimate(completed, total) — ETA based on average completion time
    // handleTerminalState(status, data) — update UI for completed/cancelled/failed
    // handleCancel() — POST to cancel endpoint, update UI
    // formatCost(amount) — "$X.XX" formatting
    // formatTime(seconds) — "~X min" or "< 1 min" formatting

    // --- Init ---
    document.addEventListener('DOMContentLoaded', initPage);
})();
```

**Key behaviors:**

1. **On page load (`initPage`):**
   - Read all data attributes from `#bulk-generator-job`
   - If status is `pending` or `processing`, start polling immediately
   - If status is terminal (completed/cancelled/failed), show final state without polling
   - If status is `processing`, do an immediate first poll (don't wait 3 seconds)

2. **Polling (`poll`):**
   - `fetch()` the status URL (read from data attribute)
   - On success: call `updateProgress(data)`
   - On error: log to console, continue polling (don't stop on transient errors)
   - On terminal state: call `handleTerminalState()`, stop polling

3. **Progress bar update:**
   - Calculate percent: `(completed / total) * 100`
   - Set `.progress-bar-fill` width to `${percent}%`
   - Update `aria-valuenow` on the progressbar container
   - Update text: "X of Y complete (Z%)"

4. **Cost tracking:**
   - `costSpent = completedCount * costPerImage`
   - Display: "Spent: $0.27 / Est. total: $0.68"
   - `costPerImage` and `totalImages` come from data attributes

5. **Time estimate:**
   - Track a `generationStartTime` (set on first poll where completed > 0)
   - Calculate `avgTimePerImage = elapsedSinceStart / completedCount`
   - `remainingTime = avgTimePerImage * (total - completed)`
   - Display: "~X min remaining" or "< 1 min remaining" or "Calculating..."
   - For first poll (completed = 0), show "Calculating..."

6. **Cancel:**
   - `POST` to cancel URL with CSRF token
   - On success: stop polling, update UI to cancelled state
   - Disable cancel button immediately on click (prevent double-click)
   - Move focus to status message after cancel

7. **Terminal state UI:**
   - `completed`: bar turns green (add `.progress-complete` class), show "All X images generated!"
   - `cancelled`: bar turns orange (add `.progress-cancelled` class), show "Cancelled — X of Y generated. Cost: $X.XX"
   - `failed`: bar turns red (add `.progress-failed` class), show "Generation failed" with error details if available
   - All terminal states: hide cancel button, stop polling

**CSRF token:** Get from cookie using the standard Django pattern:
```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

**NOTE:** Check what the status API endpoint actually returns by reading `bulk_generator_views.py`. The response JSON structure determines what fields are available (e.g., `data.completed_count`, `data.total_prompts`, `data.status`, etc.). Use the ACTUAL field names from the API response. Do NOT guess.

---

### File 5: `static/css/pages/bulk-generator-job.css`

**Current State:** Does not exist (new file).

**Styling requirements:**

1. **Job Summary Header:**
   - Background: `var(--gray-50)` with `1px solid var(--gray-200)` border
   - Padding: `1.25rem 1.5rem`
   - Border radius: `var(--radius-lg)` (consistent with platform)
   - Setting chips: inline-flex, `background: var(--white)`, border `1px solid var(--gray-200)`, `border-radius: 999px`, padding `0.25rem 0.75rem`, font-size `var(--text-sm)`, color `var(--gray-700)`
   - Margin bottom: `1.5rem`

2. **Progress Bar:**
   - Track: `background: var(--gray-200)`, height `12px`, `border-radius: 6px`
   - Fill: `background: var(--accent-color-primary)`, `border-radius: 6px`, `transition: width 0.5s ease`
   - `.progress-complete .progress-bar-fill`: `background: var(--success)`
   - `.progress-cancelled .progress-bar-fill`: `background: var(--warning)`
   - `.progress-failed .progress-bar-fill`: `background: var(--error)`
   - Pulse animation for pending state (subtle opacity animation on the bar fill)

3. **Progress Stats:**
   - `.progress-stats-row`: flex, justify-content space-between, margin-bottom `0.5rem`
   - `.progress-count`: font-weight `var(--font-medium)`, color `var(--gray-800)`
   - `.progress-percent`: color `var(--gray-500)`, margin-left `0.25rem`
   - `.progress-time`: color `var(--gray-600)`, font-size `var(--text-sm)`

4. **Cost Tracker:**
   - `.cost-spent`: font-weight `var(--font-medium)`, color `var(--gray-800)`
   - `.cost-estimated`: color `var(--gray-500)`

5. **Cancel Button:**
   - Use existing site button pattern: background `var(--error)`, color white, border-radius from site pattern
   - Hover: slightly darker
   - Disabled state: `opacity: 0.5`, `cursor: not-allowed`

6. **Status Message:**
   - `.progress-status-message p`: color `var(--gray-600)`, font-size `var(--text-sm)`, font-style italic
   - Margin-top: `1rem`

7. **Gallery Container:**
   - `.job-gallery-container`: min-height `200px` (placeholder space for Phase 5B)
   - margin-top: `2rem`

8. **Responsive:**
   - Below 768px: `.progress-stats-row` and `.progress-details-row` stack vertically (flex-direction: column)
   - Below 768px: `.setting-chip` elements wrap naturally (flex-wrap already handles this)
   - Below 768px: cancel button full width

9. **Page container:**
   - Max-width: `900px`, centered with `margin: 0 auto`
   - Padding: `1.5rem`
   - Match the same page container approach used by the existing bulk generator input page

---

### File 6: `static/js/bulk-generator.js` (MINIMAL CHANGE)

**⛔ STOP: This is the ONLY change to this existing file. Do NOT refactor, reorganize, or modify anything else.**

**Changes Needed:**
- In the generate button handler (find where it calls the start API endpoint), after receiving a successful response with a `job_id`, redirect to the job page.

**Find the existing generate handler** (it will be calling something like `fetch('/api/bulk-generator/start/', ...)`) and after the success response, add:
```javascript
window.location.href = '/tools/bulk-ai-generator/job/' + data.job_id + '/';
```

**IMPORTANT:** Read the existing code first to understand the exact structure. The variable name might not be `data.job_id` — use whatever the actual response field name is. Check the `start_generation` view in `bulk_generator_views.py` to see what field name the response uses.

---

### File 7: `prompts/tests/test_bulk_generator_job.py` (NEW)

**Current State:** Does not exist.

**Tests to write:**

1. **View access tests:**
   - Staff user can access job page → 200
   - Non-staff user gets redirected → 302
   - Anonymous user gets redirected → 302
   - Invalid job_id returns 404
   - Valid job_id returns 200 with correct template

2. **Context tests:**
   - Context contains `job` object
   - Context contains `cost_per_image` (correct value based on job settings)
   - Context contains `total_images` (correct calculation)
   - Context contains `estimated_total_cost` (correct calculation)

3. **Template tests:**
   - Template contains `data-job-id` attribute
   - Template contains `data-cost-per-image` attribute
   - Template contains progress bar elements
   - Template contains cancel button

4. **Cost calculation tests:**
   - Test all quality × size combinations from IMAGE_COST_MAP
   - Test that cost_per_image matches expected values

**Minimum test count: 10 tests**

**Test pattern:** Follow the same patterns used in `test_bulk_generator_views.py`. Use the same test fixtures and setup.

---

## 🔄 DATA MIGRATION

### Does this change affect existing data?

- [x] **NO** — This change only adds a new page view. No model changes, no migrations needed. Existing BulkGenerationJob records (if any exist from testing) will display correctly on the new page.

---

## ✅ PRE-AGENT SELF-CHECK (Required Before Running Any Agent)

⛔ **Before invoking ANY agent, CC must manually verify these items:**

- [ ] **DOM nesting matches tree diagram** — Open `bulk_generator_job.html` and trace the nesting. Are `.progress-stats-row`, `.progress-bar-container`, `.progress-details-row`, and `.progress-status-message` all SIBLINGS under `.job-progress-section`?
- [ ] **No text using --gray-400 or lighter** — Search CSS for `gray-400`. If found on any text element, fix before agent run
- [ ] **Focus management on cancel** — After cancel POST succeeds, does focus move to `.progress-status-message`?
- [ ] **aria-valuenow updates** — Does the JS update `aria-valuenow` on every poll cycle?
- [ ] **Progress bar has role="progressbar"** — Check the HTML
- [ ] **CSRF token handling** — Does the cancel POST include the CSRF token?
- [ ] **Data attributes read correctly** — Does JS read from `#bulk-generator-job` data attributes, not hardcoded values?
- [ ] **All tests pass** — Run `python manage.py test prompts` before calling agents

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

### Required Agents (Minimum 3)

**1. @django-pro**
- Task: Review view function, URL pattern, template context, test coverage
- Focus: Staff permission enforcement, `get_object_or_404` usage, context data correctness, cost calculation accuracy
- Rating requirement: 8+/10

**2. @ui-reviewer**
- Task: Review DOM structure, CSS styling, responsive behavior
- Focus: DOM nesting matches tree diagram EXACTLY, progress bar accessibility, responsive stacking below 768px, consistent use of CSS variables
- Rating requirement: 8+/10

**3. @accessibility**
- Task: Review ARIA attributes, live regions, focus management, contrast
- Focus: `role="progressbar"` with correct aria attributes, `aria-live="polite"` on status text, focus management after cancel, text contrast on all elements
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:

- **UI Agent:** DOM nesting does not match the tree diagram — especially the 4 children of `.job-progress-section` must be siblings
- **UI Agent:** Progress bar missing `role="progressbar"` or aria attributes
- **Accessibility Agent:** Status text area missing `aria-live="polite"`
- **Accessibility Agent:** Cancel button click doesn't manage focus after completion
- **Accessibility Agent:** Any text element uses `--gray-400` or lighter
- **Django Expert:** View doesn't enforce staff-only access
- **Django Expert:** Cost calculation doesn't cover all quality × size combinations
- **Code Reviewer:** JS modifies any existing file other than the one redirect line in `bulk-generator.js`

**These are non-negotiable. Do not rate above 7 if any of the above are present.**

### Agent Reporting Format

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. [Agent Name] - [Rating/10] - [Brief findings]
2. [Agent Name] - [Rating/10] - [Brief findings]
3. [Agent Name] - [Rating/10] - [Brief findings]

Critical Issues Found: [Number]
High Priority Issues: [Number]
Recommendations Implemented: [Number]

Overall Assessment: [APPROVED/NEEDS REVIEW]
```

---

## 🖥️ TEMPLATE / UI CHANGE DETECTION

**This spec creates new templates and static files — MANUAL BROWSER CHECK is MANDATORY.**

### MANUAL BROWSER CHECK (Required)

⚠️ **DO NOT commit until the developer has visually verified in a browser.**

After implementation, the developer MUST:
1. Create a BulkGenerationJob in Django shell or admin for testing
2. Visit `/tools/bulk-ai-generator/job/<job_id>/` while logged in as staff
3. Verify job summary header displays settings correctly
4. Verify progress bar renders with correct styling
5. Verify cost display shows formatted dollar amounts
6. Verify cancel button is visible and styled
7. Verify status message is visible
8. Check layout at desktop width (1200px+)
9. Check layout at tablet width (~768px)
10. Check layout at mobile width (~375px)
11. Verify no overlapping elements, broken layout, or text wrapping issues

**CC agents cannot verify visual rendering — only a human in a browser can.**

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation Testing

- [ ] Run `python manage.py test` — confirm 914+ tests pass
- [ ] Review existing bulk generator test patterns in `test_bulk_generator_views.py`

### Post-Implementation Testing

- [ ] New test file `test_bulk_generator_job.py` has minimum 10 tests
- [ ] All new tests pass individually: `python manage.py test prompts.tests.test_bulk_generator_job -v 2`
- [ ] Staff access returns 200
- [ ] Non-staff access returns 302
- [ ] Invalid job_id returns 404
- [ ] Cost calculations are correct for all quality × size combinations
- [ ] Template renders correct data attributes

### Regression Testing

- [ ] Existing bulk generator tests still pass: `python manage.py test prompts.tests.test_bulk_generator_views -v 2`
- [ ] Source credit tests still pass: `python manage.py test prompts.tests.test_source_credit -v 2`

### ⛔ FULL SUITE GATE (Required — Do NOT skip)

> Did you modify ANY file in `views/`, `models.py`, `urls.py`, `signals/`, `services/`, `tasks.py`, or `admin.py`?

- **YES** — `views/bulk_generator_views.py` and `urls.py` are modified.
- **→ Run the full test suite:** `python manage.py test`
- All tests must pass. Do NOT skip this step.
- Report total tests run and any failures.

---

## 📊 CC COMPLETION REPORT FORMAT

**After implementation, Claude Code MUST provide this exact report:**

```markdown
═══════════════════════════════════════════════════════════════
BULK GENERATOR PHASE 5A — JOB PAGE FOUNDATION — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

Agents Consulted:
1. [Agent] - [Rating/10] - [Findings]
2. [Agent] - [Rating/10] - [Findings]
3. [Agent] - [Rating/10] - [Findings]

Critical Issues Found: [N]
High Priority Issues: [N]
Recommendations Implemented: [N]
Overall Assessment: [APPROVED/NEEDS REVIEW]

## 📁 FILES CREATED / MODIFIED

| File | Action | Lines |
|------|--------|-------|
| prompts/urls.py | Modified | +1 |
| prompts/views/bulk_generator_views.py | Modified | +~50 |
| prompts/templates/prompts/bulk_generator_job.html | Created | ~XX |
| static/js/bulk-generator-job.js | Created | ~XX |
| static/css/pages/bulk-generator-job.css | Created | ~XX |
| static/js/bulk-generator.js | Modified | +1 (redirect) |
| prompts/tests/test_bulk_generator_job.py | Created | ~XX |

## 🧪 TESTING PERFORMED

- New tests: XX passing
- Full suite: XXX passing, 0 failures
- Manual browser check: [PENDING DEVELOPER VERIFICATION]

## ✅ SUCCESS CRITERIA MET

- [ ] New page loads at /tools/bulk-ai-generator/job/<id>/
- [ ] Staff-only access enforced
- [ ] Progress bar with aria attributes
- [ ] Cost tracker displays correctly
- [ ] Cancel button functional
- [ ] Responsive layout verified
- [ ] All tests pass

## 📝 NOTES

[Model field names used, any deviations from spec, observations]

═══════════════════════════════════════════════════════════════
```

---

## ⚠️ IMPORTANT NOTES

### DO list:
- ✅ Read the existing models and views before writing any code
- ✅ Use actual field names from BulkGenerationJob model
- ✅ Use actual response field names from status API endpoint
- ✅ Create separate JS and CSS files (not in existing bulk-generator files)
- ✅ Follow existing code patterns from the project
- ✅ Use CSS variables from the project's design system
- ✅ Build accessibility in from line one
- ✅ Test all quality × size cost combinations

### DO NOT list:
- ❌ Do NOT modify `bulk-generator.js` beyond the single redirect line
- ❌ Do NOT modify `bulk-generator.css`
- ❌ Do NOT create new database models or migrations
- ❌ Do NOT implement gallery rows, image display, or selection (that's Phases 5B-5D)
- ❌ Do NOT hardcode cost values in JavaScript
- ❌ Do NOT use WebSockets (polling only)
- ❌ Do NOT guess model field names — read the actual model

### Critical Reminders (repeated for emphasis):
> ⛔ **READ THE EXISTING MODELS AND VIEWS FIRST.** The BulkGenerationJob model field names are the source of truth. If this spec says `job.quality` but the model field is `job.image_quality`, use `job.image_quality`.

> ⛔ **SEPARATE JS FILE.** `bulk-generator-job.js` is a NEW file. The only change to `bulk-generator.js` is one redirect line after successful job start.

> ⛔ **DOM NESTING.** The four children of `.job-progress-section` (stats row, bar container, details row, status message) must be SIBLINGS.

---

## 💾 COMMIT STRATEGY

```bash
git add prompts/urls.py prompts/views/bulk_generator_views.py \
  prompts/templates/prompts/bulk_generator_job.html \
  static/js/bulk-generator-job.js static/css/pages/bulk-generator-job.css \
  static/js/bulk-generator.js prompts/tests/test_bulk_generator_job.py

git commit -m "feat(bulk-gen): Phase 5A — Job progress page foundation

- New page at /tools/bulk-ai-generator/job/<job_id>/
- Progress bar with real-time polling (3s interval)
- Cost tracker showing spent vs estimated total
- Time remaining estimate with calibration
- Cancel button with focus management
- Job summary header with setting chips
- Staff-only access enforced
- Redirect from input page after job start
- 10+ new tests, all existing tests passing
- Accessibility: progressbar role, aria-live, focus management
- Responsive: stacks below 768px"
```

---

**END OF SPECIFICATION**

*Phase 5B (Gallery Rows + Image Display) will build on top of this page foundation.*
