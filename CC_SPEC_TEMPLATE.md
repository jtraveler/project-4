# Claude Code Specification Template

**Last Updated:** November 4, 2025
**Purpose:** Standard template for all Claude Code (CC) specifications
**Status:** Active - Use for all CC work

---

## 📋 TEMPLATE STRUCTURE

Every specification for Claude Code MUST include the following sections in this order:

---

## ⚠️ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `docs/CC_COMMUNICATION_PROTOCOL.md`** - Contains mandatory agent usage requirements
2. **Read this entire specification** - Don't skip sections
3. **Use required agents** - Minimum 2-3 agents appropriate for the task
4. **Report agent usage** - Include ratings and findings in completion summary

**This is non-negotiable per the project's CC Communication Protocol.**

---

## 📋 OVERVIEW

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

[Repeat for each file]

---

## 🤖 AGENT REQUIREMENTS

**MANDATORY: Use wshobson/agents during implementation**

Per `docs/CC_COMMUNICATION_PROTOCOL.md`, CC must use appropriate agents for this task.

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

3. **Documentation**
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

### Example Specs Using This Template

See recent Phase F work:
- PHASE_F_DAY2.5_COMPLETION_REPORT.md
- PHASE_F_DAY2_COMPLETION_REPORT.md
- Phase F Day 2.7 (this session)

These demonstrate proper use of this template structure.

---

## 📞 QUESTIONS?

If unclear on any section:
1. Ask the user for clarification
2. Reference CC_COMMUNICATION_PROTOCOL.md
3. Look at example specs (Phase F work)

**Never skip agent testing or reporting!**

---

**END OF TEMPLATE**

Use this template for all Claude Code specifications to ensure consistent quality and professional deliverables.
