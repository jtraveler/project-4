# CC_SPEC_160_E_PRICING_ACCURACY.md
# Pricing Accuracy — Full Precision Everywhere, No Rounding

**Spec Version:** 1.0
**Session:** 160
**Modifies UI/Templates:** Yes (results template + possibly view)
**Migration Required:** No
**Agents Required:** 6 minimum
**Estimated Scope:** 1–2 str_replace in results template + view (🟡 Caution)

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_MULTI_SPEC_PROTOCOL.md` v2.2**
2. **Read `CC_REPORT_STANDARD.md`**
3. **Fix all models** — not just NB2. Every model's cost should display
   with full precision.

---

## 📋 CONFIRMED PROBLEM (verified April 2026)

Results page shows $0.07 instead of $0.067 for NB2 at 1K resolution.
Rounding is happening somewhere in the display layer. The stored value
in the database is correct — this is purely a formatting issue.

All models should show full precision (e.g. $0.003, $0.025, $0.067,
$0.101, $0.151, $0.015, $0.020) rather than rounding to 2 decimal places.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Find how cost is displayed in the results template
grep -n "cost\|price\|floatformat\|:.2f\|round(" \
    prompts/templates/prompts/bulk_generator_job.html | head -20

# 2. Find any floatformat or format filters applied to cost
grep -n "floatformat\|:.2\|:.3\|format.*cost\|cost.*format" \
    prompts/templates/prompts/ --include="*.html" -r | head -10

# 3. Find cost in the job detail view context
grep -n "cost\|actual_cost\|format_cost" \
    prompts/views/bulk_generator_views.py | head -20

# 4. Find any Python-side rounding
grep -n "round(\|:.2f\|:.3f" prompts/tasks.py | grep -i cost | head -10

# 5. Find the sticky bar cost display format in JS
grep -n "formatCost\|toFixed\|format.*cost\|cost.*format\|\.2\b" \
    static/js/bulk-generator-config.js \
    static/js/bulk-generator-ui.js | head -15
```

---

## 📁 STEP 1 — Fix rounding in results template

From Step 0 grep 1-2, identify where rounding is applied. Common Django
template filter causing this: `{{ cost|floatformat:2 }}` rounds to 2 decimal
places.

**Replace with full precision** — use enough decimal places to show all
significant digits for the pricing range ($0.003 needs 3 places, $0.067
needs 3 places, $0.151 needs 3 places):

```django
{# BEFORE: rounds to 2 decimal places #}
${{ image.actual_cost|floatformat:2 }}

{# AFTER: shows up to 3 significant decimal places #}
${{ image.actual_cost|floatformat:3 }}
```

Or if the cost is passed as a Python float, format it in the view:
```python
# In view context:
'cost_display': f'${cost:.3f}'.rstrip('0').rstrip('.')
# $0.067 → "$0.067", $0.003 → "$0.003", $0.100 → "$0.1"
```

**Use whichever approach matches how cost is currently passed to the template.**

---

## 📁 STEP 2 — Fix JS sticky bar rounding (if applicable)

From Step 0 grep 5, check if `formatCost()` or `toFixed()` rounds to 2
decimal places. If so, update to 3:

```javascript
// BEFORE:
function formatCost(cost) {
    return '$' + cost.toFixed(2);
}

// AFTER:
function formatCost(cost) {
    // Show up to 3 decimal places, strip trailing zeros
    return '$' + parseFloat(cost.toFixed(3)).toString();
}
```

---

## 📁 STEP 3 — MANDATORY VERIFICATION

```bash
# 1. Confirm no floatformat:2 on cost fields
grep -n "floatformat:2\|floatformat: 2" \
    prompts/templates/prompts/bulk_generator_job.html
# Expected: 0 results (or confirmed changed to :3)

# 2. Confirm formatCost in JS
grep -n "toFixed\|formatCost" \
    static/js/bulk-generator-config.js | head -5

# 3. Django check
python manage.py check
```

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Results page: $0.067 not rounded to $0.07 ✓
- [ ] Sticky bar: $0.067 shown correctly ✓
- [ ] $0.003 (Flux Schnell) still shows correctly ✓
- [ ] $0.151 (NB2 4K) shows correctly ✓
- [ ] No trailing zeros (e.g. $0.020 vs $0.02) — strip trailing zeros ✓

---

## 🤖 AGENT REQUIREMENTS

**Minimum 6 agents. Average 8.5+. All must score 8.0+.**

### 1. @django-pro
- Is `floatformat:3` the right Django template filter here?
- Are there edge cases (0 cost, None cost) that need guarding?
- Rating: 8.0+/10

### 2. @frontend-developer
- Does the JS `formatCost` fix work for all price points?
- Rating: 8.0+/10

### 3. @code-reviewer
- Is stripping trailing zeros correct for all our price points?
  ($0.003, $0.020, $0.040, $0.067, $0.101, $0.151)
- Rating: 8.0+/10

### 4. @python-pro
- Is the Python f-string approach idiomatic if used in view?
- Rating: 8.0+/10

### 5. @tdd-orchestrator
- Test that covers cost display precision?
- Rating: 8.0+/10

### 6. @architect-review
- Should cost formatting be centralised in a template tag or utility function
  rather than inline template filters?
- Rating: 8.0+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Results page still shows $0.07 for NB2 1K
- Any model shows rounded cost

---

## 🧪 TESTING

```bash
python manage.py check
python manage.py test --verbosity=0
```

**Manual:** Generate NB2 at 1K → results page shows **$0.067** ✅
Generate Flux Schnell → results page shows **$0.003** ✅

---

## 💾 COMMIT MESSAGE

```
fix(results): pricing shows full precision, no rounding

- Results page: floatformat:3 replaces floatformat:2
- JS formatCost: 3 decimal places with trailing zero strip
- All models: $0.003, $0.025, $0.067, $0.101, $0.151 etc.

Agents: 6 agents, avg X/10, all passed 8.0+ threshold
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_160_E.md`

---

**END OF SPEC**
