# REPORT_173_B_NSFW_PREFLIGHT

## NSFW Pre-Flight v1 — Provider-Aware ProfanityWord Extension

**Spec:** `CC_SPEC_173_B_NSFW_PREFLIGHT.md`
**Status:** PARTIAL — Sections 9 and 10 filled in after full suite gate
**Cluster shape (Memory Rule #15):** HYBRID

---

## Section 1 — Overview

Mateo identified an account-suspension risk: every NSFW prompt that
reaches the API counts against PromptFinder's API account, even if
rejected by the provider. xAI charges $0.02 per content-moderation
rejection. OpenAI/Google can suspend API access for sustained policy
violations. The existing profanity filter catches explicit slurs but
not borderline content that triggers provider-specific moderation
(e.g. `'topless'` on Nano Banana 2, `'gigantic boobs'` on NB2 only,
`'sensual'` in combination with anatomy on NB2).

This spec extends the existing `ProfanityWord` model with provider-aware
classification:

- **Tier 1 (universal):** existing `block_scope='universal'` behavior
  preserved — blocks across ALL providers (CSAM-adjacent terms, etc.)
- **Tier 2 (provider advisory):** new `block_scope='provider_advisory'`
  with `affected_providers` JSONField — blocks only when the user has
  selected one of the listed providers

The architecture deliberately reuses the existing system: same admin UI,
same pre-flight check function (extended), same user-facing error UX
with a provider-advisory message variant.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| 4 new fields on ProfanityWord (block_scope, affected_providers, last_reviewed_at, review_notes) | ✅ Met |
| Migration generated and applies cleanly | ✅ Met (0092_profanityword_provider_aware) |
| `check_text_with_provider()` method added | ✅ Met |
| Backward-compat: legacy `check_text` and `check_prompt` unchanged | ✅ Met |
| `validate_prompts(prompts, provider_id='')` extended | ✅ Met |
| Bulk view `api_validate_prompts` extracts model_identifier | ✅ Met |
| Seed management command with starter lists per provider | ✅ Met |
| Admin UI surfaces new fields with fieldsets | ✅ Met |
| User-facing message variant for provider_advisory | ✅ Met |
| 5+ tests covering all branches | ✅ Met (6 tests pass) |
| `python manage.py check` passes | ✅ Met |
| Critical Reminder #11 (Update Fields Audit) | ✅ Met (no save sites use update_fields= for ProfanityWord) |
| All 5 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (8.92/10) |

### Step 0 verbatim grep outputs

```bash
$ grep -n "class ProfanityWord" prompts/models/moderation.py
264:class ProfanityWord(models.Model):

$ wc -l prompts/models/moderation.py prompts/services/profanity_filter.py
     444 prompts/models/moderation.py
     229 prompts/services/profanity_filter.py

$ grep -n "ProfanityFilterService" prompts/admin/moderation_admin.py | head -3
20:    ProfanityWord,
162:@admin.register(ProfanityWord)
163:class ProfanityWordAdmin(admin.ModelAdmin):

$ grep -n "profanity\|preflight\|check_prompt\|check_profanity" prompts/views/bulk_generator_views.py | head -5
(no direct uses — call site is in services/bulk_generation.py validate_prompts)

$ ls prompts/migrations/*.py | grep -v __init__ | tail -3
prompts/migrations/0089_add_error_type_retry_count_to_generatedimage.py
prompts/migrations/0090_seed_gpt_image_2.py
prompts/migrations/0091_add_gpt_image_2_to_choices.py
```

The actual pre-flight call chain: frontend `bulk-generator-generation.js` →
`POST /tools/bulk-ai-generator/api/validate/` → `api_validate_prompts` view
→ `service.validate_prompts(prompts)` (service layer in
`services/bulk_generation.py`) → calls `ProfanityFilterService.check_text(text)`
per prompt.

Frontend currently sends `{prompts: [...]}` only — no `model_identifier`.

### Verification grep outputs

```bash
$ grep -n "block_scope\|affected_providers\|last_reviewed_at\|review_notes" prompts/models/moderation.py
323:    block_scope = models.CharField(
334:    affected_providers = models.JSONField(
346:    last_reviewed_at = models.DateField(
355:    review_notes = models.TextField(

$ grep -n "check_text_with_provider\|_format_provider_advisory_message" prompts/services/profanity_filter.py
236:    def check_text_with_provider(
391:    def _format_provider_advisory_message(

$ grep -n "provider_id" prompts/views/bulk_generator_views.py | head -3
267:    # Session 173-B: extract provider_id (model_identifier) from request
272:    provider_id = data.get('model_identifier', '')
276:    result = service.validate_prompts(prompts, provider_id=provider_id)

$ ls prompts/migrations/0092*.py prompts/management/commands/seed_provider_advisory_keywords.py prompts/tests/test_nsfw_preflight.py
prompts/management/commands/seed_provider_advisory_keywords.py
prompts/migrations/0092_profanityword_provider_aware.py
prompts/tests/test_nsfw_preflight.py

$ python manage.py test prompts.tests.test_nsfw_preflight
Ran 6 tests in 0.043s
OK
```

---

## Section 3 — Changes Made

### `prompts/models/moderation.py` (1 str_replace)

Added 4 new fields to `ProfanityWord` (between the existing `notes`
field and the `Meta` class):

- `block_scope` — `CharField(max_length=20, choices=['universal', 'provider_advisory'], default='universal')`
- `affected_providers` — `JSONField(default=list, blank=True)`
- `last_reviewed_at` — `DateField(null=True, blank=True)`
- `review_notes` — `TextField(blank=True, default='')`

All fields have defaults/null=True so existing rows are valid post-migration
without data backfill.

### `prompts/migrations/0092_profanityword_provider_aware.py` (new file, auto-generated)

4 `AddField` operations only. No `AlterField`, no data migration.

### `prompts/services/profanity_filter.py` (~155 lines added)

- Added new method `check_text_with_provider(text, provider_id='')`
  returning a dict with `allowed`, `reason`, `matched_words`, `severity`,
  `message`, `scope_provider`. Universal-then-advisory check pattern.
- Added 2 message helpers: `_format_universal_block_message()` (for
  consistency with universal path messaging) and
  `_format_provider_advisory_message()` (variant that names the provider
  + suggests Flux for non-Flux strict providers).
- Existing `check_text()` and `check_prompt(prompt_obj)` methods
  unchanged — full backward-compat for all existing callers.
- Memory Rule #13 application: 3 `logger.warning` calls cover empty
  text input + Tier 1 query failure + Tier 2 query failure paths.

### `prompts/services/bulk_generation.py` (1 str_replace)

`validate_prompts(prompts, provider_id='')` extended:
- Tier 1 (universal): still uses legacy `check_text(text)` — preserves
  existing test mocks against `check_text` (all 78 tests in
  `test_bulk_generation_tasks` still pass)
- Tier 2 (provider advisory): new conditional block runs ONLY if Tier 1
  cleared AND `provider_id` is given. Calls `check_text_with_provider`.

When `provider_id=''` (frontend hasn't yet been wired to send
`model_identifier` — see Section 5), Tier 2 block is skipped entirely.
Behavior identical to pre-173-B.

### `prompts/views/bulk_generator_views.py` (1 str_replace)

`api_validate_prompts` extracts `model_identifier` from the request body
(defaults to empty string) and passes to `service.validate_prompts()`
as `provider_id`. Type-checked (string).

### `prompts/admin/moderation_admin.py` (1 str_replace)

`ProfanityWordAdmin` updated:
- `list_display` adds `block_scope`, `last_reviewed_at`
- `list_filter` adds `block_scope`
- `search_fields` adds `review_notes`
- New `fieldsets` section: "Provider Awareness (Session 173-B)" groups
  the 4 new fields with description text

### `prompts/management/commands/seed_provider_advisory_keywords.py` (new, ~150 lines)

Idempotent via `update_or_create(word=word.lower(), defaults=...)`.
`--dry-run` flag for safe preview. Single-pass `word_to_data` dict
merges providers across the OpenAI/NB2/Grok lists (e.g. `'topless'`
ends up with `affected_providers=['gpt-image-1.5', 'gpt-image-2',
'google/nano-banana-2']` since those 3 providers all reject it).

### `prompts/tests/test_nsfw_preflight.py` (new file, 6 tests)

`NSFWPreflightTests` class with `setUp` clearing the 5-min word-list
cache. Tests:
1. `test_universal_block_fires_with_provider`
2. `test_universal_block_fires_with_no_provider`
3. `test_provider_advisory_blocks_for_affected_provider` (3 sub-cases)
4. `test_universal_block_takes_precedence_over_advisory`
5. `test_provider_advisory_message_suggests_flux_for_strict_providers`
6. `test_provider_advisory_with_empty_providers_does_not_block`

All pass. Tests use uniquely-named words (e.g. `'173btestbadword'`,
`'topless173b'`) to avoid `unique=True` constraint conflicts with the
27-word existing seed list.

---

## Section 4 — Issues Encountered and Resolved

**Issue 1:** Initial implementation used `affected_providers__contains=provider_id`
ORM filter (per spec section 5.2 pseudocode). First test run failed: 2 of
6 tests showed `True is not False` — advisory blocks weren't firing for
affected providers.
**Root cause:** Django's `JSONField __contains` lookup is inconsistent
between PostgreSQL prod and SQLite test DB for "list contains string
element" semantics. PostgreSQL JSONB `@>` operator expects the contained
value to be a list itself (`affected_providers__contains=[provider_id]`),
while SQLite's polyfill behavior differs.
**Fix applied:** Switched to fetch-all-advisory + filter-in-Python pattern.
The DB query filters by `block_scope='provider_advisory'` and
`is_active=True` only; the per-provider filtering happens in Python via
`provider_id in w['affected_providers']`. Same pattern as the existing
`check_text` iteration. Defensive `isinstance(w.get('affected_providers'), list)`
guards malformed entries.
**File:** `prompts/services/profanity_filter.py:340-372`

**Issue 2:** First restructure of `validate_prompts` to use `check_text_with_provider`
broke 5 tests + caused 2 errors in related test suites.
**Root cause:** Existing tests in `test_bulk_generation_tasks.py` mock
`mock_instance.check_text.return_value = (True, [], 'low')`. When I
replaced the `check_text()` call with `check_text_with_provider()`, the
mocks no longer applied, so tests querying for profanity matches saw
empty results (real test DB has no profanity rows).
**Fix applied:** Restructured `validate_prompts` to use a layered
approach: Tier 1 calls legacy `check_text()` (preserves all existing
mocks); Tier 2 conditionally calls new `check_text_with_provider()` only
when `provider_id` is given AND Tier 1 cleared. Backward-compat fully
preserved — empty `provider_id` means Tier 2 is skipped entirely.
**File:** `prompts/services/bulk_generation.py:128-181`

**Issue 3:** Dead cache key `'profanity_word_list_v2'` in
`refresh_word_list()` — flagged by @architect-review and @django-pro.
**Root cause:** Initial implementation included a "v2 cache" delete as
forward-thinking infrastructure, but `check_text_with_provider` doesn't
actually cache its results (queries the DB directly). The orphan cache
delete is harmless (no-op for non-existent keys) but misleading.
**Fix applied:** Removed `cache.delete('profanity_word_list_v2')` line
post-agent-review (one-line fix; doesn't require agent re-run since all
agents scored ≥ 8.0).
**File:** `prompts/services/profanity_filter.py:233`

### Memory Rule #13 application notes

Three logger.warning paths in `check_text_with_provider`:
- Empty/None text input (line ~270) — defensive degrade to "allowed"
  rather than crash
- Tier 1 universal-words query failure (line ~297) — log + degrade
- Tier 2 advisory-words query failure (line ~351) — log + degrade

Each includes structured `provider_id` field plus the underlying error
message via `%s`. All three paths return `'allowed': True` to avoid
hard-blocking the user when the filter itself errors — the legacy
`check_text` path is still in place at the validate_prompts layer as
the primary defense.

### Critical Reminder #11 (Update Fields Audit)

`grep -rn "ProfanityWord" prompts/ | grep -i "update_fields"` returns
empty — no save sites use `update_fields=`. All 4 new fields are nullable
or have defaults, so existing `ProfanityWord.objects.update()` calls and
plain `.save()` calls continue to work without modification.

---

## Section 5 — Remaining Issues

**Frontend wire-up of `model_identifier` in `/api/validate/` POST body**
**Recommended fix:** Add `model_identifier: I.settingModel.value` to the
fetch body in `static/js/bulk-generator-generation.js` (around line 911,
where `body: JSON.stringify({prompts: finalPrompts})` is built).
**Priority:** P2 (one-line follow-up; backend is ready)
**Reason not resolved:** Spec section 6.2 explicitly placed this out of
scope — "If model_identifier is NOT in the request body, that's a
separate fix... do NOT scope-creep this spec to add it." Backend
infrastructure is fully ready; the frontend edit is trivial.

**Pre-existing security gap: `api_start_generation` does not call `validate_prompts`
server-side.** (NOT introduced by 173-B — pre-existing.)
**Detail:** Pre-flight relies on the frontend voluntarily hitting
`api_validate_prompts` first. A client (curl, modified JS) bypassing
validate would skip ALL profanity filtering — both Tier 1 and Tier 2.
Mitigated currently by `@staff_member_required` decorator (limited
audience — only staff users can hit the bulk generator) but inconsistent
with "pre-flight is the security boundary" framing.
**Recommended fix:** Move `validate_prompts` invocation into
`api_start_generation` itself as a defense-in-depth gate. Or document
explicitly as a known limitation.
**Priority:** P3 (low — gated by `@staff_member_required`; will become
higher priority if/when bulk generation opens to non-staff users)
**Reason not resolved:** Out of scope for 173-B (which is about
extending pre-flight, not relocating it). Flagged by
@backend-security-coder during agent review.

---

## Section 6 — Concerns and Areas for Improvement

**Concern 1:** Provider identifier coupling — `seed_provider_advisory_keywords.py`
hardcodes provider strings (`'gpt-image-1.5'`, `'google/nano-banana-2'`,
etc.). If `seed_generator_models.py` changes a model_identifier, the seed
command must be updated alongside. There's no automated check.
**Impact:** Latent maintenance risk. Acceptable for v1 (~30 entries).
**Recommended action:** Add a startup self-test or management command
that cross-references `affected_providers` values against
`GeneratorModel.model_identifier` and warns on mismatches. Future P3.

**Concern 2:** Tier 2 re-runs DB query per prompt (no caching layer).
For batches of 50 prompts where Tier 1 clears, Tier 2 fires 50 times.
**Impact:** Negligible at current scale (advisory list ~30-50 entries).
**Recommended action:** Add in-memory cache for the advisory list at the
service level (matching the existing 5-min `'profanity_word_list'` cache
pattern) when batches grow. Future P3.

**Concern 3:** Provider display dict in `_format_provider_advisory_message`
duplicates names that could come from `GeneratorModel` registry.
**Impact:** Minor coupling — if a model's display name changes,
hardcoded copy must be updated.
**Recommended action:** Future P3 — read display names from
`GeneratorModel` at message-format time. Trade-off: an extra DB query
per blocked prompt, vs current hardcoded performance.

**Concern 4:** `check_text_with_provider` bypasses the existing 5-min
cache used by `check_text`. Latent inconsistency: cached words may not
reflect recent admin changes for ~5 minutes for the legacy path, but
`check_text_with_provider` queries fresh each time.
**Impact:** Acceptable — Tier 2 is the new path; freshness is preferable
to cache for v1 while admin is actively tuning lists.
**Recommended action:** When Tier 2 stabilizes (volume of advisory
checks justifies caching), unify the cache strategy. Future P3.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @django-pro | 8.8/10 | Model fields correct. Migration shape correct (4 AddField, no AlterField). JSONField __contains gotcha correctly resolved with fetch-then-filter pattern. 2 queries max, no N+1. Backward-compat clean. Word uniqueness handled in tests. Admin fieldsets match spec. Minor: dead `'profanity_word_list_v2'` cache key noted. | Yes — dead cache key removed in Section 4 Issue 3 fix |
| 1 | @backend-security-coder | 8.7/10 | Pre-flight call order verified frontend→backend. Case-insensitivity robust (lowercase + word boundary regex). No SQL/JSON injection on `affected_providers` (Python `in` operator + isinstance guard). Memory Rule #13 correctly applied at 3 fallback paths. Pre-flight is cost-positive. Empty advisory list edge case correct. Flagged pre-existing `api_start_generation` security gap (NOT introduced by 173-B but worth tracking) and frontend wire-up gap. | Yes — both flagged in Section 5 as Remaining Issues |
| 1 | @code-reviewer | 9.3/10 | Scope discipline clean (8 declared files, no creep). Evidence anchoring strong with Session 173-B traceability comments. Critical Reminder #11 verified (no update_fields= broken). Backward-compat preserved. Seed command idempotent. Memory Rule #13 honored. Implementation deviation (PostgreSQL/SQLite JSONField gotcha) defensible. Tests cover all spec-mandated branches. | N/A |
| 1 | @test-automator | 9.0/10 | All 6 tests pass. Cache invalidation in setUp essential. Unique word naming sidesteps unique=True constraint. Test 3 covers two affected + one unaffected provider. Test 4 precedence test workaround documented. Test 5 verifies both 'Flux' and provider name. Memory Rule #13 explicit test gap acceptable. View-layer integration relies on existing 158 view tests passing — sufficient for v1. | N/A |
| 1 | @architect-review | 8.8/10 | Implementation correctly deviates from spec's `__contains` filter. Double-call pattern in validate_prompts introduces architectural asymmetry (Tier 1 cached, Tier 2 fresh) — acceptable trade-off for v1. Seed command implementation cleaner than spec pseudocode. Provider identifier coupling is latent maintenance risk (acceptable for v1). Future expansion paths (warn-only, per-user override, time-decay) tracked. Dead `'profanity_word_list_v2'` cache key noted. | Yes — dead cache key removed |
| **Average** | | **8.92/10** | | **Pass ≥ 8.5** |

All scores ≥ 8.0. Average 8.92 ≥ 8.5 threshold. No re-run required.

---

## Section 8 — Recommended Additional Agents

**@frontend-developer:** Would have been the right reviewer for the
frontend wire-up gap (currently a Remaining Issue). Out of scope here
since spec section 6.2 explicitly deferred frontend changes.

**@migration-specialist:** Would have validated the migration's
zero-downtime safety (all fields default-able, no AlterField). The
generated migration meets these criteria mechanically; @django-pro's
review covered this implicitly.

For the spec's narrow scope (backend infrastructure for Tier 2
provider-aware pre-flight), the 5 chosen agents covered material
concerns adequately.

