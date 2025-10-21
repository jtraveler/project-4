# Security Review: UserProfileForm URL Cleaning Methods

## 🚨 Critical Security Issues

### 1. **URL Injection Vulnerability**
The current implementation is vulnerable to URL injection attacks.

**Vulnerable Pattern:**
```python
if not url.startswith('http'):
    if url.startswith('@'):
        url = url[1:]
    url = f'https://twitter.com/{url}'
```

**Attack Vector:**
```python
# User input: "../../../evil.com"
# Result: "https://twitter.com/../../../evil.com"
# After normalization: "https://evil.com"

# User input: "@evil.com/twitter.com/user"
# Result: "https://twitter.com/evil.com/twitter.com/user"
```

### 2. **Domain Validation Bypass**
The domain validation in `_validate_social_url` happens AFTER URL construction and has flaws:

```python
# This check is insufficient:
parsed = urlparse(url)
if parsed.netloc.replace('www.', '') not in [d for d in valid_domains]:
```

**Issues:**
- Subdomains bypass: `evil.twitter.com` would pass
- Case sensitivity: Mixed case might bypass
- Port numbers: `twitter.com:8080` might bypass

### 3. **Regex Pattern Issues**
Current patterns are too permissive:

```python
pattern=r'https?://(www\.)?(twitter\.com|x\.com)/[\w]+/?'
```

**Problems:**
- `[\w]+` only matches word characters, missing valid usernames with dots/dashes
- No anchor (`^` and `$`), so `https://twitter.com/user<script>alert(1)</script>` would match
- No length limits on username portion

## 🔧 Recommended Secure Implementation

