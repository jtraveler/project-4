# CC Spec — Bulk Generator 6D Hotfix: Published Badge Keyboard Access + Template Update

**Spec Version:** 1.0
**Date:** March 10, 2026
**Phase:** 6D Hotfix (P1 accessibility gap + project template hardening)
**Modifies UI/Templates:** Yes — manual browser check required
**Modifies Backend:** No
**Modifies Tests:** No
**Modifies Project Docs:** Yes — CC_SPEC_TEMPLATE.md
**Baseline:** 1106 passing, 12 skipped (commit b7643fb — Phase 6D)
**Target:** 1106 passing, 0 failures, 12 skipped (no new tests — CSS/JS/docs only)

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. Read `CC_COMMUNICATION_PROTOCOL.md`
2. Read this entire specification before touching any file
3. This is a P1 accessibility fix — a sighted keyboard-only user currently
   cannot reach the "View Page →" published badge link
4. Two agents required — work REJECTED with fewer

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes

### What This Spec Does

Fixes one P1 accessibility gap deferred from Phase 6C-B.1, and adds one
new Critical Reminder to CC_SPEC_TEMPLATE.md to prevent a recurring test
quality pattern from appearing in future phases.

| Item | Type | Priority |
|------|------|----------|
| Published badge `<a>` link unreachable by keyboard | P1 accessibility fix | Must fix |
| CC_SPEC_TEMPLATE Critical Reminder #9 (test assertions) | Docs update | Must fix |

No new features. No migrations. No backend changes. No new tests.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Published badge "View Page →" link reachable by keyboard (Tab)
- ✅ Badge link has visible focus indicator
- ✅ Screen readers can read the badge link (aria-hidden removed)
- ✅ Mouse-hover behaviour unchanged — badge still visually subtle on hover
- ✅ CC_SPEC_TEMPLATE.md updated with Critical Reminder #9
- ✅ 2 agents both score 8.0+/10
- ✅ Manual browser keyboard test confirmed

---

## 🔍 STEP 0 — VERIFICATION PASS

Before writing any code, confirm in `bulk-generator-job.js`:

1. Where is `aria-hidden="true"` set on the badge `<a>` element? (Find
   the exact line in `markCardPublished()` or equivalent)
2. What is the current focus style on `.published-badge` when it is an
   `<a>` element? (Is `a.published-badge:focus-visible` in the CSS?)
3. What is the full set of CSS rules on `.published-badge` currently?
   (Need to know what `pointer-events` value is set — Phase 6C-B.1
   added `pointer-events: auto` on `a.published-badge`)

Report findings before making changes.

---

## 🔧 FIX 1 — Remove `aria-hidden` from Published Badge Link

### Problem

In `markCardPublished()`, the published badge `<a>` element is created
with `aria-hidden="true"`. This was set intentionally so the `#bulk-toast-
announcer` would handle screen reader announcements rather than the badge
itself. However, `aria-hidden="true"` hides the element from ALL
non-visual interaction — including keyboard navigation. A sighted keyboard-
only user can see the "View Page →" badge on published cards but cannot
Tab to it or activate it.

### Fix — JS change

Remove `aria-hidden="true"` from the badge element in `markCardPublished()`.

The `#bulk-toast-announcer` already announces "Page published" at publish
time — the badge being keyboard-accessible does not cause duplicate
announcements because the announcer fires once on the event, not
continuously.

Instead, give the badge an explicit, descriptive `aria-label` so screen
reader users hear useful text when they Tab to it:

```javascript
// Before:
badge.setAttribute('aria-hidden', 'true');

// After:
badge.setAttribute('aria-label', 'Published — view prompt page (opens in new tab)');
```

### Fix — CSS change

Add a focus-visible style for the badge link in `bulk-generator-job.css`:

```css
a.published-badge:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
    box-shadow: 0 0 0 4px #166534; /* dark green outer ring for contrast */
}
```

This gives a double-ring: white inner ring + dark green outer ring,
matching the double-ring pattern used on other overlay buttons in the
gallery.

### What NOT to change

- Do NOT add `tabindex="-1"` to the badge or any slot element
- Do NOT change the toast announcer — it is correct as-is
- Do NOT change `pointer-events: auto` on `a.published-badge` — already fixed in 6C-B.1
- The `.btn-zoom` aria-hidden inconsistency is a separate deferred item — do NOT touch it here

---

## 🔧 FIX 2 — CC_SPEC_TEMPLATE.md Critical Reminder #9

### Problem

A recurring pattern across Phase 6 specs: CC writes negative-only
sanitisation assertions (`assertNotIn('sk-proj-')`) that pass vacuously —
they pass even when no error message is returned at all. This was flagged
by @code-reviewer in Phase 6D and was also the root cause of the weakened
`available_tags` assertion fixed in 6C-B.1.

### Fix

Add the following as Critical Reminder #9 in `CC_SPEC_TEMPLATE.md`,
immediately after the existing Critical Reminder #8 (Documentation):

```markdown
9. **Pair Every Negative Assertion with a Positive Counterpart**
   - `assertNotIn` / `assertNotEqual` alone is insufficient — it passes
     even when the field is absent or None
   - Every negative assertion about sanitisation, exclusion, or absence
     MUST be paired with a positive assertion about the expected value
   - Example (WRONG): `self.assertNotIn('sk-proj-', response_data['error'])`
   - Example (CORRECT):
     ```python
     self.assertEqual(response_data['error'], 'Rate limit reached')  # positive
     self.assertNotIn('sk-proj-', response_data['error'])            # negative
     ```
   - This pattern has caused false-confidence test passes in Phases 6C-A
     and 6D. Agents must reject any sanitisation test that lacks a
     positive assertion.
```

Also update the version header line at the top of CC_SPEC_TEMPLATE.md:

```
**Last Updated:** March 10, 2026
**Changelog:** v2.5 — Added Critical Reminder #9 (paired test assertions).
Recurring pattern: negative-only assertions (assertNotIn) passing vacuously
in Phases 6C-A and 6D.
```

---

## ♿ ACCESSIBILITY — VERIFY BEFORE AGENTS

- [ ] Tab through a published card — "View Page →" badge link is reachable
- [ ] Badge link shows double-ring focus indicator (white + dark green)
- [ ] Screen reader announces "Published — view prompt page (opens in new tab)"
      when badge is focused
- [ ] Clicking badge still opens prompt page in new tab
- [ ] Mouse hover behaviour unchanged — badge is still visually positioned
      and styled identically to pre-fix

---

## 📁 FILES TO MODIFY

| File | Change |
|------|--------|
| `static/js/bulk-generator-job.js` | Remove `aria-hidden="true"`, add `aria-label` in `markCardPublished()` |
| `static/css/pages/bulk-generator-job.css` | Add `a.published-badge:focus-visible` double-ring rule |
| `CC_SPEC_TEMPLATE.md` | Add Critical Reminder #9, update version to v2.5 |

**DO NOT touch:** Any other JS, any backend files, any test files.

---

## ✅ PRE-AGENT SELF-CHECK

- [ ] Step 0 complete — aria-hidden location confirmed, current CSS confirmed
- [ ] `aria-hidden="true"` removed from badge element in JS
- [ ] `aria-label` added: "Published — view prompt page (opens in new tab)"
- [ ] `a.published-badge:focus-visible` double-ring rule in CSS
- [ ] CC_SPEC_TEMPLATE.md — Critical Reminder #9 added
- [ ] CC_SPEC_TEMPLATE.md — version header updated to v2.5
- [ ] Manual keyboard test: Tab reaches badge, focus ring visible
- [ ] No suite regressions: `python manage.py test` still 1106 passing

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: 2 agents. Work REJECTED with fewer.**

### Agent 1: @accessibility
- Focus: badge link keyboard reachability, `aria-label` text quality,
  focus ring contrast (white + dark green double-ring ≥ 3:1 against
  green badge background), no duplicate screen reader announcements,
  Tab order logical within published card
- Rating: **8.0+/10**

### Agent 2: @code-reviewer
- Focus: CC_SPEC_TEMPLATE wording precision (is the new Critical Reminder
  clear and unambiguous?), example code in reminder is syntactically
  correct, version header updated, no unintended changes to other files
- Rating: **8.0+/10**

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- `aria-hidden="true"` still present on the badge link
- Badge link not reachable by Tab key
- No focus indicator on badge link
- Critical Reminder #9 not added to CC_SPEC_TEMPLATE.md
- Version not updated to v2.5

---

## 🧪 TESTING

```bash
# No new tests — CSS/JS/docs only
# Full suite gate (no backend files changed — targeted is sufficient, but confirm):
python manage.py test prompts.tests.test_bulk_generator_views -v 2
# Expected: same count as baseline, 0 failures
```

---

## 📊 COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
BULK GENERATOR 6D HOTFIX — COMPLETION REPORT
═══════════════════════════════════════════════════════════════

STEP 0 FINDINGS
  aria-hidden location: [file:line]
  Current a.published-badge:focus-visible rule: [exists / not present]
  pointer-events on badge: [value]

MANUAL KEYBOARD CHECK
  Tab reaches badge link: YES / NO
  Focus ring visible: YES / NO
  aria-label text confirmed: YES / NO
  Opens in new tab: YES / NO

🤖 AGENT SCORES
  1. @accessibility  — [N]/10 — [findings]
  2. @code-reviewer  — [N]/10 — [findings]
  Average: [N]/10

FILES MODIFIED
  [List]

TESTING
  Suite: [N] passing, 12 skipped, 0 failures

SUCCESS CRITERIA
  [ ] aria-hidden removed, aria-label added
  [ ] Focus ring added to a.published-badge:focus-visible
  [ ] CC_SPEC_TEMPLATE v2.5 — Critical Reminder #9 added
  [ ] Both agents 8.0+/10

SELF-IDENTIFIED FIXES
  [List or "None identified."]

DEFERRED — OUT OF SCOPE
  [List or "None identified."]
═══════════════════════════════════════════════════════════════
```

---

## 🏷️ COMMIT MESSAGE

```
fix(bulk-gen): 6D hotfix -- published badge keyboard access + template v2.5

Accessibility (P1):
- markCardPublished(): removed aria-hidden="true" from badge <a> element
- Added aria-label: "Published — view prompt page (opens in new tab)"
- a.published-badge:focus-visible: white inner + dark green outer double-ring
- Badge link now reachable by Tab; sighted keyboard users can activate it

Docs:
- CC_SPEC_TEMPLATE v2.5: Critical Reminder #9 (paired test assertions)
  Negative-only assertions (assertNotIn) must be paired with positive
  counterpart. Pattern caused false-confidence passes in Phases 6C-A + 6D.

Agent scores: @accessibility [N]/10, @code-reviewer [N]/10

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
