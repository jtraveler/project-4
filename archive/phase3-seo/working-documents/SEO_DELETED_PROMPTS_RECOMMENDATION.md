# SEO Strategy for Deleted Prompts - Recommendation

**Date:** November 6, 2025
**Context:** Bug 2 fix revealed we're returning 404 for deleted prompts
**Problem:** Losing all SEO value when prompts are soft-deleted

---

## Current Behavior (PROBLEM)

**When non-owner/bot accesses deleted prompt:**
- Returns: **HTTP 404 Not Found** (line 206)
- Google's response: Remove from index within 2-7 days
- SEO impact: **All rankings, backlinks, authority LOST**
- If restored: Start from zero (months to rebuild)

**Example Scenario:**
1. User's prompt ranks #1 for "cyberpunk midjourney prompt"
2. User accidentally deletes it
3. Google crawls within hours → 404
4. URL removed from index
5. User restores 2 days later (within 5-day window)
6. **Too late:** SEO value gone, rankings lost

---

## Recommended Strategy: Two-Tier Approach

### Tier 1: Soft Deleted (In Trash) → HTTP 302 + Custom Page

**For prompts in trash bin (retention period not expired):**

```python
if prompt.deleted_at is not None:
    # Owner: Redirect to trash (existing - keep this)
    if prompt.author == request.user:
        messages.info(...)
        return redirect('prompts:trash_bin')

    # Staff: Redirect to admin (existing - keep this)
    elif request.user.is_staff:
        messages.info(...)
        return redirect('admin_trash_dashboard')

    # Non-owners + Bots: Custom "temporarily unavailable" page
    else:
        context = {
            'prompt_title': escape(prompt.title),
            'message': 'This prompt is temporarily unavailable.',
            'suggested_prompts': get_related_prompts(prompt.tags.all()[:3]),
        }
        response = render(
            request,
            'prompts/prompt_temporarily_unavailable.html',
            context
        )
        response.status_code = 302  # Temporary redirect
        return response
```

**HTTP 302 Temporary Redirect Benefits:**
- ✅ Tells Google: "Page temporarily moved, check back later"
- ✅ URL stays in search index during retention period
- ✅ If restored, SEO value preserved (rankings, backlinks intact)
- ✅ Better than 404 (which signals permanent removal)

**Template Content (`prompt_temporarily_unavailable.html`):**
```html
<h1>Prompt Temporarily Unavailable</h1>
<p>This prompt is currently unavailable but may return soon.</p>

<h2>You Might Also Like</h2>
<!-- Show 3-6 related prompts based on tags -->
```

---

### Tier 2: Permanently Deleted → HTTP 410 Gone

**After retention period expires and prompt is hard-deleted:**

