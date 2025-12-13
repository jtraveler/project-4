"""
Test Prompts Hub: Phase I URL Migration

Tests for the /prompts/ page and related features.
Updated from test_inspiration.py for new URL structure.

All tests verify:
1. Prompts hub page returns 200 OK at /prompts/
2. Generator cards are displayed with correct data
3. Trending prompts section works correctly
4. Navigation links are present
5. All Platforms dropdown works on homepage
6. Legacy URLs redirect correctly (301)
"""

from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from prompts.constants import AI_GENERATORS


class PromptsHubTests(TestCase):
    """Test the /prompts/ page."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_prompts_hub_returns_200(self):
        """/prompts/ should return 200 OK."""
        response = self.client.get('/prompts/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            "/prompts/ did not return 200 OK"
        )

    def test_prompts_hub_uses_correct_template(self):
        """Prompts hub should use the correct template."""
        response = self.client.get('/prompts/')
        self.assertTemplateUsed(response, 'prompts/inspiration_index.html')

    def test_prompts_hub_has_generators_context(self):
        """Context should include generators list."""
        response = self.client.get('/prompts/')
        self.assertIn('generators', response.context)
        generators = response.context['generators']
        # Should have same number as AI_GENERATORS constant
        self.assertEqual(len(generators), len(AI_GENERATORS))

    def test_prompts_hub_generators_have_required_keys(self):
        """Each generator in context should have required keys."""
        response = self.client.get('/prompts/')
        generators = response.context['generators']
        required_keys = ['name', 'slug', 'prompt_count']
        for gen in generators:
            for key in required_keys:
                self.assertIn(
                    key, gen,
                    f"Generator missing required key: {key}"
                )

    def test_prompts_hub_has_trending_prompts(self):
        """Context should include trending prompts."""
        response = self.client.get('/prompts/')
        self.assertIn('trending_prompts', response.context)

    def test_prompts_hub_has_page_title(self):
        """Context should include page title."""
        response = self.client.get('/prompts/')
        self.assertIn('page_title', response.context)

    def test_prompts_hub_has_breadcrumb(self):
        """Page should have breadcrumb navigation."""
        response = self.client.get('/prompts/')
        content = response.content.decode()
        self.assertIn('breadcrumb', content)
        self.assertIn('Home', content)

    def test_generator_links_are_correct(self):
        """Generator cards should link to correct category pages."""
        response = self.client.get('/prompts/')
        content = response.content.decode()
        # Check at least one generator link is present (new URL structure)
        self.assertIn('/prompts/midjourney/', content)


class LegacyURLRedirectTests(TestCase):
    """Test that legacy URLs redirect correctly (301)."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_inspiration_redirects_to_prompts(self):
        """/inspiration/ should 301 redirect to /prompts/."""
        response = self.client.get('/inspiration/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.MOVED_PERMANENTLY,
            "/inspiration/ did not return 301 status"
        )
        self.assertEqual(
            response.url,
            '/prompts/',
            "/inspiration/ did not redirect to /prompts/"
        )

    def test_inspiration_ai_redirects_to_prompts(self):
        """/inspiration/ai/midjourney/ should 301 redirect to /prompts/midjourney/."""
        response = self.client.get('/inspiration/ai/midjourney/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.MOVED_PERMANENTLY,
            "/inspiration/ai/midjourney/ did not return 301 status"
        )
        self.assertEqual(
            response.url,
            '/prompts/midjourney/',
            "/inspiration/ai/midjourney/ did not redirect to /prompts/midjourney/"
        )

    def test_ai_directory_redirects_to_prompts(self):
        """/ai/ should 301 redirect to /prompts/."""
        response = self.client.get('/ai/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.MOVED_PERMANENTLY,
            "/ai/ did not return 301 status"
        )
        self.assertEqual(
            response.url,
            '/prompts/',
            "/ai/ did not redirect to /prompts/"
        )

    def test_ai_generator_redirects_to_prompts(self):
        """/ai/midjourney/ should 301 redirect to /prompts/midjourney/."""
        response = self.client.get('/ai/midjourney/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.MOVED_PERMANENTLY,
            "/ai/midjourney/ did not return 301 status"
        )
        self.assertEqual(
            response.url,
            '/prompts/midjourney/',
            "/ai/midjourney/ did not redirect to /prompts/midjourney/"
        )


class NavigationPromptsLinkTests(TestCase):
    """Test that Prompts link is in navigation."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_explore_dropdown_has_prompts_link(self):
        """Explore dropdown should have Prompts link."""
        response = self.client.get('/')
        content = response.content.decode()
        # Check the Prompts link is in the page
        self.assertIn('Prompts', content)
        self.assertIn('/prompts/', content)


class HomepagePlatformDropdownTests(TestCase):
    """Test the All Platforms dropdown on homepage."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_homepage_has_platform_dropdown(self):
        """Homepage should have All Platforms dropdown."""
        response = self.client.get('/')
        content = response.content.decode()
        self.assertIn('All Platforms', content)
        self.assertIn('platformDropdown', content)

    def test_platform_dropdown_has_generator_links(self):
        """Platform dropdown should have links to all generators (new URLs)."""
        response = self.client.get('/')
        content = response.content.decode()
        # Check for at least some generator links (new URL structure)
        self.assertIn('/prompts/midjourney/', content)
        self.assertIn('/prompts/dalle3/', content)
        self.assertIn('/prompts/stable-diffusion/', content)

    def test_platform_dropdown_has_view_all_link(self):
        """Platform dropdown should have 'View All Platforms' link."""
        response = self.client.get('/')
        content = response.content.decode()
        self.assertIn('View All Platforms', content)


class URLReverseTests(TestCase):
    """Test URL reversing works correctly."""

    def test_prompts_hub_url_reverses(self):
        """prompts_hub URL should reverse correctly."""
        url = reverse('prompts:prompts_hub')
        self.assertEqual(url, '/prompts/')

    def test_ai_generator_category_url_reverses(self):
        """ai_generator_category URL should reverse correctly."""
        url = reverse('prompts:ai_generator_category', kwargs={'generator_slug': 'midjourney'})
        self.assertEqual(url, '/prompts/midjourney/')
