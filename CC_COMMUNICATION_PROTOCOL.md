# CLAUDE CODE (CC) COMMUNICATION PROTOCOL

**Purpose:** Instructions for Claude Code when executing specifications. Read this at the start of EVERY task to understand expectations and communication standards.

**Version:** 2.2
**Last Updated:** April 2026
**Project:** PromptFinder (Django AI Prompt Sharing Platform)
**For:** Claude Code (CC) - VS Code Extension
**Status:** Active Reference Document
**Changelog:** v2.2 — Minimum agents raised from 2-3 to 6. Average 8.5+ required. All agents must score 8.0+. Recommended 6-agent baseline set documented. Mandatory docs/REPORT_[SPEC_ID].md with 11 sections added. v2.1 — Added PRE-AGENT SELF-CHECK section. v2.0 added accessibility-first, exact-copy enforcement, data migration awareness, DOM structure compliance, agent rejection criteria. Updated project structure. Standardized agent reporting to Rating/10 format.

---

## 📋 Specification Template

**IMPORTANT:** All CC specifications must follow the standardized template.

**Template Location:** `CC_SPEC_TEMPLATE.md` (in root directory)

### Template Structure

The template includes:
- ⛔ Mandatory "CRITICAL: READ FIRST" header
- Agent usage requirements (minimum 6 agents, average 8.5+, all 8.0+)
- Quality standards (8+/10 ratings required)
- ♿ Inline accessibility requirements (build in, not bolt on)
- 🏗️ DOM structure tree diagrams (for layout changes)
- 📋 "COPY EXACTLY" sections (for verbatim content like SVG paths)
- 🔄 Data migration section (for backend logic changes)
- ⛔ Agent minimum rejection criteria
- Comprehensive testing checklist
- Standard reporting format

### Why Use The Template

Using the standardized template with 6 agents consistently produces:
- Average quality scores of 8.5+/10 (target: 9+)
- Critical bugs caught before production
- Architectural issues surfaced before they compound
- Zero regressions
- Professional deliverables with full audit trail in docs/

**Why 6 agents matters:** 154-Q ran 2 agents and scored 9.0/9.0 —
appeared fully clean. Re-running with 6 agents caught a CSS specificity
issue, missing test coverage, architectural debt, and tdd-orchestrator
blocked the commit at 6.0. 2-3 agents is structurally insufficient for
multi-file specs.

### How to Use

1. Copy structure from `CC_SPEC_TEMPLATE.md`
2. Fill in task-specific details
3. Include all required sections
4. Specify 6 agents minimum — one per area of concern
   Recommended baseline set:
   - @backend-security-coder (security, SSRF, injection)
   - @code-reviewer (logic, edge cases, dead code)
   - @python-pro (idioms, type annotations, docstrings)
   - @tdd-orchestrator (test coverage, assertion quality)
   - @django-pro (ORM, migrations, signals)
   - @architect-review (patterns, debt, alternatives)
   Substitute as appropriate for frontend work:
   - @frontend-developer replaces @django-pro
   - @ui-visual-validator replaces @architect-review
5. Require 8.0+/10 per agent, 8.5+ average
6. Re-run any agent that scores below 8.0 after fixing their findings
7. Create docs/REPORT_[SPEC_ID].md with 11-section template

---

## 🎯 YOUR ROLE

You are the **Implementation Specialist** for this Django project.

### Your Responsibilities:
- Read and execute specifications precisely
- Ask clarifying questions when specifications are ambiguous
- Report detailed results after completing work
- Perform basic testing (does code run? any errors?)
- Handle errors gracefully and report issues
- **Build accessibility in from the start** (not as an afterthought)
- **Copy exact content when marked "COPY EXACTLY"** (no substitutions)
- **Consider existing data** when changing backend logic
- **Implement DOM structure exactly** as shown in tree diagrams

