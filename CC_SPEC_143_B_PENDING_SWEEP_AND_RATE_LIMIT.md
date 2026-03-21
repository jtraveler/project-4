# CC_SPEC_143_B_PENDING_SWEEP_AND_RATE_LIMIT.md
# D1 — Pending Image Sweep + D3 — Rate Limit Compliance

**Session:** 143
**Spec Type:** Code — commit after full test suite passes
**Report Path:** `docs/REPORT_143_B_PENDING_SWEEP_AND_RATE_LIMIT.md`
**Commit Message:** `fix: D1 pending image sweep + D3 rate limit inter-batch delay (Session 143)`

---

## ⛔ STOP — READ BEFORE STARTING

```
╔══════════════════════════════════════════════════════════════╗
║  CRITICAL: tasks.py IS 🔴 CRITICAL TIER (~3,411 lines)      ║
║                                                              ║
║  HARD LIMITS FOR tasks.py:                                   ║
║  • Maximum 2 str_replace calls on tasks.py                   ║
║  • Use 5+ line anchors on every str_replace                  ║
║  • DO NOT rewrite any surrounding logic                      ║
║  • DO NOT add new imports outside the function body          ║
║    (use local imports inside the function instead)           ║
║                                                              ║
║  Work is REJECTED if:                                        ║
║  • Any agent scores below 8.0                                ║
║  • The full test suite does not pass before commit           ║
║  • tasks.py str_replace budget is exceeded                   ║
║  • The pending sweep runs BEFORE _run_generation_loop()      ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📋 OVERVIEW

**Modifies UI/Templates:** No
**Modifies Code:** Yes — `prompts/tasks.py`, `prompts_manager/settings.py`

### What This Spec Does

Fixes two production bugs discovered in Session 143 testing (13 prompt job):

**D1 — Pending Image Sweep**
After `_run_generation_loop()` exits (for ANY reason — normal completion,
quota stop, auth stop, cancel), images left in `queued` or `generating` state
are swept to `failed` with a clear message. The `failed_count` is then
recalculated from the DB rather than the in-memory counter, which may be
stale if the loop exited early.

**D3 — Rate Limit Compliance Inter-Batch Delay**
With `BULK_GEN_MAX_CONCURRENT=4`, the loop dispatches 4 images concurrently
per batch with NO delay between batches. This produces ~8–16 images/minute
against OpenAI Tier 1's 5 images/minute limit. Adds a configurable
`OPENAI_INTER_BATCH_DELAY` setting (env var) that inserts a sleep between
batches.

### Context

**D1 Root Cause:**
`_run_generation_loop()` processes images in batches. When `stop_job=True`
fires (auth failure or quota kill), the main loop `break`s before processing
remaining batches. Images in those unprocessed batches remain in `queued`
status. `get_job_status()` reads `failed_count` from actual
`status='failed'` DB records — `queued` images are never counted.
Result: header shows "0 Failed" even though images clearly didn't generate.

**D3 Root Cause:**
Phase 5D replaced sequential generation with `ThreadPoolExecutor`. The Phase
5C inter-image delay (13s) was NOT carried over into the batch loop. After
the executor context closes, the loop immediately starts the next batch with
no pause. With 4 concurrent workers, a full batch completes in ~15–30s,
then the next batch starts immediately — producing well above Tier 1's
5 images/minute limit.

**Immediate mitigation (no code needed — do this NOW in Heroku):**
```
BULK_GEN_MAX_CONCURRENT = 1
```

---

## 🎯 OBJECTIVES

### Primary Goal

1. Any image that does not transition to `completed` or `failed` by job
   finalisation is automatically swept to `failed` with a clear message
2. `failed_count` always reflects the true number of non-completed images
3. A configurable inter-batch delay prevents rate limit breaches

### Success Criteria

- ✅ After a job where `stop_job=True` fires on batch 2 of 4, images in
  batches 3 and 4 show `status='failed'` in DB (not `queued`)
- ✅ `get_job_status()` returns the correct `failed_count` for such a job
- ✅ `OPENAI_INTER_BATCH_DELAY=12` env var causes a 12s sleep between batches
- ✅ When `OPENAI_INTER_BATCH_DELAY=0` (default), behaviour is unchanged
- ✅ Full test suite passes
- ✅ All agents score 8.0+

---

## 🔍 STEP 0 — MANDATORY GREPS BEFORE ANY CHANGES

Run ALL of these before touching any file. Record findings in the report.

```bash
# 1. Confirm _run_generation_loop location and signature
grep -n "def _run_generation_loop" prompts/tasks.py

