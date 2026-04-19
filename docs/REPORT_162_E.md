# REPORT_162_E — Narrow Bare Except in Bulk Generator Job View

**Spec:** CC_SPEC_162_E_RESULTS_VIEW_EXCEPT_NARROWING.md
**Date:** April 19, 2026
**Status:** Partial (Sections 1–8, 11). Sections 9–10 filled after full suite.

---

## Section 1 — Overview

Before this spec, `bulk_generator_job_view` at
`prompts/views/bulk_generator_views.py:104` computed `cost_per_image`
via `get_provider(job.provider, ...).get_cost_per_image(...)` inside a
`try:` block that caught bare `except Exception:` and silently fell
back to `get_image_cost(job.quality, job.size)` (the OpenAI cost map).

This was flagged as an 8.5-score concern by `@architect-review`
during 161-D: for a Replicate or xAI job whose provider lookup fails
(e.g., a model rename, a provider refactor), the view would
silently display OpenAI pricing ($0.034 medium/1024×1024) in place of
the real Replicate/xAI figure (up to $0.101 for NB2 medium). No log
signal, no observability.

161-D's scope was the root pricing-display bug (stored `estimated_cost`
was ignored) — fixing the observability gap was explicitly scoped
out. This spec closes that gap with two minimal changes:

1. Narrow the `except Exception:` to
   `except (ValueError, ImportError, AttributeError, KeyError) as e:`
   — the actual failure modes for provider-registry lookup.
2. Add `logger.warning(...)` before the fallback so any registry miss
   is visible in Heroku logs.

Fallback behavior (OpenAI cost map) is **intentionally unchanged**.
This is purely an observability hardening — the underlying semantic
fallback-is-wrong-for-non-OpenAI concern is tracked as a separate
follow-up.

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| `except Exception:` → `except (ValueError, ImportError, AttributeError, KeyError) as e:` | ✅ Met |
| Narrowed tuple covers the real failure modes (Step 0 grep of `registry.get_provider` confirmed `ValueError` — added to the tuple; spec draft had `KeyError` which is wrong for this registry) | ✅ Met |
| `logger.warning(...)` call added with `job.id`, `job.provider`, `job.model_name`, `type(e).__name__`, `e` | ✅ Met |
| Module-level logger present (`logger = logging.getLogger(__name__)` already existed at line 26) | ✅ Met |
| Fallback behavior unchanged (OpenAI cost map via `get_image_cost(...)`) | ✅ Met — diff shows the `cost_per_image = get_image_cost(...)` line is byte-identical |
| 3 regression tests added — happy path, narrowed exception + log, unexpected exception propagation | ✅ Met (with 1 extra log-content assertion absorbed per Rule 2) |
| Paired assertions throughout | ✅ Met |
| Stale narrative text grep (Rule 3) completed | ✅ Met — no stale "silent fallback is fine" comments in the file |
| `python manage.py check` clean | ✅ Met |

## Section 3 — Changes Made

### prompts/views/bulk_generator_views.py (+19 lines net)

Lines 120–140 (was 120–121): replaced bare `except Exception:` with
narrowed tuple. Added 14-line explanatory comment block enumerating
the four caught exceptions and documenting the deliberate exclusion of
other exception types (TypeError from refactor bugs should propagate).
Added 6-line `logger.warning(...)` call with `job.id`, `job.provider`,
`job.model_name`, `type(e).__name__`, and `e`.

Important deviation from the spec's AFTER block: spec draft listed
`(KeyError, ImportError, AttributeError)`, but Step 0 grep of
`prompts/services/image_providers/registry.py:39` confirmed
`get_provider` raises `ValueError` (not `KeyError`) for unknown
provider names. `ValueError` was added to the tuple. `KeyError`
retained in case a future provider's internal cost lookup uses a
dict access pattern. Tuple is therefore
`(ValueError, ImportError, AttributeError, KeyError)`.

### prompts/tests/test_bulk_generator_views.py (+82 lines)

Added 3 tests to existing `JobDetailViewContextTests` class (after
`test_estimated_total_cost_falls_back_for_legacy_jobs`):

- `test_cost_calculation_uses_provider_for_registered_job` — happy
  path. Mocks `prompts.services.image_providers.registry.get_provider`
  to return a MagicMock whose `get_cost_per_image` returns 0.101.
  Paired assertions: positive `assertAlmostEqual(..., 0.101)` +
  negative `assertNotAlmostEqual(..., 0.034)` (proves the OpenAI
  fallback was NOT taken) + call-args assertion
  (`assert_called_once_with('2:3', 'medium')`).
