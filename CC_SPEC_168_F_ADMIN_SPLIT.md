# CC_SPEC_168_F_ADMIN_SPLIT.md
# Session 168-F — `prompts/admin.py` Split into Admin Package

**Spec ID:** 168-F
**Version:** v1
**Date:** April 22, 2026
**Status:** Ready for implementation
**Priority:** P2 — ranked #4 in 168-A audit
**Type:** Code refactor — split 2,459-line admin.py into a
`prompts/admin/` package with 11 submodules
**Dependencies:** 168-catchup committed AND pushed (Grep A)

---

## ⛔ STOP — MANDATORY REQUIREMENTS

**Work will be REJECTED if ANY of the following are not met:**

1. **env.py safety gate** run; outputs recorded in Section 4
2. **CC does NOT run `migrate`** or `makemigrations`. This is
   pure Python-file reorganization. Zero schema changes
3. **Minimum 3 agents** reviewed. Every ≥ 8.0. Average ≥ 8.5
4. **168-catchup must be committed AND pushed before start** (Grep A)
5. **Zero new migrations.** `makemigrations --dry-run` MUST say
   "No changes detected" post-split
6. **`python manage.py check` clean pre AND post.** Any check
   failure = REJECTED
7. **Django admin MUST fully load post-split.** This is a
   stronger requirement than for 168-D (models split) because
   admin classes register via decorators at import time — if a
   submodule fails to import, `@admin.register(Model)` doesn't
   fire, the model silently disappears from the admin UI, and
   the bug only surfaces when someone tries to use it. Step 7
   verification is mandatory
8. **Test suite MUST pass.** Run `python manage.py test prompts`
   pre-split AND post-split. Test count equal or higher. Every
   pre-split passing test must still pass
9. **Module-level side effects preserved.** The current
   `admin.py` has 3 side-effect statements:
   - `admin.site.unregister(Tag)` (line ~1479, wrapped in
     try/except)
   - `admin.site.unregister(User)` (line ~2351)
   - `admin.site.index_template = 'admin/custom_index.html'`
     (line ~2459)
   All three must continue to execute post-split at the correct
   time (after all admin registrations fire)
10. **Mandatory 11-section report** at `docs/REPORT_168_F.md`

---

## 🚨 SAFETY GATE

```bash
grep -n "DATABASE_URL" env.py
python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
```

Expected: `DATABASE_URL: NOT SET`. Record in Section 4.

---

## ⛔ COMMANDS

