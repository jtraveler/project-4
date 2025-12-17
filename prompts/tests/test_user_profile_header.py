"""
Tests for user profile header improvements (Phase E - Part 1)

Tests cover:
- Edit button visibility (owner vs non-owner)
- Trash tab visibility and functionality (owner only)
- Media filter form rendering and filtering
- Mobile responsiveness
- JavaScript functionality (overflow arrows, smooth scrolling)
"""

import unittest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from prompts.models import Prompt, UserProfile
from django.utils import timezone
from datetime import timedelta
import json



class ProfileHeaderVisibilityTestCase(TestCase):
    """Test visibility of Edit button and Trash tab based on ownership"""

    def setUp(self):
        """Create test users and profiles"""
        self.client = Client()

        # Create profile owner
        self.owner = User.objects.create_user(
            username='profileowner',
            email='owner@test.com',
            password='testpass123'
        )

        # Create non-owner (visitor)
        self.visitor = User.objects.create_user(
            username='visitor',
            email='visitor@test.com',
            password='testpass123'
        )

        # Create UserProfile for owner
        self.owner_profile, _ = UserProfile.objects.get_or_create(user=self.owner)

        # Create some test prompts
        for i in range(5):
            Prompt.objects.create(
                title=f'Test Prompt {i}',
                slug=f'test-prompt-{i}',
                content=f'Test content {i}',
                author=self.owner,
                status=1,
                ai_generator='midjourney'
            )

        # Create one trashed prompt
        self.trashed_prompt = Prompt.objects.create(
            title='Trashed Prompt',
            slug='trashed-prompt',
            content='This is trashed',
            author=self.owner,
            status=0
        )
        self.trashed_prompt.soft_delete(self.owner)

    def test_edit_button_visible_to_owner(self):
        """Edit Profile button should be visible to profile owner"""
        self.client.login(username='profileowner', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit profile')  # Lowercase 'p' in template
        self.assertContains(response, 'btn-edit-profile')  # Custom class
        self.assertContains(response, 'fa-pen')  # Pen icon

        # Check context variable
        self.assertTrue(response.context['is_own_profile'])

    def test_edit_button_hidden_from_visitor(self):
        """Edit Profile button should NOT be visible to non-owners"""
        self.client.login(username='visitor', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        # Check the button link is not present (CSS class is always in style block)
        self.assertNotContains(response, 'Edit profile</a>')

        # Check context variable
        self.assertFalse(response.context['is_own_profile'])

    def test_edit_button_hidden_from_anonymous(self):
        """Edit Profile button should NOT be visible to anonymous users"""
        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        # Check the button link is not present (CSS class is always in style block)
        self.assertNotContains(response, 'Edit profile</a>')

        # Check context variable
        self.assertFalse(response.context['is_own_profile'])

    def test_trash_tab_visible_to_owner(self):
        """Trash tab should be visible to profile owner"""
        self.client.login(username='profileowner', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trash')
        self.assertContains(response, 'fa-trash')  # Trash icon
        # Check trash URL is present
        trash_url = reverse('prompts:user_profile_trash', args=['profileowner'])
        self.assertContains(response, trash_url)

    def test_trash_tab_hidden_from_visitor(self):
        """Trash tab should NOT be visible to non-owners"""
        self.client.login(username='visitor', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)

        # Should not contain Trash tab URL for the profile owner
        trash_url = reverse('prompts:user_profile_trash', args=['profileowner'])
        self.assertNotContains(response, trash_url)

    def test_trash_tab_hidden_from_anonymous(self):
        """Trash tab should NOT be visible to anonymous users"""
        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)

        # Should not contain Trash tab URL
        trash_url = reverse('prompts:user_profile_trash', args=['profileowner'])
        self.assertNotContains(response, trash_url)

    def test_trash_count_accuracy(self):
        """Trash tab badge should show accurate count"""
        self.client.login(username='profileowner', password='testpass123')

        # Create more trashed prompts
        for i in range(3):
            prompt = Prompt.objects.create(
                title=f'Trashed {i}',
                slug=f'trashed-{i}',
                content='Content',
                author=self.owner,
                status=1
            )
            prompt.soft_delete(self.owner)

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        # Should now show 4 trashed items
        self.assertContains(response, '>4<')



class MediaFilterFormTestCase(TestCase):
    """Test media filter form functionality and filtering"""

    def setUp(self):
        """Create test data for filtering"""
        self.client = Client()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

        # Create image prompts (have featured_image, no featured_video)
        for i in range(3):
            Prompt.objects.create(
                title=f'Image Prompt {i}',
                slug=f'image-prompt-{i}',
                content='Image content',
                author=self.user,
                status=1,
                ai_generator='midjourney',
                featured_image='test_image.jpg'  # CloudinaryField accepts string
            )

        # Create video prompts (have featured_video)
        for i in range(2):
            Prompt.objects.create(
                title=f'Video Prompt {i}',
                slug=f'video-prompt-{i}',
                content='Video content',
                author=self.user,
                status=1,
                ai_generator='runway',
                featured_video='test_video.mp4'  # CloudinaryField accepts string
            )

    def test_filter_form_renders(self):
        """Media filter dropdown should render with correct structure"""
        response = self.client.get(reverse('prompts:user_profile', args=['testuser']))

        self.assertEqual(response.status_code, 200)

        # New Pexels-style dropdown structure
        self.assertContains(response, 'id="mediaDropdown"')
        self.assertContains(response, 'profile-sort-dropdown')
        self.assertContains(response, 'mediaDropdownBtn')

    def test_filter_by_media_photos(self):
        """Filter should show only images when 'photos' selected"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media': 'photos'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain 3 image prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 3)

        for prompt in prompts:
            self.assertFalse(prompt.is_video())  # is_video() is a method

    def test_filter_by_media_videos(self):
        """Filter should show only videos when 'videos' selected"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media': 'videos'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain 2 video prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 2)

        for prompt in prompts:
            self.assertTrue(prompt.is_video())  # is_video() is a method

    def test_filter_all_shows_all_prompts(self):
        """Filter 'all' should show both images and videos"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media': 'all'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain all 5 prompts (3 images + 2 videos)
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 5)

    def test_filter_form_preserves_selection(self):
        """Form should preserve selected filter value"""
        # Request with videos filter
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media': 'videos'}
        )
        self.assertEqual(response.status_code, 200)
        # New dropdown shows "Videos only" as active and in button text
        self.assertContains(response, 'Videos only')
        # The active item should have the 'active' class
        self.assertContains(response, 'media=videos')



class MobileResponsivenessTestCase(TestCase):
    """Test mobile responsiveness of profile header"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='mobileuser',
            email='mobile@test.com',
            password='testpass123'
        )

    def test_media_filter_form_has_responsive_structure(self):
        """Media filter dropdown should have responsive structure"""
        response = self.client.get(reverse('prompts:user_profile', args=['mobileuser']))
        self.assertEqual(response.status_code, 200)
        # New dropdown structure with responsive container
        self.assertContains(response, 'profile-filters-container')
        self.assertContains(response, 'profile-sort-dropdown')

    def test_mobile_css_media_queries_present(self):
        """Check that mobile CSS media queries are present in template"""
        response = self.client.get(reverse('prompts:user_profile', args=['mobileuser']))

        self.assertEqual(response.status_code, 200)

        # Check for mobile media query styles
        content = response.content.decode('utf-8')

        # Should contain media query for screens below 990px
        self.assertIn('@media (max-width: 990px)', content)
        self.assertIn('#media-filter-form', content)
        self.assertIn('width: 100%', content)



class OverflowArrowFunctionalityTestCase(TestCase):
    """Test overflow arrow click handler and scroll behavior"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='scrolluser',
            email='scroll@test.com',
            password='testpass123'
        )

    def test_overflow_arrow_html_present(self):
        """Overflow arrow button should be present in HTML"""
        response = self.client.get(reverse('prompts:user_profile', args=['scrolluser']))

        self.assertEqual(response.status_code, 200)

        # Check arrow button exists (actual class is overflow-arrow)
        self.assertContains(response, 'overflow-arrow')
        self.assertContains(response, 'fa-chevron-right')

    def test_overflow_arrow_javascript_present(self):
        """JavaScript for arrow functionality should be present"""
        response = self.client.get(reverse('prompts:user_profile', args=['scrolluser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check JavaScript references arrow (actual class is overflow-arrow)
        self.assertIn('overflow-arrow', content)
        self.assertIn('addEventListener', content)

    def test_overflow_arrow_css_hover_effect(self):
        """Arrow should have hover effect CSS"""
        response = self.client.get(reverse('prompts:user_profile', args=['scrolluser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check hover CSS (actual class is overflow-arrow)
        self.assertIn('.overflow-arrow:hover', content)



class TrashTabIntegrationTestCase(TestCase):
    """Test trash tab integration with existing tab system"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='trashuser',
            email='trash@test.com',
            password='testpass123'
        )

        # Create active prompts
        for i in range(5):
            Prompt.objects.create(
                title=f'Active {i}',
                slug=f'active-{i}',
                content='Active content',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )

        # Create trashed prompts
        for i in range(3):
            prompt = Prompt.objects.create(
                title=f'Trashed {i}',
                slug=f'trashed-{i}',
                content='Trashed content',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )
            prompt.soft_delete(self.user)

    def test_trash_tab_shows_trashed_prompts(self):
        """Trash tab should display only trashed prompts"""
        self.client.login(username='trashuser', password='testpass123')

        # Use the dedicated trash URL pattern
        response = self.client.get(
            reverse('prompts:user_profile_trash', args=['trashuser'])
        )

        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertEqual(response.context['active_tab'], 'trash')

        # Should show 3 trashed prompts in trash_items
        trash_items = response.context['trash_items']
        self.assertEqual(len(trash_items), 3)

        for prompt in trash_items:
            self.assertTrue(prompt.is_in_trash)

    def test_all_tab_excludes_trashed_prompts(self):
        """'All' tab should NOT show trashed prompts"""
        self.client.login(username='trashuser', password='testpass123')

        response = self.client.get(
            reverse('prompts:user_profile', args=['trashuser']),
            {'tab': 'all'}
        )

        self.assertEqual(response.status_code, 200)

        # Should show only 5 active prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 5)

        for prompt in prompts:
            self.assertFalse(prompt.is_in_trash)

    def test_trash_accessible_from_profile(self):
        """Trash should be accessible from profile page"""
        self.client.login(username='trashuser', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['trashuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Trash is at /users/{username}/trash/ (separate URL)
        # Check trash link is present for profile owner
        trash_url = reverse('prompts:user_profile_trash', args=['trashuser'])
        self.assertIn(trash_url, content)



class ProfileHeaderContextTestCase(TestCase):
    """Test context variables passed to template"""

    def setUp(self):
        self.client = Client()

        self.owner = User.objects.create_user(
            username='contextowner',
            email='context@test.com',
            password='testpass123'
        )

        self.visitor = User.objects.create_user(
            username='contextvisitor',
            email='visitor@test.com',
            password='testpass123'
        )

        # Create prompts
        for i in range(10):
            Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content='Content',
                author=self.owner,
                status=1,
                ai_generator='midjourney'
            )

    def test_context_for_owner(self):
        """Context should have correct values for profile owner"""
        self.client.login(username='contextowner', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['contextowner']))

        self.assertEqual(response.status_code, 200)

        context = response.context

        # Check ownership
        self.assertTrue(context['is_own_profile'])

        # Check user objects
        self.assertEqual(context['profile_user'].username, 'contextowner')
        self.assertEqual(context['user'].username, 'contextowner')

        # Check prompt stats
        self.assertEqual(context['total_prompts'], 10)
        self.assertGreaterEqual(context['total_likes'], 0)

    def test_context_for_visitor(self):
        """Context should have correct values for non-owner"""
        self.client.login(username='contextvisitor', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['contextowner']))

        self.assertEqual(response.status_code, 200)

        context = response.context

        # Check ownership
        self.assertFalse(context['is_own_profile'])

        # Check user objects
        self.assertEqual(context['profile_user'].username, 'contextowner')
        self.assertEqual(context['user'].username, 'contextvisitor')

    def test_context_for_anonymous(self):
        """Context should handle anonymous users correctly"""
        response = self.client.get(reverse('prompts:user_profile', args=['contextowner']))

        self.assertEqual(response.status_code, 200)

        context = response.context

        # Check ownership
        self.assertFalse(context['is_own_profile'])

        # Check profile user
        self.assertEqual(context['profile_user'].username, 'contextowner')



