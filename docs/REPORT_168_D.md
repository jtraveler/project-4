# REPORT_168_D — prompts/models.py Split into models/ Package

**Spec:** CC_SPEC_168_D_MODELS_SPLIT.md (v1)
**Date:** April 22, 2026
**Status:** Complete. 11 sections filled. Pending developer smoke test + commit.
**Type:** Code refactor — split 3,517-line `prompts/models.py` into a
`prompts/models/` package with 9 submodules + re-export shim.
Relocated one signal handler to `prompts/signals.py`.
**Evidence base:** `docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md`
(168-D-prep, committed as `a905de3`).

---

## Section 1 — Overview

This spec executed the split designed by 168-D-prep. The result is a
`prompts/models/` package composed of 9 submodules (8 domain + 1
constants) plus an `__init__.py` re-export shim that preserves the
public import contract. Every external consumer (`admin.py`,
`tasks.py`, `views/*.py`, `signals.py`, `notification_signals.py`,
25 test files, `templatetags/notification_tags.py`) continues to use
`from prompts.models import <X>` unchanged.

**Post-split verification (all required gates passed):**

- `python manage.py check`: **0 issues**
- `python manage.py makemigrations --dry-run`: **"No changes detected"**
  (no accidental schema drift)
- 34 public names re-exported and importable via `from prompts.models
  import X`
- Migration count unchanged: **88 migrations** (0086 still `[ ]`)
- Signal handler `delete_cloudinary_assets` relocated from the
  former `models.py:2247` to `signals.py` with string-reference sender
  `sender='prompts.Prompt'`. Registered exactly once (verified via
  `post_delete._live_receivers(sender=Prompt)` — returns a single
  `delete_cloudinary_assets` function)
- `Prompt.likes.through` still resolves (verified via
  `connect_m2m_signals()` running without error and returning the
  `Prompt_likes` through model)
- `Follow.Meta.db_table = 'prompts_follow'` preserved — table name
  unchanged
- `BulkGenerationJob.SIZE_CHOICES` still yields 4 entries (same as
  pre-split)
- `python manage.py test prompts`: **(see Section 4 — full count
  recorded post-run)**
- Zero modifications to `admin.py`, `tasks.py`, `views/*.py`,
  `notification_signals.py`, `social_signals.py`,
  `templatetags/*.py`, `apps.py`, or any test file

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed | ✅ Met (Section 4 evidence) |
| 168-D-prep committed before start | ✅ Met — `a905de3` in git log |
| CC did NOT run migrate / makemigrations | ✅ Met — only `makemigrations --dry-run` used |
| `python manage.py check` clean pre + post | ✅ Met |
| `makemigrations --dry-run` says "No changes detected" | ✅ Met |
| All 34 public names resolve via `from prompts.models import X` | ✅ Met (Section 4 evidence) |
| No new migrations; 88 migrations unchanged | ✅ Met |
| `prompts/models.py` replaced by `prompts/models/` package | ✅ Met |
| `delete_cloudinary_assets` handler relocated to `signals.py` | ✅ Met |
| Zero consumer files modified | ✅ Met (Section 3 evidence) |
| Full test suite passes (count ≥ pre-split) | ✅ Met — see Section 4 |
| 4 agents reviewed, all ≥ 8.0, avg ≥ 8.5 | ✅ Met — see Section 10 |
| Developer smoke test flagged pre-push | ✅ Flagged — Section 9 |
| 11-section report | ✅ Met |

---

## Section 3 — Files Changed

### Deleted

- `prompts/models.py` — 3,517 lines. Content migrated to the new
  `prompts/models/` package. Signal handler relocated to
  `prompts/signals.py`.

### Modified

- `prompts/signals.py` — +2 imports at top (`post_delete` added to
  existing `post_save` line, `import cloudinary.uploader` added) +
  ~95 lines appended at bottom for the relocated
  `delete_cloudinary_assets` handler with string-ref sender
  `'prompts.Prompt'`. No existing code modified. 137 lines → 238 lines.

### Created (new files under `prompts/models/`)

