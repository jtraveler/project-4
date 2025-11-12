# BUG REPORT: Back Button Shows Ghost Deleted Prompt

**Date Reported:** November 5, 2025  
**Reported By:** Matthew  
**Severity:** 🔴 MEDIUM-HIGH - Confusing UX, leads to 404  
**Status:** ⏳ PENDING FIX  
**Found During:** Phase E Performance Optimization Testing  

---

## 📋 SUMMARY

After deleting a prompt and being redirected to homepage, using the browser back button shows the deleted prompt's detail page with the "Move to trash" modal still visible. Clicking either modal option leads to a 404 error page, creating a confusing and broken user experience.

---

## 🔍 ISSUE DETAILS

### **What Happens:**
1. User views a prompt detail page (e.g., `/prompt/my-awesome-prompt/`)
2. User clicks "Delete" button
3. User confirms deletion in modal ("Move to trash")
4. Prompt is soft-deleted (moved to trash)
5. User is redirected to homepage with success notification ✅
6. User clicks browser **Back button**
7. ❌ Old prompt detail page appears (still cached in browser)
8. ❌ Page shows the prompt content (even though it's deleted)
9. ❌ "Move to trash" modal is still visible/accessible
10. User sees two options: "Cancel" and "Move to trash"
11. User clicks either option
12. ❌ **404 error page** appears

### **Expected Behavior:**
When user clicks back button after deleting prompt:
- **Option A:** Redirect to appropriate page (previous page, trash, or homepage)
- **Option B:** Show "This prompt has been deleted" message with link to trash
- **Option C:** Detect deleted prompt and redirect automatically

### **Actual Behavior:**
- Browser shows cached version of deleted prompt page
- Modal appears functional but isn't
- Both modal options lead to 404 error
- Very confusing for users

---

## 🎯 IMPACT ASSESSMENT

**User Experience:** 🔴 MEDIUM-HIGH IMPACT
- Creates false impression prompt still exists
- Modal options appear functional but aren't
- Leads to 404 error (dead end)
- Confusing: "Can I undo? No? Why show me options?"
- Damages trust in application reliability

**Frequency:** MEDIUM
- Happens whenever user uses back button after delete
- Some users habitually use back button
- More common on mobile (gesture-based back navigation)

**Data Loss Risk:** NONE
- No data affected
- Prompt already safely in trash
- Can be restored from trash if needed

**Workaround Available:** YES
- User can navigate forward or use site navigation
- Not blocked from using site
- Just confusing experience

---

## 🔧 ROOT CAUSE ANALYSIS

**Primary Cause: Browser Cache + Soft Delete Pattern**

1. **Browser Back Button Caching:**
   - Browser caches prompt detail page
   - Back button shows cached version
   - Django doesn't re-run view logic
   - Deleted prompt appears to exist

2. **Soft Delete Not Checked:**
   - `prompt_detail` view doesn't check `deleted_at` field
   - Allows access to deleted prompts via direct URL
   - Should redirect or show error for deleted prompts

3. **Modal Still Functional:**
   - Modal HTML already loaded in cached page
   - JavaScript still executes
   - POST request goes to deleted prompt URL
   - Returns 404 because prompt effectively gone

**Technical Details:**
- Django view: `prompt_detail(request, slug)`
- Current logic: `get_object_or_404(Prompt, slug=slug, status=1)`
- Problem: Doesn't filter out `deleted_at__isnull=False`
- Soft-deleted prompts accessible via URL

---

## 📁 FILES TO INVESTIGATE

**Views:**
- `prompts/views.py` - `prompt_detail` function (needs deleted_at check)
- `prompts/views.py` - `prompt_delete` function (redirect logic)

**Models:**
- `prompts/models.py` - Soft delete implementation

**Templates:**
- `prompts/templates/prompts/prompt_detail.html` - Add meta tags for no-cache?

---

## 🧪 REPRODUCTION STEPS

**Setup:**
1. Login to application
2. Create or select a test prompt
3. Note the prompt slug/URL

**Steps to Reproduce:**
1. Navigate to prompt detail page: `/prompt/test-prompt/`
2. Click "Delete" button
3. Confirm "Move to trash" in modal
4. Observe: Redirected to homepage with "View trash" notification ✅
5. Click browser **Back button** (or swipe back on mobile)
6. Observe: Old prompt page appears (CACHED)
7. Observe: Page shows prompt content and "Move to trash" modal
8. Click either "Cancel" or "Move to trash" button
9. Result: ❌ **404 error page**

**Environment:**
- Browser: All browsers (Chrome, Firefox, Safari, Edge)
- Device: Desktop and mobile
- Deployment: Both local development and Heroku production
- Django: 5.2.3

---

## 💡 PROPOSED SOLUTIONS

### **Solution A: Check deleted_at in prompt_detail View** ✅ RECOMMENDED

**Implementation:**
```python
# In prompts/views.py - prompt_detail function

def prompt_detail(request, slug):
    """Display prompt detail page, redirect if deleted"""
    
    # Get prompt
    prompt_queryset = Prompt.objects.select_related('author').prefetch_related(...)
    
    if request.user.is_authenticated:
        prompt = get_object_or_404(prompt_queryset, slug=slug)
        
        # ✅ CHECK IF DELETED
        if prompt.deleted_at is not None:
            # Prompt is in trash
            if prompt.author == request.user or request.user.is_staff:
                # Owner/staff can view in trash
                messages.info(request, 
                    'This prompt is in your trash. You can restore it from there.')
                return redirect('prompts:trash_bin')
            else:
                # Others cannot access deleted prompts
                raise Http404("Prompt not found")
        
        # Check permission for drafts
        if prompt.status != 1 and prompt.author != request.user:
            raise Http404("Prompt not found")
    else:
        prompt = get_object_or_404(
            prompt_queryset, 
            slug=slug, 
            status=1,
            deleted_at__isnull=True  # ✅ ALSO CHECK FOR ANONYMOUS USERS
        )
    
    # ... rest of view logic
```

**Benefits:**
- Catches deleted prompts immediately
- Provides helpful message to owner
- Redirects to trash (where they can restore)
- Clean user experience
- Prevents 404 confusion

---

### **Solution B: Add Cache-Control Headers**

**Prevent browser caching of prompt detail pages:**

```python
from django.views.decorators.cache import never_cache

@never_cache
def prompt_detail(request, slug):
    # ... existing logic
```

**Or in template:**
```html
<!-- In prompt_detail.html head -->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

**Benefits:**
- Prevents browser caching issue
- Back button always re-runs Django view
- Works for all browsers

**Drawbacks:**
- Hurts performance (no caching at all)
- Every back button = full page reload
- Overkill for this specific issue

---

### **Solution C: JavaScript Back Button Handler** ⚠️ NOT RECOMMENDED

**Detect back navigation and refresh:**

```javascript
// In prompt_detail.html
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        // Page loaded from cache (back button)
        location.reload();
    }
});
```

**Drawbacks:**
- Fragile (doesn't work in all browsers)
- Performance impact
- Doesn't solve root cause
- Better to fix server-side

---

### **Recommended Approach:**

**Implement Solution A** (deleted_at check in view)

**Why:**
- Solves root cause
- Clean user experience  
- Minimal code change
- Works in all browsers
- No performance impact
- Provides helpful redirect

**Time Estimate:** 45-60 minutes
- Add deleted_at check: 15 minutes
- Test with browser back button: 15 minutes
- Test as owner vs non-owner: 10 minutes
- Test on mobile: 10 minutes
- Deploy and verify: 10 minutes

---

## ✅ TESTING CHECKLIST

**After fix is implemented:**

**Basic Functionality:**
- [ ] Delete a prompt
- [ ] Click back button
- [ ] Verify: Redirected appropriately (not 404)
- [ ] Verify: Helpful message shown

**Owner vs Non-Owner:**
- [ ] Owner clicks back → Should redirect to trash with message
- [ ] Non-owner clicks back → Should show 404 or "Prompt not found"
- [ ] Staff clicks back → Should redirect to trash (can access trash)

**Anonymous Users:**
- [ ] Anonymous user views prompt
- [ ] Owner deletes prompt (in another browser/tab)
- [ ] Anonymous refreshes → Should show 404
- [ ] Anonymous uses back button → Should show 404

**Edge Cases:**
- [ ] Prompt in trash, owner restores, clicks back → Shows prompt ✅
- [ ] Prompt in trash, owner permanently deletes → 404 ✅
- [ ] Prompt deleted by another user → 404 ✅

**Browsers:**
- [ ] Chrome (desktop)
- [ ] Firefox (desktop)
- [ ] Safari (desktop)
- [ ] Mobile Safari (iPhone)
- [ ] Mobile Chrome (Android)

**Devices:**
- [ ] Desktop (mouse + keyboard)
- [ ] Mobile (touch + gestures)
- [ ] Tablet

---

## 📊 PRIORITY JUSTIFICATION

**Why MEDIUM-HIGH Priority:**

1. **Affects User Trust:**
   - Makes app appear broken
   - "Why show me options that don't work?"
   - Damages perceived quality

2. **Common User Pattern:**
   - Many users habitually use back button
   - Especially mobile users (swipe gesture)
   - Happens frequently enough to be noticeable

3. **Relatively Easy Fix:**
   - Solution A is straightforward
   - 1 hour or less to implement
   - Low risk change (just adds check)

4. **Not Critical Because:**
   - Doesn't lose data
   - Doesn't break core functionality
   - Workaround available (use site navigation)
   - Only confusing, not breaking

---

## 📝 NOTES

**Related Considerations:**

1. **Trash Access:**
   - Owner should always be able to access their trash
   - Staff should be able to access all trash
   - Non-owners should never see deleted prompts

2. **Soft Delete Pattern:**
   - This bug reveals gap in soft delete implementation
   - Need to consistently check `deleted_at` across all views
   - Consider creating a manager method: `Prompt.objects.active()`

3. **Future Prevention:**
   - Could create custom QuerySet method
   - Could add middleware to check deleted_at globally
   - Could add automated tests for soft-delete edge cases

**Example QuerySet Method:**
```python
class PromptQuerySet(models.QuerySet):
    def active(self):
        """Return only non-deleted prompts"""
        return self.filter(deleted_at__isnull=True)
    
    def in_trash(self):
        """Return only deleted prompts"""
        return self.filter(deleted_at__isnull=False)

class Prompt(models.Model):
    objects = PromptQuerySet.as_manager()
    all_objects = models.Manager()  # Access all including deleted
```

Then: `Prompt.objects.active().get(slug=slug)`

---

## 🔗 RELATED ISSUES

**Related to:**
- Soft delete implementation
- Browser caching behavior
- User experience consistency

**Could affect:**
- Other views that access soft-deleted models
- Comment access on deleted prompts
- Like/unlike on deleted prompts

**Should also check:**
- Do any other views need `deleted_at` checks?
- Are there other back-button edge cases?

---

**Status:** Ready for implementation  
**Assigned To:** TBD  
**Target Fix Date:** TBD  
**Estimated Fix Time:** 45-60 minutes (including testing)  
**Recommended Solution:** Solution A (deleted_at check in view)  

---

**END OF BUG REPORT**
