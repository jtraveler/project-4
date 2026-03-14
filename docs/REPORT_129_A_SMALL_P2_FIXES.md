# REPORT_129_A_SMALL_P2_FIXES.md
# Session 129 — March 14, 2026

---

## Section 1 — Overview

Spec 129-A addressed four small cleanup items flagged during the Session 128 review. The primary item was updating `prompts/urls.py` to bypass the `api_views` compatibility shim and import directly from the four domain view modules created in Session 128 Spec C (api_views split). The remaining items were documentation-only: verifying the version block in `PROJECT_FILE_STRUCTURE.md`, expanding the Safe but Growing file list in `CLAUDE.md` from 3 to 5 entries (as recommended by the Session 128 file size audit), and adding an explicit PRE-AGENT SELF-CHECK reminder to `CC_MULTI_SPEC_PROTOCOL.md` to make clear that the self-check applies to all spec types including docs and audit specs.

---

## Section 2 — Expectations

| Criterion | Status | Notes |
|-----------|--------|-------|
| `urls.py` imports from domain modules, not `api_views` shim | ✅ Met | All 5 `api_views.X` references replaced |
| `manage.py check` passes after urls.py update | ✅ Met | 0 issues |
| Version block naming consistent | ✅ Met | v3.30 correctly follows v3.29 — no change needed |
| Safe but Growing shows exactly 5 entries in CLAUDE.md | ✅ Met | Expanded from 3 to 5 |
| PRE-AGENT reminder added to CC_MULTI_SPEC_PROTOCOL.md | ✅ Met | Added after COMPLETION REPORTS section |

---

## Section 3 — Changes Made

### prompts/urls.py
- Removed `from .views import api_views` (shim import — no longer needed in urls.py)
- Added `from .views import upload_api_views`
- Added `from .views import moderation_api_views`
- Added `from .views import ai_api_views`
- Line 126: `api_views.b2_upload_status` → `upload_api_views.b2_upload_status`
- Line 128: `api_views.nsfw_queue_task` → `moderation_api_views.nsfw_queue_task`
- Line 129: `api_views.nsfw_check_status` → `moderation_api_views.nsfw_check_status`
- Line 131: `api_views.nsfw_check_status` (alias) → `moderation_api_views.nsfw_check_status`
- Line 137: `api_views.ai_job_status` → `ai_api_views.ai_job_status`

### CLAUDE.md
- Safe but Growing list in `🛠️ CC Working Constraints & Spec Guidelines` section expanded from 3 to 5 entries. Added: `prompts/views/user_views.py` (630) and `prompts/views/admin_views.py` (577) from the Session 128 audit report.

### CC_MULTI_SPEC_PROTOCOL.md
- Added `### PRE-AGENT SELF-CHECK — Mandatory for ALL spec types` subsection after the COMPLETION REPORTS section. Lists all 3 spec types (code, docs, audit) with checkmarks. Explains that agents should not be the first line of defence against basic errors.

### PROJECT_FILE_STRUCTURE.md
- No change. Step 2 verification confirmed v3.30 follows v3.29 consistently — numbering is correct.

---

## Section 4 — Issues Encountered and Resolved

No issues encountered during implementation.

---

## Section 5 — Remaining Issues

**Issue:** `PROJECT_FILE_STRUCTURE.md` has a stale `**Version:** 3.27` header field at line 1651. The file's latest changelog entry is v3.30, but the document-level version metadata was not updated past v3.27.
**Recommended fix:** Update line 1651 from `3.27` to `3.30`.
**Priority:** P3
**Reason not resolved:** Pre-existing condition, outside this spec's scope (spec only required verifying the version block increment). Non-blocking.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** The Safe but Growing list in CLAUDE.md now shows 5 of the 9 files flagged in the audit report. The 4 omitted files (`b2_upload_service.py`, `content_generation.py`, `bulk_generator.html`, `constants.py`) are valid watch candidates.
**Impact:** Low — the full list exists in `docs/REPORT_FILE_SIZE_AUDIT.md`.
**Recommended action:** Consider adding a note to the CLAUDE.md section reading "See `docs/REPORT_FILE_SIZE_AUDIT.md` for complete list" to avoid readers assuming 5 is exhaustive.

**Concern:** `urls.py` has a pre-existing duplicate path: `api/upload/nsfw/status/` is registered twice — once as `nsfw_check_status` and once as `nsfw_status` (alias for N3 template compatibility). Django uses the first for routing; the second only for `reverse()` lookups.
**Impact:** Low — intentional and documented in a comment in urls.py.
**Recommended action:** In a future cleanup spec, consider whether the `nsfw_status` alias is still needed by N3 templates, and remove it if not.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 9.5/10 | All 5 functions verified in correct domain modules (b2_upload_status in upload_api_views, nsfw_queue_task+nsfw_check_status in moderation_api_views, ai_job_status in ai_api_views). check passes. Pre-existing duplicate nsfw path flagged (non-blocking). | N/A — no blocking issues |
| 1 | @code-reviewer | 8.83/10 | Version block v3.30 correct. All 5 Safe but Growing line counts match audit exactly. PRE-AGENT reminder correctly placed and covers all 3 spec types. Flagged stale version header (P3, pre-existing) and omitted 4 Safe but Growing files (editorial choice, non-blocking). | N/A — no blocking issues |
| **Average** | | **9.17/10** | | **PASS (≥8.0)** |

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added material value for this spec. The changes are documentation updates and a trivial import refactor with no logic implications.

---

## Section 9 — How to Test

**Automated:**
```bash
python manage.py check
# Expected: 0 issues

# Verify no api_views references remain in urls.py patterns:
grep "api_views\." prompts/urls.py
# Expected: no output (only the import lines at top should reference api_views module, but those have been removed)
```

**Verification of domain module function existence:**
```bash
grep -n "def b2_upload_status" prompts/views/upload_api_views.py
grep -n "def nsfw_queue_task\|def nsfw_check_status" prompts/views/moderation_api_views.py
grep -n "def ai_job_status" prompts/views/ai_api_views.py
```

---

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD | `chore: update urls.py to domain modules, fix version block, expand growing list, add self-check reminder` |

---

## Section 11 — What to Work on Next

1. Update `PROJECT_FILE_STRUCTURE.md` version header from 3.27 → 3.30 (P3, pre-existing stale field)
2. Audit whether the `nsfw_status` URL alias (duplicate path) is still referenced by N3 templates; remove if not
3. Continue with Spec B: NSFWViolationAdmin + upload_api_views helper extraction
