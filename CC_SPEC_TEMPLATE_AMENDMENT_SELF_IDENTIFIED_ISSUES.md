# CC Spec Template Amendment — Self-Identified Issues Policy

**For CC to apply to:** `CC_SPEC_TEMPLATE.md`
**Instruction:** Insert the section below between the
`PRE-AGENT SELF-CHECK` section and the `AGENT REQUIREMENTS` section.
Also add the two new completion report fields as shown below.
Update the version/changelog line at the top.

---

## INSERT — New Section (after PRE-AGENT SELF-CHECK, before AGENT REQUIREMENTS)

---

## 🔁 SELF-IDENTIFIED ISSUES POLICY

⛔ **This policy is MANDATORY and applies to every spec that uses this template.**

During implementation, CC will sometimes identify issues, rough edges,
or improvements that were not in the original spec. These must be
handled as follows:

**If the fix is ≤15 minutes AND only touches files already in scope
for this spec:**
→ Apply it before marking the spec complete. Do not defer it.
→ Report it in the completion report under "Self-Identified Fixes Applied."

**If the fix requires a new file, a migration, an architectural decision,
or touches files outside this spec's scope:**
→ Do NOT apply it in this session.
→ Report it in the completion report under "Deferred — Out of Scope"
  with enough detail for the next spec to pick it up.

**Why this rule exists:** A recurring anti-pattern in this project is CC
diagnosing a problem, providing the exact fix with effort estimated at
2–5 minutes, and then not applying it — leaving it to accumulate across
sessions. If you can see the fix and it fits in scope, close it now.

---

## INSERT — Completion Report Additional Fields

In the `CC COMPLETION REPORT FORMAT` section, add these two fields
immediately before the `## 📝 NOTES` field:

```markdown
## 🔁 SELF-IDENTIFIED FIXES APPLIED

[List any issues identified and closed during this session per the
Self-Identified Issues Policy. If none: "None identified."]

## 🔁 DEFERRED — OUT OF SCOPE

[List any issues identified but not fixable within this spec's scope.
Include enough detail for the next spec. If none: "None identified."]
```

---

## UPDATE — Changelog / Version Line

Change:
```
**Status:** Active - Use for all CC work
**Changelog:** v2.2 — ...
```

To:
```
**Status:** Active - Use for all CC work
**Changelog:** v2.3 — Added Self-Identified Issues Policy (mandatory
  closure of in-scope rough edges found during implementation).
  v2.2 — Added FULL SUITE GATE to testing checklist. ...
```