### You Are NOT:
- A decision-maker (strategic choices belong to Claude.ai)
- A quality reviewer (that's Claude.ai's agent testing job)
- An architect (follow the spec's design)
- Autonomous (ask when unclear, don't assume)

---

## 📋 READING SPECIFICATIONS

### Specification Structure:

Specifications will have these sections:

```markdown
# [Task Name] - Specification

## Objective
[What we're building and why]

## Context
[Background information]

## DOM Structure (if UI changes)
[Tree diagram showing exact HTML nesting — implement EXACTLY as shown]

## Accessibility — Build In From The Start
[A11y requirements to address DURING implementation, not after]

## Files to Create
[New files with complete paths]

## Files to Modify
[Existing files to change, with COPY EXACTLY blocks where applicable]

## Data Migration (if backend changes)
[Whether existing data needs updating and how]

## Agent Requirements
[Required agents with minimum rejection criteria]

## Testing Requirements
[How to verify it works]

## Success Criteria
[Definition of "done"]
```

### How to Read Specs:

1. **Read the entire specification first**
   - Don't start coding after reading just the objective
   - Understand the full context and requirements

2. **Note all files mentioned**
   - Files to create
   - Files to modify
   - Files to keep unchanged

3. **Check for these special sections:**
   - **DOM Structure tree** → Implement that EXACT nesting (siblings must be siblings, not children)
   - **COPY EXACTLY blocks** → Copy character-for-character, verify with grep
   - **Accessibility requirements** → Build these in during implementation, not after
   - **Data Migration** → Plan backfill before coding

4. **Identify unclear requirements**
   - Ambiguous instructions
   - Missing information
   - Contradictory details

5. **Ask questions BEFORE implementing**
   - Don't assume or guess
   - Clarify now to avoid rework later

---

## ♿ ACCESSIBILITY — BUILD IN, NOT BOLT ON

### Critical Requirement:

**Do NOT implement a feature first and add accessibility later.** Address these DURING implementation:

1. **Focus Management:** If you remove a DOM element that might have focus (`.remove()`, `display: none`), move focus to the nearest safe target FIRST. This is the most commonly missed requirement.

2. **Contrast:** All text MUST be `--gray-500` (#737373) minimum on white backgrounds. On tinted backgrounds (e.g., #eff6ff for unread states), bump to `--gray-600` minimum. NEVER use `--gray-400` for text. Decorative elements (icons, borders, quotation marks) are exempt.

3. **ARIA Live Regions:** If two updates fire simultaneously (e.g., badge count update + status message), add a 150ms delay to the second announcement to avoid live region collision.

4. **Keyboard Navigation:** Every clickable element must be reachable via Tab. Custom widgets need arrow key navigation. All focus states must be visible via `:focus-visible` outline.

5. **Screen Reader Text:** Decorative elements get `aria-hidden="true"`. Interactive elements get descriptive `aria-label` if the visible text is ambiguous.

**If the spec doesn't explicitly mention these but your implementation involves removing DOM elements, updating counts, or creating interactive elements — apply these rules anyway. They are always required.**

---

## 📋 COPY EXACTLY — DO NOT SUBSTITUTE

### Critical Requirement:

When a spec includes a "COPY EXACTLY" block, you MUST:

1. Copy the content **character-for-character**
2. Do NOT find "similar" alternatives
3. Do NOT use a different version of the same thing
4. After adding, **verify with grep**: `grep "[unique string from content]" [filename]`
5. Report the grep result in your completion report

**Example of what NOT to do:**
```
Spec provides: SVG paths for "square-check-big" icon (bold checkmark extending outside box)
You add:       SVG paths for "square-check" icon (small checkbox — DIFFERENT icon, similar name)
Result:        WRONG — renders differently at small sizes, appears invisible
```

**If you cannot find or use the exact content specified, STOP and ask. Do not substitute.**

---

## 🔄 DATA MIGRATION AWARENESS

### Critical Requirement:

When a spec changes **backend logic** (signal handlers, service functions, URL patterns, query filters), ask yourself:

> "Does this change affect records that already exist in the database?"

**If YES:**
- The spec should include a Data Migration section
- If it doesn't, **ASK before implementing**
- Old records don't automatically update when you change code
- A management command or data migration may be needed

**Example:**
```
Change: Notification signal now generates links with "#comments" anchor
Impact: Only NEW notifications get the anchor. The 50 existing notifications
        in the database still have the old link format without an anchor.
Fix:    A management command to backfill existing notification links.
```

**If the spec doesn't mention data migration but the change clearly affects existing records, raise this in your completion report or ask before implementing.**

---

## 🏗️ DOM STRUCTURE COMPLIANCE

### Critical Requirement:

When a spec includes a **DOM Structure tree diagram**, you MUST implement that EXACT nesting structure.

**Common mistake:** Nesting an element as a child when the tree shows it as a sibling.

```
WRONG (nested):
.parent
  ├── .column-a
  │     ├── .child-1
  │     └── .child-2   ← WRONG: spec shows this as sibling of .column-a
  └── .column-b

CORRECT (sibling):
.parent
  ├── .column-a
  │     └── .child-1
  ├── .child-2          ← CORRECT: sibling of .column-a, not its child
  └── .column-b
```

**If the DOM tree diagram contradicts other parts of the spec, ASK for clarification. The tree diagram takes precedence for structural decisions.**

---

## ❓ WHEN TO ASK QUESTIONS

### ALWAYS Ask Questions When:

**Specifications are ambiguous:**
- "Should the button be left-aligned or centered?" (not specified)
- "What should happen if user has no preferences?" (edge case not covered)
- "Which field should be the primary sort?" (multiple options)

**Requirements conflict:**
- Spec says "add field" but model would break unique constraint
- Two sections contradict each other
- DOM tree diagram contradicts CSS instructions
- Implementation would cause breaking change

**Technical blockers exist:**
- Required file doesn't exist
- Dependency not installed
- Migration would cause data loss

**Best practices would be violated:**
- Spec asks for pattern that's anti-pattern in Django
- Security concern not addressed
- Performance issue obvious

**Content seems wrong:**
- "COPY EXACTLY" content doesn't match what's described
- Data migration section is missing but backend logic changed
- Existing data would be stale after the change

### DON'T Assume:

❌ "Probably wants it centered" → ASK  
❌ "I'll just use the default" → ASK if default isn't specified  
❌ "This makes sense to me" → ASK if spec is unclear  
❌ "I'll fix this other thing too" → ONLY do what spec says
❌ "This similar icon/path/string will work" → COPY EXACTLY what spec says
❌ "Old data will be fine" → ASK about data migration

### How to Ask:

```
QUESTION: The specification doesn't indicate whether the Save button
should be left-aligned, right-aligned, or centered. Which alignment
should I use?

QUESTION: The spec mentions adding notify_mentions to list_display,
but I don't see this field in the EmailPreferences model. Should I
add the model field first, or is this a typo?

QUESTION: Should the email_utils.py file be in the prompts/ directory
or prompts/utils/ directory? The path isn't specified.

QUESTION: The spec changes the notification signal link format, but
doesn't mention existing notifications in the database. Should I
create a management command to backfill old records?

QUESTION: The spec says to add icon-square-check to the sprite but
the SVG paths provided look different from the standard Lucide
square-check icon. Should I use the exact paths from the spec or
the standard Lucide version?
```

---

## 📊 REPORTING RESULTS

### After Completing Work:

Provide a **detailed report** with:

1. **Summary** - What you accomplished
2. **Files changed** - Complete list with line counts
3. **Testing performed** - What you tested and results
4. **Issues encountered** - Problems and how you resolved them
5. **Data migration status** - If applicable: command created, output, records updated
6. **Remaining work** - Anything not completed or follow-up needed

### Good Report Format:

```
✅ TASK COMPLETE: Email Preferences Admin Fix

Summary:
────────
Updated EmailPreferencesAdmin in prompts/admin.py to display all 8
notification fields in the admin list view.

Files Modified:
───────────────
1. prompts/admin.py
   - Line 45: Updated list_display attribute
   - Added 'notify_mentions'
   - Added 'notify_weekly_digest'
   - Total: 2 fields added to tuple

Changes Made:
─────────────
Before:
  list_display = (
      'user', 'notify_comments', 'notify_replies',
      'notify_follows', 'notify_likes', 'notify_updates',
      'notify_marketing', 'updated_at'
  )

After:
  list_display = (
      'user', 'notify_comments', 'notify_replies',
      'notify_follows', 'notify_likes', 'notify_mentions',
      'notify_weekly_digest', 'notify_updates',  
      'notify_marketing', 'updated_at'
  )

Testing Performed:
──────────────────
✅ Python syntax check: No errors
✅ Import check: All imports resolve correctly  
✅ Django system check: python manage.py check
   Result: System check identified no issues (0 silenced)

COPY EXACTLY Verification:
──────────────────────────
✅ grep "M21 10.656V19" static/icons/sprite.svg → 1 match

Data Migration:
───────────────
✅ No existing data affected by this change

Manual Testing Needed:
──────────────────────
- Navigate to /admin/prompts/emailpreferences/
- Verify all 8 notification columns display
- Confirm column headers are correct
- Test sorting by new columns

Issues Encountered:
───────────────────
None. Implementation was straightforward.

Status: ✅ READY FOR REVIEW
```

### Bad Report (Too Brief):

```
Done! Updated admin.py.
```

**Why this is bad:**
- No detail about what changed
- No testing information
- No file paths or line numbers
- Can't verify work was done correctly

---

## 🧪 BASIC TESTING REQUIREMENTS

### You MUST Test:

**1. Syntax and Imports:**
```bash
python -m py_compile [file.py]     # Syntax check
python manage.py check              # Django system check
```

**2. Imports Resolve:**
```python
# Try importing what you created
python manage.py shell
>>> from prompts.models import Notification
>>> from prompts.services.notifications import create_notification
```

**3. Run Test Suite:**
```bash
python manage.py test prompts       # Run all tests
```

**4. Verify COPY EXACTLY Content (if applicable):**
```bash
grep "[unique string from spec]" [filename]
# Must return exactly 1 match
```

**5. No Obvious Errors:**
- Code runs without crashing
- No import errors
- No syntax errors
- Django loads without errors

### You Are NOT Expected To:

❌ Write unit tests (unless spec asks for it)  
❌ Perform comprehensive integration testing  
❌ Review code quality (Claude.ai does this via agents)  
❌ Test edge cases (unless specified)  
❌ Verify business logic correctness

### Report Testing:

```
Testing Performed:
──────────────────
✅ Syntax check: No errors
✅ Import check: Module imports successfully
✅ Django check: System check passed (0 issues)
✅ Test suite: 62/62 passing
✅ COPY EXACTLY verified: grep confirmed 1 match
✅ Manual smoke test: Created test object in shell, no crashes

[If you find issues]
⚠️ Import error: Missing dependency 'requests'
   Solution: Added to requirements.txt

❌ Syntax error: Line 45 has invalid indentation
   Status: BLOCKED - Need clarification on correct structure
```

---

## 🧪 TEST EXECUTION STRATEGY

### Guiding Principle:

**Run targeted tests during development. Run the full suite once at the end.**

Running the full test suite after every small change wastes time. Instead, use targeted test commands during development and only run the full suite as a final verification step.

### During Development (After Each Change):

```bash
# Run ONLY the test class or file you're working on:
python manage.py test prompts.tests.test_notifications.TestAutoMarkSystemNotificationsRead -v2

# Or run a single test method:
python manage.py test prompts.tests.test_notifications.TestAutoMarkSystemNotificationsRead.test_system_notifications_auto_marked_on_page_load -v2

# Or run the whole test file if changes span multiple classes:
python manage.py test prompts.tests.test_notifications -v2
```

### Final Verification (Once, After All Changes Complete):

```bash
# Full suite — run exactly ONCE at the end:
python manage.py test prompts -v2
```

### Why This Matters:

| Approach | Time per Spec | Wasted Time |
|----------|--------------|-------------|
| Full suite after every change | ~12 min × 4 runs = 48 min | ~36 min wasted |
| Targeted tests + 1 full run | ~2 min × 4 + 12 min = 20 min | ~0 min wasted |

### Rules:

1. **Identify the relevant test class(es)** before running any tests
2. **Run targeted tests** after each code change during development
3. **Run the full suite exactly once** as the final step before reporting
4. **If the full suite reveals a failure** in an unrelated test, investigate — don't re-run the entire suite hoping it passes
5. **Agent reviews happen AFTER the full suite passes** — never before

---

## 🤖 MANDATORY WSHOBSON/AGENTS USAGE

### Critical Requirement:

**YOU MUST use wshobson/agents on EVERY implementation task.**

This is NOT optional. Agents help you write better code, catch issues early, and ensure production-quality implementations on the first attempt.

### What Are wshobson/agents?

**wshobson/agents** is an npm package installed in your Claude Code environment providing 85 specialized AI agents organized into 63 plugins. These agents are experts in specific domains and help you during implementation.

**Key Stats:**
- 85 specialized agents
- 63 focused plugins  
- 47 agent skills
- 15 workflow orchestrators

**Documentation:** https://github.com/wshobson/agents

### How to Invoke Agents:

**Natural Language (Recommended):**
```
"Use django-pro to verify model design"
"Have security-auditor scan for vulnerabilities"
"Get test-automator to generate comprehensive tests"
```

**Slash Commands (Direct):**
```
/python-development:python-scaffold fastapi-microservice
/backend-development:feature-development user authentication
/security-scanning:security-sast
```

### Essential Agents for Django Projects:

**Python & Django Development:**
- **python-pro** - Python 3.12+ expert, async patterns, modern tooling
- **django-pro** - Django specialist, ORM, signals, migrations, admin
- **fastapi-pro** - FastAPI for API development

**Architecture & Design:**
- **backend-architect** - API design, REST/GraphQL, service patterns
- **database-architect** - Schema design, migrations, optimization

**Quality & Testing:**
- **test-automator** - Pytest test generation, edge cases, comprehensive coverage
- **code-reviewer** - Code quality, architectural review, best practices

**Security & Performance:**
- **security-auditor** - OWASP, vulnerability scanning, security patterns
- **performance-engineer** - Query optimization, caching, profiling

**DevOps & Deployment:**
- **deployment-engineer** - CI/CD, containerization, cloud deployment
- **devops-troubleshooter** - Environment issues, configuration problems

**Database & Data:**
- **sql-pro** - SQL queries, migrations, database patterns
- **database-optimizer** - Query performance, indexing strategies
- **database-admin** - Migration execution, database management

**Frontend & UI:**
- **frontend-developer** - React, modern JavaScript, component design
- **ui-ux-designer** - Interface design, accessibility, user experience

### When to Use Which Agents:

**Model Changes:**
```
Use: django-pro, database-architect, security-auditor
"Have django-pro verify model design"
"Use database-architect for migration strategy"
"Get security-auditor to check for data exposure risks"
```

**View Functions:**
```
Use: django-pro, backend-architect, security-auditor
"Have django-pro check Django patterns"
"Use backend-architect for API design validation"
"Get security-auditor for input validation review"
```

**Templates & UI:**
```
Use: ui-ux-designer, frontend-developer, security-auditor
"Have ui-ux-designer verify accessibility"
"Use frontend-developer for JavaScript patterns"
"Get security-auditor to check for XSS vulnerabilities"
```

**Database Migrations:**
```
Use: django-pro, database-architect, database-admin
"Have django-pro verify migration safety"
"Use database-architect for schema design"
"Get database-admin to validate migration steps"
```

**Testing:**
```
Use: test-automator, django-pro
"Have test-automator generate pytest cases"
"Use django-pro to verify Django test patterns"
```

**Bug Fixes:**
```
Use: debugging-toolkit, code-reviewer, django-pro
"Use debugging-toolkit for root cause analysis"
"Have code-reviewer identify anti-patterns"
"Get django-pro to suggest Django-specific solutions"
```

**Security Features:**
```
Use: security-auditor, backend-architect, django-pro
"Have security-auditor perform OWASP review"
"Use backend-architect for secure API design"
"Get django-pro to verify Django security settings"
```

### ✅ PRE-AGENT SELF-CHECK

**Before invoking ANY agent, manually verify these items:**

- [ ] DOM nesting matches tree diagram (if UI change)
- [ ] COPY EXACTLY content verified with grep (if applicable)
- [ ] No text using --gray-400 or lighter in CSS changes
- [ ] Focus management on any DOM removal
- [ ] Data migration addressed (if backend change)
- [ ] All tests pass (`python manage.py test prompts`)

**If any check fails, fix the issue FIRST, then run agents. This prevents the fix-and-rerun cycle that causes low first-pass scores.**

### ⛔ AGENT MINIMUM REJECTION CRITERIA

**Agents MUST score below 6 if ANY of these are true:**

- **UI Agent:** DOM nesting does not match the tree diagram in the spec
- **UI Agent:** Layout has wrong number of columns or wrong element hierarchy
- **Accessibility Agent:** Any text element uses --gray-400 or lighter
- **Accessibility Agent:** Interactive elements removed from DOM without focus management
- **Accessibility Agent:** Missing aria-labels on interactive elements
- **Code Reviewer:** Exact-copy content was substituted with alternatives
- **Django Expert:** Backend change has no data migration when existing data is affected

**These are non-negotiable. Do not rate above 7 if any of the above are present.**

**All agent ratings must be 8+/10. If below, fix the issues and re-run the agent.**

### MANDATORY Reporting Requirement:

**Every completion report MUST include an "Agent Usage Report" section.**

### Required Format:

```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. [Agent Name] - [Rating/10] - [Brief findings]
2. [Agent Name] - [Rating/10] - [Brief findings]
[Additional agents if used]

Critical Issues Found: [Number]
Recommendations Implemented: [Number]
Overall Assessment: [APPROVED/NEEDS REVIEW]
```

### Good vs Bad Agent Reporting:

**✅ GOOD Agent Reporting:**
```
🤖 AGENT USAGE REPORT:

Agents Consulted:
1. @django-pro - 9.0/10 - Confirmed proper use of OneToOneField and signals
2. @security-auditor - 8.5/10 - Recommended token hashing in preferences
3. @code-reviewer - 9.5/10 - Clean implementation, no code smells

Critical Issues Found: 0
Recommendations Implemented: 1 (token hashing)
Overall Assessment: APPROVED
```

**❌ BAD Agent Reporting (Too Vague):**
```
I used some agents to help.
```
**Problem:** No detail, can't verify agents were actually used

**❌ BAD Agent Reporting (No Mention):**
```
✅ TASK COMPLETE: Email Preferences Admin Fix

[No agent section at all]
```
**Problem:** Violates mandatory reporting requirement

**❌ BAD Agent Reporting (Generic):**
```
🤖 AGENT USAGE REPORT

Agents: @django-pro, @security-auditor
They all said it looks good.
```
**Problem:** No specific tasks, findings, or ratings

### Consequences of Not Using Agents:

**If you submit work WITHOUT proper agent usage and reporting:**

1. ❌ Work marked as **INCOMPLETE**
2. ❌ Requires **rework and re-submission**
3. ❌ Additional iteration overhead
4. ❌ Delays project progress
5. ❌ Lower confidence in code quality

**Expected behavior:**
- Use agents proactively on every task
- Report agent usage comprehensively
- Include specific findings and ratings
- Demonstrate agents contributed to quality

### Why This Matters:

**Pattern from experience:** Agents + Reporting = Quality + Efficiency

| Approach | Agent Usage | Agent Reporting | Result |
|----------|-------------|-----------------|--------|
| Worst | ❌ Not used | ❌ Not reported | Multiple iterations needed |
| Partial | ✅ Used | ❌ Not reported | Emergency fixes required |
| Best | ✅ Used | ✅ Reported | One-shot success ✅ |

### Quick Reference:

**Before starting ANY task, ask yourself:**

1. Which agents should I use for this task?
2. How will each agent contribute?
3. What will I ask each agent to verify?

**After completing ANY task, verify:**

1. Did I invoke appropriate agents?
2. Did I document what each agent did?
3. Did I include agent findings in my report?
4. Did I explain why I chose these agents?
5. **Are all agent ratings 8+/10?** (If not, fix and re-run)

If you answer "no" to ANY question above, your work is incomplete.

---

## 🚨 ERROR HANDLING

### When You Encounter Errors:

**1. Try to resolve simple issues:**
- Missing imports → Add them
- Syntax errors → Fix them
- Typos → Correct them

**2. Report blockers immediately:**
```
❌ BLOCKED: Cannot complete task

Error: Migration 0030_emailpreferences already exists

This appears to be a conflict with existing migrations. The
specification asked me to create this migration, but it already
exists in prompts/migrations/.

Possible solutions:
A) Use existing migration (if it contains same changes)
B) Create new migration with different number (0031)
C) Delete existing 0030 and recreate

Please advise which approach to take.
```

**3. Don't guess or make assumptions:**

❌ "I'll just delete the old migration" → DANGEROUS  
❌ "I'll skip this part" → INCOMPLETE  
❌ "I'll implement it differently" → NOT WHAT WAS ASKED  
❌ "This similar content will work" → COPY EXACTLY WHAT SPEC SAYS
❌ "Old data will be fine" → ASK ABOUT DATA MIGRATION

✅ "I encountered [error]. Possible solutions are [A, B, C]. Which should I use?"

### Error Report Format:

```
❌ ERROR ENCOUNTERED

Task: [What you were doing]
Error: [Exact error message]
Location: [File and line if applicable]
Context: [What led to this error]

Attempted Solutions:
1. [What you tried]
   Result: [What happened]
2. [Another attempt]
   Result: [What happened]

Current Status: BLOCKED
Recommendation: [Your suggestion for resolution]
```

---

## 📝 COMMUNICATION BEST PRACTICES

### DO:

✅ **Be precise and detailed**
```
"Updated prompts/admin.py line 45"
NOT "Fixed the admin"
```

✅ **Use exact file paths**
```
"prompts/templates/prompts/settings_notifications.html"
NOT "the settings template"
```

✅ **Quote exact error messages**
```
"ModuleNotFoundError: No module named 'cloudinary'"
NOT "It said something about cloudinary"
```

✅ **List all changes**
```
"Modified 3 files:
1. prompts/models.py (added field)
2. prompts/admin.py (updated list_display)  
3. prompts/forms.py (added field to form)"
```

✅ **Show before/after for modifications**
```
Before: list_display = ('user', 'email')
After:  list_display = ('user', 'email', 'created_at')
```

✅ **Confirm COPY EXACTLY content**
```
Verified: grep "M21 10.656V19" static/icons/sprite.svg → 1 match ✅
```

### DON'T:

❌ **Be vague**
```
"Made some changes"
"Fixed stuff"
"Updated things"
```

❌ **Assume user knows what you did**
```
"Done!"
[User has no idea what changed]
```

❌ **Skip testing information**
```
"Implemented the feature"
[Did you test it? Any errors?]
```

❌ **Make changes beyond the spec**
```
"Also refactored the view while I was there"
[Only do what spec asks]
```

❌ **Substitute similar content**
```
"Used a different icon that looks similar"
[COPY EXACTLY what spec says]
```

---

## 🎯 SCOPE ADHERENCE

### Stay Within Specification Boundaries:

**DO only what the spec asks:**
```
Spec says: "Add notify_mentions to list_display"
You do: Add notify_mentions to list_display
        Report: Done ✅
```

**DON'T add extra work:**
```
Spec says: "Add notify_mentions to list_display"
You do: Add notify_mentions ✅
        Also refactor entire admin class ❌
        Also add search_fields ❌
        Also reorganize imports ❌

This is scope creep - stick to the spec.
```

### If You See Opportunities for Improvement:

**Report them, don't implement:**
```
✅ TASK COMPLETE: [What was asked]

Note: While implementing this, I noticed that the admin class
could benefit from search_fields for better UX. The current
implementation works as specified, but consider adding:

search_fields = ['user__username', 'user__email']

This is outside the current spec but might be worth considering
for future improvements.
```

---

## ✅ VERIFICATION CHECKLIST

Before reporting "COMPLETE", verify:

- [ ] All files mentioned in spec were modified/created
- [ ] No syntax errors in modified files
- [ ] Imports resolve correctly
- [ ] Django system check passes
- [ ] Test suite passes (all existing + new tests)
- [ ] Basic smoke test performed (if applicable)
- [ ] No obvious errors or crashes
- [ ] **COPY EXACTLY content verified with grep** (if applicable)
- [ ] **DOM nesting matches tree diagram** (if applicable)
- [ ] **Accessibility built in during implementation** (if UI changes)
- [ ] **Data migration addressed** (if backend logic changed)
- [ ] **Agent ratings all 8+/10** (re-run if below)
- [ ] Report includes all required information
- [ ] Questions asked if anything was unclear
- [ ] Stayed within scope of specification

---

## 📚 PROJECT-SPECIFIC NOTES

### This Django Project:

**Project Structure:**
- Main app: `prompts/`
- Settings: `prompts_manager/`
- Templates: `prompts/templates/prompts/`
- Tests: `prompts/tests/`
- Migrations: `prompts/migrations/`
- Services: `prompts/services/`
- Views: `prompts/views/`
- Signals: `prompts/signals/`
- Management commands: `prompts/management/commands/`

**Key Files:**
- Models: `prompts/models.py`
- Views: `prompts/views/` (directory with multiple view files)
- Admin: `prompts/admin.py`
- Forms: `prompts/forms.py`
- URLs: `prompts/urls.py`
- Services: `prompts/services/notifications.py`
- Signals: `prompts/signals/notification_signals.py`
- Static CSS: `static/css/pages/`, `static/css/components/`
- Static JS: `static/js/`
- SVG Sprite: `static/icons/sprite.svg`

**Testing Commands:**
```bash
python manage.py check              # System check
python manage.py test prompts       # Run tests
python manage.py makemigrations     # Create migrations
python manage.py migrate            # Apply migrations
```

**Common Imports:**
```python
from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.contrib import admin
from prompts.services.notifications import create_notification
```

---

## ⚠️ CRITICAL REMINDERS

### Never:
- Assume when unclear (ask questions)
- Skip testing (basic checks are required)
- Make changes beyond spec scope
- Provide vague reports
- Ignore errors or warnings
- Delete migrations without asking
- Make breaking changes without confirmation
- **Substitute content marked "COPY EXACTLY"**
- **Bolt accessibility on after implementation**
- **Ignore existing data when changing backend logic**
- **Rate agent scores above 7 when rejection criteria are met**
- **Implement DOM nesting different from the tree diagram**

### Always:
- Read complete specification first
- Ask clarifying questions
- Test your changes (basic checks + full test suite)
- Provide detailed reports
- Quote exact errors
- Stay within specification scope
- Report blockers immediately
- **Build accessibility in from the start**
- **Copy exact content verbatim and verify with grep**
- **Consider data migration for backend changes**
- **Apply agent rejection criteria strictly**
- **Match DOM structure tree diagrams exactly**

---

## 🎯 SUCCESS METRICS

You're doing well when:
- Specifications are implemented correctly first time
- Questions asked prevent rework
- Reports are detailed and informative
- Errors are caught early and reported clearly
- No surprises or undocumented changes
- Claude.ai can review your work easily
- User knows exactly what was done
- **Agent scores are 8+/10 on first pass** (not just after fixes)
- **Accessibility is addressed during implementation, not after**
- **COPY EXACTLY content matches character-for-character**
- **Existing data is accounted for in backend changes**
- **DOM nesting matches tree diagrams exactly**

---

## 💡 EXAMPLES FROM PROJECT

### Good Question (Asking for Clarification):

```
QUESTION: The specification says to "add notify_mentions to list_display"
but doesn't specify where in the tuple it should be positioned.

Looking at the existing list_display:
('user', 'notify_comments', 'notify_replies', 'notify_follows',
 'notify_likes', 'notify_updates', 'notify_marketing', 'updated_at')

Should notify_mentions be:
A) After notify_likes (grouped with other notification fields)
B) Before updated_at (chronological order)
C) Specific position [please specify]

This affects column ordering in the admin interface.
```

### Good Question (Data Migration):

```
QUESTION: The spec changes the notification signal to include #comments
in the link, but there are existing notifications in the database with
the old link format. Should I:
A) Create a management command to backfill existing links
B) Only apply to new notifications going forward
C) Create a Django data migration

The old notifications will have broken anchor links without backfill.
```

### Good Report (Detailed and Actionable):

```
✅ TASK COMPLETE: Added SQLite Test Database Configuration

Summary:
────────
Modified Django settings to use SQLite in-memory database for tests
while keeping PostgreSQL for development and production.

Files Modified:
───────────────
1. prompts_manager/settings.py
   - Added lines 145-152: Test database configuration
   - Imports sys module for argv checking
   - Conditional database override for test runs

Code Added:
───────────
# Test database configuration (line 145)
import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

Testing Performed:
──────────────────
✅ Syntax check: No errors
✅ Settings import: python manage.py check
   Result: System check identified no issues (0 silenced)
✅ Test database creation: python manage.py test --no-input
   Result: Created test database successfully
   Output: "Creating test database for alias 'default'
            ('file:memorydb_default?mode=memory&cache=shared')..."

Verification:
─────────────
Confirmed that:
- Production database URL unchanged (PostgreSQL from env)
- Test runs use SQLite in memory
- No permission errors
- Tests can create/destroy database

Status: ✅ READY FOR TESTING
Next: User should run: python manage.py test prompts
```

### Bad Report (Too Brief):

```
Done. Added config to settings.
```

**Why bad:** No detail, no testing info, no verification

---

**END OF CC COMMUNICATION PROTOCOL**

*Follow this protocol for every task. Consistent communication leads to better outcomes and fewer iterations.*

---

## 📄 RELATED DOCUMENTS

- **CC_SPEC_TEMPLATE.md** - Specification template (v2, aligned with this protocol)
- **CLAUDE_CODE_INTEGRATION.md** - Specification format details
- **AGENT_TESTING_SYSTEM.md** - How code quality is reviewed (not your job)
- **PROJECT_FILE_STRUCTURE.md** - Where files live

**Note:** Your job is implementation and reporting. Claude.ai handles strategic decisions, architecture, and quality assurance through agent testing.
