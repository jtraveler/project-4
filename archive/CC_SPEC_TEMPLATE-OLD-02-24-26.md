# Claude Code Specification Template

**Last Updated:** February 18, 2026
**Purpose:** Standard template for all Claude Code (CC) specifications
**Status:** Active - Use for all CC work
**Changelog:** v2 — Added 5 new sections: inline accessibility, DOM structure diagrams, exact-copy enforcement, data migration, agent rejection criteria

---

## 📋 TEMPLATE STRUCTURE

Every specification for Claude Code MUST include the following sections in this order:

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** - Contains mandatory agent usage requirements
2. **Read this entire specification** - Don't skip sections
3. **Use required agents** - Minimum 2-3 agents appropriate for the task
4. **Report agent usage** - Include ratings and findings in completion summary

**This is non-negotiable per the project's CC Communication Protocol.**

---

## 📋 OVERVIEW

**Modifies UI/Templates:** Yes / No

### [Task Name]

Brief description of what needs to be done.

### Context

- Why this work is needed
- What came before
- Current state vs desired state

---

## 🎯 OBJECTIVES

### Primary Goal

Clear statement of what success looks like.

### Success Criteria

- ✅ Specific, measurable outcomes
- ✅ Quality requirements
- ✅ Testing requirements

---

## 🔍 PROBLEM ANALYSIS

### Current State

What exists now.

### Issues/Challenges

What's wrong or needs improvement.

### Root Cause

Why the problem exists.

---

## 🔧 SOLUTION

### Approach

High-level solution strategy.

### Implementation Details

Step-by-step what needs to be done.

### ♿ ACCESSIBILITY — BUILD THESE IN FROM THE START

⛔ **Do NOT bolt accessibility on after implementation. Build it in from line one.**

**For every interactive element you create, address these DURING implementation — not as an afterthought:**

1. **Focus Management:** If you remove a DOM element that might have focus, move focus to the nearest safe target BEFORE calling `.remove()` or setting `display: none`.