# 2. Confirm process_bulk_generation_job location
grep -n "def process_bulk_generation_job" prompts/tasks.py

# 3. Find exact line where _run_generation_loop is called (insertion anchor D1)
grep -n "_run_generation_loop\|completed_count, failed_count, total_cost" prompts/tasks.py

# 4. Find where failed_count is saved to job after the loop (second anchor D1)
grep -n "job\.failed_count\|failed_count.*save\|update_fields.*failed" prompts/tasks.py

# 5. Find the inter-batch delay / batch loop exit point (anchor D3)
grep -n "actual_cost.*save\|job\.save.*actual_cost\|inter_batch\|INTER_BATCH" prompts/tasks.py

# 6. Confirm no OPENAI_INTER_BATCH_DELAY already exists
grep -rn "OPENAI_INTER_BATCH_DELAY\|INTER_BATCH_DELAY" prompts/ prompts_manager/

# 7. Confirm settings.py location and find BULK_GEN_MAX_CONCURRENT entry
grep -n "BULK_GEN_MAX_CONCURRENT\|OPENAI_TIER" prompts_manager/settings.py

# 8. Check current line count for tasks.py (confirm tier)
wc -l prompts/tasks.py

# 9. Check current line count for settings.py
wc -l prompts_manager/settings.py

# 10. Read the FULL _run_generation_loop function body before touching it
#     (do not write any code until you have read this function end-to-end)
grep -n "def _run_generation_loop\|def _apply_generation_result\|def process_bulk" prompts/tasks.py
```

**Gate:** If `_run_generation_loop` does NOT exist at the expected location,
or if `OPENAI_INTER_BATCH_DELAY` already exists, stop and report to developer
before proceeding.

---

## 📁 FILES TO MODIFY

### File 1: `prompts/tasks.py`
**Tier:** 🔴 Critical — maximum 2 str_replace calls. No exceptions.

**str_replace call 1 of 2 — D1: Pending sweep + recalculate failed_count**

Find the block in `process_bulk_generation_job()` where
`_run_generation_loop()` is called and where `job.failed_count` is first
assigned after the loop. The addition goes BETWEEN these two — after the
loop returns, before `job.refresh_from_db()`.

**Exact anchor to find (read from actual file — do not guess line numbers):**
```python
        completed_count, failed_count, total_cost = _run_generation_loop(
            job, provider, job_api_key, images, IMAGE_COST_MAP, tz,
        )

        # Mark job complete (if not cancelled or stopped by auth failure)
        job.refresh_from_db(fields=['status'])
```

**Replace with:**
```python
        completed_count, failed_count, total_cost = _run_generation_loop(
            job, provider, job_api_key, images, IMAGE_COST_MAP, tz,
        )

        # D1: Sweep any images left in 'queued' or 'generating' state.
        # These occur when stop_job breaks the batch loop before remaining
        # batches are processed. Without this sweep, those images stay as
        # 'queued' and are never counted in failed_count.
        from prompts.models import BulkGenerationJob as _BGJ
        orphaned_qs = job.images.filter(status__in=['queued', 'generating'])
        orphaned_count = orphaned_qs.count()
        if orphaned_count:
            orphaned_qs.update(
                status='failed',
                error_message='Not generated — job ended unexpectedly',
            )
            logger.warning(
                "[D1-SWEEP] Swept %d orphaned images to failed for job %s",
                orphaned_count, job_id,
            )
            # Recalculate from DB — in-memory counter may be stale after sweep
            failed_count = job.images.filter(status='failed').count()
            _BGJ.objects.filter(pk=job.pk).update(
                failed_count=failed_count
            )

        # Mark job complete (if not cancelled or stopped by auth failure)
        job.refresh_from_db(fields=['status'])
