# Django ORM Soft Delete Patterns - Quick Reference

**Purpose:** Quick reference for correct soft delete filtering patterns in Django ORM

---

## The One-Line Answer

```python
# ✅ CORRECT PATTERN
queryset = Model.all_objects.filter(
    Q(condition1=value1) | Q(condition2=value2),  # Q objects for OR/NOT
    deleted_at__isnull=True                        # Regular param for AND
)
```

---

## Pattern Breakdown

### What's Happening

```python
Prompt.all_objects.filter(
    # ① Multiple conditions joined with OR
    Q(featured_image__isnull=True) | Q(featured_image=''),

    # ② Additional filter (implicit AND with Q object)
    deleted_at__isnull=True
)
```

**Translates to SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE (featured_image IS NULL OR featured_image='')
  AND deleted_at IS NULL
```

### Manager Selection

```python
# Use all_objects when you need:
Prompt.all_objects.filter(deleted_at__isnull=True)
# - Access to all items initially
# - Explicit filter to exclude soft-deleted
# - Admin dashboards showing all states

# Use objects when you only want active:
Prompt.objects.filter(...)
# - Already excludes soft-deleted
# - Public-facing queries
# - User profile pages
```

---

## Common Patterns

### Pattern 1: Q Object + Soft Delete Filter

```python
# ✅ RECOMMENDED
queryset = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

**When to use:**
- Multiple OR conditions
- Need to exclude soft-deleted

**Advantages:**
- Clean syntax
- Implicit AND is clear
- Standard Django convention

---

### Pattern 2: All Conditions in Q Object

```python
# ✅ VALID (but verbose)
queryset = Prompt.all_objects.filter(
    Q(
        Q(featured_image__isnull=True) | Q(featured_image='')
    ) & Q(deleted_at__isnull=True)
)
```

**When to use:**
- Very complex conditions
- Want to be explicit about AND

**Disadvantages:**
- More nesting
- Harder to read
- Rarely needed

---

### Pattern 3: Chained Filter Calls

```python
# ✅ VALID (also readable)
queryset = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image='')
).filter(
    deleted_at__isnull=True
)
```

**When to use:**
- Breaking complex queries into steps
- Adding filters conditionally

**Example with conditional logic:**
```python
queryset = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image='')
)

if request.user.is_staff:
    # Show all (including soft-deleted) for staff
    pass
else:
    # Show only active for users
    queryset = queryset.filter(deleted_at__isnull=True)
```

---

### Pattern 4: Using ~Q for NOT

```python
# ✅ VALID (exclude deleted instead of filter)
queryset = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    ~Q(deleted_at__isnull=False)  # Equivalent: deleted_at IS NULL
)

# This is the same as:
queryset = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

**When to use:**
- Rare - stick with `isnull=True` for clarity

---

## Wrong Patterns (❌ Avoid)

### ❌ Mistake 1: Forgetting Soft Delete Filter

```python
# ❌ BROKEN - Includes soft-deleted items
no_media = Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image='')
    # Missing: deleted_at__isnull=True
)
```

**Result:** Deleted items still appear in the queryset

---

### ❌ Mistake 2: Using objects Instead of all_objects

```python
# ❌ BROKEN - Can't add soft delete filter (already applied)
# This works for simple cases but lacks explicitness:
Prompt.objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image='')
)

# Better to be explicit:
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

**Result:** Less clear what filtering is happening

---

### ❌ Mistake 3: Putting All in Q Object

```python
# ❌ WORKS but unnecessarily complex
Prompt.all_objects.filter(
    Q(
        (Q(featured_image__isnull=True) | Q(featured_image=''))
        & Q(deleted_at__isnull=True)
    )
)
```

**Result:** Harder to read, no performance benefit

---

## Performance Considerations

### Query Efficiency

All of these generate the same SQL and have identical performance:

```python
# Option A (Pattern 1 - RECOMMENDED)
.filter(Q(...) | Q(...), deleted_at__isnull=True)

# Option B (Chained)
.filter(Q(...) | Q(...)).filter(deleted_at__isnull=True)

# Option C (In Q object)
.filter(Q((Q(...) | Q(...)) & Q(deleted_at__isnull=True)))
```

