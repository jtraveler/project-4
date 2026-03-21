# CC_SPEC_141_E_DOCS_UPDATE.md
# End of Session 141 — Documentation Update

**Spec Version:** 1.0
**Date:** March 2026
**Session:** 141
**Type:** Docs — commits immediately per protocol v2.2
**Agents Required:** 1 (@docs-architect)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2** — docs gate rule applies
2. **Read `CC_REPORT_STANDARD.md`** — report format applies
3. **Per v2.2:** if agent scores below 8.0 → fix and re-run before committing

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Current test count
python manage.py test --verbosity=0 2>&1 | tail -3

# 2. Find Session 140 entry in changelog
grep -n "Session 140\|Session 141" CLAUDE_CHANGELOG.md | head -5

# 3. Check Deferred P3 Items and new features section
grep -n "Planned New Features\|Feature 1\|Feature 2\|Feature 3\|Feature 4" \
    CLAUDE.md | head -10

# 4. Check reference image documentation
grep -n "reference_image\|Reference Image\|reference image" CLAUDE.md | head -5
```

---

## 📁 CHANGES REQUIRED

### `CLAUDE_CHANGELOG.md`

Add Session 141 entry:

```
### Session 141 — [date]

**Focus:** Recurring bug fixes, lightbox structure, reference image fix

**Specs:** 141-A (download proxy + blur thumbnail), 141-B (clear all cleanup),
141-C (lightbox close button), 141-D (reference image fix), 141-E (docs)

**Key outcomes:**
- Download button now works via server-side proxy endpoint
  (/api/bulk-gen/download/) — bypasses CORS restriction on CDN URLs
- Blur thumbnail preview restored — valid URL on blur now shows preview
- Clear All hardened — paste URLs captured before fields cleared,
  full paste state reset in single loop
- Single-box ✕ clear now resets thumb.src/onerror
- Lightbox close button absolutely positioned on overlay (not in flow)
  — no longer appears below image on mobile
- Lightbox caption fully removed from results page lightbox
- Lightbox CSS extracted to static/css/components/lightbox.css
- Reference image fix — GPT-Image-1 now receives reference image as
  BytesIO file object (was silently ignored since feature was built)
```

### `CLAUDE.md`

1. Update test count
2. Update reference image documentation — note that the feature now works
   and requires a file-like object passed via `gen_params['images']`
3. Add note to Planned New Features section: Vision prompt generation
   (Feature 2) uses Option A — Vision-generated prompt replaces user text
   entirely, original text not preserved
4. Mark any Deferred P3 items resolved in Session 141

### `PROJECT_FILE_STRUCTURE.md`

- Update version header date
- Update session reference to 141
- Add `static/css/components/lightbox.css` to the CSS file list
- Add `prompts/services/image_providers/openai_provider.py` if not present

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] Session 141 changelog entry added with all key outcomes
- [ ] Test count updated
- [ ] Reference image fix documented
- [ ] Feature 2 Option A decision documented
- [ ] `lightbox.css` component file added to PROJECT_FILE_STRUCTURE.md
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 1 agent. Must score 8.0+.
Per v2.2: if below 8.0 → fix and re-run. No projected scores.

### 1. @docs-architect
- Verify all key outcomes are present and accurate
- Verify new component CSS file is in PROJECT_FILE_STRUCTURE.md
- Verify Feature 2 Option A decision is documented clearly
- Rating requirement: 8+/10

---

## 🧪 TESTING

```bash
python manage.py check
```

Commits immediately after confirmed 8.0+ score.

---

## 💾 COMMIT MESSAGE

```
END OF SESSION DOCS UPDATE: session 141 — download proxy, blur thumbnail, lightbox fix, reference image
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_141_E_DOCS_UPDATE.md`

---

**END OF SPEC**
