# CC_RUN_INSTRUCTIONS_SESSION_160.md
# Session 160 — Run Instructions for Claude Code

**Date:** April 2026
**Specs in this session:** 7 specs (5 code + 1 data migration + 1 docs)
**Full test suite runs:** 1 (after all code specs agent-approved, before commits)

**Trigger phrase:**
```
Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then read
CC_RUN_INSTRUCTIONS_SESSION_160.md, then run these specs in order:
CC_SPEC_160_A_PROFANITY_ERROR_UX.md,
CC_SPEC_160_B_QUALITY_DISABLED_GRID.md,
CC_SPEC_160_C_PER_PROMPT_COST_FIX.md,
CC_SPEC_160_D_FULL_DRAFT_AUTOSAVE.md,
CC_SPEC_160_E_PRICING_ACCURACY.md,
CC_SPEC_160_F_CLOUDINARY_MIGRATION.md,
CC_SPEC_160_G_DOCS_UPDATE.md
```

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE (verified April 2026)

1. **Profanity error working but needs UX polish** — triggered word shown but not
   styled distinctively, no link to the specific prompt box like other errors have

2. **Quality section hidden for non-quality models** — need to restore the
   disabled/greyed approach with value locked to "High". Grid layout breaks
   when quality is hidden (Dimensions spans full width)

3. **Per-prompt cost not updating on quality change** — labels show 1K/2K/4K
   correctly but cost in each box doesn't respond to per-row quality changes

4. **Autosave too narrow** — currently saves model/quality/aspect only. Need
   full session persistence: all master settings including toggles + Images per
   Prompt + all per-prompt box settings (AI direction toggle, AI direction text,
   dropdowns, prompt text). Persists after generation. Cleared only on explicit
   reset. Uses existing `bulk-generator-autosave.js` file.

5. **Pricing rounding on results page** — $0.067 shows as $0.07. Template
   filter rounding issue. Fix to full precision everywhere.

6. **Cloudinary migration** — 36 prompts + videos still on Cloudinary. Need
   management command to download from Cloudinary and upload to B2. Must be
   verified before code removal.

7. **Docs** — Session 160 changelog, named draft feature planning notes,
   localStorage ↔ server-side draft relationship, tier versioning design decision.

---

## 📋 SPEC QUEUE

| Order | Spec | Type | Files | Risk |
|-------|------|------|-------|------|
| **1** | `CC_SPEC_160_A_PROFANITY_ERROR_UX.md` | Code | `bulk_generation.py`, template/JS | ✅ Safe |
| **2** | `CC_SPEC_160_B_QUALITY_DISABLED_GRID.md` | Code | `bulk-generator.js`, CSS | 🟠 High Risk |
| **3** | `CC_SPEC_160_C_PER_PROMPT_COST_FIX.md` | Code | `bulk-generator.js` | 🟠 High Risk |
| **4** | `CC_SPEC_160_D_FULL_DRAFT_AUTOSAVE.md` | Code | `bulk-generator-autosave.js`, `bulk-generator.js` | 🔴 Critical |
| **5** | `CC_SPEC_160_E_PRICING_ACCURACY.md` | Code | results template, view | 🟡 Caution |
| **6** | `CC_SPEC_160_F_CLOUDINARY_MIGRATION.md` | Data Migration | new management command | 🔴 Critical |
| **7** | `CC_SPEC_160_G_DOCS_UPDATE.md` | Docs | CLAUDE.md, changelog | ✅ Safe |

---

## ⚠️ FILE BUDGET

**`bulk-generator.js`** — Specs 160-B, 160-C, and 160-D all touch this file:
- 160-B must commit before 160-C starts
- 160-C must commit before 160-D starts
- Re-read full file before every str_replace — 🟠 High Risk minimum

**`bulk-generator-autosave.js`** — Spec 160-D primary file:
- 376 lines currently — 🟡 Caution tier
- Investigation-first: read full file before any changes

**`tasks.py` / management command** — Spec 160-F:
- New file: `prompts/management/commands/migrate_cloudinary_to_b2.py`
- 🔴 Critical — data migration touching production content

---

## ⚠️ ORDERING RULES

- **160-B → 160-C → 160-D** — all touch `bulk-generator.js`, strict order
- **160-F (Cloudinary migration) is code-spec gated** — runs after full suite
  passes but **commits immediately** as a management command (no production
  data changed until developer manually runs the command on Heroku)
- **Developer must manually verify migration on Heroku** before any Cloudinary
  code removal (that comes in a future session)
- **160-G runs last**

---

## ⛔ FULL SUITE GATE

```bash
python manage.py test
```
Expected: 1270+ tests, 0 failures, 12 skipped.

---

## 💾 COMMIT ORDER

```
1. fix(validation): profanity error — bold word, link to prompt box
2. fix(ui): quality section disabled/greyed with High locked, grid fixed
3. fix(ui): per-prompt cost updates on quality change
4. feat(ui): full draft autosave — all settings + per-prompt boxes
5. fix(results): pricing shows full precision, no rounding
6. feat(migration): Cloudinary → B2 migration management command
7. END OF SESSION DOCS UPDATE: session 160
```

---

## ⛔ HARD RULES

1. **160-B/C/D strict commit order** — same file, re-read before each spec
2. **160-D is investigation-first** — read `bulk-generator-autosave.js` fully
   before writing any code
3. **160-F creates a management command only** — does NOT run it automatically.
   Developer runs it manually on Heroku after reviewing the code.
4. **160-F does NOT remove any Cloudinary code** — migration only. Code removal
   is a separate future session after migration is confirmed.
5. **Minimum 6 agents on every spec including 160-F**
6. **@technical-writer mandatory on every report**
7. **Agent average includes ALL agents including capped ones**

---

## 🔔 DEVELOPER TESTING AFTER SESSION

1. Enter a profanity word → error shows word **bold/italic**, **link to prompt box** ✅
2. Select Flux Dev → quality shows **disabled/greyed**, locked to **High** ✅
3. Select NB2 → change per-box quality → cost **updates immediately** ✅
4. Set all settings → hard refresh → **everything restored** ✅
5. Add AI Direction text to prompt box → refresh → **text still there** ✅
6. Generate → results page shows **$0.067** not **$0.07** for NB2 1K ✅
7. Run migration command on Heroku → verify B2 images load ✅

---

**END OF RUN INSTRUCTIONS**
