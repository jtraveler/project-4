# Similar Prompt Redirect - Implementation Guide

**Goal:** When users/bots access deleted prompts, redirect to similar prompts (301/302)

---

## Phase 1: Tag-Based Matching (SIMPLE - Start Here)

### Step 1: Add Helper Function to `prompts/views.py`

```python
def find_similar_prompt(deleted_prompt):
    """
    Find most similar active prompt based on shared tags.

    Matching priority:
    1. Most shared tags (3 match > 2 match > 1 match)
    2. Most likes (popularity signal)
    3. Most recent (freshness)

    Args:
        deleted_prompt: Prompt object (deleted or in trash)

    Returns:
        Prompt object or None
    """
    from django.db.models import Count

    # Get all active prompts with matching tags
    similar = Prompt.objects.filter(
        tags__in=deleted_prompt.tags.all(),  # Has same tags
        status=1,  # Published
        deleted_at__isnull=True  # Not deleted
    ).exclude(
        id=deleted_prompt.id  # Not itself (in case of soft delete)
    ).annotate(
        shared_tags=Count('tags')  # Count matching tags
    ).order_by(
        '-shared_tags',  # Most tags in common first
        '-likes_count',  # Then most popular
        '-created_on'    # Then most recent
    ).first()

    if similar:
        return similar

    # Fallback 1: Same AI generator (e.g., all Midjourney prompts)
    similar = Prompt.objects.filter(
        ai_generator=deleted_prompt.ai_generator,
        status=1,
        deleted_at__isnull=True
    ).exclude(id=deleted_prompt.id).order_by('-likes_count').first()

    if similar:
        return similar

    # Fallback 2: Any popular prompt
    similar = Prompt.objects.filter(
        status=1,
        deleted_at__isnull=True
    ).order_by('-likes_count').first()

    return similar
```

### Step 2: Update `prompt_detail` View (Lines 204-206)

**Before:**
```python
else:
    # Non-owner: Show 404
    raise Http404("Prompt not found")
```

**After:**
```python
else:
    # Non-owner: Redirect to similar prompt
    similar = find_similar_prompt(prompt)

    if similar:
        # Determine status code based on deletion type
        if prompt.days_until_permanent_deletion and prompt.days_until_permanent_deletion > 0:
            # In trash - temporary (302)
            return redirect('prompts:prompt_detail', slug=similar.slug)
        else:
            # About to be deleted - permanent (301)
            response = redirect('prompts:prompt_detail', slug=similar.slug)
            response.status_code = 301  # Permanent redirect
            return response
    else:
        # No similar prompt found - show 404
        raise Http404("Prompt not found")
```

### Step 3: Handle Permanently Deleted Prompts

For prompts already hard-deleted from database, we need a record:

**Create model:** `prompts/models.py`

```python
class DeletedPromptRedirect(models.Model):
    """
    Stores redirect information for permanently deleted prompts.
    Allows SEO-friendly 301 redirects to similar prompts.
    """
    slug = models.SlugField(unique=True, db_index=True)
    redirect_to_slug = models.SlugField()
    deleted_permanently_at = models.DateTimeField(auto_now_add=True)
    original_title = models.CharField(max_length=200)

    # Keep for 90 days, then remove record
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.slug} → {self.redirect_to_slug}"
```

**Update `cleanup_deleted_prompts` command:**

```python
# In prompts/management/commands/cleanup_deleted_prompts.py

for prompt in trashed_prompts:
    if now >= expiry_date:
        # Find similar prompt BEFORE deleting
        similar = find_similar_prompt(prompt)

        if similar:
            # Create redirect record
            from datetime import timedelta
            DeletedPromptRedirect.objects.create(
                slug=prompt.slug,
                redirect_to_slug=similar.slug,
                original_title=prompt.title,
                expires_at=now + timedelta(days=90)
            )

        # Then hard delete
        prompt.hard_delete()
```

**Update `prompt_detail` view to check redirects:**

```python
# At the start of prompt_detail (after line 163)

# Check if this is a permanently deleted prompt
try:
    redirect_record = DeletedPromptRedirect.objects.get(slug=slug)
    # 301 permanent redirect
    response = redirect('prompts:prompt_detail', slug=redirect_record.redirect_to_slug)
    response.status_code = 301
    return response
except DeletedPromptRedirect.DoesNotExist:
    pass  # Continue to normal flow
```

---

## How It Works (User Experience)

### Scenario 1: Prompt in Trash (Soft Deleted)

**User/Bot accesses:** `promptfinder.net/prompts/cyberpunk-city/`

**System logic:**
1. Finds prompt (using `all_objects`)
2. Sees `deleted_at` is not None
3. Calls `find_similar_prompt()`
4. Finds: `promptfinder.net/prompts/neon-metropolis/` (has tags: cyberpunk, neon)
5. Returns **302 redirect** to similar prompt

**User sees:** `neon-metropolis` page (similar content)
**Google sees:** "Temporary redirect, keep original URL in index"

**If restored:** Original URL (`cyberpunk-city`) keeps its SEO value

---

### Scenario 2: Prompt Permanently Deleted

**User/Bot accesses:** `promptfinder.net/prompts/cyberpunk-city/`

**System logic:**
1. Prompt not in database
2. Checks `DeletedPromptRedirect` table
3. Finds record: `cyberpunk-city → neon-metropolis`
4. Returns **301 redirect** to similar prompt

**User sees:** `neon-metropolis` page (similar content)
**Google sees:** "Permanent redirect, transfer SEO value to new URL"

