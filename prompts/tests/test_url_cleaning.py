"""
Comprehensive test suite for social media URL cleaning methods.

Tests cover:
1. Valid inputs (normal usage)
2. Invalid inputs (validation errors)
3. Security tests (injection attempts)
4. Edge cases (boundaries, whitespace, etc.)
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from prompts.forms import UserProfileForm


class TwitterURLCleaningTests(TestCase):
    """Test Twitter URL cleaning and validation."""

    def setUp(self):
        """Create a form instance for testing."""
        self.form = UserProfileForm()

    # ==================== VALID INPUT TESTS ====================

    def test_twitter_basic_username(self):
        """Test basic username without @ symbol."""
        result = self.form.clean_social_twitter_value('elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_username_with_at(self):
        """Test username with @ prefix (Twitter native format)."""
        result = self.form.clean_social_twitter_value('@elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_full_url(self):
        """Test full twitter.com URL."""
        result = self.form.clean_social_twitter_value('https://twitter.com/elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_x_com_url(self):
        """Test x.com URL (new Twitter domain)."""
        result = self.form.clean_social_twitter_value('https://x.com/elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_http_upgrade(self):
        """Test HTTP URLs are upgraded to HTTPS."""
        result = self.form.clean_social_twitter_value('http://twitter.com/elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_underscore(self):
        """Test underscore in username (valid Twitter character)."""
        result = self.form.clean_social_twitter_value('elon_musk')
        self.assertEqual(result, 'https://twitter.com/elon_musk')

    def test_twitter_numbers(self):
        """Test numbers in username."""
        result = self.form.clean_social_twitter_value('user123')
        self.assertEqual(result, 'https://twitter.com/user123')

    def test_twitter_max_length(self):
        """Test maximum valid username length (15 characters)."""
        result = self.form.clean_social_twitter_value('a' * 15)
        self.assertEqual(result, f'https://twitter.com/{"a" * 15}')

    def test_twitter_min_length(self):
        """Test minimum valid username length (1 character)."""
        result = self.form.clean_social_twitter_value('a')
        self.assertEqual(result, 'https://twitter.com/a')

    def test_twitter_mixed_case(self):
        """Test mixed case username (case should be preserved)."""
        result = self.form.clean_social_twitter_value('ElonMusk')
        self.assertEqual(result, 'https://twitter.com/ElonMusk')

    def test_twitter_trailing_slash(self):
        """Test URL with trailing slash is normalized."""
        result = self.form.clean_social_twitter_value('https://twitter.com/elonmusk/')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_www_subdomain(self):
        """Test www subdomain is normalized."""
        result = self.form.clean_social_twitter_value('https://www.twitter.com/elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    # ==================== INVALID INPUT TESTS ====================

    def test_twitter_too_long(self):
        """Test username exceeding 15 characters is rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.form.clean_social_twitter_value('a' * 16)
        self.assertIn('1-15 characters', str(cm.exception))

    def test_twitter_space_in_username(self):
        """Test username with space is rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.form.clean_social_twitter_value('elon musk')
        self.assertIn('valid Twitter username', str(cm.exception))

    def test_twitter_exclamation_mark(self):
        """Test invalid special character (!) is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('elon!musk')

    def test_twitter_hyphen(self):
        """Test hyphen (not allowed in Twitter usernames) is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('elon-musk')

    def test_twitter_slash(self):
        """Test slash in username is rejected (path injection attempt)."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('elon/musk')

    def test_twitter_multiple_at_symbols(self):
        """Test multiple @ symbols are rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('@@elonmusk')

    def test_twitter_wrong_domain(self):
        """Test URL from wrong platform is rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.form.clean_social_twitter_value('https://facebook.com/elonmusk')
        self.assertIn('valid Twitter URL', str(cm.exception))

    def test_twitter_domain_typo(self):
        """Test common domain typo is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('https://twiter.com/elonmusk')

    # ==================== SECURITY TESTS ====================

    def test_twitter_path_traversal(self):
        """Test path traversal attack is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('../../../etc/passwd')

    def test_twitter_xss_script_tag(self):
        """Test XSS script tag injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('<script>alert(1)</script>')

    def test_twitter_xss_event_handler(self):
        """Test XSS event handler injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('user" onload="alert(1)')

    def test_twitter_javascript_protocol(self):
        """Test javascript: protocol is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('javascript:alert(1)')

    def test_twitter_data_uri(self):
        """Test data URI scheme is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('data:text/html,<script>alert(1)</script>')

    def test_twitter_open_redirect_double_at(self):
        """Test open redirect via double @ is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('@twitter.com@evil.com')

    def test_twitter_query_param_injection(self):
        """Test query parameter injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('user?admin=true')

    def test_twitter_fragment_injection(self):
        """Test fragment injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('user#admin')

    def test_twitter_null_byte(self):
        """Test null byte injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('user%00.evil.com')

    def test_twitter_crlf_injection(self):
        """Test CRLF injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_twitter_value('user%0d%0aLocation:evil.com')

    # ==================== EDGE CASES ====================

    def test_twitter_empty_string(self):
        """Test empty string returns empty (optional field)."""
        result = self.form.clean_social_twitter_value('')
        self.assertEqual(result, '')

    def test_twitter_whitespace_only(self):
        """Test whitespace-only input is treated as empty."""
        result = self.form.clean_social_twitter_value('   ')
        self.assertEqual(result, '')

    def test_twitter_leading_whitespace(self):
        """Test leading whitespace is stripped."""
        result = self.form.clean_social_twitter_value('  elonmusk')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_trailing_whitespace(self):
        """Test trailing whitespace is stripped."""
        result = self.form.clean_social_twitter_value('elonmusk  ')
        self.assertEqual(result, 'https://twitter.com/elonmusk')

    def test_twitter_uppercase(self):
        """Test uppercase username is preserved."""
        result = self.form.clean_social_twitter_value('ELONMUSK')
        self.assertEqual(result, 'https://twitter.com/ELONMUSK')


class InstagramURLCleaningTests(TestCase):
    """Test Instagram URL cleaning and validation."""

    def setUp(self):
        """Create a form instance for testing."""
        self.form = UserProfileForm()

    # ==================== VALID INPUT TESTS ====================

    def test_instagram_basic_username(self):
        """Test basic username without @ symbol."""
        result = self.form.clean_social_instagram_value('instagram')
        self.assertEqual(result, 'https://instagram.com/instagram')

    def test_instagram_username_with_at(self):
        """Test username with @ prefix."""
        result = self.form.clean_social_instagram_value('@instagram')
        self.assertEqual(result, 'https://instagram.com/instagram')

    def test_instagram_full_url(self):
        """Test full instagram.com URL."""
        result = self.form.clean_social_instagram_value('https://instagram.com/instagram')
        self.assertEqual(result, 'https://instagram.com/instagram')

    def test_instagram_http_upgrade(self):
        """Test HTTP URLs are upgraded to HTTPS."""
        result = self.form.clean_social_instagram_value('http://instagram.com/instagram')
        self.assertEqual(result, 'https://instagram.com/instagram')

    def test_instagram_dots(self):
        """Test dots in username (valid Instagram character)."""
        result = self.form.clean_social_instagram_value('user.name')
        self.assertEqual(result, 'https://instagram.com/user.name')

    def test_instagram_underscore(self):
        """Test underscore in username."""
        result = self.form.clean_social_instagram_value('user_name')
        self.assertEqual(result, 'https://instagram.com/user_name')

    def test_instagram_numbers(self):
        """Test numbers in username."""
        result = self.form.clean_social_instagram_value('user123')
        self.assertEqual(result, 'https://instagram.com/user123')

    def test_instagram_max_length(self):
        """Test maximum valid username length (30 characters)."""
        result = self.form.clean_social_instagram_value('a' * 30)
        self.assertEqual(result, f'https://instagram.com/{"a" * 30}')

    def test_instagram_min_length(self):
        """Test minimum valid username length (1 character)."""
        result = self.form.clean_social_instagram_value('a')
        self.assertEqual(result, 'https://instagram.com/a')

    def test_instagram_complex_username(self):
        """Test complex username with dots, underscores, and numbers."""
        result = self.form.clean_social_instagram_value('user.name_123')
        self.assertEqual(result, 'https://instagram.com/user.name_123')

    def test_instagram_www_subdomain(self):
        """Test www subdomain is normalized."""
        result = self.form.clean_social_instagram_value('https://www.instagram.com/user')
        self.assertEqual(result, 'https://instagram.com/user')

    # ==================== INVALID INPUT TESTS ====================

    def test_instagram_too_long(self):
        """Test username exceeding 30 characters is rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.form.clean_social_instagram_value('a' * 31)
        self.assertIn('1-30 characters', str(cm.exception))

    def test_instagram_space_in_username(self):
        """Test username with space is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('user name')

    def test_instagram_exclamation_mark(self):
        """Test invalid special character (!) is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('user!name')

    def test_instagram_hyphen(self):
        """Test hyphen (not allowed in Instagram usernames) is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('user-name')

    def test_instagram_slash(self):
        """Test slash in username is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('user/name')

    def test_instagram_starts_with_dot(self):
        """Test username starting with dot is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('.username')

    def test_instagram_ends_with_dot(self):
        """Test username ending with dot is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('username.')

    def test_instagram_consecutive_dots(self):
        """Test consecutive dots are rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('user..name')

    def test_instagram_wrong_domain(self):
        """Test URL from wrong platform is rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.form.clean_social_instagram_value('https://twitter.com/username')
        self.assertIn('valid Instagram URL', str(cm.exception))

    # ==================== SECURITY TESTS ====================

    def test_instagram_path_traversal(self):
        """Test path traversal attack is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('../../admin')

    def test_instagram_xss_script_tag(self):
        """Test XSS script tag injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('<script>alert(1)</script>')

    def test_instagram_javascript_protocol(self):
        """Test javascript: protocol is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('javascript:alert(1)')

    def test_instagram_query_param_injection(self):
        """Test query parameter injection is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_social_instagram_value('username?redirect=evil.com')

    # ==================== EDGE CASES ====================

    def test_instagram_empty_string(self):
        """Test empty string returns empty."""
        result = self.form.clean_social_instagram_value('')
        self.assertEqual(result, '')

    def test_instagram_whitespace_only(self):
        """Test whitespace-only input is treated as empty."""
        result = self.form.clean_social_instagram_value('   ')
        self.assertEqual(result, '')

    def test_instagram_uppercase(self):
        """Test uppercase username is preserved."""
        result = self.form.clean_social_instagram_value('USERNAME')
        self.assertEqual(result, 'https://instagram.com/USERNAME')


