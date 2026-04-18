# CC_SPEC_160_A_PROFANITY_ERROR_UX.md
# Profanity Error — Bold/Italic Word + Link to Prompt Box

**Spec Version:** 1.0
**Session:** 160
**Modifies UI/Templates:** Yes (error display)
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** 1–2 str_replace in `bulk_generation.py` + possibly template/JS

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Investigation-first** — read how the "Prompt 1 is not a valid image link"
   error links to its prompt box before writing any code. Mirror that pattern.

---

## 📋 CONFIRMED PROBLEMS (verified April 2026)

**Problem 1 — Triggered word not visually distinct**
The error message "Content flagged — the following word(s) were found: nigger.
Please revise your prompt." shows the word in plain text. It should be
**bold and italic** so it stands out immediately.

**Problem 2 — No link to the prompt box**
The "Prompt 1 is not a valid image link" error links directly to the
problematic prompt box. The profanity error doesn't. It should follow the
same pattern — link to "Prompt N" so the user can jump directly to the box.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read how the image link error generates its "Prompt 1" link
grep -n "is not a valid image link\|Prompt.*link\|prompt.*index\|index.*prompt" \
    prompts/services/bulk_generation.py | head -20

# 2. Read the full validate_prompts method
grep -n -A 60 "def validate_prompts" prompts/services/bulk_generation.py | head -70

# 3. Find how errors are displayed in the template/JS
grep -rn "fix.*following\|validation.*error\|prompt.*error\|error.*prompt" \
    prompts/templates/prompts/ static/js/ \
    --include="*.html" --include="*.js" | head -20

# 4. Confirm how the frontend renders error messages
# (does it render HTML from the message string, or escape it?)
grep -n "innerHTML\|innerText\|\.html(\|\.text(" \
    static/js/bulk-generator*.js | grep -i "error\|message" | head -15

# 5. Read the current profanity error message format (from 159-A)
grep -n "word(s) were found\|word_list\|html.escape" \
    prompts/services/bulk_generation.py
```

---

## 📁 STEP 1 — Add prompt index to profanity error message

From Step 0 grep 1, confirm the image link error includes the prompt index
(1-based) in its message. Apply the same pattern to the profanity error.

The error dict already has `'index': i` — use `i + 1` for the display number:

```python
errors.append({
    'index': i,
    'message': (
        f'<a href="#prompt-box-{i + 1}" class="alert-link">'
        f'Prompt {i + 1}</a> — content flagged. '
        f'The following word(s) were found: '
        f'<strong><em>{word_list}</em></strong>. '
        f'Please revise your prompt.'
    ),
})
```

**Critical:** Only use HTML in the message if Step 0 grep 4 confirms the
frontend renders it as HTML (innerHTML), not as text (innerText/textContent).
If the frontend escapes it, apply bold/italic formatting at the display layer
instead — in the template or JS error renderer.

**Adjust the `href` anchor ID** to match whatever anchor IDs the prompt boxes
actually have — confirm from Step 0 grep 3.

---

## 📁 STEP 2 — MANDATORY VERIFICATION

```bash
# 1. Confirm new message format includes prompt link and bold/italic word
grep -n "alert-link\|strong.*em\|Prompt.*content flagged" \
    prompts/services/bulk_generation.py

# 2. Confirm html.escape still applied to word_list
grep -n "html.escape\|escape.*word" prompts/services/bulk_generation.py

# 3. Confirm existing test updated for new message format
python manage.py test prompts.tests.test_bulk_generation_tasks \
    --verbosity=1 2>&1 | tail -10

# 4. Django check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 confirms frontend renders HTML (innerHTML) before using HTML tags ✓
- [ ] Prompt number link matches actual anchor ID on prompt boxes ✓
- [ ] Triggered word is bold AND italic ✓
- [ ] `html.escape()` still applied to word before bold/italic wrapping ✓
- [ ] Existing test updated ✓
- [ ] `python manage.py check` passes ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @backend-security-coder
- HTML in error message: is `word_list` safely escaped before being wrapped
  in `<strong><em>`? XSS risk if not.
- Rating: 8.0+/10

### 2. @frontend-developer
- Does the `href="#prompt-box-N"` anchor actually scroll to the right box?
  Confirm the anchor ID exists on the prompt box elements.
- Rating: 8.0+/10

### 3. @code-reviewer
- Does the frontend renderer use innerHTML or textContent? This determines
  whether HTML tags in the message work or show as literal text.
- Rating: 8.0+/10

### 4. @accessibility-expert
- Does the link from error message to prompt box correctly move focus?
- Is `<strong><em>` the right semantic markup for a flagged word?
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Existing tests updated for new message format?
- New test for prompt link format?
- Rating: 8.0+/10

### 6. @django-pro
- Is `html.escape` from `django.utils.html` the right escape function here?
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- HTML tags used without confirming frontend renders HTML (XSS risk)
- `html.escape()` removed from word_list (XSS regression from 159-A)
- Anchor ID doesn't match actual prompt box IDs

---

## 🧪 TESTING

```bash
python manage.py test prompts.tests.test_bulk_generation_tasks --verbosity=1
python manage.py test --verbosity=0
```

**Manual:** Enter a profanity word → error shows **"Prompt 1"** as a clickable
link, triggered word in **bold italic**, clicking link scrolls to prompt box ✅

---

## 💾 COMMIT MESSAGE

```
fix(validation): profanity error — bold/italic word, link to prompt box
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_A.md`

---

**END OF SPEC**
