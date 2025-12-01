# Phase G Investigation Report: Follow System & Homepage Filtering

**Date:** November 30, 2025
**Status:** Investigation Complete - Ready for Implementation
**Estimated Implementation Time:** 5-6 hours

---

## Executive Summary

This investigation confirms that **all infrastructure for Phase G homepage filters is already in place**. The Follow model, views, and URLs are fully implemented. The homepage view (PromptList) just needs minor modifications to add Trending/New/Following filter options.

**Key Finding:** No new models needed. Implementation is straightforward query modifications.

---

## 1. Follow Model Analysis

### Location
`prompts/models.py` - Line 1597

### Model Structure

```python
class Follow(models.Model):
    """
    Represents a follow relationship between two users.
    Follower follows Following.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',  # who this user follows
        help_text="The user who is following"
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower_set',  # who follows this user
        help_text="The user being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'prompts_follow'
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', '-created_at']),
            models.Index(fields=['following', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
```

### Related Names Explained

| Access Pattern | Returns | Use Case |
|---------------|---------|----------|
| `user.following_set.all()` | Follow objects where user is follower | Get all users this user follows |
| `user.follower_set.all()` | Follow objects where user is followed | Get all users following this user |

### Existing Helper Methods (UserProfile)

Located in `prompts/models.py` lines 1566-1580:

```python
@property
def follower_count(self):
    """Count of users following this user"""
    return self.user.follower_set.count()

@property
def following_count(self):
    """Count of users this user follows"""
    return self.user.following_set.count()
```

---

## 2. Homepage View Analysis

### Location
`prompts/views.py` - Line 168 (PromptList class)

### Current Implementation

```python
class PromptList(generic.ListView):
    template_name = "prompts/prompt_list.html"
    paginate_by = 18

    def get_queryset(self):
        queryset = Prompt.objects.select_related('author').prefetch_related(
            'tags', 'likes',
            Prefetch('comments', queryset=Comment.objects.filter(approved=True))
        ).filter(status=1, deleted_at__isnull=True).order_by('order', '-created_on')

        # Media filter (existing)
        media_filter = self.request.GET.get('media', 'all')
        if media_filter == 'photos':
            queryset = queryset.filter(featured_image__isnull=False)
        elif media_filter == 'videos':
            queryset = queryset.filter(featured_video__isnull=False)

        # Tag filter (existing)
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # Search filter (existing)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

        return queryset.distinct()
```

### Current Filter Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `media` | all, photos, videos | Filter by media type |
| `tag` | tag slug | Filter by specific tag |
| `search` | text | Search title/content |

### Missing Filter Parameters (To Implement)

| Parameter | Values | Description |
|-----------|--------|-------------|
| `sort` | new, trending, following | Sort/filter prompts |

---

## 3. Current Filter UI Analysis

### Location
`prompts/templates/prompts/prompt_list.html` - Lines 112-132

### Current Structure

```html
<div class="media-filter-container">
    <div class="media-filter-tabs" role="tablist">
        <a href="?media=all"
           class="media-tab {% if media_filter == 'all' %}active{% endif %}"
           role="tab">
            All
        </a>
        <a href="?media=photos"
           class="media-tab {% if media_filter == 'photos' %}active{% endif %}"
           role="tab">
            <i class="fas fa-image"></i> Photos
        </a>
        <a href="?media=videos"
           class="media-tab {% if media_filter == 'videos' %}active{% endif %}"
           role="tab">
            <i class="fas fa-video"></i> Videos
        </a>
    </div>
</div>
```

### Proposed New Structure

```html
<!-- Sort Filter (NEW) -->
<div class="sort-filter-container">
    <div class="sort-filter-tabs" role="tablist">
        <a href="?sort=new{% if media_filter != 'all' %}&media={{ media_filter }}{% endif %}"
           class="sort-tab {% if sort_by == 'new' %}active{% endif %}">
            <i class="fas fa-clock"></i> New
        </a>
        <a href="?sort=trending{% if media_filter != 'all' %}&media={{ media_filter }}{% endif %}"
           class="sort-tab {% if sort_by == 'trending' %}active{% endif %}">
            <i class="fas fa-fire"></i> Trending
        </a>
        {% if user.is_authenticated %}
        <a href="?sort=following{% if media_filter != 'all' %}&media={{ media_filter }}{% endif %}"
           class="sort-tab {% if sort_by == 'following' %}active{% endif %}">
            <i class="fas fa-user-friends"></i> Following
        </a>
        {% endif %}
    </div>
</div>

<!-- Media Filter (EXISTING - unchanged) -->
<div class="media-filter-container">
    <!-- ... existing code ... -->
</div>
```

---

## 4. Trending/Popular Logic Analysis

### Existing Implementation
`prompts/views.py` - Line 3378 (ai_generator_category view)

```python
if sort_by == 'popular':
    prompts = prompts.annotate(
        likes_count=models.Count('likes', distinct=True)
    ).order_by('-created_on', '-created_on')  # BUG: Should be '-likes_count'
elif sort_by == 'trending':
    week_ago = now - timedelta(days=7)
    prompts = prompts.filter(created_on__gte=week_ago).annotate(
        likes_count=models.Count('likes', distinct=True)
    ).order_by('-created_on', '-created_on')  # BUG: Should be '-likes_count'
```

