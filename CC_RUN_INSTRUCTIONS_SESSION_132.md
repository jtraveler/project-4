# CC_RUN_INSTRUCTIONS_SESSION_132.md
# Session 132 — Run Instructions for Claude Code

**Date:** March 15, 2026
**Specs in this session:** 2
**Full test suite runs:** 1 (at end, after both specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_132.md, then run these specs in order: CC_SPEC_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md, CC_SPEC_132_B_SESSION131_CLEANUP.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md` | Feature | `prompts/tasks.py` |
| **2** | `CC_SPEC_132_B_SESSION131_CLEANUP.md` | Cleanup | `bulk_generator_views.py`, `prompt_detail.html` |

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md`

1. Read spec in full
2. Complete ALL Step 0 greps — especially `_is_safe_image_url` (determines which download approach to use)
3. Add `_upload_source_image_to_b2` helper
4. Add `_download_source_image` helper if needed (see Step 0 decision)
5. Wire up generation task
6. Complete PRE-AGENT SELF-CHECK
7. Run 3 agents: @django-pro, @security-auditor, @code-reviewer — all must score 8.0+
8. Fix any blocking issues and re-run if needed
9. Write tests (minimum 4)
10. Run isolated check:
    ```bash
    python manage.py check
    ```
    Expected: 0 issues
11. **DO NOT COMMIT YET**

---

### SPEC 2 — `CC_SPEC_132_B_SESSION131_CLEANUP.md`

1. Read spec in full
2. Complete Step 0 greps
3. Complete Steps 1–3 (regex, thumbnail, modal link)
4. Complete PRE-AGENT SELF-CHECK
5. Run 2 agents: @django-pro, @frontend-developer — all must score 8.0+
6. Fix any blocking issues and re-run if needed
7. Run isolated check:
    ```bash
    python manage.py check
    ```
    Expected: 0 issues
8. **DO NOT COMMIT YET**

---

## ⛔ FULL SUITE GATE (after both specs agent-approved)

```bash
python manage.py test
```

Expected: 1180+ tests, 0 failures, 12 skipped.

- If suite passes → fill in Sections 9–10 on both reports → commit in order
- If suite fails → fix in-place (max 2 attempts) → re-run → if still failing, stop and report

---

## 💾 COMMIT ORDER (after suite passes)

```
1. feat(bulk-gen): SRC-6 download and upload source image to B2 on generation
2. fix: promote _SRC_IMG_EXTENSIONS to module level, thumbnail max-height, modal open-in-new-tab
```

---

## ⛔ HARD RULES

1. `tasks.py` is 🔴 Critical — maximum 2 str_replace calls, 5+ line anchors, only when new-file strategy is not possible
2. `prompt_detail.html` is 🟡 Caution — str_replace only
3. Source image failure must NEVER cancel a generation job — wrap in try/except
4. Use `update_fields=['b2_source_image_url']` — never full .save() on GeneratedImage post-generation
5. Never commit before full suite passes

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected Value |
|--------|----------------|
| Tests | 1180+ passing, 12 skipped, 0 failures |
| Migration | None |
| New feature | SRC-6 — source image downloaded and stored in B2 on generation |
| SRC pipeline | 100% end-to-end functional after this session |
| Cleanup | `_SRC_IMG_EXTENSIONS` at module level, thumbnail constrained, modal open-in-new-tab |
| Reports | `docs/REPORT_132_A_SRC6_SOURCE_IMAGE_B2_UPLOAD.md` + `docs/REPORT_132_B_SESSION131_CLEANUP.md` |

---

**END OF RUN INSTRUCTIONS**
