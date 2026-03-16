# CC_SPEC_136_A_CSS_MIGRATION.md
# Move Inline Paste/Badge CSS to bulk-generator.css

**Spec Version:** 1.0
**Date:** March 16, 2026
**Session:** 136
**Modifies UI/Templates:** YES (bulk_generator.html — remove CSS only)
**Migration Required:** No
**Agents Required:** 2 minimum
**Estimated Scope:** ~60 lines moved, 0 net new lines

---

## ⛔ CRITICAL: READ FIRST

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** before starting
2. **Read `CC_MULTI_SPEC_PROTOCOL.md`** — gate sequence applies
3. **Read `CC_REPORT_STANDARD.md`** — report format applies
4. **`bulk-generator.css` is 🟠 High Risk (1,511 lines)** — we are APPENDING only.
   Appending new rules to the end of a CSS file is safe regardless of tier.
   Do NOT edit existing rules in the file — append only.
5. **`bulk_generator.html` is 🟡 Caution** — str_replace only
6. **Zero visual changes** — this is a pure file organisation change.
   Every rule moves verbatim. No values change.

---

## 📋 OVERVIEW

The paste feature (Session 133) and error badge (Session 135) added CSS inline
in `bulk_generator.html`. This means developers looking for `.bg-source-paste-*`
or `.bg-box-error-badge` styles in `bulk-generator.css` find nothing — a
maintenance hazard. This spec moves all those rules to the external CSS file
where all other `.bg-*` component rules live.

**Rules to move (from `bulk_generator.html` inline `<style>` block):**
- `.bg-prompt-box.is-paste-target` (border-color + box-shadow)
- `.bg-source-paste-hint` and `.bg-prompt-box.is-paste-target .bg-source-paste-hint`
- `.bg-source-paste-preview`
- `.bg-source-paste-thumb`
- `.bg-source-paste-clear` and hover/focus-visible
- `.bg-box-header-actions`
- `.bg-box-error-badge` and `.bg-prompt-box.has-error .bg-box-error-badge`

**Rules to KEEP in `bulk_generator.html`:**
- `.bg-flush-btn` and variants
- `#flush-success-banner` and `.flush-banner-inner`
These are template-specific styles not part of the component system.

---

## 📁 STEP 0 — MANDATORY GREPS

```bash
# 1. Read the full inline style block to confirm exact content
sed -n '377,475p' prompts/templates/prompts/bulk_generator.html

# 2. Confirm no paste/badge rules already exist in bulk-generator.css
grep -n "source-paste\|paste-target\|paste-hint\|error-badge\|header-actions" \
    static/css/pages/bulk-generator.css

# 3. Read the end of bulk-generator.css (insertion point)
tail -25 static/css/pages/bulk-generator.css

# 4. Read the source image row section for natural grouping
grep -n "bg-prompt-source-image\|SRC-2\|Source image" \
    static/css/pages/bulk-generator.css | head -10
```

**Do not proceed until greps are complete.**

---

## 📁 STEP 1 — Append rules to `bulk-generator.css`

**File:** `static/css/pages/bulk-generator.css`

Append the following block at the very end of the file, after the last existing
rule. Copy every value VERBATIM from `bulk_generator.html` — do not change
any values, names, or formatting.

```css
/* ── SRC Paste Feature (Sessions 133–135) ────────────────── */

/* Active row selection */
.bg-prompt-box.is-paste-target {
    border-color: var(--primary, #2563eb);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

/* Paste hint text */
.bg-source-paste-hint {
    font-size: 0.72rem;
    color: var(--gray-500, #6b7280);
    margin-top: 0.25rem;
    display: none;
}
.bg-prompt-box.is-paste-target .bg-source-paste-hint {
    display: block;
    color: var(--primary);
    font-weight: 500;
}

/* Paste preview thumbnail */
.bg-source-paste-preview {
    display: none;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.4rem;
}
.bg-source-paste-thumb {
    max-width: 150px;
    max-height: 150px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid var(--gray-200, #e5e7eb);
}

/* Paste clear button */
.bg-source-paste-clear {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--gray-500, #6b7280);
    font-size: 1.1rem;
    line-height: 1;
    padding: 0.1rem 0.3rem;
}
.bg-source-paste-clear:hover { color: var(--gray-900, #111827); }
.bg-source-paste-clear:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
    border-radius: 2px;
}

/* ── Error Badge (Session 135) ────────────────────────────── */
.bg-box-header-actions {
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.bg-box-error-badge {
    display: none;
}
.bg-prompt-box.has-error .bg-box-error-badge {
    display: inline !important;
}
```

