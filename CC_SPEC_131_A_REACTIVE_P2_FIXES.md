# CC_SPEC_131_A_REACTIVE_P2_FIXES.md
# Reactive P2 Fixes — Regex Path, Prefix Allowlist, hard_delete Docstring, Debug Logs

**Spec Version:** 1.0
**Date:** March 15, 2026
**Session:** 131

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **Read this entire spec** before making any changes
5. **`bulk_generator_views.py` is ✅ Safe** — normal editing
6. **`models.py` is 🔴 Critical (3,087+ lines)** — str_replace with 5+ line anchors. Maximum 2 str_replace calls.
7. **`upload_api_views.py` is ✅ Safe (754 lines)** — normal editing
8. **No logic changes** — pure fixes and cleanup only

---

## 📋 OVERVIEW

Four small items flagged during Session 130 review, all batched into one commit:

1. **Regex path bypass** — `_SRC_IMG_EXTENSIONS.search(_url)` runs against the full URL string, meaning a crafted query string like `?redirect=image.jpg` passes extension validation. Fix: apply regex to `_parsed.path` instead, and add `and _parsed.netloc` guard.

2. **Missing B2 key prefix allowlist** — `hard_delete()` and `delete_cloudinary_assets` signal in `models.py` delete B2 source images without first verifying the key starts with a known safe prefix. Fix: add `bulk-gen/` or `media/` prefix check before deletion — consistent with `b2_rename.py` HARDENING-2 guard.

3. **`hard_delete()` docstring** — still says "Permanently delete prompt and Cloudinary assets" — doesn't mention B2 source image deletion added in Session 130.

4. **Remaining `=== UPPERCASE ===` debug log lines** — ~10 stale debug `logger.info("=== ... ===")` lines remain in `b2_upload_complete` in `upload_api_views.py` from a previous debug session.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find the regex validation block in bulk_generator_views.py
grep -n "_SRC_IMG_EXTENSIONS\|_parsed\|_netloc\|search.*_url\|search.*path" prompts/views/bulk_generator_views.py

# 2. Find both B2 source image deletion blocks in models.py
grep -n "b2_source_image_url\|b2_key\|lstrip\|B2MediaStorage\|delete.*b2\|b2.*delete" prompts/models.py | head -20

# 3. Find hard_delete docstring
grep -n "def hard_delete\|Permanently delete\|Cloudinary assets" prompts/models.py | head -5

# 4. Find all === UPPERCASE === debug lines in upload_api_views.py
grep -n "=== " prompts/views/upload_api_views.py
```

---

## 📁 STEP 1 — Fix regex path bypass in `bulk_generator_views.py`

**File:** `prompts/views/bulk_generator_views.py`

From Step 0 grep, find the validation loop. Make two changes:

**Change 1** — apply regex to parsed path, not full URL:
```python
# Before:
if _parsed.scheme != 'https' or not _SRC_IMG_EXTENSIONS.search(_url):

# After:
if _parsed.scheme != 'https' or not _parsed.netloc or not _SRC_IMG_EXTENSIONS.search(_parsed.path):
```

This closes both gaps: the query-string bypass AND the `https:///foo.jpg` malformed URL edge case.

---

## 📁 STEP 2 — Add prefix allowlist to `models.py` B2 source image deletion

**File:** `prompts/models.py`

There are TWO locations where `b2_source_image_url` is deleted — one in `hard_delete()` and one in the `delete_cloudinary_assets` post_delete signal. Both need the same guard added before the `B2MediaStorage().delete(b2_key)` call:

```python
# Add this guard immediately after b2_key is extracted, before deletion:
if not (b2_key.startswith('bulk-gen/') or b2_key.startswith('media/')):
    logger.warning(
        "Refusing to delete B2 key with unexpected prefix: %s", b2_key
    )
else:
    B2MediaStorage().delete(b2_key)
    logger.info(...)  # existing log line
```

⚠️ `models.py` is 🔴 Critical. Use str_replace with the surrounding B2 deletion block as the 5+ line anchor. Maximum 2 str_replace calls (one per deletion location).

---

## 📁 STEP 3 — Fix `hard_delete()` docstring in `models.py`

**File:** `prompts/models.py`

From Step 0 grep, find the `hard_delete` docstring. Update it:

```python
# Before:
"""Permanently delete prompt and Cloudinary assets"""

# After:
"""Permanently delete prompt, Cloudinary assets, and B2 source image."""
```

⚠️ This counts toward the 2 str_replace budget for `models.py` if combined with Step 2. Use a single str_replace that covers the docstring AND the first deletion block together if possible, or split into 2 separate calls if the locations are too far apart.

---

## 📁 STEP 4 — Remove `=== UPPERCASE ===` debug logs from `upload_api_views.py`

**File:** `prompts/views/upload_api_views.py`

From Step 0 grep, list all `logger.info("=== ... ===")` lines. Remove every one. These are debug artifacts — the module-level `logger` remains untouched, only these specific debug-style log lines are removed.

Normal editing applies (754 lines, ✅ Safe).

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Regex now applies to `_parsed.path` not `_url`
- [ ] `_parsed.netloc` guard added
- [ ] Prefix allowlist guard added to BOTH deletion locations in `models.py`
- [ ] Guard uses `logger.warning` for unexpected prefixes (not silent skip)
- [ ] `hard_delete()` docstring mentions B2 source image
- [ ] All `=== UPPERCASE ===` debug lines removed from `upload_api_views.py`
- [ ] Module-level `logger` in `upload_api_views.py` untouched
- [ ] Maximum 2 str_replace calls used on `models.py`
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 3 agents. All must score 8.0+.

### 1. @django-pro
- Verify regex is applied to `_parsed.path` not full URL
- Verify `_parsed.netloc` guard is in the correct position
- Verify prefix allowlist guard fires before deletion in both locations
- Rating requirement: 8+/10

### 2. @security-auditor
- Verify the regex path fix closes the query-string bypass
- Verify prefix allowlist matches the `b2_rename.py` HARDENING-2 pattern
- Verify `logger.warning` fires for unexpected prefixes (no silent skip)
- Rating requirement: 8+/10

### 3. @code-reviewer
- Verify `=== UPPERCASE ===` lines are fully removed with no gaps
- Verify docstring is accurate
- Verify no logic changes in any of the four steps
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Regex still applied to full URL string after this spec
- Prefix allowlist guard missing from either deletion location
- Any `=== UPPERCASE ===` debug line remaining in `upload_api_views.py`

---

## 🧪 TESTING

```bash
python manage.py check
```
Expected: 0 issues. No full test suite — runs once at end of session.

---

## 💾 COMMIT MESSAGE

```
fix: regex path validation, B2 prefix allowlist, hard_delete docstring, debug log cleanup
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_131_A_REACTIVE_P2_FIXES.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
