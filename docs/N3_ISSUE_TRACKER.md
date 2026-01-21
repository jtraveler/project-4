# N3 Implementation - Issue Tracker

**Created:** January 21, 2026
**Session:** 52

---

## 🔴 BLOCKING ISSUES (Fix in Spec 5)

### N3-URL-001: Missing URL Routes

**Status:** 🔴 Open
**Fix In:** Spec 5 (URL Routing + Views)
**Blocking:** Template will error on load until fixed

**URLs Referenced in upload.html that don't exist:**
```python
# These need to be created in prompts/urls.py:

path('api/upload/b2/presign/', views.b2_presign_upload, name='b2_presign_upload'),
path('api/upload/b2/complete/', views.b2_upload_complete, name='b2_upload_complete'),
path('api/upload/b2/moderate/', views.b2_moderate_upload, name='b2_moderate_upload'),
path('api/upload/nsfw/status/', views.nsfw_status, name='nsfw_status'),
path('upload/submit/', views.upload_submit, name='upload_submit'),
path('upload/cancel/', views.cancel_upload, name='cancel_upload'),
```

**Note:** Some of these may already exist with different names. Spec 5 will audit existing URLs and create/alias as needed.

---

## 🟡 NON-BLOCKING ISSUES

### N3-FIELD-001: Form Field Name Differences

**Status:** 🟡 Monitor
**Fix In:** Spec 5 or Backend Update

**CC used different field names than spec:**
| Spec Name | CC Used | Action |
|-----------|---------|--------|
| `content` | `prompt_content` | Update backend to accept |
| `save_as_draft` | `is_draft` | Update backend to accept |

**Resolution:** Backend view will accept CC's field names (they're actually better/clearer).

---

### N3-STYLE-001: CSS Variable Fallbacks

**Status:** 🟢 Acceptable
**Fix In:** Optional future cleanup

CC added fallback values for CSS variables which is actually good practice:
```css
var(--gray-300, #d1d5db)
```

This ensures styling works even if UI_STYLE_GUIDE variables aren't loaded.

---

## ✅ RESOLVED ISSUES

(None yet - will track resolved issues here)

---

## 📋 SPEC 5 CHECKLIST

When creating Spec 5, ensure it addresses:
- [ ] Create all missing URL routes (N3-URL-001)
- [ ] Create or update views for each URL
- [ ] Add legacy redirects for /upload/step1/ and /upload/step2/
- [ ] Verify form field names match between frontend and backend
- [ ] Test template loads without errors

---

**END OF TRACKER**
