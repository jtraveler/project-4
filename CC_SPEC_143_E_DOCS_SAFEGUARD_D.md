# CC_SPEC_143_E_DOCS_SAFEGUARD_D.md
# CLAUDE.md — Safeguard Section D + Quota Architecture Notes

**Session:** 143
**Spec Type:** Docs only — commit immediately after agents pass
**Report Path:** `docs/REPORT_143_E_DOCS_SAFEGUARD_D.md`
**Commit Message:** `docs: add safeguard section D, rate limit compliance note, quota architecture (Session 143)`

---

## ⛔ STOP — READ BEFORE STARTING

```
╔══════════════════════════════════════════════════════════════╗
║  THIS IS A DOCS-ONLY SPEC — NO CODE CHANGES                  ║
║                                                              ║
║  Docs specs follow a different gate sequence:                ║
║  1. Read spec in full                                        ║
║  2. Complete all Step 0 greps                                ║
║  3. Make CLAUDE.md changes                                   ║
║  4. python manage.py check → 0 issues                       ║
║  5. Complete PRE-AGENT SELF-CHECK                            ║
║  6. Run required agents → all 8.0+                          ║
║  7. Write FULL report (all 11 sections)                      ║
║  8. Commit immediately (no full suite needed)                ║
╚══════════════════════════════════════════════════════════════╝
```

⛔ **Work is REJECTED if:**
- Any agent scores below 8.0
- The exact text blocks below are not added verbatim
- Section placement does not match the instructions below
- The report table is missing or incomplete

---

## 📋 OVERVIEW

**Modifies UI/Templates:** No
**Modifies Code:** No
**Modifies Docs:** Yes — `CLAUDE.md` only

### What This Spec Does

Adds three documentation blocks to `CLAUDE.md`:

1. **Safeguard Section D** — Generation Retry + Finalisation Sweep + Rate Limit Compliance
   (alongside the existing Section A/B/C safeguard blocks)
2. **Key Learnings additions** — Two new bullet points about known bugs/risks discovered
   in production testing (Session 142/143)
3. **Quota + Admin Notification Architecture** — Full planned architecture for
   QUOTA-1, QUOTA-2, P2-B, and P2-C so future sessions can build from a clear spec

### Why This Is Needed

Production testing with 13 prompts revealed three critical issues:
- **Rate limit breach:** `BULK_GEN_MAX_CONCURRENT=4` dispatches ~16 images/minute
  against an OpenAI Tier 1 limit of 5 images/minute — this is a live account risk
- **Pending-after-completion gap:** Images that never transition from `pending` to
  `failed` show as "Not generated" in the gallery but count as 0 failures in the
  job header stats — a real UX and billing problem
- **No generation retry:** Transient failures (rate limit, server error) currently
  have no retry path at the generation level, silently dropping images

Additionally, the QUOTA + admin notification architecture was fully designed in
Session 142/143 planning and must be preserved in CLAUDE.md before it is lost.

---

## 🔍 STEP 0 — MANDATORY GREPS BEFORE ANY CHANGES

Run all of these before touching `CLAUDE.md`. Confirm findings in the report.

```bash
# Confirm Section A exists (bulk job deletion safeguard)
grep -n "Section A" CLAUDE.md

# Confirm Section B exists (orphan detection safeguard)
grep -n "Section B" CLAUDE.md

# Confirm Section C exists (admin operational notifications)
grep -n "Section C" CLAUDE.md

# Confirm Section D does NOT already exist
grep -n "Section D" CLAUDE.md

# Find the Key Learnings section for correct insertion point
grep -n "Key Learnings" CLAUDE.md

# Find existing rate limit learning (confirm it exists, note line number)
grep -n "OpenAI Tier 1 rate limit" CLAUDE.md

# Find QUOTA-related content if any exists already
grep -n "QUOTA\|quota" CLAUDE.md

# Find P2-B and P2-C references (confirm they exist as placeholders)
grep -n "P2-B\|P2-C" CLAUDE.md

# Check current CLAUDE.md line count
wc -l CLAUDE.md
```

**Gate:** If Section D already exists, stop and report to developer. Do not
proceed if any insertion point cannot be located.

---

## 📁 FILE TO MODIFY

### `CLAUDE.md` — Three separate additions

---

### Addition 1 — Key Learnings (2 new bullet points)

**Find this existing bullet point** (use grep line number from Step 0):
```
**OpenAI Tier 1 rate limit:** 5 images/minute, 15–45s per image.
```

**Add these two new bullet points IMMEDIATELY AFTER that line:**

