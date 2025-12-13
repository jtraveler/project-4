# CLAUDE.md Update Instructions - Phase E Task 4 Completion

**Purpose:** Step-by-step guide for updating CLAUDE.md after Task 4 is 100% complete
**Created:** November 4, 2025
**Use When:** Task 4 (Email Preferences) reaches 100% completion

---

## 📋 OVERVIEW

When you've completed Task 4 (all commits finished, tests passing), you need to update
CLAUDE.md in 3 locations to remove warnings and update status to 100%.

**This document provides exact find/replace text for each location.**

---

## 🎯 WHEN TO USE THIS GUIDE

### Prerequisites (All Must Be True)

✅ Commit 2 complete (admin field fix)
✅ Commit 3 complete (email helper functions)
✅ All tests passing (`python manage.py test prompts`)
✅ Email preferences working in production
✅ Unsubscribe system tested and functional

**If any prerequisite is false, DO NOT update CLAUDE.md yet.**

---

## 📁 LOCATION 1: Project Status Overview (Line ~56)

### Find This Text:

```markdown
  - ⚠️ **Phase E:** User Profiles & Social Foundation ⭐ **85% COMPLETE** (Oct 25 - Nov 4, 2025)
    - ⚠️ **CRITICAL:** Task 4 (Email Preferences) at 75% - See `PHASE_E_TASK4_INCOMPLETE_REMINDER.md`
    - ✅ Task 3: Report Feature (complete)
    - ✅ Task 5: Profile Header Refinements (complete)
    - 📋 Part 1: Public User Profiles (IN PROGRESS - Nov 4, 2025)
  - ✅ **Phase F:** Advanced Admin Tools & UI Refinements ⭐ **COMPLETE** (October 31, 2025)
  - 📋 **Phase G:** Social Features & Activity Feeds (future)
```

### Replace With:

```markdown
  - ✅ **Phase E:** User Profiles & Social Foundation ⭐ **COMPLETE** (October 25 - November [DATE], 2025)
  - ✅ **Phase F:** Advanced Admin Tools & UI Refinements ⭐ **COMPLETE** (October 31, 2025)
  - 📋 **Phase G:** Social Features & Activity Feeds (next)
```

**Important:** Replace `[DATE]` with actual completion date.

---

## 📁 LOCATION 2: Phase E Header (Line ~2070)

### Find This Text:

```markdown
## Phase E: User Profiles & Social Foundation ⚠️

**Status:** 85% COMPLETE (as of November 4, 2025)
**⚠️ CRITICAL INCOMPLETE ITEM:** Task 4 Email Preferences at 75% - Must finish before Phase E sign-off
**See:** `PHASE_E_TASK4_INCOMPLETE_REMINDER.md` for complete details
```

### Replace With:

```markdown
## Phase E: User Profiles & Social Foundation ✅

**Status:** 100% COMPLETE (as of [COMPLETION_DATE])
**Completion Date:** [COMPLETION_DATE]
**Production Verified:** [VERIFICATION_DATE]
**Total Tests:** [NUMBER]/[NUMBER] passing (100% pass rate)
**Next Phase:** Phase G - Social Features & Activity Feeds
**Detailed Spec:** See archived Phase E documentation
```

**Important:** Fill in bracketed placeholders with actual data:
- `[COMPLETION_DATE]` - Date when last commit pushed
- `[VERIFICATION_DATE]` - Date when tested in production
- `[NUMBER]` - Total test count (e.g., "71/71")

---

## 📁 LOCATION 3: Task 4 Warning Section (After Phase E Tasks)

### Find This ENTIRE Section:

```markdown
---

### ⚠️ PHASE E TASK 4 - INCOMPLETE (CRITICAL)

**Status:** 75% Complete - IN PROGRESS
**Priority:** HIGH - Must complete before Phase E can be marked as done
**Created:** November 4, 2025

**Why This Section Exists:**
During Phase E implementation, we strategically started Part 1 (User Profiles) before
completing Task 4 (Email Preferences). This section ensures Task 4 is NOT forgotten.

**What's Complete (75%):**
- ✅ EmailPreferences model
- ✅ EmailPreferencesAdmin
- ✅ email_preferences() view
- ✅ EmailPreferencesForm
- ✅ settings_notifications.html template
- ✅ Signal for auto-creation
- ✅ Backup/restore commands
- ✅ Safety tests

**What's INCOMPLETE (25%):**
- ❌ Field mismatch issue (Commit 2)
- ❌ Email helper functions (Commit 3)
- ❌ should_send_notification() function
- ❌ Unsubscribe system
- ❌ Email template footer updates

**FULL DETAILS:** See `PHASE_E_TASK4_INCOMPLETE_REMINDER.md` (15 KB comprehensive guide)

**Complete This Before:**
- Starting Phase G
- Marking Phase E as 100% complete
- Implementing any new notification features

---
```

### Replace With:

```markdown
---

### ✅ PHASE E TASK 4 - COMPLETE

**Status:** 100% Complete ✅
**Completion Date:** [COMPLETION_DATE]
**Priority:** ~~HIGH~~ → COMPLETE

**Final Implementation:**
- ✅ EmailPreferences model (8 notification types)
- ✅ EmailPreferencesAdmin (all 8 fields in list view)
- ✅ email_preferences() view
- ✅ EmailPreferencesForm
- ✅ settings_notifications.html template
- ✅ Signal for auto-creation
- ✅ Email helper functions (email_utils.py)
- ✅ should_send_email() function
- ✅ get_unsubscribe_url() function
- ✅ Unsubscribe system (view + template)
- ✅ Backup/restore commands
- ✅ Comprehensive tests ([NUMBER] tests passing)

**Commits Completed:**
1. ✅ Commit 1: Core system (model, admin, view, form, template)
2. ✅ Commit 1.5: UX improvements
3. ✅ Commit 2: Admin field mismatch fix
4. ✅ Commit 3: Email helper functions + unsubscribe system

**Files Created:**
- `prompts/email_utils.py` - Email preference helpers
- `prompts/templates/prompts/unsubscribe.html` - Unsubscribe page

**See Archived Documentation:**
- `PHASE_E_TASK4_INCOMPLETE_REMINDER.md` (archived after completion)

---
```

**Important:** Replace bracketed placeholders with actual data.

---

## ✅ VERIFICATION CHECKLIST

After making all 3 updates, verify:

- [ ] Location 1: Status changed from "85% COMPLETE" to "COMPLETE"
- [ ] Location 1: Warning emoji (⚠️) removed, checkmark (✅) added
- [ ] Location 1: Task 4 warning removed
- [ ] Location 2: Header emoji changed from ⚠️ to ✅
- [ ] Location 2: Status changed to "100% COMPLETE"
- [ ] Location 2: Completion date filled in
- [ ] Location 3: Warning section replaced with completion section
- [ ] Location 3: All checkmarks changed from ❌ to ✅
- [ ] Location 3: Commit list shows all 4 commits complete
- [ ] All bracketed placeholders filled in with actual data
- [ ] No typos introduced during find/replace
- [ ] File saved successfully

**Search Verification:**
- [ ] Search CLAUDE.md for "Task 4" - should find completion section (not warning)
- [ ] Search CLAUDE.md for "85%" - should find ZERO results
- [ ] Search CLAUDE.md for "⚠️ CRITICAL" - should find ZERO results (in Phase E section)

---

## 💾 COMMIT STRATEGY

After updating CLAUDE.md:

```bash
git add CLAUDE.md

git commit -m "docs(phase-e): Mark Task 4 as 100% complete, update Phase E status

- Task 4 (Email Preferences) now 100% complete
- Commit 2: Admin field fix complete
- Commit 3: Email helper functions complete
- Phase E status changed from 85% to 100%
- All tests passing ([NUMBER]/[NUMBER])
- Updated 3 locations in CLAUDE.md
- Ready for Phase G implementation"

git push origin main
```

---

## 🗄️ ARCHIVAL INSTRUCTIONS

After completing CLAUDE.md updates:

1. **Move reminder documents to archive:**
   ```bash
   mkdir -p archive/phase-e/task4-completion
   mv PHASE_E_TASK4_INCOMPLETE_REMINDER.md archive/phase-e/task4-completion/
   mv PHASE_E_TASK4_QUICK_REFERENCE.md archive/phase-e/task4-completion/
   mv CLAUDE_MD_UPDATE_INSTRUCTIONS.md archive/phase-e/task4-completion/
   ```

