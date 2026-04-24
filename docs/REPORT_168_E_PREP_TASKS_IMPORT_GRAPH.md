# REPORT 168-E-prep — tasks.py Import Graph + Django-Q Contract Map

**Spec reference:** CC_SPEC_168_E_PREP.md v1
**Type:** Docs-only / read-only analysis
**Date:** April 24, 2026
**Status:** Complete — ready for 168-E spec drafting

---

## Preamble

### env.py safety gate

Command 1:

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:#     DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")
```

The `os.environ.setdefault("DATABASE_URL", ...)` line is
commented out (line 22). Only policy-explanation comments remain
at lines 17, 20.

Command 2:

```
$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Both gate commands pass. SQLite fallback is active; no production
DB exposure possible during this spec.

### 168-F-catchup prerequisite (Grep A)

```
$ git log --oneline -5
0f9263f docs: Session 168-F CHANGELOG + Recently Completed gap fix (Session 168-F-catchup)
16a95cf refactor: split prompts/admin.py into admin/ package (Session 168-F)
70f6222 docs: PROJECT_FILE_STRUCTURE catch-up for Sessions 168-C and 168-D (Session 168-catchup followup)
0430427 docs: consolidated CHANGELOG catch-up for Sessions 166–168-D (Session 168-catchup)
56cad16 refactor: split prompts/models.py into models/ package (Session 168-D)
```

168-F-catchup (`0f9263f`) is at HEAD. Prerequisite satisfied.

---

## Section 1 — Summary

`prompts/tasks.py` contains **49 function definitions, 3,822
lines, 6 `noqa: C901` markers, 34 in-function lazy imports, and
15 module-level constants** (one of which is a 184-line string
literal). Five of the six complexity-flagged functions are
themselves >160 LOC; four exceed 200 LOC.

Repository-wide Django-Q enumeration yielded:

- **7 unique function names** are registered as Django-Q
  string-reference callers via `async_task('prompts.tasks.X',
  ...)`. These constitute the **shim contract for 168-E**.
- **0 `schedule('prompts.tasks.X', ...)` calls.**
  `django_q.tasks.schedule` is not imported anywhere.
- **0 DB-stored `Schedule` rows** (Grep H: `Schedule.objects.
  count() == 0`). No persisted schedules to break.
- **32 function names** are imported directly via
  `from prompts.tasks import X` across tests, management
  commands, views, and admin (12 public + 20 private helpers).
- **9 module-level constants** are imported directly by test
  suites (`MAX_IMAGE_SIZE`, `MAX_CONCURRENT_IMAGE_REQUESTS`,
  `DEMOGRAPHIC_TAGS`, `PASS2_SEO_SYSTEM_PROMPT`,
  `PROTECTED_TAGS`, `TAG_RULES_BLOCK`, `GENERIC_TAGS`,
  `NSFW_VIOLATION_THRESHOLD`, `NSFW_VIOLATION_WINDOW_DAYS`).
- **Grand total: 41 distinct names** must flow through the
  `prompts/tasks/__init__.py` shim. Missing any single one
  produces `ImportError` at module-load time in at least one
  consumer file — LOUD failure caught by CI, but a material
  shim-design requirement.

Cross-function dependency mapping shows **natural domain
clustering** around (1) bulk generation orchestration, (2) AI
analysis pipeline, (3) B2 storage helpers, (4) SEO/Pass 2
review, (5) publish/create prompt pages, and (6) notifications.
The initial 8-domain hypothesis in the spec is broadly supported
by evidence, with minor adjustments noted in Section 10.

**The single highest-risk finding** is the size and complexity
of the shim contract: the `prompts/tasks/__init__.py` shim must
re-export 41 distinct names covering (a) 7 Django-Q string-
reference entry points — silent-failure risk, (b) 12 public and
20 private helper functions used by direct Python imports —
loud-failure risk, and (c) 9 module-level constants imported by
test suites. The Django-Q contract (7 names) has silent-failure
production implications; the direct-import contract (32 + 9 =
41 total) has loud-failure test-suite implications.

---

## Section 2 — Expectations

