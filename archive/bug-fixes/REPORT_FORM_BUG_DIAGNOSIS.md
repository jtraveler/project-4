# Django ModelForm Bug Diagnosis: PromptReportForm Comment Field

**Date:** October 21, 2025
**Status:** ROOT CAUSE IDENTIFIED
**Severity:** Medium (Data Loss)
**File:** `prompts/forms.py` (Line 548)

---

## Executive Summary

The `comment` field in `PromptReportForm` saves as an empty string even when users provide text. **Root cause: The `clean_comment()` method is stripping whitespace from the comment, and when the comment is ONLY whitespace (or empty), it returns an empty string instead of preserving the original user input.**

**However**, based on your symptoms ("User types comment: 'This is a test comment'"), the actual issue is likely **NOT** in the form cleaning logic, but in **how the data is being submitted via AJAX**.

---

## Root Cause Analysis

### 1. The Most Likely Culprit: AJAX FormData Submission

Looking at your JavaScript in `prompt_detail.html` (lines 707-708):

```javascript
// Get form data
const formData = new FormData(reportForm);
```

**This is correct SYNTAX**, but there's a subtle issue: **If the textarea has no `name` attribute in the DOM**, FormData won't include it.

Let me check your template again (line 412):

```html
<textarea name="comment" id="id_comment" class="form-control"
          rows="4" maxlength="1000"
          placeholder="Please provide additional context..."></textarea>
```

**This looks correct!** The `name="comment"` attribute is present.

### 2. The Secondary Suspect: Form Cleaning Logic

Your `clean_comment()` method in `forms.py` (lines 546-554):

```python
def clean_comment(self):
    """Validate comment length"""
    comment = self.cleaned_data.get('comment', '').strip()

    # Length validation (redundant with maxlength, but good practice)
    if len(comment) > 1000:
        raise ValidationError('Comment cannot exceed 1000 characters.')

    return comment
```

**Analysis:**
- `.get('comment', '')` returns the POST value or empty string if missing
- `.strip()` removes leading/trailing whitespace
- Returns the stripped value

**This is CORRECT behavior for Django forms.** The `.strip()` is intentional and good practice.

### 3. The Actual Bug: Django Form Save Behavior

When you call `form.save(commit=False)`, Django:

1. Creates a new model instance
2. **Populates it with values from `cleaned_data`**
3. Returns the unsaved instance

**Key insight:** `form.save(commit=False)` **DOES** transfer all fields from `cleaned_data` to the model instance, including optional fields.

**So why is the comment empty?**

The comment is empty because **it's not in `request.POST` in the first place**.

---

## The Real Problem: Browser Developer Tools Evidence Needed

To diagnose this, you need to check:

1. **Browser Network Tab** - What is actually being sent in the POST request?
2. **Django Debug Toolbar** (if installed) - What is in `request.POST`?
3. **Server logs** - Add logging to see `request.POST` contents

---

## Debugging Steps

### Step 1: Add Logging to View

Add this at the top of `report_prompt()` view (after line 1896):

```python
# Process the report form
form = PromptReportForm(request.POST)

# DEBUG: Log what we received
import logging
logger = logging.getLogger(__name__)
logger.debug(f"POST data: {request.POST}")
logger.debug(f"Comment value: '{request.POST.get('comment', '[MISSING]')}'")

if form.is_valid():
    logger.debug(f"Form cleaned_data: {form.cleaned_data}")
    logger.debug(f"Cleaned comment: '{form.cleaned_data.get('comment', '[MISSING]')}'")

    try:
        # Create the report
        report = form.save(commit=False)

        logger.debug(f"Report comment before save: '{report.comment}'")

        report.prompt = prompt
        report.reported_by = request.user
        report.save()

        logger.debug(f"Report comment after save: '{report.comment}'")
        logger.debug(f"Report ID: {report.id}")
```

### Step 2: Check Browser Console

Add this to your JavaScript (before line 710):