2. **Create archive README:**
   ```bash
   echo "# Phase E Task 4 Completion Documents

These documents were used to track Task 4 completion and are now archived.

- PHASE_E_TASK4_INCOMPLETE_REMINDER.md - Comprehensive guide
- PHASE_E_TASK4_QUICK_REFERENCE.md - Quick status dashboard
- CLAUDE_MD_UPDATE_INSTRUCTIONS.md - CLAUDE.md update guide

**Status:** Task 4 completed on [DATE]
**Archived:** [DATE]" > archive/phase-e/task4-completion/README.md
   ```

3. **Commit archival:**
   ```bash
   git add archive/phase-e/task4-completion/
   git commit -m "archive(phase-e): Archive Task 4 completion tracking documents"
   git push origin main
   ```

---

## 🚨 IMPORTANT NOTES

### Before Using This Guide

1. **Verify Task 4 is Actually Complete:**
   - Don't rely on memory
   - Check all files exist
   - Run all tests
   - Test in production environment

2. **Double-Check File Locations:**
   - `prompts/email_utils.py` exists
   - `prompts/templates/prompts/unsubscribe.html` exists
   - Admin shows all 8 notification fields

3. **Test the System:**
   ```python
   # Django shell
   from prompts.email_utils import should_send_email, get_unsubscribe_url
   from django.contrib.auth.models import User

   user = User.objects.first()
   should_send_email(user, 'comments')  # Should return Boolean
   get_unsubscribe_url(user)  # Should return URL string
   ```

### Common Mistakes

❌ **DON'T:** Update CLAUDE.md if tests are failing
❌ **DON'T:** Forget to fill in bracketed placeholders
❌ **DON'T:** Skip verification checklist
❌ **DON'T:** Archive documents before CLAUDE.md is updated

✅ **DO:** Test everything first
✅ **DO:** Fill in all placeholders with actual data
✅ **DO:** Run verification checklist
✅ **DO:** Commit CLAUDE.md update before archiving

---

## 📞 TROUBLESHOOTING

### Issue: Can't Find Location 1

**Problem:** Line numbers have shifted

**Solution:** Search for "⚠️ **Phase E:**" to find exact location

### Issue: Can't Find Location 2

**Problem:** Phase E header moved

**Solution:** Search for "## Phase E: User Profiles & Social Foundation" to find it

### Issue: Can't Find Location 3

**Problem:** Warning section not where expected

**Solution:** Search for "⚠️ PHASE E TASK 4 - INCOMPLETE" to locate it

### Issue: Bracketed Placeholders Still Present

**Problem:** Forgot to fill in dates/numbers

**Solution:** Search CLAUDE.md for "[" to find all placeholders and fill them in

---

## 📊 EXAMPLE COMPLETED UPDATE

### Example Location 1 (After Update):

```markdown
  - ✅ **Phase E:** User Profiles & Social Foundation ⭐ **COMPLETE** (October 25 - November 8, 2025)
  - ✅ **Phase F:** Advanced Admin Tools & UI Refinements ⭐ **COMPLETE** (October 31, 2025)
  - 📋 **Phase G:** Social Features & Activity Feeds (next)
```

### Example Location 2 (After Update):

```markdown
## Phase E: User Profiles & Social Foundation ✅

**Status:** 100% COMPLETE (as of November 8, 2025)
**Completion Date:** November 8, 2025
**Production Verified:** November 8, 2025
**Total Tests:** 73/73 passing (100% pass rate)
**Next Phase:** Phase G - Social Features & Activity Feeds
**Detailed Spec:** See archived Phase E documentation
```

### Example Location 3 (After Update):

```markdown
### ✅ PHASE E TASK 4 - COMPLETE

**Status:** 100% Complete ✅
**Completion Date:** November 8, 2025
**Priority:** ~~HIGH~~ → COMPLETE

[Rest of completion section with checkmarks...]
```

---

**Document Created:** November 4, 2025
**Use When:** Task 4 reaches 100% completion
**Estimated Time:** 15 minutes to complete all updates

---

**END OF UPDATE INSTRUCTIONS**

*Keep this document until Task 4 is complete, then archive it.*
