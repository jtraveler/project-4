# HANDOFF DOCUMENT TEMPLATE STRUCTURE

**This shows the EXACT structure every handoff document must have**

---

## 📋 REQUIRED SECTIONS (IN THIS ORDER)

```markdown
# CUSTOM SESSION CONTINUATION BOILERPLATE
**From Chat:** [URL]
**Date:** [Date]
**Ready to paste into NEW chat**

---

═══════════════════════════════════════════════════════════════
SESSION START: [Phase/Task Name] - [Brief Description]
═══════════════════════════════════════════════════════════════

READ PROJECT KNOWLEDGE (Required):
──────────────────────────────────
Please read these 4 core documents from project knowledge:

1. PROJECT_COMMUNICATION_PROTOCOL.md
   - Code sharing rules (Manual vs CC vs Terminal)
   - **DUAL AGENT SYSTEM** (wshobson/agents + Agent Testing)
   - Agent testing (you orchestrate automatically)
   - When creating CC specs, include: "Read docs/CC_COMMUNICATION_PROTOCOL.md first"

2. AGENT_TESTING_SYSTEM.md
   - 8 specialized review personas (you act as these)
   - When to use which agents
   - Rating system (8+/10 required before commit)
   - Works WITH wshobson/agents (different systems)

3. CLAUDE_CODE_INTEGRATION.md
   - How I work with Claude Code (VS Code)
   - Specification format requirements

4. PROJECT_FILE_STRUCTURE.md
   - Django project layout
   - Where all files live

CRITICAL REMINDERS:
───────────────────
✅ **TWO SEPARATE AGENT SYSTEMS:**
   - **System 1: wshobson/agents** (82+ agents CC uses DURING implementation)
     Examples: @django-expert, @ui, @code-review, @test, @debug
   - **System 2: Agent Testing** (8 personas YOU act as AFTER CC finishes)
     Examples: @django-pro, @security, @code-quality, @ux-reviewer
   - BOTH systems on every feature = maximum quality

✅ Automatically suggest agent testing (System 2) after CC finishes
✅ Specify wshobson/agents (System 1) in all CC specifications
✅ Choose agents based on code type (I don't need to know the details)
✅ Only share code when there's clear ACTION to take
✅ Include CC protocol reminder in all specifications
✅ Use judgment: manual fixes vs CC specifications

✅ **TOKEN TRACKING:**
   - Show token status on EVERY substantive response
   - Format: 📊 Token Status Check with usage/remaining/status
   - Warn at 75%, 85%, 90%, 95%

✅ **TESTING PROTOCOL:**
   - Maximum 2 tests at once
   - Wait for explicit confirmation before proceeding
   - If test fails, stop immediately
   - One test → verify → next test
   - Never assume tests completed

PREVIOUS SESSION SUMMARY:
─────────────────────────
**Session Duration:** [Duration] (ended abruptly due to length)

**What We Accomplished:**
✅ [Major accomplishment 1]
   - [Detail]
   - [Detail]

✅ [Major accomplishment 2]
   - [Detail]

✅ **Commits Completed:**
[Number] commits pushed

**Commit 1:** [Title]
```
[Full commit message with all details]
```

**Commit 2:** [Title]
```
[Full commit message]
```

[Continue for all commits...]

**Critical Issue Discovered During [Phase]:**
🚨 **[Issue Name]**
- [Description of what's wrong]
- [Impact]
- [Current symptoms]
- [Why it's blocking progress]

**Session Ended:** [What was happening when it ended]

CURRENT STATE:
──────────────
**Project:** [Project Name] (Django [version])
**Deployed:** [Heroku/Other]
**Branch:** [branch name]

**Phase [X]: [Status]** ([Percentage]% complete)
- [What's complete]
- [What's complete]

✅ [Completed item 1]
✅ [Completed item 2]
✅ [Completed item 3]

❌ **BLOCKER: [Critical Issue]**
- [Description]
- [Why it blocks progress]
- [What needs fixing]

**Phase [X+1]: PENDING**
- [Next phase items]

TASK OBJECTIVE:
───────────────
**IMMEDIATE PRIORITY:** [One sentence description of the fix needed]

**The Problem:**
[Detailed explanation of what's wrong]

**Required Fix:**
[Specific solution needed]

**Example Code (if applicable):**
```[language]
[Show current WRONG code]

