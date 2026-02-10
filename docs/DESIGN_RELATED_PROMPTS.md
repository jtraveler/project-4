# Related Prompts Feature — Design Document

**Date:** February 7, 2026
**Feature:** "You Might Also Like" section on prompt detail pages
**Status:** Phase 1 complete, Phase 2 complete, Phase 2B complete (taxonomy revamp)
**Last Updated:** February 10, 2026 (Phase 2B-9b — IDF-weighted tag/category similarity; rare tags worth ~5x more than common ones)

---

## Architecture Overview

### Phase 1 (Implement Now)
Score related prompts using 4 factors from existing data:
- Tag overlap (60%)
- Same AI generator (15%)
- Similar engagement (15%)
- Recency (10%)

Reuse existing `_prompt_card.html` partial + masonry grid + Load More pattern from homepage.

### Phase 2 (Future)
Add subject categories (ManyToMany) to the Prompt model:
- AI assigns 1-3 categories during upload from predefined taxonomy
- Backfill existing prompts via management command
- Update scoring formula to include category overlap (25%)
- Categories become reusable for browse pages, SEO landing pages, filtering

---

## Phase 1 — Detailed Design

### Scoring Algorithm

```python
def get_related_prompts(prompt, limit=60):
    """
    Score and rank related prompts for a given prompt.
    
    Strategy: Pre-filter candidates, then score.
    - Step 1: Get prompts sharing at least 1 tag OR same AI generator (cheap DB query)
    - Step 2: Score each candidate in Python
    - Step 3: Sort by score descending, return top N
    """
    
    # Pre-filter: only score prompts that have SOME relationship
    prompt_tags = set(prompt.tags.values_list('id', flat=True))
    
    candidates = Prompt.objects.filter(
        status=1  # Published only
    ).exclude(
        id=prompt.id
    ).exclude(
        deleted_at__isnull=False  # Exclude soft-deleted
    ).filter(
        Q(tags__in=prompt_tags) | Q(ai_generator=prompt.ai_generator)
    ).distinct().select_related('author').prefetch_related('tags')
    
    # Score each candidate
    scored = []
    for candidate in candidates:
        candidate_tags = set(candidate.tags.values_list('id', flat=True))
        
        # Tag overlap: 60% weight
        # Jaccard similarity (intersection / union)
        if prompt_tags and candidate_tags:
            tag_score = len(prompt_tags & candidate_tags) / len(prompt_tags | candidate_tags)
        else:
            tag_score = 0
        
        # Same AI generator: 15% weight
        generator_score = 1.0 if candidate.ai_generator == prompt.ai_generator else 0.0
        
        # Similar engagement: 15% weight
        # Inverse of normalized difference in like counts
        prompt_likes = prompt.number_of_likes or 0
        candidate_likes = candidate.number_of_likes or 0
        max_likes = max(prompt_likes, candidate_likes, 1)  # avoid div by zero
        engagement_score = 1.0 - (abs(prompt_likes - candidate_likes) / max_likes)
        
        # Recency: 10% weight
        # Newer = higher score, decay over 90 days
        days_old = (timezone.now() - candidate.created_on).days
        recency_score = max(0, 1.0 - (days_old / 90))
        
        total = (
            tag_score * 0.60 +
            generator_score * 0.15 +
            engagement_score * 0.15 +
            recency_score * 0.10
        )
        
        scored.append((candidate, total))
    
    # Sort by score descending, then by created_on descending (tiebreaker)
    scored.sort(key=lambda x: (-x[1], -x[0].created_on.timestamp()))
    
    return [item[0] for item in scored[:limit]]
```

### Performance Considerations

- **Pre-filter** prevents scoring the entire database — only prompts sharing tags or AI generator are scored
- **prefetch_related('tags')** avoids N+1 queries during scoring
- **Candidate cap:** If pre-filter returns >500 candidates, limit to 500 most recent before scoring
- **Future optimization:** Cache related prompts per prompt (invalidate on new upload or tag change)
- **Index:** Existing composite indexes on (status, created_on) support the pre-filter query

### Files to Modify/Create

| File | Change | Purpose |
|------|--------|---------|
| `prompts/utils/related.py` | **NEW** | `get_related_prompts()` scoring function |
| `prompts/views/detail_views.py` | Modify | Add related prompts to `prompt_detail` context |
| `prompts/views/detail_views.py` | Modify | Add AJAX endpoint for Load More |
| `prompts/urls.py` | Modify | Add URL for Load More AJAX |
| `prompts/templates/prompts/prompt_detail.html` | Modify | Add related prompts section at bottom |
| `prompts/templates/prompts/partials/_prompt_card_list.html` | **NEW** | Partial for AJAX card list rendering (reuses `_prompt_card.html`) |