class JavaScriptFunctionalityTestCase(TestCase):
    """Test JavaScript code structure and logic"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='jsuser',
            email='js@test.com',
            password='testpass123'
        )

    def test_javascript_console_logging(self):
        """JavaScript should have console logs for debugging"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check for debugging console logs (actual log messages)
        self.assertIn('console.log', content)
        self.assertIn('Overflow', content)

    def test_javascript_scroll_functionality(self):
        """JavaScript should have scroll functionality"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check scroll amount functionality exists
        self.assertIn('scrollAmount', content)
        self.assertIn('getScrollAmount', content)

    def test_javascript_keyboard_navigation(self):
        """JavaScript should support keyboard navigation"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check keyboard navigation
        self.assertIn('ArrowLeft', content)
        self.assertIn('ArrowRight', content)
        self.assertIn('keydown', content)

    def test_javascript_smooth_scroll(self):
        """Scroll should use smooth behavior"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check smooth scroll behavior
        self.assertIn("behavior: 'smooth'", content)


# Performance and Integration Tests


class ProfileHeaderPerformanceTestCase(TestCase):
    """Test performance of profile header with large datasets"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@test.com',
            password='testpass123'
        )

        # Create large number of prompts (100)
        for i in range(100):
            Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content=f'Content {i}',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )

    def test_large_dataset_query_count(self):
        """Profile page should use optimized queries with large dataset"""
        self.client.login(username='perfuser', password='testpass123')

        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse('prompts:user_profile', args=['perfuser']))

        self.assertEqual(response.status_code, 200)

        # Profile page is complex with: user data, prompts, stats, leaderboard,
        # notifications, and various related data. 50-60 queries is reasonable
        # for this level of functionality. Ensure it doesn't grow unbounded.
        self.assertLess(len(queries), 60, f"Too many queries: {len(queries)}")

    def test_pagination_with_large_dataset(self):
        """Profile should paginate large datasets"""
        response = self.client.get(reverse('prompts:user_profile', args=['perfuser']))

        self.assertEqual(response.status_code, 200)

        # Check if pagination is present
        if hasattr(response.context['prompts'], 'paginator'):
            self.assertIsNotNone(response.context['prompts'].paginator)

        # Should not load all 100 prompts at once
        prompts_on_page = len(response.context['prompts'])
        self.assertLessEqual(prompts_on_page, 50)



