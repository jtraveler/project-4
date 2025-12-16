"""
Test Generator Page Enhancements: Phase I.3

Tests for the AI generator category page improvements including:
1. Stats display (prompt count, view count)
2. Related generators section
3. Enhanced SEO with BreadcrumbList schema
4. Empty state CTA
5. Context data integrity
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from http import HTTPStatus
from prompts.constants import AI_GENERATORS
from prompts.models import Prompt, PromptView


class GeneratorPageContextTests(TestCase):
    """Test the context data for generator pages."""

    def setUp(self):
        """Set up test client and create test user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_generator_page_returns_200(self):
        """Generator page should return 200 OK."""
        response = self.client.get('/prompts/midjourney/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            "Generator page did not return 200 OK"
        )

    def test_context_has_prompt_count(self):
        """Context should include prompt_count."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('prompt_count', response.context)
        self.assertIsInstance(response.context['prompt_count'], int)

    def test_context_has_total_views(self):
        """Context should include total_views."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('total_views', response.context)
        self.assertIsInstance(response.context['total_views'], int)

    def test_context_has_related_generators(self):
        """Context should include related_generators list."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('related_generators', response.context)
        self.assertIsInstance(response.context['related_generators'], list)

    def test_related_generators_excludes_current(self):
        """Related generators should not include the current generator."""
        response = self.client.get('/prompts/midjourney/')
        related = response.context['related_generators']
        slugs = [gen['slug'] for gen in related]
        self.assertNotIn('midjourney', slugs)

    def test_related_generators_limit_five(self):
        """Related generators should be limited to 5 max."""
        response = self.client.get('/prompts/midjourney/')
        related = response.context['related_generators']
        self.assertLessEqual(len(related), 5)

    def test_related_generators_have_required_keys(self):
        """Each related generator should have required keys."""
        response = self.client.get('/prompts/midjourney/')
        related = response.context['related_generators']
        required_keys = ['name', 'slug', 'prompt_count']
        for gen in related:
            for key in required_keys:
                self.assertIn(
                    key, gen,
                    f"Related generator missing required key: {key}"
                )

    def test_context_has_has_prompts(self):
        """Context should include has_prompts boolean."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('has_prompts', response.context)
        self.assertIsInstance(response.context['has_prompts'], bool)

    def test_context_has_page_title(self):
        """Context should include page_title."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('page_title', response.context)
        self.assertEqual(
            response.context['page_title'],
            'Midjourney Prompts'
        )

    def test_context_has_meta_description(self):
        """Context should include meta_description."""
        response = self.client.get('/prompts/midjourney/')
        self.assertIn('meta_description', response.context)
        self.assertIn('Midjourney', response.context['meta_description'])


class GeneratorPageSEOTests(TestCase):
    """Test SEO elements on generator pages."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_page_has_breadcrumb_schema(self):
        """Page should have BreadcrumbList in Schema.org structured data."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        self.assertIn('"@type": "BreadcrumbList"', content)

    def test_page_has_collection_page_schema(self):
        """Page should have CollectionPage in Schema.org structured data."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        self.assertIn('"@type": "CollectionPage"', content)

    def test_breadcrumb_has_three_items(self):
        """BreadcrumbList should have Home > Prompts > Generator."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        # Check for position markers
        self.assertIn('"position": 1', content)
        self.assertIn('"position": 2', content)
        self.assertIn('"position": 3', content)

    def test_page_title_format(self):
        """Page title should follow expected format."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        expected_title = 'Midjourney Prompts - AI Art Prompts | PromptFinder'
        self.assertIn(f'<title>{expected_title}</title>', content)

    def test_meta_description_exists(self):
        """Page should have meta description."""
        response = self.client.get('/prompts/dalle3/')
        content = response.content.decode()
        self.assertIn('DALL-E 3', content)