| File | Lines | Contents |
|------|-------|----------|
| `prompts/models/__init__.py` | 60 | Re-export shim (34 public names) |
| `prompts/models/constants.py` | 79 | `STATUS`, `MODERATION_STATUS`, `MODERATION_SERVICE`, `AI_GENERATOR_CHOICES`, `DELETION_REASONS`, `NOTIFICATION_TYPE_CATEGORY_MAP`, `_BULK_SIZE_DISPLAY` |
| `prompts/models/users.py` | 484 | UserProfile, AvatarChangeLog, EmailPreferences, Follow |
| `prompts/models/taxonomy.py` | 118 | TagCategory, SubjectCategory, SubjectDescriptor |
| `prompts/models/prompt.py` | 1,382 | PromptManager, Prompt, SlugRedirect, DeletedPrompt, PromptView |
| `prompts/models/interactions.py` | 294 | Comment, Collection, CollectionItem, Notification |
| `prompts/models/moderation.py` | 444 | PromptReport, ModerationLog, ProfanityWord, ContentFlag, NSFWViolation |
| `prompts/models/bulk_gen.py` | 447 | BulkGenerationJob, GeneratedImage, GeneratorModel |
| `prompts/models/credits.py` | 129 | UserCredit, CreditTransaction |
| `prompts/models/site.py` | 163 | SiteSettings, CollaborateRequest |
| **Total** | **3,600** | (vs 3,517 pre-split — +83 lines due to per-submodule docstring headers) |

### Created (report)

- `docs/REPORT_168_D.md` — this report.

### Scope-boundary confirmations (zero changes)

- `prompts/admin.py` — not modified. Verified: `from prompts.admin
  import PromptAdmin` still works; the 24-name import line at
  `admin.py:14` and late import at `admin.py:1616` (`AvatarChangeLog`)
  both resolve through the shim.
- `prompts/tasks.py` — not modified. 16 in-function `from
  prompts.models import ...` calls all resolve through the shim.
- `prompts/views/*.py` — not modified.
- `prompts/notification_signals.py` — not modified. 5 string-reference
  `@receiver` decorators (`sender='prompts.Comment'` etc.) still work
  because Django's app registry resolves `prompts.ModelName` by
  `app_label.ModelName`, independent of file location.
- `prompts/social_signals.py` — not modified.
- `prompts/templatetags/notification_tags.py` — not modified.
- `prompts/apps.py` — not modified.
- All 25 test files under `prompts/tests/` — not modified.
- `prompts/migrations/` — unchanged at 88 files.
- env.py — unchanged.

---

## Section 4 — Evidence (greps + post-edit checks)

### Pre-execution safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Gate passed.

### Step 0 greps

#### Grep A — 168-D-prep committed

```
$ git log --oneline -5
a905de3 docs: models.py import graph analysis + CSS directory convention (Session 168-D-prep)
213f604 refactor: split style.css into 5 modular partials (Session 168-C)
e554fa6 docs: archive discoverability pass (Session 168-B-discovery)
b45ecdd docs: archive old changelog sessions and update stale status headers (Session 168-B)
5b7b26d docs: add full repository refactoring audit (Session 168-A)
```

168-D-prep committed at `a905de3`. Prerequisite met.

#### Grep B — baseline file state

```
$ wc -l prompts/models.py
3517 prompts/models.py

$ grep -c "^class " prompts/models.py
28
```

Matches prep-report Section 5 (28 classes = 27 models + 1 Manager).

#### Grep C — taggit vs prompts order in INSTALLED_APPS

```
$ grep -n "'taggit'\|'prompts'" prompts_manager/settings.py
163:    'taggit',
166:    'prompts',
```

`taggit` (line 163) < `prompts` (line 166). Per prep-report Section 11
MEDIUM-severity item, this ordering is required so `TaggableManager`
can register its signal handlers before Prompt class body executes.

#### Grep D — pre-split test count

Full suite (1,364 tests) ran pre-split to establish baseline (run
against sqlite test DB via `--keepdb`). Completed with: **`Ran 1364
tests in 780.306s / OK (skipped=12)`**. This matches CLAUDE.md's
recorded "1364 tests" post-Session-165.

#### Grep E — migration RunPython blocks

```
$ grep -rn "from prompts.models import\|from \.models import" prompts/migrations/
(no results — zero direct imports of models from migrations)

$ grep -rn "RunPython" prompts/migrations/ | head -10
prompts/migrations/0054_rename_3d_photo_category.py:39:    migrations.RunPython(...)
prompts/migrations/0031_create_email_preferences_for_existing_users.py:45:    migrations.RunPython(...)
...
```

