# Phase E Task 4 - Quick Reference Card

**Created:** November 4, 2025
**Status:** 75% Complete → 🎯 Target: 100%
**Priority:** 🔴 HIGH

---

## 📊 VISUAL STATUS DASHBOARD

```
███████████████████░░░░░ 75% Complete

✅ Commit 1: Core System (DONE)
✅ Commit 1.5: UX Improvements (DONE)
❌ Commit 2: Admin Field Fix (PENDING)
❌ Commit 3: Email Helpers (PENDING)
```

---

## 🎯 WHAT'S NEEDED TO REACH 100%

### Commit 2: Fix Admin Field Mismatch (10% Remaining)

**File:** `prompts/admin.py`
**Time:** 10 minutes
**Action:** Add 2 missing fields to list_display

```python
# ADD THESE TWO LINES TO list_display:
'notify_mentions',      # ← ADD after notify_likes
'notify_weekly_digest', # ← ADD after notify_mentions
```

**Status:** ❌ PENDING

---

### Commit 3: Create Email Helper Functions (15% Remaining)

**Files to Create:**
1. `prompts/email_utils.py` (~90 lines)
2. `prompts/templates/prompts/unsubscribe.html` (~30 lines)

**Files to Verify:**
- `prompts/views.py` - Check unsubscribe_view() exists

**Functions Needed:**
- `should_send_email(user, notification_type)` → Boolean
- `get_unsubscribe_url(user)` → String (URL)

**Time:** 45 minutes

**Status:** ❌ PENDING

---

## 🚀 QUICK ACTION CHECKLIST

### Immediate Next Steps (Copy & Execute)

**Step 1: Commit 2 (10 min)**
```bash
# 1. Open prompts/admin.py
# 2. Find EmailPreferencesAdmin class
# 3. Add notify_mentions and notify_weekly_digest to list_display
# 4. Save file
# 5. Test in admin panel (/admin/prompts/emailpreferences/)
# 6. Commit: "fix(admin): Add missing notify fields to EmailPreferences admin"
```

**Step 2: Commit 3 (45 min)**
```bash
# 1. Create prompts/email_utils.py (copy from reminder doc)
# 2. Verify prompts/views.py has unsubscribe_view()
# 3. Create prompts/templates/prompts/unsubscribe.html
# 4. Test in Django shell:
#    from prompts.email_utils import should_send_email
#    should_send_email(user, 'comments')  # Test
# 5. Test unsubscribe URL in browser
# 6. Commit: "feat(email): Add email preference helpers and unsubscribe"
```

**Step 3: Mark Complete**
```bash
# 1. Update PHASE_E_TASK4_QUICK_REFERENCE.md (this file) to 100%
# 2. Follow CLAUDE_MD_UPDATE_INSTRUCTIONS.md
# 3. Update CLAUDE.md in 3 locations
# 4. Archive all reminder documents
```

---

## 📋 MINI CHECKLIST (Tick as You Go)

### Commit 2: Admin Fix
- [ ] Opened prompts/admin.py
- [ ] Found EmailPreferencesAdmin
- [ ] Added notify_mentions
- [ ] Added notify_weekly_digest
- [ ] Saved file
- [ ] Tested in admin
- [ ] Committed

### Commit 3: Email Helpers
- [ ] Created email_utils.py
- [ ] Added should_send_email() function
- [ ] Added get_unsubscribe_url() function
- [ ] Verified unsubscribe_view() exists
- [ ] Created unsubscribe.html template
- [ ] Tested in Django shell
- [ ] Tested in browser
- [ ] Committed

### Final Steps
- [ ] Updated this quick reference to 100%
- [ ] Updated CLAUDE.md (3 locations)
- [ ] Archived reminder documents
- [ ] Marked Phase E as 100% complete

---

## ⏰ TIME ESTIMATES

| Task | Time | Difficulty |
|------|------|------------|
| Commit 2 | 10 min | 🟢 Easy |
| Commit 3 | 45 min | 🟡 Medium |
| **TOTAL** | **55 min** | **1 hour max** |

---

## 📍 FILE LOCATIONS (Quick Access)

### Files to Modify
- `prompts/admin.py` - Line ~45 (EmailPreferencesAdmin)
- `prompts/views.py` - Check for unsubscribe_view()

### Files to Create
- `prompts/email_utils.py` (NEW)
- `prompts/templates/prompts/unsubscribe.html` (NEW)

### Documentation Files
- `PHASE_E_TASK4_INCOMPLETE_REMINDER.md` - Full guide (15 KB)
- `CLAUDE_MD_UPDATE_INSTRUCTIONS.md` - CLAUDE.md update steps
- `PHASE_E_TASK4_QUICK_REFERENCE.md` - This file

---

## 🔗 RELATED LINKS

- **Full Details:** See `PHASE_E_TASK4_INCOMPLETE_REMINDER.md`
- **Update Guide:** See `CLAUDE_MD_UPDATE_INSTRUCTIONS.md`
- **CLAUDE.md:** Search for "Phase E Task 4"

---

## 🚨 CRITICAL REMINDER

**DO NOT:**
- ❌ Proceed to Phase G without finishing this
- ❌ Implement email notifications without email_utils.py
- ❌ Mark Phase E as 100% until Commits 2 & 3 done
- ❌ Forget to update CLAUDE.md after completion

**DO:**
- ✅ Complete Commit 2 first (quick win, 10 min)
- ✅ Then Commit 3 (45 min, final push)
- ✅ Test everything before marking complete
- ✅ Update CLAUDE.md in all 3 locations

---

## 🎯 SUCCESS CRITERIA (Final Check)

Task 4 is complete when:

1. ✅ Admin shows all 8 notification fields
2. ✅ `prompts/email_utils.py` exists
3. ✅ `should_send_email()` function works
4. ✅ `get_unsubscribe_url()` function works
5. ✅ Unsubscribe view handles tokens correctly
6. ✅ Unsubscribe template renders
7. ✅ All tests passing
8. ✅ CLAUDE.md updated to 100%

---

## 📊 PROGRESS TRACKER

**Update this section as you complete tasks:**

### November 4, 2025 - Initial Status
- ⚠️ Status: 75% Complete
- ⚠️ Commit 2: PENDING
- ⚠️ Commit 3: PENDING

### [DATE] - Commit 2 Complete
- ✅ Status: 85% Complete
- ✅ Commit 2: DONE
- ⚠️ Commit 3: PENDING

### [DATE] - Commit 3 Complete
- ✅ Status: 100% Complete
- ✅ Commit 2: DONE
- ✅ Commit 3: DONE

### [DATE] - Phase E Complete
- ✅ CLAUDE.md updated
- ✅ Documents archived
- ✅ Phase E marked 100%
- 🎉 Ready for Phase G

---

**Last Updated:** November 4, 2025
**Next Action:** Complete Commit 2 (10 minutes)
**Priority:** 🔴 HIGH

---

**END OF QUICK REFERENCE**

*Update this document as you progress through commits.*
