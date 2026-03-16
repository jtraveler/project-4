# CC_RUN_INSTRUCTIONS_SESSION_133.md
# Session 133 — Run Instructions for Claude Code

**Date:** March 15, 2026
**Specs in this session:** 4 code specs + 1 docs spec
**Full test suite runs:** 1 (after all code specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_133.md, then run these specs in order: CC_SPEC_133_A_SOURCE_URL_BLUR_VALIDATION.md, CC_SPEC_133_B_SOURCE_IMAGE_PASTE.md, CC_SPEC_133_C_SSRF_HARDENING.md, CC_SPEC_133_D_P3_CLEANUP.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_133_A_SOURCE_URL_BLUR_VALIDATION.md` | Feature | `bulk-generator.js`, `bulk-generator-utils.js` |
| **2** | `CC_SPEC_133_B_SOURCE_IMAGE_PASTE.md` | Feature | `upload_api_views.py`, `urls.py`, `bulk-generator.js` |
| **3** | `CC_SPEC_133_C_SSRF_HARDENING.md` | Security | `tasks.py` |
| **4** | `CC_SPEC_133_D_P3_CLEANUP.md` | Cleanup | `tasks.py`, `prompt_detail.html`, test file |

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_133_A_SOURCE_URL_BLUR_VALIDATION.md`

1. Read spec in full
2. Complete all Step 0 greps
3. Add blur/focus handlers to `bulk-generator.js`
4. Add `isValidSourceImageUrl` to `bulk-generator-utils.js` if needed
5. Complete PRE-AGENT SELF-CHECK
6. Run 2 agents: @frontend-developer, @ux-ui-designer — all must score 8.0+
7. Run isolated check: `python manage.py check`
8. **DO NOT COMMIT YET**

---

### SPEC 2 — `CC_SPEC_133_B_SOURCE_IMAGE_PASTE.md`

1. Read spec in full
2. Complete all Step 0 greps
3. Add `source_image_paste_upload` endpoint to `upload_api_views.py`
4. Add URL to `urls.py`
5. Update source image row HTML in `bulk-generator.js`
6. Add paste + clear event handlers to `bulk-generator.js`
7. Complete PRE-AGENT SELF-CHECK
8. Run 3 agents: @frontend-developer, @security-auditor, @django-pro — all must score 8.0+
9. Write 3 tests
10. Run isolated check: `python manage.py check`
11. **DO NOT COMMIT YET**

---

### SPEC 3 — `CC_SPEC_133_C_SSRF_HARDENING.md`

1. Read spec in full
2. Complete all Step 0 greps — find exact location of `_download_source_image`
3. Add `_is_private_ip_host` helper before `_download_source_image`
4. Add private IP check + redirect blocking to `_download_source_image`
5. Complete PRE-AGENT SELF-CHECK
6. Run 2 agents: @security-auditor, @django-pro — all must score 8.0+
7. Write 3 tests
8. Run isolated check: `python manage.py check`
9. **DO NOT COMMIT YET**

---

### SPEC 4 — `CC_SPEC_133_D_P3_CLEANUP.md`

1. Read spec in full
2. Complete all Step 0 greps
3. Extract `_get_b2_client()` helper + update both upload functions
4. Fix `bytearray` in `_download_source_image` (if str_replace budget allows)
5. Add `noreferrer` to modal link in `prompt_detail.html`
6. Add 3 direct unit tests for `_download_source_image`
7. Complete PRE-AGENT SELF-CHECK
8. Run 2 agents: @django-pro, @code-reviewer — all must score 8.0+
9. Run isolated check: `python manage.py check`
10. **DO NOT COMMIT YET**

---

## ⛔ FULL SUITE GATE (after all 4 specs agent-approved)

```bash
python manage.py test
```

Expected: 1190+ tests, 0 failures, 12 skipped.

- If suite passes → fill Sections 9–10 on all reports → commit in order
- If suite fails → fix in-place (max 2 attempts) → if still failing, stop and report

---

## 💾 COMMIT ORDER (after suite passes)

```
1. feat(bulk-gen): inline blur validation for source image URL field
2. feat(bulk-gen): source image clipboard paste upload with B2 storage and preview
3. fix(security): SSRF hardening in _download_source_image — private IP filter + redirect blocking
4. refactor: extract _get_b2_client helper, bytearray fix, noreferrer, direct unit tests
```

---

## ⛔ HARD RULES

1. `tasks.py` is 🔴 Critical — max 2 str_replace calls per spec, 5+ line anchors
2. `bulk-generator.js` is 🟠 High Risk — max 2 str_replace calls per spec
3. `prompt_detail.html` is 🟡 Caution — str_replace only
4. Paste endpoint must return 403 for non-staff — never skip this check
5. Source image paste failure must never break generation flow
6. Never commit before full suite passes

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected |
|--------|----------|
| Tests | 1190+ passing, 12 skipped, 0 failures |
| New endpoint | `/api/bulk-gen/source-image-paste/` (staff-only) |
| UX | Blur validation + paste zone on every prompt row |
| Security | Private IP filter + redirect blocking in `_download_source_image` |
| Refactor | `_get_b2_client()` shared helper, bytearray fix, noreferrer |
| Reports | 4 reports in `docs/` |

---

**END OF RUN INSTRUCTIONS**