- `test_cost_calculation_logs_warning_when_provider_missing` — proves
  the narrowed-tuple branch fires AND emits a warning. Uses
  `self.assertLogs('prompts.views.bulk_generator_views', level='WARNING')`.
  Mocks `get_provider` with `side_effect=ValueError(...)`. Asserts 5
  log-content substrings (`'Provider registry lookup failed'`,
  `str(job.id)`, `'not-a-real-provider'`, `'unknown-model'`,
  `'ValueError'`) + asserts fallback cost hits `0.034` (OpenAI medium).
- `test_cost_calculation_does_not_swallow_unexpected_exceptions` —
  proves the narrowing actually works. Mocks `get_provider` with
  `side_effect=TypeError(...)`. Uses `self.assertRaises(TypeError)`
  around `self.client.get(url)` — Django test client re-raises
  uncaught view exceptions by default (`raise_request_exception=True`).
  If the narrowing were reverted to `except Exception:`, this test
  would fail because the TypeError would be swallowed and a 200
  response returned.

## Section 4 — Issues Encountered and Resolved

**Issue:** Spec draft specified the narrowed tuple as
`(KeyError, ImportError, AttributeError)`. Step 0 grep of
`prompts/services/image_providers/registry.py` lines 35–41 showed:

```python
if name not in PROVIDERS:
    ...
    raise ValueError(
        f"Unknown provider: '{name}'. Available: {available}"
    )
```

The real-world failure mode is `ValueError`, not `KeyError`. The spec
explicitly instructed to verify this via Step 0: *"If it raises a
custom exception type (`ProviderNotFoundError` or similar), add THAT
to the narrowed catch instead of generic KeyError/ImportError."*
**Fix:** tuple corrected to `(ValueError, ImportError, AttributeError,
KeyError)` — `KeyError` retained as a forward-looking defense for
future provider internals that use `dict[key]` patterns in
`get_cost_per_image`. Test 2's ValueError mock matches production
reality.

**Absorbed per Rule 2:** `@tdd-orchestrator` (9.0/10) noted that
`test_cost_calculation_logs_warning_when_provider_missing` asserted
`'not-a-real-provider'` (provider) in the log but not `'unknown-model'`
(model_name), despite the warning format logging both. 1-line
`self.assertIn('unknown-model', log_output)` added to strengthen the
paired assertion. Comment references Session 162 Rule 2.

## Section 5 — Remaining Issues

**Issue:** Eight other bare `except Exception:` blocks exist elsewhere
in `bulk_generator_views.py` at lines 783, 847, 988, 1154, 1356,
1445, 1550, 1569. Structurally similar but out of scope for 162-E.
**Recommended fix:** One-spec audit pass to add `logger.exception(...)`
or `logger.error(...)` at each endpoint boundary — the file is 🟠 High
Risk tier, so the audit must be read-only first, with surgical edits
in a follow-up. Flagged by `@architect-review`.
**Priority:** P2 (observability debt — same class of bug 162-E
closed at line 120).
**Reason not resolved:** Scope discipline — 162-E was explicitly
one-block-only.

**Issue:** The fallback-to-OpenAI-cost behavior is semantically wrong
for non-OpenAI jobs. If provider lookup fails for a Replicate NB2
job, the view now logs a warning (good) but still displays the
$0.034 OpenAI figure instead of the real ~$0.101 NB2 cost (bad).
162-E addressed observability only.
**Recommended fix:** If `job.provider != 'openai'` and registry
lookup fails, either (a) render "Cost unavailable" in the template,
or (b) pull the cost from the `GeneratorModel` DB table as a
secondary fallback. The DB fallback is preferable since
`GeneratorModel` already holds `credit_cost` for every registered
model. ~15-line change + 2 tests.
**Priority:** P2 (visible-to-user incorrect pricing).
**Reason not resolved:** Out of scope. Separately tracked in the
deferred items list for a future session.

## Section 6 — Concerns and Areas for Improvement