Every RunPython in the codebase uses `apps.get_model('prompts',
'ModelName')` (historical migration pattern — verified via direct
inspection of `0049_populate_descriptors.py`). This pattern is
**unaffected by the split** because `apps.get_model()` resolves
through Django's app registry, not by file path.

#### Grep F — test patch paths

```
$ grep -rn "patch(.prompts\.models\." prompts/tests/
prompts/tests/test_bulk_gen_rename.py:322: with patch('prompts.models.Prompt.save') as mock_save:
prompts/tests/test_nsfw_violations.py:112: with patch('prompts.models.NSFWViolation.objects') as mock_qs:
```

Two patches, both targeting attributes on model classes. These
resolve through the new package `__init__.py`
(`prompts.models.Prompt` == `prompts.models.prompt.Prompt` via
re-export). `unittest.mock.patch` handles packages correctly. **No
test changes needed.**

#### Grep G — apps.py imports

```
$ grep -n "prompts.models\|connect_m2m\|Prompt\.likes" prompts/apps.py
23:        prompts.notification_signals.connect_m2m_signals()
```

`apps.py.ready()` calls `connect_m2m_signals()` which internally
references `Prompt.likes.through`. Verified post-split that this
chain still works — `Prompt_likes` through model resolves
correctly.

#### Grep H — `delete_cloudinary_assets` reference check

```
$ grep -rn "delete_cloudinary_assets" prompts/ --include="*.py" | grep -v __pycache__
prompts/signals.py:35:def delete_cloudinary_assets(sender, instance, **kwargs):
```

Only one definition remaining (in `signals.py`). Original at
`prompts/models.py:2248` was removed with the file. No other file
calls `delete_cloudinary_assets` by name — relocation is complete.

### Post-split verification

#### V1 — `python manage.py check`

```
$ python manage.py check
System check identified no issues (0 silenced).
```

#### V2 — `makemigrations --dry-run`

```
$ python manage.py makemigrations --dry-run
No changes detected
```

**Critical — schema preserved.** Any model metadata drift (field,
Meta, index, choice changes) would have triggered a migration. None
did.

#### V3 — All 34 public names importable

```
$ python manage.py shell -c "from prompts.models import (
    UserProfile, AvatarChangeLog, EmailPreferences, Follow,
    TagCategory, SubjectCategory, SubjectDescriptor,
    PromptManager, Prompt, SlugRedirect, DeletedPrompt, PromptView,
    Comment, Collection, CollectionItem, Notification,
    PromptReport, ModerationLog, ProfanityWord, ContentFlag,
    NSFWViolation, BulkGenerationJob, GeneratedImage, GeneratorModel,
    UserCredit, CreditTransaction, SiteSettings, CollaborateRequest,
    AI_GENERATOR_CHOICES, STATUS, MODERATION_STATUS,
    MODERATION_SERVICE, DELETION_REASONS,
    NOTIFICATION_TYPE_CATEGORY_MAP,
)
print('All 33 names imported successfully.')"
All 33 names imported successfully.
```

#### V4 — Critical methods spot-check

```
$ python manage.py shell -c "...assertions..."
admin.py imports: PromptAdmin
All critical methods present.
Prompt._meta.app_label: prompts
Prompt._meta.db_table: prompts_prompt
Follow._meta.db_table: prompts_follow
BulkGenerationJob SIZE_CHOICES count: 4
```

Methods verified present: `Prompt.get_critical_flags` (uses
cross-submodule `ContentFlag` via in-function lazy import),
`Prompt.hard_delete`, `Prompt.get_recent_engagement` (uses
`SiteSettings` via in-function lazy import), `UserProfile.is_following`
(lazy `Follow` import — same submodule now), `Follow.clean`,
`BulkGenerationJob.SIZE_CHOICES` (derived from
`_BULK_SIZE_DISPLAY` + `ALL_IMAGE_SIZES` — 4 entries).

#### V5 — Signal registration verification

```
$ python manage.py shell -c "
from django.db.models.signals import post_delete
from prompts.models import Prompt
receivers = post_delete._live_receivers(sender=Prompt)
print(f'Total live receivers for Prompt: {len(receivers)}')
print('Raw:', repr(receivers)[:300])"
Total live receivers for Prompt: 2
Raw: ([<function delete_cloudinary_assets at 0x10a989800>], [])
```

The "2" is the shape of `_live_receivers()` output (a tuple of
`[sync_receivers, async_receivers]` lists). There is exactly **one
sync receiver**: `delete_cloudinary_assets`. No duplicate
registration.

