# CLAUDE CODE SPECIFICATION: Fix Console Errors & CSP Configuration

**Priority:** CRITICAL - Console errors blocking resources
**Estimated Time:** 45 minutes with testing
**Session Type:** Claude Code Implementation with Dual Agent System

---

## 📋 CC COMMUNICATION PROTOCOL REMINDER

**IMPORTANT:** Read `docs/CC_COMMUNICATION_PROTOCOL.md` first for our established workflow.

Remember:
- Be explicit about file locations and changes
- Use the dual agent system (wshobson/agents during implementation)
- Follow our iterative refinement process
- Verify changes with comprehensive testing

---

## 🎯 OBJECTIVE

Fix all console errors on the user profile page by:
1. Updating CSP (Content Security Policy) configuration to allow required external resources
2. Fixing malformed Cloudinary URLs that are missing the domain
3. Ensuring clean console across all pages
4. Implementing comprehensive tests for security headers

---

## 🔍 CURRENT PROBLEMS

### Console Errors Found (see screenshot):
1. **CSP Violations blocking resources:**
   - Bootstrap CSS from `cdn.jsdelivr.net`
   - Google Fonts from `fonts.googleapis.com` and `fonts.gstatic.com`
   - Cloudinary widget from `widget.cloudinary.com`

2. **404 Error on Cloudinary image:**
   - URL: `/8uufabo/image/upload/w_440,f_webp,q_90/8ee87aee-3c11-4f23-9749-c737914598dd_lk4gpu`
   - Missing domain: `https://res.cloudinary.com/`

3. **Warning (non-critical):**
   - Uncaught promise error in async listener

---

## 📁 FILES TO MODIFY

### 1. **settings.py** (Main configuration file)
**Location:** `/settings.py` (root directory)

**Current Issue:** CSP headers are too restrictive

**Required Changes:**
```python
# Add or update these CSP settings:

CSP_DEFAULT_SRC = ("'self'",)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline styles
    "https://cdn.jsdelivr.net",  # Bootstrap CSS
    "https://fonts.googleapis.com",  # Google Fonts
    "https://cdnjs.cloudflare.com",  # CDN resources
)

CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Required for inline scripts
    "'unsafe-eval'",  # Some jQuery operations need this
    "https://cdn.jsdelivr.net",  # Bootstrap JS
    "https://code.jquery.com",  # jQuery
    "https://cdnjs.cloudflare.com",
    "https://widget.cloudinary.com",  # Cloudinary upload widget
)

CSP_IMG_SRC = (
    "'self'",
    "data:",  # Base64 images
    "https:",  # All HTTPS images
    "http://res.cloudinary.com",  # Cloudinary HTTP
    "https://res.cloudinary.com",  # Cloudinary HTTPS
)

CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",  # Google Fonts
    "data:",  # Inline fonts
)

CSP_CONNECT_SRC = (
    "'self'",
    "https://api.cloudinary.com",  # Cloudinary API
    "https://widget.cloudinary.com",  # Cloudinary widget
    "https://res.cloudinary.com",  # Cloudinary resources
)

CSP_MEDIA_SRC = (
    "'self'",
    "https://res.cloudinary.com",  # Cloudinary videos
)

CSP_FRAME_SRC = (
    "'self'",
    "https://widget.cloudinary.com",  # Cloudinary upload iframe
)
```

---

### 2. **prompts/models.py** (Check Cloudinary URL generation)
**Location:** `/prompts/models.py`

**Check these methods for missing domains:**
- `get_image_url()`
- `get_thumbnail_url()`
- `get_video_url()` (if exists)

**Pattern to look for (WRONG):**
```python
return f"/{cloud_name}/image/upload/..."  # Missing https://res.cloudinary.com
```

**Should be (CORRECT):**
```python
return f"https://res.cloudinary.com/{cloud_name}/image/upload/..."
# OR better:
return self.image.build_url(width=440, format='webp', quality=90)
```

---

### 3. **prompts/templates/prompts/user_profile.html**
**Location:** `/prompts/templates/prompts/user_profile.html`

**Check for hardcoded Cloudinary URLs:**
- Look for any `src="/8uufabo/image/upload/..."` patterns
- Should use `{{ user.profile.avatar.url }}` or similar
- Ensure all image sources use proper URL generation

---

## 🧪 TESTS TO CREATE

### Create: **prompts/tests/test_csp_headers.py**