**SEO impact:** Backlinks and rankings transfer to `neon-metropolis`

---

## Matching Quality Examples

### Example 1: Perfect Match (3 Tags)

**Deleted Prompt:**
- Title: "Cyberpunk Neon Cityscape"
- Tags: `cyberpunk`, `cityscape`, `neon`

**Similar Prompt Found:**
- Title: "Neon Metropolis Night Scene"
- Tags: `cyberpunk`, `cityscape`, `neon`, `night`
- **Shared Tags: 3** ✅ Perfect match

---

### Example 2: Good Match (2 Tags)

**Deleted Prompt:**
- Title: "Fantasy Dragon Portrait"
- Tags: `fantasy`, `dragon`, `portrait`

**Similar Prompt Found:**
- Title: "Majestic Fantasy Dragon"
- Tags: `fantasy`, `dragon`, `creature`
- **Shared Tags: 2** ✅ Good match

---

### Example 3: Okay Match (1 Tag)

**Deleted Prompt:**
- Title: "Minimalist Logo Design"
- Tags: `minimalist`, `logo`, `design`

**Similar Prompt Found:**
- Title: "Modern Minimalist Poster"
- Tags: `minimalist`, `poster`, `modern`
- **Shared Tags: 1** ⚠️ Okay match

---

### Example 4: Fallback (Same AI Generator)

**Deleted Prompt:**
- Title: "Abstract Pattern"
- Tags: `abstract`, `pattern`
- AI Generator: Midjourney

**No tag matches found, so fallback to:**
- Title: "Geometric Shapes"
- Tags: `geometric`, `shapes`
- AI Generator: Midjourney ✅ Same generator

---

### Example 5: Last Resort (Any Popular Prompt)

**Deleted Prompt:**
- Title: "Unique One-Off Design"
- Tags: `custom`, `unique`
- AI Generator: Unknown

**No matches at all, so fallback to:**
- Most liked prompt on the platform
- Better than 404 ✅

---

## SEO Benefits

### For Soft Deleted (302 Redirect)

**Before (404):**
- Day 1: Google crawls, sees 404
- Day 3: URL removed from index
- Day 5: User restores prompt
- **Result:** SEO value LOST, must rebuild

**After (302 Redirect):**
- Day 1: Google crawls, sees 302 to similar prompt
- Day 3: Original URL stays in index
- Day 5: User restores prompt
- **Result:** SEO value PRESERVED ✅

---

### For Hard Deleted (301 Redirect)

**Before (404):**
- Prompt deleted forever
- 100 backlinks point to URL
- **Result:** All link value LOST

**After (301 Redirect):**
- Prompt deleted forever
- 100 backlinks point to URL
- 301 redirects to similar prompt
- **Result:** 90-95% of link value transferred to similar prompt ✅

---

## Implementation Checklist

### Phase 1: Basic Redirect (15 minutes)
- [ ] Add `find_similar_prompt()` function
- [ ] Update `prompt_detail` view (non-owner case)
- [ ] Use 302 for soft deletes
- [ ] Test with real deleted prompt

### Phase 2: Permanent Redirect (45 minutes)
- [ ] Create `DeletedPromptRedirect` model
- [ ] Run migration
- [ ] Update `cleanup_deleted_prompts` command
- [ ] Update `prompt_detail` view (check redirect table)
- [ ] Use 301 for permanent deletes

### Phase 3: Optimization (Future)
- [ ] Cache similar prompt results
- [ ] Add same-author preference
- [ ] Track redirect success rate
- [ ] A/B test redirect vs custom page

---

## Testing

### Test 1: Soft Delete Redirect
1. Create prompt with tags: `portrait`, `woman`, `fantasy`
2. Delete prompt (moves to trash)
3. Access prompt URL as non-owner
4. **Expected:** 302 redirect to prompt with matching tags

### Test 2: Permanent Delete Redirect
1. Wait for prompt to be permanently deleted
2. Access prompt URL
3. **Expected:** 301 redirect to similar prompt (via redirect table)

### Test 3: No Similar Prompt
1. Create prompt with very unique tags
2. Delete it
3. Access URL
4. **Expected:** Fallback redirect to same AI generator or popular prompt

---

## Monitoring

**Track these metrics:**
- Redirect success rate (% with similar prompt found)
- Average shared tags (quality of match)
- User bounce rate after redirect
- SEO recovery rate (restored prompts keeping rankings)

**Google Search Console:**
- Monitor crawl errors (should decrease)
- Check 301/302 status codes
- Verify SEO value transfer

---

## Cost Analysis

**Phase 1 (Tag Matching):**
- Development: 15 minutes
- Database queries: +1 query per deleted prompt access
- Cost: ~$0/month

**Phase 2 (Permanent Redirects):**
- Development: 45 minutes
- Database: +1 table, minimal storage
- Cost: ~$0/month

**SEO Value Preserved:**
- Average prompt: 3 months to rank
- Ranking loss value: ~$50-500 in traffic
- **ROI:** 1 hour of work saves $50-500 per restored prompt

---

## Conclusion

**Recommended Approach:**

1. **Soft Deleted:** 302 redirect to similar prompt (tag matching)
2. **Hard Deleted:** 301 redirect to similar prompt (via redirect table)

**Benefits:**
- ✅ Preserves SEO value (months of work)
- ✅ Better user experience (helpful, not 404)
- ✅ Google-approved HTTP semantics
- ✅ Simple implementation (1 hour total)

**Next Step:** Implement Phase 1 (302 for soft deletes) immediately.

---

**END OF IMPLEMENTATION GUIDE**
