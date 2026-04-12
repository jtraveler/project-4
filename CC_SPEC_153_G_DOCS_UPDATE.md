# CC_SPEC_153_G_DOCS_UPDATE.md
# End of Session 153 — Documentation Update

**Spec Version:** 1.0
**Date:** April 2026
**Session:** 153
**Type:** Docs — commits immediately per protocol v2.2
**Agents Required:** 2 minimum

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — docs gate rule applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **Per v2.2:** if any agent scores below 8.0 → fix and re-run. No projected scores.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Current test count
python manage.py test --verbosity=0 2>&1 | tail -3

# 2. Find Session 152 entry in changelog to insert after
grep -n "Session 152\|Session 153" CLAUDE_CHANGELOG.md | head -5

# 3. Current version in CLAUDE.md
grep -n "Version\|4\.4" CLAUDE.md | head -5

# 4. Current migration count
ls prompts/migrations/*.py | wc -l

# 5. PROJECT_FILE_STRUCTURE.md current state
grep -n "migration\|session\|version\|4\." PROJECT_FILE_STRUCTURE.md | head -10

# 6. Check if Session 153 already partially documented
grep -n "Session 153\|153-A\|153-B" CLAUDE.md CLAUDE_CHANGELOG.md | head -10
```

---

## 📁 CHANGES REQUIRED

### `CLAUDE_CHANGELOG.md`

Add Session 153 entry after Session 152:

```markdown
### Session 153 — April 2026

**Focus:** GPT-Image-1.5 upgrade, pricing accuracy, error messaging,
progress bar accuracy, and billing UX

**Specs:** 153-A through 153-F

**Key outcomes:**
- GPT-Image-1.5 fully deployed across all 7 production files + migration 0080.
  Both `images.edit()` and `images.generate()` API paths upgraded. All
  metadata (choices, defaults, tasks, template) updated. 2 new choice tests.
- IMAGE_COST_MAP updated to GPT-Image-1.5 pricing (20% reduction). Propagated
  to all 10 affected files including Python fallbacks, JS COST_MAP, template
  strings, and 22 test assertions.
- Per-image progress bar restart on page refresh fixed via `generating_started_at`
  timestamp on GeneratedImage (migration 0081). Negative CSS animation-delay
  gives accurate elapsed-time position. `isFirstRenderPass` flag removed.
- Billing hard limit error now shows actionable message with OpenAI billing URL
  instead of misleading "Invalid request" (153-D).
- Full billing error chain fixed end-to-end: `_sanitise_error_message` now
  emits `'Billing limit reached'`, Q-filter catches billing errors, JS map
  entry added (153-E).
- `'Quota exceeded'` frontend message no longer tells BYOK users to "contact
  admin" — now directs to OpenAI billing page.
- `I.COST_MAP` in `bulk-generator.js` (input page sticky bar) updated to
  GPT-Image-1.5 prices — was missed by 153-C (153-F).
```

### `CLAUDE.md`

1. **Update version** to `4.43`
2. **Update test count** to `1221`
3. **Add Sessions 153-A through 153-F** to Recently Completed table
4. **Add Key Learnings** (add after existing entries):

```markdown
- **Session 153 — JS cost maps can drift from Python constants:** `I.COST_MAP`
  in `bulk-generator.js` is a client-side copy of `IMAGE_COST_MAP` in
  `constants.py`. When 153-C updated the Python constant, the JS copy was
  missed. Fix pending in 153-J: `get_image_cost()` helper + template context
  injection so JS prices are generated from Python at render time.
- **Session 153 — CC agent name substitution:** CC consistently substitutes
  agent names (e.g. `@backend-security-coder` for `@django-security`). Run
  instructions now include a hard rule: "Use EXACT agent names. Do not
  substitute." If an agent is unavailable, stop and report.
- **Session 153 — Negative CSS animation-delay for elapsed-time accuracy:**
  CSS `animation-delay: -Ns` starts an animation as if it began N seconds
  ago. Used in 153-F to show per-image progress bars at their correct elapsed
  position on page refresh — no fake restart, no 0% bar.
- **Session 153 — `billing_hard_limit_reached` arrives as `BadRequestError`
  (400), not `RateLimitError` (429):** The existing `insufficient_quota`
  handler in `RateLimitError` does not catch billing limit hits. A separate
  check in `BadRequestError` is required (153-D).
```

5. **Update bulk generator status** — mark Vision "Prompt from Image",
   GPT-Image-1.5 upgrade, pricing update, and progress bar fix as complete.

6. **Update Current Blockers** — remove any items resolved this session.
   Add: "`needs_seo_review` not set on bulk-created pages — fix in 153-H."

### `PROJECT_FILE_STRUCTURE.md`

- Update date to current date
- Update session reference to 153
- Update migration count to 0081
- Update test count to 1221
- Add `GeneratedImage.generating_started_at` field note
- Update version to 4.43

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Session 153 changelog entry accurate and complete
- [ ] All 6 specs (A-F) reflected in CLAUDE.md Recently Completed table
- [ ] Version updated to 4.43
- [ ] Test count updated to 1221
- [ ] 4 new Key Learnings added
- [ ] `generating_started_at` field mentioned in PROJECT_FILE_STRUCTURE.md
- [ ] Migration 0080 and 0081 both noted
- [ ] Agent substitution rule documented in Key Learnings
- [ ] `python manage.py check` returns 0 issues

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. Both must score 8.0+.

### 1. @docs-architect
- Verify all key outcomes are present and accurate
- Verify Key Learnings are technically correct and useful
- Verify agent substitution note is documented clearly
- Verify no duplicate entries added
- Rating requirement: **8+/10**

### 2. @api-documenter
- Verify `generating_started_at` documented correctly
- Verify migration numbers match actual migration files
- Verify pricing values referenced in changelog are correct
- Verify technical accuracy of all new Key Learnings
- Rating requirement: **8+/10**

---

## 💾 COMMIT MESSAGE

```
END OF SESSION DOCS UPDATE: session 153 — GPT-Image-1.5, pricing, error messaging, progress bar
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_153_G_DOCS_UPDATE.md`

---

**END OF SPEC**
