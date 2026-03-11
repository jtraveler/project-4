# CC_SPEC_BULK_GEN_HARDENING_1 — Sibling-Check Unit Test + Batch Mirror Field Saves

**Spec ID:** HARDENING-1
**Created:** March 11, 2026
**Type:** Micro-Spec — P2 Hardening
**Template Version:** v2.5
**Modifies UI/Templates:** No

---

## ⛔ CRITICAL: READ FIRST

**BEFORE starting this task, Claude Code MUST:**

1. **Read `CC_COMMUNICATION_PROTOCOL.md`** — Contains mandatory agent usage requirements
2. **Read this entire specification** — Don't skip sections
3. **Use required agents** — @django-pro and @test-automator are MANDATORY
4. **Report agent usage** — Include ratings and findings in completion summary

**Work is REJECTED if agents are not run or average score is below 8.0/10.**

---

## 📋 OVERVIEW

Two hardening items from the SMOKE2-FIX-E post-implementation review:

**Part A:** Add a unit test for the sibling-check cleanup path in `rename_prompt_files_for_seo`. This is novel logic with a genuine blast-radius risk (deleting sibling prompts' B2 files). It has no test coverage.

**Part B:** Batch the mirror field `prompt.save()` calls in `rename_prompt_files_for_seo` into a single `save(update_fields=[...])` call. Currently each mirror field update triggers a separate DB write. Minor performance concern today; relevant when bulk-gen jobs contain 20+ images.

---

## 🎯 OBJECTIVES

### Success Criteria

- ✅ Unit test added verifying per-prompt rename task skips `cleanup_empty_prefix` when sibling files remain under `bulk-gen/{job_id}/` prefix
- ✅ Unit test added verifying per-prompt rename task logs empty prefix but does NOT call `delete_object` when prefix is already empty
- ✅ Mirror field saves batched into a single `prompt.save(update_fields=[...])` call
- ✅ No behaviour change — only the number of DB round-trips changes
- ✅ Full test suite passes

---

## 🔧 PART A — Sibling-Check Unit Test

### What to Test

`rename_prompt_files_for_seo` contains a per-prompt sibling check. After moving the primary B2 file, the task calls `list_objects_v2(MaxKeys=1)` on the `bulk-gen/{job_id}/` prefix. If `KeyCount > 0`, it skips cleanup (siblings still exist). If `KeyCount == 0`, it logs that the prefix is empty but does NOT call `delete_object` (cleanup is deferred to the backfill command).

### Test Location

Add to the existing bulk-gen rename test file — wherever `rename_prompt_files_for_seo` tests currently live. If no such file exists, create `prompts/tests/test_bulk_gen_rename.py`.

### Tests Required

**Test 1 — Sibling files present: cleanup skipped**

Mock `list_objects_v2` to return `KeyCount: 1` (sibling exists). Assert `delete_object` is NOT called after the rename completes.

**Test 2 — No sibling files: prefix logged as empty, no delete**

Mock `list_objects_v2` to return `KeyCount: 0`. Assert `delete_object` is NOT called (cleanup is deferred to backfill, not per-prompt task). Assert a log message containing the prefix is emitted.

**Test 3 — Non-bulk-gen prompt: sibling check not triggered**

Create a Prompt with a `media/images/` URL (not bulk-gen). Assert `list_objects_v2` is NOT called at all.

### Mocking Approach

Use `unittest.mock.patch` to mock the B2 boto3 client methods. Do not make real B2 API calls in tests.

---

## 🔧 PART B — Batch Mirror Field Saves

### Current Pattern (in `rename_prompt_files_for_seo`)

After moving the primary URL field, mirror fields are currently updated with individual saves:

```python
setattr(prompt, mirror_field, new_url)
prompt.save(update_fields=[mirror_field])
# ... repeated for each mirror field
```

### Target Pattern

Collect all mirror field updates, then issue a single save:

```python
mirror_fields_updated = []
for mirror_field in sharing_fields[1:]:
    setattr(prompt, mirror_field, new_url)
    mirror_fields_updated.append(mirror_field)

if mirror_fields_updated:
    prompt.save(update_fields=mirror_fields_updated)
```

### Constraint

This change must not alter any field values or the order in which they are set. Only the number of `save()` calls changes. The primary field's save (which already uses `update_fields`) is unchanged — only mirror field saves are batched.

### Verification

```bash
grep -n "prompt.save" prompts/tasks.py
```

The number of `prompt.save` calls in the bulk-gen mirror field update block should decrease from N (one per mirror field) to 1.

---

## ✅ PRE-AGENT SELF-CHECK

⛔ **Before invoking ANY agent, verify all of the following:**

- [ ] Tests for all 3 scenarios exist and pass individually
- [ ] Mock patches cover `list_objects_v2` and `delete_object`
- [ ] Mirror field saves batched — `grep -n "prompt.save" prompts/tasks.py` shows reduction in save calls in the mirror block
- [ ] No behaviour change in non-bulk-gen rename path
- [ ] `python manage.py makemigrations --check` → No changes detected
- [ ] Full test suite passes: `python manage.py test`

---

## 🤖 AGENT REQUIREMENTS

**1. @django-pro**
- Focus: Is `update_fields` used correctly for the batched save? Are the test mock patches correctly scoped (not leaking between tests)? Is `auto_now` or `auto_now_add` on any Prompt field that would be inadvertently updated by the batched save?
- Rating requirement: 8+/10

**2. @test-automator**
- Focus: Do the three tests actually exercise the sibling-check branch? Are the mocks realistic (correct return structure for `list_objects_v2`)? Is the test file organised correctly? Are there any missing edge cases?
- Rating requirement: 8+/10

### ⛔ MINIMUM REJECTION CRITERIA

Agents MUST score below 6 if ANY of these are true:
- Tests make real B2 API calls
- Batched save uses `save()` without `update_fields` (would trigger `auto_now` fields)
- Fewer than 3 test scenarios implemented

---

## ✅ DO / DO NOT

### DO
- ✅ Use `unittest.mock.patch` to mock all B2 client methods
- ✅ Use `update_fields=[...]` on every `prompt.save()` call
- ✅ Find the existing rename test file before creating a new one
- ✅ Run tests in isolation before running the full suite

### DO NOT
- ❌ Do not make real B2 API calls in any test
- ❌ Do not use `prompt.save()` without `update_fields` — this will trigger `auto_now` fields
- ❌ Do not change any function signatures in `rename_prompt_files_for_seo`
- ❌ Do not touch any template files
- ❌ Do not modify upload-flow rename paths — bulk-gen path only

---

## 🧪 TESTING

- [ ] `python manage.py test` — full suite, all pass, report total count
- [ ] New tests run in isolation: `python manage.py test prompts.tests.test_bulk_gen_rename`

---

## 📊 CC COMPLETION REPORT FORMAT

```
═══════════════════════════════════════════════════════════════
HARDENING-1: SIBLING-CHECK TEST + BATCH SAVES - COMPLETION REPORT
═══════════════════════════════════════════════════════════════

## Section 1: Overview
Describe what this hardening task was, why it existed, and what problems it solved.

## Section 2: Expectations
State what the spec required and whether those expectations were met.

## Section 3: Improvements Made
Detailed list of every change made, organised by file.

## Section 4: Issues Encountered and Resolved
For every problem hit during implementation, state the root cause and the exact fix applied.

## Section 5: Remaining Issues
Any issues not resolved, with exact recommended solutions including file name, location, and what needs to change.

## Section 6: Concerns and Areas for Improvement
Process or code quality concerns with specific actionable guidance.

## Section 7: Agent Ratings
Full table: agent name, score, key findings, whether findings were acted on. Include round number. State average and whether it met the 8.0 threshold.

## Section 8: Recommended Additional Agents
Agents not used that would have added value, and what each would have reviewed.

## Section 9: How to Test
Manual steps and automated test commands, specific and actionable.

## Section 10: Commits
Every commit hash and its description.

## Section 11: What to Work on Next
Ordered list of recommended next steps.
═══════════════════════════════════════════════════════════════
```

---

## 💾 COMMIT

```
test(bulk-gen): add sibling-check unit tests for rename cleanup path

Adds 3 tests covering the per-prompt sibling-check logic introduced
in SMOKE2-FIX-E: sibling present (skip cleanup), no sibling (log only,
no delete), non-bulk-gen prompt (check not triggered).

Also batches mirror field prompt.save() calls into a single
save(update_fields=[...]) — reduces DB round-trips from N to 1
for bulk-gen prompts with multiple sharing URL fields.

Agent ratings: @django-pro X/10, @test-automator X/10
```
