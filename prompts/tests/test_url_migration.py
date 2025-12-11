"""
Test URL Migration: Phase I.1

Tests for the /ai/ to /inspiration/ai/ URL migration with 301 redirects.

All tests verify:
1. New URLs return 200 OK
2. Old URLs return 301 permanent redirect
3. Query parameters preserved in redirects
4. Directory redirects work correctly
"""

from django.test import TestCase, Client
from http import HTTPStatus


class AIGeneratorURLMigrationTests(TestCase):
    """Test 301 redirects for AI generator pages from /ai/ to /inspiration/ai/."""

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
            'veo-3',
            'adobe-firefly',
            'bing-image-creator',
        ]

    def test_new_url_returns_200(self):
        """New /inspiration/ai/{generator}/ URLs should return 200 OK."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/inspiration/ai/{generator}/')
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f"New URL for {generator} did not return 200"
                )

    def test_old_url_returns_301(self):
        """Old /ai/{generator}/ URLs should return HTTP 301."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/ai/{generator}/', follow=False)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.MOVED_PERMANENTLY,
                    f"Generator {generator} did not return 301 status"
                )

    def test_redirect_destination_correct(self):
        """Redirects should point to correct new URL."""
        for generator in self.generators:
            with self.subTest(generator=generator):
                response = self.client.get(f'/ai/{generator}/', follow=False)
                expected_location = f'/inspiration/ai/{generator}/'
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

    def test_inspiration_index_exists(self):
        """/inspiration/ should return 200 or 302 (temporary placeholder)."""
        response = self.client.get('/inspiration/', follow=False)
        self.assertIn(
            response.status_code,
            [HTTPStatus.OK, HTTPStatus.FOUND],
            "/inspiration/ did not return expected status"
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
            '/inspiration/ai/midjourney/'
        )