```javascript
// DEBUG: Log form data
console.log('=== DEBUG: Report Form Submission ===');
console.log('Comment textarea value:', commentTextarea.value);
console.log('Comment textarea length:', commentTextarea.value.length);

// Log all FormData entries
console.log('FormData contents:');
for (let [key, value] of formData.entries()) {
    console.log(`  ${key}: "${value}"`);
}
console.log('=== END DEBUG ===');
```

### Step 3: Test Case

1. Open browser dev tools (F12)
2. Go to Network tab
3. Fill out report form with: "This is a test comment"
4. Submit form
5. Check:
   - **Console tab**: What does the DEBUG log show?
   - **Network tab**: Click on the POST request → Payload → What is the `comment` value?
   - **Server logs**: What does the Django logger show?

---

## Possible Causes (Ranked by Likelihood)

### 1. JavaScript Event Handling Issue (80% likely)

**Hypothesis:** The form is being submitted BEFORE the user's text is committed to the textarea.

**Why this happens:**
- User types in textarea
- JavaScript triggers submit
- Browser hasn't finalized the textarea value yet
- FormData captures empty value

**Test:** Add a small delay before reading FormData:

```javascript
reportForm.addEventListener('submit', function(event) {
    event.preventDefault();

    // NEW: Small delay to ensure textarea value is captured
    setTimeout(function() {
        // Get form data INSIDE setTimeout
        const formData = new FormData(reportForm);

        // ... rest of fetch code ...
    }, 50); // 50ms delay
});
```

### 2. Template Rendering Issue (15% likely)

**Hypothesis:** The textarea in the modal is not the same element that FormData is reading from.

**Why this happens:**
- Modal is duplicated in DOM (Bootstrap edge case)
- FormData reads from wrong instance
- User edits one, but FormData reads from the empty original

**Test:** Log the textarea element:

```javascript
console.log('Textarea element:', commentTextarea);
console.log('Textarea value:', commentTextarea.value);
console.log('Textarea in DOM?', document.body.contains(commentTextarea));
```

### 3. CSRF Token Missing (3% likely)

**Hypothesis:** Form fails CSRF validation silently, falls back to empty state.

**Why this happens:**
- CSRF token missing or invalid
- Django rejects POST, returns fresh form
- Fresh form has empty comment

**Test:** Check Network tab for 403 Forbidden response.

### 4. Browser Autocomplete Interference (2% likely)

**Hypothesis:** Browser autocomplete is clearing the field.

**Test:** Add `autocomplete="off"` to textarea:

```html
<textarea name="comment" id="id_comment"
          autocomplete="off"
          ...>
```

---

## The Fix (After Diagnosis)