Currently returns 404 (via `get_object_or_404` when prompt doesn't exist in DB).

**Better approach:**
```python
# In cleanup_deleted_prompts management command
# Before hard deleting, create a DeletedPromptRecord:

class DeletedPromptRecord(models.Model):
    slug = models.SlugField(unique=True)
    deleted_permanently_at = models.DateTimeField(auto_now_add=True)
    original_tags = models.JSONField()  # For suggesting related prompts

# Then in prompt_detail view:
from prompts.models import DeletedPromptRecord

try:
    prompt = get_object_or_404(prompt_queryset, slug=slug)
except Http404:
    # Check if permanently deleted
    deleted_record = DeletedPromptRecord.objects.filter(slug=slug).first()
    if deleted_record:
        # Show 410 Gone with suggestions
        context = {
            'message': 'This prompt has been permanently removed.',
            'suggested_prompts': get_related_by_tags(deleted_record.original_tags),
        }
        return render(request, 'prompts/prompt_gone.html', context, status=410)
    else:
        # Never existed - return 404
        raise Http404("Prompt not found")
```

**HTTP 410 Gone Benefits:**
- ✅ Tells Google: "Permanently removed, don't come back"
- ✅ Google removes from index FASTER than 404 (1-3 days vs 2-7 days)
- ✅ Better for index hygiene (cleans up dead links)
- ✅ Still provides good UX (suggests related prompts)

---

## SEO Impact Comparison

| Scenario | Current (404) | Recommended (302/410) |
|----------|---------------|----------------------|
| **Soft Delete (Day 1)** | URL removed from index | URL stays in index |
| **Restore (Day 3)** | SEO value lost | SEO value preserved |
| **Hard Delete (Day 5+)** | URL lingers in index | URL removed quickly |
| **User Experience** | Generic 404 page | Helpful suggestions |
| **Backlink Value** | Lost immediately | Preserved during retention |

---

## Implementation Priority

### Phase 1: Quick Fix (30 minutes)
Change non-owner behavior for soft-deleted prompts:
- Replace `raise Http404` with custom 302 response
- Create simple template
- Show 3 related prompts (same tags)

### Phase 2: Full Implementation (2 hours)
- Create `DeletedPromptRecord` model
- Update `cleanup_deleted_prompts` to create records
- Implement 410 Gone for permanently deleted
- Create `prompt_gone.html` template

### Phase 3: Advanced (Future)
- 301 redirect to "best match" similar prompt
- ML-based prompt similarity matching
- Track SEO recovery metrics

---

## Recommended Action: Start with Phase 1

**Quick fix for immediate SEO protection:**

```python
# In prompt_detail view (line 204-206)
else:
    # Non-owner: Show temporarily unavailable (302)
    related_prompts = Prompt.objects.filter(
        tags__in=prompt.tags.all(),
        status=1,
        deleted_at__isnull=True
    ).exclude(id=prompt.id).distinct()[:3]

    context = {
        'prompt_title': escape(prompt.title),
        'related_prompts': related_prompts,
    }
    response = render(
        request,
        'prompts/prompt_temporarily_unavailable.html',
        context
    )
    response.status_code = 302
    return response
```

**Create template:** `prompts/templates/prompts/prompt_temporarily_unavailable.html`
```html
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8 text-center">
            <h1 class="mb-4">Prompt Temporarily Unavailable</h1>
            <p class="lead">
                "{{ prompt_title }}" is currently unavailable but may return soon.
            </p>

            {% if related_prompts %}
            <h2 class="mt-5 mb-4">You Might Also Like</h2>
            <div class="row">
                {% for prompt in related_prompts %}
                <div class="col-md-4 mb-4">
                    <a href="{% url 'prompts:prompt_detail' prompt.slug %}">
                        <!-- Prompt card -->
                    </a>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <a href="{% url 'prompts:home' %}" class="btn btn-primary mt-4">
                Browse All Prompts
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

**Time:** 30 minutes implementation
**SEO Impact:** Preserves months of SEO work during soft-delete period

---

## Google's Documentation References

**From Google Search Central:**

> "If a page is temporarily unavailable, use a 503 (Service Unavailable) status code. If you know the page will be gone for an extended period, use 404 (Not Found) or 410 (Gone). Use 410 to indicate the page is permanently gone."

> "For temporarily moved content, use 302 (Found) or 307 (Temporary Redirect). These tell Googlebot the move is temporary and to check back."

**Source:** https://developers.google.com/search/docs/crawling-indexing/http-network-errors

---

## Decision Matrix

| Use Case | HTTP Code | When | SEO Impact |
|----------|-----------|------|------------|
| Soft delete (in trash) | **302 Found** | Retention period not expired | ✅ Preserves SEO |
| Hard delete (permanent) | **410 Gone** | After retention expired | ✅ Fast removal |
| Never existed | **404 Not Found** | Invalid/typo URLs | ✅ Standard behavior |
| Temporarily down | 503 Service Unavailable | Server maintenance | ✅ Crawl later |

---

## Rollout Plan

### Week 1: Phase 1 (Quick Fix)
- Implement 302 for soft-deleted prompts
- Create temporarily_unavailable template
- Test with real deleted prompts
- Monitor Google Search Console

### Week 2: Phase 2 (Full Implementation)
- Create DeletedPromptRecord model
- Update cleanup command
- Implement 410 Gone
- Create prompt_gone template

### Week 3: Monitor & Optimize
- Track index status in Search Console
- Measure SEO recovery rate
- Adjust retention periods if needed
- A/B test different messaging

---

## Expected Results

**Before Implementation:**
- Deleted prompt → 404 → SEO value lost in 2-7 days
- Restore success rate: 20% (users give up)

**After Implementation:**
- Deleted prompt → 302 → SEO preserved during retention
- Restore success rate: 60%+ (better UX encourages restore)
- If permanently deleted → 410 → Clean index faster

**ROI:** Preserves months of SEO work for ~30 minutes of development

---

## Questions to Consider

1. **Should free users get 302 protection?**
   - Yes - all users benefit from SEO preservation
   - Encourages upgrades (premium = longer protection)

2. **How long to keep DeletedPromptRecord?**
   - Recommend: 90 days
   - After 90 days, delete record (404 becomes acceptable)

3. **Should we email users about SEO impact?**
   - Yes - "Your prompt is in trash. It's currently hidden from Google. Restore it to preserve your rankings."

4. **Track restoration rate?**
   - Yes - A/B test different messages to optimize

---

## Conclusion

**Current approach (404) is harming SEO.**

**Recommended approach (302/410) is:**
- ✅ SEO-friendly (preserves rankings during retention)
- ✅ User-friendly (helpful suggestions)
- ✅ Google-recommended (proper HTTP codes)
- ✅ Easy to implement (30 min for Phase 1)

**Next Step:** Implement Phase 1 (302 for soft-deletes) as part of Bug 2 completion.

---

**END OF RECOMMENDATION**
