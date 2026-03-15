# REPORT: 131-A Reactive P2 Fixes

**Spec:** `CC_SPEC_131_A_REACTIVE_P2_FIXES.md`
**Session:** 131
**Date:** March 15, 2026

---

## Section 1 — Overview

Four small security and cleanup items flagged during Session 130 review, batched into one commit. The source image URL validation in the bulk generator had a query-string bypass where a crafted URL like `https://evil.com/payload?redirect=image.jpg` could pass the extension regex. The B2 source image deletion paths in `models.py` (added in SRC-4) lacked the prefix allowlist guard already established in `b2_rename.py` (HARDENING-2). The `hard_delete()` docstring still referenced only Cloudinary assets despite now also deleting B2 source images. Finally, ~10 stale `=== UPPERCASE ===` debug log lines remained in `upload_api_views.py` from a previous debug session.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Regex applied to `_parsed.path` not full URL | ✅ Met |
| `_parsed.netloc` guard added | ✅ Met |
| Prefix allowlist in BOTH `models.py` deletion locations | ✅ Met |
| `logger.warning` for unexpected prefixes (not silent) | ✅ Met |
| `hard_delete()` docstring mentions B2 source image | ✅ Met |
| All `=== UPPERCASE ===` debug lines removed | ✅ Met |
| Module-level `logger` untouched | ✅ Met |
| Maximum 2 str_replace calls on `models.py` | ✅ Met |
| `python manage.py check` passes | ✅ Met |

---

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py
- Line 189: Changed `_SRC_IMG_EXTENSIONS.search(_url)` to `_SRC_IMG_EXTENSIONS.search(_parsed.path)` and added `not _parsed.netloc` guard before extension check

### prompts/models.py
- Line 1063: Docstring updated from "Permanently delete prompt and Cloudinary assets" to "Permanently delete prompt, Cloudinary assets, and B2 source image."
- Lines 1106-1113 (hard_delete): Added prefix allowlist guard — `b2_key.startswith('bulk-gen/')` or `b2_key.startswith('media/')` check before `B2MediaStorage().delete()`, with `logger.warning` for unexpected prefixes
- Lines 2295-2302 (delete_cloudinary_assets signal): Identical prefix allowlist guard added

### prompts/views/upload_api_views.py
- Removed 10 `logger.info("=== ... ===")` debug lines from `b2_upload_complete` function (lines 470, 485, 487, 495, 499, 506, 508, 515, 664, 728)
- Line 508: `logger.warning("=== IMAGE THUMB GENERATION FAILED ===")` replaced with `logger.warning("Image thumbnail generation failed")` (real warning retained, debug formatting removed)

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation. The docstring and first deletion block in `models.py` were combined into a single str_replace call (spanning lines 1062-1114) to stay within the 2 str_replace budget for a 🔴 Critical file.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The regex `(\?.*)?$` in `_SRC_IMG_EXTENSIONS` is now dead code since it runs against `_parsed.path` which never contains query strings.
**Impact:** Cosmetic only — no functional impact.
**Recommended action:** Simplify regex to `r'\.(jpg|jpeg|png|webp|gif|avif)$'` in a future micro-cleanup.

**Concern:** `_SRC_IMG_EXTENSIONS` is compiled inside `create_job()` on every call (line 182).
**Impact:** Minor performance inefficiency — pre-existing, not introduced by this spec.
**Recommended action:** Promote to module-level constant in a future cleanup.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.0/10 | Regex fix correct, prefix guard in right position, noted dead `(\?.*)?` regex tail | No — cosmetic, deferred |
| 1 | @security-auditor | 9.0/10 | Query-string and fragment bypasses closed, prefix guard matches HARDENING-2, warning fires correctly | No issues requiring action |
| 1 | @code-reviewer | 9.0/10 | All debug lines removed, docstring accurate, no logic changes beyond spec | No issues requiring action |
| **Average** | | **9.0/10** | | **Pass ≥8.0** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The @frontend-developer agent was not needed since no JS/template changes were made.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py test
# Expected: 1176 tests, 0 failures, 12 skipped
```

**Manual verification:**
1. Confirm no `=== ` debug lines remain: `grep -n "=== " prompts/views/upload_api_views.py` → 0 matches
2. Confirm prefix guard in both models.py locations: `grep -n "startswith.*bulk-gen" prompts/models.py` → 2 matches
3. Confirm regex fix: `grep -n "_parsed.path" prompts/views/bulk_generator_views.py` → 1 match

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| *(see below)* | fix: regex path validation, B2 prefix allowlist, hard_delete docstring, debug log cleanup |

---

## Section 11 — What to Work on Next

1. Simplify `_SRC_IMG_EXTENSIONS` regex to remove dead `(\?.*)?` tail — `prompts/views/bulk_generator_views.py` line 183
2. Promote `_SRC_IMG_EXTENSIONS` to module-level constant — same file, line 182
3. Consider domain allowlist for source image URLs if they are ever fetched server-side (currently display-only, so not urgent)
