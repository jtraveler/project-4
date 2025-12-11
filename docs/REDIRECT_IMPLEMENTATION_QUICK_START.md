# 301 Redirect Implementation - Quick Start Guide

**Duration:** 30 minutes to implementation
**Complexity:** LOW
**Risk Level:** MINIMAL (with proper testing)

---

## TL;DR - Fastest Implementation Path

### 1. Update URL Configuration (5 minutes)

**File:** `prompts/urls.py`

Replace this line:
```python
path('ai/<slug:generator_slug>/', views.ai_generator_category, name='ai_generator_category'),
```

With these lines:
```python
from django.views.generic.base import RedirectView

# NEW primary URL
path('inspiration/ai/<slug:generator_slug>/',
     views.ai_generator_category,
     name='ai_generator_category_new'),

# OLD URL with 301 redirect
path('ai/<slug:generator_slug>/',
     RedirectView.as_view(
         pattern_name='prompts:ai_generator_category_new',
         permanent=True,
         query_string=True,
     ),
     name='ai_generator_category_old'),
```

### 2. Test Locally (5 minutes)

```bash
python manage.py runserver
```

In another terminal:

```bash
curl -I http://localhost:8000/ai/midjourney/
# Should show: HTTP/1.1 301 Moved Permanently
# And:         Location: /inspiration/ai/midjourney/
```

### 3. Run Unit Tests (5 minutes)

Copy the test file from Appendix A into `prompts/tests/test_seo_redirects.py`, then:

```bash
python manage.py test prompts.tests.test_seo_redirects -v 2
# All 6 tests should pass
```

### 4. Deploy to Production (15 minutes)

```bash
git add prompts/urls.py
git commit -m "refactor(seo): Add 301 redirects from /ai/* to /inspiration/ai/*"
git push heroku main
```

Then verify:

```bash
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
# Should show HTTP 301
```

**Done!** Your 301 redirects are now live. See the full protocol document for monitoring instructions.

---

## Step-by-Step Implementation Guide

### Prerequisites Checklist

- [ ] You have access to the Django project
- [ ] You have git and heroku CLI installed
- [ ] You have a Heroku account with deployment access
- [ ] You have curl installed (for testing)

### Step 1: Backup Current Configuration

```bash
# Create backup of current URL configuration
cp prompts/urls.py prompts/urls.py.backup

# Verify backup
cat prompts/urls.py.backup | grep ai_generator
```

### Step 2: Create Necessary Imports

**File:** `prompts/urls.py` (at the top)

Ensure you have:

```python
from django.urls import path, re_path
from django.views.generic.base import RedirectView  # ← ADD THIS LINE
from . import views
from . import views_admin
```

### Step 3: Implement the Redirect

Find the current line:

```python
# Before (current code around line 44)
path('ai/<slug:generator_slug>/', views.ai_generator_category, name='ai_generator_category'),
```

Replace it with:

```python
# After (new code)
# New primary URL structure (all new links use this)
path('inspiration/ai/<slug:generator_slug>/',
     views.ai_generator_category,
     name='ai_generator_category_new'),

# Legacy URL with 301 redirect (old links automatically redirect)
path('ai/<slug:generator_slug>/',
     RedirectView.as_view(
         pattern_name='prompts:ai_generator_category_new',
         permanent=True,
         query_string=True,
     ),
     name='ai_generator_category_old'),
```

### Step 4: Verify Syntax

```bash
# Check for Python syntax errors
python manage.py check

# Expected output:
# System check identified no issues (0 silenced).
```

### Step 5: Test Locally

```bash
# Start development server
python manage.py runserver

# In another terminal, run these tests:

# Test 1: Check 301 status
echo "=== Test 1: 301 Status Code ==="
curl -I http://localhost:8000/ai/midjourney/

# Test 2: Check all 11 generators
echo "=== Test 2: All 11 Generators ==="
for gen in midjourney dalle3 dalle2 stable-diffusion leonardo-ai flux sora sora2 veo-3 adobe-firefly bing-image-creator; do
    STATUS=$(curl -s -I "http://localhost:8000/ai/$gen/" | head -1)
    echo "$gen: $STATUS"
done

# Test 3: Check new URLs work
echo "=== Test 3: New URLs Return 200 ==="
curl -I http://localhost:8000/inspiration/ai/midjourney/

# Test 4: Check query string preservation
echo "=== Test 4: Query String Preservation ==="
curl -I "http://localhost:8000/ai/midjourney/?page=2&sort=trending"
```

**All should pass before moving forward.**

### Step 6: Create Unit Tests

**File:** `prompts/tests/test_seo_redirects.py`