class GeneratorPageUITests(TestCase):
    """Test UI elements on generator pages."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_hero_section_exists(self):
        """Page should have hero section (now called generator-header)."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        self.assertIn('generator-header', content)

    def test_stats_pills_exist(self):
        """Page should have stats badges (redesigned from pills to badges)."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        self.assertIn('generator-stats', content)
        self.assertIn('stat-badge', content)

    def test_related_generators_section_title(self):
        """Page should have related generators section with title if generators exist."""
        response = self.client.get('/prompts/midjourney/')
        related_generators = response.context.get('related_generators', [])
        # Section only shows if related_generators context is not empty
        if related_generators:
            content = response.content.decode()
            self.assertIn('Explore Other AI Platforms', content)

    def test_empty_state_has_upload_cta(self):
        """Empty state should have prominent upload CTA."""
        # Test with a generator that likely has no prompts
        response = self.client.get('/prompts/veo3/')
        content = response.content.decode()
        # Either shows prompts or shows upload CTA
        self.assertTrue(
            'Upload First' in content or 'masonry-grid' in content,
            "Page should show either prompts or upload CTA"
        )

    def test_breadcrumb_navigation_exists(self):
        """Page should have breadcrumb in Schema.org structured data."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        # Breadcrumb is in JSON-LD schema, not visible HTML
        self.assertIn('"@type": "BreadcrumbList"', content)
        self.assertIn('"name": "Home"', content)
        self.assertIn('"name": "Prompts"', content)

    def test_filter_bar_exists(self):
        """Page should have filter bar (redesigned with generator-filter-bar)."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        self.assertIn('generator-filter-bar', content)
        self.assertIn('generator-tabs', content)
        self.assertIn('gen-dropdown', content)
        self.assertIn('sortDropdown', content)

    def test_cta_section_exists(self):
        """Page should have CTA in empty state or upload button."""
        response = self.client.get('/prompts/midjourney/')
        content = response.content.decode()
        # After redesign, CTA is in empty state or via upload button
        # Check for either masonry grid (has prompts) or empty state CTA
        self.assertTrue(
            'generator-empty-state' in content or 'masonry-grid' in content,
            "Page should have either prompts grid or empty state with CTA"
        )


class GeneratorPageStatsTests(TestCase):
    """Test stats accuracy on generator pages."""

    def setUp(self):
        """Set up test client and test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_prompt_count_matches_database(self):
        """Prompt count should match actual database count."""
        # Create a test prompt
        prompt = Prompt.objects.create(
            title='Test Midjourney Prompt',
            slug='test-midjourney-prompt-stats',
            author=self.user,
            content='Test prompt content',
            ai_generator='midjourney',
            status=1
        )

        response = self.client.get('/prompts/midjourney/')
        prompt_count = response.context['prompt_count']

        # Count should include the new prompt
        db_count = Prompt.objects.filter(
            ai_generator='midjourney',
            status=1,
            deleted_at__isnull=True
        ).count()

        self.assertEqual(prompt_count, db_count)

        # Cleanup
        prompt.delete()

    def test_total_views_counts_correctly(self):
        """Total views should count PromptView records."""
        # Create test prompt and view
        prompt = Prompt.objects.create(
            title='Test View Count',
            slug='test-view-count-unique',
            author=self.user,
            content='Test content',
            ai_generator='midjourney',
            status=1
        )

        # Create a view record directly (bypassing rate limiting)
        PromptView.objects.create(
            prompt=prompt,
            user=self.user,
            ip_hash='test_hash_123'
        )

        response = self.client.get('/prompts/midjourney/')
        total_views = response.context['total_views']

        # Views should include our test view
        db_views = PromptView.objects.filter(
            prompt__ai_generator='midjourney',
            prompt__status=1,
            prompt__deleted_at__isnull=True
        ).count()

        self.assertEqual(total_views, db_views)

        # Cleanup
        prompt.delete()


class GeneratorPage404Tests(TestCase):
    """Test 404 handling for generator pages."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_invalid_generator_returns_404(self):
        """Invalid generator slug should return 404."""
        response = self.client.get('/prompts/invalid-generator/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_all_valid_generators_return_200(self):
        """All valid generators in AI_GENERATORS should return 200."""
        for slug in AI_GENERATORS.keys():
            with self.subTest(generator=slug):
                response = self.client.get(f'/prompts/{slug}/')
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"Generator {slug} did not return 200"
                )
