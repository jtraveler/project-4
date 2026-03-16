# CC_SPEC_136_D_VIEWS_STRUCTURE_DOCS.md
# Rewrite `prompts/views/STRUCTURE.txt` and `README.md`

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 136
**Type:** Docs — commits immediately per protocol
**Agents Required:** 1 (@docs-architect)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — docs specs commit immediately
3. **Documentation changes only** — no Python, no migrations

---

## 📋 OVERVIEW

`prompts/views/STRUCTURE.txt` and `README.md` are significantly stale:
- Reference the original December 2025 11-module split
- Still list `prompt_create` (removed Session 135)
- Do not include Session 128 API split modules (4 files)
- Do not include Session 134 prompt_views split modules (4 files)
- Line counts are wrong throughout

Both files need a full rewrite to reflect the current 22-module state.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Get current file list and line counts
wc -l prompts/views/*.py | sort -n

# 2. Get function list for each new file from Session 134
grep -n "^def \|^class " prompts/views/prompt_list_views.py
grep -n "^def \|^class " prompts/views/prompt_edit_views.py
grep -n "^def \|^class " prompts/views/prompt_comment_views.py
grep -n "^def \|^class " prompts/views/prompt_trash_views.py

# 3. Get function list for Session 128 API split files
grep -n "^def \|^class " prompts/views/ai_api_views.py
grep -n "^def \|^class " prompts/views/moderation_api_views.py
grep -n "^def \|^class " prompts/views/social_api_views.py
grep -n "^def \|^class " prompts/views/upload_api_views.py

# 4. Confirm prompt_views.py is now a shim
wc -l prompts/views/prompt_views.py
head -5 prompts/views/prompt_views.py

# 5. Confirm api_views.py is now a shim
wc -l prompts/views/api_views.py
head -5 prompts/views/api_views.py
```

**Do not proceed until greps are complete.**

---

## 📁 CHANGES REQUIRED

### `prompts/views/STRUCTURE.txt`

Rewrite completely. The new file should:
- List all 22 current modules with accurate line counts from Step 0
- Show that `prompt_views.py` and `api_views.py` are now shims
- Show the 4 prompt domain modules from Session 134
- Show the 4 API domain modules from Session 128
- Remove `prompt_create` (removed Session 135)
- Update statistics section

### `prompts/views/README.md`

Rewrite completely. The new file should:
- Update the migration date/context section
- Update the package structure table with all 22 modules
- Update each module breakdown with correct functions and line counts
- Remove `prompt_create` from `prompt_edit_views.py` listing
- Add the 4 prompt domain modules
- Add the 4 API domain modules
- Update "Total Lines" and statistics
- Mark migration checklist items as complete
- Remove the rollback plan (the original monolithic file no longer exists)

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed — all line counts and function lists gathered
- [ ] STRUCTURE.txt shows 22 modules
- [ ] README.md shows 22 modules
- [ ] `prompt_create` not listed anywhere
- [ ] `prompt_views.py` and `api_views.py` noted as shims
- [ ] 4 prompt domain modules present (list, edit, comment, trash)
- [ ] 4 API domain modules present (ai_api, moderation_api, social_api, upload_api)
- [ ] Line counts match actual file sizes from Step 0
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 1 agent. Must score 8.0+.

### 1. @docs-architect
- Verify all 22 modules listed in both files
- Verify `prompt_create` absent from all listings
- Verify shim files correctly identified
- Verify line counts plausible (within ±20 of actual)
- Rating requirement: 8+/10

---

## 🧪 TESTING

```bash
python manage.py check
```

Commits immediately after agents pass.

---

## 💾 COMMIT MESSAGE

```
docs(views): rewrite STRUCTURE.txt and README.md for current 22-module state
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_136_D_VIEWS_STRUCTURE_DOCS.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