**Concern:** `@python-pro` (9.2/10) flagged that the local import
`from prompts.services.image_providers.registry import get_provider`
inside the view function body is an import-per-request overhead. This
pattern is intentional per CLAUDE.md's circular-import guidance for
🔴 Critical files, but `bulk_generator_views.py` is 🟠 High Risk, not
🔴 Critical, so the hoist may be safe.
**Impact:** Trivial (module is cached after first import; the
`import` statement is essentially a dict lookup).
**Recommended action:** None now. If a future refactor cleans up the
view module, hoist the import to module level at that time.

**Concern:** `@architect-review` (8.5/10) argued that `AttributeError`
(a missing `get_cost_per_image` method) is a code defect, not a
config gap, and should arguably be `logger.error` not `logger.warning`.
**Impact:** Low. Current unified treatment of all four exceptions as
warning is defensible — the fallback still works and the job still
renders; on-call paging is not warranted.
**Recommended action:** None now. If log volume triage shows
`AttributeError` fires are genuinely deployment defects, split into
two branches: AttributeError → `logger.error`, others → `logger.warning`.
This is a follow-up polish, not a correctness gap.

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @code-reviewer | 9.0/10 | Narrowing accurate (verified ValueError vs KeyError); fallback byte-identical; logger well-formed with lazy %s; tests well-scoped with paired assertions | N/A — clean pass |
| 1 | @django-pro | 9.0/10 | Logger pattern idiomatic Django (%-style positional); WARNING level appropriate; test-client re-raise behavior correct; no ORM side effects; minor cosmetic note on local import | Noted in Section 6 |
| 1 | @python-pro | 9.2/10 | Exception tuple Pythonic; `type(e).__name__` cleaner than %r; %-format args safe (UUID, strings); `%r` preserves None visibility on provider/model_name fields | N/A — clean pass |
| 1 | @tdd-orchestrator | 9.0/10 | All three code paths covered; paired assertion compliance strong; tests genuinely guard against the silent-swallow regression; flagged missing `model_name` log-content assertion | Absorbed per Rule 2 (+1 line) |
| 1 | @backend-security-coder | 9.5/10 | No sensitive data leak (all logged fields are non-secret); WARNING level correct; `%r` quoting neutralizes log-injection attempts; no new 500-handler exposure | N/A — clean pass |
| 1 | @architect-review | 8.5/10 | View-layer placement correct for domain-context observability; flagged 8 other bare except blocks as P2 audit follow-up; semantic-correctness gap (wrong cost for non-OpenAI fallback) acknowledged as separately-tracked | Noted in Section 5 as P2 |
| **Average** | | **9.03/10** | | **Pass** ≥ 8.0 |

## Section 8 — Recommended Additional Agents

All six required agents ran and scored 8.5+ on first pass. Coverage
dimensions exercised: code quality, Django idiom, Python idiom, test
structure, security, and architecture. No additional agent would
have materially improved review coverage for this ~20-line change.

## Section 9 — How to Test

### Automated

```bash
python manage.py test prompts.tests.test_bulk_generator_views.JobDetailViewContextTests --verbosity=2
# Expected: 11 tests, 0 failures (8 existing + 3 new).

python manage.py test prompts --verbosity=1
# Confirmed: 1321 tests (1318 post-162-D + 3 new 162-E), 12 skipped, 0 failures.

python manage.py check
# Expected: 0 issues.
```

### Manual Heroku verification (developer step, after deploy)

1. Tail logs watching for provider-registry failures:
   ```bash
   heroku logs --tail --app mj-project-4 | grep "Provider registry"
   ```
2. Proactive smoke: from `heroku run python manage.py shell`, create
   a BulkGenerationJob with `provider='not-a-real-provider'` and
   render the job detail page — log should emit the warning line
   with job_id, provider, model_name, and `ValueError`.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| TBD (filled post-commit) | fix(views): narrow bare except in bulk generator job view |

## Section 11 — What to Work on Next

1. **Remaining bare `except Exception:` audit (P2)** — 8 other sites
   in `bulk_generator_views.py`. Read-only audit first (file is 🟠
   High Risk tier, 1588 lines).
2. **Non-OpenAI semantic fallback correctness (P2)** — when provider
   lookup fails for a Replicate/xAI job, pull cost from
   `GeneratorModel.credit_cost` DB table instead of OpenAI map. ~15
   lines + 2 tests.
3. **Import hoisting (P3)** — if a future refactor touches the view,
   move the local `from registry import get_provider` to module level.
4. **AttributeError → logger.error split (P3)** — if log volume
   triage shows AttributeError fires are deployment defects rather
   than config gaps, split the warning branch.
