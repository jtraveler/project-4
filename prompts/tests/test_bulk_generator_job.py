"""
Tests for bulk generator job progress page (Phase 5A).

Tests: view access, context data, template rendering, cost calculations.
"""
import uuid

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from prompts.constants import IMAGE_COST_MAP
from prompts.models import BulkGenerationJob


@override_settings(OPENAI_API_KEY='test-key')
class BulkGeneratorJobViewAccessTests(TestCase):
    """Tests for access control on the job progress page."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', password='testpass', is_staff=False,
        )
        self.job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
            images_per_prompt=2,
            quality='medium',
            size='1024x1024',
        )
        self.url = reverse('prompts:bulk_generator_job', kwargs={'job_id': self.job.id})

    def test_staff_can_access_job_page(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_staff_redirected(self):
        self.client.login(username='regularuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_invalid_job_id_returns_404(self):
        self.client.login(username='staffuser', password='testpass')
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': uuid.uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_valid_job_id_returns_200(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_correct_template_used(self):
        self.client.login(username='staffuser', password='testpass')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'prompts/bulk_generator_job.html')

    def test_other_staff_cannot_access_another_users_job(self):
        """Staff can only see their own jobs."""
        other_staff = User.objects.create_user(
            username='otherstaff', password='testpass', is_staff=True,
        )
        self.client.login(username='otherstaff', password='testpass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


@override_settings(OPENAI_API_KEY='test-key')
class BulkGeneratorJobViewContextTests(TestCase):
    """Tests for context data passed to the template."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.client.login(username='staffuser', password='testpass')

    def _make_job(self, quality='medium', size='1024x1024', total_prompts=5, images_per_prompt=2):
        return BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=total_prompts,
            images_per_prompt=images_per_prompt,
            quality=quality,
            size=size,
        )

    def test_context_contains_job(self):
        job = self._make_job()
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertIn('job', response.context)
        self.assertEqual(response.context['job'], job)

    def test_context_contains_cost_per_image(self):
        job = self._make_job(quality='medium', size='1024x1024')
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertIn('cost_per_image', response.context)
        self.assertEqual(response.context['cost_per_image'], 0.034)

    def test_context_contains_total_images(self):
        job = self._make_job(total_prompts=5, images_per_prompt=2)
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertIn('total_images', response.context)
        self.assertEqual(response.context['total_images'], 10)

    def test_context_contains_estimated_total_cost(self):
        job = self._make_job(quality='medium', size='1024x1024', total_prompts=5, images_per_prompt=2)
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertIn('estimated_total_cost', response.context)
        # 10 images × $0.034 = $0.34
        self.assertAlmostEqual(response.context['estimated_total_cost'], 0.34, places=4)

    def test_context_display_size_uses_multiplication_sign(self):
        job = self._make_job(size='1024x1024')
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertIn('display_size', response.context)
        self.assertIn('\u00d7', response.context['display_size'])  # ×