### DO run:
- ✅ `python manage.py check`
- ✅ `python manage.py test prompts` (pre AND post split)
- ✅ `python manage.py makemigrations --dry-run` (expected: "No
  changes detected")
- ✅ Python verification: `python -c "from django.contrib import
  admin; from prompts.admin import ...; print(admin.site._registry)"`
- ✅ `grep`, `cat`, `head`, `tail`, `wc -l`, `find`, `awk`
- ✅ File creation
- ✅ `git rm prompts/admin.py` at the end

### DO NOT run:
- ❌ `migrate` or `makemigrations` (without `--dry-run`)
- ❌ Auto-formatters (`black`, `isort`, `ruff format`) — would
  reorder imports and inflate diffs. `ruff check` read-only is
  fine
- ❌ Any modification to:
  - `prompts/models/` package
  - `prompts/signals.py`, `notification_signals.py`,
    `social_signals.py`
  - `prompts/views/*.py`
  - `prompts/tasks.py`
  - `prompts/tests/*.py`
  - `prompts/templates/`
  - `prompts/migrations/`
  - `prompts/apps.py`
  - Any `.html`, `.css`, `.js` file
- ❌ Modifying any admin class body (no refactoring, no
  deduplication, no cleanup — only relocation)

---

## 📋 OVERVIEW

### Why this spec exists

`prompts/admin.py` is 2,459 lines — ranked #4 in the 168-A
audit. It contains 28 admin classes (plus inlines, a form,
and a custom view), dominated by `PromptAdmin` at 952 LOC.

**Evidence base (pre-read by Claude.ai):**
- 28 top-level class definitions + 1 standalone function
  (`trash_dashboard`)
- 3 module-level side-effect statements (admin.site mutations)
- Imports from `prompts.models` resolve through the 168-D shim
  (24-name line at `admin.py:14` + late AvatarChangeLog import
  at line 1616)
- No string-reference registrations — all use
  `@admin.register(Model)` decorators, which fire at import time
- Self-contained — no other code imports from `admin.py`
  (verified: Grep E in Step 0)

**Comparison to 168-D models split:**
- Lower FK complexity — admin classes don't have ForeignKey
  fields; cross-class references are via `Meta.model` and
  inline relationships, resolved at registration time
- HIGHER registration-timing risk — admin decorators fire at
  import time; `__init__.py` import order matters for the
  `admin.site.unregister()` side effects

### Design: `admin/` package with import-triggered registration

**Key insight:** admin.py doesn't need a "re-export shim" like
models/ did. Django finds admin classes via side effects
(`@admin.register` decorators), not via attribute lookups.
The `__init__.py` pattern is different:

```python
# prompts/admin/__init__.py
"""
prompts.admin package.

Imports submodules to trigger @admin.register decorators + module-
level side effects (Tag/User unregister, index_template).
Order matters — taxonomy_admin imports AFTER the Tag unregister.
"""

# 1. Forms + inlines (no side effects, needed by admin modules)
from . import forms
from . import inlines

# 2. Taxonomy (includes Tag unregister + 3 admin classes)
from . import taxonomy_admin

# 3. Domain admin modules (each fires @admin.register at import)
from . import prompt_admin
from . import moderation_admin
from . import users_admin            # includes CustomUserAdmin (User unregister)
from . import interactions_admin
from . import bulk_gen_admin
from . import site_admin
from . import credits_admin

# 4. Custom views
from . import custom_views

# 5. Final site-wide customization
from django.contrib import admin as _admin
_admin.site.index_template = 'admin/custom_index.html'
```

**Why this works:**
- Every `from . import X` triggers X's module body to execute
- Each submodule's `@admin.register(Model)` decorators fire as
  the module loads
- `admin.site.unregister(Tag)` runs inside `taxonomy_admin.py`
  (before its own TagCategory/Subject admin classes register)
- `admin.site.unregister(User)` runs inside `users_admin.py`
  (before CustomUserAdmin registers)
- `admin.site.index_template` assignment runs last, after all
  submodules have loaded

### Package structure (verified against actual admin.py)

```
prompts/
├── admin/                        # NEW — was admin.py
│   ├── __init__.py               # Import orchestration + index_template
│   ├── forms.py                  # PromptAdminForm + RESERVED_SLUGS
│   ├── inlines.py                # SlugRedirectInline, ContentFlagInline,
│   │                               CollectionItemInline, GeneratedImageInline
│   ├── prompt_admin.py           # PromptAdmin, PromptViewAdmin, SlugRedirectAdmin
│   ├── moderation_admin.py       # ModerationLogAdmin, ContentFlagAdmin,
│   │                               ProfanityWordAdmin, PromptReportAdmin,
│   │                               NSFWViolationAdmin
│   ├── users_admin.py            # UserProfileAdmin, AvatarChangeLogAdmin,
│   │                               EmailPreferencesAdmin, CustomUserAdmin
│   │                               (+ User unregister)
│   ├── interactions_admin.py     # CommentAdmin, CollectionAdmin,
│   │                               CollectionItemAdmin, NotificationAdmin
│   ├── bulk_gen_admin.py         # BulkGenerationJobAdmin, GeneratorModelAdmin
│   ├── taxonomy_admin.py         # Tag unregister + TagCategoryAdmin,
│   │                               SubjectCategoryAdmin, SubjectDescriptorAdmin
│   ├── site_admin.py             # SiteSettingsAdmin, CollaborateRequestAdmin
│   ├── credits_admin.py          # UserCreditAdmin, CreditTransactionAdmin
│   └── custom_views.py           # trash_dashboard function
```

**Submodule sizes (estimated):**
- `prompt_admin.py` ~1,100 LOC (largest — includes the 952-LOC
  PromptAdmin)
- `moderation_admin.py` ~540 LOC
- `users_admin.py` ~275 LOC
- `interactions_admin.py` ~125 LOC
- `bulk_gen_admin.py` ~85 LOC
- `taxonomy_admin.py` ~85 LOC
- `site_admin.py` ~55 LOC
- `credits_admin.py` ~31 LOC
- `forms.py` ~85 LOC (PromptAdminForm + RESERVED_SLUGS)
- `inlines.py` ~50 LOC (4 inlines)
- `custom_views.py` ~70 LOC

Total: ~2,500 LOC vs 2,459 pre-split (+ ~40 lines of per-file
docstring headers and imports, same pattern as 168-D).

### Domain placement decisions

1. **PromptAdminForm + RESERVED_SLUGS → `forms.py`.** Separate
   from prompt_admin because the form is a standalone concept
   and RESERVED_SLUGS is a constant used by the form's
   `clean_slug()` method.

2. **All inlines → `inlines.py`.** Co-locates the 4 inline
   classes (SlugRedirectInline, ContentFlagInline,
   CollectionItemInline, GeneratedImageInline). Each is small
   (8-14 LOC). Keeps admin-class files focused on their
   ModelAdmin subclasses. Admin classes import inlines via
   `from .inlines import X`.

3. **trash_dashboard function → `custom_views.py`.** It's a
   standalone `@staff_member_required` view, not an admin
   class. Separate file clarifies its role and sets up for
   future custom admin views.

4. **Late `from .models import AvatarChangeLog` (line 1616) →
   top-of-file import in `users_admin.py`.** The late import
   pattern was a pre-existing quirk. Moving AvatarChangeLogAdmin
   to users_admin.py lets us put AvatarChangeLog in the same
   top-level import block as UserProfile, EmailPreferences —
   no more late imports.

5. **`CustomUserAdmin` → `users_admin.py`.** It's a user-domain
   admin class. Its `admin.site.unregister(User)` call must
   happen BEFORE `@admin.register(User)` registers CustomUserAdmin
   — keeps naturally within the same module.

6. **Late `from django.contrib.auth.admin import UserAdmin`
   (line 2349) → top-of-file import in `users_admin.py`.**
   Same reasoning as #4.

7. **Late imports for `staff_member_required` and `render`
   (lines 2116-2117) → top-of-file imports in
   `custom_views.py`.**

### Scope boundary — NOT in this spec

- Refactoring any admin class body (no method extraction, no
  deduplication, no cleanup — relocation only)
- Modifying field lists, list_displays, filters, fieldsets
- Adding new admin views or methods
- Changing admin URL patterns (get_urls() overrides preserved
  verbatim)
- Type hint additions
- Docstring rewrites

---

## 🎯 OBJECTIVES

- ✅ env.py safety gate verified
- ✅ 168-catchup committed AND pushed (Grep A)
- ✅ `python manage.py check` clean pre + post
- ✅ `python manage.py test prompts` passes pre + post
- ✅ `makemigrations --dry-run` → "No changes detected"
- ✅ `prompts/admin.py` replaced by `prompts/admin/` package
- ✅ All 28 admin classes registered in `django.contrib.admin.site._registry`
  post-split (spot-verify via Python)
- ✅ trash_dashboard accessible at its URL
- ✅ Module-level side effects preserved (Tag unregister, User
  unregister, index_template)
- ✅ Zero modifications to consumer files (models, views, tasks,
  templates, tests, signals, apps.py, migrations)
- ✅ 3 agents reviewed, all ≥ 8.0, avg ≥ 8.5
- ✅ Developer admin smoke-test completed pre-push (Step 8)

---

## 🔎 STEP 0 — MANDATORY RESEARCH GREPS

### Grep A — 168-catchup committed and pushed

```bash
git log --oneline -5
git log --oneline origin/main -3
```

Expected: commit `70f6222` (168-catchup followup) or newer on
origin/main. If not pushed, STOP.

### Grep B — Baseline admin.py state

```bash
wc -l prompts/admin.py
grep -c "^class " prompts/admin.py
grep -c "@admin.register" prompts/admin.py
```

Expected: 2,459 lines, 28 classes, 24 `@admin.register`
decorators. If values differ by >50 lines / >2 classes, STOP.

### Grep C — Admin class inventory

```bash
grep -n "^class \|^@admin.register" prompts/admin.py
```

Record the full line-range for each class. This is the data
for Section 3 of the report.

### Grep D — Module-level side effects

```bash
grep -n "admin.site.unregister\|admin.site.index_template\|admin.site.register" \
    prompts/admin.py
```

Expected:
- Line ~1479: `admin.site.unregister(Tag)` (wrapped in try/except)
- Line ~2351: `admin.site.unregister(User)`
- Line ~2459: `admin.site.index_template = 'admin/custom_index.html'`

Document EXACT line numbers for preservation tracking.

### Grep E — External consumers of admin.py

```bash
grep -rn "from prompts.admin import\|from \.admin import\|import prompts.admin" \
    --include="*.py" prompts/ 2>/dev/null | grep -v __pycache__
```

Expected: **zero hits** (admin.py is self-contained — no other
module imports from it). If any hits: the spec must preserve
those import paths (likely via `__init__.py` re-exports).

### Grep F — Baseline test count

```bash
python manage.py test prompts 2>&1 | tail -5
```

Record: "Ran N tests in X.XXXs" — N must equal post-split N.

Expected: ~1364 tests (per 168-D baseline).

### Grep G — apps.py admin reference

```bash
grep -n "admin" prompts/apps.py
```

Expected: apps.py does NOT import anything from `prompts.admin`.
Django discovers admin modules via `admin.autodiscover()`. The
default `AdminConfig` runs autodiscover at server startup. Our
`AppConfig.ready()` does not import admin.

If apps.py imports admin: flag in Section 4 — spec must handle.

### Grep H — templatetags / signals admin references

```bash
grep -rn "from prompts.admin\|from prompts import admin" \
    prompts/templatetags/ prompts/signals.py \
    prompts/notification_signals.py prompts/social_signals.py \
    2>/dev/null | grep -v __pycache__
```

Expected: zero hits.

### Grep I — Admin-registered model count baseline

```bash
python manage.py shell -c "
from django.contrib import admin
print('Models in admin.site._registry:', len(admin.site._registry))
print('---')
for model, ma in sorted(admin.site._registry.items(), key=lambda x: x[0].__name__):
    print(f'  {model.__name__} -> {ma.__class__.__name__}')
"
```

**Record this output verbatim.** Post-split, this count MUST be
identical AND every Model → Admin mapping MUST match. This is
the forensic proof that all decorators fired correctly.

---

## 🔧 SOLUTION

### Step 1 — Verify Step 0 results

All 9 greps must pass. If any inconsistency, STOP.

### Step 2 — Create the package skeleton

```bash
# Create directory
mkdir -p prompts/admin

# Create empty placeholder files (will be populated in Steps 3-7)
for m in __init__ forms inlines prompt_admin moderation_admin \
         users_admin interactions_admin bulk_gen_admin \
         taxonomy_admin site_admin credits_admin custom_views; do
    touch "prompts/admin/${m}.py"
done

# DO NOT delete prompts/admin.py yet — still source of truth
```

### Step 3 — Extract `forms.py`

Move:
- `RESERVED_SLUGS` constant (lines 20-26)
- `PromptAdminForm` class (lines 29-109)

Include at top of file:
```python
"""
Admin forms for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
import re

from django import forms

from prompts.models import Prompt
from prompts.utils.related import W_TAG


RESERVED_SLUGS = {
    # ... paste verbatim from original
}


class PromptAdminForm(forms.ModelForm):
    # ... paste verbatim from original
```

**Imports needed** (determined from class body):
- `import re` (for regex slug validation)
- `from django import forms`
- `from prompts.models import Prompt`
- `from prompts.utils.related import W_TAG`
- `from dal_select2_taggit.widgets import TaggitSelect2` — keep
  as an in-method import (original pattern on line 60, inside
  `__init__`)

### Step 4 — Extract `inlines.py`

Move:
- `SlugRedirectInline` (lines 112-119)
- `ContentFlagInline` (lines 1093-1103)
- `CollectionItemInline` (lines 1998-2006)
- `GeneratedImageInline` (lines 2290-2303)

Include at top:
```python
"""
Admin inline classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
from django.contrib import admin

from prompts.models import (
    SlugRedirect, ContentFlag, CollectionItem, GeneratedImage,
)


class SlugRedirectInline(admin.TabularInline):
    # ... paste verbatim

class ContentFlagInline(admin.TabularInline):
    # ... paste verbatim

class CollectionItemInline(admin.TabularInline):
    # ... paste verbatim

class GeneratedImageInline(admin.TabularInline):
    # ... paste verbatim
```

### Step 5 — Extract each admin submodule

For each of the 8 admin submodules (prompt_admin,
moderation_admin, users_admin, interactions_admin,
bulk_gen_admin, taxonomy_admin, site_admin, credits_admin):

**Pattern:**
```python
"""
<Domain> admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
from django.contrib import admin
from django.urls import reverse, path                    # only if used
from django.utils.html import format_html                # only if used
from django_summernote.admin import SummernoteModelAdmin # only prompt_admin

from prompts.models import (
    # <only the models this submodule registers>
)

# Imports from sibling admin submodules (if needed)
from .forms import PromptAdminForm     # prompt_admin only
from .inlines import SlugRedirectInline, ContentFlagInline, ...
                                       # each module imports only what it uses


@admin.register(<Model>)
class <Model>Admin(admin.ModelAdmin):
    # ... paste verbatim from original
```

**Per-submodule class contents** (verified against Grep C):

**`prompt_admin.py`:** PromptAdmin, PromptViewAdmin, SlugRedirectAdmin
- Imports: `PromptAdminForm` from `.forms`, `SlugRedirectInline`
  from `.inlines`
- `PromptAdmin.get_urls()` override includes a module-level
  function `move_up_view` / `move_down_view` etc. — preserve all
  methods and the URL pattern config verbatim

**`moderation_admin.py`:** ModerationLogAdmin, ContentFlagAdmin,
ProfanityWordAdmin, PromptReportAdmin, NSFWViolationAdmin
- Imports: `ContentFlagInline` from `.inlines`
- `ProfanityWordAdmin` has its own `get_urls()` override for
  `bulk-import/` — preserve

**`users_admin.py`:** UserProfileAdmin, AvatarChangeLogAdmin,
EmailPreferencesAdmin, CustomUserAdmin
- Imports at top:
  ```python
  from django.contrib.auth.models import User
  from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
  from prompts.models import (
      UserProfile, AvatarChangeLog, EmailPreferences,
  )
  ```
- **CRITICAL: the `admin.site.unregister(User)` statement must
  appear BEFORE `@admin.register(User) class CustomUserAdmin`**.
  Place it immediately above the CustomUserAdmin decorator line.

**`interactions_admin.py`:** CommentAdmin, CollectionAdmin,
CollectionItemAdmin, NotificationAdmin
- Imports: `CollectionItemInline` from `.inlines`

**`bulk_gen_admin.py`:** BulkGenerationJobAdmin, GeneratorModelAdmin
- Imports: `GeneratedImageInline` from `.inlines`

**`taxonomy_admin.py`:** TagCategoryAdmin, SubjectCategoryAdmin,
SubjectDescriptorAdmin
- Imports at top:
  ```python
  from django.contrib import admin
  from taggit.models import Tag
  from prompts.models import TagCategory, SubjectCategory, SubjectDescriptor
  ```
- **CRITICAL: Include the Tag unregister block BEFORE the
  TagCategoryAdmin registration:**
  ```python
  # Unregister default Tag admin if it exists
  try:
      admin.site.unregister(Tag)
  except admin.sites.NotRegistered:
      pass


  @admin.register(TagCategory)
  class TagCategoryAdmin(admin.ModelAdmin):
      # ...
  ```

**`site_admin.py`:** SiteSettingsAdmin, CollaborateRequestAdmin

**`credits_admin.py`:** UserCreditAdmin, CreditTransactionAdmin

### Step 6 — Extract `custom_views.py`

Move `trash_dashboard` function (lines 2119-2185):

```python
"""
Custom admin views for the prompts app.

Extracted from prompts/admin.py in Session 168-F.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.sites import site as admin_site
from django.shortcuts import render


@staff_member_required
def trash_dashboard(request):
    # ... paste verbatim from original
```

**Note the late import pattern:** original `trash_dashboard`
uses `from django.contrib.admin.sites import site as admin_site`
inside the function body (line 2170). Keep that as-is — it's
intentional to avoid importing at module load time.

**Important — check for URL routing:** the original `admin.py`
does NOT have a `urls.py` registration for trash_dashboard
(verified via Grep Extra below). Check if `prompts/urls.py`
references it:

```bash
grep -rn "trash_dashboard" --include="*.py" | grep -v __pycache__
```

If `prompts/urls.py` imports it from `prompts.admin`, update
the import path in urls.py to `from prompts.admin.custom_views
import trash_dashboard`.

**If urls.py imports from `prompts.admin` at module level (not
via a package-relative path):** CC may need to add a re-export
to `prompts/admin/__init__.py`:
```python
from .custom_views import trash_dashboard  # backward compat
```

Document the decision and any urls.py changes explicitly in
Section 4.

### Step 7 — Write the `__init__.py` orchestration

Create `prompts/admin/__init__.py`:

```python
"""
prompts.admin package.

Session 168-F split the previous 2,459-line prompts/admin.py
into this package. Django discovers admin classes via
@admin.register() decorators, which fire at import time.
Importing each submodule triggers its registrations.

Import order matters:
1. forms + inlines (no side effects) — imported first so later
   submodules can import from them
2. taxonomy_admin — contains admin.site.unregister(Tag) which
   must run before any taxonomy admin classes register
3. All other admin submodules (each fires @admin.register as
   they load; users_admin contains admin.site.unregister(User)
   internally before CustomUserAdmin registers)
4. custom_views — trash_dashboard is a standalone view, not an
   admin class
5. admin.site.index_template — set last, after all
   registrations fire (not strictly required, but tidy)
"""

# 1. Dependencies (no side effects)
from . import forms        # noqa: F401
from . import inlines      # noqa: F401

# 2. Taxonomy (unregisters default Tag admin before its own classes register)
from . import taxonomy_admin  # noqa: F401

# 3. Domain admin modules (each fires @admin.register on import)
from . import prompt_admin     # noqa: F401
from . import moderation_admin # noqa: F401
from . import users_admin      # noqa: F401 (unregisters User)
from . import interactions_admin  # noqa: F401
from . import bulk_gen_admin   # noqa: F401
from . import site_admin       # noqa: F401
from . import credits_admin    # noqa: F401

# 4. Custom views
from . import custom_views  # noqa: F401

# 5. Site-wide admin customization (last, after all registrations)
from django.contrib import admin as _admin
_admin.site.index_template = 'admin/custom_index.html'

# 6. Backward-compat re-exports if anything external imports from prompts.admin
# (per Grep E, nothing external does — but defensive exposure of PromptAdminForm
# is cheap and protects against untested shell scripts / management commands)
from .forms import PromptAdminForm, RESERVED_SLUGS  # noqa: F401
from .custom_views import trash_dashboard  # noqa: F401
```

**`# noqa: F401`** suppresses "imported but unused" lint
warnings — the imports ARE needed (for side effects), but
linters don't know that.

### Step 8 — Delete `prompts/admin.py` and verify

```bash
# Once all 11 submodule files are populated:
rm prompts/admin.py

# Verify Django still loads
python manage.py check

# Verify no schema drift
python manage.py makemigrations --dry-run
# MUST print: "No changes detected"

# Verify admin registrations — should match Grep I baseline EXACTLY
python manage.py shell -c "
from django.contrib import admin
print('Models in admin.site._registry:', len(admin.site._registry))
for model, ma in sorted(admin.site._registry.items(), key=lambda x: x[0].__name__):
    print(f'  {model.__name__} -> {ma.__class__.__name__}')
"
# Compare output against Grep I baseline line-for-line.
# If any mismatch: STOP and investigate before committing.

# Verify forms + inlines still importable (at least the ones
# used externally — should be none, but defensive)
python manage.py shell -c "
from prompts.admin import PromptAdminForm, RESERVED_SLUGS, trash_dashboard
print('Backward-compat imports OK')
"

# Test suite
python manage.py test prompts 2>&1 | tail -5
# Expected: same count as Grep F baseline, 0 failures

# File state
ls -la prompts/admin/
wc -l prompts/admin/*.py

# Scope discipline
git status --short
# Expected:
#   D prompts/admin.py
#   ?? prompts/admin/
#   ?? docs/REPORT_168_F.md
#   (nothing else)
```

### Step 9 — Developer smoke-test (Step 8 of spec — CC CANNOT do this)

**Django admin smoke-test, mandatory before push:**

```bash
python manage.py runserver
```

Open `http://localhost:8000/admin/` and verify:

1. **Admin index page loads** with the custom template (confirms
   `index_template` assignment worked)
2. **Every model section present:** Prompts, Comments,
   Collections, Users, Profiles, Tag Categories, Subject
   Categories, Moderation Logs, etc. If anything is missing,
   a submodule's `@admin.register` didn't fire
3. **Click into "Prompts" changelist** — the 952-LOC PromptAdmin
   works. Exercise:
   - Sort/filter controls render
   - Try editing a prompt — `PromptAdminForm.clean_slug()`
     validation works
   - Tag autocomplete widget works (TaggitSelect2)
4. **Click into "Profanity Words"** — ProfanityWordAdmin has its
   own `get_urls()` override for `bulk-import/`; verify the
   page loads
5. **Click into "Users"** — CustomUserAdmin registered (confirms
   `admin.site.unregister(User)` + re-register worked)
6. **Click into "Tag Categories"** — confirms taxonomy_admin's
   `admin.site.unregister(Tag)` ran (default Tag admin should be
   gone from the Taggit section; TagCategory shows instead)
7. **Trash dashboard:** navigate to `/admin/trash-dashboard/`
   (or whatever URL pattern the repo uses). Should render.

If any page fails or is missing: `git revert <168-F commit>`
and investigate. Pure Python reorganization — zero data risk.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] env.py safety gate passed
- [ ] 168-catchup committed + pushed
- [ ] No migrate, no makemigrations (except `--dry-run`)
- [ ] 11 submodule files created under `prompts/admin/`
- [ ] All 28 admin classes + 4 inlines + form + constant +
      trash_dashboard present in submodules