[Show required CORRECT code]
```

**After fixing, complete [Commit/Phase], then proceed to [Next Step].**

CONTEXT:
────────
**How We Got Here:**

**Session 1-X (Previous Chats):**
- [What happened in earlier sessions]
- [Key decisions made]
- [Current foundation]

**Session [Current] (Chat ending [URL]):**
- [What was attempted]
- [What worked]
- [What failed]
- [Where it ended]

**Why This Is Critical:**
- [Business/user impact]
- [Technical impact]
- [What it blocks]

**Technical Details:**
- [Framework versions]
- [Key technologies]
- [Configuration details]
- [File locations]

**Previous Attempts:**
- [What was tried]
- [Results]
- [Lessons learned]

IMPLEMENTATION APPROACH:
────────────────────────
**Step 1: [Action]**

[Detailed instructions]

Commands to run:
```bash
[Exact commands]
```

Expected result:
- [What should happen]

**Step 2: [Action]**

[Detailed instructions]

**Step 3: [Action]**

[Continue for all steps needed...]

QUESTIONS TO ANSWER FIRST:
──────────────────────────
Before creating fix specification, I need to know:

**1. [Question Category]:**
   - [Specific question]
   - [What you need to check]

**2. [Question Category]:**
   - [Specific question]

**3. [Question Category]:**
   - [Specific question]

**4. [Your Preference]:**
   - [Option A or B]
   - [Your comfort level]

TESTING CHECKLIST:
──────────────────
**After Fix Implementation:**

**[Test Category 1]:**
- [ ] [Specific test]
- [ ] [Specific test]
- [ ] [Specific test]

**[Test Category 2]:**
- [ ] [Specific test]
- [ ] [Specific test]

**[Test Category 3]:**
- [ ] [Specific test]

**Manual Testing:**
- [ ] [Browser test description]
- [ ] [Command line test]
- [ ] [Visual verification]

**Agent Testing (After Manual Tests Pass):**
- [ ] @[agent-name] - [What they review]
- [ ] @[agent-name] - [What they review]

DOCUMENTATION UPDATES NEEDED:
──────────────────────────────
After fixing [issue]:

**1. [Document Name]:**
- Update: [What to update]
- Mark: [What to mark complete]
- Add: [What to add]

**2. [Document Name]:**
- Update: [Specific changes]

**3. [Document Name]:**
- Note: [What to document]

COMMIT CRITERIA:
────────────────
**Do NOT commit until:**

✅ [Criterion 1]
✅ [Criterion 2]
✅ [Criterion 3]
✅ All tests passing
✅ Manual testing complete
✅ Agent testing complete (8+/10 ratings)
✅ Documentation updated

**Commit Message Format:**
```
[type]([scope]): [Short description]

- [Detail 1]
- [Detail 2]
- [Detail 3]

[Additional context]
Testing: [What was tested]
[Related info]

[Phase info]
[Resolves info]
```

READY? LET'S [ACTION]! 🚀
════════════════════════

**I need you to:**

1. **[First thing user needs to do]**
   - [Details]

2. **[Second thing]**
   - [Details]

3. **[Third thing]**
   - [Details]

4. **[Choose approach]:**
   - Option A: [Description]
   - Option B: [Description]

Once I know [what you need], I'll create [what they'll get]!
```

---

## 💡 KEY PRINCIPLES

### **1. Completeness**
Every section must be filled out with REAL information from the conversation, not placeholders.

