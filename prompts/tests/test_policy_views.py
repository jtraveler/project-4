"""
Session 173-C: smoke tests for the placeholder content policy page
linked from the bulk-generator NSFW chip ("Learn more" link).

Full policy ships in Session 175; this is a minimal pre-launch landing
page. These tests guard against accidental regression of the route +
view + template wiring.
"""
from django.test import TestCase
from django.urls import reverse


class ContentPolicyPlaceholderTests(TestCase):
    """Session 173-C: placeholder content policy page."""

    def test_content_policy_page_renders(self):
        """The /policies/content/ URL returns 200 with key content."""
        response = self.client.get(
            reverse('prompts:content_policy_placeholder')
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Content Policy')
        self.assertContains(response, 'Pre-launch placeholder')

    def test_content_policy_page_links_to_email(self):
        """The placeholder page surfaces the contact email for reports."""
        response = self.client.get(
            reverse('prompts:content_policy_placeholder')
        )
        self.assertContains(response, 'mailto:')
