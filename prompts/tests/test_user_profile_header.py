"""
Tests for user profile header improvements (Phase E - Part 1)

Tests cover:
- Edit button visibility (owner vs non-owner)
- Trash tab visibility and functionality (owner only)
- Media filter form rendering and filtering
- Mobile responsiveness
- JavaScript functionality (overflow arrows, smooth scrolling)
"""

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
        self.assertContains(response, 'Edit Profile')
        self.assertContains(response, 'btn-success')  # Green button
        self.assertContains(response, 'fa-pen')  # Pen icon

        # Check context variable
        self.assertTrue(response.context['is_owner'])

    def test_edit_button_hidden_from_visitor(self):
        """Edit Profile button should NOT be visible to non-owners"""
        self.client.login(username='visitor', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Edit Profile')

        # Check context variable
        self.assertFalse(response.context['is_owner'])

    def test_edit_button_hidden_from_anonymous(self):
        """Edit Profile button should NOT be visible to anonymous users"""
        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Edit Profile')

        # Check context variable
        self.assertFalse(response.context['is_owner'])

    def test_trash_tab_visible_to_owner(self):
        """Trash tab should be visible to profile owner"""
        self.client.login(username='profileowner', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trash')
        self.assertContains(response, 'fa-trash')  # Trash icon
        self.assertContains(response, 'badge-danger')  # Count badge

        # Check trash count is displayed (should be 1)
        self.assertContains(response, '>1<')  # Badge with count 1

    def test_trash_tab_hidden_from_visitor(self):
        """Trash tab should NOT be visible to non-owners"""
        self.client.login(username='visitor', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)

        # Should not contain Trash tab
        self.assertNotContains(response, 'href="?tab=trash"')

    def test_trash_tab_hidden_from_anonymous(self):
        """Trash tab should NOT be visible to anonymous users"""
        response = self.client.get(reverse('prompts:user_profile', args=['profileowner']))

        self.assertEqual(response.status_code, 200)

        # Should not contain Trash tab
        self.assertNotContains(response, 'href="?tab=trash"')

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

        # Create image prompts
        for i in range(3):
            Prompt.objects.create(
                title=f'Image Prompt {i}',
                slug=f'image-prompt-{i}',
                content='Image content',
                author=self.user,
                status=1,
                ai_generator='midjourney',
                is_image=True,
                is_video=False
            )

        # Create video prompts
        for i in range(2):
            Prompt.objects.create(
                title=f'Video Prompt {i}',
                slug=f'video-prompt-{i}',
                content='Video content',
                author=self.user,
                status=1,
                ai_generator='runway',
                is_image=False,
                is_video=True
            )

    def test_filter_form_renders(self):
        """Media filter form should render with correct structure"""
        response = self.client.get(reverse('prompts:user_profile', args=['testuser']))

        self.assertEqual(response.status_code, 200)

        # Check form exists
        self.assertContains(response, 'id="media-filter-form"')
        self.assertContains(response, 'method="get"')

        # Check dropdowns exist
        self.assertContains(response, 'name="media_type"')
        self.assertContains(response, 'name="ai_generator"')
        self.assertContains(response, 'name="date_range"')

        # Check options
        self.assertContains(response, '<option value="all">All Media</option>')
        self.assertContains(response, '<option value="images">Images Only</option>')
        self.assertContains(response, '<option value="videos">Videos Only</option>')

    def test_filter_by_media_type_images(self):
        """Filter should show only images when images selected"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media_type': 'images'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain 3 image prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 3)

        for prompt in prompts:
            self.assertTrue(prompt.is_image)
            self.assertFalse(prompt.is_video)

    def test_filter_by_media_type_videos(self):
        """Filter should show only videos when videos selected"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media_type': 'videos'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain 2 video prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 2)

        for prompt in prompts:
            self.assertFalse(prompt.is_image)
            self.assertTrue(prompt.is_video)

    def test_filter_by_ai_generator(self):
        """Filter should show only prompts from specific AI generator"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'ai_generator': 'midjourney'}
        )

        self.assertEqual(response.status_code, 200)

        # Should contain only midjourney prompts (3)
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 3)

        for prompt in prompts:
            self.assertEqual(prompt.ai_generator, 'midjourney')

    def test_filter_by_date_range_week(self):
        """Filter should show prompts from last 7 days"""
        # Create old prompt (8 days ago)
        old_prompt = Prompt.objects.create(
            title='Old Prompt',
            slug='old-prompt',
            content='Old content',
            author=self.user,
            status=1,
            ai_generator='midjourney'
        )
        old_prompt.created_on = timezone.now() - timedelta(days=8)
        old_prompt.save()

        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'date_range': 'week'}
        )

        self.assertEqual(response.status_code, 200)

        prompts = response.context['prompts']

        # Should not include old prompt
        self.assertNotIn(old_prompt, prompts)

        # Should include recent prompts (5 total)
        self.assertEqual(prompts.count(), 5)

    def test_filter_combination(self):
        """Multiple filters should work together"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {
                'media_type': 'images',
                'ai_generator': 'midjourney',
                'date_range': 'all'
            }
        )

        self.assertEqual(response.status_code, 200)

        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 3)

        for prompt in prompts:
            self.assertTrue(prompt.is_image)
            self.assertEqual(prompt.ai_generator, 'midjourney')

    def test_filter_form_preserves_values(self):
        """Form should preserve selected values after filtering"""
        response = self.client.get(
            reverse('prompts:user_profile', args=['testuser']),
            {'media_type': 'videos', 'ai_generator': 'runway'}
        )

        self.assertEqual(response.status_code, 200)

        # Check selected values are preserved in form
        self.assertContains(response, '<option value="videos" selected>Videos Only</option>')
        self.assertContains(response, '<option value="runway" selected>Runway</option>')


