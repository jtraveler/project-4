# Demographic Tag Ordering Fix — Completion Report

**Date:** February 15, 2026
**Spec:** DEMOGRAPHIC TAG ORDERING FIX
**Session:** 84 (continued)
**Status:** Complete — Ready for Commit

---

## Summary

Fixed demographic tags appearing in random positions after Pass 1 and Pass 2 runs.
The root cause was twofold: `tags.set()` in django-taggit does not guarantee insertion
order in the database, and the validator treated all demographic tags as a single
group without sub-sorting male/female to the very end.

**Display order now:**
```
BEFORE: photorealistic, cinematic, beard, man, male, middle-aged, warm-tones
AFTER:  photorealistic, cinematic, beard, warm-tones, middle-aged, man, male
```

---

## Files Modified

| File | Lines Changed | What Changed |
|------|---------------|--------------|
| `prompts/tasks.py` | ~25 | `GENDER_LAST_TAGS` module-level constant, 3-tier sort in `_validate_and_fix_tags()`, Pass 2 `tags.set()` replaced with `clear()` + ordered `add()`, Pass 1 sequential `add()` |
| `prompts/tests/test_validate_tags.py` | ~45 | 4 new unit tests + 1 strengthened assertion |
| `prompts/tests/test_pass2_seo_review.py` | ~45 | 1 new integration test |

---

## Implementation Details

### Part 1: Validator Ordering (tasks.py `_validate_and_fix_tags()`)

Added `GENDER_LAST_TAGS = {'male', 'female'}` at module level alongside `DEMOGRAPHIC_TAGS`.
Updated Check 7 (demographic reordering) from a 2-tier sort to a 3-tier sort:

```python
# BEFORE: 2-tier (content → all demographics)
content_tags = [t for t in deduped if t not in DEMOGRAPHIC_TAGS]
demo_tags = [t for t in deduped if t in DEMOGRAPHIC_TAGS]
deduped = content_tags + demo_tags

# AFTER: 3-tier (content → demographics except male/female → male/female)
content_tags = [t for t in deduped if t not in DEMOGRAPHIC_TAGS]
demo_other = [t for t in deduped if t in DEMOGRAPHIC_TAGS and t not in GENDER_LAST_TAGS]
demo_gender = [t for t in deduped if t in GENDER_LAST_TAGS]
deduped = content_tags + demo_other + demo_gender
```

### Part 2: Pass 2 Tag Application (tasks.py `run_seo_pass2_review()`)

Replaced `prompt.tags.set(tag_objects)` with `clear()` + sequential `add()` to
guarantee `TaggedItem.id` values are sequential and match the validated list order:

```python
# BEFORE:
prompt.tags.set(tag_objects)

# AFTER:
prompt.tags.clear()
for tag_name in validated_tags:
    tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
    prompt.tags.add(tag_obj)
```

This code is already inside `transaction.atomic()` with `select_for_update()` (line 2165),
so atomicity is guaranteed.

### Part 3: Pass 1 Tag Application (tasks.py `generate_ai_content()`)

Changed from bulk `prompt.tags.add(*existing_tags)` to sequential `add()` in validated
order. The original code also lost ordering because `values_list()` QuerySets don't
preserve the input list order:

```python
# BEFORE: bulk add (order not guaranteed)
existing_tags = Tag.objects.filter(name__in=tags).values_list('name', flat=True)
prompt.tags.add(*existing_tags)

# AFTER: sequential add (preserves validated order)
existing_tag_names = set(
    Tag.objects.filter(name__in=tags).values_list('name', flat=True)
)
for tag_name in tags:
    if tag_name in existing_tag_names:
        prompt.tags.add(tag_name)
```

---

## Tests Added (5 new)

| # | Test Name | File | What It Verifies |
|---|-----------|------|------------------|
| 1 | `test_male_always_after_man` | test_validate_tags.py | "male" is last when man+male present |
| 2 | `test_female_always_after_woman` | test_validate_tags.py | "female" is last when woman+female present |
| 3 | `test_no_gender_tag_demo_still_at_end` | test_validate_tags.py | "man" goes to end even without "male" |
| 4 | `test_multiple_demo_with_male_female_last` | test_validate_tags.py | male+female are the last two (distinct) in a group of 5 demographics |
| 5 | `test_pass2_tags_applied_in_order` | test_pass2_seo_review.py | Integration: mocks Pass 2, verifies TaggedItem.id ordering in DB matches validated order |

**Full suite:** 585 tests pass, 0 failures, 12 skipped.

---

## Agent Reviews

### Round 1 — Below Threshold

All three agents scored below the 8/10 threshold on the first review:

| Agent | Score | Key Concerns |
|-------|-------|--------------|
| @django-pro | 6.5/10 | `GENDER_LAST_TAGS` defined inside function (should be module-level); `clear()+add()` not inside transaction (incorrect — missed surrounding `atomic()` block); Pass 1 "critical bug" (incorrect — behavior preserved) |
| @code-reviewer | 7/10 | Same scope concern; same atomicity concern; N+1 query pattern |
| @test-automator | 6.5/10 | Test 5 assertions "wrong order" (incorrect — misread the spec); Test 4 missing distinctness check; missing edge cases |

