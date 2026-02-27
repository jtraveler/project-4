# BULK AI IMAGE GENERATOR — Implementation Blueprint

**Document Purpose:** Handoff document for next Claude session to hit the ground running
**Source Discussion:** Session 69 — https://claude.ai/chat/b3124a3f-ebc6-449d-b310-c2b1541c1406
**Full Spec Reference:** `docs/BULK_IMAGE_GENERATOR_PLAN.md` (in project files)
**Date:** February 27, 2026
**Status:** Ready for implementation (pending OpenAI verification)

---

## BLOCKER: OpenAI Organization Verification

**Status: NOT YET COMPLETED**

Before any implementation begins, Mateo must complete OpenAI's identity verification:

1. Go to: https://platform.openai.com/settings/organization/general
2. Click "Verification" section → "Start ID Check"
3. Complete Persona identity verification (upload government ID + selfie)
4. Wait for approval (usually instant to 24 hours)
5. After approval, test in OpenAI Playground → Image mode → model `gpt-image-1`
6. Check API tier at: https://platform.openai.com/settings/organization/limits

**Why this is required:** OpenAI restricts GPT Image model API access to verified organizations to prevent abuse. Without verification, image generation API calls will be rejected.

**After verification, record:**
- Your API tier (1-5) — determines images per minute
- Your Images Per Minute (IPM) limit
- Confirm `OPENAI_API_KEY` env var is set (same key used for NSFW moderation)

---

## WHAT WE'RE BUILDING

An admin-only bulk content generation tool that lets Mateo rapidly populate PromptFinder with original AI-generated content. Instead of manually uploading one prompt at a time (2-3 min each), this tool processes 20-50 prompts in ~10 minutes.

### The Problem

- Mateo has thousands of saved text prompts
- Manual upload is painfully slow (one at a time)
- Can't use reference images from the internet (copyright)
- Need to build out categories fast to compete with PromptHero
- Current process: ~5 hours for 100 prompts

### The Solution

1. Paste 20-50 text prompts into a form
2. Select AI model, quality, size settings
3. Click "Generate" — images created in background via Django-Q worker
4. Review gallery of generated images as they appear
5. Select which ones to keep
6. Click "Create Pages" — runs through existing pipeline (NSFW check, AI titles/descriptions/tags, SEO filenames, B2 upload)
7. Pages created in draft mode for final review

---

## ARCHITECTURE OVERVIEW

### What Already Exists (Reuse from Phase N4)

| Component | Location | Status |
|-----------|----------|--------|
| Django-Q2 task queue | settings.py | ✅ Running |
| Worker dyno | Heroku | ✅ Running |
| B2 upload service | services/b2_upload.py | ✅ Ready |
| NSFW moderation | services/nsfw_moderation.py | ✅ Ready |
| AI content generation (titles, descriptions, tags) | services/ai_content.py | ✅ Ready |
| SEO filename generation | utils/seo.py | ✅ Ready |
| OpenAI API key | settings.py (OPENAI_API_KEY) | ✅ Configured |

### What's New to Build

| Component | Description |
|-----------|-------------|
| Image generation service | OpenAI GPT-Image-1 API integration |
| Provider abstraction layer | Pluggable interface for swapping AI generators |
| Bulk generator admin page | Form, progress view, gallery, page creation |
| Django-Q tasks | Rate-limited image generation tasks |
| Database models | BulkGenerationJob, GeneratedImage |
| JavaScript | Progress polling, gallery selection, AJAX submission |

### System Flow

```
Browser (Admin)                    Server                         External
┌──────────────┐    POST      ┌─────────────────┐           ┌──────────┐
│ Input Form   │───────────→  │ View: start job │           │ OpenAI   │
│ 50 prompts   │              │ Queue 50 tasks  │           │ API      │
└──────────────┘              └────────┬────────┘           └──────────┘
                                       │                         ↑
                                       ↓                         │
┌──────────────┐              ┌─────────────────┐               │
│ Progress UI  │←── poll ──── │ Django-Q Worker  │──── API ─────┘
│ (2-3 sec)    │              │ Rate limited     │
└──────────────┘              │ 5-250 img/min    │
       │                      └────────┬────────┘
       ↓                               │
┌──────────────┐              ┌─────────────────┐
│ Gallery View │              │ B2 Storage      │
│ Select imgs  │              │ (via Cloudflare)│
└──────┬───────┘              └─────────────────┘
       │
       ↓ POST (selected images)
┌──────────────┐
│ Create Pages │ → NSFW check → AI titles → SEO filenames → Save as Draft
└──────────────┘
```