class EdgeCaseTestCase(TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@test.com',
            password='testpass123'
        )

    def test_profile_with_no_prompts(self):
        """Profile should handle user with no prompts"""
        response = self.client.get(reverse('prompts:user_profile', args=['edgeuser']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_prompts'], 0)

        # Should show empty state
        self.assertContains(response, 'No prompts')

    def test_profile_with_only_trashed_prompts(self):
        """Profile should handle user with only trashed prompts"""
        # Create and trash prompts
        for i in range(3):
            prompt = Prompt.objects.create(
                title=f'Prompt {i}',
                slug=f'prompt-{i}',
                content='Content',
                author=self.user,
                status=1,
                ai_generator='midjourney'
            )
            prompt.soft_delete(self.user)

        self.client.login(username='edgeuser', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['edgeuser']))

        self.assertEqual(response.status_code, 200)

        # 'All' tab should show 0 prompts
        self.assertEqual(response.context['prompts'].count(), 0)

        # Trash tab should show 3
        trash_response = self.client.get(
            reverse('prompts:user_profile_trash', args=['edgeuser'])
        )
        self.assertEqual(len(trash_response.context['trash_items']), 3)

    def test_invalid_filter_values(self):
        """Profile should handle invalid filter values gracefully"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['edgeuser']),
            {'media_type': 'invalid_value', 'ai_generator': 'nonexistent'}
        )

        self.assertEqual(response.status_code, 200)

        # Should default to showing all prompts (or 0 in this case)
        self.assertEqual(response.context['prompts'].count(), 0)

    def test_nonexistent_user_profile(self):
        """Profile should handle nonexistent user gracefully"""
        response = self.client.get(reverse('prompts:user_profile', args=['nonexistent']))

        # Should return 404
        self.assertEqual(response.status_code, 404)
