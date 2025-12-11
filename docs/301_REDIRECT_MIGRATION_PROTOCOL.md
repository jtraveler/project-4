# 301 Redirect Migration Protocol
## URL Migration: `/ai/{generator}/` → `/inspiration/ai/{generator}/`

**Document Version:** 1.0
**Created:** December 2024
**Project:** PromptFinder
**Scope:** 11 AI Generator Pages Migration
**Status:** Pre-Migration

---

## Executive Summary

This protocol establishes the complete process for migrating 11 AI generator category pages from `/ai/{generator}/` to `/inspiration/ai/{generator}/` while preserving search engine rankings and user access through proper 301 (permanent) redirects.

**Timeline:** 3-week migration with 8-week monitoring
**Risk Level:** LOW (with proper implementation)
**Rollback Window:** 30 days

---

## Table of Contents

1. [Pre-Migration Checklist](#pre-migration-checklist)
2. [Implementation Guide](#implementation-guide)
3. [Testing Protocol](#testing-protocol)
4. [Verification Checklist](#verification-checklist)
5. [Post-Migration Monitoring](#post-migration-monitoring)
6. [Troubleshooting Guide](#troubleshooting-guide)

---

## Pre-Migration Checklist

### Week 1: Documentation & Analysis

#### Current State Capture

Before making ANY changes, document the baseline:

**Spreadsheet to Create:** `ai_generator_migration_baseline.xlsx`

| Generator | Current URL | New URL | Current Ranking | Current Traffic | Indexed | Backlinks |
|-----------|-----------|---------|-----------------|-----------------|---------|-----------|
| Midjourney | `/ai/midjourney/` | `/inspiration/ai/midjourney/` | - | - | - | - |
| DALL-E 3 | `/ai/dalle3/` | `/inspiration/ai/dalle3/` | - | - | - | - |
| DALL-E 2 | `/ai/dalle2/` | `/inspiration/ai/dalle2/` | - | - | - | - |
| Stable Diffusion | `/ai/stable-diffusion/` | `/inspiration/ai/stable-diffusion/` | - | - | - | - |
| Leonardo AI | `/ai/leonardo-ai/` | `/inspiration/ai/leonardo-ai/` | - | - | - | - |
| Flux | `/ai/flux/` | `/inspiration/ai/flux/` | - | - | - | - |
| Sora | `/ai/sora/` | `/inspiration/ai/sora/` | - | - | - | - |
| Sora 2 | `/ai/sora2/` | `/inspiration/ai/sora2/` | - | - | - | - |
| Veo 3 | `/ai/veo-3/` | `/inspiration/ai/veo-3/` | - | - | - | - |
| Adobe Firefly | `/ai/adobe-firefly/` | `/inspiration/ai/adobe-firefly/` | - | - | - | - |
| Bing Image Creator | `/ai/bing-image-creator/` | `/inspiration/ai/bing-image-creator/` | - | - | - | - |

**Fill in using:**
- **Current Ranking:** Google Search Console (position in SERPs)
- **Current Traffic:** Google Analytics (last 30 days)
- **Indexed:** Google Search Console (how many pages indexed)
- **Backlinks:** Ahrefs / Moz (estimated backlink count)

**Commands to execute NOW:**

```bash
# Export GA data for baseline
# Export GSC data for baseline
# Take screenshots of rankings
# Note: Do this manually in web interfaces
```

#### Google Search Console Preparation

**Step 1: Verify new URL structure**

1. Log in to Google Search Console (promptfinder.net property)
2. Go to Settings > Crawl stats
3. Screenshot the baseline crawl statistics
4. Note: Google will NOT see `/inspiration/ai/{generator}/` pages yet

**Step 2: Create URL mapping document**

In GSC, you'll manually request indexing for new URLs after redirect is live.

**Step 3: Backup current Search Console data**

- Download all URL Inspection reports for current `/ai/*` pages
- Download current Core Web Vitals data
- Save Search Performance data (last 90 days minimum)

```bash
# Create backup directory
mkdir -p docs/seo_backups/pre_migration_$(date +%Y%m%d)

# Note: Manual export from GSC required
# Save all reports to this directory
```

#### Google Analytics Baseline

```bash
# Screenshot current GA dashboard
# Metrics to track:
# - Users (last 30 days)
# - Sessions
# - Engagement rate
# - Bounce rate
# - Conversion rate (if applicable)

# Create baseline report in Google Analytics
# Export as PDF for reference
```

### Week 1: Technical Preparation Checklist

- [ ] Document all 11 current URLs and their traffic
- [ ] Export Google Search Console data (all 11 pages)
- [ ] Export Google Analytics baseline (30 days minimum)
- [ ] Take screenshots of current Google rankings
- [ ] Create redirect mapping spreadsheet
- [ ] Document Heroku current DNS records
- [ ] Backup current `prompts/urls.py` to separate file
- [ ] Create new `/inspiration/` app structure (if needed)
- [ ] Write Django redirect implementation
- [ ] Set up staging environment to test
- [ ] Create rollback plan document

---

## Implementation Guide

### Option Comparison: Redirect Implementation Methods

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Django Redirect Model** | Easy to manage in admin, quick changes | Database queries on every request | Temporary redirects, small scale |
| **URL Pattern with `RedirectView`** | Permanent fix, fast, clean code | Requires code deployment | Permanent migrations |
| **Middleware** | Centralized control, flexible rules | Complex to debug | Complex rules/patterns |
| **Web Server (Nginx)** | Fastest, zero Django overhead | Requires infrastructure knowledge | High-traffic sites, final state |
| **Meta Refresh (NOT RECOMMENDED)** | Works in browser | Poor SEO, slow, user experience | Only emergency backup |

**Recommendation for PromptFinder:** URL Pattern with `RedirectView` (permanent, clean, Django-native)

### Implementation Option 1: Django Redirect Views (RECOMMENDED)

**Why this option:**
- Best for permanent SEO redirects
- No database queries needed
- Explicit in code (easy to audit)
- Proper HTTP 301 status code
- Easy to track via logs

**File:** `prompts/urls.py`

```python
from django.urls import path, re_path
from django.views.generic.base import RedirectView
from . import views
from . import views_admin

app_name = 'prompts'

urlpatterns = [
    # ... existing URL patterns ...

    # AI Generator Category Pages (NEW URLs - Phase 3)
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # PERMANENT REDIRECTS FROM OLD URLs TO NEW URLS (301)
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(
             pattern_name='prompts:ai_generator_category_new',
             permanent=True,  # This sets HTTP 301 status code
             query_string=True  # Preserves ?page=2&sort=trending etc.
         ),
         name='ai_generator_category_old'),
]
```

**Key Points:**
- `permanent=True` → HTTP 301 (SEO-friendly)
- `query_string=True` → Preserves pagination and filters
- `pattern_name` → Links to new view automatically

### Implementation Option 2: Custom Redirect View (More Control)

**Use this if you need more flexibility:**

**File:** `prompts/views.py`

```python
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 60 * 24), name='get')  # Cache 24 hours
class AiGeneratorCategoryOldRedirect(RedirectView):
    """
    Custom redirect view for old /ai/{generator}/ URLs to new structure.
    Uses 301 Permanent Redirect for SEO.
    """
    permanent = True
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        generator_slug = kwargs.get('generator_slug')

        # Optional: Validate generator slug exists
        from prompts.constants import AI_GENERATORS

        if generator_slug not in AI_GENERATORS:
            # If invalid generator, redirect to home
            return reverse('prompts:home')

        # Build new URL with /inspiration/ prefix
        new_url = reverse('prompts:ai_generator_category_new',
                         kwargs={'generator_slug': generator_slug})

        # Preserve query string (handled by parent class)
        return new_url
```

**File:** `prompts/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    # New URLs
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # Old URLs with custom redirect
    path('ai/<slug:generator_slug>/',
         views.AiGeneratorCategoryOldRedirect.as_view(),
         name='ai_generator_category_old'),
]
```

### Implementation Option 3: Middleware-Based Redirects

**Use this for complex multi-pattern redirects:**

**File:** `prompts/middleware.py`

```python
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
import re

class LegacyAIGeneratorRedirectMiddleware:
    """
    Redirects old /ai/{generator}/ URLs to new /inspiration/ai/{generator}/ structure.
    Uses 301 Permanent Redirect (SEO-friendly).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Compile regex once for performance
        self.pattern = re.compile(r'^/ai/([a-z0-9\-]+)/?')

    def __call__(self, request):
        # Check if path matches old pattern
        match = self.pattern.match(request.path)

        if match:
            generator_slug = match.group(1)

            # Build new URL
            new_path = f'/inspiration/ai/{generator_slug}/'

            # Preserve query string
            if request.GET:
                new_path += '?' + request.GET.urlencode()

            # Return 301 Permanent Redirect
            return HttpResponsePermanentRedirect(new_path)

        # If not a redirect, proceed normally
        response = self.get_response(request)
        return response
```

**File:** `prompts_manager/settings.py`

Add to `MIDDLEWARE` list:

```python
MIDDLEWARE = [
    # ... other middleware ...
    'prompts.middleware.LegacyAIGeneratorRedirectMiddleware',
    # ... remaining middleware ...
]
```

**Note:** Middleware runs before URL routing, so slower but more flexible.

---

## RECOMMENDED IMPLEMENTATION

### Use Django RedirectView (Simplest & Best)

**Step 1: Update `prompts/urls.py`**

```python
from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from . import views_admin

app_name = 'prompts'

urlpatterns = [
    # ============================================================
    # NEW AI GENERATOR CATEGORY PAGES (INSPIRATION STRUCTURE)
    # ============================================================
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # ============================================================
    # LEGACY REDIRECTS (301 PERMANENT REDIRECTS)
    # These redirect old URLs to new structure
    # Preserves rankings + query parameters
    # ============================================================
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(
             pattern_name='prompts:ai_generator_category_new',
             permanent=True,  # HTTP 301 status
             query_string=True,  # Preserve ?page=2&sort=trending
         ),
         name='ai_generator_category_old'),

    # ... rest of existing patterns ...
]
```

**Step 2: Update view function name (if needed)**

The current view name can stay the same. The URL pattern name changed from `ai_generator_category` to `ai_generator_category_new`, but the view function doesn't change.

Optional: Update any template links that hardcode URLs:

```django
{# OLD #}
<a href="{% url 'prompts:ai_generator_category' generator_slug='midjourney' %}">Midjourney</a>

{# NEW #}
<a href="{% url 'prompts:ai_generator_category_new' generator_slug='midjourney' %}">Midjourney</a>
```

**Step 3: Test locally**

```bash
python manage.py runserver

# In another terminal, test redirect:
curl -I http://localhost:8000/ai/midjourney/
# Expected output:
# HTTP/1.1 301 Moved Permanently
# Location: /inspiration/ai/midjourney/
```

**Step 4: Deploy to Heroku**

```bash
# Commit changes
git add prompts/urls.py
git commit -m "refactor(seo): Add 301 redirects from /ai/* to /inspiration/ai/*"

# Push to Heroku
git push heroku main

# Verify redirect live
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
```

### Query String & Pagination Handling

Your site uses pagination with `?page=2`. Verify it's preserved:

```bash
# Test with query parameters
curl -I "https://yoursite.com/ai/midjourney/?page=2&sort=trending"

# Should redirect to:
# https://yoursite.com/inspiration/ai/midjourney/?page=2&sort=trending
```

If `query_string=True` is set in RedirectView, Django handles this automatically.

---

## Testing Protocol

### Phase 1: Local Testing (Before Deployment)

#### Unit Test Redirects

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

    def test_trailing_slash_preserved(self):
        """Test that redirects work with/without trailing slash."""
        # With trailing slash
        response1 = self.client.get('/ai/midjourney/', follow=False)
        self.assertEqual(response1.status_code, HTTPStatus.MOVED_PERMANENTLY)

        # Without trailing slash (Django should normalize)
        response2 = self.client.get('/ai/midjourney', follow=False)
        self.assertEqual(response2.status_code, HTTPStatus.MOVED_PERMANENTLY)

    def test_new_url_returns_200(self):
        """Test that new URLs return 200 OK."""
        for generator in self.generators:
            response = self.client.get(f'/inspiration/ai/{generator}/')
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f"New URL for {generator} does not return 200"
            )

    def test_invalid_generator_handled(self):
        """Test that invalid generators still redirect."""
        response = self.client.get('/ai/invalid-generator/', follow=False)
        self.assertEqual(response.status_code, HTTPStatus.MOVED_PERMANENTLY)
```

**Run tests:**

```bash
# Run all redirect tests
python manage.py test prompts.tests.test_seo_redirects

# Run with verbose output
python manage.py test prompts.tests.test_seo_redirects -v 2

# Expected output:
# test_old_url_returns_301 ... ok
# test_redirect_destination_correct ... ok
# test_redirect_preserves_query_string ... ok
# (etc.)
# Ran 6 tests in 0.234s
# OK
```

### Phase 2: Curl Command Testing (Staging/Production-like)

**Run against local development server:**

```bash
# Start dev server
python manage.py runserver

# In another terminal, run tests:

# Test 1: Verify 301 status code
echo "=== Test 1: Check HTTP 301 status ==="
curl -I http://localhost:8000/ai/midjourney/
# Expected:
# HTTP/1.1 301 Moved Permanently
# Location: /inspiration/ai/midjourney/

# Test 2: Check all 11 generators
echo "=== Test 2: Check all 11 generators ==="
for gen in midjourney dalle3 dalle2 stable-diffusion leonardo-ai flux sora sora2 veo-3 adobe-firefly bing-image-creator; do
    echo "Testing: $gen"
    curl -s -I "http://localhost:8000/ai/$gen/" | grep -E "HTTP|Location"
done

# Test 3: Verify query string preservation
echo "=== Test 3: Check query string preservation ==="
curl -I "http://localhost:8000/ai/midjourney/?page=2&sort=trending"
# Expected:
# HTTP/1.1 301 Moved Permanently
# Location: /inspiration/ai/midjourney/?page=2&sort=trending

# Test 4: Test pagination redirect
echo "=== Test 4: Test pagination query strings ==="
curl -L "http://localhost:8000/ai/midjourney/?page=1" | grep -o "page=1" | head -1

# Test 5: Verify trailing slash handling
echo "=== Test 5: Check trailing slash ==="
curl -I "http://localhost:8000/ai/midjourney" | head -3
```

**Create testing script:**

**File:** `scripts/test_redirects.sh`

```bash
#!/bin/bash
# Test 301 redirects for all AI generators
# Usage: ./scripts/test_redirects.sh http://localhost:8000

BASE_URL="${1:-http://localhost:8000}"
GENERATORS=(
    "midjourney"
    "dalle3"
    "dalle2"
    "stable-diffusion"
    "leonardo-ai"
    "flux"
    "sora"
    "sora2"
    "veo-3"
    "adobe-firefly"
    "bing-image-creator"
)

echo "Testing 301 Redirects"
echo "Base URL: $BASE_URL"
echo "============================================"

PASSED=0
FAILED=0

for gen in "${GENERATORS[@]}"; do
    OLD_URL="$BASE_URL/ai/$gen/"
    EXPECTED_NEW="$BASE_URL/inspiration/ai/$gen/"

    # Get redirect response
    RESPONSE=$(curl -s -I -L "$OLD_URL" 2>&1)
    STATUS_LINE=$(echo "$RESPONSE" | head -n 1)
    LOCATION=$(echo "$RESPONSE" | grep -i "^Location:" | head -1 | cut -d' ' -f2-)

    echo "Generator: $gen"
    echo "  Old URL:         $OLD_URL"
    echo "  Status:          $STATUS_LINE"
    echo "  Redirect to:     $LOCATION"

    # Check if status contains 301
    if echo "$STATUS_LINE" | grep -q "301"; then
        # Check if location is correct
        if echo "$LOCATION" | grep -q "inspiration/ai/$gen"; then
            echo "  Result:          ✓ PASS"
            ((PASSED++))
        else
            echo "  Result:          ✗ FAIL (wrong destination)"
            ((FAILED++))
        fi
    else
        echo "  Result:          ✗ FAIL (not 301 status)"
        ((FAILED++))
    fi
    echo ""
done

echo "============================================"
echo "Results: $PASSED passed, $FAILED failed"
exit $FAILED
```

**Make executable and run:**

```bash
chmod +x scripts/test_redirects.sh
./scripts/test_redirects.sh http://localhost:8000
```

### Phase 3: Automated Browser Testing (Selenium)

**File:** `prompts/tests/test_seo_redirects_selenium.py`

```python
from django.test import LiveServerTestCase, override_settings
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

@override_settings(DEBUG=True)
class AIGeneratorRedirectBrowserTest(LiveServerTestCase):
    """Test redirects via actual browser (checks HTTP headers)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument('--headless')  # Run headless (no GUI)
        cls.driver = webdriver.Chrome(options=options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def test_redirect_chain_not_present(self):
        """Test that there's no redirect chain (e.g., 301 -> 302 -> 200)."""
        generators = ['midjourney', 'dalle3', 'stable-diffusion']

        for gen in generators:
            old_url = f'{self.live_server_url}/ai/{gen}/'

            # Navigate to old URL
            self.driver.get(old_url)

            # Final URL should be new structure
            final_url = self.driver.current_url
            expected_url = f'{self.live_server_url}/inspiration/ai/{gen}/'

            self.assertEqual(
                final_url,
                expected_url,
                f"Redirect chain detected for {gen}"
            )

    def test_new_url_loads_successfully(self):
        """Test that new URLs load without errors."""
        generators = ['midjourney', 'dalle3']

        for gen in generators:
            new_url = f'{self.live_server_url}/inspiration/ai/{gen}/'

            self.driver.get(new_url)

            # Check for 404 or error indicators
            page_text = self.driver.page_source
            self.assertNotIn('404', page_text)
            self.assertNotIn('Error', page_text)
```

---

## Verification Checklist

### Pre-Deployment Verification (Staging)

Verify redirect implementation BEFORE deploying to production:

**Checklist:**

- [ ] **Django Tests Pass**
  ```bash
  python manage.py test prompts.tests.test_seo_redirects -v 2
  # All tests should pass
  ```

- [ ] **Curl Tests Pass**
  ```bash
  ./scripts/test_redirects.sh http://localhost:8000
  # All 11 generators should show ✓ PASS
  ```

- [ ] **HTTP Status Correct**
  ```bash
  curl -I http://localhost:8000/ai/midjourney/
  # Must show: HTTP/1.1 301 Moved Permanently
  # NOT 302 (temporary) or 307
  ```

- [ ] **Location Header Correct**
  ```bash
  curl -I http://localhost:8000/ai/midjourney/ | grep Location
  # Must show: Location: /inspiration/ai/midjourney/
  ```

- [ ] **Query String Preserved**
  ```bash
  curl -I "http://localhost:8000/ai/midjourney/?page=2&sort=trending"
  # Must redirect to /inspiration/ai/midjourney/?page=2&sort=trending
  ```

- [ ] **No Redirect Chains**
  ```bash
  curl -L http://localhost:8000/ai/midjourney/ -D /tmp/headers.txt
  # Should only show ONE 301 redirect
  # cat /tmp/headers.txt should show 301 once, then 200
  ```

- [ ] **Cache Headers Correct**
  ```bash
  curl -I http://localhost:8000/ai/midjourney/ | grep -i cache
  # For 301 redirects, Cache-Control: public, max-age=31536000 (1 year)
  # Because 301s should be cached for SEO
  ```

- [ ] **All 11 Generators Work**
  ```bash
  for gen in midjourney dalle3 dalle2 stable-diffusion leonardo-ai flux sora sora2 veo-3 adobe-firefly bing-image-creator; do
      echo "Testing $gen..."
      curl -s -I "http://localhost:8000/ai/$gen/" | grep HTTP
  done
  # All should show 301
  ```

- [ ] **New URLs Return 200**
  ```bash
  curl -I http://localhost:8000/inspiration/ai/midjourney/
  # Must show: HTTP/1.1 200 OK
  ```

- [ ] **Settings.py Not Modified**
  ```bash
  git diff prompts_manager/settings.py
  # Should show no changes for redirect functionality
  ```

### Post-Deployment Verification (Production)

#### Immediate Verification (Within 1 Hour)

After deploying to Heroku, verify immediately:

**Staging URL Tests:**

```bash
# Test 1: Production HTTP redirect
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
# Expected: 301 Moved Permanently + Location header

# Test 2: All 11 generators
for gen in midjourney dalle3 dalle2 stable-diffusion leonardo-ai flux sora sora2 veo-3 adobe-firefly bing-image-creator; do
    STATUS=$(curl -s -I "https://mj-project-4-68750ca94690.herokuapp.com/ai/$gen/" | head -1)
    echo "$gen: $STATUS"
done

# Test 3: Follow redirect to confirm destination
curl -L https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ -D /tmp/final_headers.txt
# Check /tmp/final_headers.txt - should show 301, then 200

# Test 4: Verify content loads
curl -s https://mj-project-4-68750ca94690.herokuapp.com/inspiration/ai/midjourney/ | grep -o "<title>.*</title>"
```

**Create production verification script:**

**File:** `scripts/verify_production_redirects.sh`

```bash
#!/bin/bash
# Verify 301 redirects are working in production
# Usage: ./scripts/verify_production_redirects.sh

PROD_URL="https://mj-project-4-68750ca94690.herokuapp.com"
GENERATORS=(
    "midjourney"
    "dalle3"
    "dalle2"
    "stable-diffusion"
    "leonardo-ai"
    "flux"
    "sora"
    "sora2"
    "veo-3"
    "adobe-firefly"
    "bing-image-creator"
)

echo "Production Redirect Verification"
echo "URL: $PROD_URL"
echo "Time: $(date)"
echo "============================================"

PASSED=0
FAILED=0

for gen in "${GENERATORS[@]}"; do
    # Get HTTP status of old URL
    OLD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_URL/ai/$gen/")

    # Get location header
    LOCATION=$(curl -s -I "$PROD_URL/ai/$gen/" | grep -i "^Location:" | cut -d' ' -f2-)

    echo "Generator: $gen"
    echo "  Old URL Status: $OLD_STATUS"
    echo "  Redirects to:   $LOCATION"

    if [ "$OLD_STATUS" = "301" ]; then
        if echo "$LOCATION" | grep -q "inspiration/ai/$gen"; then
            echo "  Result:         ✓ PASS"
            ((PASSED++))
        else
            echo "  Result:         ✗ FAIL (wrong destination: $LOCATION)"
            ((FAILED++))
        fi
    else
        echo "  Result:         ✗ FAIL (status is $OLD_STATUS, expected 301)"
        ((FAILED++))
    fi
    echo ""
done

echo "============================================"
echo "Results: $PASSED passed, $FAILED failed"

# Alert if any failed
if [ $FAILED -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: $FAILED redirect(s) failed!"
    exit 1
else
    echo ""
    echo "✓ All redirects verified!"
    exit 0
fi
```

**Run verification:**

```bash
chmod +x scripts/verify_production_redirects.sh
./scripts/verify_production_redirects.sh
```

#### Weekly Verification (First 4 Weeks)

**Week 1-4 Verification Checklist:**

- [ ] **Monday:** Run `verify_production_redirects.sh` script
- [ ] **Wednesday:** Check Heroku logs for errors
  ```bash
  heroku logs --app mj-project-4 | grep "301\|redirect" | head -20
  ```
- [ ] **Friday:** Verify Google Search Console shows no errors

**Heroku Logs Check:**

```bash
# Check for redirect-related activity
heroku logs --app mj-project-4 --tail

# Look for any error messages related to redirects
heroku logs --app mj-project-4 | grep -i error | head -10

# Check for 404s (should be minimal)
heroku logs --app mj-project-4 | grep "404" | head -10
```

#### SEO Verification Tools

**Tool 1: Google Search Console**

1. Log in: https://search.google.com/search-console
2. Select property: promptfinder.net
3. Go to **URL Inspection**
4. For each old URL, check:
   - Request indexing status
   - Whether Google sees 301 redirect
   - Linked page (new URL)
5. Schedule re-crawl if needed

**Tool 2: Screaming Frog (Free Version)**

```bash
# Download: https://www.screamingfrog.co.uk/seo-spider-free/
# Steps:
# 1. Open Screaming Frog
# 2. Enter: https://mj-project-4-68750ca94690.herokuapp.com
# 3. Crawl
# 4. Filter by: URL contains '/ai/'
# 5. Check all redirects show 301 + proper destination
# 6. Export report as CSV
```

**Tool 3: SEO Checkup Tools**

```bash
# Option 1: SEMrush
# - Site Audit
# - Check Redirect Chains
# - Check Redirect Count

# Option 2: Ahrefs
# - Site Audit
# - Redirect chains report

# Option 3: Moz Pro
# - Crawl Analysis
# - Check 301 redirects
```

---

## Post-Migration Monitoring

### Week 1: Immediate Monitoring

**Daily Checklist (First 7 Days):**

| Day | Task | Pass/Fail | Notes |
|-----|------|----------|-------|
| Day 1 | Run production verification script | [ ] | |
| Day 1 | Check Heroku logs for errors | [ ] | |
| Day 1 | Monitor uptime (StatusPage) | [ ] | |
| Day 2 | Check Google Search Console | [ ] | |
| Day 2 | Monitor traffic in Analytics | [ ] | |
| Day 3 | Verify old URLs still redirect | [ ] | |
| Day 4 | Check for 404 errors | [ ] | |
| Day 5 | Review Search Console errors | [ ] | |
| Day 6 | Spot-check 3 random generators | [ ] | |
| Day 7 | Generate weekly report | [ ] | |

**Google Search Console - Day 1 Actions:**

1. Open https://search.google.com/search-console
2. For each old URL (`/ai/{generator}/`):
   - Click "Inspect URL"
   - Click "Request Indexing" to ask Google to re-crawl
   - This tells Google: "Hey, this URL moved!"

3. For each new URL (`/inspiration/ai/{generator}/`):
   - Allow Google to discover and index naturally
   - Don't manually request unless needed

**Google Analytics - Day 1 Setup:**

Create segments to track redirect impact:

1. **Segment 1: Old URL Traffic**
   - Condition: Page Path contains `/ai/`
   - Track: Sessions, Users, Bounce Rate

2. **Segment 2: New URL Traffic**
   - Condition: Page Path contains `/inspiration/ai/`
   - Track: Sessions, Users, Bounce Rate

3. **Compare** before/after metrics

**Commands for monitoring:**

```bash
# Check error rate in Heroku
heroku logs --app mj-project-4 --dyno=web | grep -c "ERROR\|500"

# Monitor redirect success rate
heroku logs --app mj-project-4 | grep "301" | wc -l

# Check for spike in 404s (should be minimal)
heroku logs --app mj-project-4 | grep "404" | wc -l
```

### Week 2-4: Observation Period

**Metrics to Track Daily:**

| Metric | Where to Check | What to Look For |
|--------|----------------|------------------|
| **Organic Traffic** | Google Analytics | Should remain stable |
| **Bounce Rate** | Google Analytics | Should not increase |
| **Avg Session Duration** | Google Analytics | Should not decrease |
| **Crawl Stats** | GSC → Settings | Google should crawl new URLs |
| **Search Impressions** | GSC → Performance | Old URLs might drop, new URLs should appear |
| **Search Clicks** | GSC → Performance | Should shift from old to new URLs |
| **Index Status** | GSC → Coverage | Old URLs should show 301, new URLs indexed |
| **Core Web Vitals** | GSC → Experience | Should remain stable |
| **HTTP Errors** | GSC → Coverage | No new 404s or errors |
| **Redirect Chains** | GSC → Coverage | Must be 0 (single 301) |
| **Internal Links** | Check for hardcoded links | Should point to new URLs |
| **Backlinks** | Ahrefs/Moz | Monitor any changes |

**Google Search Console - Week 2-4 Monitoring:**

1. **Check Coverage Report:**
   - Old URLs should show as "Excluded" with reason "Submitted URL has a Redirect"
   - This is GOOD - it means Google found the 301 redirect
   - URL should appear as "Valid and indexed" under new URL

2. **Check Performance Report:**
   - Filter by "Search Appearance"
   - Look for rankings with new URL structure
   - Old URLs should slowly disappear from reports

3. **Check Crawl Stats:**
   - Monitor "Crawled pages per day"
   - Should show new URLs being crawled
   - Old URLs crawls should decrease

**Google Analytics - Week 2-4 Monitoring:**

```
Home > Reports > Traffic Acquisition > Organic Search

Compare:
- Week before migration
- Week after migration

Look for:
- Sessions: Should stay stable (+/- 10%)
- Users: Should stay stable (+/- 10%)
- Bounce rate: Should not increase
- Avg session duration: Should not decrease
```

### Week 4-8: Ongoing Monitoring

**Monthly Monitoring Checklist:**

**Week 4:**
- [ ] Rankings recovery assessment
- [ ] Traffic stabilization check
- [ ] Backlink monitoring (should be minimal change)
- [ ] User feedback (any broken links reported?)
- [ ] Generate 4-week report

**Week 8:**
- [ ] Final ranking comparison (vs pre-migration)
- [ ] Traffic comparison (vs pre-migration)
- [ ] SEO health check
- [ ] Archive all monitoring data
- [ ] Generate 8-week final report

### Monitoring Dashboard Setup

**Create spreadsheet to track key metrics:**

**File:** `docs/seo_monitoring/redirect_migration_tracking.xlsx`

| Date | Midjourney Traffic | DALLE-3 Traffic | Stable Diff Traffic | Avg Bounce Rate | Crawl Errors | GSC Impressions | Notes |
|------|-------------------|-----------------|-------------------|-----------------|-------------|-----------------|-------|
| Pre-Migration | 150 | 120 | 95 | 35% | 0 | 2,500 | Baseline |
| Day 1 | 148 | 118 | 94 | 35% | 0 | 2,480 | Just deployed |
| Day 2 | 152 | 122 | 96 | 35% | 0 | 2,510 | Stable |
| Day 3 | 155 | 125 | 98 | 35% | 0 | 2,600 | Good |
| Week 2 | 153 | 123 | 97 | 35% | 0 | 2,550 | Stable |
| Week 4 | 154 | 124 | 98 | 35% | 0 | 2,570 | Recovery? |
| Week 8 | 156 | 126 | 100 | 35% | 0 | 2,620 | Improved! |

### Alert Conditions (When to Act)

**RED FLAGS - Act Immediately:**

1. **Redirect Status Code is NOT 301**
   - Action: Rollback immediately
   - Command: `git revert [commit-hash]`

2. **Redirect Chain Detected (301 → 302 → 200)**
   - Action: Check URL patterns for conflicts
   - Likely cause: URL pattern ordering issue

3. **404 Errors Spike**
   - Action: Check what URLs are getting 404s
   - Command: `heroku logs | grep 404 | head -20`

4. **Traffic Drops >20% Within 24 Hours**
   - Action: Check Google Search Console for errors
   - Likely cause: Improper redirect (302 instead of 301)

5. **Google Reports "Redirect Chains"**
   - Action: Fix URL patterns immediately
   - In GSC: Coverage → go to "Submitted URL has a Redirect" → check what it redirects to

6. **Heroku Errors Related to Redirects**
   - Action: Check logs and rollback if necessary
   - Command: `heroku logs --app mj-project-4 --dyno=web | tail -100`

### Weekly Reporting

**Create weekly status report:**

**Template:** `docs/seo_monitoring/weekly_redirect_report_template.md`

```markdown
# Weekly Redirect Migration Report

**Week:** [Week number and dates]
**Status:** [On Track / At Risk / Degraded]

## Key Metrics

### Traffic
- Old URLs (/ai/*): [X] sessions
- New URLs (/inspiration/ai/*): [Y] sessions
- Total organic: [Z] sessions
- **Trend:** [↑ Increasing / → Stable / ↓ Decreasing]

### Search Console
- Old URLs indexed: [X]
- New URLs indexed: [Y]
- Crawl errors: [X]
- Redirect chains detected: [X] (should be 0)
- **Trend:** [Healthy / Warning / Critical]

### Performance
- Avg bounce rate: [X]%
- Avg session duration: [X] min
- Core Web Vitals: [Green / Yellow / Red]

## Issues Identified

- [List any issues encountered]

## Actions Taken

- [List any corrective actions]

## Next Week's Focus

- [What to monitor next week]

---
Report generated: [Date]
```

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Redirect Returns 302 Instead of 301

**Problem:**
```bash
curl -I https://yoursite.com/ai/midjourney/
HTTP/1.1 302 Found  # ← WRONG, should be 301
Location: /inspiration/ai/midjourney/
```

**Root Causes:**
- `permanent=False` in RedirectView
- Django's `RedirectFallbackMiddleware` interference
- Web server caching old config

**Solution:**

```python
# Check: prompts/urls.py
path('ai/<slug:generator_slug>/',
     RedirectView.as_view(
         pattern_name='prompts:ai_generator_category_new',
         permanent=True,  # ← MUST be True
         query_string=True,
     ),
     name='ai_generator_category_old'),
```

**Verify fix:**
```bash
# Force reload (clear caches)
heroku restart --app mj-project-4

# Test again
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
# Should now show: HTTP/1.1 301 Moved Permanently
```

#### Issue 2: Redirect Chain Detected

**Problem:**
```
301 → 302 → 200 (three requests instead of two)
```

**Root Causes:**
- Two redirect rules matching same URL
- URL pattern ordering issue
- Middleware interference

**Solution:**

1. **Check URL pattern order:**
```python
# prompts/urls.py - Order matters!
urlpatterns = [
    # ... other patterns ...

    # NEW URLs first (most specific)
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # OLD URLs second (redirects to above)
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(...),
         name='ai_generator_category_old'),
]
```

2. **Remove duplicate patterns:**
```bash
# Check for duplicate patterns
grep -n "ai/" prompts/urls.py
# Look for multiple entries with same pattern
```

3. **Check middleware:**
```python
# prompts_manager/settings.py
# Make sure no other middleware is causing redirects
MIDDLEWARE = [
    # ... check for custom redirect middleware ...
]
```

4. **Test the fix:**
```bash
# Deploy and test
git push heroku main
curl -L https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ -D /tmp/headers.txt
cat /tmp/headers.txt | grep -E "HTTP|Location"
# Should show: 301, then 200 (only two requests)
```

#### Issue 3: Query Parameters Not Preserved

**Problem:**
```bash
curl https://yoursite.com/ai/midjourney/?page=2&sort=trending
# Redirects to /inspiration/ai/midjourney/ (query params lost)
```

**Solution:**

```python
# Ensure query_string=True in RedirectView
path('ai/<slug:generator_slug>/',
     RedirectView.as_view(
         pattern_name='prompts:ai_generator_category_new',
         permanent=True,
         query_string=True,  # ← MUST be True
     ),
     name='ai_generator_category_old'),
```

**Verify fix:**
```bash
curl -I "https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/?page=2&sort=trending"
# Location header should include: ?page=2&sort=trending
```

#### Issue 4: Google Search Console Still Shows Old URLs

**Problem:**
GSC still shows `/ai/{generator}/` pages as indexed after 2+ weeks.

**Root Causes:**
- Google hasn't re-crawled old URLs yet
- 301 redirect not detected properly
- GSC cache hasn't refreshed

**Solution:**

1. **Manually request re-indexing:**
   - Go to GSC
   - Click "URL Inspection"
   - Enter old URL: `/ai/midjourney/`
   - Click "Request Indexing"
   - Repeat for all 11 URLs

2. **Set up GSC redirect mapping (optional):**
   - Settings → Address prefix → Verify new URL structure
   - This helps GSC understand the migration

3. **Wait for recrawl:**
   - Google typically finds 301s within 24 hours
   - Full indexing update: 3-5 days
   - Complete replacement: 1-4 weeks

4. **Monitor in GSC:**
   - Coverage → should show old URLs as "Excluded" with "Redirect"
   - This is normal and expected

#### Issue 5: Traffic Dropped Significantly

**Problem:**
```
Before migration: 500 sessions/day from /ai/* pages
After migration: 150 sessions/day from /inspiration/ai/* pages
```

**Root Causes:**
- Improper redirect (302 instead of 301) - Google doesn't pass ranking
- Redirect not implemented correctly
- URL structure too different (unlikely but possible)

**Diagnostic Steps:**

```bash
# Step 1: Verify redirect status is 301
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
# Must show 301

# Step 2: Check Google Search Console for errors
# URL Inspection → old URL → should show "Redirect found"

# Step 3: Check if new URLs are indexed
# GSC → Coverage → should show /inspiration/ai/* as indexed

# Step 4: Check if rankings moved
# GSC → Performance → filter by "inspiration/ai"
# Should see rankings appearing for new URLs

# Step 5: If traffic still low after 2 weeks
# Action: Investigate further or consider rollback
```

**If traffic doesn't recover within 2 weeks:**

```bash
# Rollback procedure:
git log --oneline | head -10
# Find the redirect commit

git revert [commit-hash]
git push heroku main

# Monitor traffic recovery
# Should return to normal within 24-48 hours
```

#### Issue 6: SEO Tool Reports Redirect Chain

**Tools:** Screaming Frog, Ahrefs, SEMrush, Moz

**Problem:**
Tool reports redirect chain when there shouldn't be one.

**Cause:** Tools might be following redirects improperly

**Solution:**

```bash
# Manual verification (most reliable)
curl -L https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/ -D /tmp/full_headers.txt

cat /tmp/full_headers.txt
# Count the number of HTTP status lines
# Should only be 2: one 301, one 200

# Example output (CORRECT):
# HTTP/1.1 301 Moved Permanently
# Location: /inspiration/ai/midjourney/
# [blank line]
# HTTP/1.1 200 OK
# [rest of response]

# If you see 301 → 302 → 200, there IS a chain - investigate
```

### Rollback Procedure

If major issues are detected:

```bash
# Step 1: Identify the redirect commit
git log --oneline prompts/urls.py | head -5
# Find: "301 redirects from /ai/* to /inspiration/ai/*"

# Step 2: Revert the commit
git revert [commit-hash] --no-edit

# Step 3: Push to Heroku
git push heroku main

# Step 4: Verify old system restored
curl -I https://mj-project-4-68750ca94690.herokuapp.com/ai/midjourney/
# Should return 200 (not 301)

# Step 5: Monitor traffic recovery
# Check Analytics in next 24 hours
# Traffic should return to normal
```

**Post-Rollback Analysis:**

If rollback was necessary:

1. Identify what went wrong
2. Fix the issue locally
3. Test thoroughly before re-attempting migration
4. Consider phased migration (1-2 generators at a time)

---

## Implementation Timeline

### Week 1: Pre-Migration Preparation

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| Monday | Document baseline metrics | You | [ ] |
| Tuesday | Export GSC data | You | [ ] |
| Wednesday | Export Analytics baseline | You | [ ] |
| Thursday | Create testing scripts | Dev | [ ] |
| Friday | Staging environment testing | Dev | [ ] |

**Completion Criteria:**
- All baseline metrics documented
- Testing scripts verified locally
- No open questions

### Week 2: Implementation & Deployment

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| Monday | Implement redirects in code | Dev | [ ] |
| Tuesday | Local testing (unit tests + curl) | Dev | [ ] |
| Wednesday | Staging environment final test | Dev | [ ] |
| Thursday | Production deployment | Dev | [ ] |
| Friday | Immediate post-deployment verification | You | [ ] |

**Deployment Window (Recommended):**
- Time: Tuesday or Wednesday 10 AM - 2 PM UTC
- Reason: Mid-week, mid-day allows monitoring
- Avoid: Friday afternoons, weekends, holidays
- Monitor: 4-6 hours post-deployment

### Week 3-8: Monitoring & Verification

| Week | Primary Focus | Actions |
|------|---------------|---------|
| Week 1 | Immediate stability | Daily checks, error monitoring |
| Week 2 | Traffic stabilization | Continue daily checks |
| Week 3 | SEO metric movement | Monitor GSC, Analytics |
| Week 4 | Ranking recovery | Assess ranking changes |
| Week 5-8 | Long-term monitoring | Weekly checks, adjust as needed |

---

## Success Criteria

### Migration is SUCCESSFUL if:

✅ **Week 1:**
- All 11 old URLs return HTTP 301 (not 302)
- All redirects point to correct new URLs
- Query parameters preserved
- No redirect chains detected
- Heroku logs show no errors
- No spike in 404 errors

✅ **Week 2-4:**
- Traffic remains stable (±10% variance)
- Bounce rate unchanged
- Engagement metrics unchanged
- Google Search Console shows no errors
- New URLs being crawled by Google

✅ **Week 4-8:**
- Rankings beginning to appear for new URLs
- Old URLs showing as "Excluded - Redirect" in GSC (normal)
- No significant traffic loss
- Organic search performance maintained

### Red Flags (Rollback Triggers):

🚨 **Immediate Rollback If:**
- Redirect status code is 302 (not 301)
- Redirect chains detected (301 → 302 → 200)
- Traffic drops >30% within 24 hours
- New URLs not being indexed after 48 hours
- Heroku error rate spikes significantly

---

## Tools & Resources

### Required Tools

| Tool | Purpose | Cost | Link |
|------|---------|------|------|
| **Google Search Console** | SEO monitoring | Free | https://search.google.com/search-console |
| **Google Analytics** | Traffic tracking | Free | https://analytics.google.com |
| **curl** | HTTP testing | Free | Pre-installed on Mac/Linux |
| **Screaming Frog** | Crawl analysis | Free (limited) | https://www.screamingfrog.co.uk |
| **Django Test Suite** | Unit testing | Free | Built-in |

### Recommended Tools (Optional)

| Tool | Purpose | Cost | Link |
|------|---------|------|------|
| **Ahrefs** | Backlink tracking | Paid | https://ahrefs.com |
| **SEMrush** | Rank tracking | Paid | https://www.semrush.com |
| **Moz Pro** | SEO audits | Paid | https://moz.com |
| **Lighthouse** | Performance testing | Free | Chrome DevTools |
| **Uptime Robot** | Monitoring | Free tier | https://uptimerobot.com |

---

## Appendix: Code Examples

### Complete Implementation Example

**File:** `prompts/urls.py` (Complete)

```python
from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from . import views_admin

app_name = 'prompts'

urlpatterns = [
    # ============================================================
    # HOMEPAGE & MAIN NAVIGATION
    # ============================================================
    path('', views.PromptList.as_view(), name='home'),

    # ============================================================
    # PROMPT MANAGEMENT
    # ============================================================
    path('create-prompt/', views.prompt_create, name='prompt_create'),
    path('collaborate/', views.collaborate_request, name='collaborate'),

    # Upload flow
    path('upload/', views.upload_step1, name='upload_step1'),
    path('upload/details', views.upload_step2, name='upload_step2'),
    path('upload/submit', views.upload_submit, name='upload_submit'),
    path('upload/cancel/', views.cancel_upload, name='cancel_upload'),
    path('upload/extend/', views.extend_upload_time, name='extend_upload_time'),

    # Prompt detail & editing
    path('prompt/<slug:slug>/', views.prompt_detail, name='prompt_detail'),
    path('prompt/<slug:slug>/edit/', views.prompt_edit, name='prompt_edit'),
    path('prompt/<slug:slug>/delete/', views.prompt_delete, name='prompt_delete'),
    path('prompt/<slug:slug>/publish/', views.prompt_publish, name='prompt_publish'),
    path('prompt/<slug:slug>/like/', views.prompt_like, name='prompt_like'),

    # ============================================================
    # TRASH BIN
    # ============================================================
    path('trash/', views.trash_bin, name='trash_bin'),
    path('trash/<slug:slug>/restore/', views.prompt_restore, name='prompt_restore'),
    path('trash/<slug:slug>/delete-forever/', views.prompt_permanent_delete, name='prompt_permanent_delete'),
    path('trash/empty/', views.empty_trash, name='empty_trash'),

    # ============================================================
    # USER PROFILES & SOCIAL
    # ============================================================
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path('users/<str:username>/trash/', views.user_profile, {'active_tab': 'trash'}, name='user_profile_trash'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('users/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('users/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('users/<str:username>/follow-status/', views.get_follow_status, name='follow_status'),

    # ============================================================
    # SETTINGS & PREFERENCES
    # ============================================================
    path('settings/notifications/', views.email_preferences, name='email_preferences'),
    path('unsubscribe/<str:token>/', views.unsubscribe_view, name='unsubscribe'),
    path('rate-limited/', views.ratelimited, name='ratelimited'),

    # ============================================================
    # MODERATION & REPORTING
    # ============================================================
    path('prompt/<slug:slug>/report/', views.report_prompt, name='report_prompt'),
    path('admin/moderation-dashboard/', views_admin.moderation_dashboard, name='moderation_dashboard'),

    # ============================================================
    # AI GENERATOR CATEGORY PAGES
    # NEW URLS (Primary structure with /inspiration/ prefix)
    # ============================================================
    path('inspiration/ai/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category_new'),

    # PERMANENT REDIRECTS (301) FROM OLD URLS TO NEW URLS
    # These preserve SEO ranking power and redirect users properly
    # permanent=True → HTTP 301 (SEO-friendly)
    # query_string=True → Preserves pagination/filters (?page=2&sort=trending)
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(
             pattern_name='prompts:ai_generator_category_new',
             permanent=True,  # ← Critical: Sets HTTP 301 status
             query_string=True,  # ← Critical: Preserves query parameters
         ),
         name='ai_generator_category_old'),

    # ============================================================
    # SOCIAL & ENGAGEMENT
    # ============================================================
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('prompt/<slug:slug>/edit_comment/<int:comment_id>/',
         views.comment_edit, name='comment_edit'),
    path('prompt/<slug:slug>/delete_comment/<int:comment_id>/',
         views.comment_delete, name='comment_delete'),

    # ============================================================
    # ADMIN TOOLS
    # ============================================================
    path('prompt/<slug:slug>/move-up/', views.prompt_move_up, name='prompt_move_up'),
    path('prompt/<slug:slug>/move-down/', views.prompt_move_down, name='prompt_move_down'),
    path('prompt/<slug:slug>/set-order/', views.prompt_set_order, name='prompt_set_order'),
    path('prompts-admin/bulk-reorder/', views.bulk_reorder_prompts, name='bulk_reorder_prompts'),
]
```

### Testing Script (Complete)

**File:** `scripts/test_all_redirects.sh`

```bash
#!/bin/bash
# Comprehensive redirect testing script
# Tests all 11 AI generators for proper 301 redirects
# Usage: ./scripts/test_all_redirects.sh [url]

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://localhost:8000}"
GENERATORS=(
    "midjourney"
    "dalle3"
    "dalle2"
    "stable-diffusion"
    "leonardo-ai"
    "flux"
    "sora"
    "sora2"
    "veo-3"
    "adobe-firefly"
    "bing-image-creator"
)

# Test parameters
TEST_PAGES=(
    ""                      # Root page
    "?page=1"              # Page 1
    "?page=2"              # Page 2
    "?sort=trending"       # Sort parameter
    "?sort=new"            # Different sort
    "?page=2&sort=trending" # Combined parameters
)

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Header
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        301 Redirect Migration Test Suite                       ║"
echo "║        Testing: /ai/{generator}/ → /inspiration/ai/{generator}/║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Base URL: $BASE_URL"
echo "Generators: ${#GENERATORS[@]}"
echo "Test patterns: ${#TEST_PAGES[@]}"
echo ""

# ====================================================================
# TEST 1: HTTP Status Code Verification
# ====================================================================
echo "TEST 1: HTTP Status Code Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for gen in "${GENERATORS[@]}"; do
    URL="$BASE_URL/ai/$gen/"

    RESPONSE=$(curl -s -I "$URL")
    STATUS=$(echo "$RESPONSE" | head -n 1)
    STATUS_CODE=$(echo "$STATUS" | grep -o "[0-9]\{3\}" | head -1)

    ((TOTAL_TESTS++))

    if [ "$STATUS_CODE" = "301" ]; then
        echo -e "${GREEN}✓${NC} $gen: $STATUS"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗${NC} $gen: $STATUS (expected 301, got $STATUS_CODE)"
        ((FAILED_TESTS++))
    fi
done

echo ""

# ====================================================================
# TEST 2: Redirect Destination Verification
# ====================================================================
echo "TEST 2: Redirect Destination Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for gen in "${GENERATORS[@]}"; do
    URL="$BASE_URL/ai/$gen/"

    LOCATION=$(curl -s -I "$URL" | grep -i "^Location:" | cut -d' ' -f2- | tr -d '\r')
    EXPECTED="/inspiration/ai/$gen/"

    ((TOTAL_TESTS++))

    if [ "$LOCATION" = "$EXPECTED" ]; then
        echo -e "${GREEN}✓${NC} $gen → $LOCATION"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗${NC} $gen → $LOCATION (expected $EXPECTED)"
        ((FAILED_TESTS++))
    fi
done

echo ""

# ====================================================================
# TEST 3: Query String Preservation
# ====================================================================
echo "TEST 3: Query String Preservation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test with a few generators
TEST_GENERATORS=("midjourney" "dalle3" "stable-diffusion")

for gen in "${TEST_GENERATORS[@]}"; do
    for params in "${TEST_PAGES[@]}"; do
        URL="$BASE_URL/ai/$gen/$params"

        LOCATION=$(curl -s -I "$URL" | grep -i "^Location:" | cut -d' ' -f2- | tr -d '\r')
        EXPECTED="/inspiration/ai/$gen/$params"

        ((TOTAL_TESTS++))

        if [ "$LOCATION" = "$EXPECTED" ]; then
            echo -e "${GREEN}✓${NC} $gen$params"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}✗${NC} $gen$params"
            echo "  Expected: $EXPECTED"
            echo "  Got:      $LOCATION"
            ((FAILED_TESTS++))
        fi
    done
done

echo ""

# ====================================================================
# TEST 4: New URL Accessibility
# ====================================================================
echo "TEST 4: New URL Accessibility (Should return 200)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for gen in "${GENERATORS[@]}"; do
    URL="$BASE_URL/inspiration/ai/$gen/"

    RESPONSE=$(curl -s -I "$URL")
    STATUS=$(echo "$RESPONSE" | head -n 1)
    STATUS_CODE=$(echo "$STATUS" | grep -o "[0-9]\{3\}" | head -1)

    ((TOTAL_TESTS++))

    if [ "$STATUS_CODE" = "200" ]; then
        echo -e "${GREEN}✓${NC} /inspiration/ai/$gen/ returns 200"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗${NC} /inspiration/ai/$gen/ returns $STATUS_CODE (expected 200)"
        ((FAILED_TESTS++))
    fi
done

echo ""

# ====================================================================
# TEST 5: No Redirect Chains
# ====================================================================
echo "TEST 5: No Redirect Chains (Should be exactly 2 HTTP requests)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test with a few generators
for gen in "${TEST_GENERATORS[@]}"; do
    URL="$BASE_URL/ai/$gen/"

    # Use curl -L to follow redirects and save all headers
    HEADERS=$(mktemp)
    curl -s -L "$URL" -D "$HEADERS" > /dev/null 2>&1

    # Count HTTP status lines
    HTTP_COUNT=$(grep -c "^HTTP" "$HEADERS")

    ((TOTAL_TESTS++))

    # Should be exactly 2: one 301, one 200
    if [ "$HTTP_COUNT" = "2" ]; then
        echo -e "${GREEN}✓${NC} $gen: 2 HTTP requests (no chain)"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗${NC} $gen: $HTTP_COUNT HTTP requests (expected 2)"
        ((FAILED_TESTS++))
    fi

    rm -f "$HEADERS"
done

echo ""

# ====================================================================
# RESULTS SUMMARY
# ====================================================================
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    TEST RESULTS SUMMARY                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Total tests:    $TOTAL_TESTS"
echo -e "Passed:         ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:         ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}✗ $FAILED_TESTS TEST(S) FAILED${NC}"
    echo ""
    exit 1
fi
```

---

## Final Checklist

### Before Deployment

- [ ] All baseline metrics captured and documented
- [ ] Unit tests written and passing locally
- [ ] Testing scripts created and verified
- [ ] Django settings reviewed (no breaking changes)
- [ ] URL patterns reviewed (no conflicts)
- [ ] Code committed to git with clear message
- [ ] Heroku staging environment tested
- [ ] Google Search Console prepared
- [ ] Rollback plan documented
- [ ] Team notified of deployment time

### During Deployment

- [ ] Code pushed to production
- [ ] Heroku logs monitored (first 10 minutes)
- [ ] Quick smoke test (curl all 11 URLs)
- [ ] No unusual errors in logs
- [ ] Status page updated (if applicable)

### After Deployment

- [ ] All 11 generators return 301
- [ ] Query parameters preserved
- [ ] New URLs return 200
- [ ] No redirect chains
- [ ] Manual GSC check (Request Indexing)
- [ ] Analytics segments created
- [ ] Daily monitoring begun
- [ ] Team notified of completion

---

**Document prepared for PromptFinder SEO team**
**Last updated:** December 2024
**Next review:** Post-migration (Week 8)