```
- **Rate limit compliance gap (Session 143):** `BULK_GEN_MAX_CONCURRENT=4` + `ThreadPoolExecutor`
  dispatches up to 4 concurrent API calls per batch, completing in ~15s before the next batch
  starts. This produces ~16 images/minute against Tier 1's 5 images/minute limit. The original
  Phase 5C inter-image delay was removed in Phase 5D. **IMMEDIATE MITIGATION (no code deploy):**
  Set `BULK_GEN_MAX_CONCURRENT=1` in Heroku config vars. **Permanent fix:** Safeguard Section D
  (D3) — add `OPENAI_TIER` env var that auto-configures correct `max_workers` + inter-batch delay
  per tier. Do not raise `BULK_GEN_MAX_CONCURRENT` above 1 for Tier 1 until D3 is built.

- **Pending-after-completion gap (Session 143):** If the generation loop exits before all
  `GeneratedImage` records transition from `status='pending'` to `status='failed'` (e.g., quota
  exhaustion, unhandled exception), those images show as "Not generated" in the gallery but are
  never counted in `failed_count`. The job reports 0 failures despite images not generating.
  Root cause: `failed_count` only increments when the backend explicitly catches an exception per
  image — orphaned `pending` records are never swept up. Fix is Safeguard Section D (D1).
```

---

### Addition 2 — Safeguard Section D

**Find the end of the existing Section C block** in CLAUDE.md. Section C ends with
a paragraph about its architecture and the instruction "not yet built". Add the
following complete block IMMEDIATELY AFTER Section C, maintaining the same
heading style and formatting as Sections A/B/C:

```
---

### Section D — Generation Retry + Finalisation Sweep + Rate Limit Compliance

> **Status:** Not yet built — requires planning session before spec writing.
> **Priority:** HIGH — D1 (pending sweep) is a billing integrity issue. D3 (rate
> limit compliance) is an account safety issue. Build D1 + D3 before V2 launch.
> Capture date: Session 143 (March 21, 2026).

#### The Problem

Production testing with 13 prompts revealed three related generation integrity issues:
1. Images silently left in `pending` status after job completion (not counted as failed)
2. No retry for transient failures at the generation level (rate limit, server error)
3. `BULK_GEN_MAX_CONCURRENT=4` dispatches ~16 images/minute against Tier 1's 5/min limit

#### D1 — Pending-After-Completion Finalisation Sweep

After `ThreadPoolExecutor` completes (on ANY exit path — success, exception, quota, cancel),
add a sweep step:

```python
# After generation loop exits
pending_images = job.images.filter(status='pending')
if pending_images.exists():
    pending_images.update(
        status='failed',
        error_message='Not generated — job ended unexpectedly'
    )
    # Recalculate failed_count from DB (not from incremental F() counter which may be stale)
    job.failed_count = job.images.filter(status='failed').count()
    job.save(update_fields=['failed_count'])
```

This ensures `failed_count` always reflects reality and users see accurate failure stats.

**IMPORTANT:** Implement D1 before D2 — retry logic depends on accurate `status` values.

#### D2 — Generation Retry for Transient Failures

After the primary generation loop AND the D1 sweep, add a single retry pass:

- **Retry if:** `error_type` is `rate_limit` or `server_error`
- **Never retry if:** `error_type` is `content_policy`, `auth`, or `quota`
- **Max retries:** 1 per image at this level (provider already retries 3× internally)
- **Delay before retry:** 30 seconds flat (not exponential — this is a one-shot pass)
- **After retry:** Re-run D1 sweep to catch any remaining pending records

This is the "generation retry" explicitly deferred in Phase 5D due to insufficient frequency
data. The 4/13 failure rate (30%) in Session 143 testing justifies the complexity.

**DO NOT build D2 without D1 complete first.**

#### D3 — Rate Limit Compliance Audit + Tier-Aware Configuration

OpenAI rate limits are per API key tier, not just per request. Current config violates Tier 1.

| Tier | Limit | Safe `max_workers` | Recommended inter-batch delay |
|------|-------|-------------------|-------------------------------|
| Tier 1 | 5 img/min | 1 | 12s between images |
| Tier 2 | 50 img/min | 4 | 2s between images |
| Tier 3+ | 100 img/min | 8 | 1s between images |

**Implementation:** Add `OPENAI_TIER` env var (default: `1`). On task startup, read tier and
set `max_workers` + `inter_image_delay` accordingly:

```python
TIER_CONFIG = {
    1: {'max_workers': 1, 'inter_image_delay': 12},
    2: {'max_workers': 4, 'inter_image_delay': 2},
    3: {'max_workers': 8, 'inter_image_delay': 1},
}
tier = int(getattr(settings, 'OPENAI_TIER', 1))
config = TIER_CONFIG.get(tier, TIER_CONFIG[1])
```

This replaces the raw `BULK_GEN_MAX_CONCURRENT` env var (or reads it as an override).

**IMMEDIATE MITIGATION (no code deploy needed):** Set `BULK_GEN_MAX_CONCURRENT=1`
in Heroku config vars until D3 is built.

#### Build Order

```
D1 (pending sweep) → must be first, fixes billing integrity
D3 (rate limit config) → can be built alongside D1
D2 (generation retry) → only after D1 is deployed and verified
```

#### Files That Will Need Changes

| File | Change | Risk Tier |
|------|--------|-----------|
| `prompts/tasks.py` | D1 sweep + D2 retry pass in generation loop | 🔴 Critical |
| `settings.py` | `OPENAI_TIER` env var | ✅ Safe |
| `prompts/services/bulk_generation.py` | Tier-aware `max_workers` + delay config | ✅ Safe |
| Heroku config | `OPENAI_TIER=1`, `BULK_GEN_MAX_CONCURRENT=1` | Manual step |
```

