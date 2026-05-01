# REPORT_173_E_VALIDATE_WIRE_UP

## Frontend Wire-Up of model_identifier in api_validate_prompts (closes 173-B Remaining Issue)

**Spec:** `CC_SPEC_173_E_VALIDATE_WIRE_UP.md`
**Status:** COMPLETE — single-spec cluster, single commit, all 11 sections filled
**Cluster shape (Memory Rule #15):** SINGLE-SPEC

---

## Section 1 — Overview

Closes REPORT_173_B Section 5 P2 deferred item. Until this ships,
Tier 2 advisory pre-flight runs with `provider_id=''` and silently
never fires for any user — every NSFW prompt that should have been
caught by Tier 2 advisory passes through to the provider, risking
API account suspension. After ship, the entire 173-B
account-protection feature is live in production.

**Step 0 finding:** the backend wire-up was ALREADY DONE in 173-B
(commit `e06ab5c`, `prompts/views/bulk_generator_views.py:267-275`
already extracts `model_identifier` with isinstance defense + passes
to service). The only remaining gap was the frontend not sending
`model_identifier` in the validate POST body. Spec rewrote to
"frontend-only fix + 3 defensive tests on the existing backend
handler" once Step 0 confirmed backend was already in place.

---

## Section 2 — Expectations

| Success criterion | Status |
|---|---|
| Frontend `model_identifier` added to validate fetch body | ✅ Met |
| Backend handler already wired (Step 0 confirmed) | ✅ Pre-existing from 173-B |
| 3 defensive tests added (happy path, backward-compat, malformed) | ✅ Met |
| All new tests pass | ✅ Met (11/11 in ValidatePromptsAPITests) |
| `python manage.py check` passes | ✅ Met |
| CLAUDE.md Recently Completed row added | ✅ Met |
| CLAUDE_CHANGELOG.md entry added | ✅ Met |
| Deferred P2 closure marked | ✅ Met (header acknowledgment, no specific row existed) |
| Memory Rule #16 application cited | ✅ Met (changelog + CLAUDE.md row) |
| Memory Rule #17 single-commit pattern applied | ✅ Met (single commit shape) |
| Memory Rule #13 explicitly NOT applicable, documented | ✅ Met (code comment + changelog) |
| 3 agents ≥ 8.0/10, average ≥ 8.5 | ✅ Met (9.367/10) |

### Step 0 verbatim grep outputs

```bash
$ grep -n "JSON.stringify({ prompts: finalPrompts })\|urlValidate\|Validating prompts" static/js/bulk-generator-generation.js | head -10
93:        return fetch(I.urlValidateKey, {
908:            I.generateStatus.textContent = 'Validating prompts...';
911:            return fetch(I.urlValidate, {
914:                body: JSON.stringify({ prompts: finalPrompts }),

$ grep -n "I.settingModel" static/js/bulk-generator-generation.js | head -5
460:        I.settingModel.value = 'black-forest-labs/flux-schnell';
866:        var _initOpt = I.settingModel
867:            ? I.settingModel.options[I.settingModel.selectedIndex]
994:                    var selectedOpt = I.settingModel
995:                        ? I.settingModel.options[I.settingModel.selectedIndex]

$ sed -n '255,280p' prompts/views/bulk_generator_views.py
... (showed existing 173-B wire-up at lines 267-275 — already extracts model_identifier with isinstance defense, already passes provider_id= to service.validate_prompts)

$ grep -n "def validate_prompts\|provider_id\|check_text_with_provider" prompts/services/bulk_generation.py | head -10
87:    def validate_prompts(
88:        self, prompts: list[str], provider_id: str = ''
... (confirmed post-173-B signature: provider_id='' default; Tier 1 + Tier 2 layered)
```

**Step 0 verified the post-173-B `validate_prompts(prompts, provider_id='')` signature is in place** — the spec's CRITICAL note about stopping if signature differed was satisfied. Backend was already extracting and passing `model_identifier`. Reduced spec scope to frontend + tests only.

---

## Section 3 — Changes Made

### `static/js/bulk-generator-generation.js` (1 str_replace at line 911)

Added `model_identifier: modelIdentifier` to the validate fetch body,
sourced from `(I.settingModel && I.settingModel.value) || ''`. Defensive
empty-string fallback covers the edge case where `I.settingModel` is
somehow not initialised. 7-line inline comment explains the 173-E
provenance, the 173-B-defined backward-compat contract, and the
explicit Memory Rule #13 non-applicability (empty-string fallback is
documented contract, not silent corruption).