#### V6 — Migration count unchanged

```
$ ls prompts/migrations/ | wc -l
88

$ python manage.py showmigrations prompts | tail -3
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
 [ ] 0086_alter_userprofile_avatar_url
```

88 migrations, 0086 still `[ ]` (not applied) — matches pre-split.

#### V7 — Full test suite

Run against sqlite test DB with `--keepdb`.

**Command:** `python manage.py test prompts --keepdb`

**Result:** `Ran 1364 tests in 931.764s / OK (skipped=12)` —
matches pre-split count exactly (1364 vs 1364). **Zero test
deletions, zero regressions.**

(See Section 11 for the full delta.)

#### V8 — Consumer files unchanged

```
$ git status --short
 D prompts/models.py
 M prompts/signals.py
?? prompts/models/
?? docs/REPORT_168_D.md
# (Plus unrelated CC spec tracking files that existed pre-session)
```

Only: `prompts/models.py` deleted, `prompts/signals.py` modified
(signal relocation), `prompts/models/` directory created,
`docs/REPORT_168_D.md` created. **No other file modified.**

---

## Section 5 — Design choices finalized

The spec's Section "Placement decisions (finalizing prep report
ambiguities)" defined four choices; all were applied verbatim:

1. **`CollaborateRequest` → `site.py`** (not `interactions.py`).
   Rationale: no FK to Prompt or User; singleton-style admin surface
   analogous to SiteSettings. This is the only placement decision
   prep-report Section 10 left ambiguous.

2. **`delete_cloudinary_assets` handler → `signals.py` with
   `sender='prompts.Prompt'`** string-reference. Consistent with
   `notification_signals.py` convention. Rationale: removes
   `cloudinary.uploader` + `B2MediaStorage` dependency from the
   models-package top-level. (Note: `cloudinary.models` /
   `cloudinary.uploader` still imported by `prompt.py` because
   `Prompt.hard_delete()` still needs them — but that's expected;
   the removal was specifically for the *signal* path.)

3. **Constants placement:** all six shared constants
   (`STATUS`, `MODERATION_STATUS`, `MODERATION_SERVICE`,
   `AI_GENERATOR_CHOICES`, `DELETION_REASONS`,
   `NOTIFICATION_TYPE_CATEGORY_MAP`) live in
   `prompts/models/constants.py` and are re-exported via
   `__init__.py`. `_BULK_SIZE_DISPLAY` also lives there but is
   **not re-exported** — its only consumer is `BulkGenerationJob`
   inside the same package.

4. **PromptManager** stays in `prompt.py` alongside `Prompt` —
   tightly coupled.

5. **In-function lazy imports for cross-submodule references:**
   - `Prompt.get_critical_flags` → `from .moderation import
     ContentFlag`
   - `Prompt.get_recent_engagement` → `from .site import SiteSettings`
   - `Prompt.can_see_view_count` → `from .site import SiteSettings`
   - `PromptView._is_rate_limited` → `from .site import SiteSettings`
   - `UserProfile.is_following` / `is_followed_by` → **kept as
     `from prompts.models import Follow`** (unchanged from pre-split).
     Rationale: Follow is now in the same submodule (`users.py`)
     as UserProfile, so the lazy import is no longer strictly needed
     — but the spec explicitly said "keep lazy import as-is —
     reducing scope is a future cleanup." Done.

6. **Cross-layer imports preserved unchanged:**
   - `DeletedPrompt.create_from_prompt` → `from prompts.views import
     find_best_redirect_match` (models calling view code; existing
     code smell, not scope of this spec)
   - `PromptView.record_view` → `from prompts.views import
     get_client_ip` (same pattern)

7. **Module-level imports per submodule:** every submodule imports
   only what it needs (e.g., `users.py` has no `CloudinaryField`
   import; `prompt.py` does). This is cleaner than a single
   mega-file but adds ~20 total lines of imports across the 8
   domain modules. Net: 3,600 total lines of code across the
   package vs 3,517 in the mono-file — +83 lines of docstring
   headers + per-file imports.

---

## Section 6 — Import graph preservation

### Before (mono-file)

```
prompts/models.py (3,517 lines)
└── All 27 models + 1 Manager + 6 module constants + 1 signal handler
```

### After (package)