---

### Addition 3 — Quota + Admin Notification Architecture

**Find the existing "Section C — Admin Operational Notifications" safeguard block.**
This block already exists. Locate the subsection titled "Events to Surface" or
"Implementation Notes" — whichever is LAST in the Section C block.

**Add the following block IMMEDIATELY AFTER Section C's Implementation Notes,
BEFORE Safeguard Section D:**

```
#### Planned Feature Architecture — QUOTA Alerts + P2-B/C Surfaces

The following architecture was designed in Session 142/143. Do not rebuild from
scratch — implement exactly as documented here.

---

**QUOTA-1 — Quota Exhaustion Error Message + Bell Notification**
*(Planned: Session 143, ~1 spec, QUOTA-1 micro-spec)*

| Layer | Change |
|-------|--------|
| `bulk_generation.py` — `_sanitise_error_message()` | Add `'quota exhausted'` as 7th output category. Must appear BEFORE `'invalid request'` in keyword order to prevent masking. OpenAI raises `RateLimitError` for both rate limits AND quota — distinguish by checking message body for `"insufficient_quota"`. Route quota exhaustion to `error_type='quota'` (fail immediately, NO retry — unlike rate_limit which retries). |
| `static/js/bulk-generator-gallery.js` — `_getReadableErrorReason()` | Map `'quota exhausted'` → `"Failed. API quota exceeded — contact admin."` |
| `prompts/models.py` | Add `openai_quota_alert` to `NOTIFICATION_TYPES` |
| New migration | For the notification type addition |
| `prompts/tasks.py` | When quota error kills a job, fire `openai_quota_alert` bell notification to job owner using existing `_fire_bulk_gen_job_notification()` pattern |
| `prompts/tests/` | 2–3 new tests: quota sanitiser maps correctly, notification fires on quota kill, quota does NOT retry |

**⚠️ IMPORTANT — quota vs rate_limit routing in `openai_provider.py`:**
OpenAI raises `RateLimitError` for BOTH true rate limits AND quota exhaustion.
The current code retries ALL `RateLimitError` with exponential backoff (30s→60s→120s).
Quota exhaustion MUST NOT retry — same key, same balance, same result.
Step 0 grep must verify current `RateLimitError` handling before any changes.
Distinguish by: `error.code == 'insufficient_quota'` or `'quota' in str(error).lower()`.

---

**QUOTA-2 — Low Spend-Rate Warning Notification**
*(Planned: Session 144, ~1 spec)*

Design: Spend-rate alert (not true balance check — BYOK keys have no balance API).
Fires inline after each job completes (not a scheduled task).

| Component | Detail |
|-----------|--------|
| Trigger | After every job finalisation, check cumulative spend |
| Calculation | `BulkGenerationJob.objects.filter(user=job.user, created_at__gte=30_days_ago).aggregate(total=Sum('total_cost'))` |
| Threshold | `settings.OPENAI_SPEND_WARNING_THRESHOLD` (env var, default `10.00` USD) |
| New notification type | `openai_quota_warning` |
| Deduplication | Max 1 warning per user per 7 days (use notification duplicate prevention — 60s window exists, extend to 7 days for this type) |
| Message | "You've spent $X on OpenAI in the last 30 days. If your balance is running low, top it up to avoid job failures." |
| New env var | `OPENAI_SPEND_WARNING_THRESHOLD=10.00` in `settings.py` + Heroku config |
| Location | New `_check_and_warn_quota(job)` helper in `prompts/tasks.py`, called from job finalisation |

**Note:** QUOTA-2 gives early warning before QUOTA-1 fires. Together they close the
"blind until the job fails" gap.

---

**P2-B — Admin Log Tab**
*(Planned: Session 145, requires its own planning session before spec writing)*

Status: Currently a "Coming soon" placeholder in `system_notifications.html`.
The tab URL is: `/admin-tools/system-notifications/?tab=admin-log`

Design questions to resolve before spec:
1. Use existing `Notification` model filtered to `notification_type=system` (simpler,
   no new model) OR new `AdminEvent` model (more structured, filterable by event_type)?
   **Recommended:** New `AdminEvent` model — notifications are user-facing, admin events
   are operational. Mixing them in one table creates query complexity.
2. Initial events to surface (P1): quota exhaustion, job failures (entire job),
   B2 cleanup run outcomes, orphan detection results
3. Tab UI: Reverse-chronological feed with event-type filter pills. Show: timestamp,
   event type badge, summary text, user (if applicable), link to related object.
4. Auth: Staff-only (`@staff_member_required` or equivalent JSON-safe check).
5. Pagination: Standard cursor-based (existing pattern in project).

**DO NOT build P2-B without a dedicated planning session first.**
The data model decision (notification vs AdminEvent) has long-term consequences.

---

**P2-C — Web Pulse Tab**
*(Planned: Session 146+, requires its own planning session)*

Status: Currently a "Coming soon" placeholder in `system_notifications.html`.
The tab URL is: `/admin-tools/system-notifications/?tab=web-pulse`

Scope TBD — requires its own design session. Likely includes:
site-wide traffic/activity snapshot, recent signups, bulk gen job volume,
error rate summary. Do not spec until P2-B is complete.
```