- [ ] Original `prompts/admin.py` removed
- [ ] Module-level side effects preserved:
  - [ ] `admin.site.unregister(Tag)` in `taxonomy_admin.py`
        before TagCategoryAdmin
  - [ ] `admin.site.unregister(User)` in `users_admin.py`
        before CustomUserAdmin
  - [ ] `admin.site.index_template` in `__init__.py` step 5
- [ ] `python manage.py check` clean
- [ ] `makemigrations --dry-run` → "No changes detected"
- [ ] `admin.site._registry` count + mapping matches Grep I
      baseline EXACTLY
- [ ] Full test suite passes (count ≥ pre-split)
- [ ] `trash_dashboard` importable + URL routing intact
- [ ] Zero consumer-file changes
- [ ] 11-section report drafted

---

## 🤖 REQUIRED AGENTS — Minimum 3

Every agent ≥ 8.0. Average ≥ 8.5.

| Agent | Review scope |
|---|---|
| `@code-reviewer` | **Byte-level preservation** — spot-verify 5 random admin-class method signatures and 3 field lists (list_display, fieldsets) are identical pre/post split. Confirm `PromptAdmin.get_urls()` override is pasted verbatim with all 4 custom URL patterns preserved. Confirm `ProfanityWordAdmin.get_urls()` bulk-import route preserved. Confirm module-level side-effect statements (Tag unregister, User unregister, index_template) are present in the correct submodules. Confirm `makemigrations --dry-run` → "No changes detected". Confirm zero consumer-file changes. Confirm admin registry count matches Grep I baseline. |
| `@architect-review` | **Registration-timing correctness** — verify `__init__.py` import order is correct. Specifically: `taxonomy_admin` imports BEFORE any other module that might use Tag; `users_admin` contains the `admin.site.unregister(User)` BEFORE `@admin.register(User)`; `admin.site.index_template` assignment happens AFTER all submodule imports. Flag any risk that a submodule could be imported twice (would double-register admin classes — Django raises `AlreadyRegistered`). Flag any circular-import risk between submodules (e.g., forms → inlines → forms). |
| `@test-automator` (sub for @test-engineer) | **Admin integration** — run the full prompts test suite pre + post and confirm same count + same pass rate. Spot-check: do tests that exercise admin views (search in `prompts/tests/` for `/admin/`, `admin_site`, `AdminSite`, or `changelist_view`) still pass? If any tests import from `prompts.admin`, do they still work via the backward-compat re-exports in `__init__.py`? |