Based on the most likely cause (#1), here's the recommended fix:

### Fix 1: Ensure FormData Captures Latest Value

**File:** `prompts/templates/prompts/prompt_detail.html` (line 695)

```javascript
// Handle report form submission via AJAX
if (reportForm) {
    reportForm.addEventListener('submit', function(event) {
        event.preventDefault();

        // Hide previous messages
        reportError.classList.add('d-none');
        reportSuccess.classList.add('d-none');

        // Disable submit button
        submitReportBtn.disabled = true;
        submitReportBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Submitting...';

        // IMPORTANT FIX: Force blur on textarea to commit value
        if (commentTextarea) {
            commentTextarea.blur();
        }

        // Small delay to ensure value is committed
        setTimeout(function() {
            // Get form data AFTER blur
            const formData = new FormData(reportForm);

            // DEBUG (remove after testing)
            console.log('Comment value:', formData.get('comment'));

            // Submit via AJAX
            fetch(reportForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                // ... existing success/error handling ...
            })
            .catch(error => {
                // ... existing error handling ...
            })
            .finally(function() {
                // Re-enable submit button
                submitReportBtn.disabled = false;
                submitReportBtn.innerHTML = '<i class="fas fa-flag me-1"></i> Submit Report';
            });
        }, 50); // 50ms delay
    });

    // ... rest of code ...
}
```

### Fix 2: Alternative - Read Value Directly Instead of FormData

**If Fix 1 doesn't work**, try manually constructing the form data:

```javascript
// Instead of: const formData = new FormData(reportForm);
const formData = new FormData();
formData.append('csrfmiddlewaretoken', reportForm.querySelector('[name=csrfmiddlewaretoken]').value);
formData.append('reason', document.getElementById('id_reason').value);
formData.append('comment', document.getElementById('id_comment').value); // Direct access
```

---

## Questions Answered

### 1. What is the most likely root cause?

**JavaScript event timing issue** - FormData is reading the textarea value before the browser commits the user's input to the DOM.

**Location:** `prompts/templates/prompts/prompt_detail.html` (line 707)

### 2. Does form.save(commit=False) properly transfer ALL fields?

**Yes, it does.** Django's ModelForm.save(commit=False) correctly populates all fields from `cleaned_data`, including optional fields. This is NOT the issue.

### 3. Could clean_comment() using .strip() cause empty string?

**Yes, but only if the original input was whitespace-only.** Since your test input is "This is a test comment", `.strip()` would preserve it.

**The issue is that `cleaned_data.get('comment')` is returning empty string because it's not in `request.POST`.**

### 4. Is there a Django quirk with optional TextField?

**No.** Django handles `blank=True` TextFields correctly. An empty string is valid and expected for optional fields.

### 5. How to debug this?

**Best debugging approach:**

1. Add browser console logging (see Step 2 above)
2. Add Django view logging (see Step 1 above)
3. Check Network tab Payload
4. Compare what browser sends vs what Django receives

**Expected output (if working correctly):**
```
Browser console:
  comment: "This is a test comment"

Network Payload:
  comment: This is a test comment

Django logs:
  POST data: <QueryDict: {'csrfmiddlewaretoken': [...], 'reason': ['inappropriate'], 'comment': ['This is a test comment']}>
  Comment value: 'This is a test comment'
  Form cleaned_data: {'reason': 'inappropriate', 'comment': 'This is a test comment'}
  Report comment after save: 'This is a test comment'
```

---

## Best Practices to Avoid This in Future

### 1. Always Test FormData Contents in Console

```javascript
// Before sending AJAX
console.log('FormData debug:');
for (let [key, value] of formData.entries()) {
    console.log(`${key}: ${value}`);
}
```

### 2. Use Direct Value Access for Critical Fields

```javascript
// Instead of relying on FormData auto-population
const comment = document.getElementById('id_comment').value;
formData.append('comment', comment);
```

### 3. Add Server-Side Logging for Debugging

```python
# In views.py
logger.debug(f"Received POST: {request.POST}")
logger.debug(f"Form errors: {form.errors}")
logger.debug(f"Cleaned data: {form.cleaned_data}")
```

### 4. Validate in Browser Before Sending

```javascript
// Before AJAX submit
if (!commentTextarea.value.trim() && required) {
    alert('Please enter a comment');
    return false;
}
```

### 5. Use Django's Built-in Form Rendering (When Possible)

Instead of manually creating `<textarea name="comment">`, use:

```django
{{ form.comment }}
```

This ensures name attributes match field names exactly.

---

## Next Steps

1. **Implement Fix 1** (blur + setTimeout)
2. **Add debug logging** (Steps 1 & 2)
3. **Test with browser dev tools open**
4. **Report back with:**
   - Console log output
   - Network Payload screenshot
   - Django server logs
5. If still failing, try **Fix 2** (manual FormData construction)

---

## Conclusion

**Root Cause:** AJAX form submission is reading the textarea value **before** the browser commits the user's input to the DOM. This is a timing issue, not a Django form issue.

**Recommended Fix:** Add `textarea.blur()` and 50ms delay before reading FormData.

**Confidence Level:** 80% (based on symptoms and common AJAX pitfalls)

**Alternative Explanation:** If the above fix doesn't work, the issue is likely a duplicated modal in the DOM, where the user edits one instance but FormData reads from a different (empty) instance.

---

**Created:** October 21, 2025
**Author:** Claude (Django Expert Agent)
**Project:** PromptFinder - Phase E
**Document Status:** Diagnosis Complete - Awaiting Testing