---

## ✅ PRE-AGENT SELF-CHECK

Before running agents, verify all of the following:

- [ ] All three additions are present in `CLAUDE.md`
- [ ] Bullet points in Addition 1 appear immediately after "OpenAI Tier 1 rate limit" bullet
- [ ] Safeguard Section D appears after Section C and before any unrelated content
- [ ] QUOTA/P2 block appears within (or immediately after) Section C
- [ ] No existing text has been modified or deleted
- [ ] No formatting errors — headers, bullet points, tables render correctly
- [ ] `python manage.py check` returns 0 issues (docs change should not affect this,
  but run it anyway per protocol)
- [ ] All backtick code blocks are properly closed (even count of ``` in additions)
- [ ] Run `grep -n "Section D" CLAUDE.md` — must appear exactly once

---

## 🤖 REQUIRED AGENTS

Run in this order. Both must score 8.0+.

| Agent | Instruction |
|-------|-------------|
| `@docs-architect` | Review the three CLAUDE.md additions for clarity, completeness, internal consistency, and correct placement. Verify Section D architecture is unambiguous and buildable. Flag any gaps or contradictions. |
| `@api-documenter` | Review the QUOTA-1/QUOTA-2/P2-B/P2-C architecture notes for technical accuracy. Verify the OpenAI quota vs rate_limit distinction is correctly described. Verify all file references and env var names are consistent with the codebase. |

### Agent Ratings Table (Required in Report)

```
| Round | Agent            | Score | Key Findings         | Acted On? |
|-------|------------------|-------|----------------------|-----------|
| 1     | @docs-architect  | X/10  | summary              | Yes/No    |
| 1     | @api-documenter  | X/10  | summary              | Yes/No    |
| Avg   |                  | X.X/10| —                    | Pass/Fail |
```

**If average is below 8.0:** Fix issues and re-run. Do NOT commit until a confirmed
round averages 8.0+. Work is REJECTED without a passing agent round.

---

## 📊 COMPLETION REPORT

Write the full report (all 11 sections) to `docs/REPORT_143_E_DOCS_SAFEGUARD_D.md`.
Commit report + CLAUDE.md changes together in a single commit.

**Commit message:** `docs: add safeguard section D, rate limit compliance note, quota architecture (Session 143)`

---

## ⛔ BOTTOM REMINDERS

```
╔══════════════════════════════════════════════════════════════╗
║  DO NOT modify any code files — docs only                    ║
║  DO NOT skip Step 0 greps                                    ║
║  DO NOT commit with average agent score below 8.0            ║
║  DO NOT paraphrase the text blocks — add them verbatim       ║
║  DO verify Section D does not already exist before adding    ║
╚══════════════════════════════════════════════════════════════╝
```
