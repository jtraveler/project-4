# REPORT — Session 169-A: Generator Slug Diagnostic + Permanent Dot-Character Fix Plan

**Spec:** `CC_SPEC_169_A_GENERATOR_SLUG_DIAGNOSTIC.md` (v1, 2026-04-25)
**Type:** Read-only diagnostic + fix-plan deliverable
**Date executed:** 2026-04-25
**Production app:** `mj-project-4` (https://promptfinder.net)

## Preamble

| Check | Result |
|---|---|
| env.py safety gate run | ✅ `DATABASE_URL: NOT SET` — see Section 4 |
| Working tree clean | ✅ Only pre-existing noise — see Section 4 |
| `python manage.py check` (pre) | ✅ `System check identified no issues (0 silenced).` |
| `python manage.py check` (post) | ✅ Re-verified post-report — see Section 4 |
| Code/migration changes | 0 |
| Production DB writes | 0 (all queries SELECT-only via `heroku run --no-tty`) |
| `git push` to Heroku/origin | None |
| Files created | 1 — this report |

---

## Section 1 — Summary

The immediate production 500 has two compounding root causes.

**(1) Hardcoded literal in the bulk publish flow.** Both publish task functions in [tasks.py:3387](prompts/tasks.py#L3387), [3424](prompts/tasks.py#L3424), [3636](prompts/tasks.py#L3636), and [3693](prompts/tasks.py#L3693) write the literal string `'gpt-image-1.5'` to `Prompt.ai_generator`, ignoring the job's actual `provider`, `model_name`, and `generator_category`. A Grok job (provider=`xai`, model_name=`grok-imagine-image`) publishes 7 prompts, every one of them tagged `ai_generator='gpt-image-1.5'`. Production Query A confirms the failing prompt (pk=965) was generated this way.

**(2) Dotted value crashes Django's `<slug:>` URL converter.** `prompt_detail.html:457` calls `{% url 'prompts:ai_generator_category' prompt.get_generator_url_slug %}`. `get_generator_url_slug()` falls through to its last-resort branch ([prompt.py:564](prompts/models/prompt.py#L564)) and returns `'gpt-image-1.5'` verbatim. The URL pattern at [urls.py:71](prompts/urls.py#L71) uses `<slug:generator_slug>` whose regex `[-a-zA-Z0-9_]+` rejects the `.` → `NoReverseMatch` → 500.

The dot-character class issue is broader than this single literal. `AI_GENERATOR_CHOICES` ([models/constants.py:39](prompts/models/constants.py#L39)) contains `('gpt-image-1.5', 'GPT-Image-1.5')` as the canonical choice key. Migration 0080 (Session 153) set both `BulkGenerationJob.model_name` and `BulkGenerationJob.generator_category` defaults to `'gpt-image-1.5'`. There are 3 separate identifier taxonomies (`AI_GENERATOR_CHOICES`, `AI_GENERATORS` dict keys, `GeneratorModel.slug`) that disagree about whether dots are permitted — `GeneratorModel.slug` is the only one that's URL-clean (Section 7). Section 9's permanent-fix plan settles on a single canonical rule (no dots in any URL identifier, anywhere) and prescribes defense at validator, schema, and URL converter layers so a future "gpt-image-2.0" model addition is rejected up front rather than failing at template render time.

---

## Section 2 — Expectations

| Expectation | Met? |
|---|---|
| env.py safety gate verified | ✅ |
| Zero code changes | ✅ |
| Zero production DB writes | ✅ (all SELECT) |
| All 5 diagnostic questions answered with evidence | ✅ Section 5 |
| `AI_GENERATORS` dict contents catalogued | ✅ Q3 |
| Bulk publish `ai_generator`-setting code located + quoted | ✅ Q4 |
| Production data audit completed (counts only, no PII) | ✅ Section 4 |
| Permanent-fix plan delivered | ✅ Section 9 |
| 11 report sections drafted | ✅ |
| 2 agents reviewed, both ≥ 8.0, avg ≥ 8.5 | See Section 11 |

---

## Section 3 — Files Changed

| File | Status |
|---|---|
| `docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md` | created (this file) |

No other file modified.

---

## Section 4 — Evidence

### env.py safety gate

```
$ grep -n "DATABASE_URL" env.py
17:# New policy: env.py does NOT set DATABASE_URL. Django falls back to
20:# DATABASE_URL=<url> inline for that specific command.
22:#     "DATABASE_URL", "[REDACTED]")

$ python -c "import os; import env; print('DATABASE_URL:', os.environ.get('DATABASE_URL', 'NOT SET'))"
DATABASE_URL: NOT SET
```

Note: env.py source line 22 contains a commented-out example assignment with a postgres URL fragment from before the Session 163 credential rotation. The fragment in the live env.py source is non-functional (rotated). Per memory rule #4 (no credential echo, even stale/example), this report shows it as `[REDACTED]` rather than reproducing the source verbatim. Per spec rule 6, this report does not echo any credential value, live or rotated.

### Grep A — Working tree clean

```
$ git status --short
 D CC_SESSION_163_RUN_INSTRUCTIONS.md
 D CC_SPEC_163_B_MODEL_CLEANUP_AND_MIGRATION.md
 D CC_SPEC_163_C_DIRECT_UPLOAD_PIPELINE.md
 D CC_SPEC_163_D_SOCIAL_LOGIN_CAPTURE.md
 D CC_SPEC_163_E_SYNC_FROM_PROVIDER.md
 D CC_SPEC_163_F_DOCS_UPDATE.md
 D CC_SPEC_168_F_ADMIN_SPLIT.md
?? CC_SPEC_168_E_POSTMORTEM.md
?? CC_SPEC_169_A_GENERATOR_SLUG_DIAGNOSTIC.md
?? CC_SPEC_MONETIZATION_STRATEGY_DOCS_UPDATE.md
?? CC_SPEC_PROCFILE_RELEASE_PHASE_v2.md
```

Pre-existing noise only (deleted 163-series specs, untracked CC_SPEC drafts at repo root). No `prompts/` modifications. Confirmed clean baseline.

### Grep B — `AI_GENERATORS` location

```
$ grep -n "^AI_GENERATORS\b\|^AI_GENERATORS = " prompts/constants.py
11:AI_GENERATORS = {
```

Full dict contents catalogued in Q3 below.

### Grep C — `ai_generator` references

190 hits total across `prompts/`. Grouping (key hits only — full output preserved in agent inspection):

| Group | File:line | Significance |
|---|---|---|
| Field write (hardcoded literal) | `prompts/tasks.py:3387` | bulk publish v1 — passed to `_call_openai_vision` |
| Field write (hardcoded literal) | `prompts/tasks.py:3424` | bulk publish v1 — `Prompt(...ai_generator='gpt-image-1.5'...)` |
| Field write (hardcoded literal) | `prompts/tasks.py:3636` | bulk publish v2 — passed to `_call_openai_vision` |
| Field write (hardcoded literal) | `prompts/tasks.py:3693` | bulk publish v2 — `Prompt(...ai_generator='gpt-image-1.5'...)` |
| Field declaration | migration 0011 (initial), 0012, 0066, 0080 | `Prompt.ai_generator` field history |
| Choice list mutation | `prompts/migrations/0080_upgrade_gpt_image_15.py:31` | added `('gpt-image-1.5','GPT-Image-1.5')` and `('gpt-image-1','GPT-Image-1')` choice tuples |
| Form / admin metadata | `prompts/forms.py:72,81,110,111`; `prompts/admin/prompt_admin.py:37,45,102,182,183` | display, no value mutation |
| Display methods | `prompts/models/prompt.py:493,504,506,534` | `get_ai_generator_display_name`, `get_generator_url`, `get_generator_url_slug` |

### Grep D — `generator_category` / `model_name` in prompts/

Confirms the dot-defaults at the model layer (key hits below):

```
$ grep -n "^    generator_category\|^    model_name " prompts/models/bulk_gen.py
63:    model_name = models.CharField(max_length=100, default='gpt-image-1.5')
74:    generator_category = models.CharField(max_length=50, default='gpt-image-1.5')
```

Plus migration history showing this default was introduced in 0080:

| Migration | Default for `model_name` | Default for `generator_category` |
|---|---|---|
| 0061 (initial bulk gen, 2026-02) | `'gpt-image-1'` | `'ChatGPT'` |
| 0068 (Session 113, 2026-03) | (unchanged) | `'gpt-image-1'` (also backfilled existing 'ChatGPT' rows) |
| **0080 (Session 153, 2026-04-11)** | **`'gpt-image-1.5'` ← REGRESSION (dot reintroduced)** | **`'gpt-image-1.5'` ← REGRESSION** |

### Grep E — Publish flow: where `prompt.ai_generator` is set

Two functions both use a hardcoded literal:

```python
# prompts/tasks.py:3384-3389  (create_prompt_pages_from_job)
ai_content = _call_openai_vision(
    image_url=gen_image.image_url,
    prompt_text=gen_image.prompt_text,
    ai_generator='gpt-image-1.5',
    available_tags=available_tags,
)

# prompts/tasks.py:3418-3429  (create_prompt_pages_from_job)
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1.5',  # ← HARDCODED, ignores job.provider/model_name
    status=1 if job.visibility == 'public' else 0,
    ...
)

# prompts/tasks.py:3633-3638  (publish_prompt_pages_from_job — Phase 6B concurrent variant)
ai_content = _call_openai_vision(
    image_url=gen_image.image_url,
    prompt_text=gen_image.prompt_text,
    ai_generator='gpt-image-1.5',
    available_tags=available_tags,
)

# prompts/tasks.py:3686-3698  (publish_prompt_pages_from_job)
prompt_page = Prompt(
    title=title,
    slug=slug_val,
    author=job.created_by,
    content=gen_image.prompt_text,
    excerpt=ai_content.get('description', ''),
    ai_generator='gpt-image-1.5',  # ← HARDCODED, ignores job.provider/model_name
    status=1 if job.visibility == 'public' else 0,
    ...
)
```

Neither path reads `job.provider`, `job.model_name`, or `job.generator_category` when constructing the Prompt. Bug C is a code-level defect, not a configuration issue.

### Grep F — URL converters using generator identifiers

```
$ grep -rn "generator_slug\|<slug:.*generator\|ai_generator_category\|<str:.*generator" prompts/ prompts_manager/ --include="*.py"
prompts/urls.py:71:    path('prompts/<slug:generator_slug>/', views.ai_generator_category, name='ai_generator_category'),
prompts/urls.py:79:    path('inspiration/ai/<slug:generator_slug>/', RedirectView.as_view(...)),
prompts/urls.py:82:    path('ai/<slug:generator_slug>/', RedirectView.as_view(...)),
```

Three `<slug:>` patterns. All would crash on dotted values. None use `<str:>` (which would accept dots). Defense-in-depth at the URL layer is already correct — the URL converter is doing its job. The bug is upstream.

### Grep G — `GeneratorModel.slug` field type

```
$ grep -n "slug = models" prompts/models/bulk_gen.py
290:    slug = models.SlugField(unique=True, ...)
```

`SlugField` enforces Django's slug validator (`-`, `_`, alphanumerics, no dots). Confirmed by Query C which shows zero dots across all 7 production rows.

### Grep H — Generator/bulk_gen migrations

```
$ ls prompts/migrations/ | grep -i "generator\|bulk_gen"
0011_prompt_ai_generator.py
0012_prompt_featured_video_alter_prompt_ai_generator_and_more.py
0061_add_bulk_generator_models.py
0064_add_api_key_fields_to_bulk_generation_job.py
0066_add_gpt_image_1_generator_choice.py             # added 'gpt-image-1' (no dot)
0067_add_published_count_to_bulk_generation_job.py
0068_fix_generator_category_default.py               # 'ChatGPT' → 'gpt-image-1'
0082_add_generator_models_and_credit_tracking.py     # GeneratorModel introduced
0083_add_supports_reference_image_to_generator_model.py
```

Migration 0080 (`upgrade_gpt_image_15.py`) is the one that re-introduced dots — it is named for the model upgrade and not flagged with "generator" in its filename.

### Grep I — Templates calling `ai_generator_category`

```
prompts/templates/prompts/ai_generator_category.html        # 6 occurrences (canonical, type filter, sort filter)
prompts/templates/prompts/inspiration_index.html            # 2 occurrences (Schema.org URL, generator-card link)
prompts/templates/prompts/prompt_detail.html:457            # ← THE CRASH SITE
prompts/templates/prompts/partials/_generator_dropdown.html # 1 occurrence
```

`prompt_detail.html:457` is the only one that takes its argument from `prompt.get_generator_url_slug` (per-prompt-instance derived). The others all consume `gen.slug` / `generator.slug` from a server-validated context (`AI_GENERATORS.get(slug)` returned the dict, so the slug is known-clean). The user-visible 500 surfaces only on prompt detail because that's the only caller that derives the slug from prompt data rather than from a curated dict key.

### Grep J — Production logs (last 1500 lines)

```
2026-04-25T00:59:39 NoReverseMatch: Reverse for 'ai_generator_category' with arguments '('gpt-image-1.5',)' not found.
   1 pattern(s) tried: ['prompts/(?P<generator_slug>[-a-zA-Z0-9_]+)/\\Z']
2026-04-25T01:43:35 Internal Server Error: /prompt/cinematic-hispanic-woman-playing-instrument-under-northern-lights/
2026-04-25T01:43:35 NoReverseMatch at /prompt/cinematic-hispanic-woman-playing-instrument-under-northern-lights/
2026-04-25T01:43:35 File "/app/prompts/views/prompt_list_views.py", line 546, in prompt_detail
2026-04-25T01:43:35 raise NoReverseMatch(msg)
2026-04-25T01:43:35 django.urls.exceptions.NoReverseMatch: Reverse for 'ai_generator_category' with arguments '('gpt-image-1.5',)' not found.
```

Two distinct 500s in the window for the same prompt. Same crash signature. No PII (URLs and traceback filenames only).

### Production Queries — outputs

#### Query A (smoking gun)

```
pk: 965
ai_generator: 'gpt-image-1.5'
status: 1
created_on: 2026-04-25 00:53:39.791462+00:00
has generated_from: True
  job.id: 1e9840d8-bbe3-44e1-9536-36035de17e08
  job.provider: xai
  job.model_name: 'grok-imagine-image'
  job.generator_category: 'AI Generated'
```

The prompt is published (status=1). It was created from a Grok (`xai`) job using model `grok-imagine-image` and `generator_category='AI Generated'`. None of those values contain a dot, yet `ai_generator='gpt-image-1.5'` was written to the prompt. **This is impossible without a hardcoded literal somewhere in the publish path.** Grep E shows the literal at four call sites.

#### Query B (data scope)

```
Total prompts: 64
Prompts with dotted ai_generator: 7
  Percentage: 10.9%

Top 20 ai_generator values by count:
  'Midjourney': 53
  'gpt-image-1.5': 7
  'midjourney': 3
  'gpt-image-1': 1
```

Scope: **trivial** (7 rows out of 64 total). All 7 dotted prompts have `ai_generator='gpt-image-1.5'`. No other dotted variants. Note also that 53 prompts use the capitalised `'Midjourney'` (legacy upload-flow) and 3 use lowercased `'midjourney'` — both work because dashes pass the URL converter. (`'Midjourney'` resolves via `lower()+replace('_','-')` → `'midjourney'` which is in the AI_GENERATORS dict; `'gpt-image-1'` would 404 from `ai_generator_category` view because there is no `'gpt-image-1'` key in the dict, but it would not 500 because dashes pass `<slug:>`.)

#### Query C (GeneratorModel slugs)

```
Total GeneratorModel rows: 7

All GeneratorModel rows:
  slug='gpt-image-1-5-byok'  (dot=False) name='GPT-Image-1.5'   provider=openai     enabled=True byok_only=True
  slug='flux-schnell'         (dot=False) name='Flux Schnell'    provider=replicate  enabled=True byok_only=False
  slug='grok-imagine'         (dot=False) name='Grok Imagine'    provider=xai        enabled=True byok_only=False
  slug='flux-dev'             (dot=False) name='Flux Dev'        provider=replicate  enabled=True byok_only=False
  slug='flux-1-1-pro'         (dot=False) name='Flux 1.1 Pro'    provider=replicate  enabled=True byok_only=False
  slug='flux-2-pro'           (dot=False) name='FLUX 2 Pro'      provider=replicate  enabled=True byok_only=False
  slug='nano-banana-2'        (dot=False) name='Nano Banana 2'   provider=replicate  enabled=True byok_only=False
```

**100% clean.** SlugField + Django's slug validator is fully working. `'flux-1-1-pro'` (dashed) corresponds to `name='Flux 1.1 Pro'` (dotted display) — the right pattern. `GeneratorModel.slug` is the only taxonomy that's URL-safe today.

#### Query D (BulkGenerationJob audit)

```
Total BulkGenerationJob rows: 246
Jobs with dotted model_name: 32
Jobs with dotted generator_category: 0

Distinct (provider, model_name, generator_category) tuples:
  provider='openai'    model_name='gpt-image-1'                      generator_category='ChatGPT'      count=85
  provider='xai'       model_name='grok-imagine-image'               generator_category='AI Generated' count=46
  provider='openai'    model_name='gpt-image-1'                      generator_category='gpt-image-1'  count=35
  provider='replicate' model_name='google/nano-banana-2'             generator_category='AI Generated' count=25
  provider='openai'    model_name='gpt-image-1.5'                    generator_category='ChatGPT'      count=20
  provider='replicate' model_name='black-forest-labs/flux-schnell'   generator_category='AI Generated' count=13
  provider='replicate' model_name='black-forest-labs/flux-1.1-pro'   generator_category='AI Generated' count=9
  provider='replicate' model_name='black-forest-labs/flux-dev'       generator_category='AI Generated' count=8
  provider='openai'    model_name='gpt-image-1.5'                    generator_category='AI Generated' count=3
  provider='replicate' model_name='black-forest-labs/flux-2-pro'     generator_category='AI Generated' count=2
```

Three observations:

1. `generator_category` has **0 dotted values** in production despite the dotted default — the application code overrides it to one of `'ChatGPT'`, `'AI Generated'`, or `'gpt-image-1'` at job creation. The default never lands in real data.
2. `model_name` has **32 dotted values** — but most of these come from Replicate's `<vendor>/<model>` identifiers like `'black-forest-labs/flux-1.1-pro'` which contain dots in version numbers, AND from 23 `'gpt-image-1.5'` jobs (default not overridden for OpenAI BYOK path).
3. **`generator_category` is not the source** of the 7 dotted `Prompt.ai_generator` rows. The bulk publish flow doesn't read it (Grep E). The 7 dotted prompts come exclusively from the hardcoded literal.

#### Query E (xAI cross-reference — Bug C smoking gun)

```
xAI jobs: 46
  Job 1e9840d8-bbe3-44e1-9536-36035de17e08: provider=xai model_name='grok-imagine-image' generator_category='AI Generated'
    Prompt pages created: 7
      slug='cinematic-hispanic-woman-playing-instrument-under-northern-lights' ai_generator='gpt-image-1.5'
      slug='asian-woman-forest-portrait-playing-drum-cat'                       ai_generator='gpt-image-1.5'
      slug='asian-woman-walking-in-park-holding-coffee'                         ai_generator='gpt-image-1.5'
  Job dcc65e9c-...: 0 prompts
  Job c4ef751c-...: 0 prompts
  Job 9ea86981-...: 0 prompts
  Job 44340e99-...: 0 prompts
```

**All 7 dotted prompts on production come from a single Grok job.** Bug C is fully confirmed: a job whose `provider`/`model_name`/`generator_category` carry zero dots produces 7 prompts every one of which has `ai_generator='gpt-image-1.5'`. The publish flow demonstrably ignores the job's generator metadata.

### `python manage.py check` (post)

```
$ python manage.py check
System check identified no issues (0 silenced).
```

Identical to pre. No code modified.

---

## Section 5 — Five Diagnostic Questions Answered

### Q1 — What is the failing prompt's actual `ai_generator` value, and which job produced it?

`Prompt.objects.get(slug='cinematic-hispanic-woman-playing-instrument-under-northern-lights')` returned `pk=965`, `ai_generator='gpt-image-1.5'`, `status=1`, linked to `BulkGenerationJob` `1e9840d8-bbe3-44e1-9536-36035de17e08` whose `provider='xai'`, `model_name='grok-imagine-image'`, `generator_category='AI Generated'`.

**Grok mis-tagging hypothesis (Bug C): CONFIRMED.** A Grok-generated prompt is tagged `gpt-image-1.5`. Query E corroborates with 7-of-7 prompts from this job all carrying the dotted GPT-Image string.

### Q2 — How widespread is the dotted-`ai_generator` problem on production?

**Trivial scope: 7 of 64 prompts (10.9%).** All 7 carry `ai_generator='gpt-image-1.5'` exactly; no other dotted values. Top values:

```
'Midjourney':       53
'gpt-image-1.5':     7   ← target of fix
'midjourney':        3
'gpt-image-1':       1
```

A data migration affecting 7 rows is trivial and can run in the release phase with negligible downtime risk.

### Q3 — What does `AI_GENERATORS` dict in `prompts/constants.py` contain?

16 keys, **none with a dot**:

```
'midjourney', 'dalle3', 'dalle2', 'stable-diffusion', 'leonardo-ai',
'flux', 'sora', 'sora2', 'veo3', 'adobe-firefly', 'bing-image-creator',
'grok', 'wan21', 'wan22', 'nano-banana', 'nano-banana-pro'
```

Each value is a dict containing `name`, `slug`, `seo_subheader`, `seo_description`, `description`, `website`, `icon`, `choice_value`, `supports_images`, `supports_video`. Notably:

- **No key for `'gpt-image-1'`** (despite it being in `AI_GENERATOR_CHOICES` since 2026-03 via migration 0066)
- **No key for `'gpt-image-1.5'`** (added to `AI_GENERATOR_CHOICES` in migration 0080 but never added to `AI_GENERATORS`)
- **`'dalle3'`** (no dashes) but `AI_GENERATOR_CHOICES` uses `'dall-e-3'` (with dashes) — naming inconsistency, but routed via `choice_value` fallback in `get_generator_url`

Canonical key for "GPT-Image-1.5" today: **does not exist.** Either the dict needs a `'gpt-image-1-5'` (dashed) entry added, or — preferably — `Prompt.ai_generator` should map to `GeneratorModel.slug` ('gpt-image-1-5-byok' for that model) rather than to `AI_GENERATORS` keys.

### Q4 — Where exactly is `Prompt.ai_generator` set during the bulk publish flow?

Four hardcoded literal sites — verbatim quoted in Section 4 / Grep E:

| Function | File:line | Line of code |
|---|---|---|
| `create_prompt_pages_from_job` | [tasks.py:3387](prompts/tasks.py#L3387) | `ai_generator='gpt-image-1.5',` (passed to `_call_openai_vision`) |
| `create_prompt_pages_from_job` | [tasks.py:3424](prompts/tasks.py#L3424) | `ai_generator='gpt-image-1.5',` (Prompt constructor) |
| `publish_prompt_pages_from_job` | [tasks.py:3636](prompts/tasks.py#L3636) | `ai_generator='gpt-image-1.5',` (passed to `_call_openai_vision`) |
| `publish_prompt_pages_from_job` | [tasks.py:3693](prompts/tasks.py#L3693) | `ai_generator='gpt-image-1.5',` (Prompt constructor) |

Value source: **string literal**. None of the four sites read `job.provider`, `job.model_name`, or `job.generator_category`. This is true regardless of which provider the job actually ran on.

### Q5 — Does the `GeneratorModel` table contain any dotted slugs today?

**No.** All 7 production rows have dot=False (Section 4 / Query C). `SlugField` enforcement is working correctly. The dot exists only in the `name` field (the human-readable display column) where it is appropriate (`'Flux 1.1 Pro'`, `'GPT-Image-1.5'`).

This confirms `GeneratorModel.slug` as the only existing taxonomy that holds the canonical-rule line. The other two (`AI_GENERATOR_CHOICES`, `AI_GENERATORS`) are either lax (no validator on the choice keys) or mis-aligned with the data they're supposed to lookup.

---

## Section 6 — Three Confirmed/Refuted Bugs

### Bug A — Bad default values in `BulkGenerationJob` model

**Status:** confirmed, latent. **Severity:** P2 cleanup.

`prompts/models/bulk_gen.py:63` and `:74` declare `default='gpt-image-1.5'`. Migration 0080 introduced this regression on 2026-04-11 (Session 153 GPT-Image upgrade). However Query D shows that production data has zero dotted `generator_category` values — application code in `bulk_generator_views.py` overrides the default at every job creation. So Bug A is real but does **not** cause the user-visible 500. It is latent: if any code path falls back to the default, dotted values would persist.

`model_name` defaults are similar but 32 jobs do carry dotted `model_name` (mostly Replicate's slash-form identifiers, plus 23 `'gpt-image-1.5'` rows). Bug A is real for `model_name` too.

### Bug B — Inconsistent generator naming taxonomy

**Status:** confirmed. **Severity:** P1 latent.

Three taxonomies exist:

| Taxonomy | Location | Dot policy | Example dotted entry |
|---|---|---|---|
| `AI_GENERATOR_CHOICES` | `prompts/models/constants.py:28-41` | **Allows dots** | `('gpt-image-1.5', 'GPT-Image-1.5')` (line 39) |
| `AI_GENERATORS` dict keys | `prompts/constants.py:11-344` | **No dots** | (none — the dict simply has no entry for GPT-Image at all) |
| `GeneratorModel.slug` | `prompts/models/bulk_gen.py:290` (DB-backed) | **No dots** (SlugField) | (none — Query C confirms 0/7 dotted) |

Plus a fourth identifier system: `GeneratorModel.model_identifier` (e.g. `'black-forest-labs/flux-1.1-pro'`) which is the API-vendor-specific string and contains slashes/dots by design — used only for outbound API calls, never for URL routing.

Symptom: `Prompt.ai_generator` validates against `AI_GENERATOR_CHOICES` (allows dots) but is then passed to `get_generator_url_slug()` which routes through `AI_GENERATORS` (no dot key for GPT-Image) and falls through to a last-resort branch that returns the value verbatim — including the dot. The validation layer is misaligned with the URL-routing layer.

### Bug C — Bulk publish flow mis-tags `Prompt.ai_generator`

**Status:** confirmed. **Severity:** P0 user-visible.

Quoted code at four sites in [tasks.py](prompts/tasks.py) shows `ai_generator='gpt-image-1.5'` as a hardcoded literal that ignores the job's provider/model_name/generator_category. Query E shows a Grok job producing 7 prompts every one of which has `ai_generator='gpt-image-1.5'`. The hypothesis is fully validated.

Severity is P0 because:
- (a) it is the immediate root cause of the user-visible 500
- (b) it silently corrupts `ai_generator` data on every publish from any non-OpenAI bulk job — which means SEO / analytics / model-pages segmentation is wrong
- (c) it scales linearly with adoption: every Replicate or xAI job published mis-tags

---

## Section 7 — Surface Map: Every Place a Dot Could Enter

Comprehensive map of inputs to the URL-identifier pipeline:

| # | Surface | File / source | Allows dot today? | Should allow? | Notes |
|---|---|---|---|---|---|
| 1 | `BulkGenerationJob.model_name` default | [bulk_gen.py:63](prompts/models/bulk_gen.py#L63) | Yes | No (for OpenAI native) / N/A (for Replicate vendor strings) | Mixed semantics — Replicate uses `vendor/model-1.1` form intentionally; OpenAI BYOK uses our identifier |
| 2 | `BulkGenerationJob.generator_category` default | [bulk_gen.py:74](prompts/models/bulk_gen.py#L74) | Yes | No | Single-purpose URL-route identifier |
| 3 | `BulkGenerationJob` records — runtime values | DB | partly (32 dotted `model_name`, 0 dotted `generator_category`) | (1) yes for Replicate model_name, (2) no for generator_category | Query D |
| 4 | `Prompt.ai_generator` choice keys | [models/constants.py:39](prompts/models/constants.py#L39) | Yes (`'gpt-image-1.5'`) | No | `AI_GENERATOR_CHOICES` |
| 5 | `Prompt.ai_generator` field — runtime values | DB | Yes (7 rows) | No | Query B |
| 6 | `AI_GENERATORS` dict keys | [prompts/constants.py:11-344](prompts/constants.py) | No (16 keys, none dotted) | No | Should remain dot-free |
| 7 | `GeneratorModel.slug` | [bulk_gen.py:290](prompts/models/bulk_gen.py#L290) (`SlugField`) | No | No | Working correctly, defense-in-depth at model layer |
| 8 | `GeneratorModel.model_identifier` | [bulk_gen.py:301](prompts/models/bulk_gen.py#L301) | Yes (e.g. `flux-1.1-pro`) | Yes (out-of-scope — not used for URL routing) | API vendor strings — different concern |
| 9 | URL pattern `prompts/<slug:generator_slug>/` | [urls.py:71](prompts/urls.py#L71) | No (`<slug:>` rejects) | No | Defense layer working correctly |
| 10 | Two legacy redirect URL patterns | [urls.py:79,82](prompts/urls.py#L79) | No (`<slug:>`) | No | Same |
| 11 | Bulk generator UI `<select>` for category | `prompts/templates/prompts/bulk_generator.html` (not yet read in this diagnostic) | TBD by 169-B | No | Step 0 grep for the template not run — flagged for 169-B |
| 12 | Manual upload form `ai_generator` dropdown | [forms.py:81](prompts/forms.py#L81) → uses `AI_GENERATOR_CHOICES` | Yes (because choices have a dotted key) | No | Choices are the source |
| 13 | Migrations / fixtures / seed data | `0080_upgrade_gpt_image_15.py` | Yes (the migration itself uses dotted strings) | No | Will need re-write or RunPython data backfill in 169-B |
| 14 | Hardcoded literal in publish task | [tasks.py:3387,3424,3636,3693](prompts/tasks.py#L3387) | Yes (literal contains dot) | No | Bug C |
| 15 | Hardcoded literal in test fixtures | [test_bulk_page_creation.py:750,758,790,798](prompts/tests/test_bulk_page_creation.py) | Yes (asserts `ai_generator='gpt-image-1.5'`) | No (will need update when 169-B fixes the publish task) | Tests follow the bug; will follow the fix |
| 16 | `get_generator_url_slug()` last-resort fallback | [prompt.py:564](prompts/models/prompt.py#L564) | Yes (returns dotted value verbatim) | No | Fail-open behaviour propagates the dot to the URL reverser |

The dot enters the user-facing pipeline at sites 1, 4, 14 (writes); is preserved through site 16 (no sanitisation); and crashes at site 9 (URL converter does its job). Sites 6, 7, 9, 10 are correct defenses; sites 1, 2, 4, 14, 16 are missing defenses.

---

## Section 8 — URL Pattern Audit

| URL pattern | File:line | Converter | Accepts dotted value? | Action |
|---|---|---|---|---|
| `prompts/<slug:generator_slug>/` | [urls.py:71](prompts/urls.py#L71) | `<slug:>` (regex `[-a-zA-Z0-9_]+`) | **No** | Keep — defense-in-depth |
| `inspiration/ai/<slug:generator_slug>/` (legacy redirect) | [urls.py:79](prompts/urls.py#L79) | `<slug:>` | No | Keep |
| `ai/<slug:generator_slug>/` (legacy redirect) | [urls.py:82](prompts/urls.py#L82) | `<slug:>` | No | Keep |

Recommendation: **do not widen the URL converter to accept dots.** Doing so would mask future bugs and break Google's URL canonicalisation expectations (dots in path segments are unusual for content URLs). The single canonical rule should be: every value upstream of these URL patterns must already be dot-free.

---

## Section 9 — Permanent-Fix Plan

The user's stated goal: *"make it a goal to permanently fix it so generators with a dot won't have issues again."*

### 9.1 Settle the canonical identifier rule

**Rule:** All generator URL identifiers — in code, config, DB, and URLs — must match `^[a-z0-9][a-z0-9-]*$`. No dots, no underscores, no slashes, no whitespace, no uppercase. Display names ("GPT-Image-1.5", "Flux 1.1 Pro") live separately on `GeneratorModel.name` or in the second tuple position of `AI_GENERATOR_CHOICES`.

**Rationale:** This rule already holds for `GeneratorModel.slug` (Query C, 100% clean). Extending it to `AI_GENERATOR_CHOICES` keys, `AI_GENERATORS` dict keys, and `Prompt.ai_generator` runtime values closes the loop. `GeneratorModel.model_identifier` (e.g. `'black-forest-labs/flux-1.1-pro'`) is excluded — it's an outbound-API string, not a URL identifier, and follows vendor conventions.

### 9.2 Code changes required

| Surface | Change | Risk tier |
|---|---|---|
| `BulkGenerationJob.model_name` default | Reconsider — this field has mixed semantics. Recommend renaming/splitting in a separate spec; for 169-B set default to `''` (empty) and require population at job creation. | 🟠 High Risk (3,822-line tasks.py touched, model migration) |
| `BulkGenerationJob.generator_category` default | `'gpt-image-1.5'` → `'gpt-image-1-5'` (or remove the field entirely if unused for routing — see 9.4) | 🟡 Caution |
| `AI_GENERATOR_CHOICES` | Replace `('gpt-image-1.5', 'GPT-Image-1.5')` → `('gpt-image-1-5', 'GPT-Image-1.5')`; display string unchanged. Remove `('dall-e-3', ...)` legacy duplication of `'dalle3'` (or align — see 9.4). | ✅ Safe |
| `AI_GENERATORS` dict | Add `'gpt-image-1-5'` key (with `name='GPT-Image-1.5'`, full SEO copy) and `'gpt-image-1'` key (existing `AI_GENERATOR_CHOICES` entry has no dict entry today). | ✅ Safe |
| `Prompt.ai_generator` validator | Add `RegexValidator(r'^[a-z0-9][a-z0-9-]*$')` on the field. Migration alters field to add validator. | 🟡 Caution |
| `BulkGenerationJob.model_name` validator | NOT applied — Replicate identifiers contain `/` and `.`. Field is API-string, not a URL identifier. Add docstring. | ✅ Safe |
| `BulkGenerationJob.generator_category` validator | Same `RegexValidator` as `Prompt.ai_generator`. | ✅ Safe |
| `GeneratorModel.slug` | Already a `SlugField` — unchanged, but document as the canonical source of truth. | ✅ Safe |
| `get_generator_url_slug()` last-resort fallback | Replace `return self.ai_generator.lower().replace(' ', '-')` with `return None` (or a known-safe sentinel). Caller (template) must `{% if prompt.get_generator_url_slug %}` guard. Avoids fail-open propagation. | ✅ Safe |
| `prompt_detail.html:457` | Wrap `{% url ... %}` call in `{% if prompt.get_generator_url_slug %} ... {% endif %}` — defensive guard. | ✅ Safe |

### 9.3 Bulk publish flow fix — Bug C (the real fix, not just the dot)

The hardcoded literal at four sites must be replaced with a value derived from the job. Recommended implementation:

```python
# At top of create_prompt_pages_from_job AND publish_prompt_pages_from_job:
ai_generator_slug = _resolve_ai_generator_slug(job)  # new helper

# Then use ai_generator_slug in place of 'gpt-image-1.5' literal at lines 3387, 3424, 3636, 3693.
```

The helper:

```python
def _resolve_ai_generator_slug(job):
    """
    Map a BulkGenerationJob to the slug that should be written to
    Prompt.ai_generator. Pulls from the GeneratorModel registry
    (single source of truth) when possible; falls back to a safe
    'other' sentinel.

    Returns a string matching ^[a-z0-9][a-z0-9-]*$.

    NOTE: this lookup intentionally does NOT filter by `is_enabled=True`.
    `is_enabled` gates whether a model can accept NEW jobs. It is
    irrelevant to what a historical job already ran on. A Grok job run
    in April 2026 whose model is later disabled by an admin must still
    publish prompts tagged `'grok-imagine'`, not `'other'`. Filtering
    by `is_enabled` would mis-tag retrospective publishes — the same
    silent-corruption problem this fix is meant to solve, with a
    different wrong value.
    """
    # Strategy: match by (provider, model_identifier) → GeneratorModel.slug.
    # No is_enabled filter — see docstring.
    from prompts.models import GeneratorModel
    gm = GeneratorModel.objects.filter(
        provider=job.provider,
        model_identifier=job.model_name,
    ).first()
    if gm:
        return gm.slug

    # Defensive fallback — tag as 'other' rather than mis-tag.
    return 'other'
```

Once this lands, all 4 hardcoded sites in `tasks.py` use `ai_generator_slug` instead of `'gpt-image-1.5'`. New prompts published from a Grok job correctly tag as `ai_generator='grok-imagine'`; from a Flux job, `'flux-schnell'`/`'flux-dev'`/`'flux-1-1-pro'`/etc.; from OpenAI BYOK, `'gpt-image-1-5-byok'`.

This requires:

1. Adding entries to `AI_GENERATORS` dict for any `GeneratorModel.slug` that prompts are tagged with (otherwise `get_generator_url_slug` returns the slug unchanged but `ai_generator_category` view 404s).
2. Adding the new slugs to `AI_GENERATOR_CHOICES` so model validation accepts them.
3. Or — better — rewriting `get_generator_url_slug()` to query `GeneratorModel.objects.filter(slug=self.ai_generator).first()` directly, and rewriting `ai_generator_category` view to consume `GeneratorModel` rather than the static `AI_GENERATORS` dict. This collapses three taxonomies into one.

Recommend the more radical "collapse to one taxonomy" approach as the long-term fix, with a smaller intermediate fix in 169-B.

### 9.4 Data migration required

Two parts (Django data migration, NOT raw SQL — release-phase gate enforces it):

```python
# In a new migration after 0086:
def fix_dotted_generator_values(apps, schema_editor):
    Prompt = apps.get_model('prompts', 'Prompt')
    BulkGenerationJob = apps.get_model('prompts', 'BulkGenerationJob')

    # Prompt.ai_generator: 7 rows expected
    Prompt.objects.filter(ai_generator='gpt-image-1.5').update(
        ai_generator='gpt-image-1-5'
    )

    # BulkGenerationJob.generator_category: 0 rows expected per Query D,
    # but defensive sweep in case new rows have landed since.
    BulkGenerationJob.objects.filter(
        generator_category__contains='.'
    ).update(generator_category=Replace(F('generator_category'), Value('.'), Value('-')))

    # NOTE: model_name is intentionally NOT migrated. Replicate vendor
    # identifiers like 'black-forest-labs/flux-1.1-pro' must keep their
    # dots and slashes — they are outbound API strings.
```

Scope: ~7 row updates. Trivial. Reverse migration is `'gpt-image-1-5'` → `'gpt-image-1.5'`.

**Caveat — Bug C interaction:** the 7 dotted prompts come from a Grok job. Replacing them with `'gpt-image-1-5'` keeps the misattribution (a Grok prompt tagged GPT-Image), only with a URL-safe form. The user's correct fix is to retag those 7 rows as `'grok-imagine'` (matching `GeneratorModel.slug`). 169-B should propose this as the migration body, with a flag to disable if the correct retag would break test assertions or caller expectations. The simpler `Replace('.','-')` migration is a safer first step that fixes the 500 immediately, and the retag migration follows after Bug C's code fix lands.

### 9.5 Defense-in-depth

| Layer | Defense | Files |
|---|---|---|
| Schema | `RegexValidator(r'^[a-z0-9][a-z0-9-]*$')` on `Prompt.ai_generator` and `BulkGenerationJob.generator_category` | model fields |
| Choices | `AI_GENERATOR_CHOICES` keys all match the regex | `prompts/models/constants.py` |
| Lookup dict | `AI_GENERATORS` keys all match the regex | `prompts/constants.py` |
| URL converter | Keep `<slug:>` (no widening) — also covers the four other template call sites at `ai_generator_category.html:102,493,499,505,531,536`, `inspiration_index.html:35,70`, `_generator_dropdown.html:18` (each currently consumes a curated `gen.slug` from `AI_GENERATORS` so is safe today; if 169-D collapses these to `GeneratorModel` lookups, the safety property must be re-verified) | `prompts/urls.py` (no change) |
| Helper return | `get_generator_url_slug()` returns `None` (not the dotted value) when no AI_GENERATORS entry matches | `prompts/models/prompt.py` |
| Template | `{% if prompt.get_generator_url_slug %}` guard before `{% url %}` | `prompt_detail.html:457` |
| Tests | New test file `prompts/tests/test_generator_slug_validation.py` enforcing the canonical rule across all four taxonomies. **Coverage exemption:** `BulkGenerationJob.model_name` is intentionally exempt from the regex check because Replicate vendor strings (`'black-forest-labs/flux-1.1-pro'`) contain dots and slashes by design. The test for `model_name`'s default must assert exemption explicitly — e.g. `test_bulk_gen_model_name_default_documented_exempt` — so a future contributor cannot un-exempt it without conscious choice. Without this explicit assertion, the claim "these tests would have caught migration 0080's regression" only covers `generator_category`, not `model_name` — and migration 0080 dotted both. | new |
| CI | Tests run on every commit; new model values that violate `^[a-z0-9-]+$` fail validation immediately | (no CI change — existing test runner) |

The test file should assert:

```python
def test_ai_generator_choice_keys_are_dot_free():
    for key, _ in AI_GENERATOR_CHOICES:
        self.assertRegex(key, r'^[a-z0-9][a-z0-9-]*$', f"choice key {key!r} contains forbidden chars")

def test_ai_generators_dict_keys_are_dot_free():
    for key in AI_GENERATORS:
        self.assertRegex(key, r'^[a-z0-9][a-z0-9-]*$')

def test_bulk_gen_defaults_are_dot_free():
    field_default = BulkGenerationJob._meta.get_field('generator_category').default
    self.assertRegex(field_default, r'^[a-z0-9][a-z0-9-]*$')

def test_prompt_ai_generator_validator_rejects_dots():
    p = Prompt(ai_generator='gpt-image-1.5', ...)
    with self.assertRaises(ValidationError):
        p.full_clean()

def test_get_generator_url_slug_returns_none_for_unknown():
    p = Prompt(ai_generator='gpt-image-2.0', ...)
    self.assertIsNone(p.get_generator_url_slug())

def test_template_guards_against_none_slug(self):
    # Render prompt_detail with an unknown generator; template must not crash.
    ...
```

These tests would have caught migration 0080's regression at PR-review time (the `'gpt-image-1.5'` choice tuple violates the canonical rule). They are the primary insurance against a future "gpt-image-2.0"-style regression.

### 9.6 Recommended next-spec sequence

| Spec | Scope | Risk | Tests added |
|---|---|---|---|
| **169-B** — Code + data fix | (a) Update `AI_GENERATOR_CHOICES` `'gpt-image-1.5'` → `'gpt-image-1-5'`; (b) add `RegexValidator` to `Prompt.ai_generator`, `BulkGenerationJob.generator_category`; (c) data migration to convert 7 existing dotted Prompt rows; (d) tighten `get_generator_url_slug()` last-resort to return `None` + add template guard. | 🟡 Caution (touches `prompts/models/prompt.py` 🟠 file at one site, plus migration) | new test file (per 9.5) |
| **169-C** — Bulk publish flow fix (Bug C) | Replace 4 hardcoded literals in `tasks.py` with `_resolve_ai_generator_slug(job)` helper. Add `AI_GENERATORS` dict entries for grok, gpt-image-1, gpt-image-1-5. Update test fixtures in `test_bulk_page_creation.py` that assert `'gpt-image-1.5'`. Optional follow-up data migration to retag the 7 mis-tagged Grok prompts to `'grok-imagine'`. | 🔴 Critical (`tasks.py` is 3,822 lines — use new-helper-bottom-of-file pattern) | extend `test_bulk_page_creation.py` |
| **169-D** — Single-taxonomy collapse (long-term) | Rewrite `get_generator_url_slug()` to consume `GeneratorModel.slug` directly. Rewrite `ai_generator_category` view to load via `GeneratorModel.objects.get(slug=...)`. Migrate `AI_GENERATORS` dict's SEO copy fields onto `GeneratorModel`. Deprecate `AI_GENERATOR_CHOICES`. | 🔴 Critical | comprehensive |

169-B and 169-C are independently shippable. 169-D is architectural and should be sequenced after 169-B + 169-C are stable in production.

---

## Section 10 — Risks and gotchas

| # | Risk | Mitigation |
|---|---|---|
| 1 | Data migration affects production data | Heroku release phase enforces migration before web dynos serve traffic (Session 165-A). 7 rows is trivial; rollback is the inverse `Replace('-','.')` on a known set |
| 2 | Existing Google-indexed URLs may contain dotted slugs (from share buttons on the prompt detail page) | Such URLs would already 500 today — fixing them to dash-form will resolve the 500. The dotted URLs were never reachable; nothing to preserve |
| 3 | Test fixtures in [test_bulk_page_creation.py:750,758,790,798](prompts/tests/test_bulk_page_creation.py) assert the literal `'gpt-image-1.5'` | 169-B/169-C must update these assertions in lockstep with the code fix |
| 4 | If `AI_GENERATORS` dict key changes break callers using string-literal lookups (e.g. fixture data, integration tests), those need updating too | grep for `'gpt-image-1\.5'` and `"gpt-image-1\.5"` in 169-B Step 0 |
| 5 | `BulkGenerationJob.model_name` mixed semantics — Replicate uses `vendor/model-1.1` form (with dots and slashes) intentionally; OpenAI BYOK paths used to put a single identifier here | Recommend NOT applying URL-safe validator to `model_name`. Add docstring clarifying this field is an outbound API string, not a URL identifier. Long-term: rename to `provider_model_identifier` for clarity |
| 6 | CSS class names in templates that may use `ai_generator` value | Grep flagged none in `prompts/templates/` for class name use; values appear only in copy and `{% url %}` calls. 169-B should re-verify |
| 7 | Migrations use the dotted choice tuple — regenerating choices in a future migration would re-introduce the dot | 169-B's `RegexValidator` will cause `python manage.py check` to fail on any future migration that re-introduces a dotted choice. CI enforces |
| 8 | The Grok-mis-tagging (Bug C) means 7 prompts are SEO-tagged as GPT-Image when they should be Grok — affects analytics, generator-page counts, and content-type segmentation | 169-C should include the corrective retag migration (`'gpt-image-1-5'` → `'grok-imagine'` for the 7 known rows). Defer until after 169-B confirms the URL fix is stable in production |
| 9 | `'Midjourney'` (capitalised) in 53 prompts and `'midjourney'` (lowercase) in 3 prompts — case inconsistency | Out of scope for 169-A. Flag for separate cleanup spec. Both currently work because `get_generator_url_slug()` does `.lower().replace('_', '-')` first |
| 10 | `'dall-e-3'` choice key has no matching `AI_GENERATORS` dict entry (`'dalle3'` instead) | Latent 404 (not 500). Out of scope for 169-A. Flag for cleanup. Resolved by 169-D's single-taxonomy collapse |

---

## Section 11 — Agent Ratings

| Agent | Score | Key finding | Acted on? |
|---|---|---|---|
| @code-reviewer | 9.0/10 | env.py source's commented-out postgres URL fragment was reproduced verbatim in Section 4; per memory rule #4 (no credential echo, even stale/example), should be `[REDACTED]` despite the value being already-rotated and non-functional. | Yes — Section 4 env.py block now shows `[REDACTED]` in place of the rotated URL fragment |
| @architect-review (initial) | 7.5/10 | Three concerns: (1) `_resolve_ai_generator_slug`'s `is_enabled=True` filter would mis-tag retrospective publishes if a model is later disabled — silent corruption with a different wrong value; (2) test suite gap — `test_bulk_gen_defaults_are_dot_free` covers `generator_category` but not `model_name`, so the "would have caught migration 0080" claim was overstated (0080 dotted both fields); (3) 169-B-first sequencing oversold the fix — every new Grok/Replicate publish keeps writing the misattributed value until 169-C lands. | Yes — all three resolved (see re-evaluation row) |
| @architect-review (re-evaluation, post-fix) | 9.0/10 | Plan-completeness concerns fully resolved. One remaining minor implementation note for the 169-C spec author: the `'other'` fallback sentinel has no `AI_GENERATORS` dict entry, so a fallback publish would 404 silently on the generator category page — should be addressed in 169-C either by adding an `'other'` AI_GENERATORS entry or by documenting the sentinel as 404-safe pending 169-D's single-taxonomy collapse. Not a blocker on the 169-A plan itself. | Acknowledged — flagged for 169-C spec author (not a 169-A action) |
| **Average (final)** | **9.0/10** | | |

**Score formula:** average of the two reviewers using the higher of any reviewer's two scores when re-evaluation occurred (per CC_SPEC_TEMPLATE Agent Rating Protocol — re-verified post-fix score is the operative score). `(9.0 + 9.0) / 2 = 9.0`. Both reviewers ≥ 8.0, average ≥ 8.5 — meets spec rule 7.

**Fixes applied between initial and re-evaluation runs:**

1. Section 4 env.py block: replaced commented-out postgres URL fragment with `[REDACTED]` and added a clarifying note about the rotation/redaction policy
2. Section 9.3 helper code: removed the `is_enabled=True` filter from the `GeneratorModel` query and added an explicit docstring paragraph explaining why historical attribution must not depend on prospective enablement
3. Section 9.5 Tests row: added a "Coverage exemption" sub-bullet documenting `model_name` as intentionally exempt from the regex check (Replicate vendor strings are valid with dots/slashes), prescribing an explicit `test_bulk_gen_model_name_default_documented_exempt` assertion to force conscious future change
4. Section 12: added a multi-paragraph "Important caveat about 169-B's blast radius" explaining that 169-B fixes the URL-safety dimension but not the ongoing misattribution from continued Grok/Replicate publishes during the 169-C deferral window; the 169-C scope description now explicitly requires the corrective retag migration joining through `GeneratedImage.job` → `BulkGenerationJob.provider/model_name` → `GeneratorModel`

---

## Section 12 — What to Work on Next

**169-B is ready to draft.** Recommended scope: Section 9.2 (code defenses + AI_GENERATOR_CHOICES fix) + Section 9.4 (7-row data migration converting `'gpt-image-1.5'` → `'gpt-image-1-5'`) + Section 9.5 test file. Risk profile is 🟡 Caution (one tier-🟠 file touched at one site for the validator addition, plus a fresh migration). Single-spec session, ≤4 agent reviews.

**Important caveat about 169-B's blast radius:** 169-B alone does NOT stop new misattribution from happening. It fixes the URL-safety dimension (the 500 crash) for the 7 existing dotted prompts. But while 169-C is deferred, every new bulk publish from a Grok or Replicate job continues hitting the four hardcoded literals at `tasks.py:3387,3424,3636,3693` and writes `ai_generator='gpt-image-1.5'` (or after 169-B, `'gpt-image-1-5'` — still wrong, just URL-safe). Production currently has 46 xAI jobs and 57 Replicate jobs; any future publish from these continues corrupting `ai_generator` SEO/analytics segmentation. The 169-B-first sequencing is defensible because (a) it stops the user-visible 500 fastest, (b) 169-C touches 🔴 Critical `tasks.py` (3,822 lines) and benefits from staging, and (c) 169-B's data migration can be redesigned in 169-C to retag the 7 (now 7+N) rows correctly with their actual provider's slug. But the user should make this trade-off consciously rather than assume 169-B fully stops the bleeding.

**Defer 169-C until 169-B is in production for at least one session cycle.** 169-C touches the 🔴 Critical tasks.py file at four sites; staging the fix in a follow-up reduces blast radius if a regression appears. 169-C scope must explicitly include a corrective retag migration that converts every `Prompt.ai_generator` value tagged `'gpt-image-1-5'` (post-169-B) back to its actual provider's `GeneratorModel.slug` by joining through `GeneratedImage.job` → `BulkGenerationJob.provider/model_name` → `GeneratorModel`.

**Defer 169-D indefinitely.** Architectural collapse should wait until both 169-B and 169-C are stable, and only proceed if `AI_GENERATORS` divergence becomes a recurring source of bugs.

---

**End of report.**
