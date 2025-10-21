"""
Security test cases for URL validation
Run these tests to ensure your implementation is secure
"""
import unittest
from django.core.validators import ValidationError
from your_app.forms import UserProfileForm  # Update with your actual import


class URLSecurityTests(unittest.TestCase):
    """Test suite for URL validation security"""

    def setUp(self):
        self.form_class = UserProfileForm

    def test_path_traversal_attacks(self):
        """Test protection against path traversal"""
        malicious_inputs = [
            "../../../evil.com",
            "..\\..\\..\\evil.com",
            "../../admin",
            "%2e%2e%2f%2e%2e%2fadmin",
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'twitter_url': malicious})
                self.assertFalse(form.is_valid())
                self.assertIn('twitter_url', form.errors)

    def test_url_injection_attacks(self):
        """Test protection against URL injection"""
        malicious_inputs = [
            "@evil.com/twitter.com/user",
            "evil.com#@twitter.com/user",
            "evil.com?@twitter.com/user",
            "evil.com@twitter.com",
            "http://evil.com@twitter.com",
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'twitter_url': malicious})
                self.assertFalse(form.is_valid())

    def test_subdomain_attacks(self):
        """Test that subdomains are rejected"""
        malicious_inputs = [
            "https://evil.twitter.com/user",
            "https://twitter.com.evil.com/user",
            "https://sub.twitter.com/user",
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'twitter_url': malicious})
                self.assertFalse(form.is_valid())

    def test_xss_attempts(self):
        """Test protection against XSS injection"""
        malicious_inputs = [
            "user<script>alert(1)</script>",
            "user'><script>alert(1)</script>",
            'user" onclick="alert(1)"',
            "user</title><script>alert(1)</script>",
            "user\"><img src=x onerror=alert(1)>",
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'twitter_url': malicious})
                self.assertFalse(form.is_valid())

    def test_protocol_injection(self):
        """Test protection against protocol injection"""
        malicious_inputs = [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:alert(1)",
            "file:///etc/passwd",
            "about:blank",
            "blob:https://example.com/uuid",
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'website_url': malicious})
                self.assertFalse(form.is_valid())

    def test_ssrf_prevention(self):
        """Test protection against SSRF attacks"""
        malicious_inputs = [
            "http://localhost/admin",
            "http://127.0.0.1/secret",
            "http://192.168.1.1/router",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://[::1]/admin",  # IPv6 localhost
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'website_url': malicious})
                self.assertFalse(form.is_valid())

    def test_valid_inputs_accepted(self):
        """Test that valid inputs are properly accepted and normalized"""
        valid_cases = [
            # Twitter variations
            ("@username", "https://twitter.com/username"),
            ("username", "https://twitter.com/username"),
            ("https://twitter.com/username", "https://twitter.com/username"),
            ("https://x.com/username", "https://twitter.com/username"),  # x.com normalized

            # Instagram variations
            ("@user.name", "https://instagram.com/user.name"),
            ("user_name", "https://instagram.com/user_name"),
            ("https://instagram.com/user.name", "https://instagram.com/user.name"),
        ]

        for input_val, expected in valid_cases:
            with self.subTest(input=input_val):
                form = self.form_class(data={'twitter_url': input_val})
                if 'instagram' in expected:
                    form = self.form_class(data={'instagram_url': input_val})

                self.assertTrue(form.is_valid(), f"Failed for valid input: {input_val}")

    def test_unicode_homograph_attacks(self):
        """Test protection against Unicode/homograph attacks"""
        malicious_inputs = [
            "twıtter.com/user",  # Turkish dotless i
            "twiᴛᴛer.com/user",  # Small caps T
            "ｔｗｉｔｔｅｒ.com/user",  # Full-width characters
            "tw\u202erettit.com/user",  # Right-to-left override
        ]

        for malicious in malicious_inputs:
            with self.subTest(input=malicious):
                form = self.form_class(data={'twitter_url': f"https://{malicious}"})
                self.assertFalse(form.is_valid())

    def test_length_limits(self):
        """Test that overly long inputs are rejected"""
        long_username = "a" * 1000
        form = self.form_class(data={'twitter_url': long_username})
        self.assertFalse(form.is_valid())

        long_url = "https://example.com/" + "a" * 1000
        form = self.form_class(data={'website_url': long_url})
        self.assertFalse(form.is_valid())

    def test_special_characters_in_username(self):
        """Test that invalid special characters are rejected"""
        invalid_usernames = [
            "user!name",
            "user@name",
            "user#name",
            "user$name",
            "user%name",
            "user^name",
            "user&name",
            "user*name",
            "user(name)",
            "user name",  # Space
            "user/name",
            "user\\name",
            "user:name",
            "user;name",
            "user<name>",
        ]

        for invalid in invalid_usernames:
            with self.subTest(username=invalid):
                form = self.form_class(data={'twitter_url': invalid})
                self.assertFalse(form.is_valid())

    def test_port_numbers_rejected(self):
        """Test that URLs with port numbers are rejected for social media"""
        urls_with_ports = [
            "https://twitter.com:8080/username",
            "https://instagram.com:443/username",
            "http://twitter.com:80/username",
        ]

        for url in urls_with_ports:
            with self.subTest(url=url):
                if 'twitter' in url:
                    form = self.form_class(data={'twitter_url': url})
                else:
                    form = self.form_class(data={'instagram_url': url})
                self.assertFalse(form.is_valid())


def run_security_audit():
    """
    Run a comprehensive security audit of the URL validation
    """
    print("🔒 Running Security Audit...")
    print("-" * 50)

    suite = unittest.TestLoader().loadTestsFromTestCase(URLSecurityTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("-" * 50)
    if result.wasSuccessful():
        print("✅ All security tests passed!")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
        print("Please fix these security issues before deploying!")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the security audit
    run_security_audit()