class MobileResponsivenessTestCase(TestCase):
    """Test mobile responsiveness of profile header"""

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username='mobileuser',
            email='mobile@test.com',
            password='testpass123'
        )

    def test_media_filter_form_has_mobile_classes(self):
        """Media filter form should have mobile-responsive classes"""
        response = self.client.get(reverse('prompts:user_profile', args=['mobileuser']))

        self.assertEqual(response.status_code, 200)

        # Check form has responsive structure
        self.assertContains(response, 'id="media-filter-form"')

        # Check dropdowns have proper column classes
        self.assertContains(response, 'col-md-4')  # 3 columns on desktop
        self.assertContains(response, 'col-12')  # Full width on mobile

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
        self.assertIn('display: block', content)


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

        # Check arrow button exists
        self.assertContains(response, 'btn-scroll-right')
        self.assertContains(response, 'fa-chevron-right')

    def test_overflow_arrow_javascript_present(self):
        """JavaScript for arrow functionality should be present"""
        response = self.client.get(reverse('prompts:user_profile', args=['scrolluser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check JavaScript event handler
        self.assertIn('btn-scroll-right', content)
        self.assertIn('addEventListener', content)
        self.assertIn('scrollLeft', content)
        self.assertIn('e.stopPropagation()', content)

        # Check smooth scroll behavior
        self.assertIn('behavior: \'smooth\'', content)

        # Check console logging for debugging
        self.assertIn('console.log', content)
        self.assertIn('Overflow arrow clicked', content)

    def test_overflow_arrow_css_hover_effect(self):
        """Arrow should have hover effect CSS"""
        response = self.client.get(reverse('prompts:user_profile', args=['scrolluser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check hover CSS
        self.assertIn('.btn-scroll-right:hover', content)
        self.assertIn('transform: translateX(2px)', content)


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

        response = self.client.get(
            reverse('prompts:user_profile', args=['trashuser']),
            {'tab': 'trash'}
        )

        self.assertEqual(response.status_code, 200)

        # Check context
        self.assertEqual(response.context['active_tab'], 'trash')

        # Should show 3 trashed prompts
        prompts = response.context['prompts']
        self.assertEqual(prompts.count(), 3)

        for prompt in prompts:
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

    def test_trash_tab_in_overflow_system(self):
        """Trash tab should integrate with existing overflow system"""
        self.client.login(username='trashuser', password='testpass123')

        response = self.client.get(reverse('prompts:user_profile', args=['trashuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Trash tab should be in tab list (not dropdown)
        self.assertIn('href="?tab=trash"', content)

        # Should have data-tab attribute for overflow logic
        self.assertIn('data-tab', content)


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
        self.assertTrue(context['is_owner'])

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
        self.assertFalse(context['is_owner'])

        # Check user objects
        self.assertEqual(context['profile_user'].username, 'contextowner')
        self.assertEqual(context['user'].username, 'contextvisitor')

    def test_context_for_anonymous(self):
        """Context should handle anonymous users correctly"""
        response = self.client.get(reverse('prompts:user_profile', args=['contextowner']))

        self.assertEqual(response.status_code, 200)

        context = response.context

        # Check ownership
        self.assertFalse(context['is_owner'])

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

        # Check for debugging console logs
        self.assertIn('console.log(\'Overflow arrow clicked\')', content)
        self.assertIn('console.log(\'Container width:', content)
        self.assertIn('console.log(\'Scroll amount:', content)

    def test_javascript_scroll_calculation(self):
        """JavaScript should calculate scroll amount dynamically"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check scroll amount calculation
        self.assertIn('const containerWidth', content)
        self.assertIn('const scrollAmount = Math.max(200, containerWidth / 4)', content)

        # Should use min of 200px or 1/4 container width
        self.assertIn('Math.max(200', content)

    def test_javascript_stop_propagation(self):
        """Arrow click should stop event propagation"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check stopPropagation
        self.assertIn('e.stopPropagation()', content)

    def test_javascript_smooth_scroll(self):
        """Scroll should use smooth behavior"""
        response = self.client.get(reverse('prompts:user_profile', args=['jsuser']))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode('utf-8')

        # Check smooth scroll
        self.assertIn('behavior: \'smooth\'', content)
        self.assertIn('scrollTo({', content)


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

        # Should use reasonable number of queries (with select_related/prefetch_related)
        # Adjust this number based on your optimization
        self.assertLess(len(queries), 20, f"Too many queries: {len(queries)}")

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
            reverse('prompts:user_profile', args=['edgeuser']),
            {'tab': 'trash'}
        )
        self.assertEqual(trash_response.context['prompts'].count(), 3)

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
