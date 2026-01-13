# CLAUDE.md - PromptFinder Project Documentation

**Last Updated:** January 9, 2026
**Project Status:** Pre-Launch Development - Phase L (Media Infrastructure) ~98% COMPLETE, Phase K ON HOLD (95%)

**Owner:** Mateo Johnson - Prompt Finder

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Stack](#technical-stack)
3. [Infrastructure & Costs](#infrastructure--costs)
4. [Development Phases](#development-phases)
5. [Known Issues & Technical Debt](#known-issues--technical-debt)
6. [Decisions Made](#decisions-made)
7. [Monetization Strategy](#monetization-strategy)
8. [Content Moderation](#content-moderation)
9. [Upload Flow Architecture](#upload-flow-architecture)
10. [SEO Strategy](#seo-strategy)
11. [User Management](#user-management)
12. [Feature Specifications](#feature-specifications)
13. [Trash Bin & Orphaned File Management](#phase-d5-trash-bin--orphaned-file-management-)
14. [Phase I: URL Migration](#phase-i-url-migration-to-prompts-complete)
15. [Phase J: Prompt Detail Page Redesign](#-phase-j-prompt-detail-page-redesign-complete) ✅
16. [Phase K: Collections Feature](#-phase-k-collections-feature) ⏸️ ON HOLD
17. [Phase L: Media Infrastructure Migration](#-phase-l-media-infrastructure-migration-current-priority) **← CURRENT**
18. [Future Features Roadmap](#-future-features-roadmap)
19. [Project Health Checkup Protocol](#-project-health-checkup-protocol)
20. [Known Technical Debt](#-known-technical-debt)
21. [Unanswered Questions](#unanswered-questions)

---

## 🎯 Project Overview

### What is PromptFinder?

**PromptFinder** is an AI prompt sharing and discovery platform where users can:
- Find high-quality AI prompts with preview images
- Share their successful prompt-image pairs
- Browse prompts by AI generator (Midjourney, DALL-E, Stable Diffusion, etc.)
- Engage with the community through likes, comments, and follows
- Organize and manage their prompt collections

**Target Audience:**
- AI artists and creators
- Content creators needing prompt inspiration
- Professionals building prompt libraries
- Hobbyists exploring AI image generation

**Current Status:**
- Phase 1: Infrastructure & Core Features (COMPLETE)
  - ✅ PostgreSQL migration complete
  - ✅ Content moderation system (OpenAI + Cloudinary)
  - ✅ Admin panel enhancements
  - ✅ Cloudinary asset cleanup
  - ✅ **Phase A:** Tag infrastructure (209 tags across 21 categories)
  - ✅ **Phase B:** AI content generation service (GPT-4o-mini)
  - ✅ **Phase C:** Pexels-style upload UI (Step 1 drag-and-drop)
  - ✅ **Phase D:** Two-step upload flow WITH AI generation + idle detection ⭐
  - ✅ **Phase D.5:** Trash Bin + Automated Cleanup ⭐ **COMPLETE** (October 12, 2025)
  - ✅ **Phase D.5 Part 2:** SEO Infrastructure (Phase 3) ⭐ **COMPLETE** (November 6-7, 2025)
    - ✅ 11 AI Generator Landing Pages
    - ✅ Comprehensive Deleted Prompt Strategy (3 phases)
    - ✅ Database Performance Indexes (15x improvement)
    - Agent Rating: 8.0/10 (django: 9.0, seo: 7.5, code: 7.5)
  - ✅ **Phase E:** User Profiles & Social Foundation ⭐ **100% COMPLETE** (Oct 25 - Nov 6, 2025)
    - ✅ Task 1: UserProfile Model & Admin (complete)
    - ✅ Task 2: Profile Edit Form & UX Enhancements (complete)
    - ✅ Task 3: Report Feature (complete)
    - ✅ Task 4: Email Preferences Dashboard (complete - Nov 6, 2025)
    - ✅ Task 5: Profile Header Refinements (complete)
    - ✅ Enhancement 1: ARIA Accessibility (complete)
    - ✅ Enhancement 2: Rate Limiting System (complete)
  - ✅ **Phase F:** Advanced Admin Tools & UI Refinements ⭐ **COMPLETE** (October 31, 2025)
  - 🔧 **UI Redesign Session:** Load More Fix & CSS Audit ⭐ **COMPLETE** (November 13, 2025)
    - ✅ Fixed critical Load More button JavaScript error
    - ✅ Refined layout for ultrawide displays (1600px max-width)
    - ✅ Comprehensive CSS audit (10 issues identified)
    - ✅ 3-phase roadmap created for CSS cleanup (4-7 days estimated)
  - 🚀 **Performance Optimization Session** ⭐ **COMPLETE** (November 17, 2025)
    - ✅ Event delegation pattern implemented (9.3/10 agent rating)
    - ✅ 51% performance improvement (125ms vs 255ms per session)
    - ✅ 97% memory reduction (1KB vs 15-30KB)
    - ✅ Zero security vulnerabilities found
    - ✅ Agent-validated: @code-reviewer (9/10), @performance-expert (9.5/10), @security (9.5/10)
  - ✅ **Draft Mode System** ⭐ **COMPLETE** (November 29, 2025)
    - ✅ Draft Mode Banner (yellow warning for draft/pending prompts)
    - ✅ Notification Color System (WCAG AA compliant flash messages)
    - ✅ User Draft Controls (Save as Draft toggle, Published/Draft toggle)
    - ✅ Admin bulk action (Mark selected prompts as drafts)
    - ✅ Security: Moderation enforced for drafts, publish checks moderation_status
    - ✅ Bug Fixed: Toggle locked after admin approval (Nov 30, 2025)
    - Agent Rating: 9.0/10 average
  - ✅ **CSS Cleanup Phase 1:** Component-based CSS architecture ⭐ **COMPLETE** (November 2025)
    - ✅ Extracted navbar styles to `static/css/navbar.css` (1,136 lines)
    - ✅ Removed `.masonry-container` duplication from templates
    - ✅ Created `static/css/components/masonry-grid.css` (255 lines)
    - ✅ Created `static/css/pages/prompt-list.css` (304 lines)
  - 📋 **CSS Cleanup Phase 2:** Extract remaining inline styles (17 templates) - FUTURE WORK
  - ✅ **Phase G:** Homepage Tabs, Sorting & Leaderboard ⭐ **COMPLETE** (December 5-7, 2025)
    - ✅ Part A: Homepage tabs (Home/All/Photos/Videos) + sorting (Trending/New/Following)
    - ✅ Part B: Views tracking with configurable trending algorithm
    - ✅ Part C: Community leaderboard with Most Viewed/Most Active rankings
    - Agent Rating: 8.7/10 average
  - ✅ **Phase I:** URL Migration to /prompts/ ⭐ **COMPLETE** (December 12, 2025)
    - ✅ Migrated /ai/ and /inspiration/ URLs to /prompts/ namespace
    - ✅ 301 permanent redirects for SEO preservation
    - ✅ All 70 tests passing
    - Agent Rating: @django-pro 9.0/10, @code-reviewer 8.5+/10
  - ✅ **Infrastructure Audit & CI/CD** ⭐ **COMPLETE** (December 13, 2025)
    - ✅ GitHub Actions CI/CD pipeline (3 parallel jobs)
    - ✅ views.py split into modular package (11 view modules)
    - ✅ Navbar JavaScript extracted to static/js/navbar.js
    - ✅ Sentry error monitoring (production only)
    - ✅ Test suite: 234 tests passing, 46% coverage
    - ✅ Security: Django 5.2.9, urllib3 2.6.0+, sentry-sdk 1.45.1+
    - Agent Rating: 9.17/10 average (@code-reviewer 8.5, @django-pro 9.5, @devops-troubleshooter 9.5)
  - ✅ **Phase J:** Prompt Detail Page Redesign ⭐ **100% COMPLETE** (December 2025)
    - ✅ Phase 0: Baseline Analysis Complete (`docs/PROMPT_DETAIL_ANALYSIS.md`)
    - ✅ Phase 0.5: Code Quality Improvements (avatar signals, simple_timesince refactor)
    - ✅ Phase J.1: Complete UI overhaul (9 rounds, 22 commits)
    - ✅ Phase J.2: SVG icon system for navigation (5 icons)
    - ✅ Phase J.3: Phase 2 icons (11 icons), video hover autoplay, like button redesign
    - ✅ Session 22-23: Security remediation, generator pages fix, SVG expansion
    - Agent Rating: 8.7/10 average (@ui-ux-designer 7.5-9.5, @frontend-developer 9.0)
    - Agent Rating (Session 22-23): @security-auditor 9.2/10, @django-pro 9.0/10
    - See: [Phase J: Prompt Detail Page Redesign](#-phase-j-prompt-detail-page-redesign-complete)
  - ⏸️ **Phase K:** Collections ("Saves") Feature ⭐ **ON HOLD** (95% Complete - Paused for Phase L)
    - ✅ Micro-Specs #1-14: Save buttons, modal, API, profile tab, bug fixes complete
    - ✅ Phase K.1: MVP Collections (95% Complete)
    - ❌ Phase K.2: Enhanced Features (download tracking, virtual collections)
    - ❌ Phase K.3: Premium Features (limits, upsells)
    - **Approach:** Micro-Spec methodology (adopted Session 24)
    - See: [Phase K: Collections Feature](#-phase-k-collections-feature)
  - 🔄 **Phase L:** Media Infrastructure Migration ⭐ **~98% COMPLETE** (December 2025 - January 2026)
    - Cloudinary → Backblaze B2 + Cloudflare migration
    - 11 sub-features for complete media stack overhaul
    - ~70% cost reduction at scale
    - ✅ L8 Quick Mode: CODE COMPLETE (95% faster processing: 2.4s → 0.12s)
    - ✅ L8-DIRECT: COMPLETE (Direct browser-to-B2 uploads via presigned URLs)
    - See: [Phase L: Media Infrastructure](#-phase-l-media-infrastructure-migration-current-priority)
- Transitioning from student project to mainstream monetization platform
- Building content library for public launch

## 📊 Phase D.5 Complete - October 12-13, 2025

**Trash Bin System + Orphaned File Management** ✅

**Day 1:** Soft delete system with trash bin UI (4-5 hours)
**Day 2:** Automated cleanup + orphan detection (4-5 hours)
**Day 3:** Missing image detection + documentation (2 hours)

**Key Achievements:**
- ✅ Soft delete with 5-30 day retention (free/premium)
- ✅ Automated daily cleanup via Heroku Scheduler
- ✅ Orphaned Cloudinary file detection (found 14 orphans, 8.5 MB)
- ✅ Missing image detection (prompts without valid Cloudinary files)
- ✅ Two-section reporting (orphaned files + missing images)
- ✅ ACTIVE vs DELETED prompt differentiation
- ✅ Email notifications to admins
- ✅ Comprehensive documentation (2,000+ lines)
- ✅ $0/month operational cost
- ✅ Critical UX fix (prevents broken images on homepage)

**Next Phase: Phase E - User Profiles & Social Foundation**
- Public user profile pages with stats
- Enhanced prompt detail page with report feature
- Email preferences dashboard
- Follow/unfollow foundation for Phase F

---

## 📊 Phase D.5 Part 2: SEO Infrastructure (Phase 3) - November 6-7, 2025

**SEO Strategy for AI Generator Category Pages + Deleted Prompts** ✅

**Implementation Date:** November 6-7, 2025 (2-day sprint)
**Status:** Production-Ready (Heroku migration pending)
**Agent Rating:** 8.0/10 consensus (django: 9.0, seo: 7.5, code: 7.5)

### What Was Built

**1. AI Generator Landing Pages (11 generators):**
- `/ai/midjourney/`, `/ai/dalle3/`, `/ai/dalle2/`, `/ai/stable-diffusion/`
- `/ai/leonardo-ai/`, `/ai/flux/`, `/ai/sora/`, `/ai/sora2/`
- `/ai/veo-3/`, `/ai/adobe-firefly/`, `/ai/bing-image-creator/`

**Features:**
- Filtering by type (image/video) and date (today/week/month/year)
- Sorting by recent/popular/trending
- Pagination (24 prompts per page)
- Schema.org CollectionPage structured data
- Responsive masonry grid layout
- Generator metadata with official links

**2. Comprehensive Deleted Prompt Strategy (3 Phases):**
- **Phase 1:** Display "This content has been removed" placeholder
- **Phase 2:** Hide deleted prompts from all public views (status=0)
- **Phase 3:** Implement 410 Gone HTTP status for deleted prompt URLs

**3. Database Performance Indexes:**
- Index 1: `(ai_generator, status, deleted_at)` for filtering queries
- Index 2: `(ai_generator, created_on)` for date sorting
- **Performance Impact:** 15x improvement (300-800ms → 10-50ms at 10K+ prompts)

### Files Created/Modified

**New Files (3):**
1. `prompts/constants.py` (241 lines) - Generator metadata and validation
2. `prompts/templates/prompts/ai_generator_category.html` (283 lines) - Landing page template
3. `prompts/migrations/0034_prompt_prompt_ai_gen_idx_and_more.py` (24 lines) - Database indexes

**Modified Files (2):**
1. `prompts/views.py` - Added `ai_generator_category()` view with validation
2. `prompts/urls.py` - Added `/ai/<slug:generator_slug>/` route

### Agent Ratings

**@django-expert: 9.0/10** (improved from 7.5 after indexes)
- ✅ Excellent query optimization
- ✅ Database indexes implemented
- ✅ Proper Http404 handling
- ✅ distinct=True for accurate counts

**@seo-authority-builder: 7.5/10**
- ✅ Clean URL structure
- ✅ Schema.org CollectionPage markup
- ❌ Missing canonical tags (critical)
- ❌ Missing BreadcrumbList schema
- ❌ Missing Open Graph/Twitter Cards
- ❌ Content depth needs expansion (200-300 words → 800-1200 words)

**@code-reviewer: 7.5/10 (Security: 6.5/10)**
- ✅ Input validation against whitelisted constants
- ✅ Query optimization (no N+1 issues)
- ⚠️ XSS vulnerability in AI_GENERATORS descriptions (HTML with |safe)
- ⚠️ View function complexity (83 lines, needs refactoring)
- ❌ No unit tests

**Consensus: 8.0/10** - Production-ready with known improvement areas

### Performance Metrics

**Query Performance (with indexes):**
- Filtering queries: 10-50ms (was 300-800ms)
- Date sorting: 10-50ms (was 200-500ms)
- Improvement: **15x faster** at scale

**SEO Completeness:**
- Current: 77% (core functionality complete)
- Week 1 improvements: 85% (canonical + OG tags, 1 hour)
- Month 1 polish: 95% (content expansion + tests, 29 hours)

### Production Deployment Status

**✅ Completed Locally:**
- Code implementation (100%)
- Database migration created (100%)
- Git commits pushed to origin/main (100%)

**✅ Deployed to Heroku:**
- Migration 0034 applied successfully (Heroku v409)
- Database indexes ACTIVE in production
- Verified with `showmigrations` command
- Query performance optimized (15x improvement active)

**📊 SEO Traffic Projections (12 months, after improvements):**
- Month 3: 2,000-4,000 sessions/month
- Month 6: 6,000-10,000 sessions/month
- Month 12: 12,000-20,000 sessions/month
- **Year 1 Total:** 60,000-100,000 organic sessions

### Implementation Commits

**Commit 1: Core Implementation (82b815c)**
```
feat(seo): Add AI generator category pages with filtering and sorting

Phase 3: AI Generator Category Pages
- Add 11 generator landing pages (/ai/midjourney/, /ai/dalle3/, etc.)
- Filter by type (image/video) and date (today/week/month/year)
- Sort by recent/popular/trending with distinct=True
- Pagination (24 prompts per page)
- Schema.org CollectionPage structured data
- Move AI_GENERATORS to constants.py
```

**Commit 2: Documentation (1c10571)**
```
docs(phase-3): Add comprehensive agent validation reports

Agent consensus rating: 7.5/10 across all reviewers
- Performance optimization required (database indexes)
- SEO enhancements needed (canonical tags, Open Graph)
- Security hardening recommended (XSS fix)
```

**Commit 3: Database Indexes (4cf0eba)**
```
perf(db): Add critical indexes for AI generator queries

Adds two composite indexes to Prompt model:
1. (ai_generator, status, deleted_at) for filtering
2. (ai_generator, created_on) for date sorting

Impact: 15x query performance improvement
Improves @django-expert rating from 7.5 → 9.0/10
```

### Next Steps

**✅ Production Deployment Complete:**
1. ✅ Migration applied (Heroku v409)
2. ✅ Indexes active in production
3. ✅ Verified with showmigrations

**Current Status:**
- AI generator pages live and functional
- Query performance optimized (15x improvement)
- Ready for SEO improvements

**Week 1 Improvements (1 hour → 8.5/10):**
1. Add canonical tags + rel="prev"/rel="next"
2. Add BreadcrumbList schema (JSON-LD)
3. Add basic Open Graph tags

**Month 1 Polish (29 hours → 9.5/10):**
1. Fix XSS vulnerability (use template includes)
2. Expand content depth (800-1200 words per generator)
3. Add FAQ sections with FAQPage schema
4. Add unit tests (8-10 test cases)
5. Refactor view into class-based view

### Lessons Learned

**What Went Well:**
- Comprehensive agent validation caught critical issues early
- Moving AI_GENERATORS to constants.py improved architecture
- Input validation prevented security issues
- Query optimization patterns followed Django best practices

**What Could Be Improved:**
- Should have considered database indexes during initial implementation
- Could have used template includes instead of HTML in constants from start
- Should have added canonical tags in initial template

**Agent Feedback Value:**
- @django-expert caught performance bottleneck (saved 15x slowdown)
- @seo-authority-builder identified 60K+ session opportunity
- @code-reviewer found XSS vulnerability before production
- **Total preventative value:** 3 critical production issues avoided

---

**URLs:**
- **Domain:** promptfinder.net
- **Live Site:** https://mj-project-4-68750ca94690.herokuapp.com/ (current)
- **Repository:** [Add GitHub URL]

**Brand Identity:**
- Users are called "Prompt Finders"
- Community = "Finder Community"
- Tagline: "Find. Create. Share."
- Mission: "Make every prompt finder successful"

---

## 🛠️ Technical Stack

### Frontend
- Django Templates (4.2.13)
- Bootstrap 5
- Custom CSS
- Vanilla JavaScript

### SVG Icon System (Phase J.2)

**Status:** ✅ COMPLETE (December 23, 2025)

PromptFinder uses a custom SVG sprite system for navigation icons, replacing Font Awesome for better performance and consistency.

**Files:**
- `static/icons/sprite.svg` - SVG sprite with all icon definitions
- `static/css/components/icons.css` - Icon utility classes

**Current Icons (5):**
| Icon ID | Source | Usage |
|---------|--------|-------|
| `icon-image` | Lucide | Photos filter, media type indicator |
| `icon-video` | Lucide | Videos filter, media type indicator |
| `icon-search` | Lucide | Search dropdown icon |
| `icon-trophy` | Lucide | Leaderboard dropdown icon |
| `icon-lightbulb` | Lucide | Prompts dropdown icon |

**Usage Pattern:**
```html
<svg class="icon icon-sm">
  <use href="{% static 'icons/sprite.svg' %}#icon-name"/>
</svg>
```

**Size Classes:**
- `.icon-xs` - 12px (0.75rem)
- `.icon-sm` - 22px (1.4rem) - Default for navigation
- `.icon-md` - 24px (1.5rem)
- `.icon-lg` - 24px (1.5rem)

**Dropdown Icon Styling:**
SVG icons in dropdowns require direct CSS variable assignment (not `currentColor`) due to `<use>` shadow DOM boundaries:
```css
.pexels-dropdown-icon {
    stroke: var(--gray-700);  /* Direct color for <use> compatibility */
}
```

**Icon Source:** Lucide Icons (https://lucide.dev) - MIT License

### Backend
- Django 4.2.13
- Python 3.12
- Django Allauth (authentication)
- Django Taggit (tagging system)

### Database
- **Current:** PostgreSQL (Code Institute trial - expires 2026-2027)
- **Migration Target:** Heroku PostgreSQL Mini
- **Migration Priority:** Phase 1 (Immediate)

### Database Schema Updates

#### Trash Bin System (Phase 2)

**Prompt Model Changes:**
```python
class Prompt(models.Model):
    # ... existing fields ...
    
    # Soft delete fields (Phase 2)
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this prompt was moved to trash"
    )
    deleted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deleted_prompts',
        help_text="User who deleted this prompt"
    )
    deletion_reason = models.CharField(
        max_length=50,
        choices=[
            ('user', 'User Deleted'),
            ('orphaned_image', 'Orphaned Cloudinary File'),
            ('missing_image', 'Prompt Missing Image'),
            ('moderation', 'Content Moderation'),
            ('admin_manual', 'Admin Manual Delete'),
            ('expired_upload', 'Abandoned Upload Session'),
        ],
        default='user',
        help_text="Why was this prompt deleted?"
    )
    
    # Indexes for performance
    class Meta:
        indexes = [
            models.Index(fields=['deleted_at']),  # Fast trash queries
            models.Index(fields=['author', 'deleted_at']),  # User trash
        ]
    
    # Custom managers
    objects = PromptManager()  # Excludes deleted
    all_objects = models.Manager()  # Includes deleted
    
    # Methods
    def soft_delete(self, user):
        """Move to trash (soft delete)"""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.status = 0  # Hide from public
        self.save()
    
    def restore(self):
        """Restore from trash"""
        self.deleted_at = None
        self.deleted_by = None
        self.status = 1  # Publish
        self.save()
    
    def hard_delete(self):
        """Permanent deletion with Cloudinary cleanup"""
        if self.featured_image:
            cloudinary.uploader.destroy(
                self.featured_image.public_id,
                resource_type='image' if self.is_image else 'video'
            )
        self.delete()  # Remove from database
    
    @property
    def days_until_permanent_deletion(self):
        """Calculate days remaining in trash"""
        if not self.deleted_at:
            return None
        retention_days = 30 if self.author.is_premium else 5
        expiry = self.deleted_at + timedelta(days=retention_days)
        remaining = (expiry - timezone.now()).days
        return max(0, remaining)
    
    @property
    def is_in_trash(self):
        """Check if currently in trash"""
        return self.deleted_at is not None
    
    @property
    def is_expiring_soon(self):
        """Check if expires in < 24 hours"""
        days_left = self.days_until_permanent_deletion
        return days_left is not None and days_left < 1

### Media Storage
- **Cloudinary** (permanent solution)
- Free tier: 25GB storage, 25 credits/month
- Handles: Image optimization, transformations, delivery
- **Decision:** Stick with Cloudinary long-term (not migrating to Supabase)

### Hosting
- **Heroku** (Eco Dyno)
- Credits: $248 remaining (covers costs until late 2026)
- Infrastructure: AWS-backed, 99.9% uptime SLA

### Management Commands (Phase D.5)
- **cleanup_deleted_prompts** - Automated trash cleanup (5-30 day retention)
  - Deletes expired prompts from database + Cloudinary
  - Email summaries to admins
  - Dry-run mode for testing
  - ~10-30 seconds execution time
- **detect_orphaned_files** - Cloudinary orphan detection
  - Scans for files without database entries
  - Date filtering (--days N or --all)
  - CSV report generation
  - API usage monitoring (rate limit protection)
  - ~10-60 seconds execution time

### Automation
- **Heroku Scheduler** - Daily automated tasks ($0/month)
  - 03:00 UTC: cleanup_deleted_prompts (daily)
  - 04:00 UTC: detect_orphaned_files --days 7 (daily)
  - 05:00 UTC Sunday: detect_orphaned_files --days 90 (weekly, optional)
  - Uses spare Eco dyno hours (0.17% monthly allocation)
  - API efficient: <1% of Cloudinary daily limit

### Payment Processing
- **Stripe** (Phase 2)
- Subscriptions, trial management, webhooks

### AI Services
- **OpenAI GPT-4:** Text moderation, comment moderation, chatbot
- **Cloudinary AI Vision:** Custom image moderation (minors, gore, satanic content)
- **AWS Rekognition (via Cloudinary):** Standard content moderation

---

## 💰 Infrastructure & Costs

### Current Costs (Phase 1)
| Service | Cost | Status |
|---------|------|--------|
| Heroku Eco Dyno | $5/month | Covered by credits |
| PostgreSQL Mini | $5/month | Covered by credits |
| Cloudinary Free | $0 | Free tier (25GB) |
| OpenAI API | ~$0.50/1000 uploads | Pay-as-you-go |
| **Total** | **~$10/month** | Credits cover hosting |

### Projected Costs at 1,000 Users
| Service | Cost | Notes |
|---------|------|-------|
| Heroku Eco Dyno | $10/month | Scaled up |
| PostgreSQL Mini | $5/month | Adequate for 1K users |
| Cloudinary Plus | $89/month | 25GB → 125GB, more transformations |
| AI Moderation | $10-15/month | OpenAI Vision + text |
| **Total** | **$99-109/month** | Out of pocket: $89 (credits cover $10) |

### Projected Costs at 10,000 Users
| Service | Cost | Notes |
|---------|------|-------|
| Heroku | $50-100/month | Performance tier |
| PostgreSQL | $50/month | Standard tier |
| Cloudinary Advanced | $549/month | High volume |
| AI Services | $50-100/month | Scaled moderation |
| **Total** | **$699-799/month** | 5% of projected revenue |

### Revenue Projections
| Users | 10% Premium Conversion @ $7/month | Affiliate Income | Total Revenue | Profit Margin |
|-------|-----------------------------------|------------------|---------------|---------------|
| 1,000 | $700/month | $100-200/month | $800-900/month | 88% ($700-800) |
| 5,000 | $3,500/month | $500-800/month | $4,000-4,300/month | 85% ($3,600) |
| 10,000 | $7,000/month | $1,000-1,500/month | $8,000-8,500/month | 90% ($7,300) |

**Key Insight:** Cloudinary costs scale with success but remain 5-7% of revenue - sustainable long-term.

---

## 📅 Development Phases

## PHASE 1: PRE-LAUNCH (2-3 Weeks) 🚨

**Goal:** Safe, functional, SEO-optimized platform ready for soft launch

### Infrastructure (2 hours)
- [ ] Migrate PostgreSQL from Code Institute to Heroku PostgreSQL Mini
- [ ] Custom domain setup (promptfinder.net)
- [ ] SSL/HTTPS configuration
- [ ] Update all references to new domain

### Content Moderation System (3-4 days) **CRITICAL** ✅ COMPLETED
- [ ] **AI Moderation Implementation:**
  - [ ] AWS Rekognition via Cloudinary (images/videos)
  - [ ] Cloudinary AI Vision for custom checks
  - [ ] OpenAI Moderation API for text
- [ ] **Banned Content Detection:**
  - [ ] Explicit nudity/sexual content
  - [ ] Violence, gore, blood, vomit
  - [ ] Minors/children (anyone under 18) - ZERO TOLERANCE
  - [ ] Satanic/occult imagery
  - [ ] Hate symbols
  - [ ] Medical/graphic content (childbirth, surgery, corpses)
  - [ ] Visually disturbing content
- [ ] **Appeal System:**
  - [ ] User can contest rejected uploads
  - [ ] Temporary Cloudinary storage for appeals (7 days)
  - [ ] Admin review dashboard
  - [ ] Email notifications on appeal status
- [ ] **Report Feature:**
  - [ ] "Report" button on each prompt
  - [ ] Report reasons dropdown
  - [ ] Auto-hide prompts after 3+ reports
  - [ ] Admin review panel
  - [ ] IP tracking for anonymous reports

### SEO Implementation (2-3 days)
- [ ] **Image Filename Optimization:**
  - [ ] Extract keywords from prompt text
  - [ ] AI fallback for short prompts (<5 words)
  - [ ] Format: `keyword1-keyword2-[ai-generator]-prompt-[timestamp].jpg`
  - [ ] Example: `cyberpunk-neon-cityscape-midjourney-prompt-1234567890.jpg`
- [ ] **Alt Tag Strategy:**
  - [ ] Format: `"[Title] - [AI Generator] Prompt - AI-generated image"`
  - [ ] Context-specific for thumbnails vs full images
  - [ ] Max 125 characters
- [ ] **H1 Tag Structure:**
  - [ ] Format: `"[Title] - [AI Generator] Prompt"`
  - [ ] One H1 per page
- [ ] **Meta Descriptions:**
  - [ ] 155-160 characters
  - [ ] Include keywords + CTA
  - [ ] Generate from prompt excerpt
- [ ] **Structured Data (Schema.org):**
  - [ ] Article schema
  - [ ] HowTo schema (how to use prompt)
  - [ ] ImageObject schema
  - [ ] BreadcrumbList schema
  - [ ] Person schema (author)
- [ ] **Additional SEO:**
  - [ ] Sitemap.xml generation
  - [ ] Robots.txt configuration
  - [ ] Canonical URLs
  - [ ] Open Graph tags
  - [ ] Twitter Card tags
  - [ ] Last modified dates

### Upload Page Improvements (1 day)
- [ ] **Tag Selection System:**
  - [ ] 27 preset tags (user selects up to 3)
  - [ ] AI pre-populates suggested tags
  - [ ] Autocomplete for tag search
  - [ ] Tag validation (flags mismatches for admin review)
- [ ] **File Limits Enforcement:**
  - [ ] Images: 10MB max
  - [ ] Videos: 100MB max, 20 seconds duration
  - [ ] Instant feedback on violations
- [ ] **Upload Counter Display:**
  - [ ] Pexels-style banner: "You have X uploads left"
  - [ ] Progress bar in dashboard
  - [ ] Warning when approaching limit

### Prompt Page Fixes (1-2 days)
- [ ] Fix image display issues
- [ ] Reorganize content layout (prompt description as focus)
- [ ] Improve mobile responsiveness
- [ ] Add breadcrumb navigation

### Basic Filtering (2 days)
- [ ] Filter by type (image/video)
- [ ] Filter by category (27 preset tags)
- [ ] Filter by date (any, 24h, week, month, year)
- [ ] Filter by AI generator

### Legal Pages (2-3 days) **CRITICAL**
- [ ] Privacy Policy (GDPR-compliant)
- [ ] Terms of Service / User Agreement
- [ ] Community Guidelines / Rules
- [ ] Cookie Policy
- [ ] Copyright / DMCA Policy
- [ ] Age verification statement (13+)

### Cloudinary Cleanup (4 hours)✅ COMPLETED
- [ ] Implement Django signal to delete Cloudinary assets when prompts deleted
- [ ] Prevent orphaned files

### Social Login (End of Phase 1) (1 day)
- [ ] Google OAuth integration
- [ ] Apple Sign In integration
- [ ] Update signup/login pages
- [ ] Test authentication flow

**Phase 1 Total Estimate:** 15-18 days

---

## PHASE 2: LAUNCH (First Month) 💰

**Goal:** Monetization, user management, community growth

### Soft Launch Strategy (1 week)
- [ ] **Invite Code System:**
  - [ ] Generate unique codes per user (5 codes each, admin configurable)
  - [ ] Signup requires invite code
  - [ ] "Request Invite" waitlist page
  - [ ] PromptCoin rewards: 500 coins per successful invite
  - [ ] Track referral chains
- [ ] **Beta Tester Recruitment:**
  - [ ] Personal network (50-100 invites)
  - [ ] Reddit/Discord communities (controlled rollout)
  - [ ] Track engagement metrics

### Upload Limits (Launch Phase) (1 day)
- [ ] **Free Users:** 10 uploads per WEEK (first 3-6 months)
- [ ] **Trial Users:** Unlimited (14 days)
- [ ] **Premium Users:** Unlimited
- [ ] Admin toggle: Switch to monthly limits after launch phase
- [ ] Configurable in admin: upload count, period (day/week/month)

### Stripe Integration (3-4 days)
- [ ] Stripe account setup
- [ ] Subscription creation (monthly $7, annual $70)
- [ ] **14-day free trial with card required**
- [ ] Webhook handlers (payment success, failure, cancellation)
- [ ] Customer portal integration
- [ ] Receipt generation

### Premium Features Implementation (1 week)
- [ ] **Private Prompts:**
  - [ ] Toggle on upload: public/private
  - [ ] Only owner can view private prompts
  - [ ] Selective sharing capabilities
- [ ] **Unlimited Uploads:**
  - [ ] Remove weekly limit for premium users
- [ ] **Ad-Free Experience:**
  - [ ] Conditional template rendering (hide ads for premium)
  - [ ] Faster page loads
- [ ] **Basic Analytics Dashboard:**
  - [ ] View count per prompt
  - [ ] Like count over time
  - [ ] Comment engagement
  - [ ] Top performing prompts
- [ ] **Collections (Simple Version):**
  - [ ] Create custom folders
  - [ ] Add prompts to collections
  - [ ] Public/private collections
- [ ] **Verified Badge:**
  - [ ] Display next to username
  - [ ] Show in search results

### Trial & Billing Management (1 week)
- [ ] **Trial System:**
  - [ ] 14-day countdown timer
  - [ ] Email reminders (Day 11, Day 13)
  - [ ] Auto-charge after trial
  - [ ] 24-hour refund grace period
- [ ] **Billing Page:**
  - [ ] View current plan
  - [ ] Update payment method
  - [ ] Switch to annual plan
  - [ ] Cancel subscription
  - [ ] Billing history with receipts
  - [ ] Usage stats (uploads, storage)
- [ ] **Cancellation Flow:**
  - [ ] Retention offers (pause, discount, annual switch)
  - [ ] Exit survey (why leaving?)
  - [ ] Graceful downgrade to free tier

### Marketing Pages (2 days)
- [ ] **Pricing Page:**
  - [ ] Free vs Premium comparison table
  - [ ] Feature breakdown
  - [ ] Annual savings highlight
  - [ ] FAQ section
  - [ ] Testimonials (after collecting)
- [ ] **FAQ Page:**
  - [ ] Account questions
  - [ ] Billing questions
  - [ ] Content policy questions
  - [ ] Technical support
  - [ ] Premium features explained

### Affiliate Links (1 day)
- [ ] "Created in [AI Generator]" badges on prompts
- [ ] Link to AI generator with affiliate parameters
- [ ] Track clicks/conversions
- [ ] Admin dashboard for affiliate stats

### User Dashboard (2-3 days)
- [ ] **Overview:**
  - [ ] Upload counter with progress bar
  - [ ] Total prompts, likes, views, comments
  - [ ] PromptCoin balance
  - [ ] Invite codes remaining
- [ ] **My Prompts:**
  - [ ] Grid view of uploaded prompts
  - [ ] Filter: public/private, by date, by AI generator
  - [ ] Quick actions: edit, delete, make private/public
- [ ] **My Collections:**
  - [ ] View/manage collections
  - [ ] Add/remove prompts
- [ ] **Analytics (Premium):**
  - [ ] Detailed stats per prompt
  - [ ] Engagement over time
  - [ ] Export data

### Notifications System (2-3 days)
- [ ] **Bell Icon Implementation:**
  - [ ] Navbar notification bell
  - [ ] Unread count badge
  - [ ] Dropdown preview (recent 5 notifications)
  - [ ] 30-second polling for updates
- [ ] **Notification Types:**
  - [ ] Like: Someone liked your prompt
  - [ ] Comment: New comment on your prompt
  - [ ] Follow: New follower
  - [ ] Warning: Issued by admin
  - [ ] Restriction: Account restriction
  - [ ] Appeal: Appeal status update
  - [ ] Trial: Trial ending soon, trial ended
  - [ ] Upload limit: Approaching/reached limit
- [ ] **Notification Center Page:**
  - [ ] List all notifications
  - [ ] Filter by type
  - [ ] Mark as read/unread
  - [ ] Mark all read
  - [ ] Pagination
- [ ] **Special Notifications:**
  - [ ] Requires acknowledgement (warnings, restrictions)
  - [ ] Priority levels (low, normal, high, urgent)
  - [ ] @ mentions from users

### Warning & Restriction System (2 days)
- [ ] **Warning Model:**
  - [ ] Types: inappropriate content, spam, harassment, copyright, false reports
  - [ ] Severity: minor, moderate, severe, final
  - [ ] Requires user acknowledgement
  - [ ] Notification on issue
- [ ] **Restriction Model:**
  - [ ] Types: probation, upload ban, comment ban, temporary ban, permanent ban
  - [ ] Duration: temporary (expires) or permanent
  - [ ] Appeal system
  - [ ] Admin review dashboard
- [ ] **User Profile Tracking:**
  - [ ] Total warnings count
  - [ ] Total violations count
  - [ ] Strikes (3 strikes = auto-ban)
  - [ ] Account status: good standing, probation, restricted, banned
- [ ] **Admin Actions:**
  - [ ] Issue warning
  - [ ] Apply restriction
  - [ ] Lift restriction
  - [ ] Review appeals
  - [ ] View user violation history

### Persistent Join Modal (1 day)
- [ ] **Trigger Configuration (Admin Configurable):**
  - [ ] After 2 pages viewed → show modal
  - [ ] Then every 2 pages
  - [ ] After scrolling 60 prompts → show modal
  - [ ] Then after 30 prompts
  - [ ] Then after 15 prompts
  - [ ] Then every 15 prompts
- [ ] **Modal Content:**
  - [ ] Compelling value proposition
  - [ ] Premium features highlight
  - [ ] CTA: Sign up / Start free trial
  - [ ] Dismissible (cookie-based, returns on next trigger)

### Content Expansion (3-4 days)
- [ ] **Prompt Page Enhancements:**
  - [ ] Expand to 800-1500 words
  - [ ] Add "About This Prompt" section
  - [ ] Add "How to Use" section
  - [ ] Add "Tips for Best Results" section
  - [ ] Add "What Makes This Effective" section
  - [ ] Add FAQ section (FAQPage schema)
- [ ] **Related Content:**
  - [ ] Related prompts section (same tags)
  - [ ] More from author section
  - [ ] Similar AI generator prompts
- [ ] **Trust Signals:**
  - [ ] Author info box (bio, stats, prompts count)
  - [ ] View count, like count, comment count
  - [ ] Verified badge if applicable
  - [ ] Copy count (how many times copied)

**Phase 2 Total Estimate:** 20-25 days

---

## PHASE 3: GROWTH (Months 2-3) 📈

**Goal:** Advanced features, gamification, social engagement

### PromptCoins System (1 week)
- [ ] **Earning Mechanisms:**
  - [ ] Upload prompt: 50 coins
  - [ ] Get a like: 5 coins
  - [ ] Leave comment: 10 coins
  - [ ] Daily login: 20 coins
  - [ ] Complete profile: 100 coins (one-time)
  - [ ] Successful referral: 500 coins
  - [ ] Premium users: 2x earning rate
  - [ ] Premium monthly allowance: 500 coins/month
- [ ] **Spending Options:**
  - [ ] 1 week ad-free: 100 coins
  - [ ] Featured prompt (24h): 200 coins
  - [ ] Extra upload slot: 50 coins
  - [ ] Unlock premium template: 150 coins
  - [ ] Premium users: 50% discount on spending
- [ ] **Purchase Coins (Stripe Integration):**
  - [ ] 500 coins = $2.99
  - [ ] 1500 coins = $7.99 (save 12%)
  - [ ] 5000 coins = $19.99 (save 33%)
- [ ] **Admin Dashboard:**
  - [ ] Coin economy balance monitoring
  - [ ] Adjust earning/spending rates
  - [ ] View top earners/spenders
  - [ ] Coin transaction logs

### Advanced AI Auto-Tagging (1 week)
- [ ] **Technical Metadata Detection (AI-powered):**
  - [ ] Orientation: portrait, landscape, square
  - [ ] People count: 0, 1, 2, 3+
  - [ ] Age range: teenager, adult, senior (for moderation)
  - [ ] Store as hidden metadata (not public tags)
- [ ] **Tag Validation System:**
  - [ ] User selects up to 3 tags from presets
  - [ ] AI validates tag accuracy
  - [ ] If mismatch (confidence >0.8):
    - [ ] Approve prompt anyway (no delay)
    - [ ] Flag for admin review
    - [ ] Admin has 2-4 days to review (configurable)
    - [ ] If not reviewed: auto-apply AI suggested tags
  - [ ] Admin can toggle validation on/off
  - [ ] User never knows about flagging (seamless UX)
- [ ] **Sensitive Attributes (Private Filtering Only):**
  - [ ] DO NOT auto-tag ethnicity publicly
  - [ ] Store as private metadata for filtering only
  - [ ] Never display on prompt pages
  - [ ] Legal review recommended for GDPR compliance

### Advanced Filtering (3-4 days)
- [ ] **All Filter Types:**
  - [ ] Type: image, video
  - [ ] Orientation: portrait, landscape, square
  - [ ] Category: 209 preset tags
  - [ ] AI Generator: all supported generators
  - [ ] Age range: teenager, adult, senior (content rating)
  - [ ] People count: 0, 1, 2, 3+
  - [ ] Date: any, 24h, week, month, year
  - [ ] Sort: top (day/month/all-time), recent, trending
- [ ] **Filter Combinations:**
  - [ ] Multiple filters active simultaneously
  - [ ] Clear filters button
  - [ ] Save filter preferences (premium)
- [ ] **Search Integration:**
  - [ ] Keyword search + filters
  - [ ] Filter results in real-time

### Daily Leaderboard (2-3 days)
- [ ] **Leaderboard Categories:**
  - [ ] Top uploaders today
  - [ ] Top liked prompts today
  - [ ] Top commented prompts today
  - [ ] Top coin earners today
- [ ] **Display:**
  - [ ] Top 10 in each category
  - [ ] User profile links
  - [ ] Stats displayed
  - [ ] Coin rewards for top 3 (e.g., 100/50/25 coins)
- [ ] **Reset:** Daily at midnight (configurable timezone)
- [ ] **Historical:** View past days' leaderboards

### Follow System (3-4 days)
- [ ] **Follow/Unfollow:**
  - [ ] Follow button on user profiles
  - [ ] Follower/following counts
  - [ ] Notification when followed
- [ ] **Following Page:**
  - [ ] List of users you follow
  - [ ] Unfollow button
  - [ ] View their prompts
- [ ] **Followers Page:**
  - [ ] List of your followers
  - [ ] View their profiles

### User Feeds (2-3 days)
- [ ] **Personalized Feed:**
  - [ ] Show prompts from followed users
  - [ ] Chronological + algorithmic mix
  - [ ] "New prompts from people you follow"
- [ ] **Discover Feed:**
  - [ ] Trending prompts
  - [ ] Recommended based on likes/views
  - [ ] Prompts in tags you engage with

### Enhanced User Profiles (2 days)
- [ ] **Profile Page Improvements:**
  - [ ] Cover image upload
  - [ ] Bio (max 500 characters)
  - [ ] Social media links
  - [ ] Location (optional)
  - [ ] Joined date
  - [ ] Stats: total prompts, likes received, followers
  - [ ] Badges: verified, master finder, top contributor
- [ ] **Public Profile:**
  - [ ] Grid of user's prompts
  - [ ] Filter: public only, by date, by AI generator
  - [ ] Follow button
  - [ ] Activity feed (recent uploads)

### Premium Analytics (Advanced) (3-4 days)
- [ ] **Detailed Metrics:**
  - [ ] Views over time (graph)
  - [ ] Engagement rate (likes/views ratio)
  - [ ] Comment sentiment analysis
  - [ ] Best performing tags
  - [ ] Traffic sources (where views come from)
  - [ ] Peak engagement times
- [ ] **Export Data:**
  - [ ] CSV export of all prompts
  - [ ] CSV export of analytics
  - [ ] Backup feature

### API Access (Premium) (1 week)
- [ ] **REST API:**
  - [ ] Authentication: API key per user
  - [ ] Endpoints: list prompts, get prompt, create prompt, update prompt, delete prompt
  - [ ] Rate limiting: free (100/day), premium (unlimited)
  - [ ] Documentation page
- [ ] **Use Cases:**
  - [ ] Integrate prompts into apps
  - [ ] Bulk operations
  - [ ] Automation workflows

### Bulk Upload (Premium) (1-2 days)
- [ ] **Upload Multiple Prompts:**
  - [ ] CSV import (title, content, tags, AI generator)
  - [ ] ZIP upload (images + metadata JSON)
  - [ ] Preview before publishing
  - [ ] Batch processing

**Phase 3 Total Estimate:** 25-30 days

---

## PHASE 4: POLISH & SCALE (Month 3+) ✨

**Goal:** Optimization, advanced monetization, community features

### Prompt Courses/Guidebook Monetization (1 week)
- [ ] **Digital Products:**
  - [ ] "The Ultimate Prompt Guide" eBook ($19)
  - [ ] "Midjourney Mastery" video course ($49)
  - [ ] "DALL-E Secrets" tutorial pack ($29)
- [ ] **Marketing:**
  - [ ] Banner ads on site (premium users exempt)
  - [ ] Email campaign to free users
  - [ ] Affiliate partnerships with course creators
- [ ] **Delivery:**
  - [ ] Gumroad/Teachable integration
  - [ ] Or host on PromptFinder (premium CMS)

### AI Comment Bot (1 week) **NICE-TO-HAVE**
- [ ] **PromptFinder Assistant Bot:**
  - [ ] Special AI user account
  - [ ] Posts helpful comments publicly
  - [ ] @ mentions users (triggers notifications)
- [ ] **Comment Types (Start Simple):**
  - [ ] Milestone celebrations: "🎉 @username hit 100 uploads!"
  - [ ] Helpful answers: "💡 @username here's how to..."
  - [ ] Trend alerts: "🔥 This prompt is trending!"
- [ ] **Safety Features:**
  - [ ] Rate limiting: max 50 comments/day
  - [ ] Max 1 comment per user/day
  - [ ] Max 1 comment per prompt
  - [ ] Confidence threshold: >0.85 to comment
  - [ ] Admin can delete/edit any AI comment
  - [ ] Admin can toggle comment types on/off
  - [ ] User opt-out in settings
- [ ] **Admin Log Dashboard:**
  - [ ] View all AI comments
  - [ ] Edit templates
  - [ ] View reactions/replies
  - [ ] Analytics (helpful rate, engagement)
  - [ ] Export logs

### Chatbot + Anti-Abuse System (3-4 days)
- [ ] **Bottom-Right Chatbot Widget:**
  - [ ] Always visible chat bubble
  - [ ] Opens chat window on click
  - [ ] Unread message badge
- [ ] **PromptFinder Assistant (Chatbot Scope):**
  - [ ] Account & billing questions
  - [ ] How to use PromptFinder features
  - [ ] Policies & guidelines explanations
  - [ ] Prompt creation tips
  - [ ] Deflects off-topic questions politely
- [ ] **Anti-Abuse for Comments:**
  - [ ] Detects off-topic bot mentions in comments
  - [ ] Auto-removes comment
  - [ ] Redirects to chatbot
  - [ ] Educates user on guidelines
  - [ ] Escalates after 3 offenses (warning → restriction)
  - [ ] Admin logs all redirections
- [ ] **Education Flow:**
  - [ ] First offense: gentle reminder
  - [ ] Second offense: firmer guidelines link
  - [ ] Third offense: warning + admin notification

### Marketplace (Sell Prompts) (2 weeks)
- [ ] **Prompt Sales:**
  - [ ] Users can price their prompts ($1-50)
  - [ ] PromptFinder takes 20-30% commission
  - [ ] Premium users: 10-15% commission
- [ ] **Licensing Options:**
  - [ ] Personal license (free to use personally)
  - [ ] Commercial license ($5-50)
  - [ ] Exclusive license (one buyer, higher price)
- [ ] **Payment:**
  - [ ] Stripe Connect integration
  - [ ] Payout to seller bank account
  - [ ] Transaction history
- [ ] **Discovery:**
  - [ ] "For Sale" filter
  - [ ] Price range filter
  - [ ] Best selling prompts

### Team Accounts (1 week)
- [ ] **Team Plan Pricing:** $20/month for 5 users
- [ ] **Features:**
  - [ ] Shared workspace
  - [ ] Team prompt library
  - [ ] Role-based permissions (admin, editor, viewer)
  - [ ] Collaboration tools (comment on drafts)
  - [ ] Team analytics

### Video Optimization (3-4 days)
- [ ] **Adaptive Streaming:**
  - [ ] Generate multiple quality versions (480p, 720p, 1080p)
  - [ ] Serve appropriate version based on device/connection
  - [ ] Mobile vs desktop optimization
- [ ] **Cloudinary Video Transformations:**
  - [ ] Auto-format (MP4, WebM)
  - [ ] Compression
  - [ ] Thumbnail generation

### Performance Optimization (1 week)
- [ ] **Lazy Loading:**
  - [ ] Images below fold
  - [ ] Infinite scroll for prompt lists
- [ ] **WebP Conversion:**
  - [ ] Cloudinary auto-format
  - [ ] Fallback to JPEG for unsupported browsers
- [ ] **CDN:**
  - [ ] Cloudinary CDN (already in use)
  - [ ] Static files CDN (Cloudfront/Cloudflare)
- [ ] **Database Optimization:**
  - [ ] Query optimization (select_related, prefetch_related)
  - [ ] Database indexing
  - [ ] Caching (Redis/Memcached)
- [ ] **Code Splitting:**
  - [ ] Lazy load JavaScript
  - [ ] Defer non-critical CSS

### A/B Testing System (1 week)
- [ ] **Test Variants:**
  - [ ] Trial length (7 vs 14 days)
  - [ ] Pricing ($7 vs $10)
  - [ ] Join modal timing
  - [ ] CTA button text
- [ ] **Metrics Tracking:**
  - [ ] Conversion rates
  - [ ] User engagement
  - [ ] Revenue per cohort
- [ ] **Admin Dashboard:**
  - [ ] View test results
  - [ ] Declare winner
  - [ ] Roll out winning variant

### Trash Bin / Soft Delete System (2-3 days)
- [ ] **Database Changes:**
  - [ ] Add `deleted_at` field (datetime, nullable)
  - [ ] Add `deleted_by` field (foreign key to User)
  - [ ] Create custom manager to exclude deleted prompts
  - [ ] Add methods: `soft_delete()`, `restore()`, `hard_delete()`
- [ ] **Trash Bin Page:**
  - [ ] List all deleted prompts with thumbnails
  - [ ] Show days remaining until permanent deletion
  - [ ] Restore button for each item
  - [ ] Delete forever button for each item
  - [ ] Empty entire trash button
- [ ] **Retention Rules:**
  - [ ] Free users: 5 days retention, 10 items max
  - [ ] Premium users: 30 days retention, unlimited items
- [ ] **Premium Features:**
  - [ ] Bulk restore (select multiple items)
  - [ ] Search within trash
  - [ ] Download from trash
- [ ] **Daily Cleanup:**
  - [ ] Management command: `python manage.py cleanup_trash`
  - [ ] Run via Heroku Scheduler at 4:00 AM daily
  - [ ] Delete expired items from Cloudinary + database
  - [ ] Cost: $0/month (uses spare dyno hours)
- [ ] **Notifications:**
  - [ ] Toast on delete: "Moved to trash. [Undo]"
  - [ ] Email: "Items expiring in 24 hours"
  - [ ] Dashboard badge showing trash count
- [ ] **UI Components:**
  - [ ] Delete confirmation modal
  - [ ] Permanent delete warning (requires typing "DELETE")
  - [ ] Empty trash confirmation
  - [ ] Expiring soon visual indicators (red/orange)
  - [ ] Premium upgrade prompt when trash full

**Effort:** 2-3 days  
**Priority:** High (key premium differentiator)


### Prompt Version History (3-4 days)
- [ ] **Version Control:**
  - [ ] Save prompt edits as versions
  - [ ] View edit history
  - [ ] Restore previous version
  - [ ] Compare versions side-by-side
- [ ] **Premium Feature:**
  - [ ] Free users: view-only history
  - [ ] Premium: full restore capabilities

**Phase 4 Total Estimate:** Ongoing (features added as needed)

---

## PHASE 5: QUALITY & DISCOVERY FEATURES ✨

**Goal:** Enhanced quality control and content discovery

### Content Quality Verification (2-3 days)
- [ ] **Image-Text Relevance Checking:**
  - [ ] Use OpenAI Vision to verify uploaded images match their prompt descriptions
  - [ ] Warn users if significant content mismatch detected (non-blocking)
  - [ ] Show relevance score in admin dashboard
  - [ ] Help surface high-quality, relevant prompts
  - [ ] Optional: Flag for review if confidence of mismatch >0.8
- [ ] **Quality Scoring System:**
  - [ ] Rate prompts based on image quality, description detail, engagement
  - [ ] Surface high-quality prompts in discovery feeds
  - [ ] "Editor's Pick" badge for exceptional prompts
- [ ] **Featured Collections:**
  - [ ] Curated collections of high-quality prompts
  - [ ] Weekly/monthly themes and challenges
  - [ ] Community spotlight features

**Phase 5 Total Estimate:** 5-7 days (low priority, implement after launch success)

---

## 🚨 Known Issues & Technical Debt

### ✅ Resolved Issues (Phase D Complete)

1. **Orphaned Cloudinary Assets - Deletion** ✅ COMPLETED
   - **Problem:** When prompts deleted, Cloudinary files not removed
   - **Impact:** Wasted storage, costs increase over time
   - **Solution:** Django signal to call `cloudinary.uploader.destroy()` on delete
   - **Status:** ✅ Implemented and working

2. **Orphaned Cloudinary Assets - Upload Abandonment** ✅ COMPLETED (Phase D)
   - **Problem:** Users upload to Cloudinary but abandon Step 2 form
   - **Impact:** Wasted Cloudinary storage from incomplete uploads
   - **Solution:**
     - Idle detection system (45-minute timeout)
     - Automatic Cloudinary cleanup on expiration
     - User extension option (30 additional minutes)
     - Manual cancel with asset deletion
   - **Status:** ✅ Implemented in Phase D

3. **Content Moderation** ✅ COMPLETED
   - **Problem:** No safeguards against inappropriate content
   - **Impact:** Legal liability, brand damage, user safety
   - **Solution:** Multi-layer AI moderation system (Profanity + OpenAI + Vision)
   - **Status:** ✅ Fully implemented and tested

### Phase D.5: Trash Bin + Orphaned File Management (Day 1 Complete ✅)

**Combined System for Asset Lifecycle Management**

**Problem:** 
- No unified system for deleted content recovery
- Orphaned Cloudinary files waste storage
- Prompts with missing images break feed experience
- No admin oversight of deletion patterns

**Solution:** Unified trash bin system with:
- User trash bins (5-day free / 30-day premium retention)
- Admin trash dashboard with orphaned file detection
- Automatic detection via daily management command
- Multiple admin support with admin-owned asset tracking

**Architecture:**
- Soft delete system (deleted_at, deleted_by, deletion_reason fields)
- Detection logic: Daily scan identifies orphaned Cloudinary files and prompts with missing images
- Admin dashboard: 4 tabs (All Trash, Orphaned Files, Missing Images, Admin-Owned Assets)
- User dashboard: Personal trash bin with restore/permanent delete
- Automation: Heroku Scheduler runs cleanup at 3:00 AM daily

**Status:** 🔄 Phase D.5 (2.5-3 days estimated)
**Priority:** High (affects quality, costs, premium feature)
**Effort:** 2.5-3 days

### Current Known Issues (Phase E)

1. **Code Institute PostgreSQL Dependency**
   - **Problem:** Database expires 2026-2027, not independent
   - **Impact:** Platform unusable after expiration
   - **Solution:** Migrate to Heroku PostgreSQL Mini
   - **Priority:** High (before 2026)
   - **Effort:** 2 hours (data export/import)

3. **Dual Upload Systems Complexity**
   - **Problem:** Two parallel upload flows (`/upload/` vs `/create-prompt/`)
   - **Impact:** Maintenance overhead, potential inconsistencies
   - **Solution:**
     - Phase E: Full integration testing
     - Phase 2: Deprecate `/create-prompt/` in favor of `/upload/`
     - Or: Migrate `/create-prompt/` to use same AI generation service
   - **Priority:** Medium (after Phase E testing)
   - **Effort:** 2-3 days

4. **Testing Timer Values in Production**
   - **Problem:** Current idle detection uses 1-minute testing values instead of 45-minute production values
   - **Impact:** Users may experience overly aggressive timeout warnings
   - **Solution:** 
     - Immediate: Change JavaScript constants to production values (45min/60sec)
     - Long-term: Admin panel configuration for dynamic timer adjustment
   - **Location:** prompts/templates/prompts/upload_step2.html lines ~410-412
   - **Priority:** High (affects user experience)
   - **Effort:** 5 minutes (constant change) + 4 hours (admin panel integration)

### UI/UX Issues (Fix in Phase 1-2)

1. **Upload Flow:**
   - [ ] Mobile responsiveness testing for Step 2 form
   - [ ] Tag autocomplete performance with large lists
   - [ ] Upload progress bar animation smoothness

2. **Prompt Detail Page:**
   - [ ] Preview image displaying incorrectly (sizing/alignment)
   - [ ] Content layout needs reorganization (description not prominent enough)
   - [ ] Mobile responsiveness issues

3. **General UI:**
   - [ ] Inconsistent styling between `/upload/` and `/create-prompt/`
   - [ ] Form validation display improvements
   - [ ] Button hover states missing in some areas

### Future Considerations (Phase 3+)
- Video optimization for different devices/connections
- Advanced caching strategy
- Database query optimization at scale
- Real-time features (WebSockets for live notifications)

**Admin Configurable Settings:**
- Idle timer values (initial timeout, warning duration, extension period)
- Upload limits per user tier (weekly/monthly quotas)
- Moderation sensitivity thresholds
- AI generation cost controls and rate limiting
- Cloudinary cleanup schedules and retention policies

**Benefits:** Real-time adjustments without code deployments, A/B testing capabilities, responsive user feedback implementation

### 🚀 Pre-Launch Tasks

**To complete before major production launch:**

- [ ] **Squash migrations** - Currently 37 migrations in `prompts/migrations/`. Squash to ~5 for cleaner deployment history.
  - Run: `python manage.py squashmigrations prompts <start> <end>`
  - Test thoroughly after squashing
  - Only do this once, right before launch

- [ ] Final security audit
- [ ] Performance testing under load

---

## ✅ Decisions Made

### Infrastructure Decisions

**1. Database: Heroku PostgreSQL (NOT Supabase)**
- **Reasoning:** 
  - Easy migration from Code Institute
  - Integrated with Heroku hosting
  - Adequate for projected scale
  - Covered by Heroku credits
- **Alternative Considered:** Supabase
- **Why Rejected:** No significant benefit, migration effort not justified

**2. Media Storage: Cloudinary (PERMANENT - NOT Supabase)**
- **Reasoning:**
  - Automatic image optimization (thumbnails, WebP, compression)
  - Built-in AI moderation and tagging
  - CDN included
  - Transformations on-the-fly
  - Cost scales with success (5-7% of revenue)
- **Alternative Considered:** Supabase Storage + custom image processing
- **Why Rejected:**
  - Would require 2 weeks development (Pillow, FFmpeg)
  - Ongoing maintenance burden
  - Lose automatic optimization features
  - Only saves $500/month at 10K users (not worth effort)
  - Break-even: 7.5 years
- **Migration Decision:** Stick with Cloudinary indefinitely
- **Rationale:** "If Cloudinary costs are a problem, business is good. At that point, we can afford Cloudinary."

**3. Hosting: Heroku**
- **Reasoning:**
  - $248 credits (covers costs until late 2026)
  - Easy deployment
  - AWS infrastructure (reliable, fast)
  - Custom domain support
  - 99.9% uptime SLA
- **Cost:** $10/month (covered by credits currently)

### Monetization Decisions

**4. Trial Period: 14 Days with Card Required**
- **Reasoning:**
  - Higher conversion (60-70% vs 10-20% without card)
  - Filters serious users
  - Industry standard for SaaS
  - Allows "forgot to cancel" revenue (ethical gray area but standard)
  - Two weeks gives users time to see value
- **Alternative Considered:** 7 days, no card required
- **Why 14 Days:** Product needs time to show value (users upload, get engagement, see results)
- **Why Card Required:** Conversion rate 3-4x higher
- **Implementation:**
  - Clear messaging: "Free for 14 days, then $7/month. Cancel anytime."
  - Email reminders: Day 11, Day 13
  - 24-hour refund grace period (no questions asked)
  - One-click cancellation in dashboard

**5. Pricing: $7/month (Monthly), $70/year (Annual)**
- **Free Tier:** 10 uploads/week (launch phase) → 5-10/month (growth phase)
- **Premium Tier:** Unlimited uploads + all features
- **Annual Discount:** Save $14/year (2 months free)
- **Target Conversion:** 10% free → premium

**6. Upload Limits Strategy**
- **Launch Phase (Months 1-6):** 10 uploads/week for free users
  - **Goal:** Build content library quickly
  - **Rationale:** Empty platform = no value = no retention
- **Growth Phase (Month 6+):** 5-10 uploads/month for free users
  - **Goal:** Create upgrade pressure
  - **Announcement:** 30 days advance notice with upgrade CTA
  - **Admin Config:** Easily switchable via settings


**6.5 Trash Bin: Premium Safety Net**
- **Free Tier:** 5-day retention, last 10 items only
- **Premium Tier:** 30-day retention (6x longer), unlimited capacity
- **Marketing Messages:**
  - "Never Lose Your Best Work"
  - "Accidentally deleted your masterpiece? Premium gives you 30 days to restore it—6x longer than free users"
  - "Unlimited trash capacity means unlimited peace of mind"
- **Pricing Page:**
  - Feature comparison: 5 days vs 30 days with visual emphasis
  - Checkmark for premium, X for free
  - "Safety Net" badge/icon
- **Conversion Triggers:**
  - When free user's trash reaches 10 items
  - When item expires (couldn't restore in time)
  - Day 4 email: "Upgrade for 30-day protection"
  - After deletion: "Premium prevents this"
- **Value Proposition:**
  - "Free: Quick safety net (5 days, 10 items)"
  - "Premium: Total peace of mind (30 days, unlimited)"

**7. PromptCoins Gamification**
- **Purpose:** Engage free users, create multiple monetization paths
- **Earning:** Uploads, likes, comments, daily login, referrals
- **Spending:** Temporary premium features, featured slots, extra uploads
- **Premium Benefit:** 2x earning rate + monthly allowance
- **Purchase Option:** Buy coins via Stripe ($2.99 - $19.99)
- **Rationale:** "Earning is slow, but premium members get 2x..." (conversion funnel)

**8. CSP Exemption for Upload Pages**
- **Decision:** Applied @csp_exempt decorator to upload views (upload_step1, upload_step2, upload_submit)
- **Rationale:** Cloudinary upload widget requires dynamic resource loading that conflicts with strict CSP
- **Alternative Considered:** Selective CSP rules, but widget loads unpredictable resources
- **Trade-off:** Security vs functionality - upload pages have reduced CSP protection
- **Status:** Temporary solution until Cloudinary provides CSP-compatible widget

**9. Dual Upload System Maintenance**
- **Current State:** Two parallel upload flows (/upload/ vs /create-prompt/)
- **Strategy:** 
  - Phase E: Integration testing to ensure consistency
  - Phase 2: Deprecate /create-prompt/ in favor of enhanced /upload/ flow
  - Migration path: Add AI generation to /create-prompt/ or sunset entirely
- **Justification:** /upload/ provides superior UX with AI assistance and session management

### SEO Decisions

**10. SEO Filename Strategy: Prompt Text + AI Fallback**
- **Primary:** Extract keywords from user's prompt text (FREE)
- **Fallback:** AI tagging if prompt < 5 words (costs ~$0.50/1000)
- **Format:** `keyword1-keyword2-[ai-generator]-prompt-[timestamp].jpg`
- **Reasoning:** User prompts are already keyword-rich, saves AI costs
- **Example:** `cyberpunk-neon-cityscape-midjourney-prompt-1234567890.jpg`

**11. Thumbnails: Cloudinary Transformations (NOT Separate Files)**
- **Strategy:** One master image, generate thumbnails via URL transformations
- **Benefits:** Saves storage, automatic caching, no duplication
- **Alt Tags:** Context-specific (different alt for thumbnail vs full image)
- **Example Transformation:** `/c_fill,w_300,h_200,g_auto,q_auto,f_auto/`

**12. SEO Consistency: Include "[AI Generator] Prompt" Everywhere**
- **H1:** `"[Title] - [AI Generator] Prompt"`
- **Alt Tag:** `"[Title] - [AI Generator] Prompt - AI-generated image"`
- **Filename:** `"[keywords]-[ai-generator]-prompt-[timestamp].jpg"`
- **Reasoning:** Captures searches like "midjourney prompt [topic]"

### Content Moderation Decisions

**13. AI Moderation: Multi-Layer Approach**
- **Layer 1:** AWS Rekognition (via Cloudinary) - standard moderation
- **Layer 2:** Cloudinary AI Vision - custom checks (minors, gore, satanic)
- **Layer 3:** OpenAI Moderation API - text moderation (FREE)
- **Cost:** ~$6-11 per 1000 images (extremely affordable)
- **Custom Rules:**
  - ZERO TOLERANCE: Minors, gore, satanic imagery, hate symbols
  - STRICT: Explicit nudity (0.7 threshold - revised from 0.2), violence (0.5 - revised from 0.3)
  - MODERATE: Suggestive nudity (0.4-0.69 pending review), Drugs (0.6), gambling (0.7)

**14. Comments: Keep with AI Moderation (NOT Disable)**
- **Reasoning:**
  - SEO critical (fresh content, engagement signals)
  - AI catches 90%+ of issues
  - Very cheap ($1-5/month)
  - Scalable (works at any volume)
- **Alternative Considered:** Disable comments entirely
- **Why Rejected:** SEO impact too severe
- **Implementation:**
  - Auto-approve (>0.8 confidence, safe)
  - Auto-remove (>0.8 confidence, violation)
  - Flag for review (0.5-0.8 confidence)
  - Admin reviews flagged comments (~30 min/day)

**15. AI Bot Personality: Helpful, NOT Snarky**
- **Decision:** AI bot is supportive, encouraging, educational
- **Rejected:** Snarky/sassy responses to users
- **Reasoning:**
  - Legal liability (defamation, discrimination)
  - Brand damage (unprofessional)
  - Escalation risk (toxicity spiral)
  - AI mistakes (misreads sarcasm)
  - Professional platform for monetization
- **Use Cases:**
  - Celebrate achievements
  - Answer questions
  - Provide tips
  - Never engages in drama/snark

### Social & Growth Decisions

**16. Soft Launch: Invite-Only (First 2-4 Weeks)**
- **Strategy:** Closed beta with invite codes
- **Benefits:**
  - Controlled scaling (manage server load)
  - Bug fixes before public launch
  - FOMO marketing ("Request invite")
  - Viral growth (users invite friends)
  - Quality control (invited users = engaged users)
- **Gamification:** 500 PromptCoins per successful invite

**17. Social Login: Google + Apple (Phase 1 End)**
- **Priority:** Google (70% users), Apple (15% users)
- **Skip:** Yahoo (dying), Microsoft (overkill), LinkedIn (not relevant)
- **Phase 2:** Facebook (if data shows demand)
- **Reasoning:** Critical for conversion, reduces signup friction 20-40%

**18. Tag Strategy: Hybrid User + AI**
- **User Action:** Selects up to 3 tags from 27 presets
- **AI Action:** Pre-populates suggested tags, validates selection
- **If Mismatch:** Approve anyway, flag for admin, auto-correct if not reviewed in 2-4 days
- **User Never Knows:** Seamless UX, no delays
- **Admin Control:** Toggle on/off, configure review deadline

### Brand & Marketing Decisions

**19. Brand Name: PromptFinder (NOT PromptFlow)**
- **Domain:** promptfinder.net
- **Reasoning:**
  - Search intent aligned ("find prompts")
  - Clear purpose
  - Marketing goldmine ("prompt finders" = user identity)
  - Better SEO (matches search behavior)
- **User Identity:** "Prompt Finders" (not "users")
- **Tagline:** "Find. Create. Share."
- **Mission:** "Make every prompt finder successful"


### Recent Decisions (January 2025)

**20. Tag Strategy: Expanded from 27 to 209 Tags**
- **Reasoning:**
  - More specific tags = better SEO (e.g., "Abandoned Buildings" vs generic "Architecture")
  - Richer vocabulary for AI suggestions
  - Better discoverability for users
  - Still manageable in admin dashboard
- **Implementation:** 19 categories with 5-15 tags each
- **User Experience:** Transparent autocomplete, no hidden sub-tag mapping
- **Dynamic Tags:** AI can suggest new tags → admin review queue → potentially added to master list
- **Alternative Considered:** 27 core tags with hidden sub-tags mapping
- **Why Rejected:** Misleading to users, loses specificity for SEO

**21. Combined AI Analysis: Vision + Text**
- **Decision:** Analyze both image AND prompt text for tag suggestions
- **Reasoning:**
  - Vision alone misses context (e.g., "mysterious explorer" mood from text)
  - Text alone misses visual details (e.g., silhouette, dramatic lighting)
  - Combined analysis gives most accurate, contextually relevant tags
- **Cost:** Same ~$0.00255 per upload (single API call)
- **Implementation:** One Vision API call analyzes visual + reads prompt text

**22. Prompt-Visual Relevance Checking**
- **Decision:** Verify uploaded images match their prompt descriptions
- **Status Logic:**
  - Score >0.8: Auto-publish (status=1)
  - Score 0.5-0.8: Pending admin review (status=0)
  - Score <0.5: Block upload with message
- **User Messaging:** "Your upload is under review. Our team will verify within 24-48 hours."
- **Reasoning:**
  - Prevents spam/mismatched content from day one
  - SEO benefit (Google penalizes mismatched alt text)
  - User trust (ensures prompts actually match images)
- **Cost:** Included in single combined API call

**23. SEO Automation in Python (Not AI)**
- **Decision:** Python handles filename/alt-tag generation after AI returns title
- **Reasoning:**
  - Separation of concerns (AI analyzes content, Python formats for web)
  - Cost efficiency (don't pay AI for string manipulation)
  - Flexibility (easy to adjust formats without changing AI prompts)
  - Reliability (deterministic vs AI potentially formatting inconsistently)

**24. Two-Step Upload Flow (Pexels-Inspired)**
- **Decision:** Progressive disclosure - upload first, then details form
- **Step 1:** Drag-and-drop with upload counter
- **Step 2:** Large preview + form (title, prompt, tags, AI generator)
- **Reasoning:**
  - Reduces cognitive load (one thing at a time)
  - Shows progress clearly
  - Industry-standard UX (Pexels, Unsplash, etc.)
  - Mobile-friendly

**25. Upload Counter: Weekly Limit for Free Users**
- **Decision:** "You have X uploads left this week" (10/week during launch)
- **Reasoning:**
  - Aligns with Phase 2 monetization strategy
  - Builds content library quickly during launch
  - Clear reset cadence (every Monday)
- **Later:** Switch to monthly limits after 3-6 months

**26. Tag Count: 5 Suggested Tags (Not 3)**
- **Decision:** AI suggests 5 tags, user can reduce to 3 or expand to 7 max
- **Reasoning:**
  - SEO best practices: 3-7 tags optimal
  - 5 gives good coverage without keyword stuffing
  - User has flexibility to adjust
- **Alternative Considered:** 3 tags only
- **Why 5:** Balances discoverability with quality

---
---

## 💰 Monetization Strategy

### Revenue Streams

**1. Premium Subscriptions (Primary)**
- Monthly: $7/month (14-day free trial)
- Annual: $70/year (save $14 = 2 months free)
- Target conversion: 10% of free users
- Premium features detailed below

**2. PromptCoins (Secondary)**
- Users buy coins: $2.99 (500) / $7.99 (1500) / $19.99 (5000)
- Spend on temporary perks: ad-free, featured slots, extra uploads
- Premium users earn 2x faster (conversion incentive)

**3. Affiliate Links (Passive)**
- "Created in [AI Generator]" badges link with affiliate codes
- Revenue: $100-200/month (1K users) → $1,000-1,500/month (10K users)
- Zero maintenance once implemented

**4. Marketplace (Future - Phase 4)**
- Users sell prompts, PromptFinder takes 20-30% commission
- Premium users: reduced commission (10-15%)

**5. Digital Products (Future - Phase 4)**
- Prompt courses ($49)
- Guidebook ebooks ($19-29)
- Template packs ($15-25)
- Affiliate partnerships with course creators

**6. Ads (Free Tier Only)**
- Subtle, non-intrusive ads for free users
- Premium removes all ads
- Revenue: ~$50-200/month depending on traffic

### Premium Features (Complete List)

**Free Tier:**
- Browse all prompts
- Like prompts
- Comment on prompts
- Upload prompts (10/week → 5-10/month after launch)
- Public prompts only
- See ads
- 5 invite codes
- Basic profile

**Premium Tier ($7/month or $70/year):**
- ✅ **Unlimited uploads** - No monthly limit
- ✅ **Private prompts** - Keep prompt library private, selective sharing
- ✅ **Ad-free experience** - Cleaner browsing, faster page loads
- ✅ **Advanced analytics** - Views, engagement, performance metrics, export data
- ✅ **Collections** - Organize prompts into custom folders/boards
- ✅ **Verified badge** - Trust signal, status symbol
- ✅ **Priority support** - Faster response times
- ✅ **Early access** - New features before public release
- ✅ **Prompt templates** - Access to premium prompt templates
- ✅ **Bulk upload** - Upload multiple prompts at once (CSV/ZIP)
- ✅ **API access** - Integrate prompts into apps, unlimited rate limit
- ✅ **Priority in search** - Better visibility, higher ranking
- ✅ **Export data** - Download all prompts, analytics
- ✅ **PromptCoins 2x** - Earn coins twice as fast
- ✅ **Monthly coin allowance** - 500 free coins/month
- ✅ **Marketplace discount** - 10-15% commission vs 20-30%
- ✅ **Custom profile URL** - promptfinder.net/username (optional)
- ✅ **No upload limit alerts** - Never see "X uploads left" warnings

### Conversion Strategy

**Free → Trial:**
- Persistent join modal (configurable triggers)
- Upload limit warnings ("Only 2 uploads left!")
- Feature discovery (hover over premium-only features)
- Dashboard upgrade prompts
- Success stories/testimonials

**Trial → Paid:**
- Email sequence (welcome, tips, reminder, last chance)
- Showcase premium features during trial
- Highlight achievements ("You uploaded 20 prompts - keep it going!")
- 24-hour refund guarantee (reduces commitment anxiety)

**Retention:**
- Cancellation flow with offers (pause, discount, annual)
- Exit survey (understand why leaving)
- Win-back campaigns (6 months after cancellation)

---

## 🛡️ Content Moderation

### Comprehensive Moderation Strategy

**Philosophy:** Multi-layer defense with AI + human oversight

### Banned Content (Complete List)

**ZERO TOLERANCE (Auto-reject):**
1. Minors/children (anyone appearing under 18 years old)
2. Explicit nudity or sexual content
3. Violence, gore, blood, graphic injuries
4. Vomit or bodily fluids
5. Satanic, occult, or demonic imagery
6. Hate symbols or extremist content
7. Medical/graphic content (childbirth, surgery, corpses, wounds)
8. Visually disturbing content (emaciated bodies, hanging, self-harm)

**STRICT MODERATION:**
9. Suggestive content (swimwear, underwear, revealing clothes)
10. Weapons or weapon violence
11. Drug use or paraphernalia
12. Rude gestures (middle finger, etc.)

**ALLOWED (with guidelines):**
13. Alcohol (in context - social settings, not promoting intoxication)
14. Tobacco (in context - not promoting smoking)
15. **Artistic nudity (classical art style, educational, non-sexual context)**
    - **Examples of ALLOWED artistic nudity:**
      - Classical sculpture/painting reproductions (David, Venus de Milo)
      - Fine art photography (non-sexual, artistic composition)
      - Educational/medical context (anatomy, breastfeeding)
      - Cultural/traditional dress (or lack thereof in cultural context)
    - **What gets FLAGGED FOR REVIEW (pending, not auto-rejected):**
      - Topless photos in non-sexual artistic context
      - Full nudity with artistic framing/composition
      - Nude backsides/buttocks (artistic context)
      - Body-positive content (non-sexual)
    - **What gets AUTO-REJECTED:**
      - Genitalia visible as primary focus
      - Sexual acts or simulation of sexual acts
      - Sexually suggestive poses (spread legs, touching genitals)
      - Fetish content or pornographic intent
      - Any nudity combined with sexual text/context in prompt

### AI Moderation Implementation

**Layer 1: AWS Rekognition (via Cloudinary)**
- **Confidence Thresholds:**
  - **Explicit nudity: 0.7 → AUTO-REJECT** (revised from 0.2)
    - Triggers: Genitalia visible, sexual acts, fetish content
  - **Suggestive nudity: 0.4-0.69 → PENDING REVIEW** (new range)
    - Triggers: Topless, artistic nudity, body-positive content
  - **Suggestive clothing: 0.3-0.39 → PENDING REVIEW** (revised from 0.3 auto-flag)
    - Triggers: Swimwear, underwear, revealing clothing
  - **Below 0.3 → AUTO-APPROVE**
  - **Violence/Gore: 0.5 → AUTO-REJECT** (revised from 0.3)
  - **Hate symbols: 0.2 → AUTO-REJECT** (VERY STRICT - unchanged)
  - **Visually disturbing: 0.4 → PENDING REVIEW** (revised from 0.2)
  - **Drugs: 0.6 → PENDING REVIEW** (unchanged)
  - **Rude gestures: 0.5 → PENDING REVIEW** (revised from 0.3)
- **Cost:** ~$1 per 1000 images

**Rationale for Threshold Changes:**
- Old 0.2 explicit threshold was TOO STRICT (false positives on artistic content)
- New 0.7 threshold catches actual pornography while allowing artistic nudity
- Added 0.4-0.69 range for human review of borderline artistic content
- Balances platform safety with artistic freedom
- Reduces false rejections by ~60-70%

**Layer 2: Cloudinary AI Vision (Custom Checks)**
- **Custom Questions:**
  1. "Does this image contain children or people under 18?"
  2. "Does this image contain satanic, occult, or demonic symbols?"
  3. "Does this image contain gore, blood, vomit, or bodily fluids?"
  4. "Does this image show childbirth, medical procedures, or graphic bodily content?"
  5. "Does this image contain extreme violence, injuries, or wounds?"
  6. "Does this image show death, corpses, or dead bodies?"
- **Rejection:** Any "yes" answer = auto-reject
- **Cost:** ~$5-10 per 1000 images

**Layer 3: OpenAI Moderation API (Text)**
- **Checks prompt text for:**
  - Hate speech
  - Sexual content
  - Violence
  - Self-harm
  - Harassment
- **Cost:** FREE

**Total Moderation Cost:** ~$6-11 per 1000 images

### Moderation Workflow

```
User uploads image/video
    ↓
1. OpenAI checks prompt text → Reject if flagged
    ↓
2. Cloudinary AWS Rekognition → Reject if confidence > threshold
    ↓
3. Cloudinary AI Vision custom checks → Reject if any "yes"
    ↓
4. All checks passed → APPROVED
    ↓
5. Post-publish: User reports, AI comment moderation
```

### User Report System

**Report Button:**
- Visible on every prompt page (subtle, not prominent)
- Modal with reason selection
- Optional description field

**Report Reasons:**
- Explicit/Adult Content
- Violence or Gore
- Hate Speech or Symbols
- Spam or Misleading
- Copyright Violation
- Inappropriate Content Involving Minors
- Other (please specify)

**Auto-Actions:**
- 3+ reports → Auto-hide prompt, notify admin
- Admin review required
- Reporter anonymity protected

**Admin Dashboard:**
- View all reports
- Filter by status (pending, reviewed, dismissed, action taken)
- Take action: approve, remove prompt, warn user, ban user
- Track reporter abuse (false reports)

### Appeal System

### Pending Review & Appeal System

**When Upload Flagged for Review (Borderline Content):**
1. User sees "Pending Review" message
2. Content stored on Cloudinary (NOT publicly visible)
3. `access_mode="authenticated"` prevents public access
4. Admin reviews within 24-48 hours (target SLA)
5. **Auto-delete after 7 days if not reviewed**
6. User notified via email + in-app notification:
   - Day 5: "Your upload is still under review"
   - Day 7: "Your upload was not approved and has been removed"
7. If approved: prompt published
8. If rejected: explanation provided, image deleted

**When Upload Auto-Rejected (Clear Violation):**
1. User sees rejection reason immediately
2. Option to appeal decision
3. Image temporarily stored in Cloudinary (7 days)
4. `access_mode="authenticated"` prevents public access
5. User provides explanation
6. Admin reviews appeal within 24-48 hours
7. **Auto-delete after 7 days if appeal not reviewed**
8. Notification on decision (approved/rejected)
9. If approved: prompt published
10. If rejected: explanation provided, image deleted

**Review Dashboard:**
- User can view pending/appeal status
- Admin can review with image preview
- One-click approve/reject with notes
- Separate queues: "Pending Review" vs "Appeals"
- Days remaining counter for each item


### Automated Cleanup System

**Daily Heroku Scheduler Task:**
- **Command:** `python manage.py cleanup_stale_content`
- **Schedule:** Daily at 3:00 AM
- **Runtime:** ~1-3 minutes
- **Cost:** $0/month (uses spare Eco Dyno hours)

**What Gets Cleaned Up:**
1. Pending review content older than 7 days
2. Appeal content older than 7 days
3. Temporary files from failed uploads

**Cleanup Process:**
```python
# For each pending/appeal item older than 7 days:
1. Delete asset from Cloudinary
2. Update database status to 'EXPIRED'
3. Send user notification
4. Log to admin dashboard


### Comment Moderation

**AI Comment Moderation (OpenAI GPT-4):**
- **Auto-Approve:** Confidence >0.8, safe content
- **Auto-Remove:** Confidence >0.8, violates guidelines
- **Flag for Review:** Confidence 0.5-0.8 (admin decides)
- **Cost:** ~$1-5/month

**Detected Issues:**
- Harassment, bullying, personal attacks
- Passive aggression, condescending tone
- Unwanted flirting or romantic advances
- Contact info sharing (email, phone, social media)
- Spam or promotional content
- Off-topic discussions

**User Notifications:**
- Comment removed: "Your comment violated guidelines. Reason: [X]"
- Option to appeal (same process as content appeals)

**Admin Time:** ~30 minutes/day reviewing flagged comments

### Trust & Safety Features

**User Reputation System:**
- Good standing: Normal user
- Probation: Monitored activity, slower moderation approval
- Restricted: Limited features (upload ban, comment ban)
- Banned: No access

**Warning System:**
- Minor → Moderate → Severe → Final Warning → Ban
- Each warning requires user acknowledgement
- Visible in user's account (private)
- Admin can issue/lift warnings

**3-Strike System:**
- Strike 1: Warning + email
- Strike 2: Temporary restriction (upload ban 7 days)
- Strike 3: Permanent ban (with appeal option)

**Admin Tools:**
- Ban user (temporary/permanent)
- Restrict features (upload, comment, like)
- Review user's full history
- Bulk actions (remove all prompts from user)
- IP tracking for ban evasion


### 🔄 B2/OpenAI Vision Moderation (Phase L - Active)

**Status:** ✅ ACTIVE (January 2026)
**Architecture:** Step 1 NSFW Gate - blocks inappropriate content BEFORE user reaches details form

This system replaced Cloudinary moderation for B2-uploaded images, using OpenAI's GPT-4o-mini Vision model for content analysis.

**API Flow:**
```
1. User uploads image to B2 via presigned URL
2. Frontend calls POST /api/upload/b2/moderate/ with CDN URL
3. Backend fetches image, sends to OpenAI GPT-4o-mini Vision
4. Response determines outcome:
   - APPROVED (low severity) → Continue to Step 2
   - WARNING (high/medium severity) → Show warning banner, allow continue
   - BLOCKED (critical severity) → Delete from B2, show error
```

**Severity Levels:**

| Severity | Action | User Experience |
|----------|--------|-----------------|
| `critical` | BLOCKED | Upload deleted, error message shown |
| `high` | WARNING | Warning banner shown, user can continue |
| `medium` | WARNING | Warning banner shown, user can continue |
| `low` | APPROVED | No warning, continue normally |

**Key Files:**

| File | Purpose |
|------|---------|
| `prompts/services/cloudinary_moderation.py` | `moderate_b2_image()` - Core moderation logic |
| `prompts/views/api_views.py` | `b2_moderate_upload` endpoint |
| `prompts/templates/prompts/upload_step1.html` | Frontend moderation call + UI feedback |
| `prompts/constants.py` | `OPENAI_TIMEOUT = 30` constant |

**API Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload/b2/moderate/` | POST | Moderate uploaded B2 image |
| `/api/upload/b2/delete/` | POST | Delete B2 file (on rejection or cancel) |

**Security Features:**

1. **Domain Validation:** Only allows URLs from `ALLOWED_CDN_DOMAINS` list
2. **Fail-Closed Pattern:** Unknown/error states default to BLOCK (not allow)
3. **AI Refusal Detection:** `_is_ai_refusal()` detects when GPT refuses to analyze
4. **30-Second Timeout:** Prevents hanging on slow API responses
5. **CSRF Protection:** All POST endpoints require valid CSRF token

**AI Refusal Detection:**
```python
def _is_ai_refusal(analysis_text):
    """Detect if GPT-4o-mini refused to analyze the image."""
    refusal_phrases = [
        "i cannot", "i can't", "i'm unable", "i am unable",
        "cannot provide", "can't provide", "unable to provide",
        "cannot analyze", "can't analyze", "unable to analyze",
        # ... additional phrases
    ]
    return any(phrase in analysis_text.lower() for phrase in refusal_phrases)
```

**Frontend Integration:**
- Warning state persisted in `sessionStorage` key `b2_moderation_warning`
- Warning banner displays: "This image may contain sensitive content..."
- User can dismiss warning and proceed to Step 2
- Warning clears on successful form submission

**Error Handling:**
- Network errors → BLOCK (fail-closed)
- Timeout errors → BLOCK with "processing took too long" message
- AI refusal → BLOCK (treat as potentially inappropriate)
- Invalid domain → BLOCK with "invalid image URL" message

---

## 📤 Upload Flow Architecture

### ✅ Phase D Complete - Two-Step Upload Process (Pexels-Style)

**Step 1: File Upload (`/upload/`) ✅ IMPLEMENTED**
- Pexels-inspired drag-and-drop interface with visual feedback
- Direct browser → Cloudinary upload (client-side)
- Weekly limit display: "You have X uploads left" banner
- File validation (10MB images, 100MB videos, 20 sec video duration)
- Progress bar during upload with percentage
- Upload guidelines checklist displayed
- Redirects to Step 2 with Cloudinary ID + secure_url

**Step 2: Details Form (`/upload/details`) ✅ IMPLEMENTED**
- **AI-Generated (automatic, background):**
  - Title (GPT-4o-mini analyzing image)
  - Description/Excerpt (50-100 words, SEO-optimized)
  - 5 suggested tags from 209-tag system
  - Stored in session for later use
- **User-Provided (required):**
  - Prompt Content: Their actual AI prompt text
  - AI Generator: Dropdown selection (Midjourney, DALL-E, etc.)
  - Tags: Can edit AI suggestions or add custom (max 7)
- **Features:**
  - Early NSFW image warning (non-blocking, allows submit)
  - Tag autocomplete from 209 preset tags
  - Two-column layout: Image preview (60%) | Form (40%)
  - Navigation-away modal: "You have unsubmitted uploads..."
  - **Idle Detection System:** 45-minute timeout with modal
    - Modal at 40 minutes: "Still there? 5 minutes left"
    - Options: "Yes, extend 30 mins" | "Cancel upload"
    - Auto-cleanup: Deletes Cloudinary asset if abandoned
  - Session storage for upload timer tracking

**Step 3: Moderation & Publish (`/upload/submit`) ✅ IMPLEMENTED**
1. **Pre-submit validation:**
   - Profanity check on ALL text (title, content, description)
   - Blocks if violations found (high/critical severity)
   - Re-renders form with error (no redirect)
   - Preserves user input for correction
2. **Prompt creation:**
   - Uses CloudinaryResource (no re-upload)
   - AI-generated title + user's prompt content
   - Unique title handling (appends counter if duplicate)
3. **Full moderation via ModerationOrchestrator:**
   - Profanity (text) ← already checked pre-submit
   - OpenAI moderation (text)
   - OpenAI Vision (image/video)
4. **Status determination:**
   - `approved` → status=1 (Published) → detail page → "Published successfully!"
   - `pending` → status=0 (Draft) → detail page → "Being reviewed, usually within seconds"
   - `flagged` → status=0 (Draft) → detail page → "Pending review by team"
   - `rejected` → blocked → error message → no database save
5. **Cleanup:**
   - Clear upload timer session
   - Clear AI-generated session data
   - Cache clearing (list views)
6. **Redirect:** Always to detail page (handles draft visibility)

### Moderation Services Used

**Upload Flow Uses:**
1. **ContentGenerationService** - AI title/description/tags
2. **VisionModerationService** - Early image check (non-blocking warning)
3. **ProfanityFilter** - Pre-submit text check (blocking)
4. **ModerationOrchestrator** - Final comprehensive check:
   - Profanity (text)
   - OpenAI moderation (text)
   - OpenAI Vision (image/video)
   - Cloudinary moderation (image/video)

### Key Differences: /upload/ vs /create-prompt/

| Feature | /create-prompt/ | /upload/ |
|---------|----------------|----------|
| **Form Type** | Django Form | Manual POST |
| **File Upload** | Django FileField | Cloudinary direct upload |
| **AI Suggestions** | None | Title, description, 5 tags |
| **Early Warnings** | None | NSFW image warning (non-blocking) |
| **Profanity Check** | Form validation | Manual pre-submit check |
| **Moderation** | ModerationOrchestrator | Same (ModerationOrchestrator) |
| **Video Handling** | Form upload | CloudinaryResource |
| **Cloudinary Field** | UploadedFile object | CloudinaryResource object |

### CloudinaryResource Implementation
```python
from cloudinary import CloudinaryResource

# For images
prompt.featured_image = CloudinaryResource(
    public_id=cloudinary_id,
    resource_type='image'
)

# For videos
prompt.featured_video = CloudinaryResource(
    public_id=cloudinary_id,
    resource_type='video'
)
```

### 🎯 Phase D Achievements (October 2025)

**What Was Accomplished:**

1. **Two-Step Upload Flow (Complete)**
   - Pexels-inspired drag-and-drop UI
   - Client-side Cloudinary upload (no Django form submission)
   - AI-powered content generation (GPT-4o-mini)
   - Idle detection with 45-minute timeout
   - Navigation-away protection modal

2. **AI Content Generation Service**
   - Title generation from image analysis
   - SEO-optimized descriptions (50-100 words)
   - Intelligent tag suggestions (5 from 209 tags)
   - Video handling with frame extraction
   - Cost-efficient: ~$0.00255 per upload

3. **Upload Session Management**
   - Session-based upload tracking
   - Timer system with expiration
   - Automatic Cloudinary cleanup for abandoned uploads
   - Extension mechanism (30-minute extensions)
   - Cancel upload with asset deletion

4. **Enhanced Moderation Integration**
   - Early NSFW warnings (non-blocking)
   - Pre-submit profanity checks (blocking)
   - Full ModerationOrchestrator integration
   - Profanity error handling with form preservation
   - Clear user messaging based on moderation status

5. **User Experience Improvements**
   - Upload counter display ("X uploads left")
   - Real-time file validation
   - Tag autocomplete from 209 preset tags
   - Two-column responsive layout (60/40 split)
   - Progress indicators and loading states
   - Error recovery without data loss

**Technical Implementation:**

- **Views:** `upload_step1`, `upload_step2`, `upload_submit`, `cancel_upload`, `extend_upload_time`
- **Services:** ContentGenerationService (GPT-4o-mini), VisionModerationService (early check)
- **Session Management:** Upload timer tracking, AI data storage
- **JavaScript:** Idle detection, Cloudinary upload widget, navigation guards
- **Templates:** `upload_step1.html`, `upload_step2.html` with Bootstrap 5

**Key Technical Decisions:**

1. **CloudinaryResource vs File Upload:**
   - Chose CloudinaryResource to avoid double upload
   - Files stay in Cloudinary after initial upload
   - Saved bandwidth and processing time

2. **Session-Based AI Data:**
   - AI generates title/description once in Step 2
   - Stored in session for use in Step 3
   - Prevents duplicate AI API calls

3. **Non-Blocking NSFW Warnings:**
   - Early warning doesn't block submission
   - Allows user to proceed (will require manual review)
   - Better UX than hard rejection

4. **Idle Detection Timer:**
   - 45-minute session prevents abandoned files
   - Reduces wasted Cloudinary storage
   - User-friendly with extension option

**Current Timer Configuration (Testing vs Production):**

Testing Values (Currently Active):
- Initial idle timer: 1 minute 
- Warning countdown: 30 seconds
- Extension period: 30 minutes

Production Values (Final Implementation):
- Initial idle timer: 45 minutes (generous for thoughtful users)
- Warning countdown: 60 seconds (enough time to notice) 
- Extension period: 30 minutes (per "Yes" click)

**Future Enhancement:** Admin-configurable timer values through Django admin panel to allow real-time adjustment based on user feedback without code deployments.

**Cost Analysis:**
- AI Content Generation: ~$0.00255 per upload (GPT-4o-mini)
- Vision Moderation: Included in ModerationOrchestrator cost
- Cloudinary: Free tier (25GB, 25 credits/month)
- **Total per upload:** ~$0.01 (moderation + AI generation)

**What's Next (Phase E):**
- Integration testing across both flows (`/upload/` vs `/create-prompt/`)
- Performance optimization and caching
- Error handling edge cases
- User acceptance testing
- Documentation updates

---

## PHASE D.5: TRASH BIN + ORPHANED FILE MANAGEMENT ✅ COMPLETE

**Status:** Production-ready (October 12-13, 2025)
**Total Time:** 3 days (10-12 hours)
**Commits:** 10 (5d512bc → 48725a8)

### Day 1: Trash Bin UI ✅ (October 12, 2025)
**Duration:** 4-5 hours
**Commits:** 4 (5d512bc → ff4aa85)

Day 1 focused on user-facing trash bin functionality and UX polish. The primary challenge was creating a professional, responsive trash bin that matched the homepage's masonry layout while providing excellent user experience for restoration and deletion actions.

**Completed Features:**
- ✅ Database migration (soft delete fields: deleted_at, deleted_by, deletion_reason, original_status)
- ✅ Custom model managers (objects vs all_objects)
- ✅ Soft delete methods (soft_delete(), restore(), hard_delete())
- ✅ User trash bin page with masonry layout (4-column responsive grid)
- ✅ Restore functionality with smart redirects (referer-based routing)
- ✅ Undo button (returns to original page, prevents double-submit)
- ✅ Delete forever with confirmation modals
- ✅ Empty trash bulk action
- ✅ Retention rules (5 days free / 30 days premium)
- ✅ Expiring warnings (visual alerts for soon-to-expire items)
- ✅ Alert system polish (proper positioning, safe HTML rendering)
- ✅ Success messages with clickable links
- ✅ Loading states on buttons
- ✅ Video autoplay in trash grid
- ✅ Hover effects and animations

**Key Challenges Overcome:**
- Grid layout complexity (masonry vs Bootstrap conflicts)
- Alert positioning issues (staying above hero section)
- Redirect logic (Undo vs Restore from different pages)
- CC reverting manual code changes
- Card height stretching (h-100 removal)
- Duplicate alert submissions (onsubmit disable)

### Day 2: Backend Automation ✅ (October 12, 2025)
**Duration:** 4-5 hours
**Commits:** 3 (73878df, b6510bb, fb93ee0)

**Commit 5: Cleanup Management Command** (73878df)
- Django management command: `cleanup_deleted_prompts`
- Automatic deletion of expired prompts (5 days free, 30 days premium)
- Email summaries to admins
- Dry-run mode for testing
- Comprehensive error handling and logging
- ADMINS setting added to settings.py
- Files: cleanup_deleted_prompts.py (271 lines), README (248 lines)

**Commit 6: Orphaned File Detection** (b6510bb)
- Django management command: `detect_orphaned_files`
- Scans Cloudinary for files without database entries
- Date filtering (--days N or --all)
- CSV report generation
- API usage tracking and rate limit monitoring
- Found 14 orphaned files (8.5 MB) in initial scan
- Files: detect_orphaned_files.py (524 lines), README (462 lines)
- Cloudinary configuration fix applied

**Commit 7: Heroku Scheduler Setup** (fb93ee0)
- Comprehensive setup guide (758 lines)
- ADMIN_EMAIL environment variable configured
- Job configurations documented:
  - Daily cleanup at 03:00 UTC
  - Daily detection at 04:00 UTC (7 days)
  - Weekly deep scan at 05:00 UTC (90 days, optional)
- Cost analysis: $0/month (uses spare Eco dyno hours)

### Day 3: Missing Image Detection ✅ (October 13, 2025)
**Duration:** 2 hours
**Commits:** 3 (d730b19, 27aacf0, 48725a8)

**Commit 8: Documentation Update** (d730b19)
- Updated CLAUDE.md and PHASE_A_E_GUIDE.md with Phase D.5 completion
- Added comprehensive Day 2 summary for all 3 commits
- Added Phase E planning and specifications
- Reorganized future phases (F: Social, G: Premium, H: Admin, I: Performance)

**Commit 9: Missing Image Detection** (27aacf0)
- Enhanced `detect_orphaned_files` command with missing image detection
- Detects prompts where Cloudinary image/video doesn't exist
- Critical UX fix: prevents broken images on homepage feed
- New flags: `--missing-only`, `--orphans-only` for targeted scans
- Two-section CSV report (orphaned files + missing images)
- Enhanced email alerts highlighting ACTIVE prompts with broken images
- Found 3 broken prompts in initial scan (all ACTIVE, admin-owned)
- Files: detect_orphaned_files.py (+375 lines, -148 lines)

**Commit 10: Documentation Update** (48725a8)
- Updated README_detect_orphaned_files.md with missing image detection
- Renamed to "Cloudinary Asset Detection" to reflect dual functionality
- Added usage examples for new flags
- Documented two-section CSV format
- Added "What to Do with Missing Images" troubleshooting guide
- Prevention best practices and quick reference commands
- Files: README_detect_orphaned_files.md (+179 lines, -37 lines)

### Key Features Delivered:
- ✅ Soft delete with `deleted_at`, `deleted_by`, `deletion_reason`, `original_status`
- ✅ Retention periods: 5 days (free), 30 days (premium)
- ✅ Custom managers: `objects` (active), `all_objects` (includes deleted)
- ✅ Methods: `soft_delete()`, `restore()`, `hard_delete()`
- ✅ Cloudinary asset cleanup on hard delete
- ✅ Automated daily cleanup via Heroku Scheduler
- ✅ Orphaned file detection with CSV reports
- ✅ Missing image detection (prompts without valid Cloudinary files)
- ✅ Two-section reporting (orphaned files + missing images)
- ✅ ACTIVE vs DELETED prompt differentiation
- ✅ Email notifications to admins with action items
- ✅ API usage monitoring (2 calls per scan, 0.4% of limit)

### Files Created/Modified:
- `prompts/models.py` - Soft delete fields and methods
- `prompts/views.py` - Trash bin, restore, delete views
- `prompts/templates/prompts/trash_bin.html` - Trash UI
- `prompts/management/commands/cleanup_deleted_prompts.py` (271 lines)
- `prompts/management/commands/detect_orphaned_files.py` (524 lines → 899 lines with missing detection)
- `prompts/management/commands/README_cleanup_deleted_prompts.md` (248 lines)
- `prompts/management/commands/README_detect_orphaned_files.md` (462 lines → 641 lines)
- `HEROKU_SCHEDULER_SETUP.md` (758 lines)
- `CLAUDE.md` - Updated with Phase D.5 completion and Phase E planning
- `PHASE_A_E_GUIDE.md` - Updated with comprehensive implementation guide
- `PHASE_E_SPEC.md` - Created detailed Phase E specification (NEW)
- `prompts_manager/settings.py` - Added ADMINS configuration
- `.gitignore` - Added reports/*.csv
- `reports/` directory created

### Performance Metrics:
- Cleanup command: ~10-30 seconds execution
- Detection command (orphans): ~10-20 seconds (7 days), ~30-60 seconds (90 days)
- Detection command (missing images): ~10-30 seconds (checks 40-50 prompts)
- Initial missing image scan: Found 3 broken prompts (all ACTIVE, admin-owned)
- API usage: 2-4 calls per day
- Monthly cost: $0
- Dyno hours: ~0.48 hours/month (0.17% of allocation)

### Lessons Learned:
1. **Protect Critical Code:** Use HTML comments to prevent CC from reverting manual changes
2. **Test Incrementally:** Start with small scans (--days 1) before full scans
3. **Explicit Configuration:** Django management commands need explicit Cloudinary setup
4. **Documentation Is Key:** Comprehensive guides prevent future confusion
5. **Safe Defaults:** Always include --dry-run flags for destructive operations
6. **API Monitoring:** Track usage to prevent hitting rate limits
7. **Reverse Checks Matter:** Detecting both directions (orphans + missing) provides complete asset health
8. **Prioritize by Impact:** ACTIVE broken prompts need immediate action vs DELETED ones in trash
9. **Combined Reporting:** Single command for multiple checks reduces complexity and improves maintainability

### Next Steps:
- ✅ Configure Heroku Scheduler jobs (3 jobs: cleanup daily, orphan detection daily, deep scan weekly)
- Review CSV reports and fix 3 broken prompts found (all admin-owned, need image restoration)
- Monitor automated runs for 24-48 hours
- Review and delete confirmed orphaned files from Cloudinary (14 files, 8.5 MB)
- **Phase E: User Profiles & Social Foundation** (next phase, 10-12 hours estimated)

## Phase E: User Profiles & Social Foundation ✅

**Status:** 100% COMPLETE (October 25 - November 6, 2025)
**Completion Date:** November 6, 2025
**Production Verified:** All tasks complete and deployed
**Total Tests:** 71/71 passing (46 core features + 25 rate limiting)
**Agent Testing:** 9.35/10 average across all tasks
**Deployed:** Heroku v365+ (final commit: 8ea977e)
**Next Phase:** Phase G - Social Features & Activity Feeds
**Detailed Spec:** See `PHASE_E_SPEC.md`

**Final Task Completed (November 6, 2025):**
- Task 4: Email Preferences System - Fixed notify_updates behavioral inconsistency
- Investigation revealed documentation was outdated (actual state was 95% complete, not 75%)
- 15-minute fix to preserve critical platform notifications during unsubscribe
- Agent reviews: @django-expert 9.5/10, @code-review 9.2/10
- Git commit: 8ea977e79004ba13bad0e23d8bb3c3fae4abeb28

### Completion Summary

**Core Features (100% Complete):**
- Task 1: Advanced user profile enhancements ✅
- Task 2: Enhanced profile display system ✅
- Task 3: Comment field improvements ✅
- Task 4: Email preferences system with safety guarantees ✅

**Enhancements (100% Complete):**
- Enhancement 1: ARIA accessibility (WCAG 2.1 Level AA) ✅
- Enhancement 2: Rate limiting system (Dual implementation) ✅
  - **Note:** Initial implementation (Session 2) had 3 critical bugs
  - **All bugs fixed in Session 4** (October 26, 2025)
  - Comprehensive testing: 23/23 tests passing
  - Production deployed and functional

### Enhancement 2: Rate Limiting - Complete Implementation Details

**Initial Implementation (Session 2 - October 25, 2025):**
- Dual rate limiting system (custom + django-ratelimit)
- Deployed to Heroku v362
- Marked as "complete" but had critical bugs

**Bug Discovery & Fixes (Session 4 - October 26, 2025):**

**3 Critical Bugs Found:**
1. ❌ Missing `ratelimited()` error handler view
   - Settings referenced non-existent function
   - Caused AttributeError when rate limit hit

2. ❌ Rate limiting decorator not triggering
   - Applied to individual handler functions instead of router
   - Users could exceed rate limits without detection

3. ❌ Users saw generic 403 instead of branded 429 page
   - django-ratelimit 4.x doesn't respect RATELIMIT_VIEW setting
   - Exception converted to HTTP 403 instead of 429

**Solutions Implemented:**
1. ✅ Created `ratelimited()` view function (prompts/views.py line 2105)
   - Renders branded 429.html template
   - Uses TemplateResponse for testability
   - Provides user-friendly rate limit message

2. ✅ Created RatelimitMiddleware (prompts/middleware.py)
   - Intercepts Ratelimited exceptions from django-ratelimit 4.x
   - Calls custom ratelimited() view function
   - Graceful fallback if custom view missing
   - Added to MIDDLEWARE in settings.py (line 101)

3. ✅ Fixed decorator placement
   - Moved @ratelimit to unsubscribe_view() router function
   - Now correctly enforces 5 requests/hour per IP
   - All paths through router protected

**New Files Created:**
- `prompts/middleware.py` (67 lines)
  - RatelimitMiddleware class
  - InfrastructureDebugMiddleware class (for debugging)

- `templates/429.html` (64 lines)
  - Branded PromptFinder error page
  - Mobile responsive (Bootstrap 5)
  - WCAG 2.1 Level AA accessible
  - Shows "Please try again in: 1 hour"
  - Support contact information

- `prompts/tests/test_rate_limiting.py` (23 tests, 413 lines)
  - Comprehensive test suite covering all scenarios
  - Tests for rate limit enforcement
  - Tests for custom error handler
  - Tests for different IP addresses
  - Tests for template rendering
  - 100% passing

**Testing Results:**
- ✅ 23/23 automated tests passing (100%)
- ✅ Manual browser test: Shows branded 429 after 5 requests
- ✅ curl test: Blocks request 6 with HTTP 429 status
- ✅ Different IPs tracked independently
- ✅ Rate limiting now actually enforces 5/hour limit per IP
- ✅ Branded error page displays correctly

**Agent Testing (Session 4):**
- @django-pro: 9.5/10 (Excellent Django patterns, proper signal handling)
- @security: 9.5/10 (No vulnerabilities, proper error handling, IP protection)
- @code-quality: 9.5/10 (Professional structure, comprehensive tests, clear code)
- **Average: 9.5/10** (Production ready)

**Production Status:**
- ✅ All bugs fixed and tested
- ✅ Committed to repository
- ✅ Deployed to Heroku
- ✅ Fully functional in production
- ⏳ Production verification pending (next session task)

### Development Sessions - Phase E

**Session 1** (Chat: bc9f730a-318e-47c7-a715-46e6dda957b7)
- Fixed EmailPreferences admin field mismatch
- Completed Phase E Task 4
- Deployed to production

**Session 2** (Chat: f5debf9d-4733-459d-8b6a-8b8803219d84)
- Implemented Enhancement 1 (ARIA accessibility)
- Implemented Enhancement 2 (rate limiting - initial version)
- Deployed to Heroku v362
- Created handoff document stating "Phase E 100% complete"
- **Note:** Rate limiting had 3 critical bugs (discovered in Session 4)

**Session 3** (Chat: 4b18a39c-006c-4695-a5d8-a5194013f7fe)
- Used custom boilerplate continuation system (FIRST time)
- CC completed Task 1 (DRY refactoring) successfully
- Attempted Task 1.5 (custom 429 handler) but CC didn't fully implement
- Session ended mid-investigation

**Session 4** (Chat: 01933854-c51a-7485-958f-d9b17b933bfa)
- **Fixed all 3 critical rate limiting bugs**
- Created RatelimitMiddleware solution for django-ratelimit 4.x compatibility
- Implemented custom ratelimited() error handler view
- Created branded 429.html template
- Built comprehensive 23-test suite (100% passing)
- Completed agent testing (9.5/10 average)
- **Committed and deployed to production**
- Phase E NOW truly 100% complete ✅

**Session 5** (Chat: 01933854-c51a-7485-958f-d9b17b933bfa)
- Updated documentation (CLAUDE.md + created PROJECT_FILE_STRUCTURE.md)
- **Verified rate limiting in production (100% functional)**
- Browser test: Branded 429 page displays correctly after 5 requests ✅
- Created production verification script (`scripts/verify_rate_limiting_production.sh`)
- Added 2 security tests to test_rate_limiting.py (25 tests total, 100% passing)
- Investigated curl HEAD vs GET method behavior (HEAD bypasses rate limit by design)
- **Confirmed Phase E 100% complete and production-ready**

### Production Verification (Session 5 - October 27, 2025)

**Browser Test:** ✅ PASSED
- Branded 429 page displays after 5 requests
- User-friendly messaging: "Too Many Requests"
- Shows "Please try again in: 1 hour"
- Mobile responsive and accessible

**Production Logs:** ✅ VERIFIED
- Rate limiting triggers correctly
- Middleware intercepts Ratelimited exceptions
- HTTP 429 status returned properly

**Security Status:** ✅ PRODUCTION READY
- 5 requests per IP per hour enforced
- Token enumeration attacks prevented
- Email enumeration blocked
- Zero vulnerabilities detected

**Production URL:** https://mj-project-4-68750ca94690.herokuapp.com/

**Technical Investigation:**
- Discovered rate limiting decorator IS on router function (line 2364)
- curl -I sends HEAD requests (not GET) which bypass rate limiting
- Rate limiting decorator specifies `method='GET'`
- Browser uses GET → rate limiting works perfectly
- This is expected behavior (HEAD requests should be lightweight)

### Overall Project Statistics (as of October 26, 2025)

**Code Coverage:**
- Total Tests: 71 passing
  - Phase E Core: 46 tests ✅
  - Rate Limiting: 25 tests ✅ (added 2 security tests in Session 5)
- Test Success Rate: 100%
- Agent Testing Average: 9.5/10

**Files Modified in Phase E:**
- Models: prompts/models.py (EmailPreferences, UserProfile, PromptReport)
- Views: prompts/views.py (email preferences + rate limiting)
- Middleware: prompts/middleware.py (NEW - Rate limiting)
- Templates: templates/429.html (NEW - Rate limit error page)
- Admin: prompts/admin.py (EmailPreferences config)
- Forms: prompts/forms.py (Email preferences form)
- Tests: prompts/tests/test_email_preferences_safety.py, test_rate_limiting.py
- URLs: prompts/urls.py (Added rate limit test endpoint)
- Settings: prompts_manager/settings.py (Added middleware)

**Testing Infrastructure Created (Session 5):**
- Scripts: scripts/verify_rate_limiting_production.sh (88 lines)
- Documentation: PROJECT_FILE_STRUCTURE.md (641 lines)
- Tests: Added 2 security tests to test_rate_limiting.py

**Production Deployment:**
- Heroku App: mj-project-4 (EU region)
- Production URL: https://mj-project-4-68750ca94690.herokuapp.com/
- Latest Version: v365+ (October 27, 2025)
- Status: All features deployed and verified ✅
- Rate Limiting: Functional and securing endpoints ✅
- Security: Zero vulnerabilities (verified in production)

###✅ Completed Tasks Summary

**Task 1: UserProfile Model & Admin** (Complete ✅)
- UserProfile model with bio, avatar (CloudinaryField), social URLs
- Auto-creation signal for new users
- Admin interface with search, filters, stats
- Profile page displays prompts, stats, member since date

**Task 2: Profile Edit Form & UX Enhancements** (Complete ✅)
- Avatar upload/display (fixed CloudinaryField template check)
- Bio editing (500 char limit with live counter)
- Smart URL field UX (accepts @username, username, or full URLs)
- Security hardening (validation before concatenation)
- Social media icons on profile page

**Task 3: Report Feature + Profile Navigation** (100% Complete ✅)
- PromptReport model (5 reasons, 4 statuses, UniqueConstraint)
- Admin interface (list, detail, 3 bulk actions)
- Report button + modal on prompt detail pages
- Email notifications to admins
- Duplicate/self-reporting prevention
- Profile navigation links (View Profile + Edit Profile)
- Character counter with color coding (0/1000)
- 🐛 **Bug Fixed (October 21, 2025):** Comment field now saves correctly
  - **Issue:** Comment field saved as empty string despite user input
  - **Root Cause:** AJAX timing - FormData captured textarea before browser finalized value
  - **Solution:** Explicitly set FormData value: `formData.set('comment', commentTextarea.value)`
  - **Testing:** 5/5 critical database tests passed (20 browser tests deferred to user)
  - **Agent Consultations:** @django-expert (diagnosis), @code-reviewer (security), @test-automator (scenarios), @ui-ux-designer (UX verification)
  - **Documentation:** Complete bug report at `docs/bug_reports/phase_e_task3_comment_field_fix.md`

**Files Modified:** 8 files, ~672 lines of code added
**Migrations:** 0029_promptreport.py (applied)
**Testing:** 5/5 critical tests passed
**Fix Time:** 60 minutes (diagnosis + implementation + testing + documentation)

**Task 4: Email Preferences Dashboard** (100% Complete ✅ - October 25, 2025)
- EmailPreferences model with 8 notification toggles (Commits 1 & 1.5)
- Auto-creation signal (ensure_email_preferences_exist)
- Admin interface with all 8 fields, filters, organized fieldsets
- Settings page at /settings/notifications/ with toggle switches
- Save functionality with success messaging
- Email helper utilities (should_send_email, get_unsubscribe_url)
- One-click unsubscribe handler at /unsubscribe/<token>/
- Unsubscribe confirmation template (mobile-responsive)
- Data protection system (backup/restore commands, 8/8 tests passing)
- **Comprehensive Testing:** 46/46 tests passed (100% pass rate)
  - Security: Zero vulnerabilities found
  - Performance: <500ms load times
  - Code Quality: 9.2/10
  - Agent Reviews: @django-expert @security @test @code-review @database
- **UX Improvements:**
  - Removed misleading "Unsubscribe All" button
  - Removed confusing "Back" button
  - Centered Save Preferences button
  - Fixed duplicate success message bug
  - Fixed admin field mismatch (all 8 fields now visible)
- **Files Created:**
  - prompts/email_utils.py (helper functions)
  - prompts/templates/prompts/unsubscribe.html (confirmation page)
- **Files Modified:**
  - prompts/models.py (EmailPreferences model)
  - prompts/admin.py (admin interface)
  - prompts/views.py (settings view, unsubscribe handler)
  - prompts/forms.py (EmailPreferencesForm)
  - prompts/urls.py (URL routing)
  - prompts/signals.py (auto-creation signal)
  - prompts/templates/prompts/settings_notifications.html (settings page)
- **Migration:** 0030_emailpreferences.py
- **Documentation:** 1,167+ lines across multiple files
- **Implementation Time:** ~4 hours across Commits 1-3
- **Production Ready:** Approved for deployment after comprehensive testing

**All 8 Notification Types Supported:**
1. Comments on prompts (notify_comments)
2. Replies to comments (notify_replies)
3. New followers (notify_follows)
4. Likes on prompts (notify_likes)
5. Mentions @username (notify_mentions)
6. Weekly activity summary (notify_weekly_digest)
7. Product updates (notify_updates)
8. Marketing emails (notify_marketing)

### ✅ Completed: Profile Header Refinements

**Implementation Date:** October 20, 2025

**Features Completed:**
1. **Profile Header Layout** (6 fixes)
   - Pill-shaped tabs (border-radius: 40px)
   - Vertical dividers between stats
   - Larger font sizes (stats: 32px, labels: 16px)
   - Edit Profile button added and styled
   - Tabs and filters positioned on same row
   - Profile page rendering (Cloudinary config fixed)

2. **Overflow Arrow Structural Fix**
   - Created wrapper shell (`.profile-tabs-wrapper`) to isolate arrows
   - Moved arrows outside scrolling container (were inside, causing scroll)
   - Arrows now siblings of `.profile-tabs-container`, not children
   - Result: Arrows stay fixed, only tabs scroll

3. **Dynamic Arrow Visibility System**
   - `checkOverflow()` - Detects horizontal overflow
   - `updateArrowVisibility()` - Shows/hides arrows based on scroll position
   - Event listeners: DOMContentLoaded, resize, scroll
   - Arrow click handlers with 300ms timeout updates
   - Keyboard navigation: ArrowLeft, ArrowRight, Home, End
   - Debounced updates: 100ms resize, 50ms scroll

4. **Visual Refinements**
   - Removed drop shadows from arrow buttons (cleaner design)
   - Fixed width overflow on >990px screens
   - Added `min-width: 0` and `flex-shrink: 1` to wrapper

**Files Modified:**
- `prompts/templates/prompts/user_profile.html` (~205 lines total)
  - HTML structure: ~25 lines
  - CSS changes: ~40 lines
  - JavaScript: ~140 lines

**Agent Usage:**
- **Total Agents:** 5 agents across 2 tasks
- **Task 1 (Visibility):** @javascript-pro, @code-reviewer, @test-automator
- **Task 2 (Refinements):** @code-reviewer, @ui-ux-designer

**Bugs Caught by Agents:**
- 2 critical bugs (null checks, requestAnimationFrame)
- 4 memory leaks (event listener cleanup issues)
- 2 performance issues (debounce cleanup)
- 22 edge cases identified (zoom, RTL, touch, keyboard, etc.)

**Testing:**
- 8 original test scenarios ✅
- 22 additional edge cases ✅
- All viewport widths tested (1400px → 600px) ✅

**Technical Debt Acknowledged:**
1. No event listener cleanup (IIFE pattern complexity)
2. No RAF optimization (setTimeout adequate for use case)
3. Incomplete null checks in some paths (mitigated by early validation)

**Documentation:**
- Main Report: `PHASE_E_IMPLEMENTATION_REPORT.md` (root)
- Visibility Spec: `docs/specifications/phase_e_arrow_visibility_spec.md`
- Refinements Spec: `docs/specifications/phase_e_arrow_refinements_spec.md`
- Complete Report Copy: `docs/implementation_reports/phase_e_complete_report.md`

---

### 🔜 Remaining Phase E Tasks

---

### ⚠️ PHASE E TASK 4 - INCOMPLETE (CRITICAL)

**Status:** 75% Complete - IN PROGRESS
**Priority:** HIGH - Must complete before Phase E can be marked as done
**Created:** November 4, 2025

**Why This Section Exists:**
During Phase E implementation, we strategically started Part 1 (User Profiles) before
completing Task 4 (Email Preferences). This section ensures Task 4 is NOT forgotten.

**What's Complete (75%):**
- ✅ EmailPreferences model
- ✅ EmailPreferencesAdmin
- ✅ email_preferences() view
- ✅ EmailPreferencesForm
- ✅ settings_notifications.html template
- ✅ Signal for auto-creation
- ✅ Backup/restore commands
- ✅ Safety tests

**What's INCOMPLETE (25%):**
- ❌ Field mismatch issue (Commit 2)
- ❌ Email helper functions (Commit 3)
- ❌ should_send_notification() function
- ❌ Unsubscribe system
- ❌ Email template footer updates

**FULL DETAILS:** See `PHASE_E_TASK4_INCOMPLETE_REMINDER.md` (15 KB comprehensive guide)

**Complete This Before:**
- Starting Phase G
- Marking Phase E as 100% complete
- Implementing any new notification features

---

Per `PHASE_E_SPEC.md`:

### Overview
Build the foundation for social features by implementing user profiles, enhanced prompt details, and email preferences. This phase enables users to discover content creators, follow interesting users, and control their notification preferences.

### Why Phase E (vs. Premium System)?
- **Foundation for all future social features** - Enables follow system and feeds in Phase F
- **Addresses user experience gaps** - No way to see user's other prompts currently
- **Email preferences needed** - Before increasing notification volume
- **Builds community engagement** - Before monetization
- **Natural progression** - From content management (D.5) → social features (E) → monetization (G)

### Part 1: Public User Profile Pages (4-5 hours)

**Features:**
- Public profile page at `/users/<username>/`
- Display user's public prompts in grid/masonry layout
- User statistics (total prompts, likes received, member since, follower/following counts)
- Basic profile information (username, display name, bio, avatar, location, social links)
- Follow/unfollow button (foundation for Phase F)
- Responsive design (mobile-optimized)

**Implementation:**
- UserProfile model (one-to-one with User)
- Profile view and template
- URL routing for usernames
- Query optimization (prefetch prompts, likes)

### Part 2: Enhanced Prompt Detail Page (2-3 hours)

**Features:**
- "View Profile" link next to author name
- "Report Prompt" button with modal
  - Report reasons: inappropriate, spam, copyright, other
  - Optional comment field
  - Email notification to admins
  - Thank you confirmation
- "More from this user" section (3-6 prompts by same author)
- Author info card (avatar, username, follower count)

**Implementation:**
- Update `prompt_detail.html` template
- Report modal HTML
- PromptReport model (prompt, reporter, reason, comment, status)
- Report view and form handling
- Admin email notification
- Related prompts query

### Part 3: Email Preferences Dashboard (3-4 hours)

**Features:**
- User settings page at `/settings/notifications/`
- Email preference toggles:
  - New comments on my prompts
  - Replies to my comments
  - New followers
  - Likes on my prompts
  - Mentions (@username)
  - Weekly digest
  - Product updates/announcements
  - Marketing emails
- "Unsubscribe from all" option
- Email verification for changes
- Success/error messaging

**Implementation:**
- EmailPreferences model (one-to-one with User)
- Settings view and form
- Update notification logic to respect preferences
- Unsubscribe token system (for email links)
- Default preferences (all enabled except marketing)

### Database Models:

**UserProfile:**
```python
- user (OneToOne with User)
- bio (TextField, max 500 chars)
- avatar (CloudinaryField)
- location, website, social_twitter, social_instagram
- created_at, updated_at
```

**PromptReport:**
```python
- prompt, reported_by, reason, comment
- status (pending/reviewed/dismissed)
- reviewed_by, created_at, reviewed_at
```

**EmailPreferences:**
```python
- user (OneToOne)
- notify_* fields (BooleanField)
- unsubscribe_token (CharField, unique)
```

### Success Criteria:
- ✅ Users can view any public user profile
- ✅ Profiles display user's prompts and stats
- ✅ Prompt detail page has "View Profile" link
- ✅ Report button works with admin notification
- ✅ Email preferences page functional
- ✅ All notification emails respect preferences
- ✅ Unsubscribe links work correctly
- ✅ Mobile-responsive design
- ✅ No N+1 query issues (optimized)

### Leads to Phase F:
- Follow system implementation (builds on follow button)
- Personalized feeds (needs profiles + follows)
- Notifications (uses email preferences)
- User discovery (profiles enable browsing creators)

---

## Phase F: Advanced Admin Tools & UI Refinements

**Status:** ✅ COMPLETE (October 31, 2025)
**Session:** https://claude.ai/chat/cda5549b-7bd0-4d9d-a456-7a0a4f3ad177
**Completion Notes:** All objectives achieved, code committed, tested, and verified.

### Phase F Day 1: Bulk Actions System (Oct 31, 2025) ✅ COMPLETE

**✅ PHASE F DAY 1 SUCCESSFULLY COMPLETED**

All work completed, tested by user, and committed to repository (2 commits).

#### Session Objectives:
1. Implement bulk actions system for admin debugging pages
2. Enhance UI consistency across admin tools
3. Fix URL routing issues discovered during implementation
4. Update CC Communication Protocol with agent usage guidelines

#### Implementation Details:

**1. CC Communication Protocol Enhancement** ✅
- Added "🤖 MANDATORY WSHOBSON/AGENTS USAGE" section to docs/CC_COMMUNICATION_PROTOCOL.md
- Documented 85 available agents across 63 plugins
- Established agent reporting requirements and format
- Added Django-specific agent usage guidelines
- Formalized quality assurance through agent usage

**2. Bulk Actions Implementation (Debug Page)** ✅
- Three bulk action buttons: Delete Selected, Set to Published, Set to Draft
- Confirmation modals for all three actions (Bootstrap modals)
- JavaScript for checkbox selection and form population
- Enhanced checkbox visibility (darker borders via CSS)
- Responsive 3-button layout
- **Status:** Debug page fully functional with all features working

**3. URL Routing Fixes** ✅
- Fixed 19 incorrect URL references across 4 template/view files
- Created bulk_set_draft_no_media view function
- Updated nav_sidebar.html, trash_dashboard.html URL references
- Fixed 16 redirect statements in prompts/views.py
- Cleaned up duplicate patterns in prompts/urls.py

**4. Django Admin Message Rendering** ✅
- Created templates/admin/base_site.html override
- Conditional |safe filter for success messages with HTML links
- Maintains security while allowing clickable "View Trash" links

#### Issues Identified and RESOLVED:

**✅ Issue #1: Media Issues Page Shows Deleted Items (RESOLVED)**
- **Problem:** media_issues_dashboard view missing `deleted_at__isnull=True` filter
- **Resolution:** Added filter to prompts/views.py (commit 4c926fe)
- **Verification:** User tested and confirmed working
- **Commit:** `fix(admin): Add deleted filter to media_issues_dashboard query`

**✅ Issue #2: Items Don't Disappear After Delete (RESOLVED)**
- **Problem:** After bulk delete, items remained visible in table
- **Resolution:** Fixed by same filter addition as Issue #1
- **Verification:** User tested and confirmed working
- **Status:** No longer reproducible after fix

**✅ Issue #3: Success Message HTML (VERIFIED)**
- **Problem:** templates/admin/base_site.html created but not user-tested
- **Resolution:** User verified all clickable "View Trash" links work correctly
- **Verification:** Success messages render properly with HTML
- **Status:** Fully functional

**✅ Issue #4: Console Errors (DOCUMENTED)**
- Favicon 404 error (typo: favicon.ico1) - cosmetic only
- Permissions Policy warning - no functional impact
- **Status:** Cosmetic only, deferred for Phase F Day 2 (low priority)

#### Files Modified (9 files, 2 commits):

**Commit 1: `feat(admin): Add bulk publish action and enhance CC protocol` (4a7aa34)**
1. prompts/views.py - Added bulk_set_draft_no_media, fixed 16 redirects
2. prompts_manager/urls.py - Added new URL pattern
3. prompts/urls.py - Removed duplicates, added documentation
4. prompts/templates/prompts/debug_no_media.html - 3rd button, modals, JavaScript
5. prompts/templates/prompts/media_issues.html - 3rd button, modals, JavaScript
6. templates/admin/base_site.html - NEW: Django admin override
7. templates/admin/nav_sidebar.html - Fixed 2 URL references
8. templates/admin/trash_dashboard.html - Fixed 1 URL reference
9. docs/CC_COMMUNICATION_PROTOCOL.md - NEW SECTION: Agent usage (~200 lines)

**Commit 2: `fix(admin): Add deleted filter to media_issues_dashboard query` (4c926fe)**
- prompts/views.py - Added `deleted_at__isnull=True` filter to media_issues_dashboard query
- Resolves Issues #1 and #2 (deleted items showing in dashboard)

#### Testing Status (USER VERIFIED):

**✅ All Features Verified Working:**
- Debug page loads and displays correctly
- All 3 bulk action buttons functional (Delete, Publish, Draft)
- Confirmation modals open/close correctly
- Deleted prompts properly disappear from view (after fix)
- Media issues page correctly excludes deleted items (after fix)
- Items automatically disappear after delete (no refresh needed)
- Success message HTML rendering with clickable "View Trash" links
- URL routing completely fixed (19 references corrected)
- Checkboxes more visible with darker borders
- Django admin override (base_site.html) functioning as expected

#### Completion Summary:

**All Objectives Achieved (4/4):**
1. ✅ Implement bulk actions system for admin debugging pages - COMPLETE
2. ✅ Enhance UI consistency across admin tools - COMPLETE
3. ✅ Fix URL routing issues discovered during implementation - COMPLETE (19 references fixed)
4. ✅ Update CC Communication Protocol with agent usage guidelines - COMPLETE

**Quality Metrics:**
- Code coverage: All critical paths tested
- User verification: All features tested by user and confirmed working
- Bug resolution: 4 issues identified and resolved (2 in code, 2 deferred as cosmetic)
- Commits: 2 successful pushes to repository

#### Session Statistics (Final):
- **Duration:** Extended session with multiple CC iterations and user testing
- **Session ID:** cda5549b-7bd0-4d9d-a456-7a0a4f3ad177
- **Files Modified:** 9 files across 2 commits
- **Lines Added:** Approximately 300+ lines (bulk actions, modals, filters, documentation)
- **Bugs Found:** 4 (all resolved)
- **Commits:** 2 (both successful)
- **Agent Consultations:** 2 (@code-reviewer, @django-pro)
- **User Testing:** All features verified working in production

**Production Status:** ✅ Ready for next phase

---

### Phase F Day 2: Admin Backend Cosmetic Fixes (Nov 4, 2025) ✅ COMPLETE

**Session Objectives:**
1. Fix favicon 404 error in admin console
2. Fix Permissions Policy warning in browser
3. Preserve all Phase F Day 1 functionality

**Implementation Details:**

**1. Favicon Fix** ✅
- Added inline SVG favicon to `templates/admin/base_site.html`
- Blue "P" branded icon for PromptFinder
- Zero HTTP requests (embedded data URI, ~200 bytes)
- Result: Favicon 404 error completely resolved

**2. Permissions Policy Configuration** ✅
- Added SECURE_PERMISSIONS_POLICY to `prompts_manager/settings.py`
- Restricts 12 browser features (camera, microphone, geolocation, USB, etc.)
- Improves security posture from 8/10 to 9/10
- Follows principle of least privilege
- Result: Security enhanced with industry-standard restrictions

**3. Agent Testing** ✅
- @django-pro: 9.5/10 - APPROVED FOR PRODUCTION
- @code-reviewer: 9.0/10 - APPROVED FOR PRODUCTION
- Average: 9.25/10
- Status: Production ready, deploy immediately

**Files Modified:**
- `templates/admin/base_site.html` (favicon implementation)
- `prompts_manager/settings.py` (Permissions Policy, lines 54-69)

**Commits:**
- Commit 9319c30: `fix(admin): Add favicon and Permissions-Policy header`
- Commit c8bde05: `docs: Add Phase F Day 2 completion report`

**Documentation:**
- `PHASE_F_DAY2_COMPLETION_REPORT.md` (470 lines, comprehensive)

---

### Phase F Day 2.5: Configuration Verification (Nov 4, 2025) ✅ VERIFIED

**Objective:** Investigate persistent unload violation warning in console

**Investigation Results:**
- Verified SECURE_PERMISSIONS_POLICY configuration is correct
- Confirmed `'unload'` restriction was never added to our settings (correct)
- Determined issue source is external (browser defaults, Django core, or Heroku)
- Configuration optimized for Django admin compatibility
- Agent testing: 9.25/10 average (configuration optimal)

**Agent Reviews:**
- @django-pro: 9.5/10 - Configuration correct, Django admin fully compatible
- @security-auditor: 9.0/10 - Security maintained, zero vulnerabilities
- Consensus: No changes needed, current config optimal

**Key Findings:**
- Omitting `'unload'` from Permissions-Policy is correct approach
- Allows Django admin JavaScript (RelatedObjectLookups.js) to function
- Browser default behavior allows unload events when not explicitly blocked
- Adding `'unload': []` would break Django admin functionality

**Commit:**
- Commit 594cede: `docs: Phase F Day 2.5 verification complete`

**Documentation:**
- `PHASE_F_DAY2.5_COMPLETION_REPORT.md` (607 lines, comprehensive)

---

### ⚠️ Known Issue: Permissions Policy Unload Violation

**Status:** DOCUMENTED - DEFERRED (Low Priority)
**Discovered:** Phase F Day 2/2.5 (November 4, 2025)
**Investigation:** Thoroughly investigated, root cause identified

**Issue:**
Console warning appears in Django admin backend:
```
[Violation] Permissions policy violation: unload is not allowed in this document.
(anonymous) @ RelatedObjectLookups.js:215
```

**Impact Assessment:**
- ✅ **Cosmetic only** - zero functional impact
- ✅ **Django admin fully functional** - all features working
- ✅ **No user-facing issues** - invisible to end users
- ✅ **Only visible to developers** - appears in browser console only

**Root Cause Analysis:**
- Not caused by our SECURE_PERMISSIONS_POLICY configuration
- Source is external: browser defaults, Django core JavaScript, or Heroku infrastructure
- Django's `RelatedObjectLookups.js` (line 215) uses deprecated `unload` event for cleanup
- Our configuration correctly omits `'unload'` to allow admin functionality
- Cannot fix without modifying Django core or waiting for Django update

**Technical Details:**
- Django admin requires unload events for:
  - Unsaved changes warning ("You have unsaved changes")
  - Popup window cleanup (ForeignKey selection dialogs)
  - Session management on page navigation
- Blocking unload events would break critical admin features
- Current configuration (omitting `'unload'`) is optimal per @django-pro and @security-auditor

**Investigation History:**
- Phase F Day 2: Identified during favicon/Permissions-Policy implementation
- Phase F Day 2.5: Comprehensive verification by 2 agents
- Confirmed configuration correct, issue cannot be resolved at application level

**Resolution:**
- ✅ Accepted as known cosmetic issue
- ✅ Documented for future reference
- ✅ Deferred to Q1 2026 or Django update
- ✅ Not worth investigation time given zero functional impact

**Trigger for Re-investigation:**
- Django releases update fixing RelatedObjectLookups.js
- Issue causes actual functionality problems (currently does not)
- Part of larger Django admin optimization effort
- User reports admin functionality degradation (none expected)

**Related Documentation:**
- Full verification report: `PHASE_F_DAY2.5_COMPLETION_REPORT.md`
- Security audit: Conducted by @security-auditor (9.0/10)
- Django compatibility audit: Conducted by @django-pro (9.5/10)
- Configuration reference: `prompts_manager/settings.py` lines 54-69

**Decision:** Issue is cosmetic, well-understood, and not actionable at this time.

---

## UI Redesign Session - November 13, 2025

**Status:** ✅ COMPLETE - CSS Audit Completed
**Session:** https://claude.ai/code/session_011CUvvuycDFFvqCcfY962oS
**Branch:** `claude/ui-redesign-011CUvvuycDFFvqCcfY962oS`
**Duration:** Extended session
**Total Commits:** 11

### Session Objectives

1. Fix Load More button JavaScript error
2. Refine layout for ultrawide displays (1600px max-width)
3. Update padding and spacing for masonry grid
4. Conduct comprehensive CSS audit across entire application

### Work Completed ✅

#### 1. Load More Button - Critical Fix

**Problem:** "Failed to load more prompts. Please try again." error modal when clicking Load More button

**Root Cause:** `ReferenceError: dragModeEnabled is not defined` at line 1301

**Solution:**
```javascript
// Before (causing error)
if (dragModeEnabled) {

// After (fixed)
if (typeof dragModeEnabled !== 'undefined' && dragModeEnabled) {
```

**Files Modified:**
- `prompts/templates/prompts/prompt_list.html` (line 1301)

**Result:** Load More button works perfectly with no console errors

---

#### 2. Layout Refinements for Ultrawide Displays

**Container Override (≥1700px screens only):**
```css
@media (min-width: 1700px) {
    .container {
        max-width: 1600px !important;
    }
}
```

**Masonry Container Updates:**
- `padding: 40px 0` (was `20px 40px` / `20px 16px`)
- `max-width: 1600px` (was `100%`)
- `margin: 0 auto` (centers content)
- Removed all mobile responsive overrides for consistency

**Files Updated:**
1. `static/css/style.css` (lines 350-356)
2. `prompts/templates/prompts/prompt_list.html` (inline CSS updated, mobile overrides removed)
3. `prompts/templates/prompts/trash_bin.html` (inline style attribute)
4. `prompts/templates/prompts/partials/_masonry_grid.html` (inline style attribute)

**Additional Layout Fixes:**
- `.main-bg`: Added flexbox centering (`display: flex; flex-direction: column; align-items: center`)
- `.pexels-navbar`: Added `width: 100%`
- `.media-filter-container`: Added `width: 100%`

**Result:** Consistent, centered layout on all screen sizes with proper vertical spacing

---

#### 3. Comprehensive CSS Audit 🔍

**Scope:** 20+ HTML templates, style.css, base.html
**Agent Used:** @general-purpose
**Findings:** 10 issues across 4 severity levels

##### 🔴 Critical Issues (2)

1. **`.masonry-container` - Duplicate Definitions**
   - Defined in both `style.css` and `prompt_list.html` inline styles
   - Template overrides stylesheet, causing inconsistent behavior
   - **Recommendation:** Remove from template, keep only in stylesheet

2. **MASSIVE Inline `<style>` Blocks**
   - `base.html`: ~2000 lines (navbar, dropdowns, modals)
   - `prompt_list.html`: ~500 lines (masonry, filters, video cards)
   - 5+ other templates with significant inline CSS
   - **Impact:** Performance hit, not cached, maintenance nightmare
   - **Recommendation:** Extract to external CSS files

##### 🟠 High Priority Issues (3)

3. **Hardcoded Colors vs CSS Variables**
   - 30+ hardcoded color instances (e.g., `#fff`, `#6b7280`, `#333`)
   - Only 40% adoption of 92 defined CSS variables
   - **Recommendation:** Systematically replace all hardcoded colors

4. **`.media-filter-container` - Fragmented Media Queries**
   - Multiple breakpoints scattered across file
   - Hardcoded colors instead of variables
   - **Recommendation:** Consolidate and use CSS variables

5. **`.pexels-navbar` Only in Inline Styles**
   - Critical component (~2000 lines) not cached
   - Performance impact on every page load
   - **Recommendation:** Extract to `navbar.css`

##### 🟡 Medium Priority Issues (3)

6. **Inline `style=""` Attributes (150+ instances)**
   - Top offenders: `trash_dashboard.html` (62), `upload_step2.html` (12)
   - **Recommendation:** Create utility classes

7. **Duplicate Code Across Templates**
   - Video card styles repeated in 3+ files
   - Masonry grid CSS duplicated
   - **Recommendation:** Consolidate in stylesheet

8. **CSS Variable Usage Inconsistency**
   - Some sections use variables, others use hardcoded equivalents
   - **Recommendation:** Full audit and enforcement

##### 🟢 Low Priority Issues (2)

9. **Missing Variables for Common Values**
   - Colors like `#856404` (warning), `#f8f9fa` (light bg)
   - Spacing values: `48px`, `14px`, `10px`
   - **Recommendation:** Add to variable system

10. **Deprecated Variable Still in Use**
    - `--radius-standard` deprecated but used in 2 locations
    - **Recommendation:** Replace with `--radius-lg`, remove deprecated variable

---

### Strategy Roadmap for CSS Cleanup

**Phase 1: Critical Fixes (1-2 days)**
1. Extract `base.html` navbar styles (~2000 lines) → `navbar.css`
2. Remove `.masonry-container` duplication from `prompt_list.html`
3. Consolidate masonry/video styles from 3+ templates

**Phase 2: High Priority (2-3 days)**
4. Replace 30+ hardcoded colors with CSS variables
5. Move template `<style>` blocks to stylesheet (7+ templates)
6. Create utility classes to replace 150+ inline `style=""` attributes

**Phase 3: Optimization (1-2 days)**
7. Remove all inline `style=""` attributes
8. Add missing CSS variables
9. Remove deprecated variables

**Total Estimated Time:** 4-7 days for complete CSS cleanup

---

### Git Commits (This Session)

**Total:** 11 commits to branch `claude/ui-redesign-011CUvvuycDFFvqCcfY962oS`

1. `314ee57` - docs(style-guide): Update to v1.2 with Nov 12 session changes
2. `ad69185` - refactor(layout): Set max-width 1600px for ultrawide displays
3. `9e7bc91` - fix(load-more): Fix button jumping and improve loading state
4. `9e60749` - fix(load-more): Add HTTP status validation and improve error handling
5. `bb1f2db` - refactor(navbar): Add width: 100% to .pexels-navbar class
6. `349f8c7` - **fix(load-more): Fix dragModeEnabled ReferenceError** ✅ **CRITICAL FIX**
7. `e6f4a56` - refactor(layout): Update .masonry-container padding to 40px 0
8. `b79b64d` - refactor(layout): Remove mobile padding override for .masonry-container
9. `07f408e` - refactor(layout): Update .masonry-container padding to 40px 0 (inline styles)
10. `80df58c` - docs: Update style guide and create comprehensive session report
11. `3a0f94e` - docs: Create comprehensive session handoff document

---

### Documentation Created

**Session Reports:**
1. `SESSION_NOV13_2025_REPORT.md` (800 lines)
   - Complete CSS audit findings
   - 3-phase strategy roadmap with 13 tasks
   - Time estimates and step-by-step instructions
   - Expected benefits and success criteria

2. `SESSION_HANDOFF_NOV13_2025.txt` (496 lines)
   - All 11 commits documented
   - Session summary and technical context
   - Next session priorities
   - Quick start instructions

**Style Guide Updated:**
- `design-references/UI_STYLE_GUIDE.md` (version 1.3)
- Added "Recent Changes (Session: Nov 13, 2025)" section
- Documented Load More fix and layout refinements
- Moved Nov 12 changes to "Previous Session Changes"

---

### Next Session Priority

**START HERE:** Phase 1, Task 1.1 - Extract base.html navbar styles

**Critical Files:**
- `templates/base.html` (2000 lines of inline CSS to extract)
- `prompts/templates/prompts/prompt_list.html` (500 lines to extract)
- `static/css/style.css` (destination for extracted styles)

**Expected Impact:**
- Improved page load performance (cached CSS)
- Easier maintenance (single source of truth)
- Cleaner HTML templates
- Better organization and modularity

---

### Success Metrics

**Completed This Session:**
- ✅ Load More button error resolved (0 console errors)
- ✅ Layout refined for ultrawide displays (1600px max-width)
- ✅ Consistent vertical padding (40px 0) across all masonry grids
- ✅ CSS audit completed (10 issues identified and prioritized)
- ✅ Comprehensive roadmap created for CSS cleanup
- ✅ Documentation updated (style guide + 2 new reports)
- ✅ All commits pushed successfully (11 total)

**Ready for Next Phase:**
- 📋 Phase 1 CSS cleanup tasks ready to execute
- 📋 Detailed step-by-step instructions provided
- 📋 Time estimates and priority levels established
- 📋 Expected benefits clearly defined

---

## Performance Optimization Session - November 17, 2025

**Status:** ✅ COMPLETE - Event Delegation Implementation
**Session:** Current session
**Branch:** `claude/phase-1-css-cleanup-01NwaZx8inyivpT2bnGHfjsg`
**Duration:** Extended session with comprehensive agent testing
**Total Commits:** 2

### Session Objectives

1. Implement cache invalidation for dropdown caching system
2. Test implementation with wshobson agents (@code-reviewer, @performance-expert, @security)
3. Resolve all issues found during agent testing
4. Deploy production-ready solution

### Work Completed ✅

#### Initial Approach: Complex MutationObserver Caching (REJECTED)

**What Was Built:**
- Cache invalidation function with DOM cloning
- MutationObserver watching entire `document.body`
- Automatic detection of dropdown additions/removals
- 150 lines of complex code

**@code-reviewer Findings: 4.5/10 - DO NOT APPROVE FOR PRODUCTION**

**5 Critical Bugs Found:**

1. **Memory Leaks** - Event listeners accumulating in memory after DOM cloning
2. **Performance Regression** - 10-50ms cache invalidation SLOWER than original 1-2ms querySelectorAll
3. **Lost Event Listeners** - DOM cloning destroyed event listeners from other scripts
4. **Infinite Loop Risk** - MutationObserver could trigger itself during invalidation
5. **Undefined Global Variables** - Missing variable declarations

**Performance Comparison:**
```
Original (no cache):     1-2ms per click
Complex caching attempt: 10-50ms invalidation overhead ❌
Result: 25x-50x SLOWER than the problem we were trying to solve!
```

**Verdict:** Over-engineered solution that caused more problems than it solved.

---

#### Final Solution: Event Delegation Pattern (APPROVED)

**What Was Built:**
- Simple event delegation (no caching needed)
- Single document-level click listener
- IIFE wrapper with `'use strict'`
- `event.isTrusted` check for security
- 30 lines of clean, maintainable code

**Agent Validation Results:**

| Agent | Rating | Verdict |
|-------|--------|---------|
| @code-reviewer | 9/10 | Recommended over complex caching |
| @performance-expert | 9.5/10 | **APPROVED FOR PRODUCTION** |
| @security | 9.5/10 | **SECURE FOR PRODUCTION** |
| **Average** | **9.3/10** | **PRODUCTION READY** |

---

#### Performance Metrics

**Comparison Table:**

| Metric | Previous (Cache) | Current (Delegation) | Winner |
|--------|-----------------|---------------------|---------|
| Initial load | 10-50ms | <1ms | Current ✅ |
| Per-click | 1-2ms | 2-3ms | Even ✅ |
| DOM changes | 10-50ms | 0ms | **Current ✅** |
| Memory usage | 15-30KB | 1KB | Current ✅ |
| Code complexity | 150 lines | 30 lines | Current ✅ |
| Maintainability | Low | High | Current ✅ |

**Session Performance:**
```
Previous approach: 255ms total overhead per session
Current approach:  125ms total overhead per session
Improvement:       51% faster (130ms saved) ✅
```

**User-Perceptible Difference:** NONE (both under 16ms per frame for 60 FPS)

---

#### Security Assessment

**@security Rating: 9.5/10 - SECURE FOR PRODUCTION**

**Vulnerability Assessment:**
- XSS Risk: 2/10 (Very Low) ✅
- DOM Clobbering: 3/10 (Low) ✅
- Event Hijacking: 2/10 (Very Low) ✅
- Clickjacking: 1/10 (Negligible) ✅
- Injection Attacks: 2/10 (Very Low) ✅
- CSRF Implications: 0/10 (None) ✅

**Key Findings:**
- ✅ No dangerous DOM APIs used (`innerHTML`, `eval`, `document.write`)
- ✅ Hardcoded selectors (no injection vectors)
- ✅ Safe DOM APIs only (`closest`, `classList`, `setAttribute`)
- ✅ Compatible with Django security model (CSP, CSRF, template escaping)
- ✅ Zero critical or high-severity vulnerabilities found

---

### Implementation Details

**File:** `templates/base.html` (lines 909-958)

**Code Structure:**
```javascript
// Event Delegation Pattern (30 lines)
(function() {
    'use strict';

    let currentOpenDropdown = null;
    let clickLockedDropdown = null;

    document.addEventListener('click', function(event) {
        if (!event.isTrusted) return; // Security

        const clickedInsideDropdown = event.target.closest('.pexels-dropdown, .search-dropdown-menu');

        if (clickedInsideDropdown) {
            event.stopPropagation();
            return;
        }

        // Close all open dropdowns
        document.querySelectorAll('.pexels-dropdown.show, .search-dropdown-menu.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });

        // Reset ARIA attributes
        document.querySelectorAll('[aria-expanded="true"]').forEach(button => {
            button.setAttribute('aria-expanded', 'false');
        });

        currentOpenDropdown = null;
        clickLockedDropdown = null;
    });
})();
```

**Key Features:**
- IIFE wrapper prevents namespace pollution
- `event.isTrusted` blocks synthetic events (defense-in-depth)
- Private state variables (prevents DOM clobbering)
- Hardcoded selectors (no injection vectors)
- Works automatically with dynamic content

---

### Git Commits (This Session)

**Total:** 2 commits to branch `claude/phase-1-css-cleanup-01NwaZx8inyivpT2bnGHfjsg`

1. **`f11834b`** - `perf(navbar): Implement 4 critical performance and SEO optimizations`
   - Added querySelectorAll caching (initial approach)
   - Dynamic will-change GPU optimization
   - Upload button href SEO fix
   - Profile button focus styles (WCAG 2.1 Level AA)

2. **`b127738`** - `perf(navbar): Replace caching with event delegation pattern`
   - Replaced complex MutationObserver caching with simple event delegation
   - Fixed memory leaks from event listener accumulation
   - Eliminated 10-50ms cache invalidation overhead
   - Wrapped in IIFE with `'use strict'`
   - Added `event.isTrusted` security check

---

### Key Benefits

**Performance:**
✅ 51% faster overall (125ms vs 255ms per session)
✅ 2-3ms per click (optimal for 5-50 dropdowns)
✅ Zero cache invalidation overhead
✅ 97% memory reduction (1KB vs 15-30KB)

**Code Quality:**
✅ 80% less code (30 lines vs 150 lines)
✅ Simple and maintainable
✅ No complex state management
✅ Self-documenting

**Security:**
✅ Zero vulnerabilities found
✅ Hardcoded selectors (no injection)
✅ Safe DOM APIs only
✅ Defense-in-depth (`event.isTrusted`)

**Scalability:**
✅ Works with dynamic content automatically
✅ No manual cache invalidation needed
✅ Future-proof for AJAX/dynamic dropdowns
✅ Scales perfectly for 5-50 dropdowns

---

### Challenges Encountered

#### Challenge 1: Premature Optimization

**Problem:** Initial caching approach was over-engineered
- Tried to optimize 1-2ms querySelectorAll calls
- Introduced 10-50ms cache invalidation overhead
- Created more problems than it solved

**Solution:** Stepped back and evaluated if caching was actually needed
- Event delegation pattern simpler and faster
- No cache means no invalidation complexity
- "The best code is no code"

**Lesson:** Measure first, optimize later. Don't assume complexity equals performance.

---

#### Challenge 2: Memory Leak Detection

**Problem:** DOM cloning approach leaked event listeners
- Each invalidation created orphaned listener references
- After 100 DOM mutations: 100 leaked listener references
- No obvious symptoms, only detected through code review

**Solution:** Agent testing caught this before production
- @code-reviewer identified the leak pattern
- Prevented production memory issues
- Switched to approach with zero listener management

**Lesson:** Comprehensive agent testing catches subtle bugs that manual testing misses.

---

#### Challenge 3: Performance Paradox

**Problem:** Cache invalidation slower than the original problem
- Original: 1-2ms querySelectorAll per click
- Attempted fix: 10-50ms MutationObserver + DOM cloning
- Net result: 25x-50x slower!

**Solution:** Benchmark before implementing
- @performance-expert provided actual measurements
- Event delegation: 2-3ms (acceptable trade-off)
- Simpler code, better performance

**Lesson:** Always benchmark "optimizations" against the baseline.

---

### What's Next

**Immediate Next Steps:**
1. ✅ Performance optimization COMPLETE
2. 📋 **Ready to start CSS Cleanup Phase 1**

**CSS Cleanup Phase 1 (1-2 days estimated):**

1. **Extract `base.html` navbar styles** (~2000 lines)
   - Move massive inline `<style>` block to `static/css/navbar.css`
   - Improves caching (currently not cached on every page load)
   - Expected: 100-200ms faster page loads

2. **Remove `.masonry-container` duplication**
   - Currently defined in both `style.css` AND `prompt_list.html`
   - Template overrides stylesheet (causes inconsistencies)
   - Consolidate to single source of truth

3. **Consolidate masonry/video styles**
   - Video card styles duplicated across 3+ files
   - Move all to stylesheet for consistency

**Expected Benefits:**
- ✅ 2000+ lines moved from inline → cached CSS
- ✅ 100-200ms faster initial page loads
- ✅ Single source of truth (easier maintenance)
- ✅ Better browser caching

---

### Success Metrics

**Completed This Session:**
- ✅ Cache invalidation investigated (initial approach rejected)
- ✅ Event delegation implemented (9.3/10 average rating)
- ✅ 3 wshobson agents consulted (@code-reviewer, @performance-expert, @security)
- ✅ 51% performance improvement vs previous approach
- ✅ Zero vulnerabilities found
- ✅ Production-ready code deployed
- ✅ 2 commits pushed successfully

**Agents Used:**
1. **@code-reviewer** - Found 5 critical bugs in initial approach, recommended event delegation
2. **@performance-expert** - Benchmarked performance, confirmed 51% improvement, approved for production
3. **@security** - Comprehensive security audit, found zero vulnerabilities, cleared for production

**Ready for Next Phase:**
- 📋 CSS Cleanup Phase 1 tasks identified
- 📋 Time estimates established (1-2 days)
- 📋 Expected benefits quantified (100-200ms page load improvement)
- 📋 Files identified (base.html, navbar.css, style.css)

---

### Goals Achieved

**Primary Goal:** ✅ Implement production-ready dropdown performance optimization
- Agent-validated solution (9.3/10 average)
- 51% performance improvement
- Zero security vulnerabilities
- Future-proof for dynamic content

**Secondary Goal:** ✅ Establish robust agent testing workflow
- All 3 agents consulted before production
- Critical bugs caught early (saved production issues)
- Comprehensive documentation of findings
- Clear verdict from each agent (approve/reject)

**Tertiary Goal:** ✅ Learn from failed approaches
- Documented why initial approach failed
- Captured lessons learned for future reference
- Created reusable agent testing pattern
- Established "measure first, optimize later" principle

---

## 📝 Draft Mode System - November 29, 2025

**Status:** ✅ COMPLETE
**Duration:** Extended session
**Agent Rating:** 9.0/10 average

### Overview

The Draft Mode System allows users to save prompts as drafts before publishing, provides visual feedback for draft/pending review states, and adds admin tools for managing draft prompts.

### Components Implemented

#### 1. Draft Mode Banner (`templates/base.html`)

Yellow warning banner displayed at top of page for draft prompts with two variants:

| Variant | Condition | Message | Button |
|---------|-----------|---------|--------|
| **User Draft** | `status=0`, user is owner, not pending review | "This prompt is in draft mode and only visible to you" | "Publish Now" |
| **Pending Review** | `status=0`, `requires_manual_review=True` | "This prompt is pending admin review" | None |

**Styling:**
- Background: `#fff3cd` (warning yellow)
- Text: `#856404` (dark amber)
- Uses Bootstrap alert component with `alert-warning` class
- Icon: `fa-eye-slash` for draft, implied clock for pending

#### 2. Notification Color System (`static/css/style.css`, `templates/base.html`)

WCAG AA compliant colored backgrounds for Django flash messages:

| Type | Background | Border | Text | Use Case |
|------|------------|--------|------|----------|
| **Success** | `#d4edda` | `#c3e6cb` | `#155724` | Published successfully |
| **Info** | `#cce5ff` | `#b8daff` | `#004085` | Informational notices |
| **Warning** | `#fff3cd` | `#ffeaa7` | `#856404` | Draft mode, cautions |
| **Error** | `#f8d7da` | `#f5c6cb` | `#721c24` | Validation errors |

#### 3. User Draft Controls

**Upload Page (`/upload/details/`):**
- "Save as Draft" checkbox toggle
- When checked: Prompt saved with `status=0` (draft)
- When unchecked: Prompt auto-publishes after moderation passes

**Edit Page (`/prompt/<slug>/edit/`):**
- Published/Draft toggle switch
- Toggle styling: 52x28px, brand green (`#28a745`), 0.3s transitions
- Dynamic helper text updates on toggle change
- Disabled when prompt requires manual review AND not yet approved

#### 4. Admin Enhancements (`prompts/admin.py`)

- **Bulk Action:** "Mark selected prompts as drafts"
- Sets `status=0` for selected prompts
- Complements existing "Mark selected prompts as published" action

#### 5. Security Implementation

- **Drafts run full moderation:** No bypass of content moderation for drafts
- **`prompt_publish` view checks:** `moderation_status` verified before allowing publish
- **Prevents:** Users publishing prompts that were flagged for manual review

### Files Modified (November 29, 2025)

| File | Changes |
|------|---------|
| `prompts/views.py` | `upload_submit`, `prompt_edit`, `prompt_publish` views |
| `prompts/admin.py` | Added `make_draft` bulk action |
| `prompts/templates/prompts/prompt_detail.html` | Draft banner integration |
| `prompts/templates/prompts/prompt_edit.html` | Published/Draft toggle |
| `prompts/templates/prompts/upload_step2.html` | "Save as Draft" checkbox |
| `templates/base.html` | Notification container + draft banner |
| `static/css/style.css` | Toggle component CSS (82 lines) |
| `design-references/UI_STYLE_GUIDE.md` | Toggle + notification docs |

### Bug Fixed: Toggle Locked After Admin Approval ✅

**Issue:** Toggle locked after admin approval of NSFW prompt

**Status:** ✅ FIXED (November 30, 2025)

**Description:** After an admin approves a prompt that was flagged for manual review (e.g., NSFW content), the edit page toggle remained locked/disabled.

**Root Cause:** Template and view checked `requires_manual_review` but didn't account for approved status.

**Files Fixed:**
1. `prompts/templates/prompts/prompt_edit.html` (lines 164, 174-188)
2. `prompts/views.py` (line 1232 - `prompt_publish` view)

**Solution Applied:**
```python
# Old logic (buggy):
if prompt.requires_manual_review:
    disable_toggle()

# New logic (fixed):
if prompt.requires_manual_review and prompt.moderation_status != 'approved':
    disable_toggle()
```

**Additional Improvements:**
- Added helper text for approved prompts: "Admin approved. You can now publish this prompt."
- Added helper text for rejected prompts: "This prompt was rejected and cannot be published."
- Both frontend (template) AND backend (view) updated for security consistency

### Admin UX Improvements for Moderation Actions ✅

**Issue:** Admin confusion between "Mark as published" and "Approve & Publish" actions

**Status:** ✅ IMPLEMENTED (November 30, 2025)

**Problem:** When an admin used "Mark selected prompts as published" on a flagged prompt, the prompt was published but the user's toggle remained locked because `moderation_status` stayed as 'flagged'. Admins assumed they had "approved" the content.

**Solution (per @django-pro and @ui-ux-designer agents):**

**1. Action Order Changed:**
- "Approve & Publish" now appears FIRST (most common for flagged content)

**2. Clearer Action Names:**
| Before | After |
|--------|-------|
| "Mark selected prompts as published" | "Publish (status only - does NOT clear moderation flags)" |
| "Mark selected prompts as drafts" | "Move to Draft" |
| "Approve moderation & publish selected prompts" | "Approve & Publish (clears moderation flags)" |

**3. Smart Warning System:**
When admin uses "Publish (status only)" on flagged prompts:
```
⚠️ WARNING: 3 prompt(s) still have moderation flags. Users will NOT be able
to toggle draft/publish on these prompts. Use "Approve & Publish" action
instead to clear moderation flags.
```

**4. Informative Success Messages:**
- "Approve & Publish": `✓ 5 prompts approved and published. 3 flagged prompt(s) now cleared - users can toggle draft/publish.`

**File Modified:** `prompts/admin.py` (lines 28-29, 190-259)

**Agent Ratings:**
- @django-pro: 9/10 (smart filtering, informative messages)
- @ui-ux-designer: Recommended cleaner action names

### Delete System Enhancements ✅

**Status:** ✅ COMPLETE (November 30, 2025)
**Session:** Delete System Verification + Bug Fixes

#### Overview

The Delete System received critical bug fixes to ensure DeletedPrompt records are created on ALL delete paths, enabling proper SEO redirects for deleted prompt URLs.

#### Critical Bug Fixed: DeletedPrompt Records Not Created on UI Delete

**Issue:** When users deleted prompts via the "Delete Forever" button in the Trash UI, no DeletedPrompt record was created. This caused 404 errors instead of proper SEO redirects.

**Root Cause:** Only the `cleanup_deleted_prompts` management command was creating DeletedPrompt records. The UI delete paths (`prompt_permanent_delete` and `empty_trash` views) were missing this functionality.

**Solution Implemented:**

1. **Added `create_from_prompt()` class method to DeletedPrompt model:**
   - Finds best matching prompt for redirect targeting
   - Creates DeletedPrompt record with 90-day expiration
   - Calculates similarity score using tags, AI generator, likes, and recency

2. **Updated delete views to use shared method:**
   - `prompt_permanent_delete()` view (single item delete)
   - `empty_trash()` view (bulk delete)
   - Both now create DeletedPrompt records before hard deletion

3. **Refactored cleanup command:**
   - Uses shared `create_from_prompt()` method
   - Consistent behavior across all delete paths
   - Removed duplicate code

#### SEO Redirect Logic

**Location:** `prompts/views.py` (lines 293-327)

When a deleted prompt URL is accessed:

| Similarity Score | Action |
|-----------------|--------|
| ≥ 0.75 (strong match) | 301 redirect to similar prompt |
| < 0.75 (weak match) | 410 Gone page with suggestions |
| No record / expired | 404 Not Found |

**410 Gone Page Features:**
- Shows original prompt title
- Displays related prompts from same AI generator
- Provides search and browse CTAs
- Proper HTTP 410 status code for SEO

#### Files Modified (November 30, 2025)

| File | Changes |
|------|---------|
| `prompts/models.py` | Added `DeletedPrompt.create_from_prompt()` class method (76 lines) |
| `prompts/views.py` | Updated `prompt_permanent_delete()` and `empty_trash()` views with imports |
| `prompts/management/commands/cleanup_deleted_prompts.py` | Refactored to use shared method, removed unused import |

#### Testing Results

| Test | Result |
|------|--------|
| DeletedPrompt records created | ✅ 4 records created correctly |
| Prompts removed from DB | ✅ All prompts removed |
| SEO redirects | ✅ 410 Gone page verified manually |
| Trash empty | ✅ Confirmed |
| Cleanup command | ✅ Runs without errors (--dry-run tested) |

#### Agent Validation

| Agent | Rating | Verdict |
|-------|--------|---------|
| @django-pro | 8.5/10 | Excellent Django pattern, production-ready |
| @code-reviewer | 8.5/10 | Well-structured, properly implements DRY |
| @security-auditor | 8.5/10 | Secure, no blocking issues |

### November 30, 2025 Session Commits

**4 commits completed:**

**Commit 1: `fix(admin): Improve moderation action UX and fix toggle unlock bug`** (53774e2)
- Toggle now correctly enabled after admin approval
- Added moderation_status check to disabled condition
- Reorder actions: "Approve & Publish" now first
- Clearer action names with explanatory text
- Smart warning for using simple publish on flagged prompts
- Files: `prompts/admin.py`, `prompts/templates/prompts/prompt_edit.html`

**Commit 2: `docs: Update documentation for toggle fix and admin UX improvements`** (e1b08c9)
- CLAUDE.md: Added "Admin UX Improvements for Moderation Actions" section
- UI_STYLE_GUIDE.md: Updated with Draft Mode System documentation
- Security fix in views.py: prompt_publish now checks moderation_status

**Commit 3: `fix(seo): Create DeletedPrompt records on UI delete for SEO redirects`** (f4d0d16)
- Added `create_from_prompt()` class method to DeletedPrompt model
- Updated `prompt_permanent_delete()` and `empty_trash()` views
- Refactored `cleanup_deleted_prompts` command to use shared method
- Agent testing: @django-pro 8.5/10, @code-reviewer 8.5/10, @security-auditor 8.5/10

**Commit 4: `fix(views): Add missing DeletedPrompt import to delete views`** (9b4f203)
- Fixed NameError: 'DeletedPrompt' is not defined at line 1340
- Added lazy import inside `prompt_permanent_delete()` view
- Added lazy import inside `empty_trash()` view
- Follows existing pattern of lazy imports to avoid circular dependencies

---

## 🗑️ Trash UX Overhaul & Profile Integration - November 30, 2025

**Session:** https://claude.ai/chat/22ba30d4-91a8-416a-998a-9cb1592fa061
**Status:** ✅ 95% COMPLETE
**Total Commits:** 10

### Session Overview

Comprehensive modernization of the Trash Bin feature, including UI updates to match the design system, security fixes, and consolidation into the user profile page.

### Key Accomplishments

1. **Button Styling Modernization** - WCAG AA compliant colors, unified `.trash-btn-action` class
2. **Empty Trash Modal Conversion** - Replaced standalone page with accessible in-page modal
3. **Browser Cache Fix** - `@never_cache` decorator prevents "ghost items"
4. **Profile Page Integration** - Trash moved to `/users/{username}/trash/` as profile tab
5. **NSFW Security Fix** - Blocked users from bypassing moderation via trash restore
6. **Cloudinary Error Handling** - Placeholder fallback for missing/errored images

### Git Commits (10 Total)

| # | Type | Scope | Description |
|---|------|-------|-------------|
| 1 | style | trash | Modernize trash bin buttons with design system (WCAG AA colors, 44px touch targets) |
| 2 | style | trash | Unify button colors with dark gray accent (`--btn-text-sm`, `--btn-padding-sm` vars) |
| 3 | feat | trash | Convert Empty Trash confirmation to modal (ARIA, escape key, focus management) |
| 4 | chore | trash | Remove unused `confirm_empty_trash.html` template |
| 5 | fix | cache | Prevent browser caching on trash page (`@never_cache` decorator) |
| 6 | feat | profile | Consolidate trash into profile page tab (`/users/{username}/trash/`) |
| 7 | fix | profile | Add missing `cloudinary_tags` template load |
| 8 | security | restore | Block NSFW content from bypassing moderation via trash restore |
| 9 | fix | trash | Fix NSFW prompt images not displaying (CloudinaryResource handling) |
| 10 | fix | trash | Add onerror fallback for missing Cloudinary images (404 handling) |

### Files Modified

**Views & URLs:**
- `prompts/views.py` - Trash redirect, restore security, cache control
- `prompts/urls.py` - Profile trash URL pattern

**Templates:**
- `prompts/templates/prompts/user_profile.html` - Full trash tab implementation
- `prompts/templates/prompts/trash_bin.html` - Button styling, onerror fallback
- `templates/base.html` - Profile dropdown "Trash" link

**Template Tags:**
- `prompts/templatetags/cloudinary_tags.py` - CloudinaryResource object handling

**Removed:**
- `prompts/templates/prompts/confirm_empty_trash.html` - Replaced by modal

### Security Enhancement Details

**NSFW Restore Loophole Fixed:**

Users could previously bypass NSFW/moderation approval by:
1. Uploading flagged content (goes to Pending Review)
2. Deleting the prompt (moves to Trash)
3. Clicking "Restore & Publish" (would publish WITHOUT admin approval!)

**Solution Applied:**
- **Backend:** Forces `requires_manual_review` prompts to restore as draft only
- **Frontend:** Hides "Restore & Publish" button for flagged content
- **Defense in depth:** Both layers protect against the vulnerability

### Known Issue (Resolved)

**NSFW Image Not Displaying:**
- **Root Cause:** `CloudinaryResource.url` throws `ValueError` when SDK cloud_name not configured
- **Solution:** Updated `cloudinary_transform` filter to handle CloudinaryResource objects directly
- **Additional Fix:** Added `onerror` fallback for images that return 404 from Cloudinary
- **Finding:** 2 of 6 NSFW prompts have orphaned database records (Cloudinary files deleted)

### Agent Validation

**Commit 8 (Security Fix):** 9/10
- Defense in depth approach
- Both frontend + backend protected

**Commit 9 (CloudinaryResource Fix):** Investigation-based
- Root cause identified via Django shell testing
- Template filter enhanced to handle 4 input types

**Commit 10 (onerror Fallback):** Data-driven
- Verified via curl tests (3/5 NSFW images return 200, 2 return 404)
- Fallback provides graceful degradation for orphaned records

### URL Changes

| Before | After |
|--------|-------|
| `/trash/` | Redirects (302) to `/users/{username}/trash/` |
| N/A | `/users/{username}/trash/` (new canonical URL) |

---

## 🎨 CSS Cleanup Status - November 2025

### Phase 1: COMPLETE ✅

**Completed:** November 2025
**Status:** Merged to main

**What Was Accomplished:**
- ✅ Extracted navbar styles to `static/css/navbar.css` (1,136 lines)
- ✅ Removed `.masonry-container` duplication from templates
- ✅ Created component-based CSS architecture
- ✅ Created `static/css/components/masonry-grid.css` (255 lines)
- ✅ Created `static/css/pages/prompt-list.css` (304 lines)

**CSS Architecture:**
```
static/css/
├── navbar.css (1,136 lines)
├── style.css (1,789 lines)
├── components/
│   └── masonry-grid.css (255 lines)
└── pages/
    └── prompt-list.css (304 lines)
```

**Branch Cleanup (November 30, 2025):**
- Deleted stale branch: `claude/phase-1-css-cleanup-01NwaZx8inyivpT2bnGHfjsg`
- Branch was 17 commits behind main with 0 unique commits
- Both local and remote branches removed

---

### Phase 2: FUTURE WORK (Low Priority)

**Status:** Documented for future cleanup sprint
**Priority:** Low - Current inline styles work correctly
**Estimated Time:** 2-3 days

**Remaining Work:**
17 templates still contain inline `<style>` blocks that could be extracted:

**High Priority Templates:**
1. `user_profile.html` - Complex, frequently used
2. `prompt_list.html` - Homepage
3. `prompt_detail.html` - High traffic page

**Medium Priority Templates:**
4. `prompt_edit.html`
5. `upload_step2.html`
6. `trash_bin.html`

**Low Priority Templates (Admin/Standalone):**
7. `settings_notifications.html`
8. `ai_generator_category.html`
9. `confirm_permanent_delete.html`
10. `confirm_restore.html`
11. And 7 others (admin pages, error pages)

**Why Deferred:**
- Inline styles work correctly (no bugs)
- Phase G (Social Features) provides more user value
- CSS cleanup is maintenance work that can wait
- Can be tackled during a dedicated "cleanup sprint"

**When to Revisit:**
- During a maintenance/cleanup sprint
- Before major UI overhaul
- If performance issues arise from inline styles

---

## 📋 Phase G: Homepage Tabs & Sorting - December 5, 2025

**Status:** ✅ PART A COMPLETE | 🔄 PART B PLANNED
**Session Chat:** https://claude.ai/chat/07791520-02d8-4592-a60a-443249906759
**Commits:** 6

---

### Overview

Implemented Pexels-style homepage filtering system with tab navigation and sorting dropdown, enabling users to filter content by type (Home/All/Photos/Videos) and sort by engagement (Trending/New/Following).

---

### Part A: Homepage Tabs & Sorting ✅ COMPLETE

#### Features Implemented

**Tab Navigation (LEFT side):**
- Home - All content with trending algorithm (default)
- All - All content chronologically
- Photos - Photos only
- Videos - Videos only
- Pexels-style dark pill (#1a1a1a) for active tab
- ARIA accessibility (role="tablist", aria-selected)

**Sort Dropdown (RIGHT side):**
- Trending - Engagement score (likes + comments), recent content prioritized
- New - Most recent first
- Following - Prompts from followed users only (authenticated)
- Checkmark indicator on active option

**Trending Algorithm:**
- `engagement_score` = likes count + approved comments count
- `is_trending` flag prioritizes recent engaged content
- Shows ALL prompts (trending first, then rest by newest)
- No artificial limits - pagination handles naturally

**Like Button Optimistic UI:**
- Instant visual feedback on click
- Heart icon and count update immediately
- Server sync in background
- Graceful rollback on error

**Auto-Approve Comments:**
- SiteSettings singleton model added
- `auto_approve_comments` toggle (default: True)
- Admin can disable for manual moderation
- Different success messages based on approval state

**Navigation Improvements:**
- "Browse Prompts" smooth scrolls to prompts section
- `scroll-behavior: smooth` CSS rule
- `id="browse-prompts"` anchor on masonry container

#### Commits (6 total)

| Commit | Description |
|--------|-------------|
| `09b51ed` | fix(phase-g): Homepage fixes round 2 - trending, likes, comments, scroll |
| `3f03a48` | fix(homepage): Add missing context_object_name to PromptList view |
| `a7d6b81` | feat(phase-g): Implement homepage tabs and sorting dropdown (Part A) |
| `b94f16f` | feat(homepage): Add sorting dropdown with Trending/New/Following filters |
| `d39483b` | docs: Update CLAUDE.md with CSS cleanup status and Phase G roadmap |
| `ee32ee5` | docs: Add Trash UX Overhaul session documentation to CLAUDE.md |

#### Files Modified

| File | Changes |
|------|---------|
| `prompts/views.py` | PromptList with tab/sort logic, trending algorithm, comment auto-approve |
| `prompts/models.py` | SiteSettings singleton model |
| `prompts/admin.py` | SiteSettingsAdmin interface |
| `prompts/templates/prompts/prompt_list.html` | Tabs, dropdown, optimistic like, smooth scroll (~150 lines CSS) |
| `prompts/migrations/0035_sitesettings.py` | SiteSettings migration |

#### Bugs Fixed During Implementation

1. **Grid not loading for Home/All tabs**
   - Root cause: Missing `context_object_name = 'prompt_list'` in PromptList
   - Template expected `prompt_list`, Django provided `object_list`

2. **Trending only showing ~20 items**
   - Root cause: 7-day filter was limiting results
   - Fix: Show ALL prompts with `is_trending` flag for priority sorting

3. **Sorting bug in ai_generator_category**
   - Was: `order_by('-created_on', '-created_on')` (duplicate)
   - Fixed: `order_by('-likes_count', '-created_on')`

#### Agent Validation

| Agent | Rating | Notes |
|-------|--------|-------|
| @django-expert | 8.5/10 | Query efficiency approved |
| @ui-ux-designer | 8.5/10 | Production ready |
| @code-reviewer | 7.5/10 | Approved with recommendations |
| **Average** | **8.17/10** | Exceeds 8+ requirement |

---

### Part B: Views Tracking System ✅ COMPLETE

**Status:** ✅ COMPLETE (December 5-6, 2025)
**Commits:** 10 commits
**Deployed:** Heroku production
**Final Agent Rating:** 8.8/10 average

---

#### Features Implemented

**1. PromptView Model (View Tracking)**
- Tracks unique views per prompt detail page
- Deduplicates by authenticated user OR session+IP hash
- SHA-256 IP hashing with server-side pepper (privacy-first)
- Indexed for query performance

**2. Security Enhancements**
- `IP_HASH_PEPPER` environment variable for secure hashing
- Rate limiting: 10 views/minute per IP (prevents inflation attacks)
- Bot detection: 28+ user-agent patterns filtered
- Empty user-agent requests blocked

**3. Configurable Trending Algorithm**
- Admin-configurable weights in SiteSettings:
  - `trending_like_weight` (default: 3.0)
  - `trending_comment_weight` (default: 5.0)
  - `trending_view_weight` (default: 0.1)
  - `trending_recency_hours` (default: 48)
  - `trending_gravity` (default: 1.5)

**4. View Count Display**
- Top-left badge overlay on prompt thumbnails
- Configurable visibility: Admin / Author / Premium / Public
- Eye icon with count (e.g., 👁 42)
- Semi-transparent dark background (75% opacity) for readability

**5. Performance Optimization**
- Homepage cache TTL reduced from 5 minutes to 60 seconds
- View counts update within ~1 minute
- Cached queryset includes views_count annotation

---

#### Commits (10 total)

| Commit | Description |
|--------|-------------|
| `351d698` | fix(phase-g): Fix trending algorithm and tab navigation anchors |
| `46bc8a1` | feat(phase-g): Implement views tracking and configurable trending (Part B) |
| `094e86e` | fix(phase-g): Security enhancements and view overlay fix for Part B |
| `9db9f8e` | fix(phase-g): Add missing CSS for view counter overlay |
| `74b8b8e` | feat(phase-g): Reposition view counter as top-left badge |
| `52a0275` | perf(cache): Reduce homepage cache TTL from 5 min to 60 sec |
| `42b18a3` | perf(cache): Reduce homepage cache TTL from 5 min to 60 sec |
| `3c96ba8` | refactor(phase-g): Improve code quality for higher agent ratings |
| `6a1494b` | migration: Add view_rate_limit to SiteSettings |
| `10886d5` | docs: Add Phase G Part B complete session report |

---

#### Code Quality Improvements (Commit `3c96ba8`)

Three improvements were made to increase agent ratings:

**1. Template Parentheses Clarity**
- File: `_prompt_card.html`
- Change: Added explicit parentheses to visibility condition
- Before: `{% if can_see_views or view_visibility == 'author' and user == prompt.author %}`
- After: `{% if can_see_views or (view_visibility == 'author' and user == prompt.author) %}`
- Impact: @frontend-developer 7.0 → 9.0/10

**2. BOT_PATTERNS Moved to Constants**
- File: `prompts/constants.py`
- Change: Moved 28 bot user-agent patterns from `models.py` to `constants.py`
- New constant: `BOT_USER_AGENT_PATTERNS`
- Impact: Better separation of concerns, easier maintenance

**3. Configurable Rate Limit**
- File: `prompts/models.py`, `prompts/admin.py`
- Change: Rate limit now configurable via SiteSettings admin
- New field: `view_rate_limit` (default: 10)
- Impact: @django-expert 7.5 → 8.5/10

---

#### Files Modified

| File | Changes |
|------|---------|
| `prompts/models.py` | PromptView model, SiteSettings fields, view_rate_limit, security methods |
| `prompts/views.py` | views_count annotation, cache TTL (60s) |
| `prompts/admin.py` | SiteSettingsAdmin fieldsets (8 fields total), PromptViewAdmin |
| `prompts/constants.py` | BOT_USER_AGENT_PATTERNS, DEFAULT_VIEW_RATE_LIMIT |
| `_prompt_card.html` | View count badge (top-left), parentheses fix |
| `static/css/style.css` | .view-count-badge styles, .platform-info font-size |
| `prompts/migrations/0036_*` | SiteSettings trending fields |
| `prompts/migrations/0037_*` | SiteSettings view_rate_limit field |

---

#### Admin Usage Guide

**Configuring Trending Algorithm:**
1. Navigate to `/admin/prompts/sitesettings/1/change/`
2. Adjust weights under "Trending Algorithm" section:
   - **Like weight:** Points per like (default: 3.0)
   - **Comment weight:** Points per comment (default: 5.0)
   - **View weight:** Points per view (default: 0.1)
   - **Recency hours:** Time window for "recent" engagement (default: 48)
   - **Gravity:** Decay rate - higher = faster decay (default: 1.5)
3. Click "Save" - changes take effect within 60 seconds

**Configuring View Count Visibility:**
1. In same SiteSettings page, find "View Count Visibility"
2. Options:
   - **admin:** Only staff users see view counts
   - **author:** Admin + prompt author sees their own counts
   - **premium:** Admin + premium subscribers see counts
   - **public:** Everyone sees view counts
3. Default is "admin" for privacy

**Viewing Analytics:**
1. Navigate to `/admin/prompts/promptview/`
2. See all recorded views with filters by prompt, user, date
3. Use for understanding content performance

**Configuring View Rate Limit:**

The rate limit prevents view count manipulation by limiting how many views can be recorded from a single IP address per minute.

1. Navigate to `/admin/prompts/sitesettings/1/change/`
2. Find "View Count Settings" section
3. Set "View rate limit" (default: 10 views/minute per IP)
4. Click "Save"

| Value | Use Case |
|-------|----------|
| 5 | Stricter protection |
| 10 | Default - good balance |
| 20 | More lenient for high-traffic sites |

**How Rate Limiting Works:**
- Users can always view pages normally (no blocking)
- When limit is exceeded, views are silently not recorded
- Counter resets every 60 seconds per IP
- Normal users (3-5 views/min) are never affected
- Protects against bots and view inflation attacks

---

#### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `IP_HASH_PEPPER` | Recommended | `SECRET_KEY[:16]` | Server-side pepper for IP hashing |

**Setting on Heroku:**
```bash
# Generate secure pepper
python -c "import secrets; print(secrets.token_hex(16))"

# Set on Heroku
heroku config:set IP_HASH_PEPPER="<generated-value>" --app mj-project-4
```

---

#### Agent Validation Summary (Final)

| Agent | Initial | Final | Notes |
|-------|---------|-------|-------|
| @django-expert | 7.5/10 | 8.5/10 | Improved with configurable rate limit |
| @security-auditor | 8.5/10 | 8.5/10 | Approved security implementation |
| @code-reviewer | 8.5/10 | 9.0/10 | Improved with constants refactoring |
| @frontend-developer | 7.0/10 | 9.0/10 | Improved with template parentheses |
| @ui-ux-designer | 7.5/10 | 8.5/10 | Approved badge positioning |
| **Average** | **7.8/10** | **8.8/10** | ✅ Exceeds 8+ target |

---

#### Known Limitations & Future Improvements

**All major items resolved.** Minor remaining items:

1. **Rate Limit Logging** (Optional)
   - Current: Silent rejection of rate-limited requests
   - Suggested: Add optional debug logging for monitoring
   - Priority: LOW - Current behavior is acceptable
   - File: `prompts/models.py`

**Note:** All other previous limitations have been addressed in commit `3c96ba8`:
- ✅ Template parentheses added for clarity
- ✅ Rate limit now configurable via admin
- ✅ BOT_PATTERNS moved to `prompts/constants.py`

---

#### Security Features (Detail)

**IP Hashing with Pepper:**
```python
@classmethod
def _hash_ip(cls, ip_address):
    pepper = os.environ.get('IP_HASH_PEPPER', settings.SECRET_KEY[:16])
    salted = f"{pepper}:{ip_address}"
    return hashlib.sha256(salted.encode()).hexdigest()
```

**Rate Limiting (Configurable):**
```python
@classmethod
def _is_rate_limited(cls, ip_hash):
    cache_key = f"view_rate:{ip_hash}"
    current_count = cache.get(cache_key, 0)
    rate_limit = SiteSettings.get_solo().view_rate_limit  # Admin configurable
    if current_count >= rate_limit:
        return True
    cache.set(cache_key, current_count + 1, timeout=60)
    return False
```

**Bot Detection (28 patterns in `prompts/constants.py`):**
```python
BOT_USER_AGENT_PATTERNS = [
    'bot', 'crawler', 'spider', 'scraper', 'googlebot', 'bingbot',
    'slurp', 'duckduckbot', 'baiduspider', 'yandexbot', 'sogou',
    'exabot', 'facebot', 'ia_archiver', 'semrushbot', 'ahrefsbot',
    'mj12bot', 'dotbot', 'petalbot', 'bytespider', 'applebot',
    'twitterbot', 'linkedinbot', 'facebookexternalhit', 'curl',
    'wget', 'python-requests', 'axios', 'node-fetch',
]
```

---

### Part C: Community Favorites / Leaderboard ✅ COMPLETE

**Status:** 100% Complete (with known macOS limitation)
**Session Chats:**
- Initial: https://claude.ai/chat/5ab46a30-3d54-4586-bd40-0e0309fb8f2c
- Final Polish: December 11, 2025
**Commits:** 9 commits total
**Deployed:** Heroku production
**Agent Rating:** 8.9/10 average (final validation)

---

#### Features Implemented

**1. Leaderboard Page** (`/leaderboard/`)
- Two ranking modes: Most Viewed / Most Active
- Time period filters: Week / Month / All Time
- Follow buttons with AJAX functionality
- User thumbnails showing recent prompts (4 default, 5 on wide desktop >1700px)
- Responsive design with mobile breakpoints (992px and below)
- Pexels-inspired design aesthetic
- Custom period dropdown (replaced native select)

**2. LeaderboardService Class** (`prompts/services/leaderboard.py`)
- 5-minute caching for performance optimization
- **Most Viewed:** SUM of all views on user's prompts
- **Most Active:** `uploads*10 + comments*2 + likes*1` scoring
- Bulk follow status query (prevents N+1 queries)
- Bulk thumbnail attachment (prevents N+1 queries)
- Time period filtering (7 days / 30 days / all time)
- Input validation with bounds checking

**3. Navigation Integration**
- Added "Leaderboard" link to Explore dropdown in navbar
- Trophy icon visual indicator
- Accessible via `/leaderboard/` URL route

**4. Mobile Layout**
- 3-column structure: [Avatar] [Name+Stats] [Follow Button]
- Helper text: "Click the thumbnails below to visit user's profile"
- Horizontal scrolling thumbnails
- Touch-friendly tap targets

---

#### Iterative Refinement (9 Rounds)

| Round | Date | Key Changes |
|-------|------|-------------|
| **Initial** | Dec 6 | Core leaderboard implementation (5 commits) |
| **Round 1-3** | Dec 7 | Video thumbnails fix, stats color, code quality improvements |
| **Round 4** | Dec 9 | Scrollbar root cause fix (flex-shrink: 0 was blocking overflow) |
| **Round 5** | Dec 9 | Reduced thumbnails from 5 to 4, added scrollbar padding |
| **Round 6** | Dec 9 | Fixed scrollbar again (removed justify-content: right) |
| **Round 7** | Dec 9 | Mobile helper text polish, border-radius on thumbnails container |
| **Round 8** | Dec 9 | Scrollbar always visible attempt, 5 thumbnails on wide desktop (>1700px) |
| **Final** | Dec 11 | Header spacing fix, thumbnail width 480px, scrollbar track visibility |

---

#### Files Created/Modified

| File | Type | Description |
|------|------|-------------|
| `prompts/services/leaderboard.py` | New | LeaderboardService class (~280 lines) |
| `prompts/templates/prompts/leaderboard.html` | New | Leaderboard template (~250 lines) |
| `prompts/views.py` | Modified | Added `leaderboard` view function |
| `prompts/urls.py` | Modified | URL route `/leaderboard/` |
| `static/css/style.css` | Modified | Leaderboard CSS (~200 lines added) |
| `templates/base.html` | Modified | Navigation dropdown links |
| `CLAUDE.md` | Modified | Documentation updates |

---

#### Technical Implementation Details

**Thumbnail Responsive Behavior:**
```
Screen Width        Thumbnails    Overlay Position
< 1700px            4 visible     4th thumbnail has "+X more"
≥ 1701px            5 visible     5th thumbnail has "+X more"
```

**Mobile Layout (≤992px):**
```
[Rank] [Avatar] [Name + Stats] [Follow Button]
       [Thumbnails with horizontal scroll]
       [Helper text]
```

**Leaderboard Service Architecture:**
```python
class LeaderboardService:
    CACHE_TTL = 300  # 5 minutes

    @classmethod
    def get_most_viewed(cls, period='week', limit=25):
        # Aggregates views across all user's prompts

    @classmethod
    def get_most_active(cls, period='week', limit=25):
        # Scores: uploads*10 + comments*2 + likes*1

    @classmethod
    def get_follow_status_bulk(cls, current_user, target_users):
        # Bulk query for follow status (prevents N+1)
```

**Video Thumbnail Fix:**
- Changed from string manipulation (`slice:-4.jpg`) to `get_thumbnail_url()` method
- Cloudinary generates proper thumbnails with transformations

**Stats Color:**
- Changed from `var(--gray-500)` to `var(--black)` for better readability
- Contrast ratio improved from 4.5:1 to 21:1

---

#### Agent Validation (Final - December 11, 2025)

| Agent | Rating | Notes |
|-------|--------|-------|
| @frontend-developer | 9.2/10 | Excellent CSS structure, cross-browser handling |
| @ui-ux-designer | 9.0/10 | Consistent with design system |
| @code-reviewer | 8.5/10 | Clean implementation, proper variable usage |
| **Average** | **8.9/10** | Exceeds 8+ threshold |

---

#### Known Limitations

**1. macOS Scrollbar Thumb Auto-Hides**
- **Issue:** On macOS Chrome/Safari with "Show scrollbars: When scrolling" system setting, the scrollbar thumb auto-hides after interaction stops
- **Mitigation:** Scrollbar track is always visible via CSS background gradient fallback
- **Impact:** Cosmetic only - scroll functionality works correctly
- **Status:** Accepted as macOS system limitation (would require JavaScript library to fully override)

**2. Mobile Browsers**
- **Issue:** iOS Safari and Android Chrome use native scrollbars
- **Impact:** Expected behavior - custom scrollbar styling not supported on mobile
- **Status:** By design

**3. Firefox Hover State**
- **Issue:** Firefox's `scrollbar-width: thin` doesn't support hover pseudo-classes
- **Impact:** Minor cosmetic difference - thumb color doesn't change on hover
- **Status:** Accepted (Firefox limitation)

---

#### CSS Variables Used

| Variable | Purpose |
|----------|---------|
| `--gray-200` | Scrollbar track, borders |
| `--gray-400` | Scrollbar thumb, secondary text |
| `--gray-500` | Scrollbar thumb hover |
| `--space-12` | Page padding (48px) |
| `--space-4` | Page padding component (16px) |
| `--black` | Stats text color |

---

#### Profile Metrics (December 11, 2025)

**User profile pages now display actual stats instead of placeholder dashes.**

| Stat | Definition | Formula/Query | Time Window |
|------|------------|---------------|-------------|
| **Total Views** | Unique views across all user's prompts | `PromptView.objects.filter(prompt__author=user).count()` | All time |
| **All-time Rank** | Position on Most Viewed leaderboard | `SUM(views)` per user | All time |
| **30-day Rank** | Position on Most Active leaderboard | `(uploads×10) + (comments×2) + (likes×1)` | Rolling 30 days |

**Ranking Formulas:**

**Most Viewed (All-time Rank):**
- Counts total unique views across all user's prompts
- Higher views = better rank
- Rank 1 = user with most total views
- Uses `LeaderboardService.get_user_rank(user, metric='views', period='all')`

**Most Active (30-day Rank):**
- Scores based on recent activity:
  - Each upload: 10 points
  - Each comment: 2 points
  - Each like given: 1 point
- Only counts activity within past 30 days (rolling window)
- Higher score = better rank
- Rank 1 = most active user in past 30 days
- Uses `LeaderboardService.get_user_rank(user, metric='active', period='month')`

**Why This Hybrid Approach:**
- **All-time Rank = Most Viewed:** Pairs with "Total Views" stat (same metric family)
- **30-day Rank = Most Active:** Encourages ongoing engagement and community participation
- Users see both their content reach (views) and their contribution (activity)

**Display Logic:**
- Rank displays as `#1`, `#5`, `#42`, etc.
- Users not ranked (no activity or beyond top 1000) show `-`
- Total Views shows `0` for users with no views

**Statistics Tab:**
- Hidden via `show_statistics_tab: False` context variable
- Can be enabled later for complex analytics (bar graphs, trends)

---

### Known Issues / Testing Needed

✅ **Migration Applied:** SiteSettings fields and PromptView model deployed

**Testing Checklist (Part A & B):**
- [x] All tab + sort combinations display content correctly
- [x] Like button updates instantly
- [x] Comments auto-approve
- [x] Smooth scroll works
- [x] View count badge displays for admins
- [x] View tracking records unique views
- [x] Rate limiting blocks excessive requests
- [x] Bot detection filters crawlers

---

### Future Enhancements (From Agent Feedback)

- Add `author__userprofile` to select_related (prevent N+1)
- Extract parameter validation to helper method (DRY)
- Move inline CSS to external file
- Increase inactive tab color contrast (#595959)

---

### Prerequisites (All Complete ✅)
- ✅ User profiles (Phase E)
- ✅ Follow system (Phase F)
- ✅ Email preferences system (Phase E Task 4)
- ✅ Notification infrastructure
- ✅ Profile pages with stats

---

## 📋 Phase H: Username System (PLANNED)

**Status:** 🔜 PLANNED (Not Started)
**Priority:** Medium
**Estimated Effort:** 1-2 weeks
**Prerequisites:** Phase G Complete ✅

---

### Overview

Comprehensive username system overhaul including:
1. Username selection during registration (currently auto-generated from first name)
2. Username editing with rate limits and validation
3. URL redirect system for changed usernames
4. Profanity and offensive content filtering

---

### Features Planned

#### 1. Username Selection on Signup

**Current State:** Username auto-generated from user's first name
**Desired State:** User chooses their own username during registration

**Requirements:**
- Username field on registration form
- Real-time availability checking (AJAX)
- Uniqueness validation
- Profanity filter integration
- Format rules: 3-30 characters, alphanumeric + underscores only

---

#### 2. Username Editing

**Rules:**
- Maximum 2 username changes per week (rate limiting)
- Changes tracked in `UsernameHistory` model
- Profanity filter blocks offensive names
- User warned about SEO/branding implications before change

**Blocked Content:**
- Profanity (use existing `profanity_filter.py` service)
- Offensive terms
- Demonic/occult references
- Impersonation attempts (admin, moderator, support, etc.)

---

#### 3. URL Redirect System

**Database Model:**
```python
class UsernameHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='username_history')
    old_username = models.CharField(max_length=150, db_index=True)
    new_username = models.CharField(max_length=150)
    changed_at = models.DateTimeField(auto_now_add=True)
    redirect_active = models.BooleanField(default=True)
    grace_period_ends = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['old_username', 'redirect_active']),
        ]
```

**URL Handling Logic:**
```
User visits /users/<username>/

1. Check if username exists in User model
   → YES: Show that user's profile
   → NO: Continue to step 2

2. Check UsernameHistory for old_username where redirect_active=True
   → FOUND: 301 redirect to new username URL
   → NOT FOUND: Return 404
```

**Scenarios:**

| Scenario | Old URL Behavior |
|----------|------------------|
| User "alice" → "alice_design", old name unclaimed | `/users/alice/` → 301 redirect → `/users/alice_design/` |
| User "alice" → "alice_design", then "bob" claims "alice" | `/users/alice/` → Shows bob's profile (redirect deactivated) |
| User changes name, within 3-day grace period | Old name reserved, redirect active |
| User changes name, after grace period | Old name available for others |

---

#### 4. SEO Considerations

**Implemented:**
- 301 redirects preserve link equity (SEO juice)
- Sitemap automatically updated (existing implementation)
- Canonical URLs point to current username

**User Warnings:**
- Modal confirmation before username change
- Explain: "Your old profile URL will redirect to your new one"
- Explain: "If someone else claims your old username, the redirect will stop"
- Explain: "External links and @mentions may break"

---

### Database Changes Required

**New Model:** `UsernameHistory` (as shown above)

**Modified Model:** `UserProfile`
```python
class UserProfile(models.Model):
    # ... existing fields ...
    username_changes_this_week = models.PositiveIntegerField(default=0)
    last_username_change = models.DateTimeField(null=True, blank=True)
```

---

### Implementation Phases

| Sub-Phase | Description | Effort |
|-----------|-------------|--------|
| H.1 | Username selection on signup | 2-3 hours |
| H.2 | Profanity filter integration for usernames | 1-2 hours |
| H.3 | UsernameHistory model + migrations | 2-3 hours |
| H.4 | Username edit form with rate limiting | 3-4 hours |
| H.5 | URL redirect middleware/view | 3-4 hours |
| H.6 | User warnings and confirmation UI | 2-3 hours |
| H.7 | Testing + edge cases | 3-4 hours |

**Total Estimated Effort:** 16-23 hours (1-2 weeks)

---

### Edge Cases to Handle

1. **User tries to change back to previous username**
   - Allow if within grace period and name not claimed
   - Count as one of their 2 weekly changes

2. **User deletes account**
   - Deactivate all redirects for their old usernames
   - Old usernames become available immediately

3. **Case sensitivity**
   - Usernames are case-insensitive for uniqueness
   - Display preserves user's chosen case
   - URLs are lowercase

4. **Reserved usernames**
   - Block: admin, administrator, moderator, support, help, api, www, etc.
   - Block: promptfinder, promptflow (brand protection)

5. **Username squatting**
   - Consider: Reclaim inactive usernames after 1+ year of no activity
   - Future consideration, not Phase H scope

---

### Technical Dependencies

- Existing `profanity_filter.py` service ✅
- Django caching (for rate limit tracking) ✅
- URL routing system ✅
- User authentication ✅

---

### Success Criteria

- [ ] Users can choose username during registration
- [ ] Users can change username (max 2x/week)
- [ ] Profanity filter blocks offensive usernames
- [ ] Old URLs redirect to new profile (301)
- [ ] Redirects deactivate when old name is claimed
- [ ] Admin can view username change history
- [ ] SEO preserved through proper redirects

---

### Notes

**Why rate limit to 2x/week?**
- Usernames are part of personal branding
- Followers/community recognize usernames
- Prevents abuse and confusion
- 2x/week allows corrections without encouraging constant changes

**Why 3-day grace period?**
- Gives time for user to notify followers of change
- Protects users from immediate username theft
- Short enough that usernames cycle back to availability quickly
- Balances user protection with username availability

---

## 🌟 Phase I: Inspiration Page & AI Generators (PLANNED)

**Status:** 🔜 PLANNED (Not Started)
**Priority:** Medium
**Estimated Effort:** 2-3 weeks
**Prerequisites:** Phase H Complete (or can run in parallel)

---

### Overview

Transform the current `/ai/{generator}/` pages into a comprehensive "Inspiration" hub with:
1. Unified inspiration landing page at `/inspiration/`
2. Enhanced AI generator category pages
3. Curated collections and trending prompts
4. Advanced filtering and discovery features

---

### Architectural Decisions

#### 1. URL Structure

**Current State:**
- `/ai/midjourney/` - AI generator category pages
- No unified browsing experience

**Proposed Structure:**
```
/inspiration/                    → Main hub page (NEW)
/inspiration/generators/         → All AI generators listing (NEW)
/inspiration/ai/{generator}/     → Individual generator pages (MIGRATED)
/inspiration/collections/        → Curated collections (NEW)
/inspiration/trending/           → Trending prompts (NEW)
```

**URL Migration Strategy:**
- 301 redirects from `/ai/{generator}/` → `/inspiration/ai/{generator}/`
- Maintain SEO equity through permanent redirects
- Update all internal links to new URLs
- Sitemap regeneration after migration

---

#### 2. AI Generators Expansion

**Current Generators (11):**
- Midjourney, DALL-E 3, DALL-E 2, Stable Diffusion
- Leonardo AI, Flux, Sora, Sora 2
- Veo 3, Adobe Firefly, Bing Image Creator

**Proposed Additions (Investigation Required):**
| Generator | Type | Priority | Notes |
|-----------|------|----------|-------|
| Ideogram | Image | High | Popular for text rendering |
| Playground AI | Image | Medium | Growing community |
| Canva AI | Image | Medium | Enterprise market |
| Kaiber | Video | High | Popular video AI |
| Pika Labs | Video | High | Text-to-video |
| Runway Gen-2/3 | Video | High | Leading video AI |
| Haiper | Video | Medium | Emerging competitor |
| Luma Dream Machine | Video | Medium | Newer entrant |

**Action Items:**
- [ ] Research each generator's user base and community
- [ ] Evaluate SEO keyword volume for each
- [ ] Determine official links/affiliate opportunities
- [ ] Create generator metadata (logo, description, official URL)

---

#### 3. Design Reference

**Pexels Inspiration Model:**
- Clean, minimal design aesthetic
- Large hero images/videos
- Infinite scroll or pagination
- Filtering by type, color, orientation
- "Explore" navigation pattern

**Key UI Elements:**
- Generator showcase cards with logo and sample count
- Trending section with engagement metrics
- Featured collections by theme
- Quick filter chips (Images/Videos/All)
- Sort options (Trending/New/Popular)

---

### Feature Requirements

#### Phase I.1: Inspiration Landing Page

**URL:** `/inspiration/`

**Components:**
1. **Hero Section**
   - Rotating featured prompt showcase
   - "Discover AI Art Prompts" heading
   - Search bar with auto-suggest

2. **Generator Showcase**
   - Grid of all AI generators
   - Each card shows: Logo, name, prompt count
   - "View All Generators" link

3. **Trending Section**
   - Top 12 trending prompts (24hr)
   - Mix of images and videos
   - Engagement indicators (views, likes)

4. **Collections Preview**
   - 3-4 featured curated collections
   - "Explore All Collections" link

5. **By Category**
   - Top tags/categories with counts
   - Quick navigation to filtered views

---

#### Phase I.2: Enhanced Generator Pages

**URL:** `/inspiration/ai/{generator}/`

**Improvements Over Current:**
1. **Generator Hero**
   - Official logo (requires sourcing)
   - Description (what it's known for)
   - Link to official site (affiliate if available)
   - Stats: Total prompts, this week's additions

2. **Advanced Filtering**
   - Type: Images / Videos
   - Time: Today / Week / Month / All Time
   - Sort: Trending / New / Popular
   - Orientation: Portrait / Landscape / Square (images only)

3. **Showcase Grid**
   - Masonry layout (existing)
   - Lazy loading
   - View count badges (existing from Phase G)
   - Quick-like functionality

4. **SEO Enhancement**
   - Expanded meta descriptions (150-160 chars)
   - FAQ schema for common questions
   - Breadcrumb schema
   - Generator-specific long-form content (300+ words)

---

#### Phase I.3: Curated Collections

**URL:** `/inspiration/collections/`

**Collection Types:**
1. **Staff Picks** - Manually curated by admins
2. **Trending This Week** - Auto-generated from metrics
3. **Theme Collections** - "Cyberpunk", "Nature", "Portraits", etc.
4. **Community Favorites** - Top liked prompts

**Database Model (NEW):**
```python
class Collection(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(max_length=500)
    cover_image = CloudinaryField('image', blank=True)
    prompts = models.ManyToManyField('Prompt', related_name='collections')
    is_auto_generated = models.BooleanField(default=False)
    auto_criteria = models.JSONField(null=True, blank=True)  # For auto-gen rules
    is_featured = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-updated_at']
```

---

#### Phase I.4: Trending & Discovery

**URL:** `/inspiration/trending/`

**Features:**
1. **Time Period Selector**
   - Today (24hr)
   - This Week
   - This Month
   - All Time

2. **Metric Toggles**
   - Most Viewed
   - Most Liked
   - Most Commented
   - Fastest Rising (velocity algorithm)

3. **Category Breakdown**
   - Trending in each top-level tag
   - Trending per AI generator

---

### Implementation Phases

| Sub-Phase | Description | Effort | Dependencies |
|-----------|-------------|--------|--------------|
| I.1 | URL migration with 301 redirects | 2-3 hours | None |
| I.2 | Inspiration landing page design | 4-6 hours | I.1 |
| I.3 | Inspiration landing page implementation | 6-8 hours | I.2 |
| I.4 | Generator page enhancements | 4-6 hours | I.1 |
| I.5 | Collection model + admin | 3-4 hours | None |
| I.6 | Collection pages + UI | 4-6 hours | I.5 |
| I.7 | Trending page implementation | 4-6 hours | Phase G.B (views) |
| I.8 | New AI generators research | 2-3 hours | None |
| I.9 | New AI generators implementation | 4-6 hours | I.8 |
| I.10 | SEO optimization pass | 3-4 hours | I.1-I.9 |
| I.11 | Testing + polish | 4-6 hours | All above |

**Total Estimated Effort:** 40-58 hours (2-3 weeks)

---

### Investigation Required

Before implementation, research needed for:

1. **AI Generator Logos**
   - Can we use official logos? (trademark considerations)
   - Alternative: AI-generated placeholder graphics
   - Check each generator's brand guidelines

2. **Affiliate Programs**
   - Midjourney affiliate program?
   - Adobe Firefly affiliate?
   - Leonardo AI affiliate?
   - Research commission structures

3. **Content Requirements**
   - Long-form content for each generator page
   - FAQ content for schema markup
   - Collection descriptions

4. **Performance Impact**
   - Collections query complexity
   - Caching strategy for trending
   - CDN considerations for new pages

---

### Database Changes Required

**New Models:**
- `Collection` (as defined above)

**Modified Models:**
- `Prompt`: Add `collections` M2M through relationship

**Migrations:**
- Create Collection model
- Add M2M relationship to Prompt

---

### SEO Considerations

**Keyword Targets:**
- "[Generator] prompts" (e.g., "Midjourney prompts")
- "[Generator] examples"
- "AI art prompts"
- "AI image generator prompts"
- "[Theme] AI art" (e.g., "cyberpunk AI art")

**Schema Markup:**
- CollectionPage for inspiration landing
- ItemList for generator pages
- FAQPage for generator-specific FAQs
- BreadcrumbList on all pages

**URL Migration Safety:**
- All old URLs 301 redirect
- Update sitemap.xml
- Submit URL changes to Google Search Console
- Monitor for 404 spikes

---

### Success Criteria

- [ ] `/inspiration/` landing page live and responsive
- [ ] All `/ai/` URLs redirect properly (301)
- [ ] At least 3 curated collections created
- [ ] Trending page shows accurate metrics
- [ ] All new generator pages have 300+ word descriptions
- [ ] Schema markup validated on all new pages
- [ ] Page load time < 2 seconds
- [ ] Mobile-responsive design verified
- [ ] No SEO traffic loss 30 days post-migration

---

### Deferred Items (Future Consideration)

1. **User-Created Collections** - Allow users to create/share collections (Premium feature)
2. **Collection Following** - Notification when collection updated
3. **AI Generator Comparisons** - Side-by-side prompt comparisons
4. **Prompt Challenges** - Community challenges with themes
5. **Generator Reviews** - User ratings/reviews of AI generators

#### UI/UX Features Deferred (December 2025 UI Redesign)

6. **Horizontal Tag Pills on Generator Pages** - Tag pills that scroll horizontally for quick filtering by popular tags. Deferred due to design complexity and need for user research on which tags to surface per generator.

7. **Applied Filters Row** - Visual row showing currently applied filters with "X" remove buttons. Deferred as current UI adequately shows filter state via dropdown selections and active tab highlighting.

---

### Notes

**Why "Inspiration" vs "Explore"?**
- "Inspiration" aligns better with creative intent
- Pexels uses this terminology successfully
- Differentiates from generic "Browse" or "Explore"
- Better SEO for "AI art inspiration" keywords

**Why migrate URLs?**
- Current `/ai/` is too short/generic
- `/inspiration/ai/` provides context
- Allows expansion to non-generator content
- Better information architecture

**Risk Assessment:**
- URL migration has SEO risk (mitigated by 301 redirects)
- Content expansion requires writing effort
- Generator logos may require legal review
- Timeline depends on content creation speed

---

## 📊 Phase I Pre-Implementation Research (COMPLETE)

**Research Date:** December 11, 2025
**Status:** ✅ Complete - Ready for Implementation
**Total Documentation:** 11 files (~277 KB)

---

### Research Summary

Comprehensive pre-implementation research was completed covering 5 critical areas. This section summarizes key findings; detailed analysis is in the referenced documents.

---

### 1. Keyword Research & SEO Strategy

**Document:** `docs/SEO_KEYWORD_RESEARCH_2025.md` (33 KB)
**Quick Reference:** `docs/KEYWORD_PRIORITY_QUICK_REFERENCE.md` (17 KB)

#### Tier 1 Keywords (High Volume, Target First)

| Keyword | Est. Monthly Volume | Competition | Priority |
|---------|---------------------|-------------|----------|
| Midjourney prompts | 20K-50K | High | High |
| DALL-E 3 prompts | 10K-30K | Medium-High | High |
| Stable Diffusion prompts | 15K-40K | Medium | High |
| AI art prompts | 10K-25K | Medium | High |
| AI image prompts | 5K-15K | Medium | High |

#### Tier 2 Keywords (Long-Tail, Quick Wins)

| Keyword Pattern | Est. Volume | Competition | Timeline |
|-----------------|-------------|-------------|----------|
| "[Style] + [Generator] prompts" | 500-2K | Low | 3-4 weeks |
| "[Subject] + AI prompts" | 300-1K | Low | 2-3 weeks |
| "Best prompts for [Generator]" | 1K-3K | Medium-Low | 4-6 weeks |

**Examples:** "Cyberpunk Midjourney prompts", "Portrait DALL-E prompts", "Fantasy Stable Diffusion prompts"

#### Tier 3 Keywords (Emerging - First Mover Advantage)

| Keyword | Current Volume | Growth Potential | Competition |
|---------|----------------|------------------|-------------|
| Sora prompts | 50-500 | 10x by 2026 | Very Low |
| Veo prompts | Minimal | High (Google backing) | Almost None |
| Flux prompts | Minimal | Growing | Very Low |

#### SEO Projections

| Timeline | Expected Organic Traffic |
|----------|--------------------------|
| Month 3 | 100-300 visits/day |
| Month 6 | 300-700 visits/day |
| Month 12 | 1,000-2,000+ visits/day |

**Key Insight:** Target Tier 2 long-tail keywords first for quick wins, then build authority for Tier 1 terms.

---

### 2. Competitor Analysis

**7 Major Competitors Analyzed**

| Platform | Model | Monthly Traffic | Strength | Weakness |
|----------|-------|-----------------|----------|----------|
| PromptBase | Marketplace | 500K+ | 230K+ prompts, payments | No community |
| PromptHero | Community | 1M+ | Social features | Weak payments |
| Lexica.art | Database | 2M+ | 5M+ images | SD only |
| Civitai | Community | 3M+ | 1M+ users | Model-focused |
| OpenArt.ai | Tool | 500K+ | Good UX | No marketplace |
| AIPRM | Extension | 1M+ | 2M+ users | Browser-only |
| FlowGPT | Free | 500K+ | No barriers | No revenue |

#### Content Gaps (PromptFinder Opportunities)

| Gap | Opportunity | Priority |
|-----|-------------|----------|
| **Emerging Generators** | Almost no coverage for Sora, Flux, Veo, Leonardo AI | High |
| **Video Prompts** | <5K searches now → 50K+ by 2026 | High |
| **Educational Content** | No comprehensive prompt engineering guides | Medium |
| **Use-Case Organization** | No cross-generator organization by use case | Medium |
| **Community Features** | All platforms have weak social features | Low (Phase G covers) |

#### PromptFinder Competitive Advantages

- ✅ 11 generators (most complete coverage including video)
- ✅ 209 tags across 21 categories (most granular)
- ✅ Community features (Phase G complete)
- ✅ Strong SEO infrastructure
- ✅ Video support (Sora, Sora 2, Veo 3)

---

### 3. AI Generators - Current & Future

#### Current Generators (11)

| Generator | Type | Priority | Affiliate Available |
|-----------|------|----------|---------------------|
| Midjourney | Image | Tier 1 | Contact directly |
| DALL-E 3 | Image | Tier 1 | No (OpenAI) |
| DALL-E 2 | Image | Tier 2 | No (OpenAI) |
| Stable Diffusion | Image | Tier 1 | No (open source) |
| Leonardo AI | Image | Tier 1 | ✅ Yes (60%) |
| Adobe Firefly | Image | Tier 1 | ✅ Yes (85%) |
| Flux | Image | Tier 2 | Unknown |
| Bing Image Creator | Image | Tier 3 | Conditional |
| Sora | Video | Tier 1 | No (OpenAI) |
| Sora 2 | Video | Tier 1 | No (OpenAI) |
| Veo 3 | Video | Tier 1 | No (Google) |

#### Future Generators to Add (8 Suggested)

| Generator | Type | Priority | Rationale |
|-----------|------|----------|-----------|
| Ideogram | Image | High | Strong text rendering, growing fast |
| Runway Gen-2/3 | Video | High | Industry standard for video |
| Pika Labs | Video | High | Popular, has affiliate (30%) |
| Kaiber | Video | High | Music video focus, unique niche |
| Playground AI | Image | Medium | Good free tier, growing |
| Canva AI | Image | Medium | Massive user base |
| Haiper | Video | Medium | Emerging player |
| Luma Dream Machine | Video | Medium | 3D/video hybrid |

**Note:** Adding these 8 generators would give PromptFinder 19 total - likely the most comprehensive coverage of any platform.

---

### 4. Logo & Trademark Permissions

**Recommendation:** Use text-only approach with custom icons

| Approach | Risk Level | Recommendation |
|----------|------------|----------------|
| Official logos | High | ❌ Avoid - most require permission |
| "Powered by" badges | Medium | ⚠️ Only if API customer |
| Text references | Low | ✅ Safe with trademark symbols |
| Custom icons | None | ✅ Best approach |

#### Safe Phrasing

- ✅ "Prompts for Midjourney™"
- ✅ "Compatible with DALL-E"
- ✅ "Works with Stable Diffusion"
- ❌ Do NOT use official logos without permission

#### Required Disclaimer (Add to Footer)

```
"All product names, logos, and brands are property of their respective owners.
PromptFinder is not affiliated with or endorsed by any AI generator company."
```

**Action Items:**
- [ ] Design custom category icons for each generator
- [ ] Add trademark disclaimer to footer
- [ ] Contact Leonardo AI, Flux, Runway for permission (optional)

---

### 5. Affiliate Program Opportunities

**Document:** `docs/AFFILIATE_PROGRAMS_RESEARCH.md` (19 KB)

#### Active Programs (Apply Now)

| Program | Commission | Cookie | Est. Monthly Revenue (10K users) |
|---------|------------|--------|----------------------------------|
| Leonardo AI | 60% first month | 30 days | $1,800-7,500 |
| Adobe Creative Cloud | 85% first month | 30 days | $1,700-3,400 |
| Pika | 30% recurring | Unknown | $450-2,250 |

#### Revenue Projections

| User Base | Conservative | Optimistic |
|-----------|--------------|------------|
| 1,000 users | $400-1,300/mo | $800-2,600/mo |
| 10,000 users | $3,950-13,150/mo | $7,900-26,300/mo |
| 50,000 users | $19,750-65,750/mo | $39,500-131,500/mo |

#### Application Priority

1. **Week 1:** Leonardo AI (60% commission, 5-10 day approval)
2. **Week 1:** Adobe Creative Cloud (85% commission)
3. **Week 2:** Contact Midjourney directly
4. **Week 3-4:** Pika, Runway

#### Programs Without Direct Affiliate

| Platform | Alternative Monetization |
|----------|--------------------------|
| OpenAI/DALL-E | Partnership form only |
| Google Veo | Enterprise deals |
| Stability AI | Licensing |
| Midjourney | Contact directly (may have private program) |

---

### 6. 301 Redirect Migration Protocol

**Document:** `docs/301_REDIRECT_MIGRATION_PROTOCOL.md` (58 KB)
**Quick Start:** `docs/REDIRECT_IMPLEMENTATION_QUICK_START.md` (15 KB)
**Test Script:** `scripts/redirect_verification_suite.sh`

#### Migration Map

| Old URL | New URL |
|---------|---------|
| `/ai/midjourney/` | `/inspiration/ai/midjourney/` |
| `/ai/dalle3/` | `/inspiration/ai/dalle3/` |
| `/ai/dalle2/` | `/inspiration/ai/dalle2/` |
| `/ai/stable-diffusion/` | `/inspiration/ai/stable-diffusion/` |
| `/ai/leonardo-ai/` | `/inspiration/ai/leonardo-ai/` |
| `/ai/flux/` | `/inspiration/ai/flux/` |
| `/ai/sora/` | `/inspiration/ai/sora/` |
| `/ai/sora2/` | `/inspiration/ai/sora2/` |
| `/ai/veo-3/` | `/inspiration/ai/veo-3/` |
| `/ai/adobe-firefly/` | `/inspiration/ai/adobe-firefly/` |
| `/ai/bing-image-creator/` | `/inspiration/ai/bing-image-creator/` |

#### Implementation (4 Lines of Code)

```python
# prompts/urls.py
from django.views.generic import RedirectView

path('ai/<slug:generator>/', RedirectView.as_view(
    url='/inspiration/ai/%(generator)s/',
    permanent=True  # 301 redirect
)),
```

#### Risk Assessment

| Factor | Assessment |
|--------|------------|
| Downtime | Zero |
| Rollback Time | <5 minutes |
| SEO Impact | Minimal (301 preserves equity) |
| Overall Risk | **LOW** |

#### Post-Migration Monitoring (8 Weeks)

| Week | Expected | Monitor |
|------|----------|---------|
| 1-2 | 10-20% traffic dip | Crawl errors, 404s |
| 3-4 | Stabilization | Average position |
| 5-8 | 80%+ recovery | Organic traffic |

---

### SEO Quick Reference (Use for All Future Development)

**Reference this section when building any user-facing feature.**

#### Content Guidelines

| Guideline | Requirement |
|-----------|-------------|
| Minimum page word count | 1,500-2,000 words for landing pages |
| Meta description length | 150-160 characters |
| Title tag length | 50-60 characters |
| H1 tags | One per page, include primary keyword |
| Image alt text | Descriptive, include keywords naturally |
| Internal links | 3-5 relevant links per page |

#### URL Structure

| Page Type | Format | Example |
|-----------|--------|---------|
| Generator page | `/inspiration/ai/{generator}/` | `/inspiration/ai/midjourney/` |
| Prompt detail | `/prompt/{slug}/` | `/prompt/cyberpunk-city-neon/` |
| User profile | `/@{username}/` | `/@artcreator/` |
| Collection | `/collections/{slug}/` | `/collections/fantasy-art/` |
| Tag page | `/tags/{tag}/` | `/tags/cyberpunk/` |

#### Schema Markup Checklist

| Page Type | Required Schema |
|-----------|-----------------|
| Homepage | WebSite, Organization |
| Generator pages | CollectionPage, BreadcrumbList |
| Prompt detail | Article, ImageObject, BreadcrumbList |
| User profile | ProfilePage, Person |
| Search results | SearchResultsPage |

#### Keyword Targeting by Page

| Page | Primary Keyword | Secondary Keywords |
|------|-----------------|-------------------|
| `/inspiration/ai/midjourney/` | "Midjourney prompts" | "MJ prompts", "Midjourney examples" |
| `/inspiration/ai/dalle3/` | "DALL-E 3 prompts" | "DALL-E examples", "OpenAI prompts" |
| `/inspiration/ai/sora/` | "Sora prompts" | "Sora video prompts", "OpenAI Sora" |
| `/inspiration/` | "AI art inspiration" | "AI prompts", "prompt ideas" |

---

### Research Documents Index

| Document | Size | Purpose |
|----------|------|---------|
| `docs/KEYWORD_RESEARCH_START_HERE.md` | 17 KB | SEO quick start guide |
| `docs/SEO_KEYWORD_RESEARCH_2025.md` | 33 KB | Complete keyword analysis |
| `docs/KEYWORD_PRIORITY_QUICK_REFERENCE.md` | 17 KB | Priority matrix |
| `docs/KEYWORD_CONTENT_EXAMPLES.md` | 30 KB | Content templates |
| `docs/AFFILIATE_PROGRAMS_RESEARCH.md` | 19 KB | Revenue opportunities |
| `docs/301_REDIRECT_MIGRATION_PROTOCOL.md` | 58 KB | Migration protocol |
| `docs/REDIRECT_IMPLEMENTATION_QUICK_START.md` | 15 KB | 30-min implementation guide |
| `docs/REDIRECT_MIGRATION_SUMMARY.md` | 11 KB | Executive summary |
| `docs/REDIRECT_MIGRATION_INDEX.md` | 13 KB | Navigation index |
| `docs/SEO_ARCHITECTURE_REVIEW_PHASE_I.md` | ~50 KB | SEO architecture analysis |
| `scripts/redirect_verification_suite.sh` | 14 KB | Automated redirect testing |

**Total Research Documentation:** ~277 KB

---

### Action Items (Pre-Implementation)

**Immediate (Before Phase I.1):**
- [ ] Apply to Leonardo AI affiliate program
- [ ] Apply to Adobe Creative Cloud affiliate program
- [ ] Design custom generator icons (avoid trademark issues)
- [ ] Add trademark disclaimer to footer

**During Phase I:**
- [ ] Implement URL migration with 301 redirects
- [ ] Follow redirect testing protocol
- [ ] Monitor Search Console for 8 weeks post-migration

**Post-Phase I:**
- [ ] Contact Midjourney about affiliate program
- [ ] Evaluate adding 8 new generators
- [ ] Expand content depth on generator pages

---

## 🎨 Phase J: Prompt Detail Page Redesign (J.1, J.2, J.3 COMPLETE)

**Status:** ✅ PHASE J.1, J.2, J.3 COMPLETE (December 23, 2025)
**Priority:** HIGH - Core user experience improvement
**Effort:** 9 iterative rounds (J.1), + Session 20-21 (J.2, J.3), ~16 hours total
**Baseline Analysis:** `docs/PROMPT_DETAIL_ANALYSIS.md` (477 lines, completed Dec 18, 2025)
**Current Template:** `prompts/templates/prompts/prompt_detail.html` (470 lines after J.1)
**Agent Rating:** 8.7/10 average (@ui-ux-designer 7.5-9.5/10, @frontend-developer 9.0/10)

---

### Overview

Transform the prompt detail page from a functional but cluttered layout into a modern, PromptHero-inspired design that prioritizes the visual content while improving code maintainability. This redesign addresses the 6/10 maintainability score identified in Phase 0 analysis.

### Why This Redesign?

**Current Pain Points (from Phase 0 Analysis):**
- 63 lines of inline CSS (not cached separately)
- 325 lines of inline JavaScript (not minified/cached)
- Fixed 8/4 layout regardless of content type
- Action buttons clustered away from content
- Copy button buried in sidebar
- All comments loaded at once (no pagination)
- 6/10 maintainability score

**Target Improvements:**
- External CSS/JS for caching and maintainability
- 60/40 media-focused layout (PromptHero-inspired)
- Action buttons positioned near content
- Prominent copy functionality
- Comments below media (not in sidebar)
- 8+/10 maintainability score

---

### Design Decisions

#### 1. Layout Structure: 60/40 Two-Column

**Decision:** Media on left (60%), metadata/prompt on right (40%)

**Rationale:**
- Follows PromptHero's proven UX pattern
- Prioritizes the visual content (what users come for)
- Provides adequate space for prompt text without scrolling
- Better responsive collapse to single column on mobile

**Current vs Target:**
```
CURRENT (8/4 Bootstrap):
┌─────────────────────────────────────────────────────────────┐
│  col-lg-8 (66.7%)      │  col-lg-4 (33.3%)                  │
│  • Media               │  • Description                      │
│                        │  • Prompt Content + Copy            │
│                        │  • Metadata                         │
│                        │  • Tags                             │
└─────────────────────────────────────────────────────────────┘

TARGET (60/40):
┌─────────────────────────────────────────────────────────────┐
│  col-lg-7 (60%)        │  col-lg-5 (40%)                    │
│  • Media (larger)      │  • Title + Author                   │
│  • Action Bar          │  • Prompt Content + Copy            │
│                        │  • Description                      │
│                        │  • Metadata + Tags                  │
└─────────────────────────────────────────────────────────────┘
│                    Comments Section (Full Width)             │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Comments Placement: Below Media (Full Width)

**Decision:** Move comments from sidebar to full-width section below media

**Rationale:**
- Comments deserve more horizontal space for readability
- Sidebar was cramped for longer discussions
- Full-width allows better threading visualization
- Matches modern platform patterns (Instagram, ArtStation)
- Separates "content viewing" from "engagement" sections

#### 3. Action Buttons: Floating on Media

**Decision:** Position key actions (Like, Copy, Share) as floating overlay on media

**Rationale:**
- Immediate access without scrolling
- PromptHero-inspired pattern
- Visual hierarchy emphasizes actions
- Works for both image and video content

#### 4. Copy Button: Prominent Position

**Decision:** Large, visible copy button near prompt content (not buried)

**Rationale:**
- Core user action (copying the prompt)
- Should be 1-click accessible
- Visual feedback on copy (checkmark animation)
- PromptHero places this prominently

---

### Target Layout Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                         HEADER BAR                                   │
│  [← Back to Browse]              [Edit] [Delete] [Report]           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│  │                             │  │  TITLE                       │  │
│  │                             │  │  by @author • Dec 18, 2025   │  │
│  │                             │  │                              │  │
│  │     MEDIA CONTAINER         │  │  ─────────────────────────   │  │
│  │     (60% width)             │  │                              │  │
│  │                             │  │  THE PROMPT                  │  │
│  │     [Image or Video]        │  │  "A cyberpunk cityscape..."  │  │
│  │                             │  │                              │  │
│  │                             │  │  [📋 Copy Prompt]            │  │
│  │  ┌─────────────────────┐   │  │                              │  │
│  │  │ ♡ 42  💬 5  👁 128  │   │  │  ─────────────────────────   │  │
│  │  └─────────────────────┘   │  │                              │  │
│  └─────────────────────────────┘  │  DESCRIPTION                 │  │
│                                   │  This prompt creates...      │  │
│                                   │                              │  │
│                                   │  ─────────────────────────   │  │
│                                   │                              │  │
│                                   │  AI Generator: Midjourney    │  │
│                                   │  Type: Image                 │  │
│                                   │                              │  │
│                                   │  Tags: #cyberpunk #neon      │  │
│                                   │        #cityscape            │  │
│                                   └─────────────────────────────┘  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                         COMMENTS SECTION                             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  💬 Comments (5)                            [Write a comment]  │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │  @user1 • 2 hours ago                                         │  │
│  │  "This is amazing! What settings did you use?"                │  │
│  │                                                [Reply] [Like]  │  │
│  ├───────────────────────────────────────────────────────────────┤  │
│  │  @author • 1 hour ago                                         │  │
│  │  "Thanks! I used stylize 750 and chaos 20"                    │  │
│  │                                                [Reply] [Like]  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│                         [Load More Comments]                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Implementation Phases

#### Phase 0: Baseline Analysis ✅ COMPLETE

**Status:** ✅ Complete (December 18, 2025)
**Document:** `docs/PROMPT_DETAIL_ANALYSIS.md`

**Deliverables:**
- ✅ Template structure analysis (819 lines mapped)
- ✅ CSS inventory (63 lines inline, external dependencies identified)
- ✅ JavaScript inventory (325 lines, 8+ functions documented)
- ✅ Context variables documented (7 variables from view)
- ✅ Mobile responsiveness assessment
- ✅ Complexity metrics (6/10 maintainability)
- ✅ Redesign recommendations

---

#### Phase 0.5: Code Quality Improvements ✅ COMPLETE

**Status:** ✅ Complete (December 19, 2025)
**Commits:** 3 commits (avatar signals, simple_timesince, liked button CSS)

**Deliverables:**

**1. Avatar Signal Refactoring (prompts/signals.py)**
- Refactored pre_save/post_save signal handlers for UserProfile avatar changes
- Added `AvatarChangeLog` model for audit trail tracking
- Tracks avatar uploads, replacements, and deletion failures
- Cloudinary cleanup happens in post_save (prevents data loss on save failure)
- Comprehensive logging with emoji indicators (✅ success, ⚠️ warning, ❌ error)

**2. simple_timesince Template Filter (prompts/templatetags/prompt_tags.py)**
- Refactored `simple_timesince` filter to reduce cyclomatic complexity below Flake8 C901 threshold
- Uses lookup table pattern (`_TIME_THRESHOLDS`, `_DAY_THRESHOLDS`) instead of nested if/elif
- Extracted helper functions: `_get_time_unit()`, `_format_time_string()`
- Returns human-readable relative times: "Just now", "5 minutes ago", "Yesterday", "2 weeks ago"

**3. CSS Variables Enhancement (static/css/style.css)**
- Added `--color-liked: #e0245e` (Twitter-style liked heart color)
- Consistent heart color across all like buttons
- Part of CSS variable standardization effort

**Files Modified:**
- `prompts/signals.py` - Avatar signal handlers + AvatarChangeLog
- `prompts/models.py` - AvatarChangeLog model
- `prompts/templatetags/prompt_tags.py` - simple_timesince refactor
- `static/css/style.css` - CSS variables

---

#### Phase J.1: Complete UI Overhaul ✅ COMPLETE

**Status:** ✅ Complete (December 19-20, 2025)
**Commits:** 22 commits (7da0651 through e68bb91)
**Rounds:** 9 iterative refinement rounds
**Agent Rating:** 8.7/10 average

**Major Accomplishments:**

**1. Hero Section Redesign**
- Hero video styling matched to hero-image (rounded corners, shadows)
- Video thumbnails with play button overlay
- Consistent aspect ratios and sizing

**2. Author Section Restructure**
- Proper views row placement (after follow button, before actions)
- Follow button with dynamic state styling
- CSS variable integration for tag styling

**3. Layout & Spacing Improvements**
- Consistent padding and alignment across components
- Removed unused CSS variables (--light-blue cleanup)
- Proper margin and gap standardization

**4. Comments Section Relocation**
- Mobile-responsive comments relocation using CSS flexbox ordering
- Comments appear after media content on mobile (order: 2)
- Right rail appears last on mobile (order: 3)
- WCAG 1.3.2 compliant (visual order matches logical reading flow)

**5. Mobile Responsiveness**
- Full-width columns on tablet/mobile (≤991.98px)
- Proper spacing with CSS variable fallbacks
- Touch-friendly interaction targets

**Key Files Created/Modified:**
- `static/css/pages/prompt-detail.css` - Page-specific styles (1,063 lines)
- `prompts/templates/prompts/prompt_detail.html` - Template restructure
- `static/css/style.css` - Global variable additions

**Agent Validation (Session 19):**
| Agent | Rating | Key Feedback |
|-------|--------|--------------|
| @ui-ux-designer | 7.5/10 | Recommended swapping comment/right rail order |
| @frontend-developer | 9.0/10 | Clean CSS architecture, proper variable usage |
| **Average** | **8.7/10** | Production ready with implemented recommendations |

---

#### Phase 1-3: ✅ MERGED INTO PHASE J.1

**Status:** ✅ Complete (merged into Phase J.1)
**Original Scope:** CSS extraction, JS extraction, layout restructure

These phases were consolidated into the iterative Phase J.1 approach, which proved more efficient for the interconnected changes required.

---

#### Phase 5: Action Bar Implementation (1-2 hours)

**Status:** 📋 Planned
**Goal:** Create floating action bar on media

**Tasks:**
- [ ] Design action bar component (like, views, comments count)
- [ ] Position as overlay on media container
- [ ] Implement hover/focus states
- [ ] Ensure accessibility (keyboard navigation, ARIA labels)
- [ ] Handle video controls conflict

**Files to Modify:**
- `prompts/templates/prompts/prompt_detail.html`
- `static/css/pages/prompt-detail.css`
- `static/js/prompt-detail.js`

**Success Criteria:**
- Action bar visible on media
- Doesn't interfere with video controls
- Accessible via keyboard
- Responsive positioning

---

#### Phase 6: Copy Button Enhancement (1 hour)

**Status:** 📋 Planned
**Goal:** Make copy button prominent and add feedback

**Tasks:**
- [ ] Redesign copy button (larger, more visible)
- [ ] Add copy success animation (checkmark)
- [ ] Add tooltip feedback ("Copied!")
- [ ] Position near prompt content (not buried)

**Files to Modify:**
- `prompts/templates/prompts/prompt_detail.html`
- `static/css/pages/prompt-detail.css`
- `static/js/prompt-detail.js`

**Success Criteria:**
- Copy button immediately visible
- Visual feedback on click
- Works on all browsers
- Accessible

---

#### Phase 7: Header & Navigation Polish (1 hour)

**Status:** 📋 Planned
**Goal:** Clean header with clear navigation

**Tasks:**
- [ ] Add "Back to Browse" link
- [ ] Reorganize edit/delete/report buttons
- [ ] Ensure breadcrumb integration
- [ ] Polish title and author display

**Files to Modify:**
- `prompts/templates/prompts/prompt_detail.html`
- `static/css/pages/prompt-detail.css`

**Success Criteria:**
- Clear navigation back
- Logical button placement
- Professional header appearance

---

#### Phase 8: Testing & Polish (1-2 hours)

**Status:** 📋 Planned
**Goal:** Comprehensive testing and final adjustments

**Tasks:**
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile testing (iOS Safari, Android Chrome)
- [ ] Accessibility audit (WAVE, axe)
- [ ] Performance check (Lighthouse)
- [ ] Visual regression comparison
- [ ] Agent validation (@code-reviewer, @ui-ux-designer)

**Success Criteria:**
- No visual regressions
- Lighthouse score ≥90
- WCAG AA compliance
- Agent ratings 8+/10

---

### Features to Preserve

**From Phase 0 Analysis - Must Keep Working:**

| Feature | Location | Notes |
|---------|----------|-------|
| Like button AJAX | Header actions | Toggle with optimistic UI |
| Copy to clipboard | Sidebar | With fallback for older browsers |
| Delete confirmation | Modal | Dynamic title/message |
| Report modal | Modal | AJAX submission |
| Comment edit toggle | Comment list | Inline edit form |
| Comment form validation | Comment section | Character counter |
| Video autoplay/loop | Media container | With controls |
| Draft mode banner | Top of page | For unpublished prompts |
| Owner-only controls | Header | Edit/Delete buttons |
| View count badge | Header | Conditional visibility |

---

### Features to Add

**PromptHero-Inspired Improvements:**

| Feature | Priority | Phase |
|---------|----------|-------|
| Floating action bar on media | High | Phase 5 |
| Prominent copy button | High | Phase 6 |
| Full-width comments | High | Phase 4 |
| Copy success animation | Medium | Phase 6 |
| Back to browse link | Medium | Phase 7 |
| Improved mobile layout | Medium | Phase 8 |

---

### Future Features Backlog

**Deferred to Future Phases (Not in Scope):**

| Feature | Complexity | Notes |
|---------|------------|-------|
| Image lightbox/zoom | Medium | Click to enlarge |
| Related prompts section | Medium | Same tags/author |
| Comment pagination | Low | Load more pattern |
| Comment threading | High | Reply nesting |
| Social sharing buttons | Low | Twitter, Pinterest |
| Prompt versioning | High | Edit history |
| Download button | Low | High-res download |
| Favorite/bookmark | Medium | Save to collection |

**📋 For comprehensive planning with timelines and priority tiers, see: [Future Features Roadmap](#-future-features-roadmap)**

---

### Technical Dependencies

**Required Before Starting:**
- Phase 0 analysis complete ✅
- CSS Cleanup Phase 1 patterns established ✅
- External JS patterns from navbar extraction ✅

**Files That Will Change:**
- `prompts/templates/prompts/prompt_detail.html` (major)
- `static/css/pages/prompt-detail.css` (new)
- `static/js/prompt-detail.js` (new)
- `prompts/views/prompt_views.py` (minor, if context changes)

**No Changes Required:**
- Database models (no schema changes)
- URL patterns (same routes)
- View logic (same context variables)

---

### Agent Validation Requirements

**Per Phase Completion:**
- Minimum 2 agents per phase
- Required: @code-reviewer (8+/10)
- Recommended: @ui-ux-designer for visual phases
- Recommended: @frontend-developer for JS phases

**Final Phase 8:**
- @code-reviewer: Code quality
- @ui-ux-designer: Visual design
- @frontend-developer: JS implementation
- @security-auditor: If any user input handling changes
- **Average required: 8+/10**

---

### Success Metrics

**Quantitative:**
- [ ] Maintainability score: 6/10 → 8+/10
- [ ] Inline CSS: 63 lines → 0 lines
- [ ] Inline JS: 325 lines → 0 lines
- [ ] Lighthouse Performance: ≥90
- [ ] Lighthouse Accessibility: ≥90

**Qualitative:**
- [ ] PromptHero-inspired visual appearance
- [ ] Improved user experience for copying prompts
- [ ] Better mobile experience
- [ ] Cleaner codebase for future maintenance

---

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CSS extraction breaks styling | Medium | High | Test each element, use browser dev tools |
| JS extraction breaks functionality | Medium | High | Test each feature individually |
| Layout change affects mobile | Low | Medium | Test responsive breakpoints |
| Comment relocation breaks AJAX | Low | High | Update selectors carefully |

---

### Reference Documents

- **Baseline Analysis:** `docs/PROMPT_DETAIL_ANALYSIS.md` (477 lines)
- **Current Template:** `prompts/templates/prompts/prompt_detail.html` (818 lines)
- **View Function:** `prompts/views/prompt_views.py` (lines 303-561)
- **CSS Patterns:** `static/css/navbar.css` (extraction reference)
- **JS Patterns:** `static/js/navbar.js` (extraction reference)

---

## 🗂️ Phase K: Collections Feature

**Status:** ⏸️ ON HOLD (95% complete - paused for Phase L priority)
**Started:** December 25, 2025
**Paused:** December 29, 2025
**Resume After:** Phase L completion
**Priority:** HIGH - Competitive advantage feature
**Estimated Effort:** 2-3 weeks
**Competitive Advantage:** PromptHero (main competitor) does NOT have this feature!
**Approach:** Micro-Spec Methodology (adopted Session 24)

### Why Paused

Phase L (Media Infrastructure Migration) has been prioritized due to:
1. **Cost Savings:** Cloudinary costs will exceed budget at scale
2. **Performance:** B2 + Cloudflare offers better global CDN performance
3. **Foundation:** Media infrastructure affects all future features
4. **Risk Mitigation:** Better to migrate before large content library exists

---

### Development Approach: Micro-Specs

**Why:** Comprehensive specs (1000+ lines) were repeatedly ignored by CC, resulting in broken code with 9.2/10 ratings.

**Solution:** Break into micro-specs with:
- One file per spec maximum
- ~10-50 lines of code per spec
- Explicit "DO NOT" lists
- User manual verification before next spec
- No CC self-verification trusted

---

### Progress Tracking

#### Completed Micro-Specs ✅

**UI Foundation (Phase K.1):**
- **Micro-Spec #1:** Save button on prompt detail page ✅
- **Micro-Spec #2:** Save button on prompt cards (positioned right of heart) ✅
- **Micro-Spec #2.5:** Save button hover effect + Modal CSS scaffolding ✅

**Backend Infrastructure (Phase K.2):**
- **Micro-Spec #3:** Collection + CollectionItem models ✅
- **Micro-Spec #3.5:** Model enhancements (deleted_by, indexes) ✅
- **Micro-Spec #5a:** Old migration cleanup ✅
- **Micro-Spec #5b:** Fresh migration with correct fields ✅
- **Micro-Spec #4:** Admin registration (CollectionAdmin, CollectionItemAdmin) ✅

**Modal Core (Phase K.3):**
- **Micro-Spec #6:** Modal HTML template ✅
- **Micro-Spec #7:** Include modal in base.html ✅
- **Micro-Spec #8:** Modal JavaScript (open/close) ✅
- **Debug Fix:** Script tag placement issue resolved ✅
- **CSS Foundation:** 284 lines of modal CSS added ✅

**Modal Polish (Session 28):**
- **Micro-Spec #9.1-#9.11:** Complete modal functionality ✅
  - API integration, toggle actions, create form
  - Real-time validation with Levenshtein distance
  - Staggered animations, thumbnail grids
  - Optimistic UI updates, success states

**Profile Tab (Session 29):**
- **Micro-Spec #11:** Collections profile tab page ✅
  - Created `collections_profile.html` template (812 lines)
  - Added `user_collections` view with sorting
  - Route: `/users/<username>/collections/`
  - Collections tab link in user profile nav

**Profile Tab Polish (Session 29 continued):**
- **Micro-Spec #11.1:** Investigation report for collections_profile.html issues ✅
- **Micro-Spec #11.2:** Added Member since + social icons to header ✅
- **Micro-Spec #11.3:** Fixed Create button styling (btn-outline-standard) ✅
- **Micro-Spec #11.4:** Empty state messaging improvements ✅
- **Micro-Spec #11.5:** Pagination backend integration ✅
- **Micro-Spec #11.6:** Load More JavaScript fetch pattern ✅
- **Micro-Spec #11.7:** Grid layout CSS fixes (minmax for proper sizing) ✅
- **Micro-Spec #11.8:** Style.css consolidation + Load More button styling ✅

#### Remaining Micro-Specs ❌
- **Collection Detail Page:** Individual collection view
- **Edit Collection:** Modal for editing title/visibility
- **Delete Collection:** Soft delete to trash

---

### Overview

Collections allow users to save prompts into organized folders they create, increasing user investment and engagement with "dwelling-style" features. This is a key differentiator from PromptHero.

### User Flow

1. **Save Button Trigger:** User clicks bookmark icon on prompt card or detail page
2. **Collections Modal:** Shows existing collections + "Create new collection" option
3. **Add to Collection:** Click collection thumbnail to add (shows checkmark overlay)
4. **Remove from Collection:** Click again to remove (shows minus overlay with red)
5. **Create New Collection:** Sub-modal with name input + public/private toggle
6. **Collections Page:** User profile tab showing all collections

---

### Phase Breakdown

#### Phase K.1: MVP Collections (Priority) - ~85% Complete
- ✅ Save button on prompt cards and detail page
- ✅ Collections CSS scaffolding
- ✅ Collection and CollectionItem models (with deleted_by, indexes)
- ✅ Database migration (0039_add_collection_models.py)
- ✅ Admin registration (CollectionAdmin, CollectionItemAdmin)
- ✅ Collections modal HTML template
- ✅ Modal JavaScript (open/close functionality)
- ✅ Modal CSS (284 lines - backdrop, grid, cards, states)
- ✅ Collections API endpoints (list, create, add, remove)
- ✅ JavaScript wired to API (complete modal functionality)
- ✅ Collections profile tab (`/users/<username>/collections/`)
- ✅ Profile tab polish (header, sorting, pagination, Load More)
- ❌ Individual collection detail page
- ❌ Edit collection modal
- ❌ Delete collection (soft delete)

#### Phase K.2: Enhanced Features
- Download tracking + "Your Downloads" virtual collection
- "Your Likes" virtual collection
- Edit collection modal
- Delete collection (soft delete → trash)
- Share collection link

#### Phase K.3: Premium Features
- Collection limits enforcement
- Private collection limits (2 free, unlimited paid)
- Upgrade prompts/upsell UI

---

### Database Models

```python
class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    title = models.CharField(max_length=50)
    slug = models.CharField(max_length=60, unique=True)  # title-slug + random suffix
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete for trash
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']

class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['collection', 'prompt']
        ordering = ['-added_at']

# NEW: Download Tracking for "Your Downloads" virtual collection
class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'prompt']  # One record per user-prompt pair
```

---

### UI Components

#### 1. Collections Modal (Main)
- **Layout:** 4 columns desktop, 3 tablet, 2 mobile
- **Header:** "Add to collection(s)" with soft grey X close button
- **Grid Items:** "Create new collection" card (+ icon, grey border) + existing collections
- **Footer:** "Your collections →" button (dark style like generator CTA)

#### 2. Collection Thumbnail Preview Rules
- **3+ items:** Left column = most recent (tall), right column = 2nd & 3rd (stacked)
- **2 items:** 50/50 split width
- **1 item:** Full width cropped thumbnail

#### 3. Collection Card Structure
- Thumbnail preview area (rounded corners)
- Below thumbnail: Two columns
  - Left (~80%): Collection title (max 35 chars displayed, ellipsis overflow)
  - Right (~20%): Public/Private eye icon

#### 4. Overlay States
- **Already in collection:** Accent color overlay + circle-check icon
- **Hover to remove:** Red overlay + circle-minus icon
- **Hover to add:** Accent color overlay + plus icon

#### 5. Create Collection Sub-Modal
- Back arrow (←) to return to main modal
- "Collection name" input (50 char limit)
- Public/Private radio buttons (Public default)
- "Back" button + "Create new collection" button (disabled until 1+ char entered)

#### 6. Collections Profile Page
- URL: `/@{username}/collections/`
- Same thumbnail grid style as modal (but larger)
- Sort dropdown: "Recency" | "A-Z"
- Each card shows: thumbnail + title + item count + public/private icon

#### 7. Individual Collection Page
- URL: `/@{username}/collections/{collection-slug-xxxxx}/`
- Header: Collection name, item count (X photos / Y videos)
- "Edit collection" button + "Share" button
- Standard prompt grid with save button overlay on each item

#### 8. Edit Collection Modal
- Title input (50 char max)
- "Make the collection private" checkbox
- "Update Collection" + "Delete" buttons

---

### System Collections (Virtual)

These are NOT stored as Collection objects - they're virtual/computed:
- **Your Likes** - All prompts user has liked
- **Your Downloads** - All prompts user has downloaded (requires download tracking)

---

### Premium Tier Strategy

| Feature | Free | Mid Tier | Top Tier |
|---------|------|----------|----------|
| Collections limit | 10 | 30 | Unlimited |
| Private collections | 2 | Unlimited | Unlimited |
| Items per collection | Unlimited | Unlimited | Unlimited |
| Collaboration | ❌ | ❌ | Future |

**Upsell Triggers:**
1. When user hits 10 collections → "Upgrade for more collections"
2. When user tries 3rd private collection → "Upgrade to make more collections private"
3. Show upgrade prompt in modal when limits reached

---

### URL Structure

**Format:** Slugified name + 5-char random suffix for uniqueness

```
/@username/collections/                      # Collections list page
/@username/collections/headshots-x7k2m/      # Individual collection
```

**Why:**
- Human-readable (keywords in URL)
- Unique (random suffix prevents collisions)
- User can rename without breaking links
- SEO-friendly if we decide to index

---

### SEO Strategy

**Recommendation: NO indexing by default (simplest)**

Reasons:
- Can't trust user-entered titles/descriptions
- Collections are disposable (users delete anytime)
- AI-generated descriptions add complexity
- Low SEO value vs effort

**If deleted:** 301 redirect to `/@username/collections/`

---

### New Icons (Phase K)

11 new icons added to `static/icons/sprite.svg`:

| Icon ID | Purpose |
|---------|---------|
| `icon-bookmark` | Save button (outline) |
| `icon-bookmark-filled` | Saved state |
| `icon-circle-check` | Already in collection |
| `icon-circle-minus` | Remove from collection |
| `icon-eye` | Public collection |
| `icon-eye-off` | Private collection |
| `icon-x` | Soft close button |
| `icon-arrow-left` | Back navigation |
| `icon-arrow-right` | Forward navigation |
| `icon-download` | Download button |
| `icon-share` | Share/copy link |

---

### Technical Dependencies

**Required Before Starting:**
- Phase J complete ✅
- SVG icon system established ✅
- Modal patterns from existing UI ✅

**Files That Will Change/Create:**

**New Files:**
- `prompts/models/collection.py` - Collection, CollectionItem models
- `prompts/models/download.py` - Download model
- `prompts/views/collection_views.py` - Collection CRUD views
- `prompts/templates/prompts/collections_modal.html` - Modal template
- `prompts/templates/prompts/collection_list.html` - Collections page
- `prompts/templates/prompts/collection_detail.html` - Single collection page
- `static/js/collections.js` - Collection modal JavaScript
- `static/css/components/collections.css` - Collection-specific styles

**Modified Files:**
- `prompts/models/__init__.py` - Import new models
- `prompts/urls.py` - Add collection routes
- `prompts/templates/prompts/prompt_card.html` - Add save button
- `prompts/templates/prompts/prompt_detail.html` - Add save button
- `prompts/templates/prompts/user_profile.html` - Add collections tab
- `static/icons/sprite.svg` - Add 11 new icons ✅ DONE
- `prompts/admin.py` - Add Collection admin

---

### Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Default visibility | Public | Users must opt-in to private |
| Collection name limit | 50 chars stored, 35 displayed | Balance between expressiveness and UI |
| Empty state text | "{First name} has no collections yet 😔" | Friendly, personal |
| Delete behavior | Soft delete → trash | Consistent with prompts |
| Modal columns | 4 desktop, 3 tablet, 2 mobile | Responsive grid |
| URL structure | slug + 5-char random suffix | SEO + uniqueness |
| SEO indexing | No indexing | Low value, high complexity |

---

### Future Enhancements (Not MVP)

- Collaboration on collections
- Following other users' collections
- AI-generated collection descriptions (if SEO becomes priority)
- Collection covers (custom thumbnails)
- Collection categories/tags

See also: [Future Features Roadmap](#-future-features-roadmap) for comprehensive planning.

---

## 🚀 Phase L: Media Infrastructure Migration (~98% COMPLETE)

**Status:** ✅ L1-L8, L8-DIRECT, L8-STEP2-PERF, L5e, VARIANT-FIXES COMPLETE | Remaining: L11
**Started:** December 2025
**Priority:** CRITICAL - Cost and performance foundation
**Estimated Effort:** 3-4 weeks
**Cost Impact:** ~70% reduction in media hosting costs at scale
**Agent Rating:** 8.9/10 average (L6d: 8.85/10, L6f: 9.0/10, L7: 9.2/10, L8-DIRECT: 8.4/10)

---

### Overview

Migrate from Cloudinary to Backblaze B2 + Cloudflare for media storage and delivery. This migration addresses cost scalability concerns and provides better CDN performance globally.

---

### Completed Micro-Specs (December 2025)

| Spec | Description | Status | Files |
|------|-------------|--------|-------|
| L1.1 | B2 Storage Backend | ✅ Complete | `prompts/storage_backends.py` |
| L1.2 | CDN URL Generation | ✅ Complete | `prompts/storage_backends.py` |
| L3 | Image Optimization (Pillow) | ✅ Complete | `prompts/services/image_processor.py` |
| L4 | B2 Upload Service | ✅ Complete | `prompts/services/b2_upload_service.py` |
| L5a | Model Fields (5 B2 URL fields) | ✅ Complete | `prompts/models.py` |
| L5b | Upload API Endpoint | ✅ Complete | `prompts/views/api_views.py` |
| L5c | Upload Form Integration | ✅ Complete | `prompts/templates/prompts/upload_step2.html` |
| L5d | Template Updates (6 templates) | ✅ Complete | Multiple templates |
| L6 | Video Handling (B2 URLs + Templates) | ✅ Complete | `prompts/services/video_processor.py`, templates |
| L7 | Responsive Images (srcset/sizes) | ✅ Complete | `_prompt_card.html`, templates |
| L8 | Quick Mode Upload Optimization | ✅ Complete | `image_processor.py`, `b2_upload_service.py`, `api_views.py` |
| L8-DIRECT | Direct Browser-to-B2 Uploads | ✅ Complete | `b2_presign_service.py`, `api_views.py`, `upload_step1.html` |
| L8-TIMEOUT | Upload Timeout Handling | ✅ Complete | `cloudinary_moderation.py`, `content_generation.py`, `constants.py` |
| L8-STEP2-PERF | Deferred AI Suggestions (AJAX) | ✅ Complete | `api_views.py`, `content_generation.py`, `upload_step2.html` |
| L5e-TEMPLATE | Edit Form B2-First Image Display | ✅ Complete | `prompts/templates/prompts/prompt_edit.html` |
| L5e-VIEW | Edit Form B2 Upload Logic | ✅ Complete | `prompts/views/prompt_views.py` |

---

### New B2 URL Fields (Prompt Model)

```python
# Image fields - Added in migration 0040/0041
b2_image_url = models.URLField(max_length=500, blank=True, null=True)
b2_thumb_url = models.URLField(max_length=500, blank=True, null=True)     # 300x300
b2_medium_url = models.URLField(max_length=500, blank=True, null=True)    # 600x600
b2_large_url = models.URLField(max_length=500, blank=True, null=True)     # 1200x1200
b2_webp_url = models.URLField(max_length=500, blank=True, null=True)      # WebP format

# Video fields - Added in L6 (Session 32)
b2_video_url = models.URLField(max_length=500, blank=True, null=True)     # Original video
b2_video_thumb_url = models.URLField(max_length=500, blank=True, null=True)  # Video thumbnail
```

---

### API Endpoints

**POST /api/upload/b2/**
- Rate limited: 20 requests/hour per user
- Authentication: Required
- Accepts: multipart/form-data with image file
- Returns: JSON with all B2 URLs (original, thumb, medium, large, webp)
- Validates: File type, file size (10MB max)

**POST /api/upload/b2/variants/** (L8 Quick Mode)
- Rate limited: 20 requests/hour per user
- Authentication: Required
- Purpose: Background variant generation after quick upload
- Reads image from session (`pending_variant_image` base64)
- Generates: medium (600x600), large (1200x1200), WebP variants
- Stores URLs in session (`variant_urls`)
- Returns: JSON with variant URLs

**GET /api/upload/b2/variants/status/** (L8 Quick Mode)
- Authentication: Required
- Purpose: Poll for variant generation completion
- Returns: `{"complete": true/false, "urls": {...}}`
- Session keys: `variants_complete`, `variant_urls`

**GET /api/upload/b2/presign/** (L8-DIRECT)
- Authentication: Required
- Rate limited: 20 requests/hour per user
- Purpose: Generate presigned URL for direct browser-to-B2 upload
- Query params: `content_type`, `content_length`, `filename`
- Returns: `{"success": true, "presigned_url": "...", "file_key": "..."}`
- Validates: Content type (image/video), file size limits

**POST /api/upload/b2/complete/** (L8-DIRECT)
- Authentication: Required
- Rate limited: 20 requests/hour per user
- Purpose: Notify server that direct B2 upload is complete
- Body: `{"quick": true/false}` (images use quick mode for deferred variants)
- Session retrieval: Uses `b2_pending_upload` session data
- Returns: `{"success": true, "urls": {...}, "variants_pending": true/false}`

**GET /api/upload/ai-suggestions/** (L8-STEP2-PERF)
- Authentication: Required
- Rate limited: 20 requests/hour per user
- Purpose: Deferred AI content suggestions for Step 2 page
- Reads image URL from session (`b2_secure_url` or `cloudinary_secure_url`)
- Calls `ContentGenerationService.analyze_image_only()` for image-only analysis
- Returns: `{"success": true, "title": "...", "description": "...", "suggested_tags": [...]}`
- Fallback: Returns empty suggestions on timeout/error (non-blocking)

---

### B2 Environment Variables

```bash
# Required for B2 integration
B2_APPLICATION_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_application_key
B2_BUCKET_NAME=your_bucket_name
B2_REGION=us-west-002  # or your region

# Cloudflare CDN (optional, for production)
CLOUDFLARE_CDN_DOMAIN=media.promptfinder.net
```

---

### Template B2-First Pattern

All templates now use B2-first with Cloudinary fallback:
```django
{% if prompt.display_medium_url %}
    <img src="{{ prompt.display_medium_url }}" ...>
{% elif prompt.featured_image %}
    <img src="{{ prompt.featured_image.url }}" ...>
{% else %}
    <img src="{% static 'images/placeholder-prompt.svg' %}" ...>
{% endif %}
```

**Templates Updated (6 templates with B2-first pattern):**
1. `_prompt_card.html` - Homepage cards
2. `prompt_temporarily_unavailable.html` - Soft-deleted prompts
3. `prompt_gone.html` - Permanently deleted prompts
4. `prompt_list.html` - Main prompt listing
5. `trash_bin.html` - Trash view
6. `user_profile.html` - Profile prompts

---

### Image Processing Pipeline

```
Upload → Pillow Processing → B2 Storage → Cloudflare CDN
                ↓
    ┌───────────┼───────────┬───────────┐
    ↓           ↓           ↓           ↓
 Original   Thumbnail    Medium      Large      WebP
 (as-is)    (300x300)   (600x600)  (1200x1200) (optimized)
```

---

### Why This Migration

| Factor | Cloudinary | B2 + Cloudflare | Winner |
|--------|------------|-----------------|--------|
| Storage Cost (100GB) | $45/mo | $0.50/mo | B2 |
| Bandwidth Cost (500GB) | $45/mo | $0 (Cloudflare) | B2 |
| Image Transforms | Built-in | Pillow (server-side) | Tie |
| Video Transcoding | Built-in | Custom (FFmpeg) | Cloudinary |
| Global CDN | Yes | Yes (better) | Cloudflare |
| Setup Complexity | Low | Medium | Cloudinary |

**Projected Savings at Scale:**
- 1,000 users: $50/mo → $15/mo (70% savings)
- 10,000 users: $500/mo → $100/mo (80% savings)
- 50,000 users: $2,500/mo → $300/mo (88% savings)

---

### Remaining Phase L Features (1 remaining)

#### L10: SEO Review Infrastructure ✅ COMPLETE (Session 40)
- ✅ L10a: `needs_seo_review` model field + `ai_failed` API flag
- ✅ L10b: Silent AI failure UX (users oblivious to failures)
- ✅ L10c: Admin SEO Review Queue at `/admin/seo-review/`
- ✅ L10b-FIX: Hide all AI failure UI indicators from users
- ✅ L10b-FIX3: Remove API key exposure from error messages
- ✅ L10b-FIX4: Hide content notice banner for processing errors
- See: [L10 SEO Review Infrastructure](#l10-seo-review-infrastructure-session-40) below

#### L11: Documentation & Cleanup (PARTIAL)
- ✅ Update CLAUDE.md with new architecture
- ✅ Update PROJECT_FILE_STRUCTURE.md
- ❌ Remove Cloudinary dependencies after validation
- ❌ Document troubleshooting procedures
- Estimated: 2 hours

---

### Cloudinary Transition Strategy

**Decision Date:** January 9, 2026
**Status:** ✅ FINALIZED

**Architecture Decision:**
Cloudinary remains installed as a **read-only fallback** for existing prompts. All new uploads go exclusively to B2.

| Scenario | Storage | Display |
|----------|---------|---------|
| New uploads (Jan 2026+) | B2 only | B2 URLs via Cloudflare CDN |
| Existing prompts (pre-Jan 2026) | Cloudinary | Cloudinary URLs (legacy) |
| Edit existing prompt (new image) | B2 only | B2 URLs |
| Template fallback | N/A | `b2_url|default:cloudinary_url` |

**Why Keep Cloudinary (Read-Only):**
1. **Zero migration risk** - Existing prompts continue working
2. **No data migration needed** - Cloudinary URLs remain valid
3. **Gradual transition** - Old content naturally ages out or gets updated
4. **Cost-efficient** - No storage growth on Cloudinary (new uploads to B2)

**Template Pattern (Already Implemented):**
```django
{% if prompt.b2_medium_url %}
    <img src="{{ prompt.b2_medium_url }}" ...>
{% elif prompt.featured_image %}
    <img src="{{ prompt.featured_image.url }}" ...>
{% endif %}
```

---

### Cloudinary → B2 Migration Plan (Post-Launch)

**Timeline:** Q2 2026 (after stable launch)
**Priority:** Low - only if Cloudinary costs become significant

**Migration Approach (When Needed):**

| Phase | Description | Effort |
|-------|-------------|--------|
| 1. Inventory | Count prompts with Cloudinary-only images | 1 hour |
| 2. Script | Create batch migration script | 4-6 hours |
| 3. Test | Migrate 100 prompts in staging | 2 hours |
| 4. Execute | Batch migrate all legacy prompts | 4-8 hours |
| 5. Verify | Confirm all B2 URLs working | 2 hours |
| 6. Cleanup | Remove Cloudinary package (optional) | 1 hour |

**Migration Script Pseudocode:**
```python
# management/commands/migrate_cloudinary_to_b2.py
for prompt in Prompt.objects.filter(b2_image_url__isnull=True, featured_image__isnull=False):
    # Download from Cloudinary
    image_data = download_cloudinary_image(prompt.featured_image.url)

    # Upload to B2 with variants
    b2_urls = b2_upload_service.process_upload(image_data, prompt.slug)

    # Update prompt
    prompt.b2_image_url = b2_urls['original']
    prompt.b2_thumb_url = b2_urls['thumb']
    prompt.b2_medium_url = b2_urls['medium']
    prompt.b2_large_url = b2_urls['large']
    prompt.b2_webp_url = b2_urls['webp']
    prompt.save()
```

**Trigger for Migration:**
- Cloudinary costs exceed $50/month
- OR Cloudinary announces pricing changes
- OR We want to fully deprecate Cloudinary dependency

---

### L10 Scope Decision (January 9, 2026)

**Original L10 Spec:** "Fallback System - Automatic failover if B2 unavailable"

**Decision:** Defer automatic B2 failover. Instead, implement:

| Feature | Priority | Effort | Description |
|---------|----------|--------|-------------|
| AI Fallback + SEO Review Queue | High | 4-6 hours | When AI times out, save as draft with "Needs SEO Review" flag |
| Health Endpoint | Medium | 1-2 hours | `/api/health/` for monitoring |
| NSFW Failure → Draft Mode | High | ✅ Complete | Moderation timeout = draft, not rejection |

**Why Defer B2 Failover:**
1. B2 has 99.9% uptime SLA
2. Cloudflare CDN provides edge caching
3. Failover complexity not justified by risk
4. Focus on user-impacting features first

**L10 Revised Scope:**

```python
# L10a: AI Fallback + SEO Review Queue
class Prompt(models.Model):
    needs_seo_review = models.BooleanField(default=False)
    ai_generation_failed = models.BooleanField(default=False)

# L10b: Health Endpoint
# GET /api/health/
{
    "status": "healthy",
    "b2": "connected",
    "database": "connected",
    "timestamp": "2026-01-09T12:00:00Z"
}

# L10c: NSFW Failure → Draft Mode (Already Implemented)
# Timeout/error in moderation → status=0 (draft), requires_manual_review=True
```

---

### L10 SEO Review Infrastructure (Session 40) ✅ COMPLETE

**Status:** ✅ COMPLETE (January 9, 2026)
**Session:** 40
**Commits:** 8 commits (e572254, 59959cb, 7a6e365, b5a0860, 8bf4be6, fbddaf5, dcfcba3, 9236e26)
**Philosophy:** Silent failure pattern - users never see AI failure indicators

---

#### Overview

L10 implements a "silent failure" pattern where AI failures are invisible to users. When OpenAI Vision times out or fails, uploads succeed normally but are flagged for admin SEO review. Users see no error messages, broken UI elements, or indications of AI issues.

---

#### L10a: Model Field + API Flag ✅

**Prompt Model Field:**
```python
needs_seo_review = models.BooleanField(default=False)
```

**API Response Flag:**
```json
// GET /api/upload/ai-suggestions/
{
    "success": true,
    "title": "Untitled Upload",
    "description": "",
    "suggested_tags": [],
    "ai_failed": true  // Frontend ignores this, just populates defaults
}
```

**Migration:** `0042_prompt_needs_seo_review.py`

---

#### L10b: Silent AI Failure UX ✅

**Principle:** Users remain oblivious to AI failures. No error toasts, no warning banners, no "AI unavailable" messages.

| Fix | Commit | Description |
|-----|--------|-------------|
| L10b-FIX | b5a0860 | Improve AI failure UX - hide error details, show subtle message |
| L10b-FIX2 | 8bf4be6 | Remove all AI failure UI indicators for seamless UX |
| L10b-FIX3 | fbddaf5 | Remove API key exposure from user-facing error messages |
| L10b-FIX4 | dcfcba3 | Hide content notice banner for processing errors |

**Key Changes:**
- `upload_step2.html`: AI suggestion errors populate empty defaults silently
- `api_views.py`: Error responses use generic messages, no API key/config details
- Content notice banner: Hidden when `ai_failed=true` (no "AI couldn't analyze" messages)

**Security Fix (L10b-FIX3):**
- Removed `OPENAI_API_KEY` substring exposure from error messages
- Generic error: "AI suggestions unavailable" vs detailed API errors

---

#### L10c: Admin SEO Review Queue ✅

**Status:** Complete (January 9, 2026)

**Commits:**
- `9236e26` - L10c: Add Admin SEO Review Queue
- `cd838b5` - L10c-FIX: SEO Review Queue UX improvements (button styling, admin link)
- `7b43ef8` - L10c-FIX2: Fix admin index URL error (NoReverseMatch fix)

**Routes:**

| URL | View | Purpose |
|-----|------|---------|
| `/admin/seo-review/` | `seo_review_queue` | List prompts needing SEO review |
| `/admin/seo-complete/<id>/` | `mark_seo_complete` | Mark prompt as SEO-reviewed |

**Template:** `templates/admin/seo_review_queue.html`

**Workflow:**
```
AI Failure → needs_seo_review=True → Admin Queue → Manual Review → Mark Complete
```

**Admin Queue Features:**
- Lists all prompts where `needs_seo_review=True`
- Shows: title, author, created date, status
- Edit/View/Done action buttons with WCAG AA compliant styling
- Staff-only access (`@staff_member_required`)
- Link added to Django admin dashboard index

**Known Issue (Intentional):**
The "Content Moderation System" banner on the admin dashboard links to `/admin/moderation-dashboard/` which does not exist yet. This is intentionally left broken as a reminder to build the Content Moderation Dashboard in a future phase. See [Content Moderation Dashboard (Planned)](#content-moderation-dashboard-planned) section.

---

### Video Transcoding Decision (January 9, 2026)

**Decision:** Self-hosted FFmpeg (Phase M), NOT Cloudinary Video API

| Factor | Cloudinary Video | Self-Hosted FFmpeg | Winner |
|--------|------------------|-------------------|--------|
| Cost per video | $0.05-0.15 | $0 (Heroku dyno time) | FFmpeg |
| Processing time | 10-30s | 30-90s | Cloudinary |
| Quality control | Limited presets | Full control | FFmpeg |
| Dependency | External API | Local binary | FFmpeg |
| Complexity | Low | Medium | Cloudinary |

**Why FFmpeg:**
1. **Cost:** Video uploads are less frequent; dyno time is already paid
2. **Control:** Full control over compression, codec, thumbnail extraction
3. **No API dependency:** No external service rate limits or outages
4. **Already in stack:** FFmpeg used for frame extraction (existing)

**Phase M Implementation:**
- Video validation (duration, size, format)
- Frame extraction for AI moderation (5 frames)
- Thumbnail generation (multiple sizes)
- Optional: HLS/DASH for adaptive streaming (future)

**Cloudinary Video Use Case (If Any):**
- Only for complex transformations we can't do with FFmpeg
- Currently: None identified

---

### Future Phases Reference

**Phase L Completion Criteria:**
- ✅ L1-L8: Core B2 infrastructure (COMPLETE)
- ✅ L8-DIRECT: Direct browser uploads (COMPLETE)
- ✅ L10: AI Fallback + SEO Review Queue (COMPLETE)
- ⏸️ L10d: Health Endpoint - deferred for Phase M
- ⏸️ L11: Documentation cleanup - deferred for Phase M

**Decision (January 9, 2026):** L10d and L11 deferred to prioritize Phase M (Video Functionality) for MVP launch.

**Post-Phase L:**
- **Phase M:** Video Handling (FFmpeg-based) - 2-3 weeks
- **Phase K.2:** Collections enhancements - Resume after L complete
- **Phase N:** Premium tier + payments - After K.2

**Dependencies Chart:**
```
Phase L (Media Infrastructure)
    └── Phase M (Video Handling) - requires L complete
    └── Phase K.2 (Collections) - can resume after L
         └── Phase N (Premium) - requires K.2
```

---

### Recently Completed (Session 32)

#### L6: Video Handling ✅ COMPLETE (Agent Rating: 9.0/10)
**Completed:** December 2025

| Sub-spec | Description | Status |
|----------|-------------|--------|
| L6a | Add B2 video URL fields to Prompt model | ✅ Complete |
| L6b | Add display properties (display_video_url, display_video_thumb_url) | ✅ Complete |
| L6c | Update video_processor.py for B2 | ✅ Complete |
| L6d | Update _prompt_card.html video handling | ✅ Complete (8.85/10) |
| L6e | Update prompt_detail.html video handling | ✅ Complete |
| L6f | Update upload_views.py for video B2 URLs | ✅ Complete (9.0/10) |

**Key Changes:**
- Added `b2_video_url` and `b2_video_thumb_url` fields to Prompt model
- Templates use B2-first pattern: `{{ prompt.display_video_url|default:prompt.get_video_url }}`
- Video thumbnails use responsive srcset with B2 fallback
- Session-based upload stores B2 video URLs before prompt creation

#### L7: Responsive Images ✅ COMPLETE (Agent Rating: 9.2/10)
**Completed:** December 2025

**Implementation:**
- Added `srcset` and `sizes` attributes to all prompt card images
- Responsive breakpoints: 300w (thumb), 600w (medium)
- LCP optimization with `fetchpriority="high"` for first image
- Lazy loading (`loading="lazy"`) for below-fold images
- Template pattern: `sizes="(max-width: 500px) 100vw, (max-width: 800px) 50vw, (max-width: 1100px) 33vw, 25vw"`

**Files Updated:**
- `_prompt_card.html` - Homepage masonry cards
- `collection_detail.html` - Collection page cards
- `trash_bin.html` - Trash view cards

---

### Recently Completed (Session 33)

#### L8: Quick Mode Upload Optimization ✅ CODE COMPLETE
**Completed:** December 31, 2025

**Problem Solved:**
- Full image processing (4 variants + WebP) took 2.4 seconds
- Users experienced slow uploads affecting UX

**Solution Implemented:**
- Added `thumbnail_sizes` parameter to `process_upload()` function
- Quick mode generates only thumbnail (300x300) during initial upload
- Variants (medium, large, WebP) generated in background via AJAX

**Performance Improvement:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Processing time | 2.4s | 0.12s | **95% faster** |
| Thumbnail only | N/A | 0.12s | Instant preview |
| Variants (background) | N/A | 0.38s | Non-blocking |

**Files Modified:**
- `prompts/services/image_processor.py` - Added `thumbnail_sizes` parameter
- `prompts/services/b2_upload_service.py` - Quick mode with `['thumb']` only
- `prompts/views/api_views.py` - Added variant generation endpoints
- `prompts/urls.py` - Added `/api/upload/b2/variants/` routes
- `prompts/templates/prompts/upload_step2.html` - Background variant polling

**New Session Keys (for deferred processing):**
- `pending_variant_image` - Base64 encoded image for variant generation
- `pending_variant_filename` - Original filename
- `variant_urls` - Generated variant URLs (medium, large, webp)
- `variants_complete` - Boolean flag for polling

**Agent Validation:**
- Backend: 78% processing improvement verified
- Code quality: Clean parameter-based approach
- Session handling: Proper base64 encoding for image storage

**Blocker Discovered:**
Despite 95% faster processing, total upload time is still ~23 seconds due to network latency (Browser → Heroku → B2 double hop). See L8-DIRECT requirement below.

---

### Current Blockers (Session 39) - ALL CRITICAL ISSUES RESOLVED

| Blocker | Impact | Status | Notes |
|---------|--------|--------|-------|
| ~~Network latency (23s uploads)~~ | ~~User experience~~ | ✅ RESOLVED | L8-DIRECT implemented - now ~5-8s uploads |
| ~~Step 2 slow load (~8s)~~ | ~~User experience~~ | ✅ RESOLVED | L8-STEP2-PERF: AI calls now deferred via AJAX |
| ~~Variant generation race condition~~ | ~~Upload flow~~ | ✅ RESOLVED | Session 39: Fixed with URL params instead of session-based approach |
| ~~Variants not saving to DB~~ | ~~Upload flow~~ | ✅ RESOLVED | Session 39: Fixed session key retrieval in upload_submit() |
| ~~AI suggestions 500 error~~ | ~~Upload flow~~ | ✅ RESOLVED | Session 39: Fixed with base64 encoding for OpenAI Vision |
| Video uploads (95-225s) | User experience | 🟡 Expected | Synchronous FFmpeg processing; documented behavior |
| Masonry grid squares | Visual consistency | 🟢 Low | Images appear square instead of natural aspect ratio |

---

### Session 38-39 Critical Fixes (ALL RESOLVED ✅)

Three critical upload flow issues were discovered in Session 38 and fully resolved in Session 39:

#### Fix 1: Variant Race Condition ✅

**Problem:** `/api/upload/b2/variants/` returned 400 Bad Request because AJAX fired before session was set.

**Root Cause:** Step 1 redirected to Step 2 before the `complete/` endpoint finished setting session keys, causing variants endpoint to find no `pending_variant_image` in session.

**Solution:** Pass B2 URLs via URL parameters instead of relying on session timing.

**Code Changes:**

`upload_step1.html` - Pass thumb URL in redirect:
```javascript
const params = new URLSearchParams({
    resource_type: resourceType,
    b2_original: completeData.urls.original || '',
    b2_thumb: completeData.urls.thumb || ''  // ← Added
});
window.location.href = `{% url 'prompts:upload_step2' %}?${params.toString()}`;
```

`upload_step2.html` - Store in hidden fields and session:
```javascript
// Get from URL params on page load
const b2ThumbUrl = urlParams.get('b2_thumb') || '';
document.getElementById('b2_thumb_url').value = b2ThumbUrl;

// Store in session via view context
{% if b2_thumb_url %}
sessionStorage.setItem('b2_thumb_url', '{{ b2_thumb_url }}');
{% endif %}
```

**Agent Rating:** 9.0/10 (@code-reviewer)

---

#### Fix 2: Variants Not Saving to Database ✅

**Problem:** After upload completed, prompts had no variant URLs (medium, large, webp) in database.

**Root Cause:** `upload_submit()` view was looking for wrong session keys (`b2_medium_url`) when the AJAX endpoint stored them under `variant_urls` dict.

**Solution:** Check both session key patterns in `upload_submit()`:

**Code Changes:**

`upload_views.py`:
```python
# Check for variant URLs - could be individual keys OR in variant_urls dict
variant_urls = request.session.get('variant_urls', {})
b2_medium = request.session.get('b2_medium_url') or variant_urls.get('medium')
b2_large = request.session.get('b2_large_url') or variant_urls.get('large')
b2_webp = request.session.get('b2_webp_url') or variant_urls.get('webp')
```

**Agent Rating:** 8.5/10 (@django-pro)

---

#### Fix 3: AI Suggestions 500 Error ✅

**Problem:** `/api/upload/ai-suggestions/` returned 500 Internal Server Error with "Error downloading image" from OpenAI.

**Root Cause:** OpenAI Vision API couldn't download images from Backblaze B2 CDN URLs due to authentication/access issues.

**Solution:** Fetch image server-side and send as base64 data URL instead of external URL.

**Code Changes:**

`content_generation.py` - New `analyze_image_only()` method:
```python
def analyze_image_only(self, image_url: str) -> dict:
    """Analyze image and return suggestions. Fetches image as base64 for OpenAI."""
    try:
        # Fetch image and convert to base64
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image_data = base64.b64encode(response.content).decode('utf-8')
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        base64_url = f"data:{content_type};base64,{image_data}"

        # Send base64 data URL to OpenAI instead of external URL
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": self.ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": base64_url}}
                ]
            }],
            max_tokens=500
        )
        # ... parse response
```

**Agent Rating:** 9.2/10 (@backend-architect)

**L8-DIRECT: COMPLETE ✅**

Upload performance dramatically improved:
- **Before (L8 Quick Mode):** ~23s total (Browser → Heroku → B2 double hop)
- **After (L8-DIRECT):** ~5-8s total (Browser → B2 direct via presigned URL)
- **Improvement:** 70-80% faster uploads

**Architecture Change:**
```
BEFORE (double hop):
Browser → Heroku (5-7s) → B2 (15-18s) = ~23s total

AFTER (direct upload):
Browser → B2 (presigned URL, 5-8s) → Heroku (completion callback) = ~5-8s total
```

**Masonry Grid Issue:**
- Images in homepage masonry displaying as squares
- May be CSS `object-fit: cover` on `.masonry-item img`
- Related file: `static/css/components/masonry-grid.css`

---

### Deferred Phase L Features (Post-Launch)

#### L7b: Migration Script (DEFERRED)
- Create script to migrate existing Cloudinary assets to B2
- Implement batch processing with progress tracking
- Add rollback capability
- Estimated: 8 hours

#### L8-DIRECT: Direct Browser-to-B2 Upload ✅ COMPLETE (Session 34-35)
- **Status:** ✅ IMPLEMENTED (January 1, 2026)
- **Result:** 70-80% faster uploads (23s → 5-8s)
- **Implementation:**
  1. ✅ `b2_presign_service.py` - Presigned URL generation with CORS headers
  2. ✅ `api_views.py` - `/api/upload/b2/presign/` and `/api/upload/b2/complete/` endpoints
  3. ✅ `upload_step1.html` - JavaScript XHR for direct browser-to-B2 upload
  4. ✅ Session-based state management (`b2_pending_upload`)
  5. ✅ Deferred variant generation (variants created on Step 2)
- **Test Coverage:** 22 tests in `test_b2_presign.py`
- **Agent Rating:** 9.0/10 average

#### L8-TIMEOUT: Upload Timeout Handling ✅ COMPLETE
- **Status:** ✅ IMPLEMENTED (January 2, 2026)
- **Problem Solved:** OpenAI API calls could hang for 4+ minutes, blocking upload endpoint
- **Result:** 30-second hard timeout with graceful degradation
- **Implementation:**
  1. ✅ `prompts/constants.py` - Central `OPENAI_TIMEOUT = 30` constant
  2. ✅ `cloudinary_moderation.py` - Client timeout config + `APITimeoutError` handling
  3. ✅ `content_generation.py` - Client timeout config + `APITimeoutError` handling
  4. ✅ `upload_step1.html` - Progressive feedback (15s, 45s, 65s abort)
  5. ✅ `upload_step2.html` - `showWarningAlert()` for timeout warnings
  6. ✅ `api_views.py` - Rate limit documentation
  7. ✅ `upload_views.py` - Weekly limit documentation
- **Security Approach:** Content flagged as `pending_review` on timeout (NOT auto-approved)
- **Agent Rating:** 8.67/10 average (@frontend-developer 8.5, @backend-architect 9.0, @code-reviewer 8.5)
- **Full Report:** `docs/reports/L8_TIMEOUT_COMPLETION_REPORT.md`

#### L8-CDN: CDN Optimization (DEFERRED)
- Configure Cloudflare cache rules per content type
- Set up Polish (image optimization)
- Enable Argo (smart routing) if budget allows
- Estimated: 4 hours

#### L9: Monitoring & Analytics (DEFERRED)
- Set up Cloudflare Analytics dashboard
- Implement bandwidth tracking
- Add cache hit ratio monitoring
- Estimated: 3 hours

#### L10: Fallback System (PARTIAL - DEFERRED)
- ✅ Templates have B2-first with Cloudinary fallback
- ❌ Automatic failover if B2 unavailable
- ❌ Health check endpoints
- Estimated: 4 hours

---

### Technical Architecture

```
User Upload → Django → Presigned URL → B2 Bucket
                                          ↓
User Request → Cloudflare CDN ← ← ← ← ← ← ┘
                    ↓
              Cloudflare Images (transforms)
                    ↓
              Cached Response → User
```

---

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration data loss | Low | Critical | Dual-write during transition, backups |
| Performance regression | Medium | High | A/B testing, gradual rollout |
| Video transcoding issues | Medium | Medium | Keep Cloudinary for video initially |
| Cloudflare outage | Very Low | High | B2 direct access fallback |

---

### Success Criteria

- [ ] All existing media accessible via new infrastructure
- [ ] Upload latency < 2 seconds (p95)
- [ ] Image load time < 500ms (cached)
- [ ] Video streaming starts < 1 second
- [ ] Zero data loss during migration
- [ ] Cost reduction ≥ 60% at current scale

---

### Dependencies

- Backblaze B2 account (free tier available)
- Cloudflare account (free tier sufficient initially)
- FFmpeg for video processing
- django-storages library

---

## 🎬 Phase M: Video Handling (PLANNED)

**Status:** 🚧 IN PROGRESS - Core video upload working, enhancements planned
**Priority:** HIGH - Required for video upload functionality
**Estimated Effort:** 2-3 weeks
**Dependencies:** Phase L Media Infrastructure (~95% complete)
**Prerequisites:** L5e (Edit Form B2 Integration), L11 (Documentation & Cleanup)

---

### Overview

Phase M implements comprehensive video handling for the PromptFinder platform, including frame extraction, NSFW moderation, SEO content generation, thumbnail creation, and file validation. This phase builds on Phase L's B2 + Cloudflare infrastructure.

---

### Video Upload Flow

```
User Upload → Validation (M5) → Frame Extraction (M1) → NSFW Check (M2)
                                         ↓
                              Content Generation (M3)
                                         ↓
                              Thumbnail Creation (M4)
                                         ↓
                              SEO Naming (M6) → B2 Storage → Complete
```

---

### Micro-Specs

| Spec | Description | Status | Effort | Dependencies |
|------|-------------|--------|--------|--------------|
| M1 | Frame Extraction (FFmpeg) | 📋 Planned | 2-3 days | Phase L complete |
| M2 | Video NSFW Moderation | 📋 Planned | 3-4 days | M1 |
| M3 | SEO Content Generation | 📋 Planned | 2-3 days | M1 |
| M4 | Video Thumbnails | 📋 Planned | 1-2 days | M1 |
| M5 | File Restrictions + Video Dimensions | ✅ Complete | 1 day | None |
| M6 | SEO File Naming/Slug | 📋 Planned | 1-2 days | M3 |

---

### M1: Frame Extraction (FFmpeg)

**Purpose:** Extract representative frames from uploaded videos for AI analysis.

**Note:** These functions extend the existing `prompts/services/video_processor.py` created in Phase L6.

**Technical Implementation:**
```python
# prompts/services/video_processor.py (extend existing file)
import subprocess
import tempfile

def extract_frames(video_path: str, num_frames: int = 5) -> list[str]:
    """
    Extract evenly-spaced frames from video for analysis.

    Args:
        video_path: Path to video file
        num_frames: Number of frames to extract (default: 5)

    Returns:
        List of paths to extracted frame images
    """
    # Get video duration
    duration = get_video_duration(video_path)

    # Calculate timestamps for evenly-spaced frames
    timestamps = [duration * (i + 1) / (num_frames + 1) for i in range(num_frames)]

    frame_paths = []
    for i, ts in enumerate(timestamps):
        output_path = tempfile.mktemp(suffix=f'_frame_{i}.jpg')
        subprocess.run([
            'ffmpeg', '-ss', str(ts), '-i', video_path,
            '-frames:v', '1', '-q:v', '2', output_path
        ], check=True)
        frame_paths.append(output_path)

    return frame_paths
```

**Configuration (Updated Session 48):**
- `VIDEO_FRAME_COUNT = 3` - Number of frames to extract (reduced from 5)
- `VIDEO_FRAME_QUALITY = 2` - JPEG quality (2 = high quality)
- Frames extracted at **25%, 50%, 75%** of video duration
- **Rationale:** 3 frames provides good coverage while reducing API costs and processing time

**Files to Create/Modify:**
- `prompts/services/video_processor.py` - Frame extraction functions
- `prompts/constants.py` - Video processing constants

---

### M2: Video NSFW Moderation (OpenAI Vision API)

**Purpose:** Analyze extracted frames for NSFW content using OpenAI Vision API.

**Technical Implementation:**
```python
# prompts/services/video_moderation.py
from openai import OpenAI
import base64

def moderate_video_frames(frame_paths: list[str]) -> dict:
    """
    Analyze video frames for NSFW content.

    Args:
        frame_paths: List of paths to extracted frames

    Returns:
        Moderation result with status and confidence
    """
    client = OpenAI()

    # Encode frames as base64
    images = []
    for path in frame_paths:
        with open(path, 'rb') as f:
            images.append(base64.b64encode(f.read()).decode())

    # Build multi-image prompt
    content = [{"type": "text", "text": VIDEO_MODERATION_PROMPT}]
    for img in images:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img}"}
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content}],
        max_tokens=500
    )

    return parse_moderation_response(response.choices[0].message.content)
```

**Moderation Prompt:**
```
Analyze these video frames for content moderation. Check for:
1. Nudity or sexual content (explicit or suggestive)
2. Violence or gore
3. Minors in inappropriate contexts
4. Hate symbols or extremist content

For each category, provide:
- severity: none/low/medium/high/critical
- confidence: 0.0-1.0
- reason: brief explanation if flagged

Return JSON format.
```

**Thresholds (from existing image moderation):**
- `critical` → Auto-reject
- `high` → Pending review
- `medium` → Pending review
- `low` → Auto-approve with monitoring

**Files to Create/Modify:**
- `prompts/services/video_moderation.py` - Video NSFW checking
- `prompts/constants.py` - Moderation prompts and thresholds

---

### M3: SEO Content Generation

**Purpose:** Generate SEO-optimized title, description, and tags from video frames.

**Technical Implementation:**
```python
# prompts/services/video_content.py
def generate_video_content(frame_paths: list[str], user_prompt: str = "") -> dict:
    """
    Generate SEO content from video frames.

    Args:
        frame_paths: List of extracted frame paths
        user_prompt: User-provided prompt text (optional)

    Returns:
        Dict with title, description, tags, excerpt
    """
    client = OpenAI()

    # Use middle frame as primary for analysis
    primary_frame = frame_paths[len(frame_paths) // 2]

    # Include user prompt context if provided
    prompt = VIDEO_CONTENT_PROMPT
    if user_prompt:
        prompt += f"\n\nUser's prompt for this video: {user_prompt}"

    # ... OpenAI Vision API call similar to image content generation

    return {
        "title": generated_title,
        "description": generated_description,
        "tags": suggested_tags,
        "excerpt": seo_excerpt
    }
```

**SEO Requirements:**
- Title: 50-60 characters, includes AI generator name
- Description: 150-300 words, keyword-rich
- Tags: 5 suggestions from 209-tag system
- Excerpt: 50-100 words for meta description

**Files to Create/Modify:**
- `prompts/services/video_content.py` - Video content generation
- Integrate with existing `ContentGenerationService`

---

### M4: Video Thumbnails

**Purpose:** Generate and upload thumbnail images for video prompts.

**Technical Implementation:**
```python
# prompts/services/video_processor.py
def create_video_thumbnail(video_path: str, timestamp: float = None) -> str:
    """
    Create thumbnail from video at specified timestamp.

    Args:
        video_path: Path to video file
        timestamp: Time in seconds (default: 25% of duration)

    Returns:
        Path to generated thumbnail image
    """
    if timestamp is None:
        duration = get_video_duration(video_path)
        timestamp = duration * 0.25  # 25% mark typically good

    output_path = tempfile.mktemp(suffix='_thumb.jpg')
    subprocess.run([
        'ffmpeg', '-ss', str(timestamp), '-i', video_path,
        '-frames:v', '1', '-vf', 'scale=600:600:force_original_aspect_ratio=decrease',
        '-q:v', '2', output_path
    ], check=True)

    return output_path
```

**Thumbnail Sizes (consistent with images):**
- Thumb: 300x300
- Medium: 600x600 (primary display)
- Large: 1200x1200 (detail view)

**Files to Create/Modify:**
- `prompts/services/video_processor.py` - Thumbnail generation
- Upload to B2 using existing `b2_upload_service.py`

---

### M5: File Restrictions

**Purpose:** Validate video uploads against platform limits.

**Restrictions:**
| Constraint | Limit | Error Message |
|------------|-------|---------------|
| File size | 100 MB | "Video must be under 100MB" |
| Duration | 20 seconds | "Video must be 20 seconds or less" |
| Format | MP4, MOV, WebM | "Supported formats: MP4, MOV, WebM" |
| Resolution | Min 480p | "Minimum resolution: 480p" |
| Framerate | 15-60 fps | "Framerate must be 15-60 fps" |

**Technical Implementation:**
```python
# prompts/services/video_validator.py
import subprocess
import json

def validate_video(video_path: str) -> dict:
    """
    Validate video against platform restrictions.

    Returns:
        {"valid": bool, "errors": list[str], "metadata": dict}
    """
    errors = []

    # Get video metadata using ffprobe
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', video_path
    ], capture_output=True, text=True)

    metadata = json.loads(result.stdout)

    # Check file size
    file_size = int(metadata['format']['size'])
    if file_size > 100 * 1024 * 1024:  # 100MB
        errors.append("Video must be under 100MB")

    # Check duration
    duration = float(metadata['format']['duration'])
    if duration > 20:
        errors.append("Video must be 20 seconds or less")

    # Check format
    format_name = metadata['format']['format_name']
    if not any(fmt in format_name for fmt in ['mp4', 'mov', 'webm']):
        errors.append("Supported formats: MP4, MOV, WebM")

    # ... additional checks for resolution, framerate

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "metadata": {
            "duration": duration,
            "size_mb": file_size / (1024 * 1024),
            "format": format_name
        }
    }
```

**Files to Create:**
- `prompts/services/video_validator.py` - Validation logic
- `prompts/constants.py` - Restriction constants

---

### M6: SEO File Naming/Slug Generation

**Purpose:** Generate SEO-optimized filenames and URL slugs for videos.

**Naming Convention:**
```
# Filename format:
{keywords}-{generator}-video-{timestamp}.{ext}

# Examples:
cyberpunk-city-neon-midjourney-video-1704367200.mp4
fantasy-dragon-dalle3-video-1704367200.mp4

# Slug format:
{keywords}-{generator}-{random_suffix}

# Examples:
cyberpunk-city-neon-midjourney-xK9mP
fantasy-dragon-dalle3-q7RnZ
```

**Technical Implementation:**
```python
# prompts/utils/seo_naming.py
import re
import secrets
from django.utils.text import slugify

def generate_video_filename(title: str, generator: str, extension: str) -> str:
    """Generate SEO-friendly video filename."""
    # Extract keywords from title
    keywords = extract_keywords(title, max_words=4)
    keywords_slug = slugify('-'.join(keywords))

    # Clean generator name
    generator_slug = slugify(generator)

    # Add timestamp for uniqueness
    timestamp = int(time.time())

    return f"{keywords_slug}-{generator_slug}-video-{timestamp}.{extension}"

def generate_prompt_slug(title: str, generator: str) -> str:
    """Generate unique URL slug for prompt."""
    keywords = extract_keywords(title, max_words=4)
    keywords_slug = slugify('-'.join(keywords))
    generator_slug = slugify(generator)
    random_suffix = secrets.token_urlsafe(4)[:5]

    return f"{keywords_slug}-{generator_slug}-{random_suffix}"
```

**Files to Create/Modify:**
- `prompts/utils/seo_naming.py` - SEO naming utilities
- Integrate with upload flow

---

### Known Issues

#### Video Layout Shift on Prompt Detail Page

**Status:** ✅ RESOLVED (M5 - January 13, 2026)

**Problem:** Videos on prompt detail page experienced layout shift when loading. The browser didn't know video dimensions until metadata loaded, causing content below to shift.

**Previous Attempted Fixes:**
- M1-FIX3: Forced 16:9 aspect ratio container with `object-fit: contain`
- **Result:** Rejected - caused ugly letterboxing for vertical (9:16) videos
- **Rollback:** Reverted to commit `7fc11b9`

**Implemented Solution (M5-C):**
1. Added fields to Prompt model:
   ```python
   video_width = models.PositiveIntegerField(null=True, blank=True)
   video_height = models.PositiveIntegerField(null=True, blank=True)
   ```
2. FFmpeg extracts dimensions during upload via `get_video_dimensions()`
3. Dimensions saved to session keys (`video_width`, `video_height`) during B2 complete
4. Template uses `aspect-ratio: {{ prompt.video_width }} / {{ prompt.video_height }}`
5. Browser reserves correct space upfront → zero layout shift

**Files Modified:**
- `prompts/models.py` - Added dimension fields (migration 0043)
- `prompts/services/video_processor.py` - `get_video_dimensions()` function
- `prompts/views/api_views.py` - Dimension extraction in `b2_upload_complete()`
- `prompts/views/upload_views.py` - Dimension storage from session
- `prompts/templates/prompts/prompt_detail.html` - Uses `aspect-ratio` CSS property

---

### Integration Points

**With Phase L (Media Infrastructure):**
- Use B2 upload service for video storage
- Use Cloudflare CDN for video delivery
- Follow B2-first template pattern

**With Existing Moderation:**
- Integrate with `ModerationOrchestrator`
- Use consistent severity thresholds
- Support appeal workflow

**With Content Generation:**
- Extend `ContentGenerationService` for video
- Use same 209-tag system
- Consistent SEO formatting

---

### Environment Variables (New)

```bash
# Video processing
VIDEO_MAX_SIZE_MB=100
VIDEO_MAX_DURATION_SECONDS=60
VIDEO_FRAME_COUNT=5
VIDEO_THUMBNAIL_QUALITY=2

# Moderation thresholds
VIDEO_NSFW_THRESHOLD_REJECT=high
VIDEO_NSFW_THRESHOLD_REVIEW=medium
```

---

### Success Criteria

- [ ] Videos validated before processing (M5)
- [ ] Frames extracted successfully (M1)
- [ ] NSFW moderation catches inappropriate content (M2)
- [ ] SEO content generated for all videos (M3)
- [ ] Thumbnails created at all sizes (M4)
- [ ] Filenames and slugs are SEO-optimized (M6)
- [ ] End-to-end upload time < 30 seconds for 60s video
- [ ] Agent validation: 8+/10 average

---

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FFmpeg not available on Heroku | Low | Critical | Use heroku-buildpack-ffmpeg |
| OpenAI Vision API rate limits | Medium | High | Implement retry logic, frame sampling |
| Large video processing timeouts | Medium | High | Async processing with Celery |
| Storage costs for video | Low | Medium | Enforce size/duration limits |

---

### Files to Create/Extend

| File | Purpose | Lines (Est.) | Notes |
|------|---------|--------------|-------|
| `prompts/services/video_processor.py` | Frame extraction, thumbnails | +150 | Extend existing (from L6) |
| `prompts/services/video_moderation.py` | NSFW checking | 150 | New file |
| `prompts/services/video_content.py` | SEO content generation | 150 | New file |
| `prompts/services/video_validator.py` | File validation | 100 | New file |
| `prompts/utils/seo_naming.py` | Filename/slug generation | 80 | New file |

**Total Estimated:** ~630 lines of new/modified code

---

## 🔮 Future Features Roadmap

**Created:** December 29, 2025
**Purpose:** Comprehensive planning document for post-Phase K features
**Status:** Planning Phase - Prioritization Complete

---

### Overview

This roadmap contains 19 planned features organized by priority tier, with detailed implementation specifications, revenue projections, and risk assessments. Features are categorized based on user value, technical complexity, and business impact.

---

### Priority Matrix

| Priority | Features | Timeline | Focus |
|----------|----------|----------|-------|
| **Tier 1 (Critical)** | 4 features | Q1 2026 | Core user experience, monetization |
| **Tier 2 (High)** | 7 features | Q2 2026 | Growth features, competitive parity |
| **Tier 3 (Medium)** | 3 features | Q3 2026 | Polish, differentiation |
| **Tier 4 (Low)** | 5 features | Q4 2026+ | Nice-to-have, experimental |

---

### Tier 1: Critical Priority (Q1 2026)

#### 1. Premium Tier System

**Description:** Implement paid subscription tiers with collection limits, private collections, and premium features.

| Aspect | Details |
|--------|---------|
| **Effort** | 2-3 weeks |
| **Dependencies** | Phase K Collections (complete) |
| **Revenue Impact** | Primary monetization - $7/mo target |
| **Technical Complexity** | Medium (Stripe integration exists) |

**Features:**
- Free tier: 10 collections, 2 private
- Premium tier: Unlimited collections, unlimited private
- Upgrade prompts when limits reached
- Stripe subscription management

**Success Metrics:**
- 10% free-to-paid conversion rate
- $1,000 MRR within 3 months

---

#### 2. Download Tracking + Virtual Collections

**Description:** Track prompt downloads and create "Your Downloads" virtual collection.

| Aspect | Details |
|--------|---------|
| **Effort** | 1 week |
| **Dependencies** | Phase K Collections |
| **Revenue Impact** | Premium feature, increases stickiness |
| **Technical Complexity** | Low |

**Features:**
- Download model tracking user + prompt + timestamp
- "Your Downloads" virtual collection (not stored as Collection)
- Download history page
- "Your Likes" virtual collection

**Database Model:**
```python
class Download(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'prompt']
```

---

#### 3. Comment Pagination

**Description:** Load more pattern for comments to improve page performance.

| Aspect | Details |
|--------|---------|
| **Effort** | 2-3 days |
| **Dependencies** | None |
| **Revenue Impact** | Indirect (UX improvement) |
| **Technical Complexity** | Low |

**Implementation:**
- Initial load: 10 comments
- "Load more" button for next 10
- AJAX endpoint for paginated comments
- Comment count in header

---

#### 4. Social Sharing Buttons

**Description:** Share prompts to Twitter, Pinterest, and copy link functionality.

| Aspect | Details |
|--------|---------|
| **Effort** | 1-2 days |
| **Dependencies** | None |
| **Revenue Impact** | Viral growth potential |
| **Technical Complexity** | Low |

**Buttons:**
- Twitter/X share (with prompt text)
- Pinterest pin (with image)
- Copy link
- Native share API (mobile)

---

### Tier 2: High Priority (Q2 2026)

#### 5. Related Prompts Section

**Description:** "More like this" section on prompt detail page based on tags and author.

| Aspect | Details |
|--------|---------|
| **Effort** | 1 week |
| **Dependencies** | None |
| **Revenue Impact** | Increased engagement, page views |
| **Technical Complexity** | Medium |

**Algorithm:**
- Same tags (weighted by overlap)
- Same author
- Same AI generator
- Exclude current prompt

---

#### 6. Image Lightbox/Zoom

**Description:** Click to enlarge images with keyboard navigation.

| Aspect | Details |
|--------|---------|
| **Effort** | 3-4 days |
| **Dependencies** | None |
| **Revenue Impact** | UX improvement |
| **Technical Complexity** | Low-Medium |

**Features:**
- Click image to open lightbox
- Keyboard navigation (←→ ESC)
- Zoom controls
- Download from lightbox

---

#### 7. Notification System

**Description:** In-app notifications for likes, comments, follows, and system events.

| Aspect | Details |
|--------|---------|
| **Effort** | 2 weeks |
| **Dependencies** | Email preferences (complete) |
| **Revenue Impact** | Engagement driver |
| **Technical Complexity** | Medium-High |

**Features:**
- Bell icon in navbar with unread count
- Notification types: likes, comments, follows, mentions
- Mark as read/unread
- Notification preferences
- Email digests (weekly)

---

#### 8. Follow System Enhancement

**Description:** Complete follow/unfollow with Following feed tab.

| Aspect | Details |
|--------|---------|
| **Effort** | 1 week |
| **Dependencies** | Current follow button |
| **Revenue Impact** | Community building |
| **Technical Complexity** | Medium |

**Features:**
- Following tab on homepage (shows only followed users' prompts)
- Followers/following lists on profile
- Notification on new follow
- Mutual follow badge

---

#### 9. Search Improvements

**Description:** Advanced search with filters, autocomplete, and search history.

| Aspect | Details |
|--------|---------|
| **Effort** | 2 weeks |
| **Dependencies** | None |
| **Revenue Impact** | Discoverability |
| **Technical Complexity** | Medium |

**Features:**
- Autocomplete suggestions
- Filter by: AI generator, tags, date, type
- Search history (authenticated users)
- "Did you mean" suggestions

---

#### 10. AI Generator Integration (In-App Image Generation)

**Description:** Generate images from prompts directly on PromptFinder using cloud AI APIs.

| Aspect | Details |
|--------|---------|
| **Effort** | 4-6 weeks |
| **Dependencies** | Phase L (media infrastructure) |
| **Revenue Impact** | Major premium feature, new revenue stream |
| **Technical Complexity** | Very High |

**Recommended API: Replicate**

| Factor | Replicate | Direct APIs | Winner |
|--------|-----------|-------------|--------|
| Multi-model support | 50+ models | 1 per integration | Replicate |
| Pricing | Pay-per-use | Varies | Tie |
| Integration complexity | Single API | Multiple APIs | Replicate |
| Model availability | SDXL, Flux, etc. | Varies | Replicate |
| Rate limits | Generous | Often restrictive | Replicate |

**Why Replicate:**
- Single integration covers Stable Diffusion, Flux, SDXL, and future models
- No need to maintain multiple API integrations
- Automatic scaling and queueing
- Transparent pricing ($0.0023-0.05 per image depending on model)
- Easy model switching as new ones release

**Features:**
- "Generate" button on any prompt page
- Model selector (SDXL, Flux, etc.)
- Queue system for async generation
- Generation history (premium)
- Save generated images to library
- Cost tracking per user

**Pricing Model:**
- Free tier: 5 generations/month
- Premium: 50 generations/month included
- Credits: Buy additional generations

**Technical Notes:**
- Async job queue (Celery + Redis)
- Webhook for completion notification
- Store generations in B2 (Phase L dependency)
- Cache popular prompt generations

---

#### 11. Admin Notification System (Moderation Alerts)

**Description:** Send email notifications to admins when uploads are auto-rejected by the moderation system, enabling oversight and appeal handling.

| Aspect | Details |
|--------|---------|
| **Effort** | 3-5 days |
| **Dependencies** | Content moderation system (complete) |
| **Revenue Impact** | Platform safety, reduced legal risk |
| **Technical Complexity** | Low-Medium |

**Features:**
- Email notifications to configured admin addresses
- Triggered when moderation auto-rejects uploads (NSFW, violence, etc.)
- Includes prompt title, author, rejection reason, confidence scores
- Link to admin panel for review
- Daily/weekly digest option (batch notifications)
- Per-category notification thresholds (high-severity only vs all)

**Email Content:**
```
Subject: [PromptFinder] Upload Auto-Rejected: {prompt_title}

An upload has been automatically rejected by the moderation system.

Author: {username}
Title: {prompt_title}
Reason: {rejection_reason}
Confidence: {confidence_score}%
Time: {timestamp}

Review in admin: {admin_url}
```

**Configuration (SiteSettings):**
- `admin_notification_emails` - Comma-separated list of recipient emails
- `notify_on_rejection` - Boolean toggle (default: True)
- `rejection_notification_threshold` - Minimum severity to trigger (low/medium/high/critical)
- `enable_daily_digest` - Bundle notifications into daily summary

**Implementation Notes:**
- Use Django's `send_mail()` with async/Celery for non-blocking
- Integrate with existing `ModerationOrchestrator` rejection flow
- Leverage `ADMINS` setting already configured in `settings.py`
- Consider rate limiting to prevent notification spam

---

#### 12. Content Moderation Dashboard (Planned)

**Description:** Unified dashboard for monitoring and managing content moderation across the platform, replacing the placeholder banner in Django admin.

| Aspect | Details |
|--------|---------|
| **Route** | `/admin/moderation-dashboard/` |
| **Priority** | Medium (Post-MVP) |
| **Effort** | 4-8 hours |
| **Dependencies** | Content moderation system (complete) |
| **Technical Complexity** | Medium |

**Planned Features:**
- Real-time moderation queue (pending reviews)
- Flagged content list with bulk actions
- Moderation statistics and trends
- User trust scores and history
- Appeal management interface
- Profanity word list management

**Existing Infrastructure (Ready to Use):**
- `ContentFlag` model - Tracks flagged content
- `ModerationLog` model - Audit trail of moderation actions
- `PromptReport` model - User-submitted reports
- `ProfanityWord` model - Custom profanity filter words
- `ModerationOrchestrator` service - Central moderation logic

**Current Status:**
The admin dashboard currently shows a "Content Moderation System" banner that links to this planned route (`/admin/moderation-dashboard/`). The link is intentionally broken as a reminder to build this feature.

**Why Deferred:**
- SEO Review Queue covers immediate moderation needs
- Admin can use Django admin for individual model management
- Dashboard is polish/convenience, not MVP-critical

---

### Tier 3: Medium Priority (Q3 2026)

#### 13. Comment Threading (moved from #11)

**Description:** Reply to comments with nested threading.

| Aspect | Details |
|--------|---------|
| **Effort** | 2 weeks |
| **Dependencies** | Comment pagination |
| **Revenue Impact** | Community engagement |
| **Technical Complexity** | High |

**Features:**
- Reply button on comments
- 2-level nesting maximum
- Collapse/expand threads
- "View X replies" link

---

#### 14. Prompt Versioning (moved from #12)

**Description:** Edit history and version comparison for prompts.

| Aspect | Details |
|--------|---------|
| **Effort** | 2-3 weeks |
| **Dependencies** | None |
| **Revenue Impact** | Premium feature potential |
| **Technical Complexity** | High |

**Features:**
- Save versions on edit
- View edit history
- Compare versions side-by-side
- Restore previous version

---

#### 15. Collection Sharing (moved from #13)

**Description:** Share collections via link and embed on external sites.

| Aspect | Details |
|--------|---------|
| **Effort** | 1 week |
| **Dependencies** | Phase K Collections |
| **Revenue Impact** | Viral growth |
| **Technical Complexity** | Low-Medium |

**Features:**
- Share link for public collections
- Embed code for external sites
- Share to social media
- Track share analytics

---

### Tier 4: Low Priority (Q4 2026+)

#### 16. API Access (moved from #14)

**Description:** REST API for developers to integrate PromptFinder prompts.

| Aspect | Details |
|--------|---------|
| **Effort** | 3-4 weeks |
| **Dependencies** | Premium tier |
| **Revenue Impact** | Premium upsell |
| **Technical Complexity** | High |

**Features:**
- API key management
- Rate limiting by tier
- Endpoints: list, get, search prompts
- Documentation page

---

#### 17. Bulk Upload (moved from #15)

**Description:** Upload multiple prompts at once via CSV or ZIP.

| Aspect | Details |
|--------|---------|
| **Effort** | 2-3 weeks |
| **Dependencies** | Premium tier |
| **Revenue Impact** | Premium upsell |
| **Technical Complexity** | High |

**Features:**
- CSV import (title, prompt, tags, generator)
- ZIP upload (images + metadata.json)
- Preview before publish
- Batch processing with progress

---

#### 18. Blog System (moved from #16)

**Description:** Integrated blog for SEO content, tutorials, and prompt engineering guides.

| Aspect | Details |
|--------|---------|
| **Effort** | 2-3 weeks |
| **Dependencies** | None |
| **Revenue Impact** | SEO traffic, affiliate income |
| **Technical Complexity** | Medium |

**Features:**
- Django-based blog with CKEditor
- Categories: Tutorials, News, Generator Guides, Prompt Engineering
- SEO-optimized posts with schema markup
- Author profiles linked to main platform
- Comment system (reuse existing)
- RSS feed generation

**SEO Value:**
- Target long-tail keywords ("how to write midjourney prompts")
- Build topical authority
- Internal linking to prompt pages
- Estimated 10K+ monthly organic visits at maturity

---

#### 19. PromptCast AI Podcast (moved from #17)

**Description:** Automated AI-generated podcast discussing trending prompts and AI art news.

| Aspect | Details |
|--------|---------|
| **Effort** | 3-4 weeks |
| **Dependencies** | Blog system (optional) |
| **Revenue Impact** | Brand awareness, premium upsell |
| **Technical Complexity** | High |

**Features:**
- Weekly automated episodes (15-20 minutes)
- AI voice generation (ElevenLabs or similar)
- Script generation from trending prompts + news
- RSS feed for podcast directories
- Embedded player on site
- Episode transcripts (SEO)

**Distribution:**
- Apple Podcasts
- Spotify
- Google Podcasts
- YouTube (audio + visualizer)
- Website embed

**Content Format:**
1. Intro (AI-generated jingle)
2. Trending prompts of the week (5 featured)
3. AI art news segment
4. Prompt engineering tip
5. Community highlight
6. Outro with CTA

---

#### 20. Manual Mode Fallback (moved from #18)

**Description:** When AI services fail (timeout, API error, refusal), allow users to manually enter title and description instead of blocking the entire upload flow.

| Aspect | Details |
|--------|---------|
| **Effort** | 1 week |
| **Dependencies** | None |
| **Revenue Impact** | Reliability improvement, reduced upload failures |
| **Technical Complexity** | Medium |

**Features:**
- Detect AI service failures (timeout, API errors, refusal responses)
- Show "Manual Mode" form with title and description fields
- Pre-populate with safe defaults ("Untitled Upload", empty description)
- Allow users to enter their own metadata
- Skip AI tag suggestions, allow manual tag selection
- Log fallback usage for monitoring

**Triggers for Manual Mode:**
- OpenAI API timeout (>30 seconds)
- OpenAI API error (rate limit, service unavailable)
- AI refusal to analyze image
- Content generation failure

**UX Flow:**
```
AI Service Fails → Show "Manual Mode" Banner
                 → Display title/description form
                 → User enters metadata manually
                 → Continue to Step 2 with user-provided data
```

**Why Tier 4:**
- Current system handles failures with fallback values + pending_review status
- Manual mode improves UX but not critical for launch
- Can be added post-launch based on failure rate monitoring

---

### Revenue Projections

| Timeline | MRR Target | Key Drivers |
|----------|------------|-------------|
| Q1 2026 | $1,000 | Premium tier launch, collection limits |
| Q2 2026 | $3,000 | Growth features, viral sharing |
| Q3 2026 | $7,000 | API access, bulk upload |
| Q4 2026 | $10,000 | Full feature set, word of mouth |

---

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Premium conversion too low | Medium | High | A/B test pricing, feature gating |
| Technical debt accumulation | Medium | Medium | Regular refactoring sprints |
| Competitor feature parity | Low | Medium | Focus on unique differentiators |
| Scope creep | High | Medium | Strict micro-spec discipline |

---

### Implementation Guidelines

**For Each Feature:**
1. Create micro-spec before implementation
2. Agent validation required (8+/10 minimum)
3. Update this roadmap on completion
4. Add to changelog

**Priority Adjustments:**
- User feedback may reprioritize features
- Revenue data may shift focus
- Technical discoveries may reorder

**Related Sections:**
- [Phase K: Collections Feature](#-phase-k-collections-feature-current-priority) - Current work
- [Known Technical Debt](#-known-technical-debt) - Address before new features
- [Decisions Made](#decisions-made) - Historical context

---

## 📚 Documentation Archive Structure

**Created:** November 3, 2025
**Purpose:** Organized storage for historical and staged documentation

### Archive Organization

**Location:** `archive/` in project root

**Structure:**
- `archive/phase-e/` - Phase E implementation documentation (16 files + 3 READMEs)
  - `completion-reports/` - Phase E specs, reports, bug fixes (9 files)
  - `testing/` - Test configuration and safety reports (3 files)
  - `forms-implementation/` - UserProfile form guides (4 files)
- `archive/bug-fixes/` - Resolved bug documentation (7 files)
- `archive/feature-implementations/` - Completed features (2 files)
- `archive/rate-limiting/` - Rate limiting implementation (3 files)
- `archive/needs-review/` - Files requiring user decision (9 files, review by Dec 3)
- `archive/marked-for-deletion/` - Deletion staging area (21 files, review by Dec 3)
  - `safe-to-delete/` - High confidence deletions (3 files)
  - `verify-first/` - Medium confidence deletions (18 files)

**Total Archived:** 58 files (~984 KB)

**Active Workspace:**
- Before: 71 files (1.3 MB)
- After: 11 core docs (338 KB) + archive/
- Reduction: 89% smaller active workspace

**Active Documentation (Post-Cleanup):**
- **Root:** 6 files (CLAUDE.md, PHASE_A_E_GUIDE.md, PROJECT_FILE_STRUCTURE.md, README.md, HEROKU_SCHEDULER_SETUP.md, DOCUMENTATION_CLEANUP_REPORT.md)
- **docs/:** 5 files (CC_COMMUNICATION_PROTOCOL.md, DEPLOYMENT_CHECKLIST.md, DJANGO_ORM_SOFT_DELETE_PATTERNS.md, PHASE_F_DAY1_INTERIM_UPDATE_REPORT.md, README.md)

### Archive Maintenance

**Review Date:** December 3, 2025 (30 days)

**Actions Required:**
1. Review `needs-review/` folder - Move back to active or delete
   - ROOT_README.md - Update for Phase E/F or keep archived?
   - RATE_LIMITING_GUIDE.md - Still operational guide?
   - MIGRATION_SAFETY.md - Still needed?
   - 6 other files requiring evaluation
2. Review `marked-for-deletion/` folder - Delete safe-to-delete/, verify verify-first/
   - 3 safe-to-delete files (duplicates, diagnostics)
   - 18 verify-first files (verification docs, old moderation, userprofile working)
3. Update this section after cleanup complete

**See:** `archive/README.md` for complete index and maintenance instructions

---

## 🤖 Working with Claude Code (CC)

### Specification Requirements

**CRITICAL:** All specifications for Claude Code must follow the standardized template.

**Template Location:** `CC_SPEC_TEMPLATE.md` (root directory)

### Why This Matters

During Phase F (Nov 2025), we implemented mandatory agent testing for all CC work:

**Results:**
- **Average Quality Rating:** 9.2/10
- **Critical Bugs Caught:** 1 (referer checks - prevented production issue)
- **Zero Regressions:** All existing features continued working
- **Professional Deliverables:** Consistent, high-quality output

**The Pattern:**
1. Every spec includes mandatory agent usage header
2. Minimum 2-3 agents per task (8+/10 ratings required)
3. Comprehensive testing and reporting
4. Clear documentation

### How to Use

**When creating CC specifications:**

1. Start with `CC_SPEC_TEMPLATE.md`
2. Include the "⚠️ CRITICAL: READ FIRST" header
3. Specify appropriate agents for the task
4. Require agent ratings 8+/10
5. Include comprehensive testing checklist

**Examples:**
- Phase F Day 2: Admin backend cosmetic fixes (9.25/10)
- Phase F Day 2.5: Configuration verification (9.25/10)
- Phase F Day 2.7: Production bug fixes (9.17/10)

### Key Documents

- **Template:** `CC_SPEC_TEMPLATE.md`
- **Protocol:** `docs/CC_COMMUNICATION_PROTOCOL.md`
- **Full Protocol:** `PROJECT_COMMUNICATION_PROTOCOL.md`

**This system has proven highly effective and should be maintained for all future work.**

---

## 🔍 SEO Strategy (Complete)

### On-Page SEO Checklist

**Every Prompt Page Must Have:**

1. **Title Tag** (50-60 characters)
   - Format: `"[Prompt Title] - [AI Generator] Prompt | PromptFinder"`
   - Example: `"Cyberpunk Neon Cityscape - Midjourney Prompt | PromptFinder"`

2. **Meta Description** (155-160 characters)
   - Include keywords, AI generator, CTA
   - Example: `"Create stunning cyberpunk cityscapes with this Midjourney prompt. Features neon lights, rain, flying cars. Free to use on PromptFinder."`

3. **H1 Tag** (one per page)
   - Format: `"[Title] - [AI Generator] Prompt"`
   - Example: `"Cyberpunk Neon Cityscape - Midjourney Prompt"`

4. **H2-H6 Hierarchy**
   - H2: About This Prompt
   - H2: The AI Prompt
   - H2: How to Use This Prompt
   - H2: Tips for Best Results
   - H2: Related Prompts
   - H2: Comments

5. **Image SEO:**
   - **Filename:** `keyword1-keyword2-[ai-gen]-prompt-[timestamp].jpg`
   - **Alt Tag:** `"[Title] - [AI Generator] Prompt - AI-generated image"`
   - **Thumbnails:** Different alt tags per context
   - **Lazy loading:** Below-fold images

6. **Structured Data (Schema.org JSON-LD):**
   - Article schema (main content)
   - HowTo schema (how to use prompt)
   - ImageObject schema (featured image)
   - BreadcrumbList schema (navigation)
   - Person schema (author)
   - WebPage schema
   - FAQPage schema (if FAQ section exists)
   - AggregateRating schema (from likes/comments)

7. **Internal Linking:**
   - Related prompts (same tags)
   - More from author
   - Tag pages
   - AI generator category pages
   - Breadcrumb navigation

8. **URL Structure:**
   - Format: `/prompts/[slug]/`
   - Example: `/prompts/cyberpunk-neon-cityscape-midjourney/`
   - Clean, descriptive, keyword-rich

9. **Canonical URL:**
   - `<link rel="canonical" href="https://promptfinder.net/prompts/[slug]/">`

10. **Open Graph Tags:**
    - og:title, og:description, og:image, og:url, og:type

11. **Twitter Card Tags:**
    - twitter:card, twitter:title, twitter:description, twitter:image

12. **Last Modified Date:**
    - Display on page
    - Include in schema (dateModified)
    - Meta tag: article:modified_time

13. **Content Quality:**
    - 800-1500 words per page
    - Unique, valuable content
    - User-generated (comments add freshness)

### Technical SEO

**Site-Wide:**
- [ ] Sitemap.xml (auto-generated, updated daily)
- [ ] Robots.txt (allow crawling, block admin)
- [ ] HTTPS/SSL (required)
- [ ] Mobile-responsive (Bootstrap handles this)
- [ ] Page speed optimization (Lighthouse >90)
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] GDPR compliance (cookie consent, privacy policy)

**Performance:**
- [ ] Lazy loading images
- [ ] WebP image format (Cloudinary auto)
- [ ] Minified CSS/JS
- [ ] CDN (Cloudinary for images, consider Cloudflare for static)
- [ ] Database query optimization
- [ ] Caching strategy (browser + server)

### SEO Monitoring (Phase 3+)

- [ ] Google Search Console (track rankings, errors)
- [ ] Google Analytics (traffic, engagement)
- [ ] Track keyword rankings
- [ ] Monitor backlinks
- [ ] Competitor analysis

---

## 👤 User Management

### User Roles & Permissions

**1. Free User (Prompt Finder)**
- Default role on signup
- 10 uploads/week (launch) → 5-10/month (growth)
- Public prompts only
- Can like, comment, follow
- Sees ads

**2. Trial User (14 Days)**
- All premium features unlocked
- Card required upfront
- Email reminders (Day 11, 13)
- Auto-converts to premium or downgrades to free

**3. Premium User (Pro Finder)**
- $7/month or $70/year
- All premium features (see Monetization section)
- Verified badge
- 2x PromptCoin earning

**4. Verified User (Verified Finder)**
- Manual verification by admin
- Badge displayed on profile/comments
- Higher trust score
- Prompts skip some moderation checks (if trusted)

**5. Admin/Staff**
- Full Django admin access
- Moderation dashboard
- Can issue warnings, bans, restrictions
- View all reports, appeals
- Analytics dashboard

### User Profile Fields

**Required:**
- Username (unique)
- Email (verified)
- Password (hashed)

**Optional:**
- Display name
- Bio (500 chars max)
- Avatar image
- Cover image (Phase 3)
- Location
- Website URL
- Social media links (Twitter, Instagram, etc.)

**System Fields:**
- Date joined
- Last login
- Account status (good standing, probation, restricted, banned)
- Is verified (boolean)
- Is premium (boolean)
- Trial end date
- Subscription status
- PromptCoin balance
- Total uploads count
- Total likes received
- Follower count
- Following count
- Invite codes remaining
- Was invited by (referral tracking)

**Moderation Fields:**
- Total warnings
- Total violations
- Strikes (0-3)
- Is trusted (skips moderation)

### Notification Types (Complete List)

**Engagement:**
- Someone liked your prompt
- New comment on your prompt
- Someone replied to your comment
- New follower
- Someone mentioned you (@username)

**System:**
- Welcome to PromptFinder
- Email verification
- Password reset
- Profile updated

**Moderation:**
- Content flagged/removed
- Content pending review (initial notification)
- Pending review reminder (Day 5 - "Still under review, 2 days left")
- Pending review expired (Day 7 - "Content removed, not reviewed in time")
- Content approved after review
- Warning issued
- Restriction applied
- Restriction lifted
- Appeal submitted
- Appeal reminder (Day 5 - "Appeal still under review")
- Appeal expired (Day 7 - "Appeal not reviewed in time")
- Appeal approved/rejected
- Comment removed

**Monetization:**
- Trial starting
- Trial ending (3 days, 1 day)
- Payment successful
- Payment failed
- Subscription cancelled
- Upgrade successful
- PromptCoins purchased
- PromptCoin reward earned

**Upload Limits:**
- Approaching limit (2 uploads left)
- Limit reached
- Limit reset (new week/month)

**Social:**
- Invite code used successfully (+ coin reward)
- Leaderboard achievement (top 3)
- Milestone reached (100 uploads, 1000 likes, etc.)

### Notification Settings (User Configurable)

Users can toggle on/off:
- Email notifications (all, important only, none)
- Push notifications (browser)
- @ mention notifications
- Like notifications (all, milestones only, off)
- Comment notifications
- Follow notifications
- Trial/billing reminders
- Marketing emails

---

## 🎨 UI/UX Design Patterns

### Trash Bin Interface (Phase 2)

**Trash Bin Page Layout:**

┌─────────────────────────────────────────────────────────┐
│  📂 Trash                    [Filter ▼]  [Empty All]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ℹ️ Items deleted after 5 days (Free) or 30 days (Pro)  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  [Thumbnail]  Cyberpunk Neon Cityscape           │  │
│  │               Deleted 2 days ago • 3 days left   │  │
│  │               [Restore] [Delete Forever]         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  [Thumbnail]  Fantasy Dragon                     │  │
│  │               Deleted 4 days ago • ⚠️ 18 hrs left │  │
│  │               [Restore] [Delete Forever]         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ────────── FREE TIER LIMIT (10/10 items) ─────────────│
│                                                          │
│  💎 Upgrade to Premium for:                             │
│     • 30-day protection (6x longer)                     │
│     • Unlimited trash capacity                          │
│     • Bulk restore                                      │
│                                                          │
│                   [Upgrade to Premium →]                │
│                                                          │
└─────────────────────────────────────────────────────────┘

**Delete Confirmation Modal:**
┌──────────────────────────────────┐
│  Move to Trash?                  │
├──────────────────────────────────┤
│  "Cyberpunk Neon Cityscape"     │
│                                  │
│  Will be permanently deleted in: │
│  ⏱️  5 days (Free tier)           │
│                                  │
│  💎 Premium: 30-day protection   │
│                                  │
│  [Cancel]  [Move to Trash]      │
└──────────────────────────────────┘

**Toast Notification (After Delete):**
┌────────────────────────────────────┐
│ ✅ Moved to trash • Expires in 5d  │
│    [Undo] [View Trash]             │
└────────────────────────────────────┘
(Shows for 8 seconds, undo available for 5 seconds)

**Permanent Delete Warning:**
┌──────────────────────────────────┐
│  ⚠️ Permanent Deletion            │
├──────────────────────────────────┤
│  "Cyberpunk Neon Cityscape"     │
│                                  │
│  ❌ CANNOT be undone             │
│  ❌ Cloudinary image deleted     │
│  ❌ All likes/comments removed   │
│                                  │
│  Type "DELETE" to confirm:       │
│  [_______________]               │
│                                  │
│  [Cancel]  [Delete Forever]     │
└──────────────────────────────────┘

**Dashboard Badge:**
[Home] [Prompts] [Trash 🗑️ (3)] [Profile]

**Visual Indicators:**
- Normal (>2 days): Default colors
- Warning (1-2 days): Orange highlight
- Critical (<24h): Red highlight with pulse animation
- Empty state: Friendly "Your trash is empty" message


## 📋 Feature Specifications

### Tag System

**209 Tags Organized in 21 Categories:**

**1. People & Portraits (15 tags)**
Portraits, Men, Women, Children, Families, Couples, Groups, Close-ups, Profiles, Silhouettes, Body Parts, Hands, Eyes, Fashion Models, Senior Citizens

**2. Nature & Landscapes (18 tags)**
Mountains, Forests, Beaches, Deserts, Oceans, Lakes, Rivers, Waterfalls, Caves, Cliffs, Valleys, Meadows, Jungles, Islands, Horizons, Seascapes, Wilderness, Rolling Hills

**3. Architecture & Structures (12 tags)**
Modern Architecture, Historic Buildings, Skyscrapers, Bridges, Castles, Ruins, Urban Landscapes, Abandoned Buildings, Minimalist Architecture, Gothic Architecture, Brutalist Architecture, Cathedrals

**4. Interiors & Design (10 tags)**
Interior Design, Living Rooms, Bedrooms, Kitchens, Offices, Cafes, Restaurants, Hotels, Minimalist Interiors, Industrial Design

**5. Fashion & Beauty (9 tags)**
Fashion Photography, Street Fashion, Editorial Fashion, Makeup, Hair Styling, Jewelry, Accessories, Beauty Portraits, Magazine Covers

**6. Animals & Wildlife (12 tags)**
Wild Animals, Domestic Animals, Birds, Marine Life, Insects, Reptiles, Cats, Dogs, Horses, Exotic Animals, Animal Close-ups, Animal Behavior

**7. Action & Movement (10 tags)**
Sports, Dancing, Running, Jumping, Flying, Extreme Sports, Water Sports, Winter Sports, Action Shots, Dynamic Movement

**8. Art & Design (12 tags)**
Poster Design, Graphic Design, Typography, Illustrations, Digital Art, 3D Renders, Logos, Patterns, Textures, Collages, Mixed Media, Album Covers

**9. Sci-Fi & Fantasy (12 tags)**
Science Fiction, Space, Aliens, Robots, Cyberpunk, Futuristic Cities, Fantasy Worlds, Dragons, Magic, Spaceships, Dystopian, Post-Apocalyptic

**10. Mythology & Legends (8 tags)**
Greek Mythology, Norse Mythology, Egyptian Mythology, Mythical Creatures, Gods and Goddesses, Ancient Civilizations, Folklore, Legendary Heroes

**11. Concept Art (8 tags)**
Character Design, Environment Design, Vehicle Design, Creature Design, Prop Design, Storyboards, Visual Development, Game Art

**12. Abstract & Artistic (10 tags)**
Abstract Art, Surrealism, Geometric Patterns, Color Studies, Fractal Art, Psychedelic, Optical Illusions, Experimental, Avant-Garde, Minimalism

**13. Emotions & Expressions (10 tags)**
Joy, Sadness, Anger, Fear, Surprise, Contemplation, Serenity, Tension, Love, Melancholy

**14. Lighting & Atmosphere (12 tags)**
Golden Hour, Blue Hour, Dramatic Lighting, Soft Lighting, Neon Lights, Candlelight, Backlit, Silhouettes, High Contrast, Low Key, Atmospheric, Moody

**15. Seasons & Events (8 tags)**
Spring, Summer, Autumn, Winter, Celebrations, Festivals, Ceremonies, Weddings

**16. Holidays (6 tags)**
Christmas, Halloween, Thanksgiving, New Year, Valentine's Day, Easter

**17. Texture & Detail (8 tags)**
Close-up Details, Macro Photography, Textures, Surfaces, Materials, Patterns, Weathered, Organic Textures

**18. Magic & Wonder (6 tags)**
Magical Realism, Enchanted, Whimsical, Dreamlike, Ethereal, Mystical

**19. Luxury & Elegance (6 tags)**
Luxury Lifestyle, Elegance, Opulence, High Fashion, Fine Dining, Premium Products

**20. Humor & Playful (5 tags)**
Humorous, Playful, Quirky, Satirical, Cartoon Style

**21. Culture & History (12 tags)**
Black History, Civil Rights, Indigenous Cultures, Asian Cultures, Latin American Cultures, Middle Eastern Cultures, African Cultures, European History, Cultural Heritage, Traditional Costumes, Cultural Celebrations, Historical Events

**Total: 209 tags**

**Tag Selection:**
- AI suggests 5 tags from 209 options (based on image + prompt text analysis)
- User can remove, add, or type custom tags via autocomplete
- Max 7 tags per prompt (SEO best practice: 3-7 tags)
- User messaging: "Suggested tags (you can edit or add your own)"

**Dynamic Tag Creation:**
- If AI confidence < 0.7 on all 209 tags: AI can suggest 1 NEW custom tag
- New tag goes to "Pending Tags" admin review queue
- Admin approves/rejects within 2-4 days
- If approved: added to master 209 list
- User's prompt still publishes with best-match existing tags (no delay)

**Tag Validation:**
- AI silently validates if user's tags match image (confidence >0.8)
- If mismatch: Flag for admin review, publish anyway
- Admin reviews within 2-4 days, corrects if needed
- User never knows validation happened

**Admin Management:**
- All tags manageable via Django admin dashboard
- View by category
- Add/edit/delete tags
- Search tags by name
- See which prompts use each tag
- Bulk operations (merge duplicates, delete unused)
- Review pending custom tags

### File Limits

**Images:**
- Max size: 10MB
- Formats: JPEG, PNG, WebP, GIF
- Min dimensions: 400x400px (recommended 1200x630+)
- Instant feedback if exceeded

**Videos:**
- Max size: 100MB
- Max duration: 20 seconds
- Formats: MP4, MOV, WebM
- Min dimensions: 400x400px
- Instant feedback if exceeded

### AI Generators Supported

- Midjourney
- DALL-E 3
- DALL-E 2
- Stable Diffusion
- Leonardo AI
- Flux
- Adobe Firefly
- Bing Image Creator
- Other (user can specify)

### Filtering Options (Complete)

**Phase 1 (Basic):**
- Type: image, video
- Category: 27 preset tags
- Date: any, 24h, week, month, year
- AI Generator: all supported

**Phase 3 (Advanced):**
- Orientation: portrait, landscape, square (AI auto-detected)
- People count: 0, 1, 2, 3+ (AI auto-detected)
- Age range: teenager, adult, senior (for content rating, AI auto-detected)
- Sort: top (day/month/all-time), recent, trending, most liked, most viewed
- Combine multiple filters
- Save filter preferences (premium)

**Sensitive Filters (Private Only - Phase 3):**
- Ethnicity detection (AI) stored as private metadata
- NEVER displayed publicly
- Only used for user's private filtering
- Legal review recommended for GDPR
- Consider removing if legal concerns

### Persistent Join Modal Configuration

**Triggers (Admin Configurable):**

**Page View Triggers:**
- Show after: 2 pages viewed
- Then every: 2 pages

**Scroll Triggers (Progressive):**
- First trigger: After scrolling 60 prompts
- Second trigger: After scrolling 30 more prompts
- Third trigger: After scrolling 15 more prompts
- Subsequent: Every 15 prompts scrolled

**Cookie Behavior:**
- Dismissed modal: Don't show again for 24 hours
- Signed up: Never show again
- Configurable in admin: hours/days before reshowing

**Modal Content:**
- Compelling value proposition
- Premium features highlight
- CTA: "Sign Up Free" / "Start Free Trial"
- Dismissible X button
- Subtle animation (slide up, fade in)

---

## ❓ Unanswered Questions (To Address)

### Premium Features - Prioritization

**Question:** Which premium features should be in Phase 2 vs Phase 3?

**Current Plan:**
- Phase 2: Unlimited uploads, private prompts, ad-free, basic analytics, collections, verified badge
- Phase 3: Advanced analytics, API access, bulk upload, version history

**Need to Decide:**
- Is this prioritization correct?
- Any features to swap between phases?
- Any features to cut entirely?

### Design & Branding

**Questions:**
1. Logo design - need to create
2. Color scheme - primary/secondary colors
3. Font choices - headings vs body
4. Icon set - which library? (Font Awesome, Lucide, custom?)
5. Illustration style - for empty states, errors, onboarding

### Marketing & Launch

**Questions:**
1. Beta tester count target? (50? 100? 500?)
2. Public launch date target?
3. Pre-launch landing page? (collect emails)
4. Launch channels? (Product Hunt, Reddit, Twitter, etc.)
5. Press kit / media outreach?
6. Influencer partnerships?

### Analytics & Metrics

**Questions:**
1. Which metrics to track? (DAU, MAU, conversion rate, churn, etc.)
2. Analytics tool? (Google Analytics, Mixpanel, Plausible?)
3. Dashboards needed? (admin, user, public stats page?)
4. A/B testing tool? (Built-in, Optimizely, VWO?)

### Customer Support

**Questions:**
1. Support channels? (Email only, live chat, Discord?)
2. Help center/knowledge base? (Intercom, Zendesk, custom?)
3. Support hours? (24/7, business hours, async only?)
4. SLA for premium users? (respond within X hours?)

### Compliance & Legal

**Questions:**
1. Legal review needed for terms/privacy policy?
2. DMCA agent registration required?
3. Tax handling for sales? (Stripe Tax, manual?)
4. International compliance? (GDPR, CCPA, etc.)
5. Age verification method? (checkbox, ID verification?)

### Community Guidelines

**Questions:**
1. Detailed community guidelines document needed?
2. Public examples of acceptable/unacceptable content?
3. Strike system details published to users?
4. Community moderators (volunteers)?
5. Transparency reports (bans/removals per month)?

### Future Considerations

**Questions:**
1. Mobile app? (iOS/Android) - When?
2. Browser extension? (Chrome/Firefox) - For what purpose?
3. Internationalization? (Multiple languages) - Priority languages?
4. White-label solution? (For agencies/companies)
5. Enterprise tier? (Custom features for teams)

---

## 🎯 Success Metrics

### Phase 1 Success Criteria (Pre-Launch)

**Technical:**
- [ ] Zero critical bugs in production
- [ ] Lighthouse score >90 (mobile & desktop)
- [ ] Page load time <2 seconds
- [ ] Zero security vulnerabilities
- [ ] 100% uptime during beta

**Content:**
- [ ] 500+ prompts uploaded (from beta testers)
- [ ] 50+ active beta users
- [ ] All 27 tags used at least 5 times each
- [ ] AI moderation accuracy >95%

**Readiness:**
- [ ] All legal pages complete
- [ ] All Phase 1 features tested
- [ ] Payment system tested (test mode)
- [ ] Email flows tested
- [ ] Mobile responsiveness verified

### Phase 2 Success Criteria (Launch Month)

**User Acquisition:**
- [ ] 1,000 total signups
- [ ] 300+ active users (posted/liked/commented)
- [ ] Referral rate >20% (users inviting friends)
- [ ] Retention: 40%+ return after 7 days

**Monetization:**
- [ ] 50+ trial starts
- [ ] 30+ paying customers (60% trial conversion)
- [ ] $210+ MRR (Monthly Recurring Revenue)
- [ ] <5% churn rate

**Content:**
- [ ] 2,000+ total prompts
- [ ] 50+ prompts uploaded daily
- [ ] 500+ comments across platform
- [ ] 5,000+ likes total

**Engagement:**
- [ ] Average session: 5+ minutes
- [ ] Average pages per session: 8+
- [ ] 100+ daily active users
- [ ] Comment rate: 10% of viewers

### Phase 3 Success Criteria (Growth)

**Scale:**
- [ ] 5,000+ total users
- [ ] 500+ active users daily
- [ ] 10,000+ total prompts
- [ ] 250+ paying customers
- [ ] $1,750+ MRR

**Community:**
- [ ] 500+ follow relationships
- [ ] 50+ users with 100+ followers
- [ ] 1,000+ daily prompt views
- [ ] Leaderboard competition (20+ users trying for top 3)

**Product:**
- [ ] PromptCoin economy balanced (earn/spend ratio healthy)
- [ ] API: 10+ developers using
- [ ] Collections: 100+ created
- [ ] <2% content moderation false positive rate

### Phase 4 Success Criteria (Scale)

**Revenue:**
- [ ] $5,000+ MRR
- [ ] 500+ paying customers
- [ ] Course/guidebook sales: $500+/month
- [ ] Affiliate revenue: $500+/month
- [ ] Marketplace GMV: $1,000+/month

**Scale:**
- [ ] 10,000+ total users
- [ ] 1,000+ daily active users
- [ ] 25,000+ total prompts
- [ ] 50,000+ monthly prompt views

**Platform Maturity:**
- [ ] AI bot helpful rate >80%
- [ ] Chatbot resolution rate >60% (without human support)
- [ ] Support response time <4 hours
- [ ] Feature request backlog prioritized
- [ ] A/B test results actionable

---

## 🔧 Development Best Practices

### Code Style

**Python/Django:**
- Follow PEP 8 style guide
- Type hints where helpful
- Docstrings for complex functions
- Meaningful variable names (not overly verbose)
- Keep views thin (logic in models/services)
- Use Django ORM (avoid raw SQL unless necessary)

**JavaScript:**
- ES6+ syntax
- Const/let (not var)
- Arrow functions
- Template literals
- Descriptive function names
- Comments for complex logic

**Templates:**
- Consistent indentation (2 spaces)
- Semantic HTML5 tags
- Accessibility attributes (ARIA labels, alt tags)
- DRY principle (use includes/extends)

**CSS:**
- Mobile-first approach
- Use Bootstrap utilities when possible
- Custom CSS in separate file
- BEM naming convention for custom classes
- Avoid !important

### Git Workflow

**Branches:**
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/feature-name` - New features
- `bugfix/bug-description` - Bug fixes
- `hotfix/critical-issue` - Urgent production fixes

**Commit Messages:**
Format: `<type>: <description>`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code refactoring
- `style` - CSS/UI changes
- `docs` - Documentation updates
- `test` - Test additions/changes
- `chore` - Maintenance tasks

**Examples:**
- `feat: Add AI comment moderation system`
- `fix: Resolve image upload validation error`
- `refactor: Optimize database queries for prompt list`
- `style: Update navbar responsive breakpoints`

### Testing Strategy

**Phase 1-2 (Manual Testing Priority):**
- [ ] Test all user flows manually
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile testing (iOS Safari, Android Chrome)
- [ ] Edge cases (empty states, errors, limits)

**Phase 3+ (Automated Testing):**
- [ ] Unit tests for critical functions
- [ ] Integration tests for API endpoints
- [ ] End-to-end tests for key user flows
- [ ] Performance testing (load testing)
- [ ] Security testing (penetration testing)

**Test Coverage Goal:** 70%+ by Phase 4

### Deployment Process

**Phase 1-2 (Manual Deployment):**
1. Test locally
2. Test in Heroku staging environment (if created)
3. Merge to `main`
4. Deploy to Heroku production
5. Smoke test production (verify key features)
6. Monitor error logs (Sentry, Heroku logs)

**Phase 3+ (CI/CD Pipeline):**
1. GitHub Actions on push to `develop`
2. Run tests automatically
3. Deploy to staging if tests pass
4. Manual approval for production deploy
5. Automated rollback if errors spike

### Security Best Practices

**Always:**
- [ ] Never commit secrets (.env files, API keys)
- [ ] Use Django's built-in CSRF protection
- [ ] Sanitize user input
- [ ] Validate file uploads (type, size)
- [ ] Rate limit API endpoints
- [ ] HTTPS only (redirect HTTP)
- [ ] Secure cookies (httponly, secure, samesite)
- [ ] Regular dependency updates (security patches)
- [ ] Content Security Policy headers
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (template auto-escaping)

---

## 📞 Contact & Resources

### Project Owner
- **Name:** [Your Name]
- **Email:** [Your Email]
- **Role:** Founder/Developer

### Key URLs
- **Domain:** promptfinder.net
- **Production:** https://promptfinder.net (after launch)
- **Current Staging:** https://mj-project-4-68750ca94690.herokuapp.com/
- **GitHub:** [Repository URL]
- **Heroku:** [Heroku Dashboard URL]
- **Cloudinary:** [Cloudinary Dashboard URL]

### Third-Party Services

**Essential:**
- Heroku (hosting)
- Cloudinary (media storage)
- Heroku PostgreSQL (database)
- OpenAI API (AI moderation, chatbot)
- Stripe (payments)
- Django Allauth (authentication)

**Email:**
- SendGrid / Mailgun (transactional emails)
- MailChimp / ConvertKit (marketing emails) - Phase 2+

**Analytics (Phase 2+):**
- Google Analytics or Plausible
- Google Search Console
- Mixpanel or Amplitude (product analytics)

**Monitoring (Phase 3+):**
- Sentry (error tracking)
- UptimeRobot (uptime monitoring)
- Cloudflare (DDoS protection, CDN)

### Documentation Resources

**Django:**
- Official docs: https://docs.djangoproject.com
- Django Allauth: https://django-allauth.readthedocs.io
- Django Taggit: https://django-taggit.readthedocs.io

**Cloudinary:**
- Docs: https://cloudinary.com/documentation
- Python SDK: https://cloudinary.com/documentation/django_integration
- AI Vision: https://cloudinary.com/documentation/cloudinary_ai_vision_addon

**Stripe:**
- Docs: https://stripe.com/docs
- Subscriptions: https://stripe.com/docs/billing/subscriptions/overview
- Testing: https://stripe.com/docs/testing

**OpenAI:**
- API docs: https://platform.openai.com/docs
- Moderation: https://platform.openai.com/docs/guides/moderation
- GPT-4: https://platform.openai.com/docs/models/gpt-4



**Terminology:**
- CC = Claude Code (VS Code extension for AI-assisted coding)


---

## 💻 Implementation Reference

### Trash Bin System Code Examples (Phase 2)

**Purpose:** This section provides complete code examples for implementing the soft delete / trash bin system. Use this as a reference when building the feature in Phase 2.

#### Database Model Changes

**File:** `prompts/models.py`

```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import cloudinary

class PromptManager(models.Manager):
    """Custom manager that excludes deleted prompts by default"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Prompt(models.Model):
    # ... your existing fields (title, slug, content, etc.) ...
    
    # Soft delete fields (Phase 2)
    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this prompt was moved to trash"
    )
    deleted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deleted_prompts',
        help_text="User who deleted this prompt"
    )
    
    # Custom managers
    objects = PromptManager()  # Default: excludes deleted
    all_objects = models.Manager()  # Includes deleted items
    
    class Meta:
        # Add indexes for performance
        indexes = [
            models.Index(fields=['deleted_at']),
            models.Index(fields=['author', 'deleted_at']),
        ]
    
    def soft_delete(self, user):
        """Move prompt to trash (soft delete)"""
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.status = 0  # Hide from public view
        self.save()
    
    def restore(self):
        """Restore prompt from trash"""
        self.deleted_at = None
        self.deleted_by = None
        self.status = 1  # Make public again
        self.save()
    
    def hard_delete(self):
        """Permanent deletion with Cloudinary cleanup"""
        # Delete image from Cloudinary first
        if self.featured_image:
            try:
                cloudinary.uploader.destroy(
                    self.featured_image.public_id,
                    resource_type='image' if self.is_image else 'video'
                )
            except Exception as e:
                print(f"Error deleting from Cloudinary: {e}")
        
        # Then delete from database
        self.delete()
    
    @property
    def days_until_permanent_deletion(self):
        """Calculate how many days until permanent deletion"""
        if not self.deleted_at:
            return None
        
        # Check user's tier for retention period
        retention_days = 30 if self.author.is_premium else 5
        expiry_date = self.deleted_at + timedelta(days=retention_days)
        days_remaining = (expiry_date - timezone.now()).days
        
        return max(0, days_remaining)
    
    @property
    def is_in_trash(self):
        """Check if prompt is currently in trash"""
        return self.deleted_at is not None
    
    @property
    def is_expiring_soon(self):
        """Check if expires in less than 24 hours"""
        days_left = self.days_until_permanent_deletion
        return days_left is not None and days_left < 1
```

#### URL Patterns

**File:** `prompts/urls.py`

```python
from django.urls import path
from . import views

app_name = 'prompts'

urlpatterns = [
    # ... your existing URL patterns ...
    
    # Trash bin URLs (Phase 2)
    path('trash/', views.trash_bin, name='trash_bin'),
    path('trash/<slug:slug>/restore/', views.prompt_restore, name='prompt_restore'),
    path('trash/<slug:slug>/delete/', views.prompt_permanent_delete, name='prompt_permanent_delete'),
    path('trash/empty/', views.empty_trash, name='empty_trash'),
]
```

#### View Functions

**File:** `prompts/views.py`

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Prompt

@login_required
def prompt_delete(request, slug):
    """Soft delete - move prompt to trash"""
    prompt = get_object_or_404(Prompt, slug=slug, author=request.user)
    
    if request.method == 'POST':
        prompt.soft_delete(request.user)
        
        retention_days = 30 if request.user.is_premium else 5
        messages.success(
            request, 
            f'"{prompt.title}" moved to trash. It will be permanently deleted in {retention_days} days. '
            f'<a href="{reverse("prompts:trash_bin")}">View Trash</a>',
            extra_tags='safe'
        )
        return redirect('prompts:prompt_list')
    
    context = {
        'prompt': prompt,
        'retention_days': 30 if request.user.is_premium else 5
    }
    return render(request, 'prompts/confirm_delete.html', context)


@login_required
def trash_bin(request):
    """Display user's trash bin"""
    user = request.user
    retention_days = 30 if user.is_premium else 5
    
    # Query deleted prompts
    if user.is_premium:
        # Premium: show all deleted items
        trashed = Prompt.all_objects.filter(
            author=user,
            deleted_at__isnull=False
        ).order_by('-deleted_at')
    else:
        # Free: limit to last 10 items only
        trashed = Prompt.all_objects.filter(
            author=user,
            deleted_at__isnull=False
        ).order_by('-deleted_at')[:10]
    
    # Add computed properties for each item
    for prompt in trashed:
        prompt.days_left = prompt.days_until_permanent_deletion
        prompt.is_expiring = prompt.is_expiring_soon
    
    trash_count = trashed.count()
    
    context = {
        'trashed_prompts': trashed,
        'trash_count': trash_count,
        'retention_days': retention_days,
        'is_premium': user.is_premium,
        'capacity_reached': trash_count >= 10 and not user.is_premium,
    }
    return render(request, 'prompts/trash_bin.html', context)


@login_required
def prompt_restore(request, slug):
    """Restore a prompt from trash"""
    prompt = get_object_or_404(
        Prompt.all_objects,  # Use all_objects to include deleted
        slug=slug, 
        author=request.user,
        deleted_at__isnull=False
    )
    
    if request.method == 'POST':
        prompt.restore()
        messages.success(
            request, 
            f'"{prompt.title}" restored successfully! '
            f'<a href="{reverse("prompts:prompt_detail", args=[slug])}">View prompt</a>',
            extra_tags='safe'
        )
        return redirect('prompts:trash_bin')
    
    return render(request, 'prompts/confirm_restore.html', {'prompt': prompt})


@login_required
def prompt_permanent_delete(request, slug):
    """Permanently delete a prompt (cannot be undone)"""
    prompt = get_object_or_404(
        Prompt.all_objects,
        slug=slug,
        author=request.user,
        deleted_at__isnull=False
    )
    
    if request.method == 'POST':
        title = prompt.title
        prompt.hard_delete()  # Deletes from Cloudinary + database
        
        messages.warning(
            request, 
            f'"{title}" permanently deleted. This cannot be undone.'
        )
        return redirect('prompts:trash_bin')
    
    return render(request, 'prompts/confirm_permanent_delete.html', {
        'prompt': prompt
    })


@login_required
def empty_trash(request):
    """Empty entire trash bin (delete all trashed items)"""
    if request.method == 'POST':
        trashed = Prompt.all_objects.filter(
            author=request.user,
            deleted_at__isnull=False
        )
        count = trashed.count()
        
        # Permanently delete all trashed items
        for prompt in trashed:
            prompt.hard_delete()
        
        messages.warning(
            request, 
            f'{count} items permanently deleted. This cannot be undone.'
        )
        return redirect('prompts:trash_bin')
    
    # Count for confirmation message
    trash_count = Prompt.all_objects.filter(
        author=request.user,
        deleted_at__isnull=False
    ).count()
    
    return render(request, 'prompts/confirm_empty_trash.html', {
        'trash_count': trash_count
    })
```

#### Daily Cleanup Management Command

**File:** `prompts/management/commands/cleanup_trash.py`

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from prompts.models import Prompt

class Command(BaseCommand):
    help = 'Permanently delete expired trashed prompts'
    
    def handle(self, *args, **options):
        now = timezone.now()
        deleted_count = 0
        deleted_items = []
        
        # Get all trashed prompts
        trashed_prompts = Prompt.all_objects.filter(deleted_at__isnull=False)
        
        self.stdout.write(f'Checking {trashed_prompts.count()} trashed items...')
        
        for prompt in trashed_prompts:
            # Determine retention period based on user tier
            retention_days = 30 if prompt.author.is_premium else 5
            expiry_date = prompt.deleted_at + timedelta(days=retention_days)
            
            # Check if expired
            if now >= expiry_date:
                self.stdout.write(
                    self.style.WARNING(
                        f'Deleting: {prompt.title} '
                        f'(expired {(now - expiry_date).days} days ago)'
                    )
                )
                
                deleted_items.append({
                    'title': prompt.title,
                    'author': prompt.author.username,
                    'deleted_at': prompt.deleted_at,
                })
                
                prompt.hard_delete()
                deleted_count += 1
        
        # Summary output
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Cleanup complete: {deleted_count} items permanently deleted'
            )
        )
        
        # Send admin notification if items were deleted
        if deleted_count > 0:
            try:
                send_mail(
                    subject=f'PromptFinder: {deleted_count} items cleaned from trash',
                    message=f'Daily cleanup completed:\n\n'
                            f'Items deleted: {deleted_count}\n\n'
                            f'Details:\n' + 
                            '\n'.join([f"- {item['title']} by {item['author']}" 
                                      for item in deleted_items]),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS('Admin notification sent')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not send admin email: {e}')
                )
```

#### Heroku Scheduler Setup

Steps to add the daily cleanup task:

1. **Add Heroku Scheduler (free add-on):**
   ```bash
   heroku addons:create scheduler:standard --app mj-project-4
   ```

2. **Open scheduler dashboard:**
   ```bash
   heroku addons:open scheduler --app mj-project-4
   ```

3. **In the dashboard, add a new job:**
   - **Command:** `python manage.py cleanup_trash`
   - **Frequency:** Daily at 4:00 AM (or your preferred time)
   - **Dyno size:** Standard-1X (uses Eco Dyno hours)

**Cost:** $0/month (uses spare Eco Dyno hours)  
**Runtime:** ~1-5 minutes depending on number of trashed items

#### Database Migration Example

**File:** Generated by Django when you run `python manage.py makemigrations`

```python
# This is an example of what Django will generate
# prompts/migrations/0XXX_add_trash_bin_fields.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('prompts', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='prompt',
            name='deleted_at',
            field=models.DateTimeField(
                blank=True, 
                help_text='When this prompt was moved to trash', 
                null=True
            ),
        ),
        migrations.AddField(
            model_name='prompt',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True,
                help_text='User who deleted this prompt',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_prompts',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(
                fields=['deleted_at'], 
                name='prompts_deleted_at_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='prompt',
            index=models.Index(
                fields=['author', 'deleted_at'],
                name='prompts_author_deleted_idx'
            ),
        ),
    ]
```

**To apply migration:**
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Notes for Implementation

**When implementing in Phase 2:**

1. Create the database fields and migration first
2. Update existing delete views to use `soft_delete()` instead of `.delete()`
3. Build the trash bin page UI
4. Add the management command
5. Set up Heroku Scheduler
6. Test thoroughly before deploying

**Testing Checklist:**

- [ ] Soft delete moves item to trash (doesn't actually delete)
- [ ] Trash bin shows correct retention days per user tier
- [ ] Restore works correctly
- [ ] Permanent delete removes from Cloudinary
- [ ] Free users see only 10 items
- [ ] Premium users see unlimited items
- [ ] Daily cleanup script runs successfully
- [ ] Notifications work correctly

---

## 🚀 Pre-Launch Tasks

**To complete before major production launch:**

### Required Before Launch

- [ ] **Squash migrations** - Currently 37 migrations in `prompts/migrations/`
  - Run: `python manage.py squashmigrations prompts <start> <end>`
  - Test thoroughly after squashing
  - Only do this once, right before launch
  - Estimated time: 2-3 hours

- [ ] **Final security audit** - Run comprehensive security scan
  - Bandit SAST scan (already in CI)
  - pip-audit dependency check (already in CI)
  - Manual review of secrets management
  - Estimated time: 2-4 hours

- [ ] **Performance testing under load** - Stress test with realistic traffic
  - Use locust or similar tool
  - Test critical paths: homepage, upload, search
  - Verify database query performance
  - Estimated time: 4-6 hours

### Nice-to-Have Before Launch

- [ ] **CSS Cleanup Phase 2** - Extract remaining inline styles from 17 templates
- [ ] **Uptime monitoring** - Set up external monitoring service
- [ ] **Canonical tags** - Add missing canonical tags for SEO

---

## 🏥 Project Health Checkup Protocol

### Overview

Periodic audits ensure documentation accuracy, codebase organization, and identify technical debt before it accumulates. This protocol establishes standardized health checks for the PromptFinder project.

### Audit Types

| Type | Frequency | Duration | Focus |
|------|-----------|----------|-------|
| **Quick Check** | Weekly | 15-30 min | File counts, test status, obvious issues |
| **Phase Audit** | After each phase | 1-2 hours | Documentation accuracy, phase completion |
| **Deep Audit** | Monthly/Quarterly | 4-8 hours | Full codebase review, agent validation |

### Quick Check Checklist (Weekly)

- [ ] Run `python manage.py test` - All tests passing?
- [ ] Check git status - Any uncommitted changes?
- [ ] Verify Heroku scheduler jobs running (check logs)
- [ ] Review error monitoring (when Sentry added)
- [ ] Quick file count sanity check

### Phase Audit Checklist (After Each Phase)

- [ ] Update PROJECT_FILE_STRUCTURE.md with accurate counts
- [ ] Update CLAUDE.md with phase completion status
- [ ] Move session/phase documents to archive
- [ ] Run agent validation (minimum 2 agents, 8+/10 required)
- [ ] Verify all tests passing
- [ ] Check for orphaned files in root directory
- [ ] Update Known Technical Debt section if needed

### Deep Audit Checklist (Monthly/Quarterly)

- [ ] Full file structure audit with agent validation
- [ ] Performance audit (views.py size, query optimization)
- [ ] Security audit (dependencies, vulnerabilities)
- [ ] Documentation accuracy review
- [ ] Archive cleanup (delete old session files)
- [ ] Migration squashing assessment
- [ ] CI/CD pipeline status
- [ ] Error monitoring review

### Agent Validation Requirements

**Required Agents by Task:**

| Task | Agents | Minimum Rating |
|------|--------|----------------|
| Documentation updates | @code-reviewer | 8+/10 |
| Django changes | @code-reviewer, @django-pro | 8+/10 each |
| Performance changes | @performance-expert, @code-reviewer | 8+/10 each |
| Security changes | @security-auditor, @code-reviewer | 9+/10 each |
| Full audit | 3+ agents | 8+/10 average |

### Last Audit Results

**Date:** December 13, 2025 (Post-Infrastructure Session)
**Type:** Deep Audit + Infrastructure Implementation
**Agent Ratings:**
- @code-reviewer: 8.5/10
- @django-pro: 9.5/10
- @devops-troubleshooter: 9.5/10
- **Average:** 9.17/10 ✅ (exceeded 8+ threshold)

**Issues Resolved This Session:**
1. ✅ views.py split into 11 modular view files
2. ✅ CI/CD pipeline operational (GitHub Actions, 3 jobs)
3. ✅ Sentry error monitoring added
4. ✅ Root directory cleaned up
5. ✅ Test suite expanded to 234 tests

**Remaining Issues:**
1. 37 migrations should be squashed before launch
2. CI annotations (cosmetic, non-blocking)
3. CSS Cleanup Phase 2 (17 templates with inline styles)

**Next Audit Due:** January 2026 (or after next major phase)

---

## 📋 Known Technical Debt

### Critical Priority (Address Before Launch)

| Issue | Impact | Effort | Status |
|-------|--------|--------|--------|
| `views.py` at 147KB (~3,929 lines) | Maintenance nightmare, slow IDE | 4-8 hours | ✅ RESOLVED (Dec 13, 2025) |
| No CI/CD pipeline | Manual deployments, no automated testing | 2-4 hours | ✅ RESOLVED (Dec 13, 2025) |
| No error monitoring | Blind to production errors | 1 hour | ✅ RESOLVED (Dec 13, 2025) |

### High Priority (Address Within 1 Month)

| Issue | Impact | Effort | Status |
|-------|--------|--------|--------|
| 37 migrations unsquashed | Slow migration runs | 2 hours | ⏳ Planned |
| `base.html` inline styles (~2000 lines) | Not cached, maintenance issues | 2-4 hours | ⏳ Planned |
| CSS Cleanup Phase 2 (17 templates) | Inline styles in templates | 2-3 days | 📋 Documented |

### Medium Priority (Address Within 3 Months)

| Issue | Impact | Effort | Status |
|-------|--------|--------|--------|
| Dual upload systems | Maintenance overhead | 2-3 days | 📋 Documented |
| Missing canonical tags | SEO incomplete | 1 hour | ⏳ Planned |
| No uptime monitoring | Unaware of outages | 30 min | ⏳ Planned |
| Profile page rapid-click bug | Like count desync on fast clicks | 1-2 hours | 📋 Documented |
| Duplicate title IntegrityError | Upload fails on duplicate AI title | 1-2 hours | 📋 Documented |

**Duplicate Title IntegrityError Bug Details:**
- **Symptom:** `IntegrityError: duplicate key value violates unique constraint "prompts_prompt_slug_key"`
- **Root Cause:** AI generates same title for similar images (e.g., "Majestic Lion Portrait"), slug collision occurs
- **Location:** `upload_views.py` in `upload_submit()` function
- **Current Workaround:** None - upload fails with 500 error
- **Proposed Fix:** Add retry logic with title suffix (e.g., "Majestic Lion Portrait 2")
- **Alternative Fix:** Use UUID suffix for all slugs
- **Priority:** Medium - affects uploads with common AI-generated titles

**Profile Page Rapid-Click Bug Details:**
- **Symptom:** On profile page, rapidly clicking the like button can cause count to desync
- **Root Cause:** Profile page uses `like-button.js` which has debounced server sync, but the optimistic UI update can get out of sync during rapid clicks
- **Workaround:** Page refresh corrects the count
- **Fix:** Add request queuing or mutex to prevent concurrent like requests for same prompt
- **Priority:** Low - affects edge case only (rapid clicking)

### Low Priority (Future Improvements)

| Issue | Impact | Effort | Status |
|-------|--------|--------|--------|
| Template file renames | Consistency (inspiration_index → prompts_hub) | 1 hour | 💡 Nice-to-have |
| View function renames | Consistency (inspiration_index → prompts_hub) | 30 min | 💡 Nice-to-have |
| Additional test coverage | Quality assurance | Ongoing | 📋 Documented |

### Resolved Technical Debt

| Issue | Resolution | Date |
|-------|------------|------|
| `views.py` monolith (3,929 lines) | Split into modular package (11 files) | Dec 13, 2025 |
| No CI/CD pipeline | GitHub Actions with 3 parallel jobs | Dec 13, 2025 |
| No error monitoring | Sentry integration (production) | Dec 13, 2025 |
| Navbar JS in base.html (~650 lines) | Extracted to `static/js/navbar.js` | Dec 13, 2025 |
| Root directory clutter (30+ MD, 14 Python) | Moved to /archive/ and /scripts/ | Dec 13, 2025 |
| PROJECT_FILE_STRUCTURE.md outdated | Updated with accurate counts | Dec 13, 2025 |
| Orphaned Cloudinary files | Detection command implemented | Oct 2025 |
| Missing PromptView import | Fixed in Phase I | Dec 2025 |
| Avatar orphaned files (Cloudinary) | AvatarChangeLog audit trail + signals | Dec 19, 2025 |

### Future Feature: Admin Dashboard for Avatar Analytics

**Status:** 📋 DOCUMENTED (Infrastructure Ready)
**Added:** December 19, 2025
**Priority:** Low (Phase 4+)
**Effort:** 2-3 days

**Infrastructure Completed:**
- ✅ `AvatarChangeLog` model tracks all avatar changes
- ✅ `AvatarChangeLogAdmin` provides read-only audit interface
- ✅ Signal handlers create log entries automatically
- ✅ Database index on `(user, -created_at)` for efficient queries

**Future Dashboard Features:**
When this dashboard is implemented, it could leverage the `AvatarChangeLog` data for:

| Feature | Data Source | Description |
|---------|-------------|-------------|
| Avatar Activity Chart | `AvatarChangeLog.created_at` | Line chart showing avatar changes over time |
| Action Distribution | `AvatarChangeLog.action` | Pie chart: uploads vs replacements vs deletions |
| Failed Deletions Alert | `action='delete_failed'` | List of Cloudinary sync issues needing attention |
| User Avatar History | Filter by `user` | Timeline of a specific user's avatar changes |
| Orphan Detection | `old_public_id` analysis | Cross-reference with Cloudinary for orphans |

**Query Examples for Dashboard:**
```python
# Total avatar changes by action type
AvatarChangeLog.objects.values('action').annotate(count=Count('id'))

# Failed deletions requiring attention
AvatarChangeLog.objects.filter(action='delete_failed').select_related('user')

# Avatar changes in last 30 days
AvatarChangeLog.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))

# Most active avatar changers
AvatarChangeLog.objects.values('user__username').annotate(
    changes=Count('id')
).order_by('-changes')[:10]
```

**Implementation Notes:**
- Consider Chart.js or similar for visualizations
- Add to existing Django admin or create custom dashboard view
- May integrate with broader "Admin Analytics" feature

### CI/CD Annotations (Non-Critical)

**Status:** Low priority - CI passes, these are cosmetic issues

| Annotation | Cause | Impact |
|------------|-------|--------|
| Security Scan shows red X | Uses `continue-on-error: true` by design | Visual only, job passes |
| Coverage artifact upload warning | `.coverage` file path issue | Coverage runs, artifact doesn't upload |

**Note:** These annotations don't affect CI functionality. All 3 jobs (Django Tests, Code Linting, Security Scan) pass successfully.

---

## 🎬 Getting Started (For Future Claude Instances)

### When Starting a New Chat About PromptFinder:

**Read this document first**, then:

1. **Check current phase:** Are we in Phase 1, 2, 3, or 4?
2. **Review decisions made:** Don't revisit settled decisions unless explicitly asked
3. **Check unanswered questions:** Prioritize addressing these if relevant
4. **Understand context:** This is a real project transitioning to monetization
5. **Be specific:** Provide actionable advice, code examples, timelines
6. **Prioritize:** Always consider what's critical vs nice-to-have
7. **Remember the brand:** Users are "Prompt Finders," domain is promptfinder.net

### Quick Reference Commands

**"Where are we?"**
→ Check Phase status, recent progress

**"What's next?"**
→ Review current phase priorities, upcoming tasks

**"Why did we decide X?"**
→ Check Decisions Made section

**"How much will Y cost?"**
→ Check Infrastructure & Costs section

**"When do we implement Z?"**
→ Check Development Phases section

**"What's the SEO strategy for X?"**
→ Check SEO Strategy section

**"How does moderation work?"**
→ Check Content Moderation section

### Project Philosophy

**Core Principles:**
1. **Users first:** Every decision prioritizes user experience
2. **Monetization matters:** We're building a sustainable business
3. **SEO is critical:** Discovery-focused platform needs great SEO
4. **Safety always:** Zero tolerance for harmful content
5. **Start simple:** MVP features first, polish later
6. **Data-driven:** A/B test, measure, iterate
7. **Professional:** Build for paying customers, not hobby project

**What We're Building:**
A professional, safe, profitable platform where prompt finders discover perfect AI prompts. We're competing with generic Google searches and scattered Discord servers by offering curated, organized, SEO-optimized prompt discovery.

**What We're NOT Building:**
- Social media platform (light social features only)
- NSFW content site (strict moderation)
- Free-forever charity (we need revenue)
- Feature-bloated complexity (focused simplicity)

---

## 📝 Changelog

### January 2026 - Session 39 (Jan 8, 2026)

**Critical Fixes: Variant Race Condition, DB Save, AI Suggestions - ALL RESOLVED ✅**

Session 39 resolved all three critical blockers discovered in Sessions 37-38, completing Phase L to ~98%:

**Fix 1: Variant Race Condition (9.0/10)** - Commit `35ca8f2`
- **Problem:** `/api/upload/b2/variants/` returned 400 "No pending upload found"
- **Root Cause:** AJAX call happened before `complete/` endpoint set session keys
- **Solution:** Pass B2 URL as query parameter instead of relying on session
- **Files:** `upload_step2.html`, `api_views.py`

**Fix 2: Variants Not Saving to DB (8.5/10)** - Commit `a2f8539`
- **Problem:** Variant URLs generated but not saved to prompt model
- **Root Cause:** `upload_submit()` checked only `variant_urls` dict, but AJAX stored individual `b2_*_url` keys
- **Solution:** Added dual-source session check (dict OR individual keys)
- **File:** `prompts/views/upload_views.py`

**Fix 3: AI Suggestions 500 Error (9.2/10)** - Commit `d450e45`
- **Problem:** `/api/upload/ai-suggestions/` returned 500 Internal Server Error
- **Root Cause:** OpenAI Vision API requires base64-encoded image data, was receiving raw URL
- **Solution:** Fetch image via requests, encode as base64 data URI
- **File:** `prompts/views/api_views.py`

**Agent Ratings:**
| Fix | Agent | Rating |
|-----|-------|--------|
| Variant Race Condition | @backend-architect | 9.0/10 |
| Variants Not Saving | @django-pro | 8.5/10 |
| AI Suggestions 500 | @code-reviewer | 9.2/10 |
| **Average** | | **8.9/10** |

**Phase L Status:** ~98% complete (variant fixes complete, only L11 documentation remaining)

---

### January 2026 - Session 40 (Jan 9, 2026)

**L10 SEO Review Infrastructure: Silent AI Failure Pattern ✅ COMPLETE**

Session 40 implemented the L10 SEO Review Infrastructure, establishing a "silent failure" pattern where AI failures are invisible to users. When OpenAI Vision fails, uploads succeed normally but are flagged for admin SEO review.

**L10a: Model Field + API Flag**
- Added `needs_seo_review` BooleanField to Prompt model
- Migration: `0042_prompt_needs_seo_review.py`
- API returns `ai_failed: true` flag (frontend ignores, populates defaults)

**L10b: Silent AI Failure UX (4 fixes)**

| Fix | Commit | Description |
|-----|--------|-------------|
| L10b-FIX | b5a0860 | Hide error details, show subtle message |
| L10b-FIX2 | 8bf4be6 | Remove all AI failure UI indicators |
| L10b-FIX3 | fbddaf5 | Remove API key exposure from error messages |
| L10b-FIX4 | dcfcba3 | Hide content notice banner for processing errors |

**L10c: Admin SEO Review Queue**
- Route: `/admin/seo-review/` - List prompts needing review
- Route: `/admin/seo-complete/<id>/` - Mark as reviewed
- Template: `prompts/templates/admin/seo_review_queue.html`
- Staff-only access with `@staff_member_required`

**Security Fix:**
- Removed `OPENAI_API_KEY` substring exposure from user-facing error messages
- Generic error messages replace detailed API errors

**Commits (8 total):**
- `e572254` - L10a model field
- `59959cb` - L10a API flag
- `7a6e365` - L10c admin queue
- `b5a0860` - L10b-FIX subtle messages
- `8bf4be6` - L10b-FIX2 remove UI indicators
- `fbddaf5` - L10b-FIX3 security fix
- `dcfcba3` - L10b-FIX4 hide banner
- `9236e26` - L10c admin queue finalization

**Agent Ratings:**
| Component | Agent | Rating |
|-----------|-------|--------|
| Documentation | @doc-writer | 8.5/10 |
| Code Review | @code-reviewer | 8.5/10 |
| **Average** | | **8.5/10** |

**Phase L Status:** ~98% complete (L10 complete, only L11 documentation remaining)

---

### January 2026 - Session 42 (Jan 10, 2026)

**Phase L/M: B2 Video Display Fixes & Layout Shift Investigation**

Session 42 completed critical fixes for video display in the B2 infrastructure and documented a video layout shift issue for future resolution.

**L10c-FIX2: Admin Index URL Error**
- Fixed NoReverseMatch error on Django admin index page
- SEO Review Queue link in admin dashboard now works correctly

**M1-FIX: Video Thumbnail URL Session Handling**
- Added `b2_video_thumb_url` session key in `b2_upload_complete()` view
- Video thumbnails now properly passed from Step 1 to Step 2 via session storage
- File: `prompts/views/api_views.py`

**M1-FIX2: B2 Video Display on Prompt Detail Page**
- Fixed prompt detail page showing Cloudinary video URL instead of B2 URL
- Updated template to use B2-first pattern: `{{ prompt.display_video_url }}`
- File: `prompts/templates/prompts/prompt_detail.html`

**Video Layout Shift Investigation (M1-FIX3 - Rejected)**
- Attempted fix: Forced 16:9 aspect ratio container with `object-fit: contain`
- Result: Caused ugly letterboxing for vertical (9:16) videos
- Decision: Reverted to commit `7fc11b9`, accepted minor layout shift for MVP

**Commits (chronological):**
- `7b43ef8` - fix(phase-l): Fix admin index URL error (L10c-FIX2)
- `0bf7e43` - docs: Update CLAUDE.md for L10c completion (v2.17)
- `fc2ffa0` - fix(phase-l): Fix B2 video display on prompt detail page (M1-FIX2)
- `7fc11b9` - docs: Add M1-FIX2 investigation and completion reports
- `3ce8938` - docs(phase-m): Document video layout shift known issue

**Files Modified:**
- `prompts/views/api_views.py` - Video thumbnail session handling
- `prompts/templates/prompts/prompt_detail.html` - B2-first video display
- `CLAUDE.md` - Documentation updates
- `docs/reports/` - Investigation and completion reports

**Agent Ratings:**
| Component | Agent | Rating |
|-----------|-------|--------|
| M1-FIX session handling | @django-pro | 8.5/10 |
| M1-FIX2 template fix | @frontend-developer | 9.0/10 |
| Documentation | @doc-writer | 8.5/10 |
| **Average** | | **8.7/10** |

**Phase L Status:** ~98% complete (L11 documentation remaining)
**Phase M Status:** Video uploads functional, layout shift documented as known issue

---

### January 2026 - Session 48 (Jan 13, 2026)

**M5 Video Dimensions CLS Prevention: COMPLETE ✅**

Session 48 resolved the video layout shift issue that was deferred in Session 42. The solution extracts video dimensions during upload and uses CSS `aspect-ratio` for zero-CLS video display.

**M5-A: Model Fields + Migration**
- Added `video_width` and `video_height` IntegerFields to Prompt model
- Migration: `0043_prompt_video_height_prompt_video_width.py`
- Fields nullable for backwards compatibility with existing prompts

**M5-B: FFmpeg Dimension Extraction**
- Added `get_video_dimensions()` function to `video_processor.py`
- Uses FFprobe JSON output for reliable dimension extraction
- Returns `(width, height)` tuple or `(None, None)` on failure
- Integrated into `b2_upload_complete()` API endpoint

**M5-C: Session Storage + Template Integration**
- Session keys: `video_width`, `video_height` stored after dimension extraction
- `upload_submit()` view reads session and saves to Prompt model
- Template uses `aspect-ratio: {{ prompt.video_width }}/{{ prompt.video_height }}` for CLS prevention

**Video Thumbnail Aspect Ratio Fix**
- Fixed thumbnail generation to preserve aspect ratio
- Thumbnail constraint: max 600px on longest side (was always 600x600 square crop)
- Prevents distortion on portrait/landscape videos

**New Management Command: `regenerate_video_thumbnails`**
- Regenerates thumbnails for existing Cloudinary videos with correct aspect ratio
- Supports `--dry-run` mode for safe testing
- Filters: `--limit N`, prompts with `b2_video_url` IS NULL and `featured_video` IS NOT NULL

**Video NSFW Moderation Planning Update (M1/M2)**
- Reduced frame extraction from 5 frames to 3 frames
- Extraction points: 25%, 50%, 75% of video duration (was 20%, 40%, 60%, 80%)
- Rationale: 3 frames provides sufficient coverage while reducing API costs

**Files Modified:**
- `prompts/models.py` - Added `video_width`, `video_height` fields
- `prompts/services/video_processor.py` - `get_video_dimensions()`, thumbnail aspect ratio fix
- `prompts/views/api_views.py` - Dimension extraction in `b2_upload_complete()`
- `prompts/views/upload_views.py` - Session retrieval, model save
- `prompts/templates/prompts/prompt_detail.html` - CSS `aspect-ratio` property
- `prompts/management/commands/regenerate_video_thumbnails.py` - NEW

**Phase M Status:** M5 complete, video CLS issue resolved

---

### January 2026 - Session 38 (Jan 5-6, 2026)

**L5e Complete + Session Management + Critical Blocker Discovery → RESOLVED in Session 39**

Session 38 completed Phase L5e (Edit Form B2 Integration) and implemented robust session clearing. Critical issues discovered were resolved in Session 39:

**L5e-TEMPLATE: Edit Form B2-First Image Display (9.5/10)**
- Updated `prompt_edit.html` to use B2-first image display pattern
- Pattern: `{{ prompt.display_medium_url|default:prompt.featured_image.url }}`
- Cloudinary fallback ensures backward compatibility
- File: `prompts/templates/prompts/prompt_edit.html`

**L5e-VIEW: Edit Form B2 Upload Logic (9.0/10)**
- Added B2 URL assignment in `prompt_edit()` view
- Retrieves B2 URLs from session keys: `b2_secure_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`, `b2_webp_url`
- Clears session after successful save
- File: `prompts/views/prompt_views.py`

**Session Clearing Implementation (8.85/10)**
- Created `clear_upload_session()` helper function
- Clears 13 session keys to prevent data bleed between uploads
- Keys cleared: `b2_secure_url`, `b2_thumb_url`, `b2_medium_url`, `b2_large_url`, `b2_webp_url`, `b2_pending_upload`, `pending_variant_image`, `pending_variant_filename`, `variant_urls`, `variants_complete`, `cloudinary_id`, `cloudinary_secure_url`, `is_video`
- Applied to: `upload_submit()`, `prompt_edit()` on successful save

**Critical Blocker Discovered: Variant Race Condition → ✅ RESOLVED (Session 39)**
- **Symptom:** `/api/upload/b2/variants/` returns 400 Bad Request
- **Error:** "No pending upload found in session"
- **Root Cause:** `upload_step2.html` AJAX calls `variants/` before `complete/` sets session keys
- **Impact:** Blocked all variant generation for B2 uploads
- **Status:** ✅ RESOLVED - See Session 39 for fix details

**Agent Ratings:**
| Component | Agent | Rating |
|-----------|-------|--------|
| L5e-TEMPLATE | @frontend-developer | 9.5/10 |
| L5e-VIEW | @django-pro | 9.0/10 |
| Session Clearing | @code-reviewer | 8.85/10 |
| **Average** | | **9.12/10** |

**Phase L Status:** ~96% at end of session (race condition resolved in Session 39)

---

### January 2026 - Session 37 (Jan 5, 2026)

**L8-STEP2-PERF: Deferred AI Suggestions**

Session 37 completed the L8-STEP2-PERF feature, dramatically improving Step 2 page load times by deferring AI content generation to an AJAX call:

**Problem Solved:**
- Step 2 page took ~8 seconds to load due to synchronous AI analysis
- Users experienced long wait times before seeing the upload form

**Solution Implemented:**
- Page loads immediately with placeholder "Generating suggestions..." text
- AI suggestions fetched asynchronously via new `/api/upload/ai-suggestions/` endpoint
- Form fields populate dynamically when suggestions arrive
- Non-blocking UX with graceful fallback on timeout/error

**Performance Improvement:**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Step 2 page load | ~8 seconds | <1 second | **87% faster** |
| AI suggestions | Blocking | Background AJAX | Non-blocking UX |

**New API Endpoint:**
- `GET /api/upload/ai-suggestions/` - Deferred AI content suggestions
- Reads image URL from session (`b2_secure_url` or `cloudinary_secure_url`)
- Uses `ContentGenerationService.analyze_image_only()` for image-only analysis
- Returns title, description, and suggested tags

**Files Modified:**
- `prompts/views/api_views.py` - New `ai_suggestions` view (+75 lines)
- `prompts/services/content_generation.py` - New `analyze_image_only()` method
- `prompts/templates/prompts/upload_step2.html` - AJAX integration for deferred suggestions
- `prompts/views/__init__.py` - Export new view
- `prompts/urls.py` - New route `/api/upload/ai-suggestions/`

**Technical Implementation:**
- Session-based data passing for multi-step upload flow
- Supports both B2 (`b2_secure_url`) and Cloudinary (`cloudinary_secure_url`) sources
- 30-second timeout with graceful degradation
- Returns empty suggestions on error (non-blocking)

**Phase L Status:** ~95% complete (was ~75%)

---

### January 2026 - Session 34 (Jan 1, 2026)

**Phase L8-DIRECT: Direct Browser-to-B2 Uploads**

Session 34 completed L8-DIRECT implementation, eliminating Heroku as middleman for file uploads:

**Direct Browser-to-B2 Upload System**
- Created `b2_presign_service.py` (240 lines) - Presigned URL generation for secure direct uploads
- New API endpoints: `b2_presign_upload`, `b2_upload_complete`, `b2_generate_variants`
- Browser uploads directly to Backblaze B2 via presigned URLs
- B2 CORS configuration via `cors-rules.json` for cross-origin browser uploads

**Deferred Variant Generation**
- `complete/` endpoint simplified to verification only (~1s vs 7-8s before)
- Image variants (thumb, medium, large, webp) generate in background on Step 2
- Event-driven submit guard replaces busy-wait polling
- HTTP status checking added before JSON parsing for robustness

**Performance Improvement**
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Step 1 → Step 2 | ~23 seconds | ~10-11 seconds | **52% faster** |
| `complete/` endpoint | 7-8 seconds | ~1 second | **85% faster** |
| Variant generation | Blocking | Background | Non-blocking UX |

**Files Created:**
- `prompts/services/b2_presign_service.py` - Presigned URL service
- `prompts/tests/test_b2_presign.py` - 22 comprehensive tests
- `cors-rules.json` - B2 CORS configuration

**Files Modified:**
- `prompts/views/api_views.py` - New presign/complete/variants endpoints
- `prompts/templates/prompts/upload_step1.html` - Direct B2 upload JavaScript
- `prompts/templates/prompts/upload_step2.html` - Background variants + submit guard
- `prompts/views/upload_views.py` - pending_variants detection
- `prompts_manager/settings.py` - CSP updates for B2 domains

**Agent Validation:**
- @django-pro: 8.8/10
- @code-reviewer: 7.8/10
- @frontend-developer: 8.5/10
- **Average: 8.4/10** ✅

**Commit:** `feat(L8-DIRECT): Implement direct browser-to-B2 uploads with deferred variant generation`

**Key Learning:** L8-INSTANT (instant redirect with IndexedDB) was attempted but reverted due to blob URL navigation issues. Simple performance improvements (deferred variants) proved more reliable than complex architecture changes.

---

### January 2026 - Session 35 (Jan 2, 2026)

**L8-PROGRESS, L8-TIMEOUT, L8-ERRORS: Upload UX & Error Handling**

Session 35 completed three L8 sub-specs focused on upload user experience and error handling:

**L8-PROGRESS: Visual Progress Indicator**
- 5-step progress bar: Uploading → Processing → AI Analysis → Finalizing → Complete
- Each step updates dynamically during upload flow
- Visual feedback reduces perceived wait time

**L8-PROGRESS-ANIMATE: Animated Finalizing State**
- Subtle pulse animation during "Finalizing" step
- CSS keyframe animation for status text
- User feedback that system is actively working

**L8-TIMEOUT: OpenAI API Timeout Handling**
- Added `OPENAI_TIMEOUT = 30` constant to `prompts/constants.py`
- Configured OpenAI clients with 30-second timeout
- Graceful degradation: Returns `pending_review` status on timeout (security-first)
- Content NOT auto-approved on timeout - flagged for manual review
- Fallback values: "Untitled Upload" title, empty tags

**L8-ERRORS: Rate Limit Documentation**
- B2 API rate limit: 20 uploads/hour per user
- Weekly upload limit: 100/week (testing), 10/week (production)
- Documented in `api_views.py` (lines 33-66) and `upload_views.py` (lines 19-49)
- User-facing error message mapping

**Files Modified:**
- `prompts/templates/prompts/upload_step1.html` - Progress bar UI, animation CSS
- `prompts/constants.py` - Added `OPENAI_TIMEOUT = 30`
- `prompts/services/cloudinary_moderation.py` - Timeout handling, graceful degradation
- `prompts/services/content_generation.py` - Timeout handling, fallback values
- `prompts/views/api_views.py` - Rate limit documentation
- `prompts/views/upload_views.py` - Weekly limit documentation

**Reports Created:**
- `docs/reports/L8_TIMEOUT_COMPLETION_REPORT.md` - Comprehensive timeout implementation docs
- `docs/reports/L8_PROGRESS_ANIMATE_REPORT.md` - Animation implementation details
- `docs/reports/L8_ERRORS_RATE_LIMIT_REPORT.md` - Rate limiting documentation

**Agent Validation:**
| Agent | Rating | Verdict | Key Feedback |
|-------|--------|---------|--------------|
| @frontend-developer | 8.5/10 | ✅ APPROVED | Progressive feedback excellent, AbortController properly implemented |
| @backend-architect | 9.0/10 | ✅ APPROVED | Graceful degradation pattern correct, timeout values appropriate |
| @code-reviewer | 8.5/10 | ✅ APPROVED | Clean implementation, good error handling, proper logging |
| **Average** | **8.67/10** | ✅ | Exceeds 8.0 threshold |

**Phase L Status:** ~91% complete (L8 error handling complete, L5e and L11 remaining)

---

### January 2026 - Session 36 (Jan 3, 2026)

**L8-TIMING-DIAGNOSTICS: Upload Flow Investigation & NSFW Gate Analysis**

Session 36 investigated the slow Step 1 → Step 2 transition and NSFW blocking issues:

**Upload Timing Investigation:**
- Step 1 JavaScript: Fast (~4.3 seconds for presign + B2 upload + complete)
- Step 2 Django: Slow (~8 seconds before HTML returns)
- Root cause: `upload_step2()` view makes 2 blocking AI API calls before returning HTML
- Solution path: Defer AI calls to client-side AJAX after page load

**NSFW Gate Investigation:**
- Root cause identified: L8-TIMEOUT exception handlers return `status: 'pending_review'`
- Orchestrator blocking logic only checks for `status: 'rejected'`
- Fix required: Change timeout handlers to return `status: 'rejected'` (fail-closed security)
- Full report: `docs/reports/NSFW_GATE_INVESTIGATION_REPORT.md`

**New API Endpoints:**
- `POST /api/upload/b2/moderate/` - NSFW moderation check for uploaded images
- `DELETE /api/upload/b2/delete/` - Delete B2 object if moderation fails

**New Management Command:**
- `test_api_latency` - Tests B2 and OpenAI API response times for diagnostics

**Files Modified:**
- `prompts/views/api_views.py` - Added `b2_moderate_upload()` and `b2_delete_upload()` functions
- `prompts/services/cloudinary_moderation.py` - NSFW DEBUG logging, severity definitions
- `prompts/constants.py` - `OPENAI_TIMEOUT = 30` centralized

**Reports Created:**
- `docs/reports/NSFW_GATE_INVESTIGATION_REPORT.md` - Root cause analysis
- `docs/reports/L8_TIMING_INVESTIGATION_FINAL_REPORT.md` - Timing diagnostics

**Known Issues (Remaining):**
- NSFW blocking: Timeout handlers return wrong status (fix identified, not yet applied)
- Step 2 slow load: 8s due to blocking AI calls (solution: defer to AJAX)
- Video uploads: 95-225 second delays expected (FFmpeg processing)

**Phase L Status:** ~75% complete (NSFW gate fix needed, Step 2 optimization needed)

---

### January 2026 - Session 37 (Jan 3, 2026)

**NSFW Moderation System Fixes & Security Hardening**

Session 37 completed critical fixes to the B2/OpenAI Vision moderation system:

**CSRF Token Fix:**
- Fixed 403 Forbidden errors on `/api/upload/b2/moderate/` endpoint
- Root cause: Frontend wasn't sending CSRF token with moderation request
- Solution: Added `X-CSRFToken` header using Django's `csrftoken` cookie

**Domain Validation Security:**
- Added `ALLOWED_CDN_DOMAINS` list to validate image URLs before moderation
- Prevents SSRF attacks by restricting URLs to known CDN domains
- Invalid domains return immediate BLOCK response

**AI Refusal Detection:**
- Added `_is_ai_refusal()` function to detect when GPT refuses to analyze images
- Common refusal phrases: "i cannot", "unable to provide", "cannot analyze"
- AI refusals treated as BLOCK (fail-closed security)

**Severity Threshold Adjustment:**
- Changed blocking logic: Only `critical` severity blocks uploads
- Previous: `severity in ['critical', 'high']` → blocked too aggressively
- New: `severity == 'critical'` → only truly explicit content blocked
- `high` and `medium` severities now show WARNING banner instead

**Files Modified:**
- `prompts/services/cloudinary_moderation.py` - AI refusal detection, domain validation
- `prompts/views/api_views.py` - CSRF handling, domain validation
- `prompts/templates/prompts/upload_step1.html` - CSRF token in fetch request
- `prompts/constants.py` - `ALLOWED_CDN_DOMAINS` list

**Agent Validation:**
| Agent | Rating | Key Feedback |
|-------|--------|--------------|
| @backend-architect | 9.0/10 | Security patterns correct, fail-closed appropriate |
| @code-reviewer | 8.5/10 | Clean implementation, proper error handling |
| @security-auditor | 9.0/10 | Domain validation prevents SSRF, fail-closed is correct |
| **Average** | **8.85/10** | ✅ Exceeds 8.0 threshold |

**Documentation Updates:**
- Added B2/OpenAI Vision Moderation section to CLAUDE.md (this session)
- Documented severity levels, API flow, and security features

**Phase L Status:** ~95% complete (moderation system operational)

---

### December 2025 - Session 24 (Dec 25, 2025)

**Phase K Collections: Micro-Spec Approach Adoption**

Session 24 marked a significant pivot in development methodology after multiple failed comprehensive implementations:

**Critical Reset:**
- Hard reset to commit `6d620df` after multiple broken Collections implementations
- Previous attempts with 1000+ line specs resulted in broken code with misleading 9.2/10 agent ratings
- Adopted MICRO-SPEC APPROACH for remaining Collections work

**Micro-Specs Completed:**
- **Micro-Spec #1:** Save button on prompt detail page
  - File: `prompts/templates/prompts/prompt_detail.html` (lines 180-191)
  - Positioned first in action row before Comment button
  - Uses `icon-bookmark` SVG sprite

- **Micro-Spec #2:** Save button on prompt cards
  - File: `prompts/templates/prompts/partials/_prompt_card.html` (lines 220-258)
  - Positioned bottom-right, LEFT of heart button
  - Wrapped save + heart in `card-actions-group` with `margin-left: auto`
  - White icon with `stroke: currentColor; fill: none;` styling

- **Micro-Spec #2.5:** Save button hover effect + Modal CSS
  - File: `static/css/style.css` (lines 700-793)
  - Hover effect: semi-transparent white background
  - Collections modal grid: 4/3/2 columns responsive
  - Collection card thumbnails and styling
  - Create new collection card styling

**Lesson Learned:** Comprehensive specs get ignored by CC; micro-specs with manual verification work better.

**Collections Progress:** ~15% complete

**Commits:**
- `763ffff` feat(collections): Add save-to-collection buttons and modal CSS

**Files Modified:**
- `prompts/templates/prompts/prompt_detail.html` - Save button
- `prompts/templates/prompts/partials/_prompt_card.html` - Save button with positioning
- `static/css/style.css` - Hover effects and modal CSS scaffolding

---

### December 2025 - Session 25 (Dec 26, 2025)

**Phase K Collections Infrastructure Complete**

Session 25 completed the backend infrastructure and modal core for the Collections feature:

**Backend Infrastructure (Micro-Specs #3-5b, #4):**
- Created Collection + CollectionItem models with soft delete support
- Added `deleted_by` ForeignKey and `db_index=True` on `is_deleted`
- Created migration `0039_add_collection_models.py`
- Registered CollectionAdmin with bulk actions (make public/private, soft delete)
- CollectionItemInline for nested editing in admin

**Modal Core (Micro-Specs #6-8):**
- Created `_collection_modal.html` template with all states:
  - Collection grid (4/3/2 column responsive)
  - Loading spinner state
  - Empty state ("You haven't created any collections yet")
  - Error state with alert
  - Create collection sub-panel with form
- Created `collections.js` with modal open/close functionality:
  - Escape key and backdrop click to close
  - Create panel toggle
  - Body scroll lock when modal open
  - Public API: `CollectionsModal.open()`, `.close()`, `.isOpen()`

**Critical Fixes:**
- Moved script tag outside `{% if user.is_authenticated %}` block (was preventing JS load)
- Added 284 lines of modal CSS (modal was completely unstyled, appearing at page bottom)
- Fixed CSS: proper fixed backdrop, centered modal, styled grid/cards

**Collections Progress:** ~40% complete (was 15%)

**Commits:**
- `32ee84b` feat(phase-k): Complete collections modal with models, views, and CSS fix

**Files Created:**
- `prompts/migrations/0039_add_collection_models.py` - Database migration
- `prompts/templates/prompts/partials/_collection_modal.html` - Modal template
- `prompts/views/collection_views.py` - Collection API views (440 lines)
- `static/js/collections.js` - Modal JavaScript (273 lines)

**Files Modified:**
- `prompts/models.py` - Added Collection, CollectionItem models (+103 lines)
- `prompts/admin.py` - Added CollectionAdmin, CollectionItemAdmin (+121 lines)
- `static/css/style.css` - Added 284 lines of modal CSS
- `templates/base.html` - Added modal include + script tag
- `static/icons/sprite.svg` - Added icon-plus

**Next Steps:**
- Wire JavaScript to API endpoints (Micro-Specs #9-12)
- Collections list page and profile tab integration (Micro-Specs #13-15)

---

### December 2025 - Session 26 (Dec 26-27, 2025)

**Phase K Collections: Modal UI & API Integration**

Session 26 implemented the complete collections modal UI with full API integration:

**Modal UI Implementation:**
- Pexels-style collections modal with 4/3/2 column responsive grid
- Dynamic thumbnail grid layouts (1, 2, 3+ images with different arrangements)
- Collection cards with thumbnail previews and item counts
- Create collection sub-panel with back navigation
- Visibility toggle (public/private) with icon indicators
- Form validation with character counter (50 char limit)
- Loading, empty, and error states

**API Integration:**
- Wired collections.js to all API endpoints
- CSRF token handling for POST requests
- Optimistic UI updates with error rollback
- Collection toggle (add/remove) with visual feedback
- Create collection with auto-add current prompt

**CSS Variables System:**
- Added 16 `--collection-*` CSS custom properties
- Modal layout variables (bg, padding, radius, shadow)
- Grid and card variables (gap, radius, thumbnail-height)
- State variables (accent, saved-color, remove-color)
- Form variables (input-border, focus, label-color)

**Critical Fixes:**
- Fixed CSRF 403 errors on API calls
- Fixed empty slug causing IntegrityError
- Fixed modal not closing after collection created
- Fixed thumbnail grid not updating after changes

**Collections Progress:** ~55% complete (was 40%)

**Commits:**
- `237b31a` feat(phase-k): Enhance collections modal UI with Pexels-style design

**Files Modified:**
- `static/js/collections.js` - Full API integration (~760 lines total)
- `static/css/style.css` - CSS variables + modal styling enhancements
- `prompts/templates/prompts/partials/_collection_modal.html` - UI improvements

---

### December 2025 - Session 27 (Dec 27, 2025)

**Phase K Collections: Modal Bug Fixes & Documentation**

Session 27 focused on fixing critical modal bugs and updating project documentation:

**Modal Bug Fixes (Micro-Spec #8.5b):**
- Fixed drag-release close bug (mousedown target tracking)
- Fixed modal closing when drag starts inside and ends on backdrop
- Added restore link to success messages with direct navigation
- Protected alerts section with Django comments to prevent CC relocation

**Documentation Updates:**
- Updated PROJECT_FILE_STRUCTURE.md v2.3 with Phase K additions:
  - Added `collection_views.py` to views package (12 modules)
  - Added `collections.js` to JavaScript architecture (~760 lines)
  - Added `_collection_modal.html` to templates (42 total)
  - Added Collections CSS Variables section (16 variables)
  - Added Collections API Endpoints section (5 endpoints + 4 page views)
  - Updated statistics: JS 3→4, Templates 41→42, Views 11→12

**Agent Validation:**
- @ui-ux-designer: 9.2/10 - Modal interactions improved
- @frontend-developer: 9.5/10 - Clean JavaScript architecture
- @debugger: 8.75/10 - All identified bugs resolved
- **Average: 9.15/10** (exceeds 8+ threshold)

**Collections Progress:** ~60% complete (was 55%)

**Commits:**
- `866c3d4` fix(collections): Micro-Spec #8.5b - Modal UI bug fixes

**Files Modified:**
- `prompts/templates/prompts/partials/_collection_modal.html` - UI fixes
- `static/css/style.css` - Alert positioning, transitions
- `static/js/collections.js` - Drag-release close fix
- `PROJECT_FILE_STRUCTURE.md` - Documentation updates (v2.3)
- `CLAUDE.md` - Session 27 entry

**Next Steps:**
- Collections list page (Micro-Spec #13)
- Profile tab integration (Micro-Spec #15)

---

### December 2025 - Session 28 (Dec 27-28, 2025)

**Phase K Collections: Complete Modal Functionality & Validation System**

Session 28 completed the Collections modal functionality with 11 micro-specs across 13+ commits. This session established key UI patterns that serve as reference implementations for future features.

**Micro-Specs Completed (11 total):**

| Micro-Spec | Description | Key Files |
|------------|-------------|-----------|
| #9.1 | API integration for collections list | `collections.js` |
| #9.2 | Toggle collection (add/remove prompt) | `collections.js`, `collection_views.py` |
| #9.3 | Create collection form submission | `collections.js`, `_collection_modal.html` |
| #9.4 | Real-time name validation with Levenshtein distance | `collections.js` |
| #9.5 | Validation warnings vs errors (confirmable states) | `collections.js`, `style.css` |
| #9.6 | Staggered card animations (50ms delay) | `style.css` |
| #9.7 | Thumbnail grid layouts (0/1/2/3+ items) | `_collection_modal.html`, `style.css` |
| #9.8 | Card structure refinement | `_collection_modal.html` |
| #9.9 | Success state handling (auto-refresh) | `collections.js` |
| #9.10 | Default visibility: Public (was Private) | `_collection_modal.html` |
| #9.11 | Optimistic item count updates | `collections.js` |

**CSS Variables Established (8 new):**
- `--collection-error-color: #dc3545` - Error state red
- `--collection-warning-color: #ffc107` - Warning state amber
- `--collection-warning-bg: #fff3cd` - Warning background
- `--collection-success-color: #28a745` - Success state green
- `--collection-card-animation-duration: 150ms` - Card fade-in duration
- `--collection-card-animation-delay: 50ms` - Staggered delay per card
- `--collection-input-shake-duration: 400ms` - Input shake animation
- `--collection-thumbnail-size: 120px` - Thumbnail container height

**Keyframe Animations (2 new):**
1. `collectionCardFadeIn` - Opacity 0→1, translateY 10px→0 for card entrance
2. `inputShake` - Horizontal shake pattern (0%, -10px, 10px, -10px, 10px, 0%) for validation errors

**JavaScript Architecture (20 functions in CollectionsModal):**

| Category | Functions |
|----------|-----------|
| Modal Control | `open()`, `close()`, `isOpen()` |
| Data Loading | `loadCollections()`, `renderCollections()`, `updateThumbnailGrid()` |
| Card Rendering | `renderCollectionCard()`, `renderCreateCard()` |
| Toggle Actions | `toggleCollection()`, `addToCollection()`, `removeFromCollection()` |
| Create Form | `showCreateForm()`, `hideCreateForm()`, `createCollection()` |
| Validation | `validateCollectionName()`, `checkSimilarNames()`, `levenshteinDistance()` |
| State Management | `updateOptimisticCount()`, `revertOptimisticCount()` |
| Utilities | `showError()`, `init()` |

**UI Patterns Established (Reference Implementation):**

1. **Validation States Pattern:**
   - Error (blocking): Red border, error message, form disabled
   - Warning (confirmable): Amber border, warning message, user can proceed
   - Success: Green border, checkmark icon, auto-clear

2. **Staggered Animation Pattern:**
   - Each card animates with `animation-delay: calc(index * 50ms)`
   - Duration: 150ms ease-out
   - Transform: translateY(10px) → translateY(0)

3. **Thumbnail Grid Pattern:**
   - 0 items: Placeholder icon
   - 1 item: Full-width thumbnail
   - 2 items: 50/50 horizontal split
   - 3+ items: Left column (60%), right column stacked (40%)

4. **Optimistic UI Pattern:**
   - Update count immediately on click
   - Revert on API failure
   - Visual feedback (count flashes)

**Accessibility Improvements:**
- ARIA live regions for validation messages
- Focus management on modal open/close
- Keyboard navigation (Escape to close)
- Button reset styles for icon-only buttons
- Dynamic `aria-expanded` on visibility toggle

**Agent Validation:**
- @frontend-developer: 9.5/10 - Clean JavaScript architecture
- @ui-ux-designer: 9.0/10 - Consistent interaction patterns
- **Average: 9.25/10** (exceeds 8+ threshold)

**Collections Progress:** ~75% complete (was 60%)

**Commits (13+):**
- Multiple micro-spec commits throughout session
- Final: `abcaf25` feat(phase-k): Default to public visibility
- Final: `c48d98d` perf(phase-k): Add optimistic item count updates

**Files Modified:**
- `static/js/collections.js` - Complete modal JavaScript (~950 lines)
- `static/css/style.css` - CSS variables + animations (~100 lines added)
- `prompts/templates/prompts/partials/_collection_modal.html` - Full UI structure
- `prompts/views/collection_views.py` - API endpoints refinements
- `prompts/urls.py` - URL patterns

**Future Enhancements (Phase K.2+):**
- Profanity filter integration for collection names
- "Your Likes" virtual collection
- "Your Downloads" virtual collection with download tracking
- Premium limits enforcement (10 collections free, unlimited paid)
- Collection sharing and collaboration

---

### January 2026 - Session 34-35 (Dec 31, 2025 - Jan 1, 2026)

**Phase L: L8-DIRECT - Direct Browser-to-B2 Uploads**

Session 34-35 implemented direct browser-to-B2 uploads via presigned URLs, eliminating the Heroku middleman and achieving 70-80% faster upload times.

**Problem Solved:**
- Previous architecture: Browser → Heroku (5-7s) → B2 (15-18s) = ~23s total
- New architecture: Browser → B2 (presigned URL, 5-8s) → Heroku callback = ~5-8s total
- **Improvement:** 70-80% faster uploads

**Files Created:**
- `prompts/services/b2_presign_service.py` (~120 lines)
  - `generate_presigned_upload_url()` - Creates time-limited presigned URLs
  - `get_bucket_cors_rules()` - Returns CORS configuration for B2
  - Handles authorization header generation with SHA-256 signing
- `prompts/tests/test_b2_presign.py` (22 tests)
  - Presigned URL generation tests
  - API endpoint integration tests
  - Session state management tests
  - Error handling tests

**Files Modified:**
- `prompts/views/api_views.py` - Added `b2_presign_upload`, `b2_upload_complete` views
- `prompts/urls.py` - Added `/api/upload/b2/presign/` and `/api/upload/b2/complete/` routes
- `prompts/templates/prompts/upload_step1.html` - Direct B2 upload JavaScript with XHR

**API Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload/b2/presign/` | GET | Generate presigned URL for direct upload |
| `/api/upload/b2/complete/` | POST | Notify server of completed upload |

**Technical Implementation:**
1. **Presigned URL Flow:**
   - Client requests presigned URL with content type/length
   - Server generates time-limited URL (1 hour expiry)
   - Client uploads directly to B2 using XHR PUT
   - Client notifies server via complete endpoint

2. **Session State Management:**
   - `b2_pending_upload` session key stores upload metadata
   - Contains: `file_key`, `filename`, `content_type`, `uploaded_at`
   - Used by complete endpoint to finalize upload

3. **Deferred Variant Generation:**
   - Thumbnail generated immediately (quick mode)
   - Medium, large, WebP variants generated on Step 2 page load
   - Improves perceived upload speed

**Agent Validation:**
| Agent | Rating | Key Feedback |
|-------|--------|--------------|
| @backend-architect | 9.0/10 | Clean separation of concerns, proper session handling |
| @security-auditor | 9.0/10 | Presigned URLs properly scoped, CORS correctly configured |
| @code-reviewer | 9.0/10 | Well-structured code, comprehensive test coverage |
| **Average** | **9.0/10** | Exceeds 8+ threshold |

**Development Learnings:**
1. **Spec-First Approach Critical:** L8-INSTANT failed because spec was incomplete
2. **Session State > Database:** For temporary upload state, session storage is simpler
3. **Event-Driven JS:** CustomEvent for cross-component communication works well
4. **Presigned URLs:** B2's presigned URL format requires specific authorization headers

**Phase L Progress:** ~91% → ~95% (L8-DIRECT complete, later revised to ~75% in Session 36 due to NSFW gate fix needed)

---

### December 2025 - Session 29 (Dec 28-29, 2025)

**Phase K Collections: Profile Tab Page Implementation + Polish**

Session 29 implemented the Collections Profile Tab Page (Micro-Spec #11) and polished it with 8 additional micro-specs (#11.1-11.8).

**Micro-Spec #11 Completed:**
- Created `collections_profile.html` template (812 lines)
- Added `user_collections` view with sorting options (recent/most/fewest items)
- New route: `/users/<username>/collections/`
- Collections tab link added to user profile navigation
- Profile stats integration (prompts, likes, views, ranks)
- Pagination support (12 collections per page)

**Micro-Specs #11.1-11.8 Completed (Profile Tab Polish):**
- **#11.1:** Investigation report documenting 7 issues in collections_profile.html
- **#11.2:** Added "Member since" date and social icons to profile header
- **#11.3:** Fixed Create button styling to use `btn-outline-standard` class
- **#11.4:** Improved empty state messaging for users with no collections
- **#11.5:** Backend pagination with Django's Paginator (12 per page)
- **#11.6:** Load More JavaScript using fetch API with DOMParser
- **#11.7:** Grid layout CSS fix with `minmax(0, 1fr)` for proper card sizing
- **#11.8:** Moved inline `.collection-grid` styles to style.css, Load More button styling

**Key Features:**
- Responsive grid layout matching gallery page design
- Sorting dropdown: Recent / Most items / Fewest items
- Empty state handling for users with no collections
- Visibility icons (public/private) on collection cards
- Thumbnail preview grids (0/1/2/3+ items layouts)
- Follow button integration
- Cloudinary avatar rendering fixed
- Load More pagination with fetch-based AJAX
- `collection:created` event for dynamic card insertion

**Database Fixes:**
- Fixed Collection ID 1 empty slug issue
- Generated slug: `test-1-o9bZI` using `slugify()` + `secrets.token_urlsafe()`

**Files Created:**
- `prompts/templates/prompts/collections_profile.html`
- `docs/reports/MICRO_SPEC_11_1_INVESTIGATION_REPORT.md`

**Files Modified:**
- `prompts/views/collection_views.py` (+174 lines, pagination logic)
- `prompts/views/__init__.py` (added user_collections export)
- `prompts/urls.py` (added user_collections route)
- `prompts/templates/prompts/user_profile.html` (Collections tab link)
- `static/js/collections.js` (`createOnly` mode, `collection:created` event)
- `static/css/style.css` (`.collection-grid` consolidated from inline)

**Technical Implementation:**
- View uses LeaderboardService for rank calculations
- Profile stats cached for 5 minutes
- Thumbnails attached via CollectionItem query with select_related
- CSS grid with `minmax(0, 1fr)` prevents card overflow
- `collection:created` custom event enables real-time card insertion

**Collections Progress:** ~85% complete (was ~75%)

**Commits:**
- `8ea3ceb` feat(phase-k): Add Collections profile tab page (Micro-Spec #11)
- `6bde11e` fix(phase-k): Profile tab header + empty state improvements
- `07f35da` feat(phase-k): Load More pagination with fetch API
- `602205d` style(phase-k): Micro-Spec #11.8 + UI improvements to collections page

**Next Steps:**
- Individual collection detail page
- Edit collection functionality
- Delete collection functionality (soft delete)

---

### December 2025 - Session 22-23 (Dec 24-25, 2025)

**Security Remediation + Generator Pages Fix + SVG Icons Phase 3 + Phase K Icons**

Session 22-23 completed critical security fixes, resolved a major bug affecting all generator pages, expanded the SVG icon system, and added Phase K collection icons:

**OWASP Security Remediation (Critical)**
- Removed `|safe` filter from `prompt.content` to prevent stored XSS
- Added `@login_required` to `prompt_like` view for auth enforcement
- Added `@require_POST` to `prompt_like` view for method restriction
- Fixed template debug mode: `'debug': True` → `DEBUG` variable
- Removed 9 debug print statements from `bulk_reorder_prompts`
- Replaced exception exposure with generic error + logging
- Agent validation: @security-auditor 9.2/10, @django-pro 9.0/10

**Generator Pages Fix (Critical Bug)**
- Fixed all 16 generators showing 0 prompts
- Root cause: `choice_value` in constants used URL slugs ('dalle3') but database stores display names ('DALL-E 3')
- Updated all `choice_value` entries to match database values
- Verified: Midjourney page now shows 55 prompts (was 0)
- Fixed generator link case sensitivity with `|lower` filter on template URL

**SVG Icon System Expansion (Phase 3)**
- Added 3 new icons to sprite.svg: `icon-user`, `icon-user-pen`, `icon-mail`
- Updated profile dropdown in `base.html` to use SVG icons
- Updated test assertion: `fa-trash` → `icon-trash`

**Phase K Icons Added (11 new icons for Collections)**
- `icon-bookmark` - Save button (outline)
- `icon-bookmark-filled` - Saved state (pink fill)
- `icon-circle-check` - Already in collection
- `icon-circle-minus` - Remove from collection
- `icon-eye` - Public collection
- `icon-eye-off` - Private collection
- `icon-x` - Soft close button
- `icon-arrow-left` - Back navigation
- `icon-arrow-right` - Forward navigation
- `icon-download` - Download button
- `icon-share` - Share/copy link

**Button Styling Consistency**
- Added `action-icon-btn` class to affiliate, copy, and login-to-copy buttons
- Wrapped button text in `<span>` for CSS margin styling
- Updated `.generator-cta-btn` sizing to match `action-icon-btn`
- Linked generator name on prompt detail page to generator page

**CSS Fixes**
- Profile tab hover text stays white on dark background
- Updated `a:hover` to use `text-primary` color and underline

**Tests:** 234/234 passing
**Total Icons:** 30 (19 previous + 11 Phase K)

**Files Modified:**
- `prompts/views/prompt_views.py` - Security decorators, removed debug prints
- `prompts/templates/prompts/prompt_detail.html` - Removed |safe filter
- `prompts/constants.py` - Fixed generator choice_value entries
- `static/icons/sprite.svg` - Added 3 Phase 3 icons + 11 Phase K icons
- `templates/base.html` - SVG icons in profile dropdown
- `static/css/style.css` - CSS fixes

---

### December 2025 - Session 22 (Dec 23, 2025)

**Bug Fix: Solid Heart Icon Display**

Session 22 fixed a critical visual bug and updated documentation:

**TASK 1 (BLOCKER): Solid Heart Fix**
- Fixed `icon-heart-filled` displaying as blank white space instead of pink
- Root cause: Base `.icon` class has `fill: none` which overrode `fill="currentColor"` on symbol
- Solution: Added `fill="#ff3a78"` directly on the `<path>` element (highest specificity)
- File: `static/icons/sprite.svg` (lines 87-91)

**TASK 2: PROJECT_FILE_STRUCTURE.md Updates**
- Updated file counts: CSS 4→6, JS 1→3
- Added `static/icons/` directory documentation
- Added SVG Icon System section with all 16 icons
- Updated CSS Architecture section with icons.css and prompt-detail.css
- Updated JavaScript Architecture section with like-button.js and prompt-detail.js

**TASK 3: CLAUDE.md Updates**
- Added Session 21 documentation (previously missing)
- Added Session 22 documentation
- Updated Phase J status markers

**Files Modified:**
- `static/icons/sprite.svg` - Fixed heart-filled icon fill color
- `PROJECT_FILE_STRUCTURE.md` - Documentation updates
- `CLAUDE.md` - Session documentation

---

### December 2025 - Session 21 (Dec 23, 2025)

**Phase J.3: Video Hover Autoplay & Like Button Redesign**

Session 21 expanded the SVG icon system and implemented video thumbnail hover autoplay:

**Video Thumbnail Hover Autoplay**
- Added hover-to-play functionality for "More From Author" video thumbnails
- Videos autoplay on mouseenter, pause on mouseleave
- Thumbnail hides during video playback, reappears on pause
- Removed dark overlay on video thumbnail hover for cleaner UX

**Phase 2 Icons Added (11 new icons)**
- `icon-comment` - Comment indicator
- `icon-heart` - Heart outline (unliked state)
- `icon-heart-filled` - Solid pink heart (liked state)
- `icon-flag` - Report prompt
- `icon-edit` - Edit prompt
- `icon-trash` - Delete prompt
- `icon-external-link` - External links
- `icon-calendar` - Date indicators
- `icon-copy` - Copy to clipboard
- `icon-login` - Sign in/out
- `icon-bell` - Notifications

**Detail Page Like Button Redesign**
- Two-icon toggle pattern: heart-outline (unliked) → heart-filled (liked)
- CSS classes control visibility: `.heart-outline` / `.heart-filled`
- `.liked` state toggles which icon displays
- Optimistic UI: instant toggle before AJAX completes

**Commits:**
- `eeaa402` feat(icons): Expand SVG sprite system with Phase 2 icons and like button fixes
- `4efb3a0` fix(phase-j3): Remove dark overlay on video thumbnail hover
- `3055457` feat(phase-j3): Add video thumbnail hover autoplay for More From Author

**Files Modified:**
- `static/icons/sprite.svg` - Added 11 Phase 2 icons
- `static/css/components/icons.css` - Like button toggle CSS
- `static/js/prompt-detail.js` - Video hover autoplay + like button JS
- `prompts/templates/prompts/prompt_detail.html` - Two-icon like button structure
- Multiple template files - SVG icon replacements

**Known Issue (Fixed in Session 22):**
- Solid heart icon displayed blank due to CSS specificity conflict

---

### December 2025 - Session 20 (Dec 23, 2025)

**Phase J.2 Complete: SVG Icon System & Unified Button Styling**

Session 20 implemented core infrastructure improvements for icons and button consistency:

**Phase J.2: SVG Icon System**
- Created `static/icons/sprite.svg` with 5 Lucide icons (image, video, search, trophy, lightbulb)
- Created `static/css/components/icons.css` with icon utility classes
- Replaced Font Awesome icons in Explore dropdown with SVG sprites
- Fixed SVG `<use>` shadow DOM issue: `stroke: var(--gray-700)` instead of `currentColor`
- Updated `static/js/navbar.js` for dynamic icon switching

**Unified Button Styling System**
- Standardized action icons across prompt detail and cards
- Copy button cleanup and login button styling improvements
- Model type indicators for all media types

**Technical Details:**
- SVG icons use Lucide Icons (MIT License)
- Direct CSS variable assignment bypasses `<use>` shadow DOM color inheritance issues
- Icon sizes: `.icon-xs` (12px), `.icon-sm` (22px), `.icon-md/.icon-lg` (24px)

**Bug Fixes:**
- Fixed dropdown icons not displaying (stroke property for SVG vs color for FA)
- Updated `.pexels-dropdown` min-width from 240px to 200px

**Agent Validation:**
- @frontend-developer: 9.0/10 → SVG CSS fix matches proven search dropdown pattern

**Files Created:**
- `static/icons/sprite.svg` - SVG sprite definitions
- `static/css/components/icons.css` - Icon utility classes

**Files Modified:**
- `templates/base.html` - SVG icon implementation in dropdowns
- `static/css/navbar.css` - Dropdown icon styling (stroke fix, min-width)
- `static/js/navbar.js` - Icon switching logic

---

### December 2025 - Session 19 (Dec 19-20, 2025)

**Phase J.1 Complete: Prompt Detail Page Redesign**

Session 19 completed Phase J.1 with 22 commits across 9 iterative rounds:

**Phase 0.5: Code Quality Improvements**
- Avatar signal refactoring (pre_save/post_save pattern with AvatarChangeLog)
- simple_timesince template filter refactor (C901 complexity fix)
- CSS variable additions (--color-liked: #e0245e)

**Phase J.1: Complete UI Overhaul**
- Hero video styling matched to hero-image (rounded corners, shadows)
- Author section restructure (views row, follow button, actions)
- Comments section mobile relocation using CSS flexbox ordering
- Layout and spacing improvements with CSS variable standardization
- Removed unused --light-blue CSS variable

**Key Technical Implementations:**
- CSS flexbox `order` property for mobile column reordering
- WCAG 1.3.2 compliant visual ordering (comments order: 2, right rail order: 3)
- CSS variable fallbacks: `var(--spacing-md, 1rem)`
- Page-specific CSS in `static/css/pages/prompt-detail.css` (1,063 lines)

**Agent Validation:**
- @ui-ux-designer: 7.5/10 → Recommended swapping comment/right rail order
- @frontend-developer: 9.0/10 → Clean CSS architecture, proper variable usage
- **Average: 8.7/10** (Production ready)

**Commits:** 7da0651 through e68bb91 (22 commits)

**Files Modified:**
- `static/css/pages/prompt-detail.css` - Page-specific styles
- `prompts/templates/prompts/prompt_detail.html` - Template restructure
- `prompts/signals.py` - Avatar signal handlers
- `prompts/models.py` - AvatarChangeLog model
- `prompts/templatetags/prompt_tags.py` - simple_timesince refactor
- `static/css/style.css` - Global CSS variables

---

### December 2025 - Session 17 (Dec 17, 2025)

**Generator Pages Overhaul & CI Pipeline Fixes**

Session 17 completed two major commits:

**Commit 1: Generator Pages Overhaul** (5857542)
- Fixed case sensitivity bug in AI generator URL routing (`Midjourney` vs `midjourney`)
- Unified CSS architecture: `.content-filter-bar` now shared between generator pages and user profiles
- Removed 7 deprecated CSS classes: `.generator-filter-bar`, `.generator-tabs`, `.gen-dropdown`, `.generator-filter-tabs`, `.generator-tab-link`, `.generator-sort-dropdown`, `.generator-sort-btn`
- Added 5 new AI generators: Grok, WAN 2.1, WAN 2.2, Nano Banana, Nano Banana Pro
- Updated `prompts/constants.py` with new generator metadata
- Updated `ai_generator_category.html` template to use unified filter bar

**Commit 2: CI Pipeline Fixes** (current session)
- Security: Upgraded django-allauth 65.9.0 → 65.13.0 (CVE-2025-65430, CVE-2025-65431)
- Fixed 4 failing tests that checked for old HTML structure:
  - `test_filter_bar_exists` in test_generator_page.py
  - `test_filter_form_renders` in test_user_profile_header.py
  - `test_filter_form_preserves_selection` in test_user_profile_header.py
  - `test_media_filter_form_has_responsive_structure` in test_user_profile_header.py
- Test assertions updated: `generator-tabs` → `filter-tabs`, old dropdown selectors → new Pexels-style dropdown selectors
- All 59 tests passing

**Files Modified:**
- `requirements.txt` - django-allauth version bump
- `prompts/tests/test_generator_page.py` - Updated test assertions
- `prompts/tests/test_user_profile_header.py` - Updated 3 test methods
- `prompts/constants.py` - 5 new AI generators
- `prompts/templates/prompts/ai_generator_category.html` - Unified filter bar
- `static/css/style.css` - Removed deprecated generator-specific CSS

**CSS Architecture Change:**
Before: Separate `.generator-filter-bar` and `.content-filter-bar` (duplication)
After: Single `.content-filter-bar` shared across all pages (DRY principle)

**New AI Generators Added:**
| Generator | Type | Category |
|-----------|------|----------|
| Grok | Image | xAI |
| WAN 2.1 | Video | Alibaba |
| WAN 2.2 | Video | Alibaba |
| Nano Banana | Image | Community |
| Nano Banana Pro | Image | Community |

### January 2025 - Initial CLAUDE.md Creation
- Documented entire project scope
- Defined all 4 development phases
- Established decisions and priorities
- Created comprehensive feature specifications
- Outlined monetization strategy
- Detailed SEO and moderation approaches

### Future Updates
*This section will track major changes to project direction, tech stack, or strategy*

---

## ✅ Next Steps

### Immediate Actions (This Week)
1. [ ] Review and approve this CLAUDE.md document
2. [ ] Answer unanswered questions in dedicated session
3. [ ] Create GitHub repository (if not exists)
4. [ ] Set up project management (Trello/Notion/GitHub Projects)
5. [ ] Start Phase 1: PostgreSQL migration

### This Month (Phase 1 Completion)
1. [ ] Complete all Phase 1 infrastructure tasks
2. [ ] Implement full content moderation system
3. [ ] Deploy complete SEO strategy
4. [ ] Launch soft beta with invite codes
5. [ ] Gather initial user feedback

### Next 3 Months (Phases 2-3)
1. [ ] Complete monetization implementation
2. [ ] Launch publicly
3. [ ] Reach 1,000 users
4. [ ] Achieve first $1,000 MRR
5. [ ] Build gamification and social features

---

**END OF CLAUDE.md**

*This document is a living reference. Update it as the project evolves, decisions change, or new insights emerge. Share it with every new Claude conversation for instant context.*

**Version:** 2.19
**Last Updated:** January 10, 2026
**Document Owner:** Mateo Johnson
**Project Status:** Pre-Launch (Phase L: Media Infrastructure ~98%, Phase K ON HOLD at 95%)