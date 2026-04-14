# CC_RUN_INSTRUCTIONS_SESSION_154_BATCH4.md
# Session 154 Batch 4 — Run Instructions for Claude Code

**Date:** April 2026
**Session:** 154
**Specs in this batch:** 3 code specs
**Full test suite runs:** 1 (after all code specs agent-approved)
**Trigger phrase:**
`Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then
read CC_RUN_INSTRUCTIONS_SESSION_154_BATCH4.md, then run these specs in
order: CC_SPEC_154_N_JS_AND_PROVIDER_FIXES.md,
CC_SPEC_154_O_DISABLE_UX.md, CC_SPEC_154_P_RESULTS_PAGE.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE

The following specs have already been committed before this batch:
- ✅ **154-A** — GeneratorModel, UserCredit, CreditTransaction data layer
- ✅ **154-B** — Replicate + xAI providers
- ✅ **154-C** — Platform mode architecture
- ✅ **154-D** — Dynamic model selector, BYOK toggle, aspect ratio UI
- ✅ **154-E** — Docs update
- ✅ **154-F** — BYOK UX redesign + JS init order
- ✅ **154-G** — CSS skin updates
- ✅ **154-H** — updateCostEstimate/updateGenerateBtn forward reference
- ✅ **154-I** — handleModelChange init call moved after addBoxes(4)
- ✅ **154-J** — API key gate, aspect ratios, per-box overrides, credits display
- ✅ **154-K** — FileOutput crash, per-box quality hide, temp dollar display
- ✅ **154-L** — Character Reference Image — supports_reference_image field + migration
- ✅ **154-M** — CSS aspect ratio flex-wrap + border/background updates

**Issues confirmed from production testing that this batch fixes:**
- ❌ Flux 1.1 Pro shows "Generation failed" for NSFW instead of helpful message
- ❌ Per-box Dimensions override always hidden (regression from 154-J)
- ❌ "Prompt from Image" auto-enables AI Influence checkbox
- ❌ Generate button only activates when prompt text entered
- ❌ Aspect ratio defaults to 1:1, doesn't maintain selection when switching models
- ❌ Quality and Character Reference Image hide instead of disable
- ❌ Grok + Nano Banana should support reference images
- ❌ Results page shows technical model ID (google/nano-banana-2)
- ❌ Results page placeholder cards always render 1:1

---

## 📋 SPEC QUEUE

| Order | Spec | Key Files | Tier |
|-------|------|-----------|------|
| **1** | `CC_SPEC_154_N_JS_AND_PROVIDER_FIXES.md` | replicate_provider.py, bulk-generator.js, seed_generator_models.py | 🔴 Critical (tasks.py) |
| **2** | `CC_SPEC_154_O_DISABLE_UX.md` | bulk-generator.js, seed_generator_models.py | ✅ Safe |
| **3** | `CC_SPEC_154_P_RESULTS_PAGE.md` | bulk_generator_views.py, bulk_generator_job.html | ✅ Safe |

---

## ⚠️ DEPENDENCY ORDER

- **154-O depends on 154-L already committed** — uses `supports_reference_image` field
- **154-O depends on 154-N** — 154-N restores per-box dimensions visibility before 154-O adds disabled state
- **154-P is independent** — can run after N

---

## ⚠️ FILE BUDGET

**`bulk-generator.js`** — 🟡 Caution tier (1000+ lines):
- Spec N: 3 str_replace calls (dimensions fix, vision handler, updateGenerateBtn, aspect ratio)
- Spec O: 1 str_replace call (quality disable, ref image disable)
- **Total: 4 str_replace — use Python script if approaching limit**

**`prompts/services/image_providers/replicate_provider.py`** — ✅ Safe:
- Spec N: 1 str_replace (ModelError handler)

**`prompts/management/commands/seed_generator_models.py`** — ✅ Safe:
- Spec N: 2 value changes (default_aspect_ratio)
- Spec O: 2 value changes (supports_reference_image)
- Can combine into one run: `python manage.py seed_generator_models`

**`prompts/views/bulk_generator_views.py`** — ✅ Safe:
- Spec P: 2 str_replace calls (model_display_name, gallery_aspect)

**`prompts/templates/prompts/bulk_generator_job.html`** — ✅ Safe:
- Spec P: 1 str_replace (model display line)

---

## 🔁 EXECUTION SEQUENCE

### SPEC N — Provider + JS Fixes (5 changes)

1. Read spec fully
2. Step 0 greps — READ all outputs before any edits
3. Change 1: Add ModelError handler to `replicate_provider.py`
4. Change 2: Fix dimensions regression in `handleModelChange`
5. Change 3: Remove vision auto-enable of direction checkbox
6. Change 4: Update `updateGenerateBtn` to use box count
7. Change 5a: Add `preferredAspect` logic to `handleModelChange`
8. Change 5b: Update seed defaults + run seed command
9. Step 1 verification greps — ALL must pass
10. Agents: @frontend-developer, @code-reviewer
11. Both ≥ 8.0 → partial report, **DO NOT COMMIT**

---

### SPEC O — Disable UX + Seed Update (3 changes)

1. Read spec fully
2. Step 0 greps — confirm existing CSS disabled patterns
3. Change 1: Disable quality group (opacity + pointerEvents)
4. Change 2: Disable Character Reference Image with hint
5. Change 3: Update Grok + Nano Banana seed + run seed command
6. Step 1 verification greps — ALL must pass
7. Agents: @frontend-developer, @code-reviewer
8. Both ≥ 8.0 → partial report, **DO NOT COMMIT**

---

### SPEC P — Results Page Fixes (3 changes)

1. Read spec fully
2. Step 0 greps — read gallery_aspect view code and template
3. Change 1: Add model_display_name to view context
4. Change 2: Fix gallery_aspect for aspect ratio strings
5. Change 3: Update template to use model_display_name
6. Step 1 verification greps — ALL must pass
7. Agents: @code-reviewer, @tdd-orchestrator
8. Both ≥ 8.0 → partial report, **DO NOT COMMIT**

---

## ⛔ FULL SUITE GATE (after all 3 specs agent-approved)

```bash
python manage.py test
```

Expected: 1227+ tests, 0 failures, 12 skipped.

- Passes → fill Sections 9–10 on all reports → commit in order
- Fails → identify which spec caused regression → fix in-place

---

## 💾 COMMIT ORDER

```
1. fix(bulk-gen): ModelError NSFW message, dimensions regression, vision/direction, generate button, aspect ratio 2:3 default
2. fix(bulk-gen): disable Quality + Character Ref Image instead of hiding; Grok + Nano Banana support ref images
3. fix(bulk-gen): results page friendly model name + aspect ratio placeholders
```

---

## ⛔ HARD RULES

1. **154-L must be committed before 154-O** — `supports_reference_image` field required
2. **Dimensions override must ALWAYS be visible** — never hide `.bg-override-size` parentDiv
3. **Do NOT re-run migration** — 154-L already applied migration for `supports_reference_image`
4. **Run seed command once after both N and O changes** — or run twice (once after each)
5. **Disable means opacity + pointerEvents, not display:none** — this is the explicit requirement
6. **Per protocol v2.2** — both agents must score ≥ 8.0 before proceeding

---

## ⚠️ AGENT NAME SUBSTITUTIONS (Option B authorised)

- `@django-security` → `@backend-security-coder`
- `@tdd-coach` → `@tdd-orchestrator`
- `@accessibility-expert` → `@ui-visual-validator`

Document substitutions in Section 7 of each report.

---

## 🔔 DEVELOPER BROWSER CHECKS (required before commit)

**After Spec N:**
1. Select Flux Schnell → per-box Dimensions visible ✅
2. Toggle "Prompt from Image" to Yes → AI Influence NOT auto-checked ✅
3. Page loads → Generate button immediately active ✅
4. Set 2:3 on Grok → switch to Flux Dev → 2:3 maintained ✅

**After Spec O:**
5. Select Flux Dev → Quality master selector faded/disabled ✅
6. Select Flux Dev → Character Reference Image faded + hint shown ✅
7. Select Grok → Character Reference Image active (Grok supports it) ✅

**After Spec P:**
8. Go to any Flux job results page → Model shows "Flux Dev" not the ID ✅
9. Flux job generated with 2:3 → placeholder cards render portrait ✅

---

**END OF RUN INSTRUCTIONS**
