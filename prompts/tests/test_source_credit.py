"""
Tests for source credit feature.

Covers:
- parse_source_credit() URL detection and KNOWN_SITES lookup
- Prompt model field defaults and constraints
- Bulk generator pipeline: source_credit flows from GeneratedImage to Prompt
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from prompts.models import Prompt
from prompts.utils.source_credit import parse_source_credit, KNOWN_SITES


class ParseSourceCreditTests(TestCase):
    """Tests for parse_source_credit() utility."""

    def test_empty_string_returns_empty(self):
        self.assertEqual(parse_source_credit(''), ('', ''))

    def test_none_input_returns_empty(self):
        self.assertEqual(parse_source_credit(None), ('', ''))

    def test_whitespace_only_returns_empty(self):
        self.assertEqual(parse_source_credit('   '), ('', ''))

    def test_plain_text_returns_text_no_url(self):
        name, url = parse_source_credit('PromptHero')
        self.assertEqual(name, 'PromptHero')
        self.assertEqual(url, '')

    def test_plain_text_with_spaces(self):
        name, url = parse_source_credit('John Doe')
        self.assertEqual(name, 'John Doe')
        self.assertEqual(url, '')

    def test_known_https_url_extracts_display_name(self):
        name, url = parse_source_credit(
            'https://prompthero.com/prompt/abc123'
        )
        self.assertEqual(name, 'PromptHero')
        self.assertEqual(url, 'https://prompthero.com/prompt/abc123')

    def test_known_http_url_extracts_display_name(self):
        name, url = parse_source_credit(
            'http://civitai.com/models/12345'
        )
        self.assertEqual(name, 'Civitai')
        self.assertEqual(url, 'http://civitai.com/models/12345')

    def test_known_www_url_extracts_display_name(self):
        name, url = parse_source_credit(
            'https://www.prompthero.com/prompt/xyz'
        )
        self.assertEqual(name, 'PromptHero')
        self.assertEqual(url, 'https://www.prompthero.com/prompt/xyz')

    def test_unknown_url_uses_domain(self):
        name, url = parse_source_credit('https://example.com/page')
        self.assertEqual(name, 'example.com')
        self.assertEqual(url, 'https://example.com/page')

    def test_bare_domain_with_path_detected_as_url(self):
        name, url = parse_source_credit('prompthero.com/prompt/abc')
        self.assertEqual(name, 'PromptHero')
        self.assertEqual(url, 'https://prompthero.com/prompt/abc')

    def test_bare_domain_without_path_treated_as_text(self):
        """Domain without a path slash is treated as plain text."""
        name, url = parse_source_credit('prompthero.com')
        self.assertEqual(name, 'prompthero.com')
        self.assertEqual(url, '')

    def test_all_known_sites_resolve(self):
        """Every entry in KNOWN_SITES should resolve correctly."""
        seen = set()
        for domain, expected_name in KNOWN_SITES.items():
            if expected_name in seen:
                continue
            seen.add(expected_name)
            name, url = parse_source_credit(f'https://{domain}/test')
            self.assertEqual(
                name, expected_name,
                f'{domain} should resolve to {expected_name}'
            )

    def test_strips_whitespace(self):
        name, url = parse_source_credit('  PromptHero  ')
        self.assertEqual(name, 'PromptHero')
        self.assertEqual(url, '')

    def test_script_tag_treated_as_plain_text(self):
        """XSS script tag input is returned as plain text (no URL)."""
        name, url = parse_source_credit('<script>alert("xss")</script>')
        self.assertEqual(name, '<script>alert("xss")</script>')
        self.assertEqual(url, '')

    def test_javascript_uri_treated_as_plain_text(self):
        """javascript: URI is not treated as a URL."""
        name, url = parse_source_credit('javascript:alert(1)')
        self.assertEqual(name, 'javascript:alert(1)')
        self.assertEqual(url, '')

    def test_very_long_input_truncated(self):
        """Input exceeding 200 chars is handled gracefully."""
        long_input = 'A' * 300
        name, url = parse_source_credit(long_input)
        self.assertEqual(name, long_input)
        self.assertEqual(url, '')


class PromptSourceCreditModelTests(TestCase):
    """Tests for Prompt model source_credit fields."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='pass123'
        )

    def test_source_credit_blank_by_default(self):
        prompt = Prompt(
            title='Test SC Default',
            slug='test-sc-default',
            content='test content',
            author=self.user,
            ai_generator='midjourney',
        )
        prompt.save()
        self.assertEqual(prompt.source_credit, '')
        self.assertEqual(prompt.source_credit_url, '')

    def test_source_credit_max_length(self):
        prompt = Prompt(
            title='Test SC MaxLen',
            slug='test-sc-maxlen',
            content='test content',
            author=self.user,
            ai_generator='midjourney',
            source_credit='x' * 200,
        )
        prompt.save()
        prompt.refresh_from_db()
        self.assertEqual(len(prompt.source_credit), 200)

    def test_source_credit_url_stores_and_retrieves(self):
        prompt = Prompt(
            title='Test SC URL',
            slug='test-sc-url',
            content='test content',
            author=self.user,
            ai_generator='midjourney',
            source_credit='PromptHero',
            source_credit_url='https://prompthero.com/prompt/abc',
        )
        prompt.save()
        prompt.refresh_from_db()
        self.assertEqual(prompt.source_credit, 'PromptHero')
        self.assertEqual(
            prompt.source_credit_url,
            'https://prompthero.com/prompt/abc'
        )