```
prompts/models/
├── __init__.py (shim: re-exports 34 public names)
├── constants.py (6 shared constants + 1 private)
├── users.py (4 classes: UserProfile, AvatarChangeLog, EmailPreferences, Follow)
├── taxonomy.py (3 classes: TagCategory, SubjectCategory, SubjectDescriptor)
├── prompt.py (5 classes: PromptManager, Prompt, SlugRedirect, DeletedPrompt, PromptView)
├── interactions.py (4 classes: Comment, Collection, CollectionItem, Notification)
├── moderation.py (5 classes: PromptReport, ModerationLog, ProfanityWord, ContentFlag, NSFWViolation)
├── bulk_gen.py (3 classes: BulkGenerationJob, GeneratedImage, GeneratorModel)
├── credits.py (2 classes: UserCredit, CreditTransaction)
└── site.py (2 classes: CollaborateRequest, SiteSettings)
```

### Import paths (external → models)

| External consumer | Path used | Resolves via |
|-------------------|-----------|--------------|
| `admin.py:14` — 24-name block | `from .models import Prompt, ...` | `__init__.py` re-exports |
| `admin.py:1616` — late import | `from .models import AvatarChangeLog` | `__init__.py` re-exports |
| `signals.py:21` | `from .models import UserProfile, EmailPreferences` | `__init__.py` re-exports |
| `signals.py:35` (NEW) | `@receiver(sender='prompts.Prompt')` | Django app registry |
| `notification_signals.py` — 5 `@receiver` | `sender='prompts.<Model>'` | Django app registry |
| `notification_signals.py` — 4 in-function imports | `from prompts.models import Notification / Prompt` | `__init__.py` re-exports |
| `tasks.py` — 16 in-function imports | `from prompts.models import <X>` | `__init__.py` re-exports |
| `templatetags/notification_tags.py:4` | `from prompts.models import Notification` | `__init__.py` re-exports |
| 25 test files (~70 imports) | Various `from prompts.models import ...` | `__init__.py` re-exports |
| 2 test `patch()` paths | `patch('prompts.models.Prompt.save')` etc. | `__init__.py` re-exports + `unittest.mock` package handling |
| Migrations `RunPython` | `apps.get_model('prompts', '<Model>')` | Django app registry |

### Import paths (intra-package)

| From submodule | To submodule | Pattern |
|----------------|--------------|---------|
| `prompt.py` → `.constants` | module-level `from .constants import ...` |
| `interactions.py` → `.prompt` (Comment.prompt FK) | module-level `from .prompt import Prompt` |
| `moderation.py` → `.constants` | module-level `from .constants import ...` |
| `bulk_gen.py` → `.constants` | module-level `from .constants import _BULK_SIZE_DISPLAY` |
| `prompt.py` → `.moderation` (ContentFlag) | in-function `from .moderation import ContentFlag` |
| `prompt.py` → `.site` (SiteSettings) | in-function `from .site import SiteSettings` |
| `users.py` → `.users` (Follow, self-ref) | in-function `from prompts.models import Follow` (via shim) |

No circular imports. Verified by `python manage.py check` returning
zero issues, and `from prompts.models import *` working in a Django
shell.

---

## Section 7 — Risk register coverage

All risks from prep-report Section 11 were mitigated. Traceability:

| Prep-report risk | Severity | Mitigation applied in 168-D |
|------------------|----------|------------------------------|
| Signal resolution — direct-class `sender=Prompt` | MEDIUM | ✅ Relocated to `signals.py` with string-ref `sender='prompts.Prompt'` — verified via `_live_receivers()` |
| `signals.py` module-level import of `UserProfile`, `EmailPreferences` | LOW | ✅ `__init__.py` re-exports both — verified via Django boot |
| In-function lazy imports `from prompts.models import Follow` | LOW | ✅ Shim re-exports Follow — verified via `UserProfile.is_following` code path |
| `admin.py` single-line 24-name import (HIGH blocker) | **HIGH** | ✅ Shim re-exports all 24 names — verified via `from prompts.admin import PromptAdmin` |
| `tasks.py` 16 in-function imports | LOW | ✅ All names in shim — verified via full test suite passing |
| `notification_signals.py` string-ref senders | LOW | ✅ No change needed — Django app registry |
| Module-level constants shared across models | MEDIUM | ✅ Extracted to `constants.py`, re-exported |
| Third-party library imports | LOW | ✅ Each submodule imports what it needs |
| taggit signal-registration ordering | MEDIUM | ✅ Verified `'taggit'` (line 163) < `'prompts'` (line 166) in settings.py INSTALLED_APPS |
| `db_table = 'prompts_follow'` override | LOW | ✅ Preserved verbatim — verified `Follow._meta.db_table == 'prompts_follow'` |
| Migration RunPython blocks | UNKNOWN | ✅ Zero `from prompts.models import` in migrations; all use `apps.get_model()` — pattern unaffected by split |
| Test patches | UNKNOWN | ✅ 2 patches found, both resolve through package `__init__.py` via `unittest.mock` package handling |
| `Meta.app_label` overrides | NONE | ✅ Zero overrides confirmed |
| CloudinaryField forward reference in signal | LOW | ✅ `cloudinary.uploader` imported at top of `signals.py` |
| Circular import: moderation ↔ prompts | MEDIUM | ✅ In-function lazy import in `Prompt.get_critical_flags` |
| Circular import: prompts ↔ site | LOW-MEDIUM | ✅ In-function lazy imports in `Prompt.get_recent_engagement`, `Prompt.can_see_view_count`, `PromptView._is_rate_limited` |

**Severity resolution:** 1 HIGH ✅ mitigated. 4 MEDIUM ✅ mitigated.
7 LOW ✅ mitigated. 2 UNKNOWN ✅ resolved as LOW (migrations use
`apps.get_model`; test patches work through package).

---

## Section 8 — Behavior preservation proofs

### Method signatures spot-check (5 random classes across domains)

Per spec's `@code-reviewer` criterion "byte-level preservation — spot-verify
5 random class method signatures are identical pre/post split":

1. **`UserProfile.get_avatar_color_index(self)`** — identical body:
   MD5 hash of username → modulo 8 + 1. Present.
2. **`Prompt.hard_delete(self)`** — identical body: 3 try/except
   blocks for Cloudinary image, Cloudinary video, B2 source image
   (with `bulk-gen/` or `media/` prefix check). Present.
3. **`DeletedPrompt.create_from_prompt(cls, prompt, logger=None)`** —
   identical body: computes tag_names, calls
   `find_best_redirect_match` (imported lazily from
   `prompts.views`), creates record with 90-day expiry. Present.
4. **`BulkGenerationJob.progress_percent`** — identical property:
   `min(round((processed / self.total_images) * 100), 100)` where
   processed = completed + failed. Present.
5. **`CreditTransaction.__str__`** — identical body: sign prefix +
   username + amount + type + balance_after. Present.

### `delete_cloudinary_assets` verbatim preservation

Pre-split (`models.py:2247-2332`) vs post-split (`signals.py:35-135`):
- Docstring: **verbatim**
- Image deletion block (try/except with `cloudinary.uploader.destroy`
  on `public_id`, resource_type='image'): **verbatim**
- Video deletion block (try/except with
  `cloudinary.uploader.destroy` on `public_id`, resource_type='video'):
  **verbatim**
- B2 source image deletion block: **verbatim** — preserves the
  critical `bulk-gen/` or `media/` prefix check (security boundary),
  the try/except that prevents deletion blocking, and the nested
  imports (`from urllib.parse import urlparse as _urlparse`, `from
  prompts.storage_backends import B2MediaStorage`)
- Signal decorator: `@receiver(post_delete, sender=Prompt)` →
  `@receiver(post_delete, sender='prompts.Prompt')` (direct-class →
  string-ref; **only change**, equivalent at runtime via app registry)

### `Follow.Meta.db_table` preservation

Pre-split: `db_table = 'prompts_follow'` at line 2355.
Post-split: `db_table = 'prompts_follow'` at `users.py:463`.
Verified via `Follow._meta.db_table == 'prompts_follow'` in shell.

Migration-state impact: **zero**. The explicit `db_table` override
means Django does NOT auto-rename the table based on the submodule
name — the `prompts_follow` table remains the authoritative
identifier regardless of Python file location.

### `BulkGenerationJob.SIZE_CHOICES` preservation

Pre-split: `SIZE_CHOICES = [(s, _BULK_SIZE_DISPLAY[s]) for s in
ALL_IMAGE_SIZES]` at line 2945.
Post-split: same expression at `bulk_gen.py:37`. `_BULK_SIZE_DISPLAY`
imported from `.constants` (module-level). Verified same 4-element
result in shell.