### All 3 agents MUST also verify

- [ ] `python manage.py check` clean pre AND post
- [ ] `makemigrations --dry-run` reports "No changes detected"
- [ ] `admin.site._registry` count matches baseline
- [ ] 88 migrations unchanged
- [ ] No consumer files modified

### Exact response table

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | X.X/10 | [finding] | Yes/No/N/A |
| @architect-review | X.X/10 | [finding] | Yes/No/N/A |
| @test-automator | X.X/10 | [finding] | Yes/No/N/A |
| **Average** | **X.X/10** | | |

### Agent substitution

If `@test-engineer` not in registry, substitute with
`@test-automator` (pattern established in 168-D, 10/10 score).
Disclose explicitly.

---

## 🧪 TESTING

### Automated (CC runs — every one MUST pass)

```bash
python manage.py check
python manage.py makemigrations --dry-run   # "No changes detected"
python manage.py test prompts               # ≥ pre-split count
# Plus Grep I comparison post-split
```

### Mandatory developer smoke-test (pre-push)

Per Step 9: open `/admin/` and verify all admin pages load
without error. See Step 9 for the 7-item checklist.

### Production verification (post-push)

1. Heroku release phase: "No migrations to apply" + standing
   django_summernote warning
2. Visit production `/admin/` and click into 2-3 changelists
3. Check Heroku logs for `AlreadyRegistered`, `ImportError`, or
   any admin-related exception (should be 0)

