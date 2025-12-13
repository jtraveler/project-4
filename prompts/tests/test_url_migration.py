"""
Test URL Migration: Phase I (Updated)

Tests for URL migration to /prompts/ namespace with 301 redirects.

All tests verify:
1. New /prompts/ URLs return 200 OK
2. Legacy /ai/ URLs return 301 permanent redirect to /prompts/
3. Legacy /inspiration/ai/ URLs return 301 permanent redirect to /prompts/
4. Query parameters preserved in redirects
5. Directory redirects work correctly
"""

from django.test import TestCase, Client
from http import HTTPStatus


class AIGeneratorURLMigrationTests(TestCase):
    """Test 301 redirects for AI generator pages to /prompts/ namespace."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.generators = [
            'midjourney',
            'dalle3',
            'dalle2',
            'stable-diffusion',
            'leonardo-ai',
            'flux',
            'sora',
            'sora2',
            'veo3',
            'adobe-firefly',
            'bing-image-creator',
        ]

    def test_new_url_returns_200(self):
        """New /prompts/{generator}/ URLs should return 200 OK."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/prompts/{generator}/')
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"New URL for {generator} did not return 200"
                )

    def test_old_ai_url_returns_301(self):
        """Old /ai/{generator}/ URLs should return HTTP 301."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/ai/{generator}/', follow=False)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.MOVED_PERMANENTLY,
                    f"Generator {generator} did not return 301 status"
                )

    def test_old_inspiration_ai_url_returns_301(self):
        """Old /inspiration/ai/{generator}/ URLs should return HTTP 301."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(
                    f'/inspiration/ai/{generator}/',
                    follow=False
                )
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.MOVED_PERMANENTLY,
                    f"Generator {generator} did not return 301 status"
                )

    def test_ai_redirect_destination_correct(self):
        """Redirects from /ai/ should point to /prompts/."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/ai/{generator}/', follow=False)
                expected_location = f'/prompts/{generator}/'
                self.assertEqual(
                    response.url,
                    expected_location,
                    f"Generator {generator} redirects to wrong URL"
                )

    def test_inspiration_ai_redirect_destination_correct(self):
        """Redirects from /inspiration/ai/ should point to /prompts/."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(
                    f'/inspiration/ai/{generator}/',
                    follow=False
                )
                expected_location = f'/prompts/{generator}/'
                self.assertEqual(
                    response.url,
                    expected_location,
                    f"Generator {generator} redirects to wrong URL"
                )

    def test_redirect_preserves_query_string(self):
        """Query parameters should be preserved in redirect."""
        test_cases = [
            ('?page=2', '?page=2'),
            ('?sort=trending', '?sort=trending'),
            ('?type=image&sort=popular', '?type=image&sort=popular'),
            ('?page=3&type=video&date=week', '?page=3&type=video&date=week'),
        ]
        for query_string, expected_qs in test_cases:
            with self.subTest(query_string=query_string):
                response = self.client.get(
                    f'/ai/midjourney/{query_string}',
                    follow=False
                )
                self.assertIn(
                    expected_qs,
                    response.url,
                    f"Query string '{query_string}' not preserved in redirect"
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

    def test_prompts_hub_returns_200(self):
        """/prompts/ should return 200 OK."""
        response = self.client.get('/prompts/', follow=False)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            "/prompts/ did not return 200 OK"
        )

    def test_followed_redirect_returns_200(self):
        """Following the redirect should reach a 200 OK page."""
        response = self.client.get('/ai/midjourney/', follow=True)
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            "Following redirect did not end at 200 OK"
        )
        # Verify we landed at the correct URL
        self.assertEqual(
            response.request['PATH_INFO'],
            '/prompts/midjourney/'
        )
