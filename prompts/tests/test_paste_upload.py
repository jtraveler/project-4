"""
Tests for the source_image_paste_upload endpoint (Session 133, SPEC 133_B).
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile


@override_settings(
    B2_ENDPOINT_URL='https://test.example.com',
    B2_ACCESS_KEY_ID='test-key',
    B2_SECRET_ACCESS_KEY='test-secret',
    B2_BUCKET_NAME='test-bucket',
    B2_CUSTOM_DOMAIN='cdn.test.example.com',
)
class PasteUploadTests(TestCase):
    """Tests for /api/bulk-gen/source-image-paste/ endpoint."""

    def setUp(self):
        self.url = reverse('prompts:source_image_paste_upload')
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='regularuser', password='testpass', is_staff=False,
        )

    def test_paste_upload_staff_only(self):
        """Non-staff POST returns 403."""
        self.client.login(username='regularuser', password='testpass')
        tiny_png = SimpleUploadedFile('test.png', b'\x89PNG' + b'\x00' * 100,
                                     content_type='image/png')
        response = self.client.post(self.url, {'file': tiny_png})
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])

    def test_paste_upload_invalid_content_type(self):
        """Non-image file returns 400."""
        self.client.login(username='staffuser', password='testpass')
        text_file = SimpleUploadedFile('test.txt', b'hello world',
                                      content_type='text/html')
        response = self.client.post(self.url, {'file': text_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Invalid image type', data['error'])

    def test_paste_upload_size_limit(self):
        """File over 5MB returns 400."""
        self.client.login(username='staffuser', password='testpass')
        # 5MB + 1 byte
        big_file = SimpleUploadedFile('big.png', b'\x00' * (5 * 1024 * 1024 + 1),
                                     content_type='image/png')
        response = self.client.post(self.url, {'file': big_file})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('too large', data['error'])