### Rollback

Pure Python-file reorganization. `git revert <168-F commit>`
restores the original `prompts/admin.py` and removes the
`prompts/admin/` package. No data loss.

---

## 🚨 CRITICAL REMINDERS

1. **env.py safety gate MANDATORY**
2. **168-catchup must be committed + pushed before start**
3. **Zero new migrations** — `makemigrations --dry-run` MUST
   say "No changes detected"
4. **Zero consumer-file changes** — models, views, tasks,
   signals, templates, tests, apps.py all untouched
5. **Module-level side effects preserved** — Tag unregister,
   User unregister, index_template
6. **`__init__.py` import order matters** — taxonomy BEFORE
   other admins that might use Tag; users_admin contains its
   own User unregister; index_template LAST
7. **`admin.site._registry` post-split MUST match Grep I baseline
   exactly** — same count, same Model → AdminClass mapping
8. **Admin decorators fire at import time** — if a submodule
   fails to import silently, its model disappears from admin
   UI. Step 9 smoke-test catches this
9. **Developer smoke-test MANDATORY pre-push** — CC cannot run
   the dev server
10. **Missing agent ratings table = REJECTED**
11. **3 agents minimum**

---

## ✅ PRE-COMMIT CHECK

- [ ] All PRE-AGENT SELF-CHECK items ticked
- [ ] All 3 agents ≥ 8.0, avg ≥ 8.5
- [ ] Agent ratings table present
- [ ] `docs/REPORT_168_F.md` with all 11 sections
- [ ] Section 9 flags developer smoke-test as MANDATORY
- [ ] git status shows only:
      D: prompts/admin.py
      ??: prompts/admin/
      ??: docs/REPORT_168_F.md
      Nothing else
