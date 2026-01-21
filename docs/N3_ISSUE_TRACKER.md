# N3 Implementation - Issue Tracker

**Created:** January 21, 2026
**Session:** 52
**Updated:** January 21, 2026 (Spec 5 Complete)

---

## 🔴 BLOCKING ISSUES (Fix in Spec 5)

*None remaining - all blocking issues resolved.*

---

## 🟡 NON-BLOCKING ISSUES

*None remaining - all non-blocking issues resolved.*

---

## ✅ RESOLVED ISSUES

### N3-FIELD-001: Form Field Name Differences ✅

**Status:** ✅ RESOLVED
**Verified:** January 21, 2026
**Fixed In:** Session 52

**Original Concern:** Spec files mentioned different field names than implementation might use.

**Initial Error:** Original verification was performed against the WRONG template (`upload_step2.html` - the old Step 2 template) instead of the correct N3 template (`upload.html`).

**Re-verification against correct template (`upload.html`) found 3 mismatches:**

| Field Purpose | HTML had | View expects | Status |
|---------------|----------|--------------|--------|
| Prompt content | `prompt_content` | `content` | ❌ Fixed |
| Save as draft | `is_draft` | `save_as_draft` | ❌ Fixed |
| Cloudinary ID | `b2_file_key` | `cloudinary_id` | ❌ Fixed |

**Fixes Applied (via sed):**
```bash
sed -i '' 's/name="prompt_content"/name="content"/g' prompts/templates/prompts/upload.html
sed -i '' 's/name="is_draft"/name="save_as_draft"/g' prompts/templates/prompts/upload.html
sed -i '' 's/name="b2_file_key"/name="cloudinary_id"/g' prompts/templates/prompts/upload.html
```

**Verification Results (grep on upload.html):**
- Line 535: `<input type="hidden" name="cloudinary_id" id="b2FileKey">` ✅
- Line 549: `name="content"` ✅
- Line 586: `<input type="checkbox" id="isDraft" name="save_as_draft" disabled>` ✅

**Final Field Name Mapping (All Correct):**

| Field Purpose | HTML name= | View expects | Match? |
|---------------|------------|--------------|--------|
| Prompt content | `content` | `content` | ✅ |
| AI Generator | `ai_generator` | `ai_generator` | ✅ |
| Save as draft | `save_as_draft` | `save_as_draft` | ✅ |
| Tags JSON | `tags` | `tags` | ✅ |
| Cloudinary ID | `cloudinary_id` | `cloudinary_id` | ✅ |
| Resource type | `resource_type` | `resource_type` | ✅ |
| AI failed flag | `ai_failed` | `ai_failed` | ✅ |
| Variant URLs | `variant_*_url` | `variant_*_url` | ✅ |

**Resolution:** 3 field names fixed in `upload.html` to match backend expectations.

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

### N3-URL-001: Missing nsfw_status URL Name ✅

**Status:** ✅ RESOLVED
**Fixed In:** Spec 5

**Issue:** Template expected `{% url 'prompts:nsfw_status' %}` but urls.py only had `nsfw_check_status`.

**Resolution:** Added alias URL in `prompts/urls.py` (line 112):
```python
# Alias for N3 upload template compatibility
path('api/upload/nsfw/status/', api_views.nsfw_check_status, name='nsfw_status'),
```

**Verification:** All required URL names now exist:
| URL Name | Line | Status |
|----------|------|--------|
| b2_presign_upload | 80 | ✅ |
| b2_upload_complete | 81 | ✅ |
| b2_moderate_upload | 84 | ✅ |
| nsfw_status | 112 | ✅ (alias) |
| upload_submit | 19 | ✅ |
| cancel_upload | 21 | ✅ |

---

## 📋 SPEC 5 CHECKLIST

Status after Spec 5 completion:
- [x] Create all missing URL routes (N3-URL-001) - ✅ Added `nsfw_status` alias
- [x] Create or update views for each URL - ✅ All views exist in api_views.py
- [ ] Add legacy redirects for /upload/step1/ and /upload/step2/ - Not needed (current URLs work)
- [x] Verify form field names match between frontend and backend - ✅ See N3-FIELD-001 (backend will accept CC's names)
- [x] Test template loads without errors - ✅ All URL names resolve correctly

---

**END OF TRACKER**
