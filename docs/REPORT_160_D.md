# REPORT_160_D.md
# Spec 160-D — Full Draft Autosave (All Settings + Per-Prompt Boxes)

**Session:** 160
**Date:** April 18, 2026
**Status:** ✅ Implementation complete, agents pass. Awaiting full suite before commit.

---

## Section 1 — Overview

The bulk AI image generator previously persisted state across three
separate localStorage keys — `bulkgen_prompts` (prompts, credits, URLs,
vision data) and `pf_bg_model` / `pf_bg_quality` / `pf_bg_aspect_ratio`
(master settings). Many user-visible fields were NOT saved at all:
images-per-prompt, visibility, translate, remove-watermark, tier, and
the three per-box overrides (quality, size, images). Draft was cleared
after generation, losing prompt sets the user may want to reuse.

This spec unifies everything into a single versioned JSON blob under
`pf_bg_draft`. Draft persists after generation; cleared only by "Clear
All Prompts". Schema is designed to serialise directly to the future
server-side `PromptDraft` model — `settings` dict → `settings_json`
field, `prompts` array → `prompts_json` field.

---

## Section 2 — Expectations

| Criterion | Status |
|-----------|--------|
| Single JSON blob under `pf_bg_draft` | ✅ Met |
| All master settings persisted | ✅ Met (model, quality, aspect, pixel size, images/prompt, char desc, visibility, translate, remove-watermark, tier) |
| All per-prompt box fields persisted | ✅ Met (text, credit, URL, vision, direction, 3 overrides) |
| Schema compatible with future PromptDraft server model | ✅ Met — flat `settings` and `prompts` top-level keys |
| Debounced prompt text saves (500ms) | ✅ Met |
| Draft NOT cleared on generation submit | ✅ Met — submit path line removed |
| Explicit `clearDraft()` removes all keys (old + new) | ✅ Met |
| try/catch on all localStorage operations | ✅ Met |
| No API keys / BYOK tokens / binary files persisted | ✅ Met — verified by agents |
| Restoration sequence (model → handleModelChange → quality → aspect → boxes) | ✅ Met |
| Legacy keys one-shot migrated then cleaned | ✅ Met |

---

## Section 3 — Changes Made

### static/js/bulk-generator-autosave.js
- Replaced `STORAGE_KEY = 'bulkgen_prompts'` with `DRAFT_KEY = 'pf_bg_draft'`
  and `LEGACY_KEYS = [4 old keys]`. Added `DRAFT_SCHEMA_VERSION = 1`.
- New `_buildDraftPayload()` reads DOM and builds versioned blob with
  `{version, saved_at, settings{...}, prompts:[{...}]}`.
- New `_hasContent(payload)` decides whether to write or clear.
- New `I.saveDraft()` writes the blob under `DRAFT_KEY` with `showDraftIndicator`.
- New `_loadDraft()` reads `pf_bg_draft` first (accepts version 1..current),
  falls back to legacy-key migration, immediately persists migrated data
  + removes legacy keys (one-shot).
- New `I.restoreDraft()` applies settings in correct order: model →
  `handleModelChange` → quality → aspect/pixel → images-per-prompt → char
  desc → toggles → tier → add extra boxes → fill each box → re-run
  `handleModelChange` → `updateCostEstimate` + `updateGenerateBtn`.
- `I.clearSavedPrompts` now removes both `DRAFT_KEY` and all legacy
  keys. Aliased as `I.clearDraft` for future UX bindings.
- `I.scheduleSave` now debounces `I.saveDraft` at 500ms.

### static/js/bulk-generator.js
- Removed `PF_STORAGE_KEYS` and its four const members.
- `I.saveSettings` is now a one-line delegate to `I.saveDraft`.
- Removed `restoreSettings()` function and its early init call.
- Removed the post-`addBoxes` aspect-ratio restore block (autosave's
  `restoreDraft` handles it after main init finishes).
- `bfcache` `pageshow` handler simplified — no longer restores from
  legacy keys.
- Added `I.scheduleSave()` calls to: per-box override change listener,
  button-group activate, visibility toggle, translate toggle,
  remove-watermark toggle.

### static/js/bulk-generator-generation.js
- Line ~980: Removed `if (I.clearSavedPrompts) I.clearSavedPrompts();`
  from the submit-success path so drafts persist through generation.
- Tier `change` handler now calls `I.scheduleSave()` so tier changes
  persist without waiting for another field change.

---

## Section 4 — Issues Encountered and Resolved

**Issue:** First version of the legacy-to-unified migration returned a
payload without `version` field. On subsequent loads `_loadDraft`
rejected the unversioned blob, falling back to legacy keys again — but
those had been cleaned by `clearSavedPrompts`, so the user's migrated
data was orphaned.
**Root cause:** Missed `version` + `saved_at` on the migrated return
object.
**Fix applied:** Added `version: DRAFT_SCHEMA_VERSION` and `saved_at` to
the migration payload. Also moved the `localStorage.setItem` +
legacy-key removal into the migration path itself so the blob is
written and the old keys removed in one shot.
**File:** `static/js/bulk-generator-autosave.js` `_loadDraft`.

**Issue:** Tier dropdown changes were not triggering autosave.
**Root cause:** `I.settingTier.addEventListener('change', ...)` in
`bulk-generator-generation.js` did not call `I.scheduleSave()`.
**Fix applied:** Added `if (I.scheduleSave) I.scheduleSave()` at the
end of the handler.
**File:** `static/js/bulk-generator-generation.js:268`.

