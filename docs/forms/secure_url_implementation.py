"""
Secure implementation of social media URL validation for UserProfileForm
"""
import re
from urllib.parse import urlparse
from django.core.validators import ValidationError
from django import forms

class SecureUserProfileForm(forms.ModelForm):
    """
    Secure form implementation with proper URL validation
    """

    # Strict username patterns based on platform rules
    TWITTER_USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{1,15}$')
    INSTAGRAM_USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_.]{1,30}$')

    # Full URL patterns with anchors for complete matching
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

        # Determine if input is a full URL or username
        if url.startswith(('http://', 'https://')):
            return self._validate_twitter_full_url(url)
        else:
            return self._build_twitter_url_from_username(url)

    def _build_twitter_url_from_username(self, username):
        """Build Twitter URL from username with strict validation"""
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]

        # Security: Reject any URL-like characters that could cause injection
        suspicious_chars = ['/', '\\', ':', '.', '?', '#', '&', '<', '>', '"', "'"]
        if any(char in username for char in suspicious_chars):
            raise ValidationError(
                'Please enter a valid Twitter username (letters, numbers, and underscores only)'
            )

        # Validate username format according to Twitter rules
        if not self.TWITTER_USERNAME_PATTERN.match(username):
            raise ValidationError(
                'Twitter usernames can only contain letters, numbers, and underscores (max 15 characters)'
            )

        # Build and return safe URL
        return f'https://twitter.com/{username}'

    def _validate_twitter_full_url(self, url):
        """Validate a full Twitter URL with strict security checks"""
        # Parse URL safely
        try:
            parsed = urlparse(url.lower())
        except Exception:
            raise ValidationError('Invalid URL format')

        # Security: Check protocol
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError('Only HTTP and HTTPS URLs are allowed')

        # Security: Strict domain validation (no subdomains, no ports)
        domain = parsed.netloc.replace('www.', '')

        # Check for port numbers
        if ':' in domain:
            raise ValidationError('URLs with port numbers are not allowed')

        # Check for subdomains (more than one dot after removing www)
        if domain.count('.') > 1:
            raise ValidationError('Invalid Twitter URL - subdomains not allowed')

        # Validate domain is exactly twitter.com or x.com
        if domain not in ['twitter.com', 'x.com']:
            raise ValidationError('URL must be from twitter.com or x.com')

        # Validate complete URL pattern
        if not self.TWITTER_URL_PATTERN.match(url):
            raise ValidationError(
                'Please enter a valid Twitter URL (e.g., https://twitter.com/username)'
            )

        # Extract username from path and validate
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 1 or not path_parts[0]:
            raise ValidationError('Invalid Twitter profile URL - must be a direct profile link')

        username = path_parts[0]
        if not self.TWITTER_USERNAME_PATTERN.match(username):
            raise ValidationError('Invalid username in Twitter URL')

        # Return normalized, safe URL
        return f'https://twitter.com/{username}'

    def clean_instagram_url(self):
        """Safely clean and validate Instagram URL"""
        url = self.cleaned_data.get('instagram_url', '').strip()

        if not url:
            return ''

        # Determine if input is a full URL or username
        if url.startswith(('http://', 'https://')):
            return self._validate_instagram_full_url(url)
        else:
            return self._build_instagram_url_from_username(url)

    def _build_instagram_url_from_username(self, username):
        """Build Instagram URL from username with strict validation"""
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]

        # Security: Reject any URL-like characters except period (Instagram allows it)
        suspicious_chars = ['/', '\\', ':', '?', '#', '&', '<', '>', '"', "'"]
        if any(char in username for char in suspicious_chars):
            raise ValidationError(
                'Please enter a valid Instagram username'
            )

        # Validate username format according to Instagram rules
        if not self.INSTAGRAM_USERNAME_PATTERN.match(username):
            raise ValidationError(
                'Instagram usernames can only contain letters, numbers, periods, and underscores (max 30 characters)'
            )

        # Instagram specific rules
        if username.startswith('.') or username.endswith('.'):
            raise ValidationError('Instagram usernames cannot start or end with a period')

        if '..' in username:
            raise ValidationError('Instagram usernames cannot contain consecutive periods')

        # Build and return safe URL
        return f'https://instagram.com/{username}'

    def _validate_instagram_full_url(self, url):
        """Validate a full Instagram URL with strict security checks"""
        # Parse URL safely
        try:
            parsed = urlparse(url.lower())
        except Exception:
            raise ValidationError('Invalid URL format')

        # Security: Check protocol
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError('Only HTTP and HTTPS URLs are allowed')

        # Security: Strict domain validation
        domain = parsed.netloc.replace('www.', '')

        # Check for port numbers
        if ':' in domain:
            raise ValidationError('URLs with port numbers are not allowed')

        # Validate domain is exactly instagram.com
        if domain != 'instagram.com':
            raise ValidationError('URL must be from instagram.com')

        # Validate complete URL pattern
        if not self.INSTAGRAM_URL_PATTERN.match(url):
            raise ValidationError(
                'Please enter a valid Instagram URL (e.g., https://instagram.com/username)'
            )

        # Extract username from path and validate
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 1 or not path_parts[0]:
            raise ValidationError('Invalid Instagram profile URL - must be a direct profile link')

        username = path_parts[0]
        if not self.INSTAGRAM_USERNAME_PATTERN.match(username):
            raise ValidationError('Invalid username in Instagram URL')

        # Instagram specific validation
        if username.startswith('.') or username.endswith('.'):
            raise ValidationError('Invalid Instagram username')

        if '..' in username:
            raise ValidationError('Invalid Instagram username')

        # Return normalized, safe URL
        return f'https://instagram.com/{username}'

    def clean_website_url(self):
        """Safely validate website URL with security checks"""
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

        # Security: Protocol validation
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError('Only HTTP and HTTPS URLs are allowed')

        if not parsed.netloc:
            raise ValidationError('Invalid URL - missing domain')

        # Security: Check for injection attempts
        suspicious_patterns = [
            'javascript:', 'data:', 'vbscript:', 'file:', 'about:', 'blob:',
            '<script', '</script>', 'onclick', 'onerror', 'onload',
            '../', '..\\', '%2e%2e', '%252e%252e',  # Path traversal
            '\x00', '\r', '\n',  # Null bytes and newlines
        ]

        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                raise ValidationError('Invalid URL - contains suspicious content')

        # Security: Block local/private addresses
        blocked_patterns = [
            'localhost', '127.0.0.1', '0.0.0.0',
            '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.',
            '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.',
            '::1', 'fe80:', 'fc00:', 'fd00:', 'ff00:',
            '169.254.',  # Link-local
            'metadata.google.internal',  # Cloud metadata endpoints
            'metadata.azure.com',
            '169.254.169.254',  # AWS metadata
        ]

        netloc_lower = parsed.netloc.lower()
        for blocked in blocked_patterns:
            if blocked in netloc_lower:
                raise ValidationError('This domain is not allowed')

        # Length validation
        if len(url) > 200:
            raise ValidationError('URL cannot exceed 200 characters')

        # Check for valid domain structure
        if '..' in parsed.netloc or parsed.netloc.startswith('.') or parsed.netloc.endswith('.'):
            raise ValidationError('Invalid domain name')

        # Additional validation for common typos/issues
        if parsed.netloc.count(':') > 1:  # IPv6 would have more, but we blocked those
            raise ValidationError('Invalid URL format')

        return url