### Fixes Applied After Round 1

| Fix | What Changed |
|-----|--------------|
| `GENDER_LAST_TAGS` scope | Moved from inside `_validate_and_fix_tags()` to module level alongside `DEMOGRAPHIC_TAGS` |
| Test 4 distinctness | Added `self.assertNotEqual(result[-1], result[-2])` assertion |

### Issues Disputed (Not Bugs)

| Concern | Why It's Not An Issue |
|---------|----------------------|
| **Transaction atomicity** | The `clear()` + `add()` loop is ALREADY inside `transaction.atomic()` with `select_for_update()` at line 2165. All three agents missed this surrounding context. |
| **Pass 1 "critical bug"** | The new code only calls `add(tag_name)` when `tag_name in existing_tag_names`. Behavior is identical to the original — just sequential instead of bulk. |
| **Test 5 "wrong assertions"** | `ordered_tags[-1] == 'male'` (male is last) and `ordered_tags[-2] == 'man'` (man is before male) IS the correct expected order per the spec. The test-automator misread the requirement. |
| **N+1 queries** | Background Django-Q2 task, max 10 tags, runs at most every 5 minutes per prompt. ~20 queries is negligible. `add(*list)` internally loops the same way. |

### Round 2 — All Pass

| Agent | Score | Verdict |
|-------|-------|---------|
| @django-pro | 9/10 | Confirmed transaction safety, constant scope fixed |
| @code-reviewer | 9/10 | All concerns resolved, production-ready |
| @test-automator | 9.5/10 | Tests correct, spec-compliant |

**Average: 9.2/10 — APPROVED**

---

## Blockers

None. All blockers were resolved during implementation:

| Potential Blocker | Resolution |
|-------------------|------------|
| django-taggit `set()` doesn't preserve order | Replaced with `clear()` + sequential `add()` |
| `values_list()` QuerySet loses input order | Pre-compute set of existing names, iterate original list |
| Agent reviews below 8/10 | Fixed scope issue, disputed incorrect concerns with evidence |

---

## Potential Improvements (Not Implemented — Out of Scope)

### 1. Bulk Tag Creation Optimization

The current loop does one `get_or_create()` + one `add()` per tag (~20 queries for
10 tags). Could pre-build all Tag objects then add sequentially:

```python
tag_objs = [Tag.objects.get_or_create(name=n)[0] for n in validated_tags]
prompt.tags.clear()
for obj in tag_objs:
    prompt.tags.add(obj)
```

This separates lookups from TaggedItem creation, potentially enabling future
bulk_create optimization. Not worth it now — background task, 10 tags max.

### 2. Module-Level Subset Assertion

Add a runtime check that `GENDER_LAST_TAGS` is always a subset of `DEMOGRAPHIC_TAGS`:

```python
assert GENDER_LAST_TAGS.issubset(DEMOGRAPHIC_TAGS), \
    "GENDER_LAST_TAGS must be a subset of DEMOGRAPHIC_TAGS"
```

Prevents future drift if someone adds to one set but not the other. Low priority
since both constants are defined 4 lines apart.

### 3. Template-Level Ordering

Currently relying on `TaggedItem.id` ascending for display order. An alternative
would be to add an explicit `ordering` field to TaggedItem or sort in the template
query. Not needed now since the `clear()` + `add()` pattern guarantees sequential IDs,
but would be more robust if django-taggit ever changes its default ordering.

### 4. Pass 1 Tag Creation

Pass 1 (`generate_ai_content()`) currently skips tags that don't exist in the Tag
table. This means new long-tail tags from AI are silently dropped. A future improvement
would be to use `get_or_create()` instead, similar to Pass 2. Out of scope for this
ordering fix.

---

## Commit Information

**Suggested commit message:**
```
fix(tags): ensure demographic tags display last with male/female at very end

- Add GENDER_LAST_TAGS module-level constant for male/female sub-sorting
- Update _validate_and_fix_tags() to 3-tier sort: content → demographic → male/female
- Replace tags.set() with clear() + ordered add() in Pass 2 for guaranteed
  insertion order in database (already inside transaction.atomic())
- Change Pass 1 tag application to sequential add() preserving validated order
- 5 new tests for demographic ordering and gender-last behavior

Display order: [content tags] → [demographic tags] → [male/female last]
Before: photorealistic, cinematic, beard, man, male, middle-aged, warm-tones
After:  photorealistic, cinematic, beard, warm-tones, middle-aged, man, male

Agent reviews: @django-pro 9/10, @code-reviewer 9/10, @test-automator 9.5/10
```

---

**Report generated:** February 15, 2026
**Tests:** 585 pass / 0 fail / 12 skipped
**Agent average:** 9.2/10
