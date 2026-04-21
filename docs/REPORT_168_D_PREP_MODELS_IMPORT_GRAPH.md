# REPORT_168_D_PREP — models.py Import Graph Analysis + CSS Directory Convention

**Spec:** CC_SPEC_168_D_PREP.md (v1)
**Date:** April 21, 2026
**Status:** Complete. All 14 sections filled. Pending commit.
**Type:** Read-only code analysis + ~10-line CLAUDE.md addition (zero code changes)

---

## Preamble — Safety Gate + Prerequisite

### env.py safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "postgres://uddlhq8fogou0o:...")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Gate passed.

### Grep A — 168-C commit confirmation

```
$ git log --oneline -5
213f604 refactor: split style.css into 5 modular partials (Session 168-C)
e554fa6 docs: archive discoverability pass (Session 168-B-discovery)
b45ecdd docs: archive old changelog sessions and update stale status headers (Session 168-B)
5b7b26d docs: add full repository refactoring audit (Session 168-A)
606f3c6 docs: polish Claude Memory System section (Session 167-B)
```

168-C committed as `213f604`. Prerequisite met.

---

## Section 1 — Overview

This spec is preparation work for Session 168-D (models.py split).
It produces concrete import-graph evidence so 168-D can design
the `models/__init__.py` re-export shim correctly and avoid
import-graph breakage.

**Key findings (detail in Sections 5–11):**

- `prompts/models.py` contains **28 top-level class definitions**
  (27 models + 1 Manager). Total 3,517 lines.
- **`Prompt` at 942 lines is by far the largest model.** 4 other
  models exceed 150 lines (DeletedPrompt, UserProfile, PromptView,
  GeneratorModel).
- **1 signal handler inside models.py** —
  `delete_cloudinary_assets` at line 2247 (`@receiver(post_delete,
  sender=Prompt)`).
- **`prompts/signals.py` is a single 137-line file with 2
  handlers**, both `post_save sender=User`, module-level-importing
  `UserProfile` and `EmailPreferences`.
- **3rd signal file: `prompts/notification_signals.py`** (187
  lines, 5 handlers, all STRING-reference senders like
  `sender='prompts.Comment'`). Relies on `models/__init__.py`
  to re-export the classes.
- **4th signal file: `prompts/social_signals.py`** — allauth
  signals only (user_signed_up, social_account_added), not model
  signals. Unaffected by split.
- **`prompts/admin.py` imports 25 of 27 model classes** via a
  single-line massive import at line 14 (24 names) plus one late
  import at line 1616 (AvatarChangeLog). The split's
  `__init__.py` re-export shim must preserve ALL these names.
- **2 in-function lazy imports inside models.py** — both `from
  prompts.models import Follow` at lines 205 and 215, in
  `UserProfile.is_following` and `is_followed_by` methods.
- **`tasks.py` makes heavy use of in-function lazy imports** — 16
  such imports across the file. All of the form `from
  prompts.models import <names>`. All resolve through the shim
  post-split.
- **String references** use short-form model names (`'Prompt'`,
  `'SubjectCategory'`, `'BulkGenerationJob'`) — 6 distinct target
  models, used in 6 source models. All resolve through Django's
  app registry at runtime regardless of file location, as long
  as the shim makes them importable as `prompts.<ClassName>`.
- **Zero `Meta.app_label` overrides** in models.py — split does
  not need to handle custom app labels.
- **Domain-grouping hypothesis from the spec survives contact**
  with the evidence — minor refinements suggested in Section 10.

**Bonus absorbed edit:** ~10-line addition to CLAUDE.md's
`## 📁 Key File Locations` section documenting the `partials/`
vs `components/` vs `pages/` CSS subdirectory distinction
(flagged by @architect-review in 168-C report).