### **2. Specificity**
Use exact:
- Commit messages (full text)
- Error messages
- File paths
- Code examples
- URLs

### **3. Context**
Explain:
- How user got to this point
- Why current issue matters
- What's blocking progress
- Technical reasoning

### **4. Actionability**
Provide:
- Exact commands to run
- Specific questions to answer
- Clear next steps
- Testing procedures

### **5. Token Awareness**
Include reminders about:
- Showing token status regularly
- Testing protocol (max 2 tests)
- Sequential approach
- Explicit confirmation needed

---

## 📊 TOKEN TRACKING FORMAT

Include this in EVERY handoff document in the CRITICAL REMINDERS section:

```markdown
✅ **TOKEN TRACKING:**
   - Show token status on EVERY substantive response
   - Format: 📊 Token Status Check
     Current Usage: ~X / 190,000 tokens
     Remaining: ~Y tokens (Z% left)
     Status: ✅ [message]
   - Warn at 75%, 85%, 90%, 95%
```

---

## 💬 TESTING PROTOCOL FORMAT

Include this in EVERY handoff document in the CRITICAL REMINDERS section:

```markdown
✅ **TESTING PROTOCOL:**
   - Maximum 2 tests at once
   - Wait for explicit confirmation before proceeding
   - If test fails, stop immediately
   - One test → verify → next test
   - Never assume tests completed
   - Verify URLs before creating scripts
   - Double-check environment details
```

---

## ✅ QUALITY CHECKLIST

Before providing the handoff document, verify:

- [ ] All sections present (see template above)
- [ ] Real information (not placeholders)
- [ ] Exact commit messages included
- [ ] Code examples where helpful
- [ ] Specific questions listed
- [ ] Testing checklist comprehensive
- [ ] Token tracking reminders included
- [ ] Testing protocol reminders included
- [ ] File saved as .md
- [ ] Download link provided

---

## 📝 EXAMPLE SNIPPETS

### **Good "What We Accomplished" Section:**
```
✅ **Phase F Day 1: Follow/Unfollow System Foundation**
   - Created Follow model (follower/following relationships)
   - Implemented AJAX endpoints for follow/unfollow
   - Added follow button to user profiles
   - Rate limiting (50 actions/hour)
   - Caching (5min TTL for counts)
   - 10 comprehensive tests created
   - Heroku testing scripts generated
```

### **Good "Current State" Section:**
```
**Phase E: 100% COMPLETE ✅**
- Email Preferences Dashboard
- ARIA Accessibility
- Rate Limiting System (all bugs fixed)
- 71 total tests passing
- Zero security vulnerabilities
- Production verified

**Phase F Day 1: INCOMPLETE (95% done)**
✅ Follow model created
✅ Follow/unfollow endpoints work
✅ Follow button functional (CSRF fixed)

❌ **BLOCKER: Incomplete profile link coverage**
- Need clickable links in MORE places
- Users can't discover profiles easily
```

### **Good "Task Objective" Section:**
```
**IMMEDIATE PRIORITY:** Complete profile link coverage so users can discover profiles naturally

**The Problem:**
Commit 3 added profile links to some places, but we need comprehensive coverage:
- Prompt cards (homepage grid) - Status unknown
- Prompt detail page author - Status unknown  
- Comment authors - Status unknown

**Required Coverage:**
1. **Homepage prompt cards** - Username should link to profile
2. **Prompt detail page** - Author name should link to profile
3. **Comments section** - Comment author names should link to profiles
```

---

## 🎯 FINAL NOTES

The handoff documents you create should be:
- ✅ **Comprehensive** - Everything new Claude needs
- ✅ **Actionable** - Clear next steps
- ✅ **Specific** - Real data, not generic
- ✅ **Complete** - All sections filled
- ✅ **Copy-paste ready** - User pastes and goes

Remember: These handoff documents prevent context loss and enable seamless continuity between sessions. Take the time to make them thorough and accurate!