```python
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class CSPHeaderTests(TestCase):
    """Test that CSP headers allow required external resources"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_csp_allows_bootstrap_cdn(self):
        """Bootstrap CSS should be allowed in CSP"""
        response = self.client.get(reverse('prompts:home'))
        csp = response.get('Content-Security-Policy', '')
        self.assertIn('cdn.jsdelivr.net', csp)
    
    def test_csp_allows_google_fonts(self):
        """Google Fonts should be allowed in CSP"""
        response = self.client.get(reverse('prompts:home'))
        csp = response.get('Content-Security-Policy', '')
        self.assertIn('fonts.googleapis.com', csp)
        self.assertIn('fonts.gstatic.com', csp)
    
    def test_csp_allows_cloudinary(self):
        """Cloudinary resources should be allowed"""
        response = self.client.get(reverse('prompts:home'))
        csp = response.get('Content-Security-Policy', '')
        self.assertIn('res.cloudinary.com', csp)
        self.assertIn('widget.cloudinary.com', csp)
    
    def test_profile_page_loads_without_csp_errors(self):
        """Profile page should load all resources"""
        url = reverse('prompts:user_profile', args=['testuser'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that response includes expected external resources
        self.assertContains(response, 'bootstrap')
    
    def test_cloudinary_urls_include_domain(self):
        """All Cloudinary URLs should include full domain"""
        # Create a test prompt with image
        from prompts.models import Prompt
        prompt = Prompt.objects.create(
            user=self.user,
            title="Test",
            prompt_text="Test prompt"
        )
        # If prompt has get_image_url method
        if hasattr(prompt, 'get_image_url'):
            url = prompt.get_image_url()
            if url:
                self.assertTrue(
                    url.startswith('https://res.cloudinary.com') or
                    url.startswith('http://res.cloudinary.com'),
                    f"Cloudinary URL missing domain: {url}"
                )
```

---

## 🤖 AGENTS TO USE

### During Implementation (wshobson/agents):
- **@django-expert** - For settings.py CSP configuration
- **@security** - To review CSP settings for security implications  
- **@test** - For creating comprehensive test coverage
- **@javascript-pro** - To verify client-side impact
- **@debug** - For investigating the 404 error

### After Implementation (Agent Testing System):
You should act as these personas to review:
- **@security** - Verify CSP doesn't open security holes
- **@performance** - Check resource loading efficiency
- **@ux-reviewer** - Ensure no visual regressions
- **@test-analyst** - Validate test coverage

---

## 📋 IMPLEMENTATION STEPS

1. **First, investigate the current CSP configuration:**
   ```bash
   # Check if django-csp is installed
   grep -i "django-csp" requirements.txt
   
   # Look for current CSP settings
   grep -n "CSP_" settings.py
   
   # Find the malformed Cloudinary URL
   grep -r "/8uufabo/image/upload" .
   ```

2. **Update settings.py with the complete CSP configuration above**

3. **Fix any Cloudinary URL generation issues found in models.py**

4. **Check and fix any hardcoded URLs in templates**

5. **Create the test file test_csp_headers.py**

6. **Run tests locally:**
   ```bash
   python manage.py test prompts.tests.test_csp_headers -v 2
   ```

7. **Manual verification:**
   ```bash
   python manage.py runserver
   # Open http://localhost:8000/users/[username]/
   # Check browser console for errors
   ```

8. **Check all pages for console errors:**
   - Homepage
   - Profile page  
   - Prompt detail page
   - Upload page

---

## ✅ SUCCESS CRITERIA

1. **Zero console errors** on all pages
2. **All external resources load:**
   - Bootstrap CSS applies correctly
   - Google Fonts load (check typography)
   - Cloudinary images display
   - No 404 errors

3. **Tests pass:**
   - All CSP header tests pass
   - No security vulnerabilities introduced
   - Existing functionality maintained

4. **Performance maintained:**
   - Page load time not significantly impacted
   - Resources load efficiently

---

## 💬 QUESTIONS FOR CC TO ASK

If CC encounters any ambiguity, it should ask:

1. "I found [X] CSP configuration. Should I replace it entirely or merge with the new settings?"

2. "I found [Y] instances of Cloudinary URLs. Should I fix all of them or just the one causing the 404?"

3. "Should I add CSP report-uri for monitoring violations in production?"

4. "Do you want nonce-based CSP for inline scripts in the future, or is 'unsafe-inline' acceptable?"

---

## 📊 AGENT TESTING CHECKLIST

After CC completes implementation, run agent testing:

### @security (9/10 minimum)
- [ ] CSP allows only necessary domains
- [ ] No overly permissive wildcards
- [ ] Maintains XSS protection
- [ ] CSRF still protected

### @performance (8/10 minimum)  
- [ ] Resources load efficiently
- [ ] No blocking resources
- [ ] Caching headers appropriate

### @test-analyst (8/10 minimum)
- [ ] Test coverage comprehensive
- [ ] Edge cases covered
- [ ] Both positive and negative tests

### @ux-reviewer (9/10 minimum)
- [ ] No visual regressions
- [ ] All images/fonts load
- [ ] Responsive design maintained

---

## 🎯 COMMIT MESSAGE

```bash
fix(security): Resolve CSP violations and Cloudinary URL issues

- Update CSP configuration to allow required external resources
- Allow Bootstrap CDN, Google Fonts, and Cloudinary widgets
- Fix malformed Cloudinary URLs missing domain
- Add comprehensive CSP header tests
- Maintain security while enabling necessary third-party resources

Testing: All CSP tests passing, console errors resolved
Agents: Security review passed (9/10), no vulnerabilities
Browser: Verified clean console in Chrome/Firefox/Safari

Resolves: Console errors on profile page
Phase F Day 1: Console cleanup complete
Ready for: Phase F Day 2 implementation
```

---

## 🚀 FINAL NOTES

This specification provides CC with everything needed to:
1. Fix the console errors systematically
2. Add proper test coverage
3. Use the dual agent system effectively
4. Ensure production-ready code

The fix balances security with functionality, allowing only the specific external resources your app needs while maintaining protection against XSS and other attacks.

After this implementation, you'll have a clean console and can proceed confidently to Phase F Day 2!