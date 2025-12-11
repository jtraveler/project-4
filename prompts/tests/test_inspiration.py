"""
Test Inspiration Hub: Phase I.2

Tests for the /inspiration/ page and related features.

All tests verify:
1. Inspiration index page returns 200 OK
2. Generator cards are displayed with correct data
3. Trending prompts section works correctly
4. Navigation links are present
5. All Platforms dropdown works on homepage
"""

from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from prompts.constants import AI_GENERATORS


class InspirationIndexTests(TestCase):
    """Test the /inspiration/ page."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_inspiration_index_returns_200(self):
        """/inspiration/ should return 200 OK."""
        response = self.client.get('/inspiration/')
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            "/inspiration/ did not return 200 OK"
        )

    def test_inspiration_index_uses_correct_template(self):
        """Inspiration index should use the correct template."""
        response = self.client.get('/inspiration/')
        self.assertTemplateUsed(response, 'prompts/inspiration_index.html')

    def test_inspiration_index_has_generators_context(self):
        """Context should include generators list."""
        response = self.client.get('/inspiration/')
        self.assertIn('generators', response.context)
        generators = response.context['generators']
        # Should have same number as AI_GENERATORS constant
        self.assertEqual(len(generators), len(AI_GENERATORS))

    def test_inspiration_index_generators_have_required_keys(self):
        """Each generator in context should have required keys."""
        response = self.client.get('/inspiration/')
        generators = response.context['generators']
        required_keys = ['name', 'slug', 'prompt_count']
        for gen in generators:
            for key in required_keys:
                self.assertIn(
                    key, gen,
                    f"Generator missing required key: {key}"
                )

    def test_inspiration_index_has_trending_prompts(self):
        """Context should include trending prompts."""
        response = self.client.get('/inspiration/')
        self.assertIn('trending_prompts', response.context)

    def test_inspiration_index_has_page_title(self):
        """Context should include page title."""
        response = self.client.get('/inspiration/')
        self.assertIn('page_title', response.context)
        self.assertEqual(
            response.context['page_title'],
            'AI Prompt Inspiration'
        )

    def test_inspiration_index_has_breadcrumb(self):
        """Page should have breadcrumb navigation."""
        response = self.client.get('/inspiration/')
        content = response.content.decode()
        self.assertIn('breadcrumb', content)
        self.assertIn('Home', content)

    def test_generator_links_are_correct(self):
        """Generator cards should link to correct category pages."""
        response = self.client.get('/inspiration/')
        content = response.content.decode()
        # Check at least one generator link is present
        self.assertIn('/inspiration/ai/midjourney/', content)

    def test_ai_directory_redirects_to_inspiration(self):
        """/ai/ should 301 redirect to /inspiration/."""
        response = self.client.get('/ai/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.MOVED_PERMANENTLY,
            "/ai/ did not return 301 status"
        )
        self.assertEqual(
            response.url,
            '/inspiration/',
            "/ai/ did not redirect to /inspiration/"
        )


class NavigationInspirationLinkTests(TestCase):
    """Test that Inspiration link is in navigation."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_explore_dropdown_has_inspiration_link(self):
        """Explore dropdown should have Inspiration link."""
        response = self.client.get('/')
        content = response.content.decode()
        # Check the Inspiration link is in the page
        self.assertIn('Inspiration', content)
        self.assertIn('/inspiration/', content)


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
        """Platform dropdown should have links to all generators."""
        response = self.client.get('/')
        content = response.content.decode()
        # Check for at least some generator links
        self.assertIn('/inspiration/ai/midjourney/', content)
        self.assertIn('/inspiration/ai/dalle3/', content)
        self.assertIn('/inspiration/ai/stable-diffusion/', content)

    def test_platform_dropdown_has_view_all_link(self):
        """Platform dropdown should have 'View All Platforms' link."""
        response = self.client.get('/')
        content = response.content.decode()
        self.assertIn('View All Platforms', content)


class URLReverseTests(TestCase):
    """Test URL reversing works correctly."""

    def test_inspiration_index_url_reverses(self):
        """inspiration_index URL should reverse correctly."""
        url = reverse('prompts:inspiration_index')
        self.assertEqual(url, '/inspiration/')

    def test_ai_generator_category_url_reverses(self):
        """ai_generator_category URL should reverse correctly."""
        url = reverse('prompts:ai_generator_category', kwargs={'generator_slug': 'midjourney'})
        self.assertEqual(url, '/inspiration/ai/midjourney/')