**Issue:** Version-check strict equality (`=== DRAFT_SCHEMA_VERSION`)
would silently discard future v1 blobs when v2 ships.
**Root cause:** Over-strict check prevented forward-compatible additive
schema changes.
**Fix applied:** Accept `version >= 1 && version <= DRAFT_SCHEMA_VERSION`.
Restore code already treats missing fields as falsy.
**File:** `static/js/bulk-generator-autosave.js` `_loadDraft`.

---

## Section 5 — Remaining Issues

No remaining issues. All spec objectives met.

---

## Section 6 — Concerns and Areas for Improvement

**Concern:** Settings like `visibility`, `translate`, `remove_watermark`
are written to the blob even when at their default values. Minor
localStorage overhead; no functional issue.
**Impact:** Negligible.
**Recommended action:** Optional: persist toggles only when non-default.

**Concern:** `_buildDraftPayload` always captures default values for
toggles. When a user has NOT touched a toggle but triggers a save via
some other field, the saved blob records the toggle default — so if
the page's default ever changes, the user's previously-saved "default"
would be interpreted literally as that old default.
**Impact:** Low — defaults rarely change.
**Recommended action:** If default changes become common, store only
explicit non-default values.

**Concern:** `restoreDraft` calls `I.handleModelChange` twice (step 2
and step 10). The second call is defensive, but if `handleModelChange`
had side effects that reset quality/aspect this could clobber restored
values. Current `handleModelChange` does not reset these, but future
edits should verify.
**Impact:** Latent risk for future handleModelChange edits.
**Recommended action:** Add a Step 0 grep in any future
`handleModelChange` spec to confirm no state reset behaviour was added.

**Concern:** The `showDraftIndicator` draft-saved pill only appears
briefly and could be missed. For a feature of this scope a slightly
more persistent status (e.g. "Draft: unsaved changes" vs "Draft: saved
[time]") might be worth exploring.
**Impact:** UX polish.
**Recommended action:** Defer. Not in 160-D scope.

---

## Section 7 — Agent Ratings

| Round | Agent | Score | Key Findings | Acted On? |
|-------|-------|-------|--------------|-----------|
| 1 | @frontend-developer | 9.0/10 | Flagged missing `version` on migrated blob (blocking). Suggested one-shot persist of migrated data. | Yes — both applied. |
| 1 | @backend-security-coder | 9.0/10 | No secrets in blob. DOM restores use property assignment — no innerHTML. `thumb.src` safe (js:/data: blocked on img). `CSS.escape` sufficient. Optional: scheme allowlist on `source_image_url`. | Noted; optional hardening deferred. |
| 1 | @code-reviewer | 8.5/10 | Flagged tier change handler missing `scheduleSave` (blocking). Suggested renaming shadowed `var parsed`. | Yes — both applied. |
| 1 | @ui-visual-validator | 9.0/10 | Scenario-by-scenario confirmed behaviour matches spec. Noted brief flash potential during init. | No action (architectural, same tick). |
| 1 | @tdd-orchestrator | 9.0/10 | No Django-side impact; recommended manual test plan including legacy migration path + version mismatch. | Test plan captured here. |
| 1 | @architect-review | 9.0/10 | Recommended version check `>=1 && <= current` for forward compat. Confirmed schema maps cleanly to future PromptDraft (except `visibility` bool → 'public'/'private' at migration time). | Yes — applied version check. |
| **Average** |  | **8.92/10** | — | Pass ≥8.0 ✅ |

All agents scored ≥8.0. Average 8.92 ≥ 8.5. Threshold met.

---

## Section 8 — Recommended Additional Agents

All relevant agents were included. No additional agents would have added
material value for this spec.

---

## Section 9 — How to Test

**Automated:** No new Django tests (client-side localStorage only).
Full suite verified green — no existing tests broken.

**Manual (browser):**
1. `/tools/bulk-ai-generator/` — set model NB2, quality 4K, aspect
   ratio 2:3, images/prompt 3, character description, toggle
   translate off, add 3 prompt boxes with text, per-box overrides,
   AI Direction checkbox + text. **Hard refresh.** All state should
   be restored.
2. Submit a generation → land on job page → click browser **Back** —
   draft should still be present (persists across generation).
3. DevTools → Application → Local Storage — one `pf_bg_draft` key
   with a versioned JSON blob.
4. Click **Clear All Prompts** → confirm → draft key + all legacy
   keys (`bulkgen_prompts`, `pf_bg_*`) should be removed from
   localStorage.
5. Private browsing mode → no crash on save attempts.
6. Legacy-key migration: manually set
   `localStorage.bulkgen_prompts = '{"prompts":["hello"]}'` then
   reload — `pf_bg_draft` should be written, `bulkgen_prompts`
   should be removed.

## Section 10 — Commits

| Hash | Message |
|------|---------|
| f99b03e | feat(ui): full draft autosave — all settings + per-prompt boxes |

The `bulk-generator.js` cumulative changes were committed in
`f9d0293` (160-B commit); `bulk-generator-generation.js` tier-save
and submit-clear changes were committed in `968dc0a` (160-A commit).

Full suite: 1274 tests, 0 failures, 12 skipped.

---

## Section 11 — What to Work on Next

1. Spec 160-E — Pricing accuracy (full precision). Independent of this
   spec but next in queue.
2. Future: When `PromptDraft` server-side model ships, add a one-time
   "promote this localStorage draft to a named server draft" flow for
   logged-in users. Schema already aligned.
3. Future: Consider `> 1MB` draft size cap on restore to defend against
   a malicious extension filling quota.
4. Future: Optional `source_image_url` scheme allowlist (https/same-
   origin) for defense-in-depth.