- [ ] Agent substitutions disclosed

---

## 📝 COMMIT MESSAGE

```
refactor: split prompts/admin.py into admin/ package (Session 168-F)

Fourth code refactor from the 168-A audit. Reduces the
2,459-line prompts/admin.py to a `prompts/admin/` package
with 11 submodules organized by domain.

Package structure:
- admin/__init__.py          — import orchestration + index_template
- admin/forms.py             — PromptAdminForm + RESERVED_SLUGS
- admin/inlines.py           — 4 inline classes (Slug, ContentFlag,
                                CollectionItem, GeneratedImage)
- admin/prompt_admin.py      — PromptAdmin (952 LOC), PromptViewAdmin,
                                SlugRedirectAdmin
- admin/moderation_admin.py  — ModerationLog, ContentFlag,
                                ProfanityWord, PromptReport,
                                NSFWViolation admins
- admin/users_admin.py       — UserProfile, AvatarChangeLog,
                                EmailPreferences, Custom User admins
                                (+ User unregister)
- admin/interactions_admin.py — Comment, Collection, CollectionItem,
                                 Notification admins
- admin/bulk_gen_admin.py    — BulkGenerationJob, GeneratorModel admins
- admin/taxonomy_admin.py    — TagCategory, SubjectCategory,
                                SubjectDescriptor admins (+ Tag
                                unregister)
- admin/site_admin.py        — SiteSettings, CollaborateRequest admins
- admin/credits_admin.py     — UserCredit, CreditTransaction admins
- admin/custom_views.py      — trash_dashboard standalone view

Django discovers admin classes via @admin.register decorators
that fire at module import time. The `__init__.py` imports each
submodule in an order that preserves the module-level side
effects: taxonomy_admin (Tag unregister) loads before
TagCategory registers; users_admin internally unregisters User
before CustomUserAdmin; index_template is set after all admin
classes are registered.

Verified post-split:
- `python manage.py check`: 0 issues
- `makemigrations --dry-run`: "No changes detected"
- Full test suite: same count as pre-split, 0 failures
- admin.site._registry: same count + same Model→Admin mapping
  as pre-split baseline (forensic verification in report)
- Zero consumer files modified (models, views, tasks,
  signals, templates, tests, apps.py, migrations, templatetags)

Git history note: git blame on the new submodule files will
start from this commit. For pre-split history, consult
prompts/admin.py in any commit before this one.

Developer admin smoke-test pending before push — see
REPORT_168_F.md Section 9 for the 7-item verification list.

Agents: 3 reviewed (@code-reviewer, @architect-review,
@test-automator — sub for @test-engineer), all >= 8.0,
avg X.XX/10.

Files:
- prompts/admin.py (DELETED — content migrated to package)
- prompts/admin/ (NEW package — 12 files)
- docs/REPORT_168_F.md (new completion report)
```

---

**END OF SPEC 168-F**
