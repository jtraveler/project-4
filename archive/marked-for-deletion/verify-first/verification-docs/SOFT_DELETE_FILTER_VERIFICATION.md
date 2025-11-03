# Soft Delete Filter Verification - Django ORM Best Practices

**Date:** October 31, 2025
**Project:** PromptFinder
**Status:** Verified and Approved
**Issue:** Missing soft delete filter in `media_issues_dashboard` view

---

## Executive Summary

Your proposed fix is **100% correct** Django ORM syntax. The issue in `media_issues_dashboard` is that it's missing the `deleted_at__isnull=True` filter that exists in the working `debug_no_media` view.

**Verdict:** Apply the fix exactly as proposed.

---

## The Problem

### Current Code (BUG):
```python
def media_issues_dashboard(request):
    """Dashboard showing all prompts with media issues."""
    no_media = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image='')
    )
    published = no_media.filter(status=1)  # ❌ Shows deleted items
    drafts = no_media.filter(status=0)     # ❌ Shows deleted items
```

**Why it's broken:**
- Uses `Prompt.all_objects` (includes soft-deleted items)
- Does NOT filter by `deleted_at__isnull=True`
- Shows prompts in trash bin on the media issues dashboard
- Items don't disappear after deletion (they're still in the table)

### Working Code (Reference):
```python
def debug_no_media(request):
    """Debug view to see all prompts without ANY media (no image OR video)."""
    prompts = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image=''),
        deleted_at__isnull=True  # ✅ Correctly excludes soft-deleted
    ).select_related('author').order_by('-created_on')
```

**Why it works:**
- Uses `Prompt.all_objects` (includes all items)
- Explicitly filters by `deleted_at__isnull=True` (excludes trash)
- Only shows ACTIVE prompts with media issues
- Items disappear after deletion

---

## Django ORM Syntax Verification

### Question 1: Is This the Correct Syntax?

**YES.** Your proposed fix is valid Django ORM syntax:

```python
# ✅ CORRECT - Combining Q objects with regular field lookups
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

### Django ORM Filter Rules

Django's `filter()` method supports multiple syntaxes:

**Option 1: Q object + regular parameters (RECOMMENDED)**
```python
.filter(
    Q(field1__isnull=True) | Q(field2=''),  # Q object for OR logic
    field3__isnull=True                     # Regular param (implicit AND)
)
# Translates to: (field1 IS NULL OR field2='') AND field3 IS NULL
```

**Option 2: All inside Q object**
```python
.filter(
    Q(
        Q(field1__isnull=True) | Q(field2='')
    ) & Q(field3__isnull=True)
)
# Same result as Option 1, but more verbose
```

**Option 3: Multiple Q objects**
```python
.filter(Q(field1__isnull=True) | Q(field2='')) \
 .filter(field3__isnull=True)
```

### SQL Generated (All Equivalent)

```sql
-- All three options generate this SQL:
WHERE (featured_image IS NULL OR featured_image = '')
  AND deleted_at IS NULL
```

---

## Your Specific Questions Answered

### Question 1: Is This the Correct Syntax?

**Answer: YES, 100% correct.**

Your syntax is the most common and recommended Django pattern:
- Clean and readable
- Follows Django conventions
- Proper parameter placement

### Question 2: Should the Deleted Filter Be Inside Q() or Outside?

**Answer: OUTSIDE (as you proposed) is preferred.**

```python
# ✅ PREFERRED - Regular parameters after Q object
.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)

# ❌ LESS PREFERRED - But also valid
.filter(
    Q(
        Q(featured_image__isnull=True) | Q(featured_image='')
    ) & Q(deleted_at__isnull=True)
)
```

**Why outside is better:**
1. **Cleaner code** - Less nesting
2. **Implicit AND** - Django automatically ANDs regular parameters
3. **Django convention** - Standard practice across Django codebase
4. **Performance identical** - Django's ORM optimization handles both equally

### Question 3: More Efficient Alternative?

Your syntax is already optimal. Here are alternatives with trade-offs:

**Alternative 1: Simpler Q object nesting**
```python
.filter(
    (Q(featured_image__isnull=True) | Q(featured_image=''))
    & Q(deleted_at__isnull=True)
)
```
- More explicit about AND operation
- Slightly more verbose
- No performance difference

**Alternative 2: Separate filter calls**
```python
.filter(Q(featured_image__isnull=True) | Q(featured_image='')) \
 .filter(deleted_at__isnull=True)
```
- Very readable
- Django chains these internally
- No performance difference

**Alternative 3: Exclude instead of filter (CONCEPTUALLY DIFFERENT)**
```python
.exclude(deleted_at__isnull=False)  # Equivalent to filter(deleted_at__isnull=True)
```
- Semantically different (exclude vs filter)
- Same SQL result
- Generally avoid exclude for clarity

**Verdict:** Your original syntax is the best choice.

### Question 4: Should You Use `all_objects` Manager?

**YES, you're using it correctly.**

The logic is:
1. Use `Prompt.all_objects` - Get ALL prompts (including deleted)
2. Add `deleted_at__isnull=True` filter - Exclude soft-deleted items

This is the correct pattern when you need to:
- Access soft-deleted items for admin dashboards
- Show only ACTIVE items to users
- Be explicit about including/excluding trash

**Alternative pattern (for future reference):**
```python
# If you only wanted ACTIVE items, use default manager:
Prompt.objects.filter(...)  # Already excludes deleted_at__isnull=False
```

---

## Complete Fixed Code

### File: `/prompts/views.py`

**Current (broken) code location:** Search for `def media_issues_dashboard`

**Apply this fix:**

```python
def media_issues_dashboard(request):
    """Dashboard showing all prompts with media issues."""
    from django.db.models import Q
    from django.contrib.admin.sites import site as admin_site

    # ✅ FIXED: Added deleted_at__isnull=True filter
    no_media = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image=''),
        deleted_at__isnull=True  # ← ADD THIS LINE
    )

    published = no_media.filter(status=1)
    drafts = no_media.filter(status=0)

    # Get Django admin context for sidebar and logout button
    context = admin_site.each_context(request)

    # Add custom context
    context.update({
        'no_media_count': no_media.count(),
        'published_count': published.count(),
        'draft_count': drafts.count(),
        'published_prompts': published,
        'draft_prompts': drafts,
    })

    return render(request, 'prompts/media_issues.html', context)