**All generate identical SQL:**
```sql
WHERE (condition1 OR condition2) AND deleted_at IS NULL
```

**Performance tip:** Ensure `deleted_at` has a database index:

```python
class Prompt(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['author', 'deleted_at']),
        ]
```

---

## Soft Delete Model Setup

### Required Model Definition

```python
from django.db import models

class PromptManager(models.Manager):
    """Default manager - excludes soft-deleted items"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Prompt(models.Model):
    # ... other fields ...
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this item was soft-deleted"
    )

    # Custom managers
    objects = PromptManager()      # Excludes deleted by default
    all_objects = models.Manager() # Includes everything

    class Meta:
        indexes = [
            models.Index(fields=['deleted_at']),
        ]
```

---

## Usage Quick Reference

### For Public Pages (Users)
```python
# ✅ Shows only active prompts
Prompt.objects.filter(status=1)
# The objects manager already excludes deleted_at__isnull=False
```

### For Admin Dashboards
```python
# ✅ Shows all prompts, explicitly excluding soft-deleted
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True  # Explicit is better than implicit
)

# Or, if you want soft-deleted only:
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=False  # Show only deleted
)
```

### For User Trash Bins
```python
# ✅ Shows only user's soft-deleted prompts
Prompt.all_objects.filter(
    author=request.user,
    deleted_at__isnull=False
).order_by('-deleted_at')
```

---

## SQL Generation Examples

### Example 1: Media Issues (Correct)
```python
Prompt.all_objects.filter(
    Q(featured_image__isnull=True) | Q(featured_image=''),
    deleted_at__isnull=True
)
```

**SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE (featured_image IS NULL OR featured_image = '')
  AND deleted_at IS NULL
ORDER BY created_on DESC;
```

---

### Example 2: User Trash Bin
```python
Prompt.all_objects.filter(
    author_id=1,
    deleted_at__isnull=False
).order_by('-deleted_at')
```

**SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE author_id = 1
  AND deleted_at IS NOT NULL
ORDER BY deleted_at DESC;
```

---

### Example 3: With Complex OR
```python
Prompt.all_objects.filter(
    Q(title__icontains='search') | Q(content__icontains='search'),
    status=1,
    deleted_at__isnull=True
)
```

**SQL:**
```sql
SELECT * FROM prompts_prompt
WHERE (title LIKE '%search%' OR content LIKE '%search%')
  AND status = 1
  AND deleted_at IS NULL;
```

---

## Testing the Pattern

### Unit Test Example
```python
def test_media_issues_excludes_deleted():
    """Verify soft-deleted prompts don't appear in media issues"""
    # Create prompts
    active = Prompt.objects.create(title="Active", author=user)
    deleted = Prompt.objects.create(title="Deleted", author=user)

    # Soft delete one
    deleted.deleted_at = timezone.now()
    deleted.save()

    # Query
    from django.db.models import Q
    no_media = Prompt.all_objects.filter(
        Q(featured_image__isnull=True) | Q(featured_image=''),
        deleted_at__isnull=True
    )

    # Assert
    self.assertIn(active, no_media)      # ✅ Active appears
    self.assertNotIn(deleted, no_media)  # ✅ Deleted doesn't appear
```

---

## Summary

| Need | Pattern | Code |
|------|---------|------|
| Active items only | Use objects manager | `Prompt.objects.all()` |
| All items (admin) | all_objects + filter | `Prompt.all_objects.filter(..., deleted_at__isnull=True)` |
| Deleted items only | all_objects + negate | `Prompt.all_objects.filter(..., deleted_at__isnull=False)` |
| Complex OR logic | Q objects | `Q(cond1) \| Q(cond2)` |
| Combine with AND | Regular params | `.filter(Q(...) \| Q(...), param=value)` |

---

**Created:** October 31, 2025
**For:** PromptFinder Phase F - Admin Tools
**Related:** SOFT_DELETE_FILTER_VERIFICATION.md