### View Changes

**prompt_detail view** — Add to context:
```python
# In prompt_detail view, after existing context
related_prompts = get_related_prompts(prompt, limit=60)
# Paginate: show first page (matches homepage count)
related_page_size = 18  # matches homepage page size
context['related_prompts'] = related_prompts[:related_page_size]
context['has_more_related'] = len(related_prompts) > related_page_size
context['related_prompt_slug'] = prompt.slug
```

**New AJAX endpoint** — Load More:
```python
# URL: /prompt/<slug>/related/?page=2
def related_prompts_ajax(request, slug):
    prompt = get_object_or_404(Prompt, slug=slug, status=1)
    page = int(request.GET.get('page', 1))
    page_size = 18
    
    related = get_related_prompts(prompt, limit=60)
    start = (page - 1) * page_size
    end = start + page_size
    page_prompts = related[start:end]
    has_more = end < len(related)
    
    # Return rendered HTML partial (same pattern as homepage)
    html = render_to_string('prompts/partials/_prompt_card_list.html', {
        'prompts': page_prompts,
        'request': request,
    })
    return JsonResponse({'html': html, 'has_more': has_more})
```

### Template Structure

**In `prompt_detail.html` — after comments section:**
```html
{% if related_prompts %}
<section class="related-prompts-section">
    <div class="container">
        <h2 class="related-prompts-title">You Might Also Like</h2>
        <div class="masonry-container">
            <div class="masonry-grid" id="related-prompts-grid">
                {% for prompt in related_prompts %}
                    {% include '_prompt_card.html' with prompt=prompt %}
                {% endfor %}
            </div>
        </div>
        {% if has_more_related %}
        <div class="load-more-container text-center mt-4">
            <button id="load-more-related"
                    class="btn btn-primary btn-lg"
                    data-slug="{{ related_prompt_slug }}"
                    data-next-page="2">
                Load More
            </button>
            <div id="related-loading-spinner" class="mt-3" style="display: none;">
                <i class="fas fa-spinner fa-spin"></i> Loading...
            </div>
        </div>
        {% endif %}
    </div>
</section>
{% endif %}
```

**Load More JS** (reuse homepage pattern):
```javascript
document.getElementById('load-more-related')?.addEventListener('click', function() {
    const btn = this;
    const slug = btn.dataset.slug;
    const page = btn.dataset.nextPage;
    const spinner = document.getElementById('related-loading-spinner');
    
    btn.style.display = 'none';
    spinner.style.display = 'block';
    
    fetch(`/prompt/${slug}/related/?page=${page}`, {
        headers: {'X-Requested-With': 'XMLHttpRequest'}
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('related-prompts-grid').insertAdjacentHTML('beforeend', data.html);
        spinner.style.display = 'none';
        if (data.has_more) {
            btn.dataset.nextPage = parseInt(page) + 1;
            btn.style.display = 'inline-block';
        }
        // Re-init masonry if needed
    });
});
```

### CSS

Minimal additions — reuse existing `.masonry-container`, `.masonry-grid`, and `.prompt-card` styles. Only new CSS:

```css
.related-prompts-section {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--gray-200);
}

.related-prompts-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
}
```

---

## Phase 2 — Subject Categories (Future Design)

### Category Model

```python
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Optional icon class
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

# On Prompt model:
class Prompt(models.Model):
    # ... existing fields ...
    categories = models.ManyToManyField(
        'Category',
        blank=True,
        related_name='prompts'
    )
```

### Predefined Taxonomy (~25 categories)