⚠️ Read the exact values from `bulk_generator.html` via the Step 0 grep before
appending. If any value in the spec above differs from the live file, use the
live file value. The goal is verbatim copy — no interpretation.

---

## 📁 STEP 2 — Remove moved rules from `bulk_generator.html`

**File:** `prompts/templates/prompts/bulk_generator.html`

The inline `<style>` block currently contains two sections — the flush button
CSS and the paste/badge CSS. After this change it should contain only the
flush button CSS.

From Step 0 grep, the style block currently ends with the error badge rules
before `</style>`. Use str_replace to replace the entire style block, keeping
the flush button rules and removing the paste/badge rules.

**The remaining style block after migration should be:**
```html
<style>
/* ── Flush button ── */
.bg-flush-btn {
    background: transparent;
    border: 1px solid #ef4444;
    color: #dc2626;
    padding: 0.4rem 1rem;
    border-radius: var(--radius-lg, 8px);
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
}
.bg-flush-btn:hover,
.bg-flush-btn:focus-visible {
    background: #fef2f2;
    outline: 2px solid #dc2626;
    outline-offset: 2px;
}
/* ── Success banner ── */
#flush-success-banner {
    position: fixed;
    top: 1rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    min-width: 400px;
    max-width: 90vw;
}
.flush-banner-inner {
    background: #d1fae5;
    border: 1px solid #6ee7b7;
    color: #065f46;
    border-radius: var(--radius-lg, 8px);
    padding: 0.75rem 1.25rem;
    text-align: center;
    font-size: 0.9rem;
}
</style>
```

⚠️ Read the exact current flush button CSS from Step 0 grep before writing
the str_replace. Use the live values — do not rely on the block above if
any value differs.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 greps completed
- [ ] All paste/badge rules appended to `bulk-generator.css` verbatim
- [ ] No paste/badge values changed during migration
- [ ] `bulk_generator.html` inline style block retains only flush button CSS
- [ ] No paste/badge rules remain in `bulk_generator.html`
- [ ] `bulk-generator.css` existing rules untouched
- [ ] `python manage.py check` passes

---

## 🤖 AGENT REQUIREMENTS

Minimum 2 agents. All must score 8.0+.

### 1. @frontend-developer
- Verify CSS values are identical in both locations (no values changed)
- Verify all moved rules are present in `bulk-generator.css`
- Verify no paste/badge rules remain in `bulk_generator.html`
- Verify flush button CSS still present in `bulk_generator.html`
- Rating requirement: 8+/10

### 2. @code-reviewer
- Verify the moved block is logically grouped with a comment header
- Verify no existing `bulk-generator.css` rules were modified
- Verify the inline style block in the template is clean after removal
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA
- Any CSS value changed during migration (e.g. color, size, display)
- Any paste/badge rule still in `bulk_generator.html`
- Any flush button rule accidentally removed from `bulk_generator.html`

---

## 🧪 TESTING

```bash
python manage.py check
```

**Manual browser check (Mateo must verify):**
1. Open bulk generator — verify paste feature looks identical to before
2. Paste an image — verify preview, hint text, and locked input all work
3. Enter invalid URL → Generate → verify ⚠️ badge still appears on error boxes
4. Verify no visual regression vs pre-migration behaviour

Full suite runs at end of session.

---

## 💾 COMMIT MESSAGE

```
refactor(css): move paste/badge inline CSS from bulk_generator.html to bulk-generator.css
```

---

## 📊 COMPLETION REPORT

Save to: `docs/REPORT_136_A_CSS_MIGRATION.md`
Follow `CC_REPORT_STANDARD.md` for the 11-section format.

---

**END OF SPEC**