---

## AI PROVIDER STRATEGY

### Phase 1 (v1.0): OpenAI Only

- Use GPT-Image-1 (or GPT-Image-1.5 if available post-verification)
- Admin-only, uses platform's OpenAI API key
- Validates the workflow before adding complexity

### Phase 2 (v1.2): Provider Abstraction + Replicate

**Critical design decision:** Build a provider abstraction layer from day one so we can plug in additional generators later without rewriting the core.

```python
# services/image_providers/base.py
class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt, size, quality, n=1) -> list[GeneratedImage]:
        pass

    @abstractmethod
    def get_rate_limit(self) -> int:
        """Images per minute"""
        pass

# services/image_providers/openai_provider.py
class OpenAIImageProvider(ImageProvider):
    def generate(self, prompt, size, quality, n=1):
        # GPT-Image-1 API call
        ...

# services/image_providers/replicate_provider.py (future)
class ReplicateImageProvider(ImageProvider):
    def generate(self, prompt, size, quality, n=1):
        # Replicate API (Flux, SDXL, etc.)
        ...
```

**Why Replicate matters for later:**
- Hosts dozens of image models (Flux, SDXL, Stable Diffusion)
- Different aesthetic styles for different categories
- Some models are cheaper than OpenAI
- Users could pick which model best fits their prompt style
- BYOK model works with Replicate too (users bring their own Replicate key)

### Provider Selection UI (Future)

When we add Replicate, the admin form gets a model dropdown:

```
Model: [GPT-Image-1 ▼]
        ├── GPT-Image-1 (OpenAI) — Best quality, $0.03-0.13/img
        ├── Flux Pro (Replicate) — Fast, artistic, ~$0.05/img
        ├── SDXL (Replicate) — Good variety, ~$0.02/img
        └── Stable Diffusion 3 (Replicate) — Budget, ~$0.01/img
```

**For v1.0, we hardcode OpenAI but structure the code so swapping is trivial.**

---

## COST ANALYSIS

### OpenAI GPT-Image-1 Pricing (per image, square 1024×1024)

| Quality | Cost/Image | 20 Images | 50 Images | 100 Images |
|---------|-----------|-----------|-----------|------------|
| Low | $0.015 | $0.30 | $0.75 | $1.50 |
| Medium | $0.03 | $0.60 | $1.50 | $3.00 |
| High | $0.05 | $1.00 | $2.50 | $5.00 |

**Recommended default:** Medium quality — best cost/quality balance for bulk

### Monthly Projections (Admin Use)

| Usage | Images/Month | Cost/Month |
|-------|-------------|------------|
| Light | 200 | $6-10 |
| Medium | 500 | $15-25 |
| Heavy | 1,000 | $30-50 |

### Rate Limits by OpenAI Tier

| Tier | Unlock At | Images/Min |
|------|-----------|------------|
| Tier 1 | $5 spent | 5 |
| Tier 2 | $50 spent | 20 |
| Tier 3 | $100 spent | 50 |
| Tier 4 | $250 spent | 150 |
| Tier 5 | $500 spent | 250 |

---

## DATABASE MODELS (Planned)

```python
class BulkGenerationJob(models.Model):
    """Tracks a batch of image generation requests"""
    id = UUIDField(primary_key=True)
    created_by = ForeignKey(User)
    status = CharField(choices=['pending','processing','completed','failed'])
    provider = CharField(default='openai')  # Future: 'replicate', etc.
    model_name = CharField(default='gpt-image-1')
    quality = CharField(choices=['low','medium','high'])
    size = CharField(default='1024x1024')
    total_prompts = IntegerField()
    completed_count = IntegerField(default=0)
    failed_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)

class GeneratedImage(models.Model):
    """Individual generated image within a job"""
    job = ForeignKey(BulkGenerationJob)
    prompt_text = TextField()
    status = CharField(choices=['queued','generating','completed','failed'])
    image_url = URLField(blank=True)  # B2 URL after upload
    revised_prompt = TextField(blank=True)  # Model's interpretation
    selected = BooleanField(default=True)  # Admin selection
    prompt_page = ForeignKey(Prompt, null=True)  # Created page link
    error_message = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
```

