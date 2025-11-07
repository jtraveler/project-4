# Bug 2 Testing Checklist

**CRITICAL:** Please clear your browser cache before testing!

Chrome: Settings → Privacy → Clear browsing data → Cached images and files

---

## ✅ Test 1: Owner Back Button (PRIMARY TEST)

**Steps:**
1. ✅ Clear browser cache
2. ✅ Log in as prompt owner
3. ✅ Go to one of your prompt detail pages
4. ✅ Click delete icon → Modal appears
5. ✅ Click "Move to Trash" → Redirected to homepage
6. ✅ **CLICK BACK BUTTON**

**Expected:**
- Redirects to trash bin page
- Shows message: "This prompt 'X' is in your trash. You can restore it from there."

**Pass/Fail:** _____________

---

## ✅ Test 2: Non-Owner Access (OPTIONAL)

**Steps:**
1. ✅ Log out
2. ✅ Log in as different user
3. ✅ Try to access deleted prompt URL directly

**Expected:**
- 404 error page

**Pass/Fail:** _____________

---

## ✅ Test 3: Anonymous Access (OPTIONAL)

**Steps:**
1. ✅ Log out completely
2. ✅ Try to access deleted prompt URL

**Expected:**
- 404 error page

**Pass/Fail:** _____________

---

## Result

**If Test 1 passes, respond with:** "Test 1 passed - please commit Bug 2"

**If Test 1 fails, respond with:** "Test 1 failed - still seeing ghost prompt page"

---

**Files Modified:**
- `prompts/views.py` (prompt_detail: lines 259-280)
- `prompts/views.py` (prompt_delete: line 788 simplified)

**Root Cause:**
Browser HTTP cache was storing prompt detail pages. Previous fix added cache headers to redirect (wrong location). New fix adds cache headers to prompt_detail view response (correct location).

**Solution:**
Prevent browser from caching prompt detail pages at all, forcing fresh server request on back button.