```

---

**str_replace call 2 of 2 — D3: Inter-batch delay in `_run_generation_loop()`**

Find the inter-batch cost save at the END of the batch `for` loop body, just
before the loop iterates to the next batch. This is the last statement inside
the `for batch_start in range(...)` loop.

**Exact anchor to find (read from actual file):**
```python
        # Update job cost after each batch for live UI feedback.
        # completed_count and failed_count are updated per-image via F() expressions above.
        job.actual_cost = total_cost
        job.save(update_fields=['actual_cost'])

    return completed_count, failed_count, total_cost
```

**Replace with:**
```python
        # Update job cost after each batch for live UI feedback.
        # completed_count and failed_count are updated per-image via F() expressions above.
        job.actual_cost = total_cost
        job.save(update_fields=['actual_cost'])

        # D3: Inter-batch delay for OpenAI rate limit compliance.
        # Tier 1 allows 5 images/min. With max_workers=4 and no delay,
        # throughput exceeds the limit. Set OPENAI_INTER_BATCH_DELAY=12
        # in Heroku config vars to comply with Tier 1 (one image every 12s).
        # Skip the delay after the last batch.
        _inter_batch_delay = getattr(settings, 'OPENAI_INTER_BATCH_DELAY', 0)
        _is_last_batch = (
            batch_start + MAX_CONCURRENT_IMAGE_REQUESTS >= len(images_list)
        )
        if _inter_batch_delay > 0 and not _is_last_batch:
            logger.info(
                "[D3-RATE-LIMIT] Sleeping %ds between batches (job %s)",
                _inter_batch_delay, job.id,
            )
            time.sleep(_inter_batch_delay)

    return completed_count, failed_count, total_cost
```

---

### File 2: `prompts_manager/settings.py`
**Tier:** Read the file first to confirm tier. Expected ✅ Safe or 🟡 Caution.

Find the block where `BULK_GEN_MAX_CONCURRENT` is defined. Add
`OPENAI_INTER_BATCH_DELAY` immediately after it.

**Exact anchor to find:**
```python
BULK_GEN_MAX_CONCURRENT = int(os.environ.get('BULK_GEN_MAX_CONCURRENT', 4))
```

*(Note: if the actual line differs slightly, find the line with
`BULK_GEN_MAX_CONCURRENT` and `os.environ.get` and adapt accordingly.
Do NOT guess — read the file first.)*

**Replace with:**
```python
BULK_GEN_MAX_CONCURRENT = int(os.environ.get('BULK_GEN_MAX_CONCURRENT', 4))