Total diff: ~12 lines (1 new variable declaration + 1 comment block + 1
expanded JSON.stringify body).

### `prompts/tests/test_bulk_generator_views.py` (1 str_replace adding 3 tests)

Added 3 new test methods to the existing `ValidatePromptsAPITests` class
between `test_non_string_prompts_returns_400` and the next class
declaration:

1. **`test_173e_validate_passes_model_identifier_to_service`** — happy
   path. Sends `model_identifier='google/nano-banana-2'`, asserts
   `mock_validate.assert_called_once_with(['a clean test prompt'], provider_id='google/nano-banana-2')`.

2. **`test_173e_validate_defaults_model_identifier_to_empty`** —
   backward-compat. Omits the field entirely, asserts
   `provider_id=''` passed to service.

3. **`test_173e_validate_coerces_malformed_model_identifier_to_empty`**
   — defensive boundary. Iterates 5 malformed values
   (`None, 42, ['gpt-image-1.5'], {'value': 'x'}, True`), each in a
   fresh `with patch(...)` context to avoid `mock.reset_mock`
   complications. Asserts each coerces to empty string at the HTTP
   boundary.

All 3 tests use the existing `setUp` pattern (login as `staffuser`)
and the existing class URL (`self.url = reverse('prompts:api_bulk_validate_prompts')`).

### `CLAUDE.md` (3 str_replaces)

1. **New Recently Completed row** above Session 173-D row (line 78).
   Comprehensive single-row entry documenting: Step 0 finding (backend
   already done), one-line frontend fix, 3 defensive tests, Memory
   Rules #16/#17 application, cluster shape SINGLE-SPEC.

2. **Deferred P2 section header acknowledgment** above the existing
   table — explicit closure note for the model_identifier wire-up
   item from REPORT_173_B Section 5 (no specific row existed in the
   table; the deferred item was tracked only in the 173-B report).

3. **Version footer** 4.71 → 4.72 with full Session 173-E follow-on
   summary (~10 lines). The prior 4.71 version footer (Session 173
   main cluster) preserved below as historical-reference comment lines
   for traceability.

### `CLAUDE_CHANGELOG.md` (1 str_replace adding 1 entry)

Added 1 new entry above the existing Session 173-D entry (line 35).
Multi-paragraph: Outcome → Step 0 finding → Frontend fix details →
3 tests → Memory Rule applications → Files modified → Test count →
Cluster shape → Agent ratings (filled post-review).

### `PROJECT_FILE_STRUCTURE.md` (2 str_replaces)

- Last Updated: `May 1, 2026 (Sessions 163–173)` →
  `May 1, 2026 (Sessions 163–173, +173-E follow-on)`
- Total Tests: `1408` → `1411`
- Current Phase narrative: added "Tier 2 advisory pre-flight
  activated end-to-end in Session 173-E"

---

## Section 4 — Issues Encountered and Resolved

**Issue (positive):** Step 0 revealed the backend wire-up was already
in place from 173-B. The spec was drafted assuming both frontend AND
backend gaps existed.
**Root cause:** The spec author worked from REPORT_173_B Section 5's
description of the deferred item, which mentioned both frontend and
backend handler gaps. But REPORT_173_B Section 4 Issue 2 documented
that CC's actual 173-B implementation already included the backend
wire-up at `bulk_generator_views.py:267-275`. The spec's CRITICAL
warning at Section 2 (verify the actual current state via Step 0)
caught this correctly.
**Fix applied:** No fix needed — the missing piece was simply the
frontend POST body. Reduced scope from "2 edits + 3 tests" to
"1 frontend edit + 3 tests + folded docs". All 3 tests still added
because they verify the END-TO-END wire-up contract via the view
layer, regardless of which session implemented which half.
**File:** `prompts/views/bulk_generator_views.py:267-275` —
verified pre-existing from 173-B commit `e06ab5c`. NOT modified in
this spec.

### Memory Rule #13 explicitly NOT applicable (per spec section 11)

The spec section 11's DO list says: "Document in REPORT Section 4
why Memory Rule #13 is NOT applicable here." Memory Rule #13 requires
`logger.warning` on silent-fallback paths. The empty-string fallback
in this spec (`(I.settingModel && I.settingModel.value) || ''`) is
the **documented 173-B contract** — when `provider_id=''`, the
service correctly falls back to Tier 1 universal-only check. This
is NOT a silent corruption path; it's the explicitly-designed
backward-compat path. No `logger.warning` required.

The same reasoning applies to the backend's existing isinstance
defense (`if not isinstance(model_identifier, str): model_identifier
= ''`) — the empty-string coercion is intentional defense at the
HTTP boundary, not silent corruption.