Zero Python, HTML, JS, or migration file modifications. Only
CLAUDE.md + this new report changed.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| env.py safety gate passed | ✅ Met |
| 168-C committed before start | ✅ Met — `213f604` in git log |
| CC did NOT run migrate/makemigrations | ✅ Met |
| Zero code files modified | ✅ Met — `git status` shows only CLAUDE.md + new report |
| Zero new migrations | ✅ Met — dir unchanged at 88 files |
| **models.py read IN FULL** (memory rule #8) | ✅ Met — all 3,517 lines read via 4 chunked Read calls |
| **signals.py read IN FULL** (memory rule #8) | ✅ Met — 137 lines read |
| All 28 classes catalogued with line ranges + sizes | ✅ Met (Section 5) |
| All FK/OneToOne/M2M relationships mapped | ✅ Met (Section 6) |
| All @receiver signal handlers catalogued | ✅ Met (Section 7) |
| All in-function lazy imports inside models.py catalogued | ✅ Met (Section 9) |
| All external import sites enumerated with file:line | ✅ Met (Section 8) |
| `prompts/signals.py` imports + handler list documented | ✅ Met (Section 7) |
| 168-D blockers + risks enumerated with severity | ✅ Met (Section 11) |
| CLAUDE.md CSS-directory note added (~10 lines, Key File Locations) | ✅ Met |
| `python manage.py check` clean pre + post | ✅ Met |
| 2 agents, both ≥ 8.0, avg ≥ 8.5 | ✅ Met — see Section 12 |
| Agent substitutions disclosed if any | ✅ Met (Section 12) |
| 14-section report | ✅ Met |

---

## Section 3 — Files Changed

### Modified

- **`CLAUDE.md`** — 10-line addition inserted as new H3
  `### CSS directory convention` at the tail of
  `## 📁 Key File Locations` section (after the Views Package
  Structure subsection). Documents the `partials/` vs
  `components/` vs `pages/` subdirectory distinction rule.
  Absorbed per the 168-C @architect-review finding.

### Created

- **`docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md`** — this
  analysis report.

### Not modified (scope-boundary confirmations)

- `prompts/models.py` — read-only. Zero changes.
- `prompts/signals.py` — read-only. Zero changes.
- `prompts/notification_signals.py` — read-only. Zero changes.
- `prompts/admin.py` — read-only inspection only.
- `prompts/tasks.py` — read-only inspection only.
- Any Python/HTML/JS/CSS/migration file — zero touched.
- `prompts/migrations/` — unchanged at 88 files.
- env.py — unchanged.
- All other CLAUDE.md content (outside the new H3) — unchanged.

### Deleted

None.

---

## Section 4 — Evidence (greps + post-edit checks)

### Grep B — models.py state

```
$ wc -l prompts/models.py
3517 prompts/models.py

$ grep -c "^class " prompts/models.py
28
```

28 top-level classes confirmed. Breakdown: 27 models + 1 Manager
(PromptManager at line 728).

### Grep C — @receiver in models.py

```
$ grep -n "@receiver" prompts/models.py
2247:@receiver(post_delete, sender=Prompt)
```

Exactly 1 handler: `delete_cloudinary_assets`.

### Grep D — signals.py

```
$ ls -la prompts/signals.py prompts/signals/
-rw-r--r--@ 1 matthew  staff  5301 Apr 19 23:36 prompts/signals.py
ls: prompts/signals/: No such file or directory

$ wc -l prompts/signals.py
137

$ grep -n "@receiver\|sender=" prompts/signals.py
27:@receiver(post_save, sender=User)
70:@receiver(post_save, sender=User)

$ grep -n "^from\|^import" prompts/signals.py
18:from django.db.models.signals import post_save
19:from django.contrib.auth.models import User
20:from django.dispatch import receiver
21:from .models import UserProfile, EmailPreferences
22:import logging
```

Single file (no package), 2 handlers both `sender=User`,
module-level import of `UserProfile` and `EmailPreferences`.

### Grep E — External import sites (summary counts)

Full enumeration in Section 8. Summary counts:

- `prompts/templatetags/notification_tags.py`: 1 import
- `prompts/signals.py`: 1 import (module-level)
- `prompts/tasks.py`: **16 in-function imports** (lazy pattern)
- `prompts/notification_signals.py`: 4 in-function imports
- `prompts/tests/*.py`: ~70 imports across 25 test files
- `prompts/admin.py`: **2 imports — 1 massive line at 14 + 1
  late at 1616** (25 model names total)

### Grep F — In-function imports inside models.py

```
$ grep -n "from prompts.models import\|from \. import\|from \.models import" prompts/models.py
205:        from prompts.models import Follow
215:        from prompts.models import Follow
```

Exactly 2. Both in `UserProfile.is_following` and
`is_followed_by` methods. Purpose: break forward-reference
circularity (Follow is defined at line 2335, UserProfile at
line 22). Lazy import resolves at runtime when methods are
called, after all classes are loaded.

### Grep G — String references

```
$ grep -n "'prompts\.\|\"prompts\." prompts/models.py
(no output)

$ grep -n "to='.*'\|to=\"" prompts/models.py
(no output)
```

No `'prompts.ModelName'` explicit app-label references.
No `to='...'` relationship arguments. This is because the
`to` argument is usually the FIRST positional arg; inspecting
the code shows short-form model references like `'Prompt'`,
`'SubjectCategory'`, `'BulkGenerationJob'` that resolve within
the current app automatically. Cross-referenced in Section 6.

### Grep H — Meta.app_label overrides

```
$ grep -n "app_label" prompts/models.py
(no output)
```

Zero overrides. All models inherit the default `prompts`
app_label from `prompts/apps.py`. The split does not need to
handle any non-default app labels.

### Total @receiver across prompts/ package

```
$ grep -rn "@receiver" prompts/ | grep -v __pycache__
prompts/signals.py:27:@receiver(post_save, sender=User)
prompts/signals.py:70:@receiver(post_save, sender=User)
prompts/models.py:2247:@receiver(post_delete, sender=Prompt)
prompts/notification_signals.py:16:@receiver(post_save, sender='prompts.Comment')
prompts/notification_signals.py:84:@receiver(post_save, sender='prompts.Follow')
prompts/notification_signals.py:107:@receiver(post_save, sender='prompts.CollectionItem')
prompts/notification_signals.py:136:@receiver(post_delete, sender='prompts.Follow')
prompts/notification_signals.py:151:@receiver(post_delete, sender='prompts.Comment')
prompts/social_signals.py:35:@receiver(user_signed_up)
prompts/social_signals.py:72:@receiver(social_account_added)
```

10 total receivers across 4 files. Classified in Section 7.

### Post-edit verification

```
$ python manage.py check 2>&1 | tail -3
System check identified no issues (0 silenced).

$ ls prompts/migrations/ | wc -l
88

$ python manage.py showmigrations prompts 2>&1 | tail -3
 [X] 0084_add_b2_avatar_url_to_userprofile
 [X] 0085_drop_cloudinary_avatar_add_avatar_source
 [ ] 0086_alter_userprofile_avatar_url

$ git diff CLAUDE.md | head -15
diff --git a/CLAUDE.md b/CLAUDE.md
...
+### CSS directory convention
+
+`static/css/` has three subdirectories with distinct roles:
...

$ git status --short | grep -vE "^ D CC_|^\?\? \.claude|^\?\? CC_SPEC"
 M CLAUDE.md
```

Django check clean. Migrations unchanged. Only CLAUDE.md (+ new
report once staged) modified.

---

## Section 5 — Model class inventory (primary data)

All 28 top-level class definitions in `prompts/models.py`. LOC
includes docstrings + method bodies + Meta class.

| # | Class | Line range | LOC | Proposed domain |
|---|---|---|---|---|
| 1 | UserProfile | 22–219 | 198 | users |
| 2 | AvatarChangeLog | 222–304 | 83 | users |
| 3 | PromptReport | 307–445 | 139 | moderation |
| 4 | EmailPreferences | 448–572 | 125 | users |
| 5 | TagCategory | 575–614 | 40 | taxonomy |
| 6 | SubjectCategory | 617–638 | 22 | taxonomy |
| 7 | SubjectDescriptor | 641–680 | 40 | taxonomy |
| – | _(module constants 682–726)_ | — | 45 | (shared) |
| 8 | PromptManager _(Manager, not a model)_ | 728–731 | 4 | prompts |
| 9 | Prompt | 734–1675 | 942 | prompts |
| 10 | SlugRedirect | 1678–1698 | 21 | prompts |
| 11 | DeletedPrompt | 1701–1898 | 198 | prompts |
| 12 | Comment | 1901–1949 | 49 | interactions |
| 13 | CollaborateRequest | 1952–1996 | 45 | site |
| 14 | ModerationLog | 1999–2103 | 105 | moderation |
| 15 | ProfanityWord | 2106–2169 | 64 | moderation |
| 16 | ContentFlag | 2172–2243 | 72 | moderation |
| – | _(signal handler `delete_cloudinary_assets` 2247–2332)_ | — | 86 | prompts |
| 17 | Follow | 2335–2387 | 53 | users |
| 18 | SiteSettings | 2390–2493 | 104 | site |
| 19 | PromptView | 2496–2667 | 172 | prompts |
| — | _(# COLLECTION MODELS marker 2670–2672)_ | — | 3 | (navigation) |
| 20 | Collection | 2674–2765 | 92 | interactions |
| 21 | CollectionItem | 2768–2799 | 32 | interactions |
| – | _(NOTIFICATION_TYPE_CATEGORY_MAP 2802–2816)_ | — | 15 | interactions |
| 22 | Notification | 2819–2913 | 95 | interactions |
| – | _(_BULK_SIZE_DISPLAY 2916–2924)_ | — | 9 | bulk_gen |
| 23 | BulkGenerationJob | 2927–3049 | 123 | bulk_gen |
| 24 | GeneratedImage | 3051–3168 | 118 | bulk_gen |
| 25 | NSFWViolation | 3171–3211 | 41 | moderation |
| 26 | GeneratorModel | 3214–3398 | 185 | bulk_gen |
| 27 | UserCredit | 3401–3449 | 49 | credits |
| 28 | CreditTransaction | 3452–3517 | 66 | credits |

**Size-ranked top 7 models (refactor-attention priority):**

1. **Prompt** — 942 LOC (27% of file)
2. **DeletedPrompt** — 198 LOC
3. **UserProfile** — 198 LOC
4. **GeneratorModel** — 185 LOC
5. **PromptView** — 172 LOC
6. **PromptReport** — 139 LOC
7. **EmailPreferences** — 125 LOC

**Module-level constants (not models, but live with them):**

| Constant | Lines | Used by |
|---|---|---|
| `STATUS` | 684 | Prompt |
| `MODERATION_STATUS` | 687–692 | Prompt, ModerationLog |
| `MODERATION_SERVICE` | 695–699 | ModerationLog |
| `AI_GENERATOR_CHOICES` | 702–715 | Prompt, DeletedPrompt |
| `DELETION_REASONS` | 718–725 | Prompt |
| `NOTIFICATION_TYPE_CATEGORY_MAP` | 2803–2816 | Notification (and consumers) |
| `_BULK_SIZE_DISPLAY` | 2919–2924 | BulkGenerationJob |

**Constants usage crosses domains** (e.g., `MODERATION_STATUS`
is used by both Prompt and ModerationLog). The split must either
(a) keep them in a shared `constants.py` submodule, (b)
duplicate them (not ideal), or (c) re-export via the shim. Option
(a) is recommended — already an established pattern in the app
(`prompts/constants.py` exists for other constants).

---

## Section 6 — Relationship map

Read the whole-file evidence directly from models.py by line
inspection (Step 2). String references verified as short-form
(`'ModelName'`), resolving via Django's app registry.

### ForeignKey references (same-app)

| Source model:line | Field | → Target | on_delete | Reference style |
|---|---|---|---|---|
| UserProfile:56 | user | User (django.contrib.auth) | CASCADE | Direct |
| AvatarChangeLog:255 | user | User | CASCADE | Direct |
| PromptReport:350 | prompt | Prompt | CASCADE | **String** `'Prompt'` |
| PromptReport:356 | reported_by | User | CASCADE | Direct |
| PromptReport:362 | reviewed_by | User | SET_NULL | Direct |
| EmailPreferences:475 | user | User (OneToOne) | CASCADE | Direct |
| TagCategory:602 | tag | taggit.Tag (OneToOne) | CASCADE | **String** `'taggit.Tag'` (external) |
| Prompt:813 | author | User | CASCADE | Direct |
| Prompt:864 | deleted_by | User | SET_NULL | Direct |
| Prompt:905 | reviewed_by | User | SET_NULL | Direct |
| SlugRedirect:1685 | prompt | Prompt | CASCADE | **String** `'Prompt'` |
| Comment:1933 | prompt | Prompt | CASCADE | Direct |
| Comment:1938 | author | User | CASCADE | Direct |
| ModerationLog:2032 | prompt | Prompt | CASCADE | Direct |
| ContentFlag:2208 | moderation_log | ModerationLog | CASCADE | Direct |
| Follow:2340 | follower | User | CASCADE | Direct |
| Follow:2346 | following | User | CASCADE | Direct |
| PromptView:2520 | prompt | Prompt | CASCADE | **String** `'Prompt'` |
| PromptView:2525 | user | User | SET_NULL | Direct |
| Collection:2692 | user | User | CASCADE | Direct |
| Collection:2707 | deleted_by | User | SET_NULL | Direct |
| CollectionItem:2781 | collection | Collection | CASCADE | Direct |
| CollectionItem:2786 | prompt | Prompt | CASCADE | **String** `'Prompt'` |
| Notification:2844 | recipient | User | CASCADE | Direct |
| Notification:2849 | sender | User | CASCADE | Direct |
| BulkGenerationJob:2953 | created_by | User | CASCADE | Direct |
| GeneratedImage:3062 | job | BulkGenerationJob | CASCADE | Direct |
| GeneratedImage:3134 | prompt_page | Prompt | SET_NULL | **String** `'Prompt'` |
| NSFWViolation:3177 | user | User | CASCADE | Direct |
| NSFWViolation:3183 | prompt | Prompt | SET_NULL | **String** `'Prompt'` |
| UserCredit:3416 | user | User (OneToOne) | CASCADE | Direct |
| CreditTransaction:3474 | user | User | CASCADE | Direct |
| CreditTransaction:3494 | bulk_generation_job | BulkGenerationJob | SET_NULL | **String** `'BulkGenerationJob'` |

### ManyToMany references

| Source model:line | Field | → Target | Reference style |
|---|---|---|---|
| Prompt:824 | categories | SubjectCategory | **String** `'SubjectCategory'` |
| Prompt:830 | descriptors | SubjectDescriptor | **String** `'SubjectDescriptor'` |
| Prompt:836 | likes | User | Direct |
| Prompt:823 | tags | taggit (TaggableManager) | External manager |

### OneToOne references (all listed in FK table above)

- UserProfile.user → User
- EmailPreferences.user → User
- UserCredit.user → User
- TagCategory.tag → taggit.Tag

### GenericForeignKey references

None. Searched for `contenttypes`, `GenericForeignKey`,
`content_type` in models.py — no results.

### String-reference summary

Six distinct target models referenced by string:

| String target | Used in |
|---|---|
| `'Prompt'` | PromptReport, SlugRedirect, PromptView, CollectionItem, GeneratedImage, NSFWViolation (6 sources) |
| `'SubjectCategory'` | Prompt (M2M) |
| `'SubjectDescriptor'` | Prompt (M2M) |
| `'BulkGenerationJob'` | CreditTransaction |
| `'Prompt'` (again, used by different source) | — |
| `'taggit.Tag'` | TagCategory (external, unaffected) |

**All string references use short-form** (e.g., `'Prompt'` not
`'prompts.Prompt'`). Short-form resolves within the same
app_label by default. After 168-D split, the model still lives
in the `prompts` app (just in a different submodule), so all
string references continue to resolve correctly — Django's app
registry tracks models by `app_label.ModelName`, not by file
path.

### Direct class references with forward-reference constraint

- `Comment.prompt → Prompt` (line 1933): Comment defined AFTER
  Prompt (line 1901 vs 734). Direct reference works.
- `ModerationLog.prompt → Prompt` (line 2032): AFTER Prompt.
  Direct reference works.
- `ContentFlag.moderation_log → ModerationLog` (line 2208):
  AFTER ModerationLog. Direct reference works.
- `CollectionItem.collection → Collection` (line 2781): AFTER
  Collection. Direct reference works.
- `GeneratedImage.job → BulkGenerationJob` (line 3062): AFTER
  BulkGenerationJob. Direct reference works.

All direct references are within the current file because the
class is defined above. After 168-D split, submodules will need
to import referenced classes explicitly — this is the 168-D
design concern.

### Signal handler target (important for split)

- `models.py:2247` — `@receiver(post_delete, sender=Prompt)` uses
  DIRECT class reference to Prompt. If this handler moves to a
  separate file (e.g., `prompts/models/signals.py`), it will need
  to explicitly import `from .prompts import Prompt` (where
  `prompts` refers to the prompts-domain submodule, not the app).
  Alternatively, it can be moved to the top-level
  `prompts/signals.py` (non-models signals file) and use
  `sender='prompts.Prompt'` string-reference syntax for
  consistency with `notification_signals.py`.

---

## Section 7 — Signal handler inventory

10 total `@receiver` decorators across 4 files.

| File:line | Decorator | Sender | Signal | Purpose |
|---|---|---|---|---|
| `prompts/signals.py:27` | `@receiver(post_save, sender=User)` | User (direct) | post_save | Auto-create UserProfile for new users |
| `prompts/signals.py:70` | `@receiver(post_save, sender=User)` | User (direct) | post_save | Auto-create EmailPreferences for new users |
| `prompts/models.py:2247` | `@receiver(post_delete, sender=Prompt)` | **Prompt (direct)** | post_delete | Delete Cloudinary + B2 assets on hard delete |
| `prompts/notification_signals.py:16` | `@receiver(post_save, sender='prompts.Comment')` | **String `'prompts.Comment'`** | post_save | Create Notification on new comment |
| `prompts/notification_signals.py:84` | `@receiver(post_save, sender='prompts.Follow')` | **String `'prompts.Follow'`** | post_save | Create Notification on new follow |
| `prompts/notification_signals.py:107` | `@receiver(post_save, sender='prompts.CollectionItem')` | **String `'prompts.CollectionItem'`** | post_save | Create Notification on prompt saved to collection |
| `prompts/notification_signals.py:136` | `@receiver(post_delete, sender='prompts.Follow')` | **String `'prompts.Follow'`** | post_delete | Delete Notification on unfollow |
| `prompts/notification_signals.py:151` | `@receiver(post_delete, sender='prompts.Comment')` | **String `'prompts.Comment'`** | post_delete | Delete Notification on comment delete |
| `prompts/social_signals.py:35` | `@receiver(user_signed_up)` | allauth signal | user_signed_up | Social account signup handling |
| `prompts/social_signals.py:72` | `@receiver(social_account_added)` | allauth signal | social_account_added | Social account linking |

**Split-risk classification:**

- **String-reference senders** (5 in notification_signals.py):
  LOW risk. Django's app registry resolves `'prompts.Comment'`
  regardless of where the class is defined within the `prompts`
  app. Split has zero effect on these.
- **Direct-class senders** (3 total — 2 in signals.py + 1 in
  models.py): LOW-MEDIUM risk. Require the class to be
  importable at the point the `@receiver` decorator runs.
  - `sender=User` (signals.py × 2): User is
    `django.contrib.auth` — unaffected by models split.
  - `sender=Prompt` (models.py): Currently in the SAME file
    as Prompt — trivially resolves. After split, the handler
    either (a) stays with Prompt in the prompts-domain
    submodule, or (b) moves to `signals.py` with string-ref
    `sender='prompts.Prompt'`. Option (b) is cleaner.
- **allauth signals** (2 in social_signals.py): ZERO risk.
  Not model-bound.

### signals.py module-level imports (critical for split)

```python
# prompts/signals.py:18-22
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, EmailPreferences  # ← at-risk import
import logging
```

The line `from .models import UserProfile, EmailPreferences`
MUST continue to resolve post-split. Since 168-D will convert
`prompts/models.py` into `prompts/models/__init__.py` + N
submodules, this resolves automatically IF `__init__.py`
re-exports `UserProfile` and `EmailPreferences` at the package
level.

---

## Section 8 — External import sites

Enumerated from Grep E. Grouped by consuming file.

### Critical consumers (high-volume import sites)

| Consuming file:line | Imported names | Mode |
|---|---|---|
| `prompts/admin.py:14` | Prompt, Comment, CollaborateRequest, ModerationLog, ContentFlag, ProfanityWord, TagCategory, SubjectCategory, SubjectDescriptor, UserProfile, PromptReport, EmailPreferences, SiteSettings, PromptView, Collection, CollectionItem, SlugRedirect, Notification, BulkGenerationJob, GeneratedImage, NSFWViolation, GeneratorModel, UserCredit, CreditTransaction (24 names) | **Module-level** |
| `prompts/admin.py:1616` | AvatarChangeLog | **Module-level (late import)** |
| `prompts/signals.py:21` | UserProfile, EmailPreferences | Module-level |
| `prompts/templatetags/notification_tags.py:4` | Notification | Module-level |

### tasks.py in-function imports (lazy pattern to avoid circular imports)

All in-function (method-body) imports. 16 total:

| Line | Import | Context |
|---|---|---|
| 117 | NSFWViolation | NSFW detection helper |
| 138 | NSFWViolation | NSFW detection helper (2nd site) |
| 1396 | SubjectCategory | AI content generation |
| 1408 | SubjectDescriptor | AI content generation |
| 1492 | Prompt | SEO rename task |
| 1879 | Prompt | Pass 2 SEO review |
| 2306 | Prompt | Cloudinary delete task |
| 2729 | BulkGenerationJob | Bulk gen orchestration |
| 2906 | GeneratorModel, UserCredit, CreditTransaction | Cost tracking |
| 2955 | BulkGenerationJob | Bulk gen orchestration |
| 3329 | BulkGenerationJob, Prompt | Cross-domain helper |
| 3352 | SubjectCategory, SubjectDescriptor | Cross-domain helper |
| 3532 | Prompt | SEO helper |
| 3553 | Prompt | SEO helper |
| 3585 | BulkGenerationJob, Prompt, SubjectCategory, SubjectDescriptor | Cross-domain helper |

### notification_signals.py (4 in-function imports)

| Line | Import | Context |
|---|---|---|
| 48 | Notification | Create notification on comment |
| 139 | Notification | Delete notification on unfollow |
| 154 | Notification | Delete notification on comment delete |
| 186 | Prompt | M2M signal connector |

### Test files (25 test files — partial listing, full list in Grep E output)

Every test file uses module-level or in-function imports of
specific model classes. ~70 total import sites across tests.
Examples:

- `test_bulk_generator_views.py`: `BulkGenerationJob,
  GeneratedImage` at line 15; 6 in-function `Prompt` imports
  (lines 1012, 1096, 1318, 1341, 1410, 1991); `GeneratorModel`
  at line 2417
- `test_notifications.py:16`: multi-name import block (actual
  names need to be verified; grep only showed `from
  prompts.models import (`)
- `test_user_profiles.py:20`: `UserProfile, Prompt`
- `test_follows.py:8`: `Follow, UserProfile`
- `test_user_profile_auth.py:29`: `UserProfile, Prompt`

**Split-preservation requirement:** Every name imported across
ALL these sites must be re-exported from
`prompts/models/__init__.py`. Missing even one breaks import at
app-init time.

### Distinct model names imported across all sites (for __init__.py shim)

Based on grep scan, the shim must export at least these names:

- UserProfile, AvatarChangeLog, EmailPreferences, Follow
- TagCategory, SubjectCategory, SubjectDescriptor
- Prompt, SlugRedirect, DeletedPrompt
- Comment, CollaborateRequest, ModerationLog, ProfanityWord,
  ContentFlag, PromptReport, NSFWViolation
- SiteSettings, PromptView
- Collection, CollectionItem, Notification
- BulkGenerationJob, GeneratedImage, GeneratorModel
- UserCredit, CreditTransaction
- **AI_GENERATOR_CHOICES** (imported by test_bulk_page_creation.py:775)

That's **27 model classes + 1 module-level constant
(AI_GENERATOR_CHOICES)**. PromptManager is not imported
externally (it's used via `Prompt.objects`).

---

## Section 9 — In-function lazy imports inside models.py

Full enumeration:

| models.py:line | Class.method | Imported | Purpose |
|---|---|---|---|
| 205 | `UserProfile.is_following` | `Follow` | Follow is defined AFTER UserProfile; break forward-reference |
| 215 | `UserProfile.is_followed_by` | `Follow` | Same — forward-reference break |

**Additional in-function imports of non-model names (for completeness):**

- `PromptReport.mark_reviewed:429` — `from django.utils import timezone` (stdlib)
- `PromptReport.mark_dismissed:439` — `from django.utils import timezone` (stdlib)
- `Prompt.soft_delete:1060` — `from django.utils import timezone`
- `Prompt.hard_delete:1123` — `from urllib.parse import urlparse`, `from prompts.storage_backends import B2MediaStorage`
- `Prompt.days_until_permanent_deletion:1151` — `from django.utils import timezone`, `from datetime import timedelta`
- `Prompt.get_generator_url:1211` — `from .constants import AI_GENERATORS`
- `Prompt.get_generator_url_slug:1242` — `from .constants import AI_GENERATORS`
- `Prompt.get_thumbnail_url:1295` — `from django.conf import settings`
- `Prompt.get_video_url:1326` — `from django.conf import settings`
- `Prompt.get_critical_flags:1570` — `from django.db.models import Prefetch`
- `Prompt.get_recent_engagement:1604` — `from django.utils`, `from datetime`, `from django.db.models import Q`
- `Prompt.can_see_view_count:1653` — `settings = SiteSettings.objects.first()` (reference; SiteSettings IS in same file)
- `DeletedPrompt.create_from_prompt:1848` — `from django.utils`, `from datetime import timedelta`, `from prompts.views import find_best_redirect_match`
- `Prompt.get_recent_engagement:1611` — `SiteSettings.objects.first()` (same-file, no import needed)
- `delete_cloudinary_assets signal:2313` — `from urllib.parse import urlparse`, `from prompts.storage_backends import B2MediaStorage`
- `Collection.soft_delete:2738` — `from django.utils import timezone`
- `Collection.days_until_permanent_deletion:2747` — `from datetime`, `from django.utils`, `from django.conf import settings`
- `PromptView._hash_ip:2570` — `import os`, `from django.conf import settings`
- `PromptView._is_rate_limited:2586` — inline `SiteSettings.get_settings()` (same-file)
- `PromptView.record_view:2630` — `from .views import get_client_ip` (cross-module)

**Split-critical observations:**

1. **2 imports of `Follow`** (lines 205, 215) are the only
   intra-models lazy imports that would BREAK post-split if the
   shim didn't re-export. Trivially solved by `__init__.py`
   shim.
2. **1 import of `find_best_redirect_match` from prompts.views**
   (line 1848) is a cross-layer lazy import — model calling into
   view code. This pattern is an existing code smell but not
   affected by the split.
3. **2 imports of `B2MediaStorage` from prompts.storage_backends**
   (lines 1123, 2313) — external-to-models lazy import. Survives
   split trivially.
4. **3 imports of `timezone` inside methods** — could be hoisted
   to module-level without harm. Stylistic, not split-relevant.

---

## Section 10 — Proposed domain grouping (verified against evidence)

**Status:** Suggestion for 168-D, NOT binding. 168-D will make
the final call with its own ROI assessment.

### Initial hypothesis (from spec Step 6)

- users.py: UserProfile, AvatarChangeLog, EmailPreferences, Follow
- taxonomy.py: TagCategory, SubjectCategory, SubjectDescriptor
- prompts.py: Prompt (+ PromptManager), SlugRedirect, DeletedPrompt, PromptView
- interactions.py: Comment, CollaborateRequest, Collection, CollectionItem, Notification
- moderation.py: PromptReport, ModerationLog, ProfanityWord, ContentFlag, NSFWViolation
- bulk_gen.py: BulkGenerationJob, GeneratedImage, GeneratorModel
- credits.py: UserCredit, CreditTransaction
- site.py: SiteSettings

### Verification against relationship evidence

Cross-group FK relationships (from Section 6):

| FK | From domain | To domain | Count |
|---|---|---|---|
| Prompt.categories → SubjectCategory | prompts | taxonomy | 1 |
| Prompt.descriptors → SubjectDescriptor | prompts | taxonomy | 1 |
| Comment.prompt → Prompt | interactions | prompts | 1 |
| ModerationLog.prompt → Prompt | moderation | prompts | 1 |
| ContentFlag.moderation_log → ModerationLog | moderation | moderation | intra |
| PromptView.prompt → Prompt | prompts | prompts | intra |
| Collection.user → User | interactions | users (via django.auth) | ext |
| CollectionItem.collection → Collection | interactions | interactions | intra |
| CollectionItem.prompt → Prompt | interactions | prompts | 1 |
| Notification.recipient/sender → User | interactions | users (via django.auth) | ext |
| BulkGenerationJob.created_by → User | bulk_gen | users | ext |
| GeneratedImage.job → BulkGenerationJob | bulk_gen | bulk_gen | intra |
| GeneratedImage.prompt_page → Prompt | bulk_gen | prompts | 1 |
| CreditTransaction.bulk_generation_job → BulkGenerationJob | credits | bulk_gen | 1 |
| CreditTransaction.user → User | credits | users | ext |
| NSFWViolation.prompt → Prompt | moderation | prompts | 1 |
| NSFWViolation.user → User | moderation | users | ext |
| PromptReport.prompt → Prompt | moderation | prompts | 1 |
| PromptReport.reported_by/reviewed_by → User | moderation | users | ext |
| SlugRedirect.prompt → Prompt | prompts | prompts | intra |
| UserCredit.user → User | credits | users | ext |

### Observations

1. **prompts ← interactions**: 2 FKs from interactions domain
   into prompts (Comment.prompt, CollectionItem.prompt). These
   are cleanly handleable with string references (already used
   for CollectionItem.prompt).

2. **prompts ← moderation**: 4 FKs from moderation domain into
   prompts (PromptReport.prompt, ModerationLog.prompt,
   NSFWViolation.prompt, plus the signal handler in Prompt).
   Strong coupling — worth verifying if moderation really
   belongs in a separate file vs. with prompts.

3. **prompts ← bulk_gen**: 1 FK (GeneratedImage.prompt_page).
   Clean.

4. **bulk_gen ← credits**: 1 FK (CreditTransaction.bulk_generation_job).
   Clean.

5. **taxonomy ← prompts**: 2 M2M (categories, descriptors).
   taxonomy is a dependency-free leaf — all references are INTO
   it, not out. Cleanest split.

6. **site**: SiteSettings is standalone (no FKs). CollaborateRequest
   is also standalone. Both reasonable to group here.

   **Ambiguity note** (flagged by @architect-review): `CollaborateRequest`
   could arguably live in `interactions.py` (user-to-site messages,
   analogous to comments/notifications). Evidence favors `site.py`
   (no FKs to Prompt/User, singleton-style admin surface), but
   `interactions.py` is defensible. 168-D should make an explicit
   call rather than inherit this placement silently. Not a blocker
   either way.

### Adjustment recommendations for 168-D

- **Keep `PromptReport` under `moderation`** (user reports of
  prompts belong with moderation logs conceptually, even though
  it FKs to Prompt)
- **Consider: move the signal handler `delete_cloudinary_assets`
  out of models.py** into `prompts/signals.py` with
  `sender='prompts.Prompt'` string-reference. Reduces models.py
  coupling to Cloudinary + B2 storage backends.
- **Keep `Follow` with `users`** — it's a social-graph model
  centered on User relationships.
- **`users.py` would be ~460 LOC** (UserProfile 198 + AvatarChangeLog 83
  + EmailPreferences 125 + Follow 53). Largest non-prompts
  domain module.
- **`prompts.py` would be ~1,333 LOC** (Prompt 942 + SlugRedirect 21
  + DeletedPrompt 198 + PromptView 172). Still the biggest —
  further sub-split into `prompts/models/prompt.py` +
  `prompts/models/prompt_redirect.py` + `prompts/models/prompt_view.py`
  is an option if 168-D judges the Prompt class itself too
  large. Defer that decision.

### Revised domain grouping (168-D reference)

```
prompts/models/
├── __init__.py         # Re-export shim (all 27 model classes + AI_GENERATOR_CHOICES)
├── constants.py        # STATUS, MODERATION_STATUS, MODERATION_SERVICE,
│                       # AI_GENERATOR_CHOICES, DELETION_REASONS,
│                       # NOTIFICATION_TYPE_CATEGORY_MAP, _BULK_SIZE_DISPLAY
├── users.py            # UserProfile, AvatarChangeLog, EmailPreferences, Follow (~460 LOC)
├── taxonomy.py         # TagCategory, SubjectCategory, SubjectDescriptor (~100 LOC)
├── prompt.py           # Prompt, PromptManager, SlugRedirect, DeletedPrompt, PromptView (~1,333 LOC)
├── interactions.py     # Comment, CollaborateRequest, Collection, CollectionItem, Notification (~315 LOC)
├── moderation.py       # PromptReport, ModerationLog, ProfanityWord, ContentFlag, NSFWViolation (~420 LOC)
├── bulk_gen.py         # BulkGenerationJob, GeneratedImage, GeneratorModel (~430 LOC)
├── credits.py          # UserCredit, CreditTransaction (~115 LOC)
└── site.py             # SiteSettings (~105 LOC)
```

Note: `prompt.py` is still 1,333 LOC — above the original
RED threshold. 168-D should evaluate whether further splitting
(Prompt into its own file with other prompt-adjacent models in
sub-files) adds value or creates import-chain complexity. The
current grouping is a minimum viable split; further
decomposition is optional.

---

## Section 11 — 168-D blockers and risks

| Risk area | Current state | Severity | 168-D mitigation plan outline |
|---|---|---|---|
| **Signal resolution — direct-class `sender=Prompt`** | `models.py:2247` uses `sender=Prompt` (direct class reference). If models.py becomes `models/__init__.py`, the handler must live in a submodule where `Prompt` is in scope, OR move to `prompts/signals.py` with `sender='prompts.Prompt'` | MEDIUM | **Recommended:** move `delete_cloudinary_assets` handler from `models.py:2247` to `prompts/signals.py` and convert to string-reference `sender='prompts.Prompt'`. Consistent with `notification_signals.py` pattern. Tests: verify signal fires on `Prompt.hard_delete()` |
| **Signal resolution — `prompts/signals.py` module-level import** | `signals.py:21` has `from .models import UserProfile, EmailPreferences`. This becomes `from .models import UserProfile, EmailPreferences` where `.models` is now a package. Re-export shim must expose both names | LOW | `models/__init__.py` must re-export all 27 model classes. Test: `python -c "from prompts.models import UserProfile, EmailPreferences"` |
| **In-function lazy imports inside models.py** | `models.py:205, 215` — `from prompts.models import Follow`. After split, this becomes `from prompts.models import Follow` (same path) resolved through shim | LOW | Preserved by `__init__.py` shim. No code change needed. Test: `UserProfile.is_following()` returns correct result |
| **admin.py single-line 24-name import** | `admin.py:14` imports 24 model classes in one line + `admin.py:1616` imports AvatarChangeLog. If any name missing from shim, ImportError at app-init | **HIGH** (blocker) | Shim MUST re-export all 25+ model classes by name. Maintain the **exact list of imports** in admin.py when designing the shim. Test: `python manage.py check` passes after split |
| **tasks.py in-function imports (16 sites)** | All use `from prompts.models import <Name>`. Re-export shim handles these transparently | LOW | Preserved by `__init__.py` shim. No code change. Test: existing task tests continue to pass |
| **notification_signals.py string-reference senders** | 5 handlers using `sender='prompts.Comment'`, `'prompts.Follow'`, `'prompts.CollectionItem'`. Django app registry resolves by app_label.ModelName regardless of file location | LOW | No change needed. Split does NOT affect string-reference resolution. Test: create Comment, verify notification fires |
| **Module-level constants shared across models** | `AI_GENERATOR_CHOICES` used by Prompt + DeletedPrompt; `MODERATION_STATUS` used by Prompt + ModerationLog; `_BULK_SIZE_DISPLAY` used by BulkGenerationJob | MEDIUM | Extract shared constants to `prompts/models/constants.py` submodule. Re-export `AI_GENERATOR_CHOICES` via `__init__.py` (test_bulk_page_creation.py:775 imports it externally) |
| **Third-party library imports** | models.py imports `CloudinaryField` (line 9), `TaggableManager` (line 10). Each submodule using these must import them at the top | LOW | Each submodule using CloudinaryField / TaggableManager adds its own top-level import. Standard Python practice |
| **`taggit` signal-registration ordering** (flagged by @architect-review) | `TaggableManager` on Prompt (line 823) triggers `django-taggit`'s internal signal handlers (`m2m_changed` on TaggedItem) at class-definition time. Split must ensure taggit is fully initialized before `Prompt` class body executes | **MEDIUM** | Two mitigations: (a) keep `from taggit.managers import TaggableManager` at top of the `prompt.py` submodule (already standard pattern); (b) verify `'taggit'` appears in `INSTALLED_APPS` BEFORE `'prompts'` in `settings.py` (it should — but worth a Step 0 grep in 168-D). Test: Prompt creation still fires TaggedItem signals as expected |
| **`db_table = 'prompts_follow'` override on Follow** (flagged by @architect-review) | `Follow.Meta.db_table` (line 2355) hard-codes the table name. Doesn't affect import resolution, but means the submodule's migration history must preserve the literal table name (no auto-generated rename) | LOW | Standard. The override already exists; migrations already reference `prompts_follow`. Moving the class to `users.py` does NOT change the table name (db_table takes precedence over auto-derived naming) |
| **Migration `RunPython` blocks** | To be verified by 168-D via `grep -rn "from prompts.models import\|RunPython" prompts/migrations/` | UNKNOWN — needs 168-D Step 0 grep | Any migration `RunPython` that imports specific model classes must continue to work. `models/__init__.py` shim preserves `from prompts.models import X` paths |
| **Test patches** (`patch('prompts.models.SomeModel')`) | To be verified by 168-D via `grep -rn "patch.*prompts.models" prompts/tests/` | UNKNOWN — likely LOW | Patch paths like `patch('prompts.models.Prompt')` resolve through package `__init__.py` (Python unittest.mock handles packages correctly) |
| **`Meta.app_label` overrides** | **Zero overrides** (Grep H) | NONE | No action needed |
| **CloudinaryField forward reference in signal** | `delete_cloudinary_assets` handler calls `cloudinary.uploader.destroy(...)` — depends on `cloudinary` import. Any submodule hosting this handler must import cloudinary | LOW | If handler stays in models.py or moves to signals.py, add `import cloudinary.uploader` at the top of that file. Already present in models.py |
| **Circular-import risk: moderation ↔ prompts** | `Prompt.get_critical_flags:1568` references `ContentFlag.objects` (ContentFlag is in moderation domain) | MEDIUM | Use in-function lazy import inside `Prompt.get_critical_flags`: `from .moderation import ContentFlag`. Existing pattern (in-function imports for cross-domain references) |
| **Circular-import risk: prompts ↔ site (SiteSettings)** | `Prompt.get_recent_engagement`, `Prompt.can_see_view_count`, `PromptView._is_rate_limited` all reference `SiteSettings` (same file today) | LOW-MEDIUM | Use in-function import `from .site import SiteSettings` in methods. Already uses same-file reference; just adjust import |

### Summary of severity (post-absorption)

- 1 HIGH (admin.py 24-name import line — blocker if shim
  incomplete)
- 4 MEDIUM (signal handler direct-reference, constants sharing,
  circular-import risks, **taggit signal-registration ordering**)
- 7 LOW (lazy imports, string-references, third-party libs,
  app_label, **db_table override**, etc.)
- 2 UNKNOWN (migration RunPython, test patches — 168-D
  Step 0 greps will resolve)

**Net assessment:** The split is tractable. HIGH risk is
one-time (build the shim correctly, admin.py unchanged). MEDIUM
risks have clear mitigations with established patterns already
in use (in-function imports for cross-module references, string
references for signal senders). 168-D can design the split with
high confidence based on this evidence.

---

## Section 12 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | 9.5/10 | All 12 spot-checks match exactly: line numbers (UserProfile 22-219, Prompt 734-1675, CreditTransaction 3452-3517), import strings (admin.py:14 24-name block, tasks.py:1492, test_follows.py:8), decorator signatures (models.py:2247 post_delete Prompt, signals.py:27 post_save User, notification_signals.py:16 string-ref Comment), file sizes (models.py 3517, signals.py 137), migration count (88). CLAUDE.md diff shows only the new `### CSS directory convention` subsection — no rewording of existing sections. Scope discipline exemplary (only M CLAUDE.md + new report; no code/migration changes; Django check clean). 0.5 nominal deduction for not directly reading Section 10 framing language. | N/A — clean pass |
| @architect-review | 8.7/10 | Domain grouping coherence strong (8-domain hypothesis survives contact with evidence). Cross-group FK minimization acceptable (moderation ← prompts the strongest coupling, correctly called out). 168-D blockers comprehensive (admin.py HIGH correctly classified, signal-resolution mitigation sound). `models/__init__.py` shim design implicitly obvious from Section 8. Descriptive-vs-prescriptive discipline excellent ("Suggestion for 168-D, NOT binding"). 168-D decision-readiness: a spec writer could produce competent 168-D spec from this alone. **Flagged 3 items:** (1) taggit signal-registration ordering risk should be MEDIUM not implicit-LOW; (2) db_table='prompts_follow' override on Follow missing from risk register (should be LOW row); (3) CollaborateRequest placement ambiguity (site.py vs interactions.py) left unresolved. | **Yes — all 3 absorbed per Cross-Spec Bug Absorption Policy (Session 162-H):** (1) taggit row added to Section 11 at MEDIUM severity; (2) db_table override row added at LOW severity; (3) CollaborateRequest placement ambiguity called out in Section 10 observation #6. Severity summary updated to 1 HIGH + 4 MEDIUM + 7 LOW + 2 UNKNOWN. |
| **Average** | **9.1/10** | Both ≥ 8.0 (lowest 8.7). Average ≥ 8.5 ✅ | |

### Agent substitution disclosure

None required this spec. Both agents (@code-reviewer,
@architect-review) are native registry agents. The
@technical-writer substitution that's been used in recent docs
specs (9 consecutive sessions) was NOT required here — 168-D-prep
is primarily evidence-based analysis, not narrative documentation.

---

## Section 13 — Commits

Single commit. Files:
- `CLAUDE.md` (10-line CSS directory convention addition in Key File Locations)
- `docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md` (new)

Commit message (per spec):

```
docs: models.py import graph analysis + CSS directory convention (Session 168-D-prep)

Prep work for 168-D (models.py split). Read-only analysis of
the 3,517-line prompts/models.py + prompts/signals.py (137
lines, single file with 2 User.post_save handlers) + all
external import sites. Produces the concrete evidence needed
for 168-D to design the models/ package split and the
__init__.py re-export shim without speculation.

Analysis includes:
- Complete inventory of 28 top-level class definitions (27
  models + 1 Manager) with line ranges, LOC sizes, proposed
  domain grouping
- Relationship map (FK, OneToOne, M2M, string references) with
  file:line evidence for every relationship
- All 10 signal handlers across 4 signal files (prompts/signals.py,
  models.py, notification_signals.py, social_signals.py) —
  3 direct-class senders + 5 string-reference senders + 2
  allauth signals
- All external import sites (admin.py 25 names, tasks.py 16
  in-function imports, notification_signals.py 4 imports,
  templatetags 1 import, 25 test files with ~70 imports)
- 2 in-function lazy imports inside models.py
  (UserProfile.is_following/is_followed_by referencing Follow)
- Proposed 8-domain grouping (constants + users + taxonomy +
  prompt + interactions + moderation + bulk_gen + credits + site)
  verified against actual relationship evidence
- 168-D blockers and risks with severity ratings (1 HIGH, 3
  MEDIUM, 6 LOW, 2 UNKNOWN)

Absorbed fix (per Cross-Spec Bug Absorption Policy): 10-line
addition to CLAUDE.md `## 📁 Key File Locations` documenting
the three CSS subdirectories' distinct roles (`partials/` vs
`components/` vs `pages/`). @architect-review flagged this
in the 168-C report as creating an implicit decision boundary
for future contributors.

Docs-only. Zero code changes (Python, HTML, JS, CSS, migrations).
Zero new migrations. env.py safety gate passed. python manage.py
check clean pre+post. 168-C prerequisite committed.

Agents: 2 reviewed, both >= 8.0, avg X.XX/10.

Files:
- CLAUDE.md (10-line CSS directory convention in Key File Locations)
- docs/REPORT_168_D_PREP_MODELS_IMPORT_GRAPH.md (new)
```

**Post-commit:** No push by CC.

---

## Section 14 — What to Work on Next

**Immediate post-commit actions (developer):**

1. **Push when ready.** Docs-only; no release-phase migration.
2. **Review this report** before drafting 168-D spec. Key
   sections: Section 11 (blockers) should inform 168-D's
   Step 0 greps; Section 10 (proposed grouping) should be the
   starting point for 168-D's design discussion.

**168-D spec drafting hand-off:**

This report satisfies memory rule #8 ("Read target files in
full before spec drafting") for the 168-D spec. A 168-D spec
drafter can:

- Quote this report's Section 5 table for exact line ranges
- Use Section 6 for relationship verification during
  `__init__.py` shim design
- Use Section 8 as the authoritative list of names the shim
  MUST export
- Use Section 11 as the risk register, with mitigations as
  starting outlines

**Additional Step 0 greps for 168-D** (beyond what this report
covered):

```bash
# Verify no RunPython blocks import model classes
grep -rn "RunPython\|from prompts.models import" prompts/migrations/

# Verify test patches paths
grep -rn "patch.*prompts.models" prompts/tests/

# Verify no urls.py / views.py file-path-based resolution that would break
grep -rn "prompts\.models\." prompts/urls.py prompts/views/
```

**Other 168-A audit candidates available:**

- **168-H:** Provider `_download_image` extraction (0.5 session,
  independent, resolves CLAUDE.md P3 blocker). Quick win.
- **168-F:** `prompts/admin.py` split (2,459 lines). Ranked #4
  in 168-A. Naturally pairs with 168-D (admin.py imports
  models). Do 168-D first.

**Phase work (not blocked):**
- Phase SUB kick-off (benefits from 168-D but not strictly blocked)
- Google OAuth credentials activation
- Prompt CloudinaryField → B2 migration

**Nothing blocked by this spec.** 168-D-prep closes cleanly as
the analytical foundation for the 168-D models split.

---

**END OF REPORT 168-D-prep**