# Inter-batch delay for OpenAI rate limit compliance (seconds).
# Tier 1 (5 img/min): set to 12 with BULK_GEN_MAX_CONCURRENT=1
# Tier 2 (50 img/min): set to 2 with BULK_GEN_MAX_CONCURRENT=4
# Default 0 = no delay (safe only if BULK_GEN_MAX_CONCURRENT=1 and jobs are small)
OPENAI_INTER_BATCH_DELAY = int(os.environ.get('OPENAI_INTER_BATCH_DELAY', 0))
```

---

## 🔄 DATA MIGRATION

No migration required. No model fields are changed.

The D1 sweep updates `GeneratedImage.status` and `BulkGenerationJob.failed_count`
at runtime — no historical backfill is needed. Existing jobs with orphaned
`queued` images are already complete; the sweep only fires for future jobs.

---

## 🧪 TESTS TO WRITE

Add tests to `prompts/tests/test_bulk_generator_views.py` or
`prompts/tests/test_bulk_generation_tasks.py` (grep for which file contains
`ProcessBulkJobTests` to confirm the correct file).

### Test 1 — D1: Orphaned queued images are swept to failed

```python
# Scenario: job has 6 images, loop processes batch 1 (images 1-4),
# stop_job fires on image 2, batch 2 (images 5-6) never runs.
# Expected: images 5-6 are swept to 'failed' after loop exits.
# Expected: failed_count on job reflects all failed images.
```

**Verification assertions (both required — avoids vacuous test):**
- `assertIn(orphaned_image.status, ['failed'])` — positive assertion
- `assertNotEqual(orphaned_image.status, 'queued')` — confirms state changed
- `assertEqual(job.failed_count, expected_total_failed_count)` — count is correct

### Test 2 — D1: No sweep fires when all images complete normally

```python
# Scenario: all images complete successfully.
# Expected: sweep query finds 0 orphaned images, no update occurs.
# Expected: failed_count is 0.
```

### Test 3 — D3: Inter-batch delay fires between batches (not after last)

```python
# Mock time.sleep, set OPENAI_INTER_BATCH_DELAY=5, run 3-image job
# with MAX_CONCURRENT_IMAGE_REQUESTS=1 (2 batches).
# Expected: time.sleep called once (between batch 1 and batch 2).
# Expected: time.sleep NOT called after the last batch.
```

### Test 4 — D3: No delay when OPENAI_INTER_BATCH_DELAY=0 (default)

```python
# Mock time.sleep, confirm it is never called when delay=0.
```

---

## ✅ PRE-AGENT SELF-CHECK

Before running agents, verify:

- [ ] Both str_replace calls used anchors of 5+ lines (not short single-line anchors)
- [ ] D1 sweep is placed AFTER `_run_generation_loop()` returns, BEFORE `job.refresh_from_db()`
- [ ] D3 delay is placed at the END of the batch loop body, BEFORE `return`
- [ ] D3 delay does NOT fire after the last batch (`_is_last_batch` check present)
- [ ] `orphaned_qs.update()` is a bulk queryset update (not a loop with `.save()`)
- [ ] `_BGJ.objects.filter(pk=job.pk).update(failed_count=failed_count)` uses
  exact count from DB, not the in-memory variable (which may be stale)
- [ ] `time.sleep` import already exists in tasks.py (line ~19) — do NOT add duplicate
- [ ] `settings` import already exists in tasks.py — do NOT add duplicate
- [ ] `OPENAI_INTER_BATCH_DELAY` added to settings.py uses `os.environ.get()`
  consistent with `BULK_GEN_MAX_CONCURRENT` pattern
- [ ] All 4 tests have BOTH positive and negative assertions (no vacuous tests)
- [ ] `python manage.py check` returns 0 issues
- [ ] `wc -l prompts/tasks.py` — confirm only 2 str_replace calls made

---

## 🤖 REQUIRED AGENTS

All agents must score 8.0+. Average must be ≥ 8.0.

| Agent | Role | Focus |
|-------|------|-------|
| `@django-pro` (sonnet) | Django ORM correctness | Queryset bulk update vs F() vs save(), transaction safety of D1 sweep, correct update_fields |
| `@python-pro` (sonnet) | Python code quality | Local import placement, variable naming, edge cases in sweep logic |
| `@security-auditor` (opus) | Security review | Ensure orphaned sweep cannot mark completed/published images as failed; verify no TOCTOU race on status update |
| `@backend-security-coder` (opus) | Backend security | Rate limit logging (confirm no sensitive info in log lines), settings env var injection safety |
| `@performance-optimizer` (sonnet) | Performance | Confirm `orphaned_qs.count()` + `orphaned_qs.update()` are two DB calls not N+1; check `filter(status='failed').count()` is indexed |
| `@code-reviewer` (sonnet) | General review | Logic correctness, test coverage completeness, edge case handling |

### Agent Ratings Table (Required)

```
| Round | Agent                    | Score | Key Findings              | Acted On? |
|-------|--------------------------|-------|---------------------------|-----------|
| 1     | @django-pro              | X/10  | summary                   | Yes/No    |
| 1     | @python-pro              | X/10  | summary                   | Yes/No    |
| 1     | @security-auditor        | X/10  | summary                   | Yes/No    |
| 1     | @backend-security-coder  | X/10  | summary                   | Yes/No    |
| 1     | @performance-optimizer   | X/10  | summary                   | Yes/No    |
| 1     | @code-reviewer           | X/10  | summary                   | Yes/No    |
| Avg   |                          | X.X/10| —                         | Pass/Fail |
```

**If average is below 8.0:** Fix ALL flagged issues and re-run agents. Do NOT
commit until a confirmed round scores 8.0+. Work is REJECTED otherwise.

---

## ⛔ BOTTOM REMINDERS

```
╔══════════════════════════════════════════════════════════════╗
║  tasks.py is 🔴 CRITICAL — 2 str_replace calls MAXIMUM      ║
║  D1 sweep must NEVER run before _run_generation_loop()       ║
║  D1 must NEVER update images with status='completed'         ║
║  D3 delay must NOT fire after the last batch                 ║
║  Full test suite must pass BEFORE commit                     ║
║  All 6 agents must score 8.0+ before commit                  ║
╚══════════════════════════════════════════════════════════════╝
```
