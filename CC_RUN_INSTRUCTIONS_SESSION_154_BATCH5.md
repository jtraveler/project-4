# CC_RUN_INSTRUCTIONS_SESSION_154_BATCH5.md
# Session 154 Batch 5 — Run Instructions for Claude Code

**Date:** April 2026
**Session:** 154
**Specs in this batch:** 1 code spec
**Trigger phrase:**
`Read CC_MULTI_SPEC_PROTOCOL.md and CC_REPORT_STANDARD.md first, then
read CC_RUN_INSTRUCTIONS_SESSION_154_BATCH5.md, then run:
CC_SPEC_154_Q_PROVIDER_FIXES2.md`

---

## ⛔ READ THIS ENTIRE DOCUMENT BEFORE STARTING ANYTHING

---

## 📋 CONFIRMED CURRENT STATE

**Root cause of Grok 400:** `_ASPECT_TO_DIMENSIONS` maps to non-standard
pixel sizes (e.g. `1344x768`, `1216x832`). xAI only accepts exactly
`1024x1024`, `1792x1024`, or `1024x1792`. All other sizes return HTTP 400.

**Root cause of Flux Schnell failure:** `str(first_output)` returns
`"FileOutput(url='https://...')"` not the raw URL. The HTTPS check then
fails because the string doesn't start with `https://`. Fix uses
`first_output.url` attribute directly.

**Root cause of missing cursor:** JS sets `pointerEvents: none` on
disabled sections but browser needs explicit `cursor: not-allowed` since
pointer-events suppresses cursor feedback. CSS attribute selector fix.

---

## 📋 SPEC QUEUE

| Order | Spec | Key Files | Tier |
|-------|------|-----------|------|
| **1** | `CC_SPEC_154_Q_PROVIDER_FIXES2.md` | xai_provider.py, replicate_provider.py, bulk-generator.css | ✅ Safe |

---

## ⚠️ FILE BUDGET

**`xai_provider.py`** — ✅ Safe:
- 2 str_replace calls (`_ASPECT_TO_DIMENSIONS` dict + `_resolve_dimensions` function)

**`replicate_provider.py`** — ✅ Safe:
- 1 str_replace call (FileOutput URL extraction)

**`bulk-generator.css`** — ✅ Safe:
- 1 addition (new rule at end of file)

---

## 🔁 EXECUTION SEQUENCE

1. Read spec fully
2. Step 0 greps — read all outputs before any edits
3. Change 1: Replace `_ASPECT_TO_DIMENSIONS` + `_resolve_dimensions` in xai_provider.py
4. Change 2: Fix FileOutput URL extraction in replicate_provider.py
5. Change 3: Add cursor CSS rule to bulk-generator.css
6. Step 1 verification greps — ALL must pass
7. Run `python manage.py collectstatic --noinput`
8. Run `python manage.py check`
9. Agents: @backend-security-coder, @code-reviewer
10. Both ≥ 8.0 → fill report → **DO NOT COMMIT until developer confirms
    Grok generates successfully in production**

---

## ⛔ HARD RULES

1. **xAI dimensions MUST be one of:** `1024x1024`, `1792x1024`, `1024x1792` — no others
2. **Use `hasattr(first_output, 'url')` guard** — do not assume `.url` always exists
3. **`str(first_output.url)`** not `first_output.url` — URL may not be a plain string
4. **CSS cursor rule targets `[style*="pointer-events: none"]`** — note the space
   around the colon matches how JS sets the style. Include both with and without
   space variants to be safe
5. **Do NOT change `_DEFAULT_DIMENSIONS`** — keep as `(1024, 1024)`

---

## ⚠️ AGENT SUBSTITUTIONS (Option B authorised)

- `@django-security` → `@backend-security-coder`
- `@tdd-coach` → `@tdd-orchestrator`
- `@accessibility-expert` → `@ui-visual-validator`

---

## 🔔 DEVELOPER BROWSER CHECKS (required before commit)

1. Generate with Grok Imagine → succeeds, no 400 error ✅
2. Generate with Flux Schnell → succeeds, image renders ✅
3. Select Flux Dev → hover over Quality section → `cursor: not-allowed` ✅
4. Select Flux Dev → hover over Character Reference Image → `cursor: not-allowed` ✅
5. Select GPT-Image-1.5 → both sections active → normal cursor ✅

---

## 💾 COMMIT MESSAGE

```
fix(providers): Grok 400, Flux FileOutput URL, disabled cursor

- xai_provider.py: constrain to xAI's 3 valid sizes
- replicate_provider.py: use FileOutput.url before str()
- bulk-generator.css: cursor:not-allowed on disabled sections
```

---
**END OF RUN INSTRUCTIONS**