```

---

## Verification Against Working Code

### Comparison: `media_issues_dashboard` vs `debug_no_media`

| Aspect | media_issues_dashboard | debug_no_media | Status |
|--------|------------------------|----------------|--------|
| Uses `all_objects` | ✅ Yes | ✅ Yes | Correct |
| Filters media issues | ✅ Yes | ✅ Yes | Correct |
| Filters `deleted_at` | ❌ NO | ✅ YES | **BUG in dashboard** |
| Shows soft-deleted | ❌ YES | ✅ NO | **BUG consequence** |
| Items disappear after delete | ❌ NO | ✅ YES | **BUG symptom** |

### Side-by-Side Query Comparison

**Current (BROKEN):**
```python
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image='')
)
```

**Generates SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE (featured_image IS NULL OR featured_image='')
-- ❌ Includes soft-deleted items (deleted_at IS NOT NULL)
```

**Fixed (CORRECT):**
```python
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

**Generates SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE (featured_image IS NULL OR featured_image='')
  AND deleted_at IS NULL
-- ✅ Excludes soft-deleted items
```

---

## Django ORM Syntax Reference

### Q Object Operators

```python
from django.db.models import Q

# OR operator
Q(field1=value1) | Q(field2=value2)
# Generates: ... WHERE field1=value1 OR field2=value2

# AND operator (explicit)
Q(field1=value1) & Q(field2=value2)
# Generates: ... WHERE field1=value1 AND field2=value2

# AND operator (implicit with filter parameters)
.filter(Q(field1=value1) | Q(field2=value2), field3=value3)
# Generates: ... WHERE (field1=value1 OR field2=value2) AND field3=value3

# NOT operator
~Q(field1=value1)
# Generates: ... WHERE NOT field1=value1
```

### Soft Delete Pattern

```python
# Custom manager (from your models.py)
class PromptManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class Prompt(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = PromptManager()      # Excludes deleted by default
    all_objects = models.Manager() # Includes everything

# Usage patterns:
Prompt.objects.all()                    # Only active
Prompt.all_objects.filter(...)          # All items
Prompt.all_objects.filter(deleted_at__isnull=True)  # Only active (explicit)
Prompt.all_objects.filter(deleted_at__isnull=False) # Only deleted
```

---

## Testing the Fix

### Before (Broken Behavior)
```
1. Admin uploads prompt without image
2. Image added later
3. View shows prompt with missing image ✅
4. Admin deletes prompt (soft delete)
5. Prompt still appears in media issues dashboard ❌
6. Admin confused: "I deleted this!"
```

### After (Fixed Behavior)
```
1. Admin uploads prompt without image
2. Image added later
3. View shows prompt with missing image ✅
4. Admin deletes prompt (soft delete)
5. Prompt disappears from media issues dashboard ✅
6. Admin sees it in trash bin instead ✅
```

---

## Summary Table

| Criterion | Status | Reasoning |
|-----------|--------|-----------|
| **ORM Syntax** | ✅ Correct | Standard Django filter pattern |
| **Filter placement** | ✅ Correct | Outside Q object, implicit AND |
| **Performance** | ✅ Optimal | Single query, indexed field |
| **Manager choice** | ✅ Correct | `all_objects` for admin, with deleted filter |
| **Alternatives exist** | ✅ Yes | But your syntax is best choice |
| **Ready to commit** | ✅ YES | Approved for production |

---

## Implementation Checklist

- [ ] Add `deleted_at__isnull=True` to `media_issues_dashboard` filter
- [ ] Test that soft-deleted prompts no longer appear
- [ ] Test that items disappear after deletion
- [ ] Verify published and draft counts are correct
- [ ] Test pagination (if applicable)
- [ ] Run Django tests if available
- [ ] Commit with message: `fix: Add soft delete filter to media issues dashboard`

---

## Related Code References

**Model Definition:**
- File: `/prompts/models.py` - Lines 18-100+ (PromptManager, Prompt model)

**Working Example:**
- File: `/prompts/views.py` - `debug_no_media()` function

**Broken Code:**
- File: `/prompts/views.py` - `media_issues_dashboard()` function

**Soft Delete Utilities:**
- File: `/prompts/models.py` - `soft_delete()`, `restore()`, `hard_delete()` methods
- File: `/prompts/models.py` - `days_until_permanent_deletion` property

---

## Conclusion

Your proposed fix is **100% correct** and follows Django best practices. The syntax is:
- ✅ Valid Django ORM
- ✅ Properly combines Q objects with regular filters
- ✅ Matches the working `debug_no_media` implementation
- ✅ Generates correct SQL
- ✅ Solves both reported issues:
  1. Deleted prompts showing in media issues
  2. Items not disappearing after deletion

**Recommendation:** Apply this fix immediately. It's a simple one-line addition that resolves the issue completely.