@override_settings(OPENAI_API_KEY='test-key')
class BulkGeneratorJobTemplateTests(TestCase):
    """Tests for template rendering."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.client.login(username='staffuser', password='testpass')
        self.job = BulkGenerationJob.objects.create(
            created_by=self.staff_user,
            total_prompts=5,
            images_per_prompt=2,
            quality='medium',
            size='1024x1024',
        )
        self.url = reverse('prompts:bulk_generator_job', kwargs={'job_id': self.job.id})

    def test_template_contains_data_job_id(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-job-id=')

    def test_template_contains_data_cost_per_image(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-cost-per-image=')

    def test_template_contains_progress_bar(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'role="progressbar"')

    def test_template_contains_cancel_button_for_active_job(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'Cancel Generation')

    def test_template_no_cancel_button_for_completed_job(self):
        self.job.status = 'completed'
        self.job.save()
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Cancel Generation')

    def test_template_contains_aria_live(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'aria-live="polite"')

    def test_template_contains_status_url(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-status-url=')

    def test_template_contains_cancel_url(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-cancel-url=')


@override_settings(OPENAI_API_KEY='test-key')
class ImageCostMapTests(TestCase):
    """Tests for the IMAGE_COST_MAP pricing constant."""

    def test_low_quality_square(self):
        self.assertEqual(IMAGE_COST_MAP['low']['1024x1024'], 0.009)

    def test_low_quality_landscape(self):
        self.assertEqual(IMAGE_COST_MAP['low']['1536x1024'], 0.013)

    def test_low_quality_portrait(self):
        self.assertEqual(IMAGE_COST_MAP['low']['1024x1536'], 0.013)

    def test_medium_quality_square(self):
        self.assertEqual(IMAGE_COST_MAP['medium']['1024x1024'], 0.034)

    def test_medium_quality_landscape(self):
        self.assertEqual(IMAGE_COST_MAP['medium']['1536x1024'], 0.050)

    def test_medium_quality_portrait(self):
        self.assertEqual(IMAGE_COST_MAP['medium']['1024x1536'], 0.050)

    def test_high_quality_square(self):
        self.assertEqual(IMAGE_COST_MAP['high']['1024x1024'], 0.134)

    def test_high_quality_landscape(self):
        self.assertEqual(IMAGE_COST_MAP['high']['1536x1024'], 0.200)

    def test_high_quality_portrait(self):
        self.assertEqual(IMAGE_COST_MAP['high']['1024x1536'], 0.200)

    def test_all_quality_levels_present(self):
        self.assertIn('low', IMAGE_COST_MAP)
        self.assertIn('medium', IMAGE_COST_MAP)
        self.assertIn('high', IMAGE_COST_MAP)

    def test_view_uses_correct_cost_for_high_quality_landscape(self):
        """Integration: view picks correct cost from IMAGE_COST_MAP."""
        staff_user = User.objects.create_user(
            username='staffuser2', password='testpass', is_staff=True,
        )
        self.client.login(username='staffuser2', password='testpass')
        job = BulkGenerationJob.objects.create(
            created_by=staff_user,
            total_prompts=1,
            images_per_prompt=1,
            quality='high',
            size='1536x1024',
        )
        url = reverse('prompts:bulk_generator_job', kwargs={'job_id': job.id})
        response = self.client.get(url)
        self.assertEqual(response.context['cost_per_image'], 0.200)
        self.assertAlmostEqual(response.context['estimated_total_cost'], 0.200, places=4)


class GetCostPerImageDelegationTests(TestCase):
    """Tests that get_cost_per_image() delegates to IMAGE_COST_MAP (Session 143)."""

    def setUp(self):
        from prompts.services.image_providers.openai_provider import OpenAIImageProvider
        self.provider = OpenAIImageProvider(api_key='sk-test')

    def test_high_square(self):
        cost = self.provider.get_cost_per_image(size='1024x1024', quality='high')
        self.assertAlmostEqual(cost, 0.134)
        self.assertNotAlmostEqual(cost, 0.067)  # old stale value

    def test_high_portrait(self):
        cost = self.provider.get_cost_per_image(size='1024x1536', quality='high')
        self.assertAlmostEqual(cost, 0.200)
        self.assertNotAlmostEqual(cost, 0.092)  # old stale value

    def test_medium_landscape(self):
        cost = self.provider.get_cost_per_image(size='1536x1024', quality='medium')
        self.assertAlmostEqual(cost, 0.050)
        self.assertNotAlmostEqual(cost, 0.046)  # old stale value

    def test_low_square(self):
        cost = self.provider.get_cost_per_image(size='1024x1024', quality='low')
        self.assertAlmostEqual(cost, 0.009)

    def test_unknown_quality_falls_back(self):
        cost = self.provider.get_cost_per_image(size='1024x1024', quality='unknown')
        self.assertAlmostEqual(cost, 0.034)  # fallback is medium square

    def test_size_is_no_longer_ignored(self):
        """Regression: old COST_MAP ignored size entirely."""
        square_cost = self.provider.get_cost_per_image(size='1024x1024', quality='high')
        portrait_cost = self.provider.get_cost_per_image(size='1024x1536', quality='high')
        self.assertNotEqual(square_cost, portrait_cost)  # must differ by size