Documented inline in:
1. The frontend code comment at `bulk-generator-generation.js:911-918`
2. The CLAUDE_CHANGELOG.md 173-E entry (Memory Rule #13 paragraph)
3. The CLAUDE.md Recently Completed row

### Memory Rule #16 application

Mateo raised this deferred item before any Session 174 work began,
which is exactly the rule's intended cadence ("at cluster-planning
start, surface relevant deferred items"). The single-spec cluster
shape is itself the closure: the deferred item gets its own
focused commit + report rather than being deferred indefinitely
or rolled into a larger Session 174 cluster.

### Memory Rule #17 single-commit pattern

Single-spec clusters where docs and code ship in one commit don't
need a separate backfill commit because anyone reading git log
sees the same commit hash for both. The CHANGELOG entry uses
"see commit log for hash" phrasing rather than `commit pending` to
avoid the chicken-and-egg of self-referencing. The CLAUDE.md row
uses "Commit: see git log" with the same intent.

This is an explicit application of Memory Rule #17's elaboration
in the run instructions Section 6: "for single-spec clusters
where docs and code ship in one commit, the self-reference
backfill is automatic."

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met. The 173-B
account-protection feature is fully active end-to-end in production
once this commit deploys.

The pre-existing security gap from REPORT_173_B Section 5
(`api_start_generation` doesn't call `validate_prompts` server-side)
remains a separate P3 item. NOT closed by this spec — it's a
distinct latent concern. Mitigated currently by `@staff_member_required`
decorator. Will become higher-priority before Phase SUB launch when
bulk generation opens to non-staff users.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** @frontend-developer noted the 7-line inline JS comment
explaining Memory Rule #13 non-applicability is unusually verbose.
**Impact:** Cosmetic — adds cognitive overhead for future readers
who don't need to know the Memory Rule reasoning at the call site.
**Recommended action:** Acceptable for now because the spec's DO/DO
NOT list explicitly required the Memory Rule #13 reasoning to be
documented in the code (spec section 8 PRE-AGENT SELF-CHECK item).
If future readers find the comment too long, it can be tightened to
2-3 lines and the rationale moved entirely to this REPORT Section
4. P3 candidate — not blocking.

**Concern:** Three Memory Rule applications in one ~12-line code
diff feels like ceremony heavy relative to the actual change size.
**Impact:** None operationally — the rules genuinely apply.
**Recommended action:** None. The ceremony reflects the tight
process discipline established in 171-D + 172-D + 173-D, which
addresses real failure patterns. Single-spec clusters benefit from
the same discipline as multi-spec clusters; the alternative
("skip the docs because it's a small change") is exactly how
silent accumulation patterns developed in the first place.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.5/10 | Frontend edit at correct location (line 911 urlValidate POST, NOT urlValidateKey/urlPreparePrompts/urlStart). Defensive pattern correct. `var` declaration matches ES5 file style. `.then(...)` chain untouched. Minor cosmetic note: 7-line inline comment is verbose. | Documented in Section 6 |
| 1 | @django-pro | 9.2/10 | Mock path correct (`prompts.views.bulk_generator_views.service.validate_prompts`). assert_called_once_with(positional, provider_id=...) correctly enforces keyword-arg form. Test 3's per-iteration fresh `with patch(...)` context cleaner than spec's `mock.reset_mock()` suggestion. `True` correctly tests bool-isinstance-vs-str defense. View-layer scope only (service mocked) — properly bounded. | N/A |
| 1 | @code-reviewer | 9.4/10 | Scope discipline excellent: backend NOT in diff (Step 0 finding correctly applied; spec descoped). Memory Rule #16 application explicit in CHANGELOG + CLAUDE.md header. Memory Rule #17 single-commit pattern (`see commit log for hash` phrasing) avoids chicken-and-egg. Memory Rule #13 non-applicability documented in BOTH source comment AND changelog. PFS counts synced. | N/A |
| **Average** | | **9.367/10** | | **Pass ≥ 8.5** |

All 3 agents ≥ 8.0. Average 9.367 ≥ 8.5 threshold. No re-run required.

---

## Section 8 — Recommended Additional Agents

**@accessibility-expert:** N/A — this spec changes a fetch body, not
any user-visible UI. No accessibility surface.

**@security-auditor:** Could have evaluated whether `model_identifier`
sent in the POST body is a new injection surface. Quick analysis: the
backend uses `data.get('model_identifier', '')` + isinstance defense
+ passes as `provider_id=` keyword arg to a Python function that
filters `ProfanityWord.objects.filter(... block_scope='provider_advisory')`
then iterates the queryset in Python with `provider_id in
w['affected_providers']`. No SQL injection (no raw query), no JSON
injection (Django's JSONField is read-only here). Out of scope but
non-concerning.

For the spec's narrow scope (frontend fetch body addition + 3 view
tests), the 3 chosen agents covered material concerns adequately.

---

## Section 9 — How to Test

### Closing checklist (Memory Rule #14)

**Migrations:** N/A — no model field changes in this spec.

**Manual browser tests (max 2 at a time, with explicit confirmation between):**

Round 1 (the activation test):
1. Submit a bulk job with prompt containing `'topless'` + Nano Banana 2
   selected → verify pre-flight rejects with provider-advisory message
   ("Content advisory for Nano Banana 2: prompt contains 'topless'…").
   This is the test that confirms 173-B's full chain is now live.
2. Submit the SAME prompt but with Flux Schnell selected → verify
   pre-flight ALLOWS submission (Flux is permissive, no advisory
   keywords for that model).

Round 2 (regression check):
3. Submit a bulk job with a prompt that ONLY contains universal-block
   words (not advisory) → verify it rejects regardless of provider.
   Confirms 173-E didn't break Tier 1.
4. Submit a bulk job with a clean prompt + any provider → verify it
   submits successfully. Confirms backward-compat for legitimate use.

**Failure modes to watch for:**
- Round 1 Test 1 fails (advisory not firing) → check Network tab in
  DevTools, confirm the validate POST body includes `"model_identifier":
  "..."`. If yes, backend wire-up gap; if no, frontend wire-up gap.
  Backend was already done in 173-B so frontend is the likely
  suspect.
- Round 1 Test 2 fails (Flux rejected) → ProfanityWord seed has a
  Flux-affected entry that shouldn't exist; check
  `/admin/prompts/profanityword/` filter `block_scope='provider_advisory'`
  for any entry with Flux-prefixed `affected_providers`.
- Round 2 fails → universal-block flow broken (Tier 1) — would have
  been caught by existing 8 ValidatePromptsAPITests; check those.

**Backward-compatibility verification:**
- Existing universal-block ProfanityWord entries — unchanged behavior
  (Tier 1 fires regardless of provider_id; existing test
  `test_universal_block_fires_with_no_provider` from 173-B still passes)
- Existing Flux Schnell jobs (no advisory keywords for Flux) — submit
  successfully (no false-positive blocks)
- Frontend without 173-E (e.g. cached browser) — backend defaults
  `provider_id=''`, falls back to Tier 1 universal-only — same
  behavior as pre-173-B. No regression for users on cached JS until
  they hard-refresh.

**Automated test results:**

```bash
$ python manage.py test prompts.tests.test_bulk_generator_views.ValidatePromptsAPITests -v 2 2>&1 | tail -5
Ran 11 tests in 37.643s
OK

$ python manage.py check
System check identified no issues (0 silenced).
```

Full suite not re-run — single-spec cluster doesn't require it per
spec section 5 ("no full-suite gate needed for single-spec cluster").
The 3 new tests are isolated to the view layer (mocked service); the
existing 8 tests in `ValidatePromptsAPITests` still pass; no other
files were touched. Risk of regression elsewhere is minimal.

---

## Section 10 — Commits

*Single commit per Memory Rule #17 single-commit pattern. Hash is in
the git log as the most-recent commit at session end.*

| Hash | Message |
|------|---------|
| see git log | fix(bulk-gen): wire model_identifier through api_validate to activate 173-B Tier 2 advisory pre-flight (Session 173-E) |

---

## Section 11 — What to Work on Next

1. **Mateo's post-deploy verification** (Memory Rule #14 closing
   checklist): Round 1 (activation test) + Round 2 (regression
   check). 4 tests total, max 2 at a time with explicit confirmation
   between.
2. **If Round 1 + 2 all pass:** Session 173-E ships clean. The
   173-B account-protection feature is fully active in production.
   Move to Session 174.
3. **Session 174 candidates** (per Memory Rule #16 — review at
   cluster planning start):
   - Modal persistence on bulk publish refresh (Deferred P2)
   - IMAGE_COST_MAP per-model restructure / Scenario B1 (Deferred P2)
   - Reset Master + Clear All Prompts UX (Deferred P2 — pending
     `bulk-generator-autosave.js` upload)
4. **Pre-existing security gap remains as P3:** `api_start_generation`
   doesn't call `validate_prompts` server-side. Will become higher-
   priority before Phase SUB launch when bulk generation opens to
   non-staff users.