| Category | Slug | Covers |
|----------|------|--------|
| Portrait | portrait | People, faces, headshots, character art |
| Fashion & Style | fashion-style | Clothing, shoes, accessories, runway |
| Landscape & Nature | landscape-nature | Mountains, forests, oceans, weather |
| Urban & City | urban-city | Streets, skylines, architecture, night city |
| Sci-Fi & Futuristic | sci-fi-futuristic | Space, cyberpunk, tech, robots |
| Fantasy & Mythical | fantasy-mythical | Magic, dragons, medieval, enchanted |
| Animals & Wildlife | animals-wildlife | Pets, wild animals, birds, underwater |
| Interior & Architecture | interior-architecture | Rooms, buildings, structures |
| Abstract & Artistic | abstract-artistic | Patterns, shapes, surreal, textures |
| Food & Drink | food-drink | Cuisine, beverages, cooking |
| Vehicles & Transport | vehicles-transport | Cars, planes, motorcycles, ships |
| Horror & Dark | horror-dark | Creepy, gothic, dark themes |
| Anime & Manga | anime-manga | Japanese animation style |
| Photorealistic | photorealistic | Hyper-real, photography style |
| Digital Art | digital-art | 3D renders, CGI, digital painting |
| Illustration | illustration | Hand-drawn style, sketches, cartoons |
| Product & Commercial | product-commercial | Product shots, advertising |
| Sports & Action | sports-action | Athletics, movement, competition |
| Music & Entertainment | music-entertainment | Instruments, concerts, performers |
| Retro & Vintage | retro-vintage | Old-school, nostalgic, film grain |
| Minimalist | minimalist | Clean, simple, whitespace |
| Macro & Close-up | macro-closeup | Detailed close shots |
| Seasonal & Holiday | seasonal-holiday | Christmas, Halloween, seasonal |
| Text & Typography | text-typography | Lettering, logos, word art |
| Meme & Humor | meme-humor | Funny, comedic, meme-style |

### Upload Flow Integration

Add to the existing OpenAI Vision API prompt:

```
Additionally, classify this image into 1-3 subject categories from this exact list:
[Portrait, Fashion & Style, Landscape & Nature, Urban & City, ...]

Return as: "categories": ["Portrait", "Fashion & Style"]
```

### Backfill Strategy

Management command:
```bash
python manage.py backfill_categories --batch-size=50 --delay=2
```
- Re-analyzes existing prompt images via OpenAI API
- Processes in batches to respect rate limits
- Logs progress and failures
- Can be resumed (skips prompts that already have categories)

### Updated Scoring Formula (Phase 2 → Phase 2B → Phase 2B-9 → Phase 2B-9c)

| Factor | Phase 1 | Phase 2 | Phase 2B | Phase 2B-9 | Phase 2B-9c |
|--------|---------|---------|----------|------------|-------------|
| Tag overlap | 60% | 35% | 20% | 35% | **30%** |
| Subject categories | — | 35% | 25% | 30% | **25%** |
| Subject descriptors | — | — | 25% | 25% | **35%** |
| Same AI generator | 15% | 10% | 10% | 5% | **5%** |
| Similar engagement | 15% | 10% | 10% | 3% | **3%** |
| Recency | 10% | 10% | 10% | 2% | **2%** |

Phase 2B-9 rationale: Content similarity (tags + categories + descriptors) = 90% of score. Non-relevance factors (generator + engagement + recency) = 10% tiebreakers only. Generator also removed from pre-filter to avoid pulling in irrelevant candidates that only match on platform.

Phase 2B-9b: Tag and category scoring now use IDF-weighted similarity (`1 / log(count + 1)`) — rare items worth more.

Phase 2B-9c: Extended IDF weighting to descriptors. Rebalanced weights to prioritize descriptors (35%) over tags (30%) and categories (25%) because key content signals (ethnicity, mood, setting) live in descriptors. All three content factors now use IDF-weighted similarity.

### Additional Phase 2 Benefits

- **Browse by category pages:** `/categories/`, `/categories/portrait/`
- **Homepage category filters:** Quick filter chips above the grid
- **SEO landing pages:** Category pages with meta descriptions
- **Admin dashboard:** Content distribution by category
- **Upload UX:** User can see/edit AI-assigned categories before publishing

---

## Implementation Plan

### Phase 1 (IMPLEMENTED — Session 74)
1. ✅ Created `prompts/utils/related.py` with scoring function
2. ✅ Added related prompts context to `prompt_detail` view
3. ✅ Added AJAX endpoint + URL for Load More
4. ✅ Added template section to `prompt_detail.html`
5. ✅ Created `partials/_prompt_card_list.html` partial
6. ✅ Minimal CSS additions in `prompt-detail.css`
7. ✅ Reuses `_prompt_card.html` and masonry grid patterns
8. ⚠️ **Known bug:** Grid layout not distributing cards evenly (JS column approach needs replacing with CSS column-count — planned Session 75)

### Phase 2 Spec (future session)
1. Create Category model + migration
2. Seed categories via data migration
3. Update upload OpenAI prompt
4. Create backfill management command
5. Update scoring function
6. Admin interface for categories
7. (Optional) Browse-by-category pages

---

**END OF DESIGN DOCUMENT**