### ⚠️ Bug Identified

**Issue:** Both popular and trending sorts use `order_by('-created_on', '-created_on')` instead of sorting by likes_count.

**Fix Required:**
```python
# Popular - all time, sorted by likes
.order_by('-likes_count', '-created_on')

# Trending - last 7 days, sorted by likes
.order_by('-likes_count', '-created_on')
```

### Likes Field Location
`prompts/models.py` - Line 645

```python
likes = models.ManyToManyField(
    User, related_name='prompt_likes', blank=True
)
```

---

## 5. Implementation Recommendations

### Query Modifications for PromptList

```python
def get_queryset(self):
    queryset = Prompt.objects.select_related('author').prefetch_related(
        'tags', 'likes',
        Prefetch('comments', queryset=Comment.objects.filter(approved=True))
    ).filter(status=1, deleted_at__isnull=True)

    # Sort filter (NEW)
    sort_by = self.request.GET.get('sort', 'new')

    if sort_by == 'following' and self.request.user.is_authenticated:
        # Get IDs of users the current user follows
        followed_users = self.request.user.following_set.values_list('following_id', flat=True)
        queryset = queryset.filter(author_id__in=followed_users)
        queryset = queryset.order_by('-created_on')

    elif sort_by == 'trending':
        # Last 7 days, sorted by likes
        week_ago = timezone.now() - timedelta(days=7)
        queryset = queryset.filter(created_on__gte=week_ago).annotate(
            likes_count=Count('likes', distinct=True)
        ).order_by('-likes_count', '-created_on')

    else:  # 'new' (default)
        queryset = queryset.order_by('order', '-created_on')

    # Existing media filter
    media_filter = self.request.GET.get('media', 'all')
    if media_filter == 'photos':
        queryset = queryset.filter(featured_image__isnull=False)
    elif media_filter == 'videos':
        queryset = queryset.filter(featured_video__isnull=False)

    # ... rest of existing filters ...

    return queryset.distinct()
```

### Context Data Addition

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context['sort_by'] = self.request.GET.get('sort', 'new')
    context['media_filter'] = self.request.GET.get('media', 'all')
    # ... existing context ...
    return context
```

---

## 6. Files to Modify

| File | Changes | Estimated Time |
|------|---------|----------------|
| `prompts/views.py` | Add sort parameter handling to PromptList.get_queryset() | 1 hour |
| `prompts/views.py` | Fix bug in ai_generator_category sorting | 15 minutes |
| `prompts/templates/prompts/prompt_list.html` | Add sort filter tabs UI | 1.5 hours |
| `static/css/style.css` | Style sort filter tabs (if needed) | 30 minutes |
| `prompts/views.py` | Add sort_by to context | 15 minutes |
| Testing & Polish | Manual testing, edge cases | 2 hours |

**Total Estimated Time:** 5-6 hours

---

## 7. Testing Checklist

### Sort Filter Tests
- [ ] "New" shows prompts ordered by creation date (newest first)
- [ ] "Trending" shows prompts from last 7 days ordered by likes
- [ ] "Following" only appears for authenticated users
- [ ] "Following" shows only prompts from followed users
- [ ] "Following" shows empty state when not following anyone
- [ ] Sort preserves media filter selection
- [ ] Sort preserves tag filter selection
- [ ] Sort preserves search query

### Edge Cases
- [ ] Anonymous user sees New/Trending but not Following
- [ ] User following 0 people sees appropriate message
- [ ] Trending with 0 prompts in last 7 days shows message
- [ ] URL parameters combine correctly (?sort=trending&media=photos)

### Performance
- [ ] Following query uses index (check EXPLAIN)
- [ ] Trending annotation doesn't cause N+1
- [ ] Page load time under 500ms

---

## 8. Dependencies & Prerequisites

### Already Complete ✅
- Follow model with indexes
- Follow/unfollow views and URLs
- UserProfile helper methods
- Likes ManyToManyField on Prompt
- Media filter UI pattern

### Not Required
- No new database migrations
- No new models
- No external dependencies

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance degradation on Following filter | Low | Medium | Index already exists on follower field |
| Trending shows stale content on low-traffic days | Medium | Low | Consider 30-day fallback if 7-day is empty |
| UI confusion with two filter rows | Low | Low | Clear visual hierarchy, familiar pattern |

---

## 10. Conclusion

Phase G homepage filtering is straightforward to implement:

1. **Infrastructure exists** - Follow model, likes field, and helper methods are complete
2. **Pattern exists** - ai_generator_category has sorting logic to adapt (with bug fix)
3. **UI pattern exists** - Media filter tabs provide template for sort tabs
4. **No database changes** - Just view and template modifications

**Recommendation:** Proceed with implementation. Start with the bug fix in ai_generator_category, then adapt the logic for PromptList.

---

## Appendix: Related URLs

| URL Pattern | View | Purpose |
|-------------|------|---------|
| `/` | PromptList | Homepage with filters |
| `/users/<username>/follow/` | follow_user | Follow a user |
| `/users/<username>/unfollow/` | unfollow_user | Unfollow a user |
| `/users/<username>/follow-status/` | get_follow_status | AJAX check if following |
| `/ai/<slug>/` | ai_generator_category | Has sorting logic to reuse |

---

*Report generated as part of Phase G investigation. See CLAUDE.md for full project context.*
