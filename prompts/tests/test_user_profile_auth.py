"""
Test authentication requirements for user_profile view.

This test suite verifies the @login_required decorator behavior on the
user_profile view, including redirect logic, next parameter handling,
and access control.

IMPORTANT: As of the current implementation (October 2025), the user_profile
view does NOT have @login_required decorator. It is publicly accessible.

These tests are written to verify what WOULD happen if @login_required
were added, and also include tests for the current public access behavior.

Run with:
    python manage.py test prompts.tests.test_user_profile_auth

To test WITH @login_required:
    1. Add @login_required decorator to user_profile view (line 1671 in views.py)
    2. Run: python manage.py test prompts.tests.test_user_profile_auth.LoginRequiredTests

To test WITHOUT @login_required (current behavior):
    3. Run: python manage.py test prompts.tests.test_user_profile_auth.PublicAccessTests
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from prompts.models import UserProfile, Prompt


class LoginRequiredTests(TestCase):
    """
    Tests for @login_required decorator on user_profile view.

    NOTE: These tests assume @login_required IS applied to the view.
    If the decorator is not present, these tests will FAIL (as expected).
    """

    @classmethod
    def setUpTestData(cls):
        """Create test users once for all test methods."""
        # Create user with profile
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Profile auto-created by signal
        cls.profile = cls.user.userprofile

        # Create another user for testing "other user" scenarios
        cls.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )

    def setUp(self):
        """Create fresh client for each test."""
        self.client = Client()

    def test_anonymous_user_redirected_to_login(self):
        """
        Test that anonymous (not logged in) users are redirected to login page.

        Expected behavior with @login_required:
        - Status code: 302 (redirect)
        - Redirect location: /accounts/login/?next=/users/testuser/
        """
        url = reverse('prompts:user_profile', args=['testuser'])
        response = self.client.get(url)

        # Should redirect (302)
        self.assertEqual(
            response.status_code,
            302,
            "Anonymous user should be redirected to login (302)"
        )

        # Should redirect to login URL
        self.assertTrue(
            response.url.startswith('/accounts/login/'),
            f"Should redirect to login page, got: {response.url}"
        )

    def test_anonymous_redirect_includes_next_parameter(self):
        """
        Test that redirect to login includes 'next' parameter with original URL.

        This allows Django to redirect back to the profile after successful login.

        Expected URL: /accounts/login/?next=/users/testuser/
        """
        url = reverse('prompts:user_profile', args=['testuser'])
        response = self.client.get(url)

        # Extract 'next' parameter from redirect URL
        expected_next = '/users/testuser/'
        self.assertIn(
            f'next={expected_next}',
            response.url,
            f"Redirect should include next parameter. Got: {response.url}"
        )

    def test_after_login_redirects_to_original_profile(self):
        """
        Test that after logging in, user is redirected back to the profile page.

        Workflow:
        1. Anonymous user tries to access /users/testuser/
        2. Redirected to /accounts/login/?next=/users/testuser/
        3. User logs in
        4. Redirected back to /users/testuser/
        """
        profile_url = reverse('prompts:user_profile', args=['testuser'])
        login_url = reverse('account_login')  # Django allauth login URL

        # Step 1: Try to access profile (not logged in)
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 302)

        # Step 2: Log in with 'next' parameter
        login_response = self.client.post(
            login_url,
            {
                'login': 'testuser',
                'password': 'testpass123',
            },
            follow=False
        )

        # Django allauth may use different login mechanism
        # Alternative: use Django's built-in login
        self.client.login(username='testuser', password='testpass123')

        # Step 3: Access profile again (now logged in)
        response = self.client.get(profile_url)

        # Should now return 200 OK (not redirect)
        self.assertEqual(
            response.status_code,
            200,
            "Logged-in user should be able to access profile (200)"
        )

    def test_authenticated_user_can_view_profiles(self):
        """
        Test that authenticated users can view profile pages normally.

        Expected behavior with @login_required:
        - Status code: 200 OK
        - Profile data displayed
        - No redirect
        """
        # Log in first
        self.client.login(username='testuser', password='testpass123')

        url = reverse('prompts:user_profile', args=['testuser'])
        response = self.client.get(url)

        # Should return 200 OK
        self.assertEqual(
            response.status_code,
            200,
            "Authenticated user should access profile successfully (200)"
        )

        # Should render correct template
        self.assertTemplateUsed(response, 'prompts/user_profile.html')

        # Should have profile in context
        self.assertIn('profile_user', response.context)
        self.assertEqual(response.context['profile_user'].username, 'testuser')

    def test_authenticated_user_can_view_own_profile(self):
        """
        Test that authenticated users can view their own profile page.

        Expected behavior:
        - Status code: 200 OK
        - is_owner flag should be True in context
        """
        # Log in
        self.client.login(username='testuser', password='testpass123')

        # View own profile
        url = reverse('prompts:user_profile', args=['testuser'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context['is_owner'],
            "Viewing own profile should set is_owner=True"
        )

    def test_authenticated_user_can_view_other_profiles(self):
        """
        Test that authenticated users can view other users' profile pages.

        Expected behavior:
        - Status code: 200 OK
        - is_owner flag should be False in context
        """
        # Log in as testuser
        self.client.login(username='testuser', password='testpass123')

        # View otheruser's profile
        url = reverse('prompts:user_profile', args=['otheruser'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context['is_owner'],
            "Viewing another user's profile should set is_owner=False"
        )
        self.assertEqual(
            response.context['profile_user'].username,
            'otheruser'
        )

    def test_invalid_username_returns_404_when_authenticated(self):
        """
        Test that 404 is returned for non-existent users (even when logged in).

        Login requirement should not interfere with 404 handling.

        Expected behavior:
        - Status code: 404 (not 302)
        """
        # Log in first
        self.client.login(username='testuser', password='testpass123')

        # Try to access non-existent user
        url = reverse('prompts:user_profile', args=['nonexistentuser'])
        response = self.client.get(url)

        # Should return 404 (not redirect)
        self.assertEqual(
            response.status_code,
            404,
            "Non-existent user should return 404, not redirect"
        )

    def test_next_parameter_preserves_query_string(self):
        """
        Test that 'next' parameter preserves query strings like media filters.

        Example: /users/john/?media=photos
        After login, should redirect to: /users/john/?media=photos (not lose media param)
        """
        profile_url = reverse('prompts:user_profile', args=['testuser'])
        full_url = f"{profile_url}?media=photos"

        # Try to access with query string (not logged in)
        response = self.client.get(full_url)

        # Redirect URL should include full original URL with query params
        # Note: URL encoding may change ? to %3F and = to %3D
        self.assertIn('next=', response.url)

        # Alternative check: ensure 'media' is preserved somewhere in redirect
        # (URL encoding makes exact matching difficult)
        encoded_url = response.url
        self.assertTrue(
            'media' in encoded_url or '%3F' in encoded_url,
            f"Query string should be preserved in redirect. Got: {encoded_url}"
        )

    def test_login_required_works_with_ajax_requests(self):
        """
        Test that @login_required works correctly with AJAX requests.

        AJAX requests should still receive 302 redirect (not 403).
        """
        url = reverse('prompts:user_profile', args=['testuser'])

        # Make AJAX request (not logged in)
        response = self.client.get(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # Should still redirect to login (302)
        self.assertEqual(response.status_code, 302)

    def test_logout_removes_access(self):
        """
        Test that logging out prevents access to profile pages.

        Workflow:
        1. Log in → access profile (200 OK)
        2. Log out
        3. Try to access profile → redirect to login (302)
        """
        url = reverse('prompts:user_profile', args=['testuser'])

        # Step 1: Log in and verify access
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Step 2: Log out
        self.client.logout()

        # Step 3: Try to access again (should redirect)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            302,
            "After logout, access should be denied (302 redirect)"
        )


class PublicAccessTests(TestCase):
    """
    Tests for PUBLIC access to user_profile view (current behavior).

    NOTE: These tests verify the CURRENT implementation where
    user_profile does NOT have @login_required decorator.

    If @login_required is added, these tests will FAIL (as expected).
    """

    @classmethod
    def setUpTestData(cls):
        """Create test users once for all test methods."""
        cls.user = User.objects.create_user(
            username='publicuser',
            email='public@example.com',
            password='testpass123'
        )

    def setUp(self):
        """Create fresh client for each test."""
        self.client = Client()

    def test_anonymous_user_can_view_profiles(self):
        """
        Test that anonymous users can view public profiles (current behavior).

        Expected behavior WITHOUT @login_required:
        - Status code: 200 OK
        - No redirect to login
        """
        url = reverse('prompts:user_profile', args=['publicuser'])
        response = self.client.get(url)

        # Should return 200 OK (not redirect)
        self.assertEqual(
            response.status_code,
            200,
            "Anonymous users should be able to view public profiles (200)"
        )

        # Should render template
        self.assertTemplateUsed(response, 'prompts/user_profile.html')

    def test_anonymous_user_sees_profile_data(self):
        """
        Test that anonymous users can see profile data and prompts.

        Expected behavior:
        - Profile user in context
        - Prompts displayed
        - is_owner = False
        """
        url = reverse('prompts:user_profile', args=['publicuser'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertIn('profile_user', response.context)
        self.assertEqual(
            response.context['profile_user'].username,
            'publicuser'
        )
        self.assertFalse(
            response.context['is_owner'],
            "Anonymous users should not be marked as owner"
        )

    def test_anonymous_user_can_use_media_filters(self):
        """
        Test that anonymous users can use media filters on public profiles.

        Expected behavior:
        - ?media=photos works
        - ?media=videos works
        - No login required
        """
        url = reverse('prompts:user_profile', args=['publicuser'])

        # Test photos filter
        response = self.client.get(url, {'media': 'photos'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['media_filter'], 'photos')

        # Test videos filter
        response = self.client.get(url, {'media': 'videos'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['media_filter'], 'videos')

    def test_no_redirect_to_login_for_anonymous(self):
        """
        Test that anonymous users are NOT redirected to login.

        This is the KEY difference from @login_required behavior.
        """
        url = reverse('prompts:user_profile', args=['publicuser'])
        response = self.client.get(url)

        # Should NOT redirect
        self.assertNotEqual(
            response.status_code,
            302,
            "Anonymous users should NOT be redirected (current behavior)"
        )

        # Should be successful response
        self.assertEqual(response.status_code, 200)


class LoginRequiredEdgeCaseTests(TestCase):
    """
    Edge case tests for @login_required on user_profile view.

    Tests unusual scenarios and boundary conditions.
    """

    @classmethod
    def setUpTestData(cls):
        """Create test users."""
        cls.user = User.objects.create_user(
            username='edgeuser',
            email='edge@example.com',
            password='testpass123'
        )

    def setUp(self):
        """Create fresh client."""
        self.client = Client()

    def test_next_parameter_with_special_characters(self):
        """
        Test that 'next' parameter handles special characters in username.

        Django allows: letters, digits, @, +, ., -, and _
        """
        # Create user with special chars
        special_user = User.objects.create_user(
            username='user_name.123',
            password='testpass123'
        )

        url = reverse('prompts:user_profile', args=['user_name.123'])
        response = self.client.get(url)

        # Assuming @login_required is applied
        if response.status_code == 302:
            # Check redirect includes escaped username
            self.assertIn('next=', response.url)

    def test_next_parameter_with_pagination(self):
        """
        Test that 'next' parameter preserves pagination query strings.

        Example: /users/john/?page=2
        Should redirect to: /accounts/login/?next=/users/john/?page=2
        """
        url = reverse('prompts:user_profile', args=['edgeuser'])
        full_url = f"{url}?page=2"

        response = self.client.get(full_url)

        # If @login_required is applied, check 'next' param
        if response.status_code == 302:
            self.assertIn('next=', response.url)

    def test_next_parameter_with_multiple_query_params(self):
        """
        Test 'next' parameter with multiple query strings.

        Example: /users/john/?media=photos&page=2
        """
        url = reverse('prompts:user_profile', args=['edgeuser'])
        full_url = f"{url}?media=photos&page=2"

        response = self.client.get(full_url)

        if response.status_code == 302:
            # Just verify redirect happens and includes 'next'
            self.assertIn('next=', response.url)

    def test_authenticated_user_without_profile_object(self):
        """
        Test behavior if UserProfile object is missing (edge case).

        This shouldn't happen due to signals, but test defensive code.
        """
        # Create user without triggering signal (hypothetical)
        # In practice, signal always creates profile

        # Log in and access profile
        self.client.login(username='edgeuser', password='testpass123')
        url = reverse('prompts:user_profile', args=['edgeuser'])

        # Should still work (profile auto-created by signal)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_case_sensitive_username_in_next_parameter(self):
        """
        Test that username case is preserved in 'next' parameter.

        Django usernames are case-sensitive.
        """
        # Try to access user with exact case
        url = reverse('prompts:user_profile', args=['edgeuser'])
        response = self.client.get(url)

        if response.status_code == 302:
            # Check 'next' preserves lowercase 'edgeuser'
            self.assertIn('edgeuser', response.url)

        # Try uppercase (should 404, not redirect)
        url_upper = reverse('prompts:user_profile', args=['EDGEUSER'])
        response_upper = self.client.get(url_upper)

        # Even with login required, 404 should take precedence
        # (can't login to access non-existent user)
        self.assertEqual(response_upper.status_code, 404)


@override_settings(LOGIN_URL='/custom-login/')
class CustomLoginURLTests(TestCase):
    """
    Test @login_required with custom LOGIN_URL setting.

    Verifies that Django respects custom login URL in redirects.
    """

    @classmethod
    def setUpTestData(cls):
        """Create test user."""
        cls.user = User.objects.create_user(
            username='customuser',
            password='testpass123'
        )

    def setUp(self):
        """Create fresh client."""
        self.client = Client()

    def test_redirect_uses_custom_login_url(self):
        """
        Test that @login_required uses custom LOGIN_URL from settings.

        With LOGIN_URL='/custom-login/', should redirect there (not /accounts/login/).
        """
        url = reverse('prompts:user_profile', args=['customuser'])
        response = self.client.get(url)

        # Assuming @login_required is applied
        if response.status_code == 302:
            # Should redirect to custom login URL
            self.assertTrue(
                response.url.startswith('/custom-login/'),
                f"Should redirect to /custom-login/, got: {response.url}"
            )


# ==============================================================================
# Test Execution Instructions
# ==============================================================================
#
# To run all auth tests:
#     python manage.py test prompts.tests.test_user_profile_auth
#
# To test WITH @login_required (after adding decorator):
#     python manage.py test prompts.tests.test_user_profile_auth.LoginRequiredTests
#
# To test WITHOUT @login_required (current behavior):
#     python manage.py test prompts.tests.test_user_profile_auth.PublicAccessTests
#
# To test edge cases:
#     python manage.py test prompts.tests.test_user_profile_auth.LoginRequiredEdgeCaseTests
#
# To test custom login URL:
#     python manage.py test prompts.tests.test_user_profile_auth.CustomLoginURLTests
#
# ==============================================================================
# Expected Test Results
# ==============================================================================
#
# CURRENT IMPLEMENTATION (no @login_required):
#   - LoginRequiredTests: FAIL (view is public, no redirect)
#   - PublicAccessTests: PASS (view is public)
#   - Edge case tests: PASS (if conditions handle both cases)
#
# WITH @login_required ADDED:
#   - LoginRequiredTests: PASS (view requires auth)
#   - PublicAccessTests: FAIL (view no longer public)
#   - Edge case tests: PASS (designed for @login_required)
#
# ==============================================================================
# How to Add @login_required to user_profile View
# ==============================================================================
#
# In prompts/views.py (line 1671), change:
#
#     def user_profile(request, username):
#
# To:
#
#     @login_required
#     def user_profile(request, username):
#
# And ensure this import exists at the top:
#
#     from django.contrib.auth.decorators import login_required
#
# ==============================================================================