# Example usage with proper error handling
def example_usage():
    """
    Example of how to use the secure form with proper error handling
    """
    form_data = {
        'twitter_url': '@username',  # Will be converted to https://twitter.com/username
        'instagram_url': 'my.username',  # Will be converted to https://instagram.com/my.username
        'website_url': 'example.com',  # Will be converted to https://example.com
    }

    form = SecureUserProfileForm(data=form_data)

    if form.is_valid():
        # Safe to use the cleaned URLs
        twitter = form.cleaned_data.get('twitter_url')
        instagram = form.cleaned_data.get('instagram_url')
        website = form.cleaned_data.get('website_url')

        print(f"Twitter: {twitter}")
        print(f"Instagram: {instagram}")
        print(f"Website: {website}")
    else:
        # Handle validation errors
        for field, errors in form.errors.items():
            print(f"{field}: {', '.join(errors)}")


# Template usage example (Django template)
"""
<!-- Always escape URLs in templates and use security attributes -->
{% load static %}

{% if user.profile.twitter_url %}
    <a href="{{ user.profile.twitter_url|escape }}"
       target="_blank"
       rel="noopener noreferrer nofollow"
       class="social-link">
        <i class="fab fa-twitter"></i> Twitter
    </a>
{% endif %}

{% if user.profile.instagram_url %}
    <a href="{{ user.profile.instagram_url|escape }}"
       target="_blank"
       rel="noopener noreferrer nofollow"
       class="social-link">
        <i class="fab fa-instagram"></i> Instagram
    </a>
{% endif %}

{% if user.profile.website_url %}
    <a href="{{ user.profile.website_url|escape }}"
       target="_blank"
       rel="noopener noreferrer nofollow"
       class="social-link">
        <i class="fas fa-globe"></i> Website
    </a>
{% endif %}
"""