2. **Contrast:** All text MUST be --gray-500 (#737373) minimum on white backgrounds. On tinted backgrounds (e.g., #eff6ff for unread), bump to --gray-600. NEVER use --gray-400 for text. Decorative elements (icons, borders) are exempt.

3. **ARIA Live Regions:** If two updates fire simultaneously (e.g., badge count + status message), add a 150ms delay to the second to avoid live region collision.

4. **Keyboard Navigation:** Every clickable element must be reachable via Tab. Custom widgets need arrow key navigation. All focus states must be visible (`:focus-visible` outline).

5. **Screen Reader Text:** Decorative elements get `aria-hidden="true"`. Interactive elements get descriptive `aria-label` if the visible text is ambiguous.

**If the spec involves removing elements from DOM, hiding elements, or updating counts — accessibility requirements are listed inline with those implementation steps below, not just in the agent section.**

---

## 🏗️ DOM STRUCTURE (Required for UI/Layout Changes)

⛔ **If this spec changes HTML structure or layout, include a tree diagram showing exact DOM nesting.**

CC must implement the EXACT nesting shown here. Do not reorganize, flatten, or restructure.

### Required Structure
```
.component-wrapper (flex row, align-items: center)
  ├── .column-1         ← description of what goes here
  ├── .column-2         ← description
  │     ├── .child-a
  │     └── .child-b
  ├── .column-3         ← description (SIBLING of column-2, NOT a child)
  └── .column-4         ← description
```

### ⛔ Common Mistake to Avoid
```
WRONG: .column-3 nested inside .column-2
RIGHT: .column-3 as a sibling of .column-2
```

**Agent rejection criteria:** If the implemented DOM nesting does not match this tree diagram, the UI agent score MUST be below 6. Do not rate above 7 if the structure is wrong, even if the visual appearance seems close.

---

## 📁 FILES TO MODIFY

### File 1: [filename]

**Current State:** [description]

**Changes Needed:**
- [specific change 1]
- [specific change 2]

**Before:**
```
[code example]
```

**After:**
```
[code example]
```

### 📋 COPY EXACTLY — DO NOT SUBSTITUTE

⛔ **The following content must be copied character-for-character. Do not find alternatives, use similar versions, or make substitutions.**

```
[exact content that must be copied verbatim — SVG paths, specific strings, URLs, etc.]
```

**Verification step:** After adding, run `grep "[unique string from above]" [filename]` and confirm it appears exactly once.

[Repeat for each file]

---

## 🔄 DATA MIGRATION (Required for Backend Logic Changes)

⛔ **If this spec changes backend logic (signal handlers, service functions, URL patterns), answer these questions:**

### Does this change affect existing data?

- [ ] **YES** — Existing records in the database were created under the old logic and need updating
- [ ] **NO** — This change only affects newly created records going forward

### If YES: Provide a migration strategy

**Option A: Management Command**
- Create `prompts/management/commands/[command_name].py`
- Must be idempotent (safe to run multiple times)
- Must report: total found, updated, skipped, errors
- Include in the spec as a required file

**Option B: Data Migration**
- Create a Django data migration
- Include rollback logic

**Option C: Manual SQL / Django Shell**
- Provide the exact commands to run
- Include verification query

### Records to backfill

| Model | Filter | Field(s) to Update | Expected Count |
|-------|--------|-------------------|----------------|
| [Model] | [filter criteria] | [fields] | [estimate] |

**IMPORTANT:** The management command or migration must be run AFTER the code changes are deployed. Include the run command in the completion report.

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

Per `CC_COMMUNICATION_PROTOCOL.md`, CC must use appropriate agents for this task.

### Required Agents (Minimum 2-3)

**1. [Agent Name]** (e.g., @django-pro)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

**2. [Agent Name]** (e.g., @code-reviewer)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

**3. [Agent Name]** (optional third agent)
- Task: [what to review]
- Focus: [specific areas]
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:

- **UI Agent:** DOM nesting does not match the tree diagram in the DOM STRUCTURE section
- **UI Agent:** Layout has wrong number of columns or wrong element hierarchy
- **Accessibility Agent:** Any text element uses --gray-400 or lighter
- **Accessibility Agent:** Interactive elements removed from DOM without focus management
- **Accessibility Agent:** Missing aria-labels on interactive elements
- **Code Reviewer:** Exact-copy content was substituted with alternatives
- **Django Expert:** Backend change has no data migration when existing data is affected

**These are non-negotiable. Do not rate above 7 if any of the above are present.**

### Agent Reporting Format

At the end of implementation, CC must report:

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. [Agent Name] - [Rating/10] - [Brief findings]
2. [Agent Name] - [Rating/10] - [Brief findings]
[Additional agents if used]

Critical Issues Found: [Number]
High Priority Issues: [Number]
Recommendations Implemented: [Number]

Overall Assessment: [APPROVED/NEEDS REVIEW]
```

---

## 🖥️ TEMPLATE / UI CHANGE DETECTION

**If this spec modifies ANY of the following, the MANUAL BROWSER CHECK below is MANDATORY:**
- HTML templates (.html files)
- CSS or inline styles
- JavaScript files
- Admin template overrides
- Any file in a `templates/` directory
- Any file in a `static/` directory

### MANUAL BROWSER CHECK (Required for UI/template changes)

⚠️ **DO NOT commit until the developer has visually verified in a browser.**

After implementation, the developer MUST:
1. Open the affected page(s) in a browser at 127.0.0.1:8000
2. Check layout at desktop width (1200px+)
3. Check layout at tablet width (~768px) if responsive
4. Verify no overlapping elements, broken floats, or text wrapping issues
5. Verify the change matches the intended layout described in this spec
6. Screenshot or confirm visual verification before accepting agent scores

**CC agents cannot verify visual rendering — only a human in a browser can.**
**Agent UI scores above 8 require visual verification to be valid.**

---

## 🧪 TESTING CHECKLIST

### Pre-Implementation Testing

- [ ] [Test item 1]
- [ ] [Test item 2]

### Post-Implementation Testing

- [ ] [Test item 1]
- [ ] [Test item 2]

### Regression Testing

- [ ] [Existing feature 1 still works]
- [ ] [Existing feature 2 still works]

---

## 📊 CC COMPLETION REPORT FORMAT

**After implementation, Claude Code MUST provide a completion report in this format:**

```markdown
═══════════════════════════════════════════════════════════════
[TASK NAME] - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## 🤖 AGENT USAGE SUMMARY

[Agent report as specified above]

## 📁 FILES MODIFIED

[List of files with line counts]

## 🧪 TESTING PERFORMED

[Test results]

## ✅ SUCCESS CRITERIA MET

[Checklist of success criteria]

## 🔄 DATA MIGRATION STATUS

[If applicable: command run, output, records updated]

## 📝 NOTES

[Any additional observations]

═══════════════════════════════════════════════════════════════
```

---

## ⚠️ IMPORTANT NOTES

### Critical Reminders

1. **Agent Testing is Mandatory**
   - Not optional
   - Minimum 2-3 agents
   - All must rate 8+/10
   - Document findings

2. **Quality Over Speed**
   - Take time to do it right
   - Address agent concerns
   - Test thoroughly

3. **Accessibility is Built In, Not Bolted On**
   - Address focus management, contrast, ARIA during implementation
   - Do NOT wait for the a11y agent to flag these
   - If removing DOM elements, handle focus FIRST

4. **Copy Exact Content When Specified**
   - SVG paths, URLs, strings marked "COPY EXACTLY" must be verbatim
   - Do NOT substitute with similar alternatives
   - Verify with grep after adding

5. **Consider Existing Data**
   - Backend logic changes may require data migration
   - Old records don't automatically update
   - Include backfill strategy when applicable

6. **Match DOM Structure Exactly**
   - If a tree diagram is provided, implement that exact nesting
   - Siblings must be siblings, not children
   - Agents must reject work where nesting is wrong

7. **Documentation**
   - Clear commit messages
   - Comprehensive reports
   - Easy to understand

---

## 💾 COMMIT STRATEGY

### Recommended Commit Message Format

```bash
git commit -m "[type]([scope]): [subject]

[body explaining what and why]

[optional footer with references, agent ratings, etc.]"
```

**Types:**
- feat: New feature
- fix: Bug fix
- docs: Documentation only
- style: Formatting, no code change
- refactor: Code change that neither fixes a bug nor adds a feature
- test: Adding tests
- chore: Maintenance

---

## 🎯 EXAMPLES

### Example Patterns This Template Addresses

- **DOM nesting fix:** A layout spec required 4 columns as siblings but the implementation nested column 3 inside column 2. The tree diagram section would have caught this.
- **Exact SVG paths:** A spec provided exact SVG icon paths but the implementation substituted a similar-looking icon with different paths. The "COPY EXACTLY" section prevents this.
- **Backend data migration:** A signal handler change only affected new records, leaving existing database records with stale data. The "DATA MIGRATION" section ensures backfill is planned upfront.
- **Accessibility bolt-on:** Focus management and ARIA live region timing were added only after agent review flagged them. The inline accessibility section ensures these are built in from the start.
- **Cross-component sync:** Two JS files needed to communicate via a custom DOM event. The agent rejection criteria ensured proper review of the event dispatch/listener pattern.

---

## 📞 QUESTIONS?

If unclear on any section:
1. Ask the user for clarification
2. Reference CC_COMMUNICATION_PROTOCOL.md
3. Look at recent completed specs in the project for examples

**Never skip agent testing or reporting!**

---

**END OF TEMPLATE**

Use this template for all Claude Code specifications to ensure consistent quality and professional deliverables.