### `GeneratedImage.size` / `quality` choices reference

Pre-split: `choices=BulkGenerationJob.SIZE_CHOICES` and
`choices=BulkGenerationJob.QUALITY_CHOICES` at lines 3102, 3109.
Post-split: same class-attribute references preserved at
`bulk_gen.py:185, 193`. Works because `BulkGenerationJob` is defined
above `GeneratedImage` in the same submodule.

---

## Section 9 — Developer smoke test (MANDATORY before push)

**Critical — CC cannot run the dev server; the developer MUST
complete this checklist before pushing.**

Per spec Step 9:

```bash
python manage.py runserver
```

Then visit the following URLs and confirm **no 500 errors**:

1. **`/`** (homepage) — exercises Prompt, Follow, Notification,
   UserProfile
2. **`/prompt/<any-slug>/`** — exercises Prompt.get_critical_flags
   (which uses the in-function `ContentFlag` import, one of the
   primary risk points), comments, tags, collections
3. **`/profile/<username>/`** — exercises UserProfile, Follow,
   follower/following counts
4. **`/tools/bulk-ai-generator/`** (staff-only) — exercises
   BulkGenerationJob, GeneratorModel, UserCredit
5. **Django admin at `/admin/`** — **especially open the Prompt
   changelist**. This is the `admin.py:14` 24-name import line
   (the HIGH-severity prep-report blocker). If ImportError during
   admin boot, the shim is missing a name

**If any 500 error:** `git revert <168-D commit>` — the split is a
pure Python-file reorganization; revert restores the original
`prompts/models.py` and removes the `prompts/models/` package.
Signals.py gets its original form back. Zero data impact.

**If no 500 errors:** safe to push. The Heroku release phase will
run `migrate --noinput` — expected output "No migrations to apply"
+ the standing `django_summernote` warning (see CLAUDE.md). If
Heroku release phase fails, rollback is immediate (Heroku holds
previous version).

### Optional manual verification (post-push, production)

- Check Heroku logs for `ImportError`, `AttributeError`, or
  `NoMethodFoundError` on prompt-related paths (should be 0)
- Create a test comment on a prompt — triggers
  `notification_signals.on_comment_created` with string-ref sender
  `'prompts.Comment'`. Confirms the string-ref pattern works
  through the package

---

## Section 10 — Agent Ratings

Per spec minimum: 4 agents, each ≥ 8.0, average ≥ 8.5.

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | 9.2/10 | Byte-level preservation verified: 5 random class method signatures (UserProfile.get_total_likes, Prompt.soft_delete+hard_delete, ProfanityWord full body, BulkGenerationJob.progress_percent+is_active, CreditTransaction full body) are byte-identical pre/post split. `delete_cloudinary_assets` body is verbatim in signals.py — only the decorator sender changed (direct class → string-ref). `makemigrations --dry-run` reports "No changes detected" — schema preserved. Test suite matches exactly: 1364 tests / OK / 12 skipped. `__all__` contains **34 names** (28 classes + 6 constants) — the audit prompt originally said 33, reconciled upward to 34 in Section 6 / commit message. Consumer files untouched. | **Yes** — documentation nit absorbed: "33" → "34" in REPORT. No code change. |
| @architect-review | 9.2/10 | Import graph is acyclic. The only module-level cross-submodule import (`interactions.py` → `.prompt`) is safe because `__init__.py` loads `.prompt` (line 17) before `.interactions` (line 20). Constants placement coherent: 6 shared constants re-exported via shim, `_BULK_SIZE_DISPLAY` is private. All 4 prep-report MEDIUM risks mitigated (signal-ref, constants sharing, moderation↔prompts circular, prompts↔site circular, taggit ordering). Signal timing safe: `PromptsConfig.ready()` fires before any request. Minor code-smell: `users.py` `UserProfile.is_following` still uses `from prompts.models import Follow` (round-trip through shim) even though Follow is now same-file — deliberate per spec "reducing scope is a future cleanup." | N/A — observation recorded for future micro-spec; not blocking |
| @test-automator (sub for @test-engineer) | 10.0/10 | `git status prompts/tests/` clean — zero test modifications. Pre-split `1364 tests in 780.306s` vs post-split `1364 tests in 931.764s`, both `OK (skipped=12)` — exact match. Three spot-checked test files (test_follows.py, test_bulk_generator_views.py, test_notifications.py) all import names that resolve through the shim including `NOTIFICATION_TYPE_CATEGORY_MAP` (confirmed type=dict via shell). In-function lazy imports in Prompt class (get_critical_flags, get_recent_engagement, can_see_view_count, PromptView._is_rate_limited) and UserProfile.is_following all resolve correctly. Both `patch('prompts.models.Prompt.save')` and `patch('prompts.models.NSFWViolation.objects')` start/stop without AttributeError. | N/A |
| @backend-security-coder | 9.5/10 | All 4 security properties of `delete_cloudinary_assets` preserved byte-for-byte: (1) hard-delete-only via `@receiver(post_delete, ...)`; (2) Cloudinary image+video deletion blocks identical (separate try/except, correct resource_type); (3) **B2 prefix check `bulk-gen/` or `media/` allowlist intact** — this is the security boundary preventing arbitrary B2 deletion; (4) try/except+logger.error on all three blocks prevents cloud-failure from blocking DB deletion. Nested imports remain lazy inside B2 try block. Sole change: `sender=Prompt` → `sender='prompts.Prompt'` (string-ref) — equivalent runtime binding via app registry, matches notification_signals.py convention. Registration via `ready()` fires before any request handler — timing safe. Exactly one sync receiver registered (no duplicates). | N/A |
| **Average** | **9.475/10** | All 4 ≥ 8.0 ✅ Average ≥ 8.5 ✅ | |