| Requirement | Status |
|---|---|
| env.py safety gate run, outputs recorded | ✅ Section 4 |
| No `migrate` / `makemigrations` run | ✅ Verified |
| Zero code changes; only the new report created | ✅ Section 3 |
| Zero new migrations | ✅ Migration dir unchanged (87 files incl. `__init__.py`) |
| 168-F-catchup committed before start | ✅ `0f9263f` at HEAD |
| All 49 functions catalogued with line range + LOC | ✅ Section 5 |
| Module-level constants catalogued | ✅ Section 6 |
| Django-Q string-reference callers enumerated | ✅ Section 7 |
| Direct-import external callers enumerated | ✅ Section 8 |
| All 34 in-function lazy imports enumerated | ✅ Section 9 |
| Proposed 8-domain grouping verified against evidence | ✅ Section 10 |
| 168-E blockers + risks enumerated with severity | ✅ Section 11 |
| `python manage.py check` clean pre + post | ✅ 0 issues both passes |
| Read tasks.py IN FULL (memory rule #8) | ✅ Lines 1–3,822 read |
| Evidence is descriptive, not prescriptive | ✅ Section 10 "not binding" |

---

## Section 3 — Files Changed

New files (1):

- `docs/REPORT_168_E_PREP_TASKS_IMPORT_GRAPH.md` — this report

Modified files: **none**
Migrations: **none**
Code files: **none**

---

## Section 4 — Evidence

### env.py safety gate

Recorded in Preamble. `DATABASE_URL: NOT SET` confirmed.

### Grep A — 168-F-catchup commit

Recorded in Preamble. HEAD is `0f9263f`.

### Grep B — tasks.py state

```
$ wc -l prompts/tasks.py
    3822 prompts/tasks.py

$ grep -c "^def \|^async def " prompts/tasks.py
49

$ grep -c "noqa: C901" prompts/tasks.py
6
```

Line count matches spec expectation exactly (3,822). Function
count matches (49). `noqa: C901` count is 6 — within the "5 or
6" band allowed by Grep B.

### Grep C — function definitions

49 entries. Full listing embedded in Section 5 below.

### Grep D — Django-Q string-reference callers

All callers enumerated. Unique `prompts.tasks.FUNC` targets: 7.
Details in Section 7.

### Grep E — in-function lazy imports

34 hits. Details in Section 9.

### Grep F — top-level imports

```python
import concurrent.futures
import json
import logging
import re
import time
import uuid
from typing import Optional, Tuple
from urllib.parse import urlparse
import base64
import requests

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.urls import reverse
from django.utils.text import slugify
```

17 top-level import lines. Note `from django.db.models import
F, Q` and `from django.db import IntegrityError, transaction`
are heavily used by the bulk-gen + publish paths. Every split
submodule will need a targeted subset of these imports.

### Grep G — direct-import external callers

Located 85 match lines across 17 consumer files. Full table in
Section 8.

### Grep H — DB-stored Schedule entries

```
Active Django-Q schedules: 0
```

**Zero persisted schedules.** The quietest Django-Q failure mode
(schedule pointing to a relocated dotted path) has zero surface
in this repo today.

### Grep I — cross-function dependencies

37 caller relationships catalogued. Summary in Section 10.

### `python manage.py check`

Pre-analysis: `System check identified no issues (0 silenced).`
Post-analysis: `System check identified no issues (0 silenced).`

---

## Section 5 — Function inventory (primary data)

LOC = line-range span, inclusive of the `def` line, docstring,
and trailing blank line before the next def. `noqa: C901` lines
are as recorded in source.

| # | Function | Lines | LOC | Public/Private | `noqa: C901` | Proposed domain |
|---|---|---|---|---|---|---|
| 1 | `_fire_bulk_gen_job_notification` | 49–71 | 23 | private | — | notifications |
| 2 | `_fire_bulk_gen_publish_notification` | 74–102 | 29 | private | — | notifications |
| 3 | `_record_nsfw_violation` | 110–127 | 18 | private | — | nsfw_moderation |
| 4 | `_check_nsfw_repeat_offender` | 130–156 | 27 | private | — | nsfw_moderation |
| 5 | `_fire_nsfw_repeat_offender_notification` | 159–192 | 34 | private | — | notifications |
| 6 | `run_nsfw_moderation` | 195–261 | 67 | **public (Django-Q entry)** | — | nsfw_moderation |
| 7 | `test_task` | 264–279 | 16 | **public (Django-Q entry)** | — | placeholders / diagnostics |
| 8 | `placeholder_nsfw_moderation` | 282–311 | 30 | public | — | placeholders |
| 9 | `generate_ai_content` | 314–325 | 12 | public (deprecated stub) | — | ai_analysis |
| 10 | `_get_analysis_url` | 328–355 | 28 | private | — | ai_analysis |
| 11 | `_call_openai_vision` | 358–431 | 74 | private | — | ai_analysis |
| 12 | `_validate_and_fix_tags` | 434–580 | 147 | private | **✓** | ai_analysis (tag rules live here) |
| 13 | `_is_quality_tag_response` | 770–810 | 41 | private | — | ai_analysis |
| 14 | `_call_openai_vision_tags_only` | 813–921 | 109 | private | — | ai_analysis |
| 15 | `_is_safe_image_url` | 924–953 | 30 | private | — | ai_analysis (SSRF guard for AI pipeline) |
| 16 | `_download_and_encode_image` | 956–1007 | 52 | private | — | ai_analysis |
| 17 | `_build_analysis_prompt` | 1010–1262 | 253 | private | — | ai_analysis (mostly one string literal) |
| 18 | `_parse_ai_response` | 1265–1297 | 33 | private | — | ai_analysis |
| 19 | `_validate_ai_result` | 1300–1343 | 44 | private | — | ai_analysis |
| 20 | `_update_prompt_with_ai_content` | 1346–1455 | 110 | private | — | ai_analysis |
| 21 | `_sanitize_content` | 1458–1481 | 24 | private | — | ai_analysis |
| 22 | `_generate_unique_slug_with_retry` | 1484–1506 | 23 | private | — | ai_analysis (single-upload slug flow) |
| 23 | `_handle_ai_failure` | 1509–1549 | 41 | private | — | ai_analysis |
| 24 | `placeholder_variant_generation` | 1552–1584 | 33 | public | — | placeholders |
| 25 | `_is_valid_uuid` | 1597–1616 | 20 | private | — | ai_analysis (AI job cache validator) |
| 26 | `update_ai_job_progress` | 1619–1646 | 28 | public | — | ai_analysis |
| 27 | `get_ai_job_status` | 1649–1669 | 21 | public | — | ai_analysis |
| 28 | `generate_ai_content_cached` | 1672–1852 | 181 | **public (Django-Q entry)** | — | ai_analysis |
| 29 | `rename_prompt_files_for_seo` | 1863–2052 | 190 | **public (Django-Q entry)** | **✓** | seo_pipeline |
| 30 | `_build_pass2_prompt` | 2262–2290 | 29 | private | — | seo_pipeline |
| 31 | `run_seo_pass2_review` | 2293–2520 | 228 | **public (Django-Q entry)** | **✓** | seo_pipeline |
| 32 | `queue_pass2_review` | 2523–2557 | 35 | public | — | seo_pipeline |
| 33 | `_run_generation_with_retry` | 2564–2646 | 83 | private | — | bulk_generation |
| 34 | `_apply_generation_result` | 2649–2714 | 66 | private | — | bulk_generation |
| 35 | `_run_generation_loop` | 2717–2878 | 162 | private | **✓** | bulk_generation |
| 36 | `_get_platform_api_key` | 2881–2894 | 14 | private | — | bulk_generation |
| 37 | `_deduct_generation_credits` | 2897–2939 | 43 | private | — | bulk_generation |
| 38 | `process_bulk_generation_job` | 2942–3083 | 142 | **public (Django-Q entry)** | — | bulk_generation |
| 39 | `_get_b2_client` | 3086–3098 | 13 | private | — | b2_storage |
| 40 | `_upload_generated_image_to_b2` | 3101–3147 | 47 | private | — | b2_storage |
| 41 | `_upload_source_image_to_b2` | 3150–3193 | 44 | private | — | b2_storage |
| 42 | `_is_private_ip_host` | 3196–3209 | 14 | private | — | b2_storage |
| 43 | `_download_source_image` | 3212–3268 | 57 | private | — | b2_storage |
| 44 | `_apply_m2m_to_prompt` | 3271–3307 | 37 | private | — | prompt_pages |
| 45 | `create_prompt_pages_from_job` | 3310–3521 | 212 | public | **✓** | prompt_pages |
| 46 | `_ensure_unique_title` | 3524–3542 | 19 | private | — | prompt_pages |
| 47 | `_generate_unique_slug` | 3545–3567 | 23 | private | — | prompt_pages |
| 48 | `publish_prompt_pages_from_job` | 3570–3797 | 228 | **public (Django-Q entry)** | **✓** | prompt_pages |
| 49 | `_fire_quota_alert_notification` | 3800–3822 | 23 | private | — | notifications |

### Summary statistics

- Total functions: **49**
- Public (no leading underscore): **13** (9 real public + 4
  module-level API exposed to consumers)
- Private (leading underscore): **36**
- `noqa: C901` flagged: **6** (spec expected 5–6; found 6)
- Functions >200 LOC: **4** (#28, #31, #45, #48)
- Functions 100–200 LOC: **6** (#12, #14, #20, #29, #35, #38)
- Functions ≤100 LOC: **39** (80% of functions)

### Complexity hotspots (`noqa: C901`)

| Function | LOC | Reason noted in source |
|---|---|---|
| `_validate_and_fix_tags` (L434) | 147 | "tag validation requires complex branching" |
| `rename_prompt_files_for_seo` (L1863) | 190 | "SEO renaming has many conditional paths" |
| `run_seo_pass2_review` (L2293) | 228 | "multi-step AI review pipeline" |
| `_run_generation_loop` (L2717) | 162 | "generation loop has inherent branching for batching, cancellation, and error handling" |
| `create_prompt_pages_from_job` (L3310) | 212 | "page creation requires branching for M2M, error handling, and TOCTOU retry" |
| `publish_prompt_pages_from_job` (L3570) | 228 | (no explicit comment; implicit reason: near-duplicate of #45 with ThreadPoolExecutor) |

**168-E scope note:** the spec explicitly forbids reducing
complexity as part of the split. All 6 flagged functions should
move verbatim. Simplification is a separate refactor track.

---

## Section 6 — Module-level constants

15 module-level names. Critical for the split because several
are imported directly by consumers (see Section 8) and must be
re-exported by the shim.

| Line | Name | Type | Shim re-export required? |
|---|---|---|---|
| 33 | `logger` | logging.Logger | No (internal) |
| 36 | `NSFW_CACHE_TTL` | int | Conditional (not seen in Grep G, but symmetry with `AI_JOB_CACHE_TIMEOUT` suggests re-export) |
| 39 | `MAX_IMAGE_SIZE` | int | **Yes** — `test_src6_source_image_upload.py:219, 237` imports it |
| 46 | `MAX_CONCURRENT_IMAGE_REQUESTS` | int | **Yes** — `test_bulk_generation_tasks.py:1109, 1172` imports it |
| 106 | `NSFW_VIOLATION_THRESHOLD` | int | Conditional |
| 107 | `NSFW_VIOLATION_WINDOW_DAYS` | int | Conditional |
| 585 | `GENERIC_TAGS` | frozenset-like set | Internal (used only by `_is_quality_tag_response`) |
| 601 | `TAG_RULES_BLOCK` | str (~82 lines) | Internal |
| 695 | `SPLIT_THESE_WORDS` | set | Internal |
| 703 | `PRESERVE_DESPITE_STOP_WORDS` | set | Internal |
| 709 | `PRESERVE_SINGLE_CHAR_COMPOUNDS` | set | Internal |
| 721 | `DEMOGRAPHIC_TAGS` | set | **Yes** — `test_validate_tags.py:12` imports it |
| 731 | `GENDER_LAST_TAGS` | set | Internal |
| 734 | `BANNED_AI_TAGS` | set | Internal |
| 740 | `ALLOWED_AI_TAGS` | set | Internal |
| 747 | `PROTECTED_TAGS` | set | Internal |
| 761 | `BANNED_ETHNICITY` | set | Internal |
| 1594 | `AI_JOB_CACHE_TIMEOUT` | int | Internal |
| 2070 | `PASS2_SEO_SYSTEM_PROMPT` | str (~190 lines) | Internal |

**Tag-validation constants cluster (L585–L767)** is logically a
`tags_constants` module (~180 lines) that `ai_analysis` and
`seo_pipeline` both consume. 168-E should consider whether to
(a) leave them in whichever submodule `_validate_and_fix_tags`
lives in, and import from there in the Pass 2 submodule, or
(b) hoist them into a shared `constants.py` or `tag_rules.py`
submodule. Option (b) is cleaner architecturally; option (a)
matches the 168-D precedent (models split kept shared items in
a `constants.py` submodule).

**Load-order sensitivity:** `MAX_CONCURRENT_IMAGE_REQUESTS`
(line 46) evaluates `getattr(settings, 'BULK_GEN_MAX_CONCURRENT',
4)` at import time. If the split puts this in a submodule
imported lazily, the first-import-wins behavior shifts (today
it's always first because `prompts.tasks` is imported at Django
app-ready time via task discovery). The comment at lines 42–45
explicitly documents this as a known test-mocking gotcha:
"@override_settings(BULK_GEN_MAX_CONCURRENT=N) in tests will NOT
change this value." The split must preserve this semantics or
document any change.

---

## Section 7 — Django-Q string-reference callers (CRITICAL)

### 7.1 — `async_task('prompts.tasks.X', ...)` registrations

All 13 `async_task` call sites across the entire repository.
Each names a `prompts.tasks.X` function as the first positional
argument.

| Caller file:line | Function referenced | Context |
|---|---|---|
| `prompts/tasks.py:11` | `run_nsfw_moderation` | module docstring example (not a runtime call) |
| `prompts/tasks.py:12` | `generate_ai_content_cached` | module docstring example (not a runtime call) |
| `prompts/tasks.py:276` | `test_task` | inside `test_task` docstring (not a runtime call) |
| `prompts/tasks.py:1447` | `rename_prompt_files_for_seo` | **internal** call from `_update_prompt_with_ai_content` (single-upload AI flow) |
| `prompts/tasks.py:2544` | `run_seo_pass2_review` | **internal** call from `queue_pass2_review` (with 45s schedule) |
| `prompts/tasks.py:3488` | `rename_prompt_files_for_seo` | **internal** call from `create_prompt_pages_from_job` |
| `prompts/tasks.py:3758` | `rename_prompt_files_for_seo` | **internal** call from `publish_prompt_pages_from_job` |
| `prompts/admin/prompt_admin.py:921` | `rename_prompt_files_for_seo` | admin `save_model` hook when `b2_image_url` present |
| `prompts/management/commands/test_django_q.py:146` | `test_task` | diagnostic command smoke test |
| `prompts/management/commands/backfill_ai_content.py:562` | `rename_prompt_files_for_seo` | queue SEO rename post-backfill |
| `prompts/views/upload_api_views.py:707` | `generate_ai_content_cached` | AI content task after video NSFW check |
| `prompts/views/upload_views.py:495` | `rename_prompt_files_for_seo` | upload-flow SEO rename (Session 122 fix) |
| `prompts/views/bulk_generator_views.py:759` | `publish_prompt_pages_from_job` | concurrent publish task queued from view |
| `prompts/views/moderation_api_views.py:52` | `run_nsfw_moderation` | image NSFW moderation task |
| `prompts/views/moderation_api_views.py:232` | `generate_ai_content_cached` | AI content task after image NSFW check |
| `prompts/services/bulk_generation.py:339` | `process_bulk_generation_job` | orchestrator task queued from `start_job` |

### 7.2 — `schedule(...)` registrations

```
(No matches)
```

`django_q.tasks.schedule` is not imported anywhere in the repo.
`async_task` is the only Django-Q string-reference entry point.

**Caveat:** `queue_pass2_review` at `tasks.py:2544` uses
`async_task` with `schedule_type='O'` + `next_run=run_at` — this
is a scheduled async task registered via async_task, NOT via the
Schedule model. It still resolves `'prompts.tasks.run_seo_pass2_
review'` via `importlib` at runtime.

### 7.3 — DB-stored `Schedule` entries

```
Active Django-Q schedules: 0
```

Zero rows. No persisted schedules reference `prompts.tasks.X`
today. This vector has zero 168-E risk surface.

**Future-proofing note:** if 168-E lands in a window where an
operator has recently created a scheduled task (e.g., via admin
or management command), the Schedule model's `func` column would
hold a stale dotted path. Recommendation: the 168-E post-push
protocol should include a verification step that re-runs Grep H
just before deploy and cross-references the count. If non-zero,
audit each row's `func` against the new shim contract.

### 7.4 — Shim contract (THE CRITICAL LIST)

**The following 7 function names MUST be re-exported by
`prompts/tasks/__init__.py` post-split so that `importlib.
import_module('prompts.tasks').getattr(FUNC)` resolves exactly
as it does today:**

1. `run_nsfw_moderation` — `moderation_api_views.py:52`
2. `generate_ai_content_cached` — `upload_api_views.py:707`,
   `moderation_api_views.py:232`
3. `test_task` — `management/commands/test_django_q.py:146`
4. `rename_prompt_files_for_seo` — 6 call sites
   (`admin/prompt_admin.py:921`, `management/commands/backfill_
   ai_content.py:562`, `views/upload_views.py:495`, plus 3
   internal self-calls at `tasks.py:1447, 3488, 3758`)
5. `run_seo_pass2_review` — 1 internal self-call at
   `tasks.py:2544` via `queue_pass2_review`
6. `process_bulk_generation_job` — `services/bulk_generation.
   py:339`
7. `publish_prompt_pages_from_job` — `views/bulk_generator_
   views.py:759`

**Failure mode if any of the above is missing from the shim:**
`async_task(...)` enqueues successfully (it does not validate
the path at queue time). When the qcluster worker picks up the
task, `importlib.import_module('prompts.tasks')` resolves the
new package but `getattr('prompts.tasks', FUNC)` raises
`AttributeError`. Django-Q logs the failure and marks the Task
as failed; the user sees nothing unless they check Heroku logs.
**This is the silent-failure risk the spec warns about.**

**Verification strategy for 168-E:** a post-split smoke test
should exist that imports and calls each of the 7 names via
`importlib`:

```python
import importlib
mod = importlib.import_module('prompts.tasks')
for name in ['run_nsfw_moderation', 'generate_ai_content_cached',
             'test_task', 'rename_prompt_files_for_seo',
             'run_seo_pass2_review', 'process_bulk_generation_job',
             'publish_prompt_pages_from_job']:
    assert hasattr(mod, name), f"{name} missing from shim"
```

This assertion set should be part of the 168-E test suite or
`manage.py check` custom check.

---

## Section 8 — External callers via direct Python import

All `from prompts.tasks import X` / `from prompts import tasks`
/ `import prompts.tasks` references across the repo. These are
ALSO shim-contract requirements, but with LOUDER failure mode
(`ImportError` at module load or at the call site, which CI
catches immediately).

Line counts are approximate — matches aggregated from `grep -rn`
output.

### Test files (majority of usage)

| Caller file | Names imported | Call sites |
|---|---|---|
| `tests/test_tags_context.py:18` | `_call_openai_vision_tags_only` | 1 (module-level import) |
| `tests/test_src6_source_image_upload.py` | `_apply_generation_result`, `_is_private_ip_host`, `_download_source_image`, `MAX_IMAGE_SIZE` | 10 (1 module-level + 9 in-function) |
| `tests/test_backfill_hardening.py:16` | Module-level: `_is_quality_tag_response`, `GENERIC_TAGS`. In-function: `_call_openai_vision`, `_call_openai_vision_tags_only` (at L164, L177, L194, L232, L245, L259) | 8 (1 module-level + 7 in-function) |
| `tests/test_source_credit.py` | `create_prompt_pages_from_job` | 2 in-function |
| `tests/test_bulk_generator_views.py` | `publish_prompt_pages_from_job` (×4), `process_bulk_generation_job` | 5 in-function |
| `tests/test_validate_tags.py:12` | `_validate_and_fix_tags`, `DEMOGRAPHIC_TAGS` | 1 module-level |
| `tests/test_nsfw_violations.py:14` | `_record_nsfw_violation`, `_check_nsfw_repeat_offender`, `_fire_nsfw_repeat_offender_notification`, `NSFW_VIOLATION_THRESHOLD`, `NSFW_VIOLATION_WINDOW_DAYS` | 1 module-level |
| `tests/test_bulk_generation_tasks.py` | `_run_generation_loop`, `process_bulk_generation_job` (×16), `MAX_CONCURRENT_IMAGE_REQUESTS` (×2), `create_prompt_pages_from_job` (×8), `_generate_unique_slug` (×3), `_upload_generated_image_to_b2` (×2), `_run_generation_with_retry` (×5) | 36+ |
| `tests/test_bulk_gen_notifications.py:14` | `_fire_bulk_gen_job_notification`, `_fire_bulk_gen_publish_notification` (module-level); `_run_generation_with_retry` at L215; `_fire_quota_alert_notification` at L252 | 3 (1 module-level + 2 in-function) |
| `tests/test_bulk_page_creation.py:24` | `create_prompt_pages_from_job`, `publish_prompt_pages_from_job` | 3 |
| `tests/test_pass2_seo_review.py:24` | `PASS2_SEO_SYSTEM_PROMPT`, `PROTECTED_TAGS`, `TAG_RULES_BLOCK`, `_build_pass2_prompt`, `run_seo_pass2_review`, `queue_pass2_review`, `_validate_and_fix_tags`, `_is_quality_tag_response` | 1 module-level |
| `tests/test_bulk_gen_rename.py` | `rename_prompt_files_for_seo` | 6 in-function |

### Non-test consumers

| Caller file | Names imported | Call sites |
|---|---|---|
| `management/commands/test_django_q.py:114` | `test_task`, `placeholder_nsfw_moderation`, `placeholder_ai_generation` (DEAD — does not exist), `placeholder_variant_generation` — entire block wrapped in `try/except ImportError` | 1 module-level |
| `management/commands/run_pass2_review.py:18` | `run_seo_pass2_review` | 1 module-level |
| `management/commands/backfill_bulk_gen_seo_rename.py:7` | `rename_prompt_files_for_seo` | 1 module-level |
| `management/commands/backfill_ai_content.py:161, 343` | L161: `_call_openai_vision_tags_only`, `_is_quality_tag_response`, `_validate_and_fix_tags`. L343: `_call_openai_vision`, `_is_quality_tag_response`, `_sanitize_content`, `_generate_unique_slug_with_retry`, `_validate_and_fix_tags` | 2 in-function |
| `management/commands/reorder_tags.py:18` | `_validate_and_fix_tags` | 1 module-level |
| `management/commands/backfill_categories.py:62` | `_call_openai_vision` | 1 in-function |
| `admin/prompt_admin.py:434, 473, 522, 582, 721, 773, 797` | `_validate_and_fix_tags`, `queue_pass2_review` (multiple), `_call_openai_vision`, `_sanitize_content`, tuple import at 721 | 7 in-function |
| `views/moderation_api_views.py:218` | `_record_nsfw_violation` | 1 in-function |
| `views/prompt_trash_views.py:239, 274` | `queue_pass2_review` | 2 in-function |
| `views/upload_views.py:313, 506, 631` | `get_ai_job_status`, `_validate_and_fix_tags`, `queue_pass2_review` | 3 in-function |
| `views/ai_api_views.py:210` | `get_ai_job_status` | 1 in-function |

### Distinct names imported directly (required shim re-exports via Python import path)

**Resolution of tuple-import files:** §8's consumer table flagged
several "tuple import (multiple — inspect file for exact list)"
entries. Those have now been fully resolved by direct file
inspection. The complete consolidated shim contract below.

Consolidating Sections 7 and 8, `prompts/tasks/__init__.py`
MUST re-export the following **41 names** so every import
across the repo continues to resolve after the split. Grouped
by category.

**Public task entry points — 7 names (Django-Q-registered, per §7.4):**
- `run_nsfw_moderation`
- `generate_ai_content_cached`
- `test_task`
- `rename_prompt_files_for_seo`
- `run_seo_pass2_review`
- `process_bulk_generation_job`
- `publish_prompt_pages_from_job`

**Public API called by direct imports — 5 names:**
- `queue_pass2_review` (admin, views, management command)
- `get_ai_job_status` (views/upload_views.py, views/ai_api_views.py)
- `create_prompt_pages_from_job` (test_source_credit.py,
  test_bulk_page_creation.py, test_bulk_generation_tasks.py)
- `placeholder_nsfw_moderation` (management/commands/test_django_q.py:114)
- `placeholder_variant_generation` (management/commands/test_django_q.py:114)

**Private helpers imported by tests / management commands / admin — 20 names:**
- `_call_openai_vision` (admin/prompt_admin.py, management/commands/
  backfill_ai_content.py, test_backfill_hardening.py)
- `_call_openai_vision_tags_only` (management/commands/backfill_ai_
  content.py, test_tags_context.py, test_backfill_hardening.py)
- `_validate_and_fix_tags` (admin/prompt_admin.py:434, management/
  commands/backfill_ai_content.py, management/commands/reorder_tags.py,
  views/upload_views.py:506, test_validate_tags.py, test_pass2_
  seo_review.py)
- `_is_quality_tag_response` (management/commands/backfill_ai_content.py,
  test_backfill_hardening.py:17, test_pass2_seo_review.py:31)
- `_sanitize_content` (admin/prompt_admin.py:522, management/commands/
  backfill_ai_content.py:346)
- `_apply_generation_result` (test_src6_source_image_upload.py:10)
- `_run_generation_with_retry` (test_bulk_generation_tasks.py,
  test_bulk_gen_notifications.py:215)
- `_run_generation_loop` (test_bulk_generation_tasks.py:541)
- `_upload_generated_image_to_b2` (test_bulk_generation_tasks.py:1431, 1467)
- `_is_private_ip_host` (test_src6_source_image_upload.py)
- `_download_source_image` (test_src6_source_image_upload.py)
- `_generate_unique_slug` (test_bulk_generation_tasks.py:1385, 1392, 1533)
- `_generate_unique_slug_with_retry` (management/commands/backfill_ai_
  content.py:346) — **DISTINCT** from `_generate_unique_slug` (line 3545);
  this is the AI-analysis-domain variant at line 1484
- `_record_nsfw_violation` (views/moderation_api_views.py:218,
  test_nsfw_violations.py:14)
- `_check_nsfw_repeat_offender` (test_nsfw_violations.py:14)
- `_fire_nsfw_repeat_offender_notification` (test_nsfw_violations.py:14)
- `_fire_bulk_gen_job_notification` (test_bulk_gen_notifications.py:14)
- `_fire_bulk_gen_publish_notification` (test_bulk_gen_notifications.py:14)
- `_fire_quota_alert_notification` (test_bulk_gen_notifications.py:252)
- `_build_pass2_prompt` (test_pass2_seo_review.py:27)

**Module-level constants imported by tests — 9 names:**
- `MAX_IMAGE_SIZE` (test_src6_source_image_upload.py:219, 237)
- `MAX_CONCURRENT_IMAGE_REQUESTS` (test_bulk_generation_tasks.py:1109, 1172)
- `DEMOGRAPHIC_TAGS` (test_validate_tags.py:12)
- `PASS2_SEO_SYSTEM_PROMPT` (test_pass2_seo_review.py:24)
- `PROTECTED_TAGS` (test_pass2_seo_review.py:25)
- `TAG_RULES_BLOCK` (test_pass2_seo_review.py:26)
- `GENERIC_TAGS` (test_backfill_hardening.py:18)
- `NSFW_VIOLATION_THRESHOLD` (test_nsfw_violations.py:18)
- `NSFW_VIOLATION_WINDOW_DAYS` (test_nsfw_violations.py:19)

**Total distinct names that must flow through the shim: 41**
(20 private helpers + 12 public + 9 constants).

### Pre-existing dead import (NOT a shim requirement)

`management/commands/test_django_q.py:114` imports a function
that **does not exist in tasks.py**:

```python
from prompts.tasks import (
    test_task,
    placeholder_nsfw_moderation,
    placeholder_ai_generation,      # ← DOES NOT EXIST
    placeholder_variant_generation,
)
```

The entire import block is wrapped in `try/except ImportError`
(lines 113–128), so this has been failing gracefully since the
file's creation. 168-E should **NOT** add a stub for
`placeholder_ai_generation` — the correct fix is to remove the
dead name from the import block in `test_django_q.py` as part
of an unrelated cleanup spec. For 168-E purposes: preserve
current behavior (the try/except continues to catch the
ImportError).

### Shim sizing context

This is a LARGER surface than 168-D's models shim (34 re-exports
were mostly model classes with clean semantics). Here the surface
is 41 names split across tasks, constants, and private helpers
with subtle import-order implications.

**168-E test coverage recommendation:** follow the 168-D pattern
of adding an explicit `from prompts.tasks import *`-style
assertion that verifies every name in the `__all__` list is
accessible from the shim. Include constants AND private helpers
in `__all__` (deviates from PEP 8 convention but matches actual
test-file usage — underscore-prefixed names are imported directly
by 8 test modules). Alternative: a `test_shim_contract.py` that
imports every name from a hardcoded list and asserts `hasattr`
on each — catches regressions without relying on `__all__`.

---

## Section 9 — In-function lazy imports inside tasks.py

All 34 lazy imports, catalogued in source order. These are the
circular-import break patterns the split must preserve.

| # | Line | Containing function | Imported | Purpose |
|---|---|---|---|---|
| 1 | 51 | `_fire_bulk_gen_job_notification` | `from prompts.services.notifications import create_notification` | notifications service |
| 2 | 76 | `_fire_bulk_gen_publish_notification` | same as #1 | notifications service |
| 3 | 117 | `_record_nsfw_violation` | `from prompts.models import NSFWViolation` | model (break circular) |
| 4 | 138 | `_check_nsfw_repeat_offender` | `from prompts.models import NSFWViolation` | model (break circular) |
| 5 | 165 | `_fire_nsfw_repeat_offender_notification` | `from prompts.services.notifications import create_notification` | notifications service |
| 6 | 226 | `run_nsfw_moderation` | `from prompts.services.vision_moderation import VisionModerationService` | vision service |
| 7 | 374 | `_call_openai_vision` | `from prompts.constants import OPENAI_TIMEOUT` | constants |
| 8 | 831 | `_call_openai_vision_tags_only` | `from prompts.constants import OPENAI_TIMEOUT` | constants |
| 9 | 1396 | `_update_prompt_with_ai_content` | `from prompts.models import SubjectCategory` | model (break circular) |
| 10 | 1408 | `_update_prompt_with_ai_content` | `from prompts.models import SubjectDescriptor` | model (break circular) |
| 11 | 1492 | `_generate_unique_slug_with_retry` | `from prompts.models import Prompt` | model (break circular) |
| 12 | 1879 | `rename_prompt_files_for_seo` | `from prompts.models import Prompt` | model (break circular) |
| 13 | 1880 | `rename_prompt_files_for_seo` | `from prompts.utils.seo import generate_seo_filename, generate_video_thumbnail_filename` | SEO utility |
| 14 | 1881 | `rename_prompt_files_for_seo` | `from prompts.services.b2_rename import B2RenameService` | B2 service |
| 15 | 2306 | `run_seo_pass2_review` | `from prompts.models import Prompt` | model (break circular) |
| 16 | 2341 | `run_seo_pass2_review` | `from prompts.constants import OPENAI_TIMEOUT` | constants |
| 17 | 2671 | `_apply_generation_result` | `from prompts.constants import get_image_cost` | constants helper |
| 18 | 2729 | `_run_generation_loop` | `from prompts.models import BulkGenerationJob` | model (break circular) |
| 19 | 2730 | `_run_generation_loop` | `from prompts.services.bulk_generation import BulkGenerationService` | service |
| 20 | 2731 | `_run_generation_loop` | `from prompts.services.image_providers import get_provider as _get_provider` | provider registry |
| 21 | 2906 | `_deduct_generation_credits` | `from prompts.models import GeneratorModel, UserCredit, CreditTransaction` | models (break circular) |
| 22 | 2955 | `process_bulk_generation_job` | `from prompts.models import BulkGenerationJob` | model (break circular) |
| 23 | 2956 | `process_bulk_generation_job` | `from prompts.services.image_providers import get_provider` | provider registry |
| 24 | 2969 | `process_bulk_generation_job` | `from prompts.services.bulk_generation import (decrypt_api_key, BulkGenerationService,)` | service (break circular — services.bulk_generation imports `async_task` from django_q which bootstraps `prompts.tasks`) |
| 25 | 3329 | `create_prompt_pages_from_job` | `from prompts.models import BulkGenerationJob, Prompt` | models (break circular) |
| 26 | 3330 | `create_prompt_pages_from_job` | `from prompts.services.bulk_generation import _sanitise_error_message` | service (circular reference documented in memory & class docstring at tasks.py:3330) |
| 27 | 3331 | `create_prompt_pages_from_job` | `from prompts.utils.source_credit import parse_source_credit` | utility |
| 28 | 3352 | `create_prompt_pages_from_job` | `from prompts.models import SubjectCategory, SubjectDescriptor` | models (could be consolidated with #25) |
| 29 | 3532 | `_ensure_unique_title` | `from prompts.models import Prompt` | model (break circular) |
| 30 | 3553 | `_generate_unique_slug` | `from prompts.models import Prompt` | model (break circular) |
| 31 | 3585 | `publish_prompt_pages_from_job` | `from prompts.models import BulkGenerationJob, Prompt, SubjectCategory, SubjectDescriptor` | models (break circular) |
| 32 | 3586 | `publish_prompt_pages_from_job` | `from prompts.services.bulk_generation import _sanitise_error_message` | service (circular) |
| 33 | 3587 | `publish_prompt_pages_from_job` | `from prompts.utils.source_credit import parse_source_credit` | utility |
| 34 | 3806 | `_fire_quota_alert_notification` | `from prompts.services.notifications import create_notification` | notifications service |

### Patterns observed

- **Models imported lazily everywhere** (17 of 34) — consistent
  with the project's established "break circular via in-
  function import" pattern
- **Notifications service imported lazily** in 4 places —
  matches the "non-blocking notification fire" pattern
- **`prompts.services.bulk_generation` is lazily imported** in
  #19, #24, #26, #32 — this is the circular that the docstring
  at tasks.py:3330 explicitly calls out
- **Constants imported lazily** in 4 places — unusual given
  that `from django.conf import settings` is top-level; likely
  historical and could be hoisted, but **168-E must NOT
  refactor these** (out of scope)
- **No in-function imports cross submodule boundaries the
  spec's hypothesis assigns differently** — the lazy imports
  are all to `prompts.models`, `prompts.services.*`,
  `prompts.utils.*`, `prompts.constants`. Zero references to
  "another tasks submodule" because everything currently lives
  in one file. Post-split, intra-tasks-package calls (e.g.,
  `publish_prompt_pages_from_job` calling `_apply_m2m_to_
  prompt`) can use direct Python imports between submodules
  without circular concerns (provided no cycles are introduced)

**168-E preservation requirement:** all 34 lazy imports move
verbatim with their containing functions. None should be
hoisted to module level as part of the split. If 168-E wants to
reduce them, that's a separate spec.

---

## Section 10 — Proposed domain grouping (verified against evidence)

### The spec's initial 8-domain hypothesis

The spec proposed:

1. `notifications.py` — bulk-gen + NSFW + quota alerts
2. `nsfw_moderation.py`
3. `ai_analysis.py` — vision + tag pipeline + AI job cache
4. `seo_pipeline.py` — SEO rename + Pass 2 review
5. `bulk_generation.py` — generation orchestration
6. `b2_storage.py` — B2 upload + SSRF guards
7. `prompt_pages.py` — create + publish
8. `placeholders.py` (or merged)

### Evidence-based validation

**Cross-function call graph (from Grep I, condensed):**

- `notifications` group: 4 functions (2 fire-bulk-gen-*, 1
  NSFW-notify, 1 quota-alert). Called by external domains
  (bulk_generation.py:#38, nsfw_moderation:#4). **Clean cluster.**
- `nsfw_moderation` group: 3 functions. `_record_` calls
  `_check_`; `_check_` calls `_fire_nsfw_repeat_offender_
  notification` (cross-domain call into `notifications`).
  **Clean cluster with one cross-domain edge.**
- `ai_analysis` group (candidate functions per §5): ~17
  functions including `_call_openai_vision` (called by 4 task
  functions across domains), `_validate_and_fix_tags` (called
  by 7 places including `publish_prompt_pages_from_job` in the
  `prompt_pages` domain via `_apply_m2m_to_prompt`). **Heavy
  shared use — cross-domain imports required.**
- `seo_pipeline` group: 4 functions. `run_seo_pass2_review`
  uses `_download_and_encode_image` from `ai_analysis`;
  `_build_pass2_prompt` references 4 tag-validation constants
  from `ai_analysis`; uses `_get_analysis_url` and
  `_sanitize_content`. **Heavy reliance on `ai_analysis`
  private helpers + constants — must import across submodule.**
- `bulk_generation` group: 6 functions. `_run_generation_loop`
  imports `BulkGenerationService` at function body (lazy),
  calls `_run_generation_with_retry`, `_apply_generation_result`,
  `_upload_generated_image_to_b2` (b2_storage),
  `_upload_source_image_to_b2` (b2_storage),
  `_download_source_image` (b2_storage). `process_bulk_
  generation_job` calls `_fire_bulk_gen_job_notification`
  (notifications), `_fire_quota_alert_notification`
  (notifications), `_run_generation_loop`, `_deduct_generation_
  credits`, `_get_platform_api_key`. **Strong internal
  cohesion; moderate cross-domain edges into b2_storage and
  notifications.**
- `b2_storage` group: 5 functions. `_get_b2_client` is called
  only internally. `_is_private_ip_host` is called by
  `_download_source_image`. Self-contained. **Cleanest
  cluster — no cross-domain calls outbound.**
- `prompt_pages` group: 5 functions. `create_prompt_pages_
  from_job` and `publish_prompt_pages_from_job` share
  structure (publish is the concurrent variant of create);
  both call `_apply_m2m_to_prompt`, `_ensure_unique_title`,
  `_generate_unique_slug`, `_call_openai_vision` (ai_analysis),
  `_fire_bulk_gen_publish_notification` (notifications),
  `parse_source_credit` (lazy import), and both queue
  `rename_prompt_files_for_seo` (seo_pipeline) via Django-Q
  (cross-domain string reference).

### Verified grouping recommendation

The spec's 8-domain hypothesis holds with these refinements:

**CONFIRMED as proposed:**
- `notifications` (4 fns)
- `nsfw_moderation` (4 fns — includes `run_nsfw_moderation`)
- `b2_storage` (5 fns)
- `bulk_generation` (6 fns)

**PROPOSED ADJUSTMENTS:**

1. **`placeholders` module is thin (2 functions: `test_task`,
   `placeholder_*`).** Consider merging `test_task` into a
   `diagnostics.py` submodule or keeping at package root for
   discoverability. The Django-Q shim still re-exports it
   either way. `placeholder_nsfw_moderation` + `placeholder_
   variant_generation` are effectively dead code (noted in
   their docstrings as "not yet implemented") — 168-E could
   consider a follow-up deletion spec, but for the split
   itself, leave them in a `placeholders.py` module.

2. **`ai_analysis` is the largest cluster (~17 fns, ~1,100
   LOC including the 253-LOC `_build_analysis_prompt` string
   literal).** Within it, the tag-validation constants cluster
   (L585–L767, ~180 lines of sets + `TAG_RULES_BLOCK`) is
   reused by `seo_pipeline` (via `_build_pass2_prompt` and
   `run_seo_pass2_review` → `_validate_and_fix_tags`). **Two
   options:**
   - **Option A (recommended):** keep constants in
     `ai_analysis` and have `seo_pipeline` import them. Matches
     "where the owner function lives" principle.
   - **Option B:** hoist into `tag_rules.py` submodule. Cleaner
     architecturally; matches the 168-D precedent of a
     `constants.py` submodule.

3. **`seo_pipeline` has the `_get_analysis_url` dependency
   from `ai_analysis`.** One helper function (`_get_analysis_
   url`) is only called by `run_seo_pass2_review`. Could
   reasonably move with it to `seo_pipeline` (it computes a
   URL from a Prompt; SEO is the only consumer). The spec's
   grouping left it in `ai_analysis` — both are defensible.
   Recommendation: move to `seo_pipeline` if the sole caller
   is there, else keep in `ai_analysis` if 168-E prefers
   co-locating URL-resolution helpers.

4. **`prompt_pages.py` has heavy cross-domain traffic.** Both
   create_/publish_ functions call into `ai_analysis`
   (`_call_openai_vision`, `_validate_and_fix_tags`),
   `notifications` (`_fire_bulk_gen_publish_notification`),
   and `seo_pipeline` (via Django-Q string ref to
   `rename_prompt_files_for_seo`). **This is expected** — these
   are the top-level orchestrator functions for publishing.
   **The risk:** if the shim is wrong or a re-export is missed,
   this domain fails first and loudest because it's the most
   integrated.

5. **`_fire_nsfw_repeat_offender_notification` assignment.**
   Spec grouping places it in `notifications`. Alternative:
   keep in `nsfw_moderation` since it's tightly coupled to the
   NSFW violation workflow (only called by `_check_nsfw_
   repeat_offender`). Either works. Recommendation: put all
   three `_fire_*_notification` helpers in `notifications` for
   symmetry, even though 168-E may find naming inconsistency
   between `_fire_nsfw_repeat_offender_notification` (NSFW-
   flavored name but in notifications) and the NSFW-specific
   helpers.

### Final proposed grouping for 168-E

| Submodule | Functions | LOC estimate |
|---|---|---|
| `notifications.py` | `_fire_bulk_gen_job_notification`, `_fire_bulk_gen_publish_notification`, `_fire_nsfw_repeat_offender_notification`, `_fire_quota_alert_notification` | ~110 |
| `nsfw_moderation.py` | `run_nsfw_moderation`, `_record_nsfw_violation`, `_check_nsfw_repeat_offender`, constants `NSFW_CACHE_TTL`, `NSFW_VIOLATION_THRESHOLD`, `NSFW_VIOLATION_WINDOW_DAYS` | ~120 |
| `ai_analysis.py` | `generate_ai_content` (deprecated stub), `_call_openai_vision`, `_call_openai_vision_tags_only`, `_validate_and_fix_tags`, `_is_quality_tag_response`, `_is_safe_image_url`, `_download_and_encode_image`, `_build_analysis_prompt`, `_parse_ai_response`, `_validate_ai_result`, `_update_prompt_with_ai_content`, `_sanitize_content`, `_generate_unique_slug_with_retry`, `_handle_ai_failure`, `_is_valid_uuid`, `update_ai_job_progress`, `get_ai_job_status`, `generate_ai_content_cached`, plus 13 tag-validation constants | ~1,100 |
| `seo_pipeline.py` | `rename_prompt_files_for_seo`, `_build_pass2_prompt`, `run_seo_pass2_review`, `queue_pass2_review`, `_get_analysis_url` (moved), `PASS2_SEO_SYSTEM_PROMPT` | ~515 |
| `bulk_generation.py` | `_run_generation_with_retry`, `_apply_generation_result`, `_run_generation_loop`, `_get_platform_api_key`, `_deduct_generation_credits`, `process_bulk_generation_job`, constant `MAX_CONCURRENT_IMAGE_REQUESTS` | ~520 |
| `b2_storage.py` | `_get_b2_client`, `_upload_generated_image_to_b2`, `_upload_source_image_to_b2`, `_is_private_ip_host`, `_download_source_image`, constant `MAX_IMAGE_SIZE` | ~180 |
| `prompt_pages.py` | `_apply_m2m_to_prompt`, `create_prompt_pages_from_job`, `_ensure_unique_title`, `_generate_unique_slug`, `publish_prompt_pages_from_job` | ~520 |
| `placeholders.py` | `test_task`, `placeholder_nsfw_moderation`, `placeholder_variant_generation` | ~80 |
| **`__init__.py` (shim)** | all imports + `__all__` re-exports | ~60 |

Total across submodules: ~3,205 LOC + overhead ≈ original 3,822
(residual goes to import lines, module docstrings, and header
comments per submodule).

**This grouping is a suggestion, not binding.** 168-E may
refine based on its own reading.

---

## Section 11 — 168-E blockers and risks

Severity-ranked. Each entry includes a concrete mitigation
outline.

| # | Risk area | Current state | Severity | 168-E mitigation plan |
|---|---|---|---|---|
| 1 | **Django-Q string-reference shim** | 7 unique function names registered as `async_task('prompts.tasks.X', ...)` across 13 call sites (6 internal self-calls + 7 external) | **HIGH** | `prompts/tasks/__init__.py` re-exports all 7 names. Post-split smoke test uses `importlib.import_module('prompts.tasks')` + `getattr(FUNC)` assertions for each name. Run both pre-push (dev) and post-push (after deploy). Failure mode is silent worker crash — so verification must be automated, not visual. |
| 2 | **Direct-import consumer API** | **41 distinct names** imported via `from prompts.tasks import X` across 17 consumer files (tests, management commands, views, admin). Breakdown: 12 public + 20 private helpers + 9 module-level constants. Surface resolved by enumerating every tuple import. | **HIGH** | Shim `__all__` re-exports all 41 names. Failure mode is `ImportError` at module-load — LOUD and caught immediately by CI. Still HIGH severity because missing even one breaks the test suite, and the underscore-prefixed helpers make PEP 8-based `__all__` auto-generation insufficient. **Build the list by hand from §8's consolidated contract.** A `test_shim_contract.py` asserting `hasattr` on each of the 41 names is recommended as the regression guard. |
| 3 | **DB-stored scheduled tasks** | 0 active `Schedule` rows in local dev DB | **LOW (current)** / **HIGH if non-zero at deploy** | Re-run `Schedule.objects.count()` on production DB immediately before 168-E deploy (via Heroku shell). If non-zero, audit each row's `func` column against the new shim contract. Today's value of 0 means zero risk. |
| 4 | **In-function lazy imports** | 34 instances, all preserving circular-import break patterns | **MEDIUM** | Move verbatim with containing function. No refactoring as part of 168-E. Post-split `makemigrations --dry-run` should produce "No changes detected" and `manage.py check` should stay clean. Any refactoring of these 34 lines is a separate spec. |
| 5 | **Cross-submodule dependencies** | Evidence shows `prompt_pages` depends on `ai_analysis`, `notifications`, and `seo_pipeline` (via Django-Q); `seo_pipeline` depends on `ai_analysis` constants. ~8–10 cross-submodule import edges needed | **MEDIUM** | Use direct Python imports between submodules (no circulars within `prompts/tasks/` package itself since all lazy imports are to external packages). Example: `prompts/tasks/seo_pipeline.py` has `from prompts.tasks.ai_analysis import _download_and_encode_image, _sanitize_content, _get_analysis_url, _parse_ai_response`. Document the dependency graph in the package `__init__.py` docstring. |
| 6 | **Complexity hotspots (6 `noqa: C901`)** | 6 functions flagged, 4 of which are ≥190 LOC; 2 are ≥220 LOC | **LOW (for split)** | Move verbatim — do NOT attempt complexity reduction during 168-E. The noqa markers survive the move. A separate follow-up spec can tackle simplification. Explicitly call out in 168-E's Scope Boundary. |
| 7 | **Module-level constants split** | 15 constants at module level; tag-validation cluster (~180 lines) used across `ai_analysis` + `seo_pipeline` + 1 imported by test suite | **MEDIUM** | Decide Option A (keep in owner submodule) vs Option B (extract to `tag_rules.py` / `constants.py`). Recommend Option A for this split — matches 168-D precedent when constants are tightly coupled to one owner function. If Option B chosen, the shim MUST re-export `DEMOGRAPHIC_TAGS` (already used by `test_validate_tags.py`). |
| 8 | **Worker dyno restart required** | Django-Q qcluster loads `prompts.tasks` at startup | **LOW (logistics)** | After `git push heroku main` completes and release-phase migrate runs, restart worker dyno: `heroku ps:restart worker`. Document in 168-E's post-push protocol. Without restart, the worker still holds the pre-split module reference and new task registrations would resolve to the old module state. |
| 9 | **Load-order sensitivity of `MAX_CONCURRENT_IMAGE_REQUESTS`** | Evaluated once at import time (line 46); documented as test-mocking gotcha in source comment | **MEDIUM** | Preserve exact semantics: the constant evaluates once at the submodule's first import. Test suite already mocks it via `prompts.tasks.MAX_CONCURRENT_IMAGE_REQUESTS` direct attribute patching (test_bulk_generation_tasks.py:1109, 1172). The shim must re-export the bound name, and the submodule that owns it (`bulk_generation.py`) must be imported before any test mock applies. |
| 10 | **`generate_ai_content` deprecated stub** | Line 314–325. Docstring says "DEPRECATED (N4-Cleanup)"; always returns error dict | **LOW (codebase hygiene)** | Keep in the split — no consumer depends on behavior, but defensive retention guards any stale queued task from the pre-cache era. Future spec can remove after operational confidence. |
| 11 | **`prompts.services.bulk_generation` ↔ `prompts.tasks` circular** | `services/bulk_generation.py:339` calls `async_task('prompts.tasks.process_bulk_generation_job', ...)` with string ref; `tasks.py:#24, #26, #32` imports from `services/bulk_generation.py` at function scope (lazy). Circular is broken by lazy imports | **MEDIUM (preservation)** | 168-E split must preserve this. `prompts/tasks/bulk_generation.py` must NOT import `prompts.services.bulk_generation` at module level; the 4 lazy imports (at current lines 2730, 2969, 3330, 3586 in source) must remain in-function. |
| 12 | **Test file update scope** | 14 test files + 7 management/view files import from `prompts.tasks` | **LOW** | Import path stays `prompts.tasks` — shim-based. Consumer files need zero changes. The test suite acts as the primary regression signal: if it passes, the shim contract is met. |
| 13 | **Migration side effects** | None — no model changes involved | **NONE** | 168-E should NOT create migrations. `makemigrations --dry-run` must return "No changes detected". If it doesn't, something is imported wrong (e.g., a model is accidentally being re-registered). |
| 14 | **Integration with future scheduled tasks** | Bulk job deletion (Section A) + detect_b2_orphans (Section B done) + admin notifications (Section C) all involve future scheduled tasks. If those add `Schedule.objects.create(...)` calls, they will create DB rows pointing to `prompts.tasks.X` paths | **LOW (future)** | Document in the 168-E completion report that any future scheduled-task work must resolve task paths via the post-split shim (no direct submodule paths like `prompts.tasks.seo_pipeline.rename_prompt_files_for_seo`). Enforce as a CC_SPEC_TEMPLATE rule. |

### Overall risk assessment

**Highest-risk vector:** Django-Q string references (#1). Silent
failure mode makes missed shim exports invisible until a task
type fires in production. Mitigation via automated importlib
assertion is cheap and highly effective.

**Secondary risk:** test suite coverage via direct imports (#2).
LOUD failure mode catches issues in CI, but the surface is
larger than 168-D.

**All other risks are bounded.** The 0-schedule count (#3),
absence of migrations (#13), and preserved lazy-import pattern
(#4, #11) eliminate most of the failure modes that were
theoretical concerns in the spec.

---

## Section 12 — Agent Ratings

Below is the template for the required 2-agent review. Both
scores must be ≥ 8.0; average must be ≥ 8.5. Agents run after
this report is saved; scores to be filled in by the executing
human/CC before commit.

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | 10.0/10 | All 4 evidence verifications pass cleanly: 3 function-line spot-checks exact, 3 Django-Q caller file:line citations verified, Grep H Schedule count==0 reproduced, zero code files modified. §7.4 shim contract and §8 direct-import surface grounded in verifiable grep output. | N/A (read-only) |
| @architect-review | 7.5/10 → **9.5/10** (re-verified after §8 fix) | Initial review: §8 final list claimed ~27 names but left 12 tuple-import names unresolved ("inspect file for exact list" placeholders). Fix applied inline: every tuple import resolved, §8 now lists 41 explicit names with per-name consumer citations, §1/§11#2/§14 all updated to match. Re-review: fix is complete and consistent; half-point deduction was minor table-prose staleness (resolved in this commit). | Yes — §8 resolved to 41 named entries + stale table text cleaned up |
| **Average** | **9.75/10** | | |

### Agent review scope (reiterated for the agents)

- **@code-reviewer**: evidence accuracy. Spot-verify 3 reported
  line numbers against actual `prompts/tasks.py` content;
  confirm every string-reference caller in §7.1 table is real
  (pick 3 rows, grep independently); confirm the Grep H
  Schedule count of 0 is reproducible; confirm no `.py`,
  `.html`, `.js`, `.css`, or migration file has been modified.
- **@architect-review**: analysis completeness. Does §7.4
  comprehensively cover all call sites? Would the 168-E shim
  design be obvious from this evidence? Is the 8-domain
  grouping's cross-function cohesion validated by the call
  graph data in §10? Are blockers/risks in §11 genuinely
  comprehensive — especially around scheduled tasks in the DB
  (quietest failure mode)?

---

## Section 13 — Commits

One commit expected:

```
docs: tasks.py import graph + Django-Q contract analysis (Session 168-E-prep)

[see CC_SPEC_168_E_PREP.md for full commit body template]

Files:
- docs/REPORT_168_E_PREP_TASKS_IMPORT_GRAPH.md (new)
```

---

## Section 14 — What to Work on Next

### 168-E: tasks.py split (last major refactor from 168-A audit)

This report satisfies **memory rule #8** for the 168-E spec
draft — it catalogues every function, constant, import
relationship, cross-function dependency, and Django-Q contract
point needed to design the `prompts/tasks/` package correctly.

**Evidence produced that 168-E can cite directly:**

- Function inventory with line ranges + LOC (§5)
- Module-level constant inventory with re-export requirements
  (§6)
- **Django-Q shim contract — 7 names** (§7.4)
- **Direct-import shim contract — 41 names** (§8 end)
- In-function lazy import map (§9) — preserve verbatim
- Verified 8-domain grouping (§10)
- 14 enumerated blockers with severity + mitigations (§11)

**Recommended 168-E spec structure:**

1. **Scope:** split `prompts/tasks.py` (3,822 lines) into a
   `prompts/tasks/` package with ~8 submodules + `__init__.py`
   shim. Zero behavioral changes. Zero complexity reduction.
2. **Shim contract (copy from this report §7.4 + §8):**
   explicit `__all__` list of 41 names (7 Django-Q entries +
   12 public + 20 private helpers + 9 constants). Consumer
   citation per name is listed in §8.
3. **Post-split verification:**
   - `python manage.py check` clean pre + post
   - `makemigrations --dry-run` → "No changes detected"
   - Full test suite passes (expect 1364 tests as of 168-F)
   - Automated importlib smoke test for 7 Django-Q entry points
4. **Post-push protocol:**
   - `heroku ps:restart worker` (worker dyno picks up new
     module layout)
   - Re-run `Schedule.objects.count()` on prod — must remain 0
   - Monitor qcluster logs for 24h for any
     `AttributeError: module 'prompts.tasks' has no attribute
     'X'` traces
5. **Risk acknowledgment:** cite §11's risk #1 and #2 as the
   primary concerns; note that #3 is currently zero-surface.

**Estimated size:** 168-E is larger than 168-D (models split,
1 commit, ~1,200 LOC relocated). tasks.py at 3,822 LOC is
~3× the scope of models.py. Consider whether 168-E should
split into 168-E-A (extract `notifications.py`, `b2_storage.py`,
`placeholders.py` — lowest-risk) and 168-E-B (extract
`ai_analysis.py`, `seo_pipeline.py`, `bulk_generation.py`,
`prompt_pages.py` — higher-risk). Or single-commit if CC
confidence is high enough post-prep.

### Follow-ups unlocked by 168-E

1. **Complexity reduction of 6 `noqa: C901` functions** —
   separate post-168-E spec track. The 4 functions over 190
   LOC are prime candidates.
2. **`placeholder_nsfw_moderation` + `placeholder_variant_
   generation` cleanup** — dead code confirmed (§5 footnote).
3. **Tag validation constant refactor** — optional: extract
   the ~180-line `tag_rules_*` block into a `tag_rules.py`
   submodule if shared usage between `ai_analysis` and
   `seo_pipeline` feels awkward after the split.
4. **168-E completion closes 168-A audit** — all 5 top-ranked
   refactors (style.css 168-C, models.py 168-D, admin.py 168-F,
   docs archive 168-B, tasks.py 168-E) shipped.

---

**END OF REPORT 168-E-prep**