```python
import re
from urllib.parse import urlparse, quote
from django.core.validators import ValidationError
from django.utils.html import escape

class UserProfileForm(forms.ModelForm):
    # Username validation patterns
    TWITTER_USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{1,15}$')
    INSTAGRAM_USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_.]{1,30}$')

    # URL validation patterns (with anchors)
    TWITTER_URL_PATTERN = re.compile(
        r'^https?://(www\.)?(twitter\.com|x\.com)/[A-Za-z0-9_]{1,15}/?$',
        re.IGNORECASE
    )
    INSTAGRAM_URL_PATTERN = re.compile(
        r'^https?://(www\.)?instagram\.com/[A-Za-z0-9_.]{1,30}/?$',
        re.IGNORECASE
    )

    def clean_twitter_url(self):
        """Safely clean and validate Twitter/X URL"""
        url = self.cleaned_data.get('twitter_url', '').strip()

        if not url:
            return ''

        # Check if it's a full URL or just username
        if url.startswith(('http://', 'https://')):
            return self._validate_twitter_full_url(url)
        else:
            return self._build_twitter_url_from_username(url)

    def _build_twitter_url_from_username(self, username):
        """Build Twitter URL from username with strict validation"""
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]

        # Reject if contains any URL-like patterns
        if any(char in username for char in ['/', '\\', ':', '.', '?', '#', '&']):
            raise ValidationError(
                'Please enter a valid Twitter username (letters, numbers, and underscores only)'
            )

        # Validate username format
        if not self.TWITTER_USERNAME_PATTERN.match(username):
            raise ValidationError(
                'Twitter usernames can only contain letters, numbers, and underscores (max 15 characters)'
            )

        # Build safe URL
        return f'https://twitter.com/{username}'

    def _validate_twitter_full_url(self, url):
        """Validate a full Twitter URL"""
        # Parse URL
        try:
            parsed = urlparse(url.lower())
        except Exception:
            raise ValidationError('Invalid URL format')

        # Strict domain validation
        allowed_domains = ['twitter.com', 'x.com']
        domain = parsed.netloc.replace('www.', '')

        # Check for port numbers or subdomains
        if ':' in domain or domain.count('.') > 1:
            raise ValidationError('Invalid Twitter URL')

        if domain not in allowed_domains:
            raise ValidationError('URL must be from twitter.com or x.com')

        # Validate full URL pattern
        if not self.TWITTER_URL_PATTERN.match(url):
            raise ValidationError(
                'Please enter a valid Twitter URL (e.g., https://twitter.com/username)'
            )

        # Extract and validate username from path
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 1:
            raise ValidationError('Invalid Twitter profile URL')

        username = path_parts[0]
        if not self.TWITTER_USERNAME_PATTERN.match(username):
            raise ValidationError('Invalid username in Twitter URL')

        # Return normalized URL
        return f'https://twitter.com/{username}'

    def clean_instagram_url(self):
        """Safely clean and validate Instagram URL"""
        url = self.cleaned_data.get('instagram_url', '').strip()

        if not url:
            return ''

        # Check if it's a full URL or just username
        if url.startswith(('http://', 'https://')):
            return self._validate_instagram_full_url(url)
        else:
            return self._build_instagram_url_from_username(url)

    def _build_instagram_url_from_username(self, username):
        """Build Instagram URL from username with strict validation"""
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]

        # Reject if contains any suspicious URL-like patterns
        if any(char in username for char in ['/', '\\', ':', '?', '#', '&']):
            raise ValidationError(
                'Please enter a valid Instagram username (letters, numbers, periods, and underscores only)'
            )

        # Validate username format
        if not self.INSTAGRAM_USERNAME_PATTERN.match(username):
            raise ValidationError(
                'Instagram usernames can only contain letters, numbers, periods, and underscores (max 30 characters)'
            )

        # Additional Instagram rules
        if username.startswith('.') or username.endswith('.'):
            raise ValidationError('Instagram usernames cannot start or end with a period')

        if '..' in username:
            raise ValidationError('Instagram usernames cannot contain consecutive periods')

        # Build safe URL
        return f'https://instagram.com/{username}'

    def _validate_instagram_full_url(self, url):
        """Validate a full Instagram URL"""
        # Parse URL
        try:
            parsed = urlparse(url.lower())
        except Exception:
            raise ValidationError('Invalid URL format')

        # Strict domain validation
        domain = parsed.netloc.replace('www.', '')

        # Check for port numbers or subdomains
        if ':' in domain or domain != 'instagram.com':
            raise ValidationError('Invalid Instagram URL')

        # Validate full URL pattern
        if not self.INSTAGRAM_URL_PATTERN.match(url):
            raise ValidationError(
                'Please enter a valid Instagram URL (e.g., https://instagram.com/username)'
            )

        # Extract and validate username from path
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 1:
            raise ValidationError('Invalid Instagram profile URL')

        username = path_parts[0]
        if not self.INSTAGRAM_USERNAME_PATTERN.match(username):
            raise ValidationError('Invalid username in Instagram URL')

        # Additional Instagram rules
        if username.startswith('.') or username.endswith('.'):
            raise ValidationError('Invalid Instagram username')

        if '..' in username:
            raise ValidationError('Invalid Instagram username')

        # Return normalized URL
        return f'https://instagram.com/{username}'

    def clean_website_url(self):
        """Safely validate website URL"""
        url = self.cleaned_data.get('website_url', '').strip()

        if not url:
            return ''

        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        # Parse and validate
        try:
            parsed = urlparse(url)
        except Exception:
            raise ValidationError('Invalid URL format')

        # Security checks
        if not parsed.scheme in ['http', 'https']:
            raise ValidationError('Only HTTP and HTTPS URLs are allowed')

        if not parsed.netloc:
            raise ValidationError('Invalid URL - missing domain')

        # Check for suspicious patterns
        suspicious_patterns = [
            'javascript:', 'data:', 'vbscript:', 'file:', 'about:',
            '<script', 'onclick', 'onerror', '../', '..\\',
        ]
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                raise ValidationError('Invalid URL')

        # Length check
        if len(url) > 200:
            raise ValidationError('URL cannot exceed 200 characters')

        # Additional validation for common issues
        if parsed.netloc.startswith('.') or parsed.netloc.endswith('.'):
            raise ValidationError('Invalid domain name')

        # Check for localhost/private IPs
        blocked_hosts = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '192.168.', '10.', '172.16.', '172.31.',
            '::1', 'fe80::', 'fc00::', 'fd00::'
        ]
        for blocked in blocked_hosts:
            if blocked in parsed.netloc:
                raise ValidationError('This domain is not allowed')

        return url
```

## 🧪 Edge Cases to Test