---

## Section 9 — How to Test

### Closing checklist (Memory Rule #14)

**Migrations:** `0092_profanityword_provider_aware.py` — 4 AddField ops,
no data migration. Applies via Heroku release phase on deploy. No
manual `python manage.py migrate` required (per project policy — CC
never runs migrate).

**Manual browser tests (max 2 at a time, with explicit confirmation between):**

Round 1 (universal blocks unchanged — backward-compat sanity):
1. Submit a bulk job with a Tier 1 universal-block term (e.g. CSAM-adjacent)
   → verify pre-flight rejects with the SAME wording as pre-173-B
   ("Content flagged — the following word(s) were found: ...").
2. Submit a clean prompt → verify it passes validation as before.

Round 2 (admin tuning):
3. Visit `/admin/prompts/profanityword/` → verify the new fields
   (block_scope, last_reviewed_at) appear in the list view AND
   filterable via the right sidebar. Open one entry and verify the
   "Provider Awareness (Session 173-B)" fieldset section is present.
4. Run `python manage.py seed_provider_advisory_keywords --dry-run` →
   verify it lists ~30 words with provider lists. Then run without
   --dry-run → verify count summary.

Round 3 (Tier 2 advisory — REQUIRES FRONTEND WIRE-UP FIRST):
5. **PRE-REQUISITE:** apply the one-line frontend fix (add
   `model_identifier: I.settingModel.value` to the validate POST body
   in `bulk-generator-generation.js`). Until this happens, Tier 2
   silently never fires in production.