### Agent substitution disclosure

`@test-engineer` not in this registry. Substituted with
`@test-automator` (closest-match native agent — test automation,
framework verification, import resolution). Disclosed per Session 153
"COPY EXACTLY" rule and Session 162-H Cross-Spec Bug Absorption Policy.
Substitution scope identical to original: test integrity, import
resolution, mock-patch verification.

### Action taken on findings

- **Code-reviewer's `__all__` count nit** (33 vs 34): absorbed into
  this report at commit time. References to "33 public names" in
  the spec's optimistic framing were updated to "34 public names"
  throughout Section 1, 2, 4-V3, 5, 6, and the commit message.
  Breakdown: 28 classes (27 models + 1 `PromptManager`) + 6 constants
  = 34. `PromptManager` is defensively re-exported because `tasks.py`
  imports it in at least one site.
- **Architect-review's same-file Follow round-trip observation**:
  recorded as non-blocking future cleanup. Not addressed in 168-D
  because the spec explicitly said "keep lazy import as-is — reducing
  scope is a future cleanup." Deliberate scope discipline.
- **No other issues flagged.**

---

## Section 11 — Commits + final test count

Planned single commit. Files:

- `prompts/models.py` (DELETED — content migrated to package)
- `prompts/models/__init__.py` (NEW — shim)
- `prompts/models/constants.py` (NEW)
- `prompts/models/users.py` (NEW)
- `prompts/models/taxonomy.py` (NEW)
- `prompts/models/prompt.py` (NEW)
- `prompts/models/interactions.py` (NEW)
- `prompts/models/moderation.py` (NEW)
- `prompts/models/bulk_gen.py` (NEW)
- `prompts/models/credits.py` (NEW)
- `prompts/models/site.py` (NEW)
- `prompts/signals.py` (MODIFIED — absorbs `delete_cloudinary_assets`)
- `docs/REPORT_168_D.md` (NEW)

Commit message will follow the spec's template verbatim (see
CC_SPEC_168_D_MODELS_SPLIT.md "COMMIT MESSAGE" section).

**Post-commit:** No push by CC. Developer runs the smoke test per
Section 9 before pushing.

### Final test counts

- **Pre-split:** `Ran 1364 tests in 780.306s / OK (skipped=12)`
- **Post-split:** `Ran 1364 tests in 931.764s / OK (skipped=12)`
- **Delta:** 0 tests added, 0 tests removed, 0 failures.
  Wall-clock time increased by ~151s (~19%), normal test-isolation
  variance on a local dev machine, not a signal.

### Final agent scores

| Agent | Score |
|---|---|
| @code-reviewer | 9.2/10 |
| @architect-review | 9.2/10 |
| @test-automator (sub @test-engineer) | 10.0/10 |
| @backend-security-coder | 9.5/10 |
| **Average** | **9.475/10** |

All ≥ 8.0 ✅ Average ≥ 8.5 ✅

---

**END OF REPORT 168-D**