### Malicious Inputs
```python
test_cases = [
    # Path traversal attempts
    "../../../evil.com",
    "..\\..\\..\\evil.com",

    # URL injection
    "@evil.com/twitter.com/user",
    "evil.com#@twitter.com/user",
    "evil.com?@twitter.com/user",

    # Protocol injection
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",

    # Subdomain attacks
    "evil.twitter.com/user",
    "twitter.com.evil.com/user",

    # Port injection
    "twitter.com:8080/user",

    # Double protocol
    "http://http://twitter.com/user",

    # Unicode/homograph attacks
    "twitter.com/user\u202e\u0027\u003e\u003cscript\u003ealert(1)\u003c/script\u003e",
    "twıtter.com/user",  # Using Turkish dotless i

    # XSS attempts
    "user<script>alert(1)</script>",
    "user'><script>alert(1)</script>",
    "user\" onclick=\"alert(1)\"",

    # SQL injection attempts
    "user' OR '1'='1",
    "user'; DROP TABLE users--",

    # SSRF attempts
    "http://169.254.169.254/",
    "http://metadata.google.internal/",

    # Long inputs
    "a" * 1000,

    # Special characters
    "user!@#$%^&*()",
    "user with spaces",
    "user/../../admin",

    # Case variations
    "TWITTER.COM/user",
    "TwItTeR.cOm/user",

    # Multiple @ symbols
    "@@@@user",
    "@user@evil.com",
]
```

### Valid Edge Cases
```python
valid_cases = [
    # Different formats
    "@username",
    "username",
    "https://twitter.com/username",
    "http://twitter.com/username",
    "https://x.com/username",
    "twitter.com/username",  # Missing protocol

    # Valid special usernames
    "user_name",  # Twitter allows underscores
    "user.name",  # Instagram allows periods
    "username123",  # Numbers allowed

    # Case variations (should normalize)
    "Twitter.com/UserName",
    "INSTAGRAM.COM/USERNAME",
]
```

## 🛡️ Additional Security Recommendations

### 1. **Content Security Policy (CSP)**
```python
# In your template when displaying these URLs:
from django.utils.html import escape
from urllib.parse import quote

# Always escape when rendering
{{ user.profile.twitter_url|escape }}
```

### 2. **Rate Limiting**
```python
# Add rate limiting to prevent automated testing
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/h', method='POST')
def update_profile(request):
    # Profile update logic
```

### 3. **Logging Suspicious Activity**
```python
import logging

logger = logging.getLogger(__name__)

def clean_twitter_url(self):
    url = self.cleaned_data.get('twitter_url', '').strip()

    # Log suspicious patterns
    suspicious_patterns = ['../', '<script', 'javascript:', 'data:']
    if any(pattern in url.lower() for pattern in suspicious_patterns):
        logger.warning(
            f"Suspicious URL input detected: {url[:100]} from user {self.instance.user.id}"
        )

    # Continue with validation...
```

### 4. **Database Storage**
```python
# Model field definition with additional constraints
class UserProfile(models.Model):
    twitter_url = models.URLField(
        max_length=200,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^https?://(www\.)?(twitter\.com|x\.com)/[A-Za-z0-9_]{1,15}/?$',
                message='Invalid Twitter URL'
            )
        ]
    )
```

### 5. **Template Security**
```html
<!-- Always use 'noopener noreferrer' for external links -->
{% if user.profile.twitter_url %}
    <a href="{{ user.profile.twitter_url|escape }}"
       target="_blank"
       rel="noopener noreferrer">
        Twitter Profile
    </a>
{% endif %}
```

## ✅ Testing Checklist

- [ ] Test all malicious inputs from the list above
- [ ] Verify normalized URLs are consistent
- [ ] Check that validation messages are user-friendly
- [ ] Test with disabled JavaScript
- [ ] Verify URLs are properly escaped in templates
- [ ] Test with different character encodings
- [ ] Verify rate limiting works
- [ ] Check logging of suspicious inputs
- [ ] Test with very long inputs
- [ ] Verify database constraints match form validation

## 📝 Summary

The original implementation has several critical security vulnerabilities:

1. **URL injection** - User input directly concatenated without validation
2. **Domain validation bypass** - Insufficient domain checking
3. **Missing input sanitization** - No protection against XSS
4. **Regex issues** - Patterns without anchors and improper character classes
5. **No protection against SSRF** - Could be used to probe internal networks

The recommended implementation provides:
- Strict username validation before URL construction
- Proper domain validation with no bypass opportunities
- Protection against common web vulnerabilities
- Clear error messages for users
- Consistent URL normalization
- Logging of suspicious activity

Always remember: **Never trust user input**, even when it seems like "just a username".