6. Submit a bulk job with a Tier 2 advisory term + Nano Banana 2 (e.g.
   "topless") → verify the new advisory message appears with provider
   name + Flux suggestion.
7. Submit the SAME prompt with Flux Schnell selected → verify
   pre-flight ALLOWS submission.

**Failure modes to watch for:**
- Universal blocks no longer fire → Tier 1 path broken (regression on
  legacy `check_text` flow). Run existing 78 tests in
  `test_bulk_generation_tasks.py` to catch.
- Tier 2 fires for non-affected providers → fetch-then-filter Python
  logic broken (check `provider_id in w['affected_providers']` line).
- Migration fails to apply → check `0092_profanityword_provider_aware.py`
  for unexpected operations beyond the 4 AddField. Run
  `python manage.py migrate --plan` first.

**Backward-compatibility verification:**
- Pre-173-B `validate_prompts(prompts)` callers (no `provider_id`) —
  unchanged behavior (Tier 2 skipped).
- Pre-173-B `ProfanityWord` rows — auto-classified as `block_scope='universal'`
  via the field default; no data backfill needed.
- Existing `check_text()` and `check_prompt(prompt_obj)` methods — unchanged.

**Automated test results:**

```bash
$ python manage.py test prompts.tests.test_nsfw_preflight
Ran 6 tests in 0.043s
OK

$ python manage.py test prompts.tests.test_bulk_generator_views
Ran 158 tests in 439.164s
OK

$ python manage.py test prompts.tests.test_bulk_generation_tasks
Ran 78 tests in 108.734s
OK

$ python manage.py test prompts.tests.test_xai_provider
Ran 25 tests in 0.223s
OK
```

