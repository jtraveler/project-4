# CC_RUN_INSTRUCTIONS_SESSION_131.md
# Session 131 — Run Instructions for Claude Code

**Date:** March 15, 2026
**Specs in this session:** 2
**Full test suite runs:** 1 (at end, after both specs agent-approved)
**Trigger phrase:** `Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read CC_RUN_INSTRUCTIONS_SESSION_131.md, then run these specs in order: CC_SPEC_131_A_REACTIVE_P2_FIXES.md, CC_SPEC_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 SPEC QUEUE

| Order | Spec File | Type | Files Touched |
|-------|-----------|------|---------------|
| **1** | `CC_SPEC_131_A_REACTIVE_P2_FIXES.md` | Bug fixes + cleanup | `bulk_generator_views.py`, `models.py`, `upload_api_views.py` |
| **2** | `CC_SPEC_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md` | Template feature | `prompt_detail.html` |

---

## 🔁 EXECUTION SEQUENCE

### SPEC 1 — `CC_SPEC_131_A_REACTIVE_P2_FIXES.md`

1. Read `CC_SPEC_131_A_REACTIVE_P2_FIXES.md` in full
2. Complete Step 0 greps (mandatory — do not skip)
3. Complete Steps 1–4 (regex fix, prefix allowlist, docstring, debug log cleanup)
4. Complete PRE-AGENT SELF-CHECK
5. Run 3 agents: @django-pro, @security-auditor, @code-reviewer — all must score 8.0+
6. Fix any blocking issues and re-run if needed
7. Run isolated check:
   ```bash
   python manage.py check
   ```
   Expected: 0 issues
8. **DO NOT COMMIT YET** — hold per protocol until full suite passes

---

### SPEC 2 — `CC_SPEC_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md`

1. Read `CC_SPEC_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md` in full
2. Complete Step 0 greps (mandatory — do not skip)
3. Complete Steps 1–2 (rail card + modal)
4. Complete PRE-AGENT SELF-CHECK
5. Run 3 agents: @frontend-developer, @ux-ui-designer, @security-auditor — all must score 8.0+
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

Expected: 1165+ tests, 0 failures, 12 skipped.

- If suite passes → fill in Sections 9–10 of both reports → commit both specs in order
- If suite fails → fix in-place (max 2 attempts) → re-run → if still failing, stop and report

---

## 💾 COMMIT ORDER (after suite passes)

```
1. fix: regex path validation, B2 prefix allowlist, hard_delete docstring, debug log cleanup
2. feat(prompt-detail): SRC-5 staff-only source image display + lightbox
```

---

## ⛔ HARD RULES

1. `models.py` is 🔴 Critical — maximum 2 str_replace calls, 5+ line anchors required
2. `prompt_detail.html` is 🟡 Caution — str_replace only, no rewrites
3. Never commit before full suite passes
4. Never skip Step 0 greps on either spec
5. Never fire agents before PRE-AGENT SELF-CHECK is complete
6. Spec 2 (template only) requires browser verification by Mateo — note this in report

---

## 🔢 EXPECTED FINAL STATE

| Metric | Expected Value |
|--------|----------------|
| Tests | 1165+ passing, 12 skipped, 0 failures |
| Migration | None (no model changes) |
| New feature | Staff-only source image card + lightbox on prompt detail |
| Security fixes | Regex path validation + B2 prefix allowlist |
| Debug cleanup | All `=== UPPERCASE ===` lines removed from `upload_api_views.py` |
| Reports | `docs/REPORT_131_A_REACTIVE_P2_FIXES.md` + `docs/REPORT_131_B_SRC5_SOURCE_IMAGE_DISPLAY.md` |

---

**END OF RUN INSTRUCTIONS**