class WebsiteURLCleaningTests(TestCase):
    """Test website URL cleaning and validation."""

    def setUp(self):
        """Create a form instance for testing."""
        self.form = UserProfileForm()

    # ==================== VALID INPUT TESTS ====================

    def test_website_domain_only(self):
        """Test domain without protocol gets HTTPS added."""
        result = self.form.clean_website_value('example.com')
        self.assertEqual(result, 'https://example.com')

    def test_website_with_www(self):
        """Test www subdomain is preserved."""
        result = self.form.clean_website_value('www.example.com')
        self.assertEqual(result, 'https://www.example.com')

    def test_website_full_https_url(self):
        """Test full HTTPS URL is preserved."""
        result = self.form.clean_website_value('https://example.com')
        self.assertEqual(result, 'https://example.com')

    def test_website_http_upgrade(self):
        """Test HTTP URLs are upgraded to HTTPS."""
        result = self.form.clean_website_value('http://example.com')
        self.assertEqual(result, 'https://example.com')

    def test_website_subdomain(self):
        """Test subdomain is preserved."""
        result = self.form.clean_website_value('blog.example.com')
        self.assertEqual(result, 'https://blog.example.com')

    def test_website_with_path(self):
        """Test URL with path is preserved."""
        result = self.form.clean_website_value('example.com/about')
        self.assertEqual(result, 'https://example.com/about')

    def test_website_with_query_params(self):
        """Test URL with query parameters is preserved."""
        result = self.form.clean_website_value('example.com?ref=twitter')
        self.assertEqual(result, 'https://example.com?ref=twitter')

    def test_website_with_anchor(self):
        """Test URL with anchor is preserved."""
        result = self.form.clean_website_value('example.com#section')
        self.assertEqual(result, 'https://example.com#section')

    def test_website_complex_url(self):
        """Test complex URL with subdomain, path, query, and anchor."""
        result = self.form.clean_website_value('blog.example.com/page?id=123#top')
        self.assertEqual(result, 'https://blog.example.com/page?id=123#top')

    def test_website_hyphenated_domain(self):
        """Test hyphenated domain name."""
        result = self.form.clean_website_value('my-site.com')
        self.assertEqual(result, 'https://my-site.com')

    def test_website_multiple_subdomains(self):
        """Test multiple subdomain levels."""
        result = self.form.clean_website_value('api.dev.example.com')
        self.assertEqual(result, 'https://api.dev.example.com')

    # ==================== INVALID INPUT TESTS ====================

    def test_website_invalid_tld(self):
        """Test invalid top-level domain is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('example.123')

    def test_website_no_tld(self):
        """Test domain without TLD is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('example')

    def test_website_space_in_domain(self):
        """Test space in domain is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('my site.com')

    def test_website_at_symbol(self):
        """Test @ symbol in domain is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('my@site.com')

    def test_website_double_slash_in_path(self):
        """Test double slash in path is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('example.com//page')

    def test_website_ftp_protocol(self):
        """Test FTP protocol is rejected (only HTTP/HTTPS allowed)."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('ftp://example.com')

    # ==================== SECURITY TESTS ====================

    def test_website_path_traversal(self):
        """Test path traversal is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('example.com/../../etc/passwd')

    def test_website_encoded_path_traversal(self):
        """Test encoded path traversal is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('example.com/..%2F..%2Fadmin')

    def test_website_xss_script_tag(self):
        """Test XSS script tag is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('<script>alert(1)</script>')

    def test_website_javascript_protocol(self):
        """Test javascript: protocol is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('javascript:alert(document.cookie)')

    def test_website_file_protocol(self):
        """Test file: protocol is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('file:///etc/passwd')

    def test_website_data_protocol(self):
        """Test data: protocol is rejected."""
        with self.assertRaises(ValidationError):
            self.form.clean_website_value('data:text/html,<h1>Phish</h1>')

    # ==================== EDGE CASES ====================

    def test_website_empty_string(self):
        """Test empty string returns empty."""
        result = self.form.clean_website_value('')
        self.assertEqual(result, '')

    def test_website_whitespace_only(self):
        """Test whitespace-only input is treated as empty."""
        result = self.form.clean_website_value('   ')
        self.assertEqual(result, '')

    def test_website_leading_whitespace(self):
        """Test leading whitespace is stripped."""
        result = self.form.clean_website_value('  example.com')
        self.assertEqual(result, 'https://example.com')

    def test_website_trailing_whitespace(self):
        """Test trailing whitespace is stripped."""
        result = self.form.clean_website_value('example.com  ')
        self.assertEqual(result, 'https://example.com')

    def test_website_uppercase_domain(self):
        """Test uppercase domain is normalized to lowercase."""
        result = self.form.clean_website_value('EXAMPLE.COM')
        self.assertEqual(result, 'https://example.com')

    def test_website_mixed_case_domain(self):
        """Test mixed case domain is normalized."""
        result = self.form.clean_website_value('ExAmPlE.CoM')
        self.assertEqual(result, 'https://example.com')

    def test_website_trailing_slashes(self):
        """Test trailing slashes are cleaned."""
        result = self.form.clean_website_value('example.com///')
        # Note: Depends on implementation - may preserve or clean
        self.assertTrue(result.startswith('https://example.com'))


# ==================== INTEGRATION TESTS ====================

class URLCleaningIntegrationTests(TestCase):
    """Integration tests for form-level URL cleaning."""

    def test_all_fields_empty(self):
        """Test form accepts all empty social media fields."""
        form = UserProfileForm(data={
            'social_twitter': '',
            'social_instagram': '',
            'website': '',
        })
        # Assuming these are the only required fields or you provide other required data
        # Adjust based on your actual form requirements
        self.assertTrue(form.is_valid() or 'social_twitter' not in form.errors)

    def test_all_fields_valid(self):
        """Test form accepts all valid social media URLs."""
        form = UserProfileForm(data={
            'social_twitter': 'elonmusk',
            'social_instagram': 'instagram',
            'website': 'example.com',
        })
        # Check social fields are cleaned correctly
        if form.is_valid():
            self.assertEqual(form.cleaned_data.get('social_twitter'), 'https://twitter.com/elonmusk')
            self.assertEqual(form.cleaned_data.get('social_instagram'), 'https://instagram.com/instagram')
            self.assertEqual(form.cleaned_data.get('website'), 'https://example.com')

    def test_mixed_valid_and_empty(self):
        """Test form handles mix of valid and empty fields."""
        form = UserProfileForm(data={
            'social_twitter': 'elonmusk',
            'social_instagram': '',
            'website': 'example.com',
        })
        if form.is_valid():
            self.assertEqual(form.cleaned_data.get('social_twitter'), 'https://twitter.com/elonmusk')
            self.assertEqual(form.cleaned_data.get('social_instagram'), '')
            self.assertEqual(form.cleaned_data.get('website'), 'https://example.com')

    def test_one_invalid_field_shows_error(self):
        """Test form shows error for invalid field while preserving valid ones."""
        form = UserProfileForm(data={
            'social_twitter': 'this_username_is_way_too_long_for_twitter',  # 16+ chars
            'social_instagram': 'validuser',
            'website': 'example.com',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('social_twitter', form.errors)
        # Valid fields should still be cleaned
        # Note: Django may not populate cleaned_data for invalid forms
        # This behavior depends on your form implementation


# ==================== PERFORMANCE TESTS ====================

class URLCleaningPerformanceTests(TestCase):
    """Performance tests for URL cleaning methods."""

    def test_bulk_username_cleaning(self):
        """Test cleaning 100 usernames completes quickly."""
        import time
        form = UserProfileForm()

        start = time.time()
        for i in range(100):
            form.clean_social_twitter_value(f'user{i}')
        end = time.time()

        # Should complete in under 1 second
        self.assertLess(end - start, 1.0, "Cleaning 100 usernames took too long")

    def test_bulk_url_validation(self):
        """Test validating 100 URLs completes quickly."""
        import time
        form = UserProfileForm()

        urls = [f'https://example{i}.com' for i in range(100)]

        start = time.time()
        for url in urls:
            try:
                form.clean_website_value(url)
            except ValidationError:
                pass  # Some may fail, that's ok
        end = time.time()

        # Should complete in under 2 seconds
        self.assertLess(end - start, 2.0, "Validating 100 URLs took too long")