Full suite results filled post-gate.

---

## Section 10 — Commits

*Hash filled in post-commit; rides into Session 173-D docs commit per
Memory Rule #17.*

| Hash | Message |
|------|---------|
| `e06ab5c` | feat(moderation): NSFW pre-flight v1 — provider-aware ProfanityWord + advisory keyword lists (Session 173-B) |

---

## Section 11 — What to Work on Next

1. **Run Spec 173-C** (chip icon + placeholder content policy page)
   immediately — independent file surface (sprite SVG, JS chip rendering,
   new template/view/URL), can run in series.
2. **Full test suite gate** after 173-C — commit gate for all three
   code specs.
3. **Frontend wire-up follow-up (P2):** add one line to
   `bulk-generator-generation.js` validate POST body to send
   `model_identifier`. Trivial change; activates Tier 2 in production.
4. **Mateo runs the seed command** after deploy:
   ```
   python manage.py seed_provider_advisory_keywords --dry-run
   python manage.py seed_provider_advisory_keywords
   ```
   Tunes via `/admin/prompts/profanityword/`.
5. **Future P3 candidates** (from agent reviews):
   - Cross-reference `affected_providers` values against
     `GeneratorModel.model_identifier` for typo detection
   - Add caching layer to `check_text_with_provider` Tier 2 path
   - Read display names from `GeneratorModel` at message-format time
   - Move `validate_prompts` into `api_start_generation` as
     defense-in-depth gate (pre-existing security gap noted in Section 5)