---

## IMPLEMENTATION PHASES

### Phase 1: Core Infrastructure (3-4 days)
- Database models + migrations
- OpenAI image generation service (with provider abstraction)
- B2 upload integration for generated images
- Django-Q tasks with rate limiting
- Basic error handling + retry logic

### Phase 2: API Endpoints (2-3 days)
- Start generation view (POST)
- Status polling endpoint (GET, returns progress JSON)
- Create pages endpoint (POST, selected images → prompt pages)
- URL routing

### Phase 3: Frontend (3-4 days)
- Input form template (prompts textarea, settings dropdowns)
- Progress view with real-time updates
- Gallery view with image selection
- JavaScript for polling, selection, form handling
- CSS styling

### Phase 4: Integration & Testing (2-3 days)
- End-to-end testing
- Error handling edge cases
- Admin permissions
- Documentation

**Total estimate: 10-14 days**

---

## UX/UI APPROACH

**Important:** Mateo will provide UX/UI suggestions and mockup ideas for the bulk generator interface. These should be discussed with Claude for feedback before implementation. The UI needs to handle several distinct states:

1. **Input state** — Form with prompt textarea, settings, estimated cost display
2. **Generating state** — Progress bar, images appearing in real-time
3. **Gallery state** — Grid of generated images with selection checkboxes
4. **Creating state** — Progress of page creation pipeline
5. **Complete state** — Summary with links to created pages

**Design principles from Session 69:**
- Progressive disclosure — show complexity as needed
- Real-time feedback — images appear as they complete
- Non-blocking — user can select while generation continues
- Clear costs — show estimated cost before generation
- Recoverable — can cancel mid-generation
- Mobile responsive — 4 columns → 2 → 1

**UX/UI workflow for this feature:**
1. Mateo sketches/describes the UI concept
2. Claude reviews and provides feedback on UX patterns, accessibility, edge cases
3. Final design agreed upon
4. CC spec written with exact UI requirements
5. CC implements
6. Browser testing and iteration

---

## PREMIUM/MONETIZATION (Future — v1.1+)

### BYOK Model (Bring Your Own Key)

Platform-paid API doesn't scale because OpenAI rate limits are per API key, not per user. With 100 users sharing one key, queue times would be hours.

**Solution:** Premium users bring their own OpenAI (and later Replicate) API key.

| Tier | Price | Features | API Key |
|------|-------|----------|---------|
| Free | $0 | Browse, save prompts | N/A |
| Pro | $12-15/mo | Bulk generator, all features | BYOK required |

**Profit: ~$11.50-14.50/user/month** (PromptFinder provides infrastructure, user pays OpenAI directly)

---

## WHAT TO DO IN THE NEXT SESSION

### Before Starting (Mateo Action Items)
- [ ] Complete OpenAI Organization Verification
- [ ] Record API tier and rate limits
- [ ] Test image generation in OpenAI Playground

### Session Agenda
1. Confirm OpenAI verification complete
2. Review this blueprint for any updates
3. Mateo presents UX/UI ideas → discuss with Claude
4. Write Phase 1 CC spec (models, migrations, provider service, tasks)
5. CC implements Phase 1
6. Write Phase 2 CC spec (API endpoints)
7. Continue through phases

### Key Files to Reference
- `docs/BULK_IMAGE_GENERATOR_PLAN.md` — Full v1.4 specification (1300+ lines)
- `prompts/services/` — Existing services to reuse
- `prompts/tasks.py` — Django-Q task patterns
- `prompts_manager/settings.py` — Django-Q config, OpenAI key

---

## DEFERRED ITEMS (Noted for Future)

- **P2-B: Admin Log tab** — Login tracking, staff presence detection (on hold)
- **P2-C: Web Pulse tab** — Server errors, API health, security alerts (on hold)
- **Link click tracking** — Track clicks on embedded Quill links in system notifications (future feature in memory)

---

**END OF BLUEPRINT**