```python
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

class AIGeneratorRedirectTests(TestCase):
    """Test 301 redirects for AI generator pages."""

    def setUp(self):
        self.client = Client()
        self.generators = [
            'midjourney',
            'dalle3',
            'dalle2',
            'stable-diffusion',
            'leonardo-ai',
            'flux',
            'sora',
            'sora2',
            'veo-3',
            'adobe-firefly',
            'bing-image-creator',
        ]

    def test_old_url_returns_301(self):
        """Test that old /ai/{generator}/ returns HTTP 301."""
        for generator in self.generators:
            response = self.client.get(f'/ai/{generator}/', follow=False)
            self.assertEqual(
                response.status_code,
                HTTPStatus.MOVED_PERMANENTLY,
                f"Generator {generator} did not return 301 status"
            )

    def test_redirect_destination_correct(self):
        """Test that redirects point to correct new URL."""
        for generator in self.generators:
            response = self.client.get(f'/ai/{generator}/', follow=False)
            expected_location = f'/inspiration/ai/{generator}/'
            self.assertEqual(
                response.url,
                expected_location,
                f"Generator {generator} redirects to wrong URL"
            )

    def test_redirect_preserves_query_string(self):
        """Test that query parameters are preserved."""
        response = self.client.get(
            '/ai/midjourney/?page=2&sort=trending',
            follow=False
        )
        self.assertEqual(
            response.url,
            '/inspiration/ai/midjourney/?page=2&sort=trending',
            "Query string not preserved in redirect"
        )

    def test_new_url_returns_200(self):
        """Test that new URLs return 200 OK."""
        for generator in self.generators:
            response = self.client.get(f'/inspiration/ai/{generator}/')
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f"New URL for {generator} does not return 200"
            )
```

**Run tests:**

```bash
python manage.py test prompts.tests.test_seo_redirects -v 2
```

### Step 7: Commit to Git

```bash
# Stage changes
git add prompts/urls.py

# Commit with descriptive message
git commit -m "refactor(seo): Add 301 redirects from /ai/* to /inspiration/ai/*

- Migrate AI generator pages to new /inspiration/ai/ URL structure
- Implement 301 permanent redirects for SEO ranking transfer
- Preserve query parameters (pagination, sorting, filters)
- Add unit tests for all 11 generators
- Closes Phase G SEO improvement task"

# Verify commit
git log --oneline -1
```

### Step 8: Deploy to Heroku

```bash
# Push to production
git push heroku main

# Monitor deployment
heroku logs --app mj-project-4 --tail

# Wait for completion message:
# "remote: https://mj-project-4-68750ca94690.herokuapp.com deployed to Heroku"
```

### Step 9: Production Verification

```bash
# Test production redirects
echo "=== Production Verification ==="

# Test 1: Check 301 status
echo "Test 1: 301 Status Code"
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ | head -1

# Test 2: Check location header
echo "Test 2: Location Header"
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ | grep Location

# Test 3: Follow redirect
echo "Test 3: Follow Redirect"
curl -L https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ -D /tmp/headers.txt
cat /tmp/headers.txt | grep HTTP

# Test 4: Check all 11 generators
echo "Test 4: All 11 Generators"
for gen in midjourney dalle3 dalle2 stable-diffusion leonardo-ai flux sora sora2 veo-3 adobe-firefly bing-image-creator; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://mj-project-4-68750ca94690.herokuapp.com/ai/$gen/")
    echo "$gen: $STATUS"
done

# Expected: All should show 301
```

### Step 10: Post-Deployment Steps

1. **Update Google Search Console**
   - Go to https://search.google.com/search-console
   - For each old URL, click "Request Indexing"
   - This tells Google to re-crawl and see the 301 redirect

2. **Monitor Heroku Logs**
   ```bash
   heroku logs --app mj-project-4 | grep error
   # Should show no errors
   ```

3. **Create Google Analytics Segments**
   - Old traffic: Page path contains `/ai/`
   - New traffic: Page path contains `/inspiration/ai/`
   - Compare metrics before/after

4. **Set Calendar Reminders**
   - Day 1: Verify production redirects
   - Day 3: Check traffic stability
   - Week 1: Monitor GSC for errors
   - Week 2: Assess ranking changes
   - Week 4: Final verification

---

## Troubleshooting

### Issue: Redirect returns 302 instead of 301

**Fix:**
```python
# Check permanent=True is set
RedirectView.as_view(
    pattern_name='prompts:ai_generator_category_new',
    permanent=True,  # ← MUST be True
    query_string=True,
)
```

If already set correctly:
```bash
# Restart Heroku and clear caches
heroku restart --app mj-project-4
git push heroku main  # Re-deploy
```

### Issue: Query parameters not preserved

