# CC_SPEC_160_G_DOCS_UPDATE.md
# End of Session 160 — Documentation Update

**Spec Version:** 1.0
**Session:** 160
**Type:** Docs — commits immediately per protocol v2.2
**Agents Required:** 2 minimum

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **This spec runs LAST** — after all code specs committed
3. All `[...]` placeholders must be filled with actual values
4. **Feature 4 (named drafts) section requires meaningful updates** —
   not just a version bump

---

## 📁 STEP 0

```bash
python manage.py test --verbosity=0 2>&1 | tail -3
git log --oneline -10
grep -n "^Version\|Feature 4\|localStorage\|PromptDraft\|draft.*tier" CLAUDE.md | head -20
```

---

## 📁 CHANGES REQUIRED

### `CLAUDE_CHANGELOG.md`

Add Session 160 entry:

```markdown
### Session 160 — April 2026

**Focus:** Profanity UX, quality disabled grid, per-prompt cost fix,
full draft autosave, pricing accuracy, Cloudinary migration command

**Specs:** 160-A through 160-G

**Key outcomes:**
- Profanity error: triggered word now bold/italic with link to prompt box
- Quality section restored to disabled/greyed (not hidden) for non-quality
  models, locked to "High". Grid layout fixed to two columns.
  Future-proofed for per-prompt model selection.
- Per-prompt cost: fixed root cause of quality change not updating cost
  display (root cause: [fill from 160-C report])
- Full draft autosave: single JSON blob under pf_bg_draft — saves all master
  settings, all per-prompt box content (text, AI direction, dropdowns).
  Persists after generation. Cleared only on explicit reset. Schema designed
  for future PromptDraft server-side migration.
- Pricing accuracy: full precision everywhere — $0.067 no longer rounds to
  $0.07. All models show correct decimal places.
- Cloudinary migration command: migrate_cloudinary_to_b2 management command
  created. Developer must run manually: --dry-run first, then --limit 3,
  then full run. Cloud name confirmed: dj0uufabo.
- [X] tests passing
```

### `CLAUDE.md`

1. **Update test count** to actual value
2. **Version → 4.51**
3. **Update date**
4. **Add Session 160 to Recently Completed**

5. **Update Feature 4: Save Prompt Draft section** — add the following:

```markdown
#### localStorage ↔ Server-Side Draft Relationship

The Session 160 full draft autosave (localStorage) is the anonymous/pre-login
foundation of the named draft system. The JSON schema stored under `pf_bg_draft`
was designed to be directly serialisable to the `PromptDraft` model:
- `settings` dict → `settings_json` field
- `prompts` array → `prompts_json` field

When Feature 4 ships, logged-in users will have their localStorage draft
automatically offered for promotion to a named server-side draft. Logged-out
users continue to use localStorage only.

#### Draft Versioning — Tier Design Decision

Draft versioning (save history) is a premium tier differentiator:

| Tier | Named Drafts | Version History | Sharing |
|------|-------------|-----------------|---------|
| Free | 1 (overwrite only) | No | No |
| Creator | 5 named drafts | No | No |
| Pro | Unlimited | Yes (last 10 versions) | No |
| Studio | Unlimited | Yes (unlimited) | Yes (team) |

**Status:** Design decision confirmed. Do not spec until Phase SUB
subscription tiers are implemented. Tier names and limits subject to
change based on pricing strategy.
```

6. **Update Cloudinary section** — note migration command exists,
   remind that Cloudinary code removal is a future session after migration
   confirmed on Heroku:

```markdown
#### Cloudinary Migration Status (Session 160)

Management command: `migrate_cloudinary_to_b2` created.
Run sequence:
1. `python manage.py migrate_cloudinary_to_b2 --dry-run`
2. `python manage.py migrate_cloudinary_to_b2 --limit 3` (verify 3 records)
3. `python manage.py migrate_cloudinary_to_b2` (full migration)

After confirmed working on Heroku:
- CloudinaryField → CharField migration (future session)
- Cloudinary code + package removal (after field migration)
- Remove CLOUDINARY_URL from Heroku config vars (after code removal)

Cloud name: dj0uufabo (corrected — old typo was dj0uufabot)
```

7. **Update report files list** — add REPORT_160_A through REPORT_160_G

### `PROJECT_FILE_STRUCTURE.md`

1. Update date
2. Add 7 new report files
3. Add `migrate_cloudinary_to_b2.py` to management commands table
4. Note `pf_bg_draft` localStorage key in `bulk-generator-autosave.js` entry
5. Note `bulk-generator-autosave.js` line count updated

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] All `[...]` placeholders filled ✓
- [ ] Feature 4 localStorage ↔ server-side relationship documented ✓
- [ ] Draft versioning tier table added ✓
- [ ] Cloudinary migration run sequence documented ✓
- [ ] Version 4.51 ✓
- [ ] Test count actual from Step 0 ✓
- [ ] `python manage.py check` passes ✓

---

## 🤖 AGENT REQUIREMENTS

2 agents minimum. Both 8.0+.

### 1. @docs-architect
- Feature 4 updates complete and accurate?
- Draft versioning tier table matches developer's stated intent?
- Rating: 8.0+/10

### 2. @api-documenter
- Cloudinary migration run sequence technically correct?
- localStorage schema description accurate?
- Rating: 8.0+/10

---

## 💾 COMMIT MESSAGE

```
END OF SESSION DOCS UPDATE: session 160 — draft autosave, Cloudinary migration, tier versioning
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_G.md`

---

**END OF SPEC**