class BulkGeneratorSourceCreditTests(TestCase):
    """Tests for source_credit flowing through bulk generator pipeline."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='staffuser', password='pass123', is_staff=True
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_source_credit_flows_to_prompt(self, mock_vision):
        """Source credit on GeneratedImage copies to created Prompt."""
        from prompts.services.bulk_generation import BulkGenerationService
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'Credit Flow Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        service = BulkGenerationService()
        job = service.create_job(
            user=self.user,
            prompts=['test prompt'],
            source_credits=['https://prompthero.com/prompt/abc'],
        )

        # Verify source credit stored on GeneratedImage
        gen_image = job.images.first()
        self.assertEqual(
            gen_image.source_credit,
            'https://prompthero.com/prompt/abc'
        )

        # Simulate completed image
        gen_image.status = 'completed'
        gen_image.image_url = 'https://cdn.example.com/test.png'
        gen_image.save(update_fields=['status', 'image_url'])

        # Run page creation
        result = create_prompt_pages_from_job(
            str(job.id), [str(gen_image.id)]
        )

        self.assertEqual(result['created_count'], 1)

        # Verify source credit parsed and set on Prompt
        prompt = Prompt.objects.filter(
            title='Credit Flow Test'
        ).first()
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt.source_credit, 'PromptHero')
        self.assertEqual(
            prompt.source_credit_url,
            'https://prompthero.com/prompt/abc'
        )

    @patch('prompts.tasks._call_openai_vision')
    def test_empty_source_credit_leaves_prompt_blank(self, mock_vision):
        """Empty source credit on GeneratedImage leaves Prompt fields blank."""
        from prompts.services.bulk_generation import BulkGenerationService
        from prompts.tasks import create_prompt_pages_from_job

        mock_vision.return_value = {
            'title': 'No Credit Test',
            'description': 'desc',
            'tags': [],
            'categories': [],
            'descriptors': {},
        }

        service = BulkGenerationService()
        job = service.create_job(
            user=self.user,
            prompts=['test prompt'],
            source_credits=[''],
        )

        gen_image = job.images.first()
        gen_image.status = 'completed'
        gen_image.image_url = 'https://cdn.example.com/test.png'
        gen_image.save(update_fields=['status', 'image_url'])

        create_prompt_pages_from_job(
            str(job.id), [str(gen_image.id)]
        )

        prompt = Prompt.objects.filter(
            title='No Credit Test'
        ).first()
        self.assertIsNotNone(prompt)
        self.assertEqual(prompt.source_credit, '')
        self.assertEqual(prompt.source_credit_url, '')