**Fix:**
```python
# Check query_string=True is set
RedirectView.as_view(
    pattern_name='prompts:ai_generator_category_new',
    permanent=True,
    query_string=True,  # ← MUST be True
)
```

### Issue: Import error "RedirectView not found"

**Fix:**
```python
# Add at top of prompts/urls.py
from django.views.generic.base import RedirectView
```

### Issue: Test failures

```bash
# Re-run tests with verbose output
python manage.py test prompts.tests.test_seo_redirects -v 2

# Check for specific failures and fix issues
```

---

## Verification Checklist

Complete this before considering implementation done:

- [ ] Django check passes: `python manage.py check`
- [ ] Unit tests pass: `python manage.py test prompts.tests.test_seo_redirects`
- [ ] Local curl tests pass: `curl -I http://localhost:8000/ai/midjourney/`
- [ ] All 11 generators return 301 locally
- [ ] New URLs return 200 locally
- [ ] Query string preserved locally
- [ ] Code committed to git
- [ ] Deployed to Heroku successfully
- [ ] Production curl tests pass
- [ ] All 11 generators return 301 in production
- [ ] New URLs return 200 in production
- [ ] No errors in Heroku logs
- [ ] GSC updated (manual request indexing)
- [ ] Analytics segments created

---

## Code Examples by Framework

### If Using Django's URL Include (optional)

If you prefer to organize URLs in a separate file:

**File:** `prompts/urls_redirects.py`

```python
from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = 'prompts_redirects'

urlpatterns = [
    # New URLs
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # Redirects
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(
             pattern_name='prompts:ai_generator_category_new',
             permanent=True,
             query_string=True,
         ),
         name='ai_generator_category_old'),
]
```

Then include in main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('', include('prompts.urls_redirects')),
    # ... other patterns ...
]
```

---

## Advanced: Redirect with Validation

If you want to validate the generator exists before redirecting:

**File:** `prompts/views.py`

```python
from django.views.generic.base import RedirectView
from django.urls import reverse
from prompts.constants import AI_GENERATORS

class AIGeneratorLegacyRedirect(RedirectView):
    permanent = True
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        generator_slug = kwargs.get('generator_slug')

        # Validate generator exists
        if generator_slug not in AI_GENERATORS:
            return reverse('prompts:home')  # Redirect invalid to home

        # Return proper new URL
        return reverse('prompts:ai_generator_category_new',
                      kwargs={'generator_slug': generator_slug})
```

**File:** `prompts/urls.py`

```python
from . import views

path('ai/<slug:generator_slug>/',
     views.AIGeneratorLegacyRedirect.as_view(),
     name='ai_generator_category_old'),
```

---

## Monitoring After Deployment

### Hour 1 After Deployment

```bash
# Every 15 minutes
./scripts/verify_production_redirects.sh
```

### Day 1 After Deployment

```bash
# Morning
heroku logs --app mj-project-4 | grep -i error | head -10

# Afternoon
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/

# Evening
# Check Google Search Console (manual)
```

### Week 1-4 After Deployment

```bash
# Daily check
./scripts/verify_production_redirects.sh

# Weekly check
# Review Google Search Console
# Review Google Analytics
# Check for ranking changes
```

---

## Key Points to Remember

✅ **DO:**
- Use `permanent=True` for HTTP 301
- Use `query_string=True` to preserve parameters
- Test locally before deploying
- Run unit tests
- Monitor for 48 hours after deployment
- Request re-indexing in Google Search Console

❌ **DON'T:**
- Use 302 (temporary) redirects - loses SEO value
- Forget `query_string=True` - breaks pagination
- Deploy without testing - catches 90% of issues
- Skip monitoring - catch problems early
- Hardcode URLs - use `url` template tag or `reverse()`

---

## Questions?

Refer to the full protocol document: `docs/301_REDIRECT_MIGRATION_PROTOCOL.md`

Key sections:
- Troubleshooting Guide (for specific issues)
- Testing Protocol (for comprehensive testing)
- Post-Migration Monitoring (for long-term tracking)
- Appendix (for complete code examples)

---

## Estimated Timeline

| Step | Duration |
|------|----------|
| Update URLs | 5 min |
| Test locally | 5 min |
| Run unit tests | 5 min |
| Deploy to Heroku | 5 min |
| Verify production | 5 min |
| Post-deployment setup | 5 min |
| **Total** | **30 minutes** |

**Monitoring** (not included in above):
- Week 1: Daily checks (5 min each)
- Week 2-4: Every 3 days (5 min each)
- Weeks 5-8: Weekly (5 min each)

---

**Quick Start prepared for PromptFinder development team**
**Date:** December 2024
**Ready to deploy immediately upon review**

