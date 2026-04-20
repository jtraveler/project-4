"""
Regression tests for 163-B UserProfile schema change.

Migration 0085 dropped `UserProfile.avatar` (CloudinaryField),
renamed `b2_avatar_url` → `avatar_url`, and added `avatar_source`
CharField with choices. Admin + form + signals were updated
accordingly.

These tests guard against:
- Schema regressions (field set, presence / absence of specific
  fields).
- `avatar_source` choices enforcement.
- UserProfileAdmin list + detail pages rendering without 500
  (163-A Gotcha 10 regression).

v2 note: these tests WILL FAIL until migration 0085 is applied.
That's expected during Phase 1 and becomes green in Phase 3 once
the developer runs the migration.
"""
from __future__ import annotations

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from prompts.models import UserProfile


class UserProfileSchema163BTests(TestCase):
    """Migration 0085 introduced avatar_url + avatar_source, removed
    avatar. Verify the schema exposed by the ORM matches."""

    def test_userprofile_has_avatar_url_field(self):
        user = User.objects.create_user(username='schema_163b_url')
        profile = user.userprofile
        self.assertTrue(
            hasattr(profile, 'avatar_url'),
            'UserProfile missing avatar_url after 163-B',
        )
        # Paired negative: old field name is gone
        self.assertFalse(
            hasattr(profile, 'b2_avatar_url'),
            'UserProfile still exposes b2_avatar_url; rename incomplete',
        )

    def test_userprofile_has_avatar_source_with_default(self):
        user = User.objects.create_user(username='schema_163b_source')
        profile = user.userprofile
        self.assertTrue(hasattr(profile, 'avatar_source'))
        self.assertEqual(profile.avatar_source, 'default')

    def test_userprofile_no_longer_has_avatar_cloudinary_field(self):
        user = User.objects.create_user(username='schema_163b_noavatar')
        profile = user.userprofile
        field_names = {f.name for f in UserProfile._meta.fields}
        self.assertIn('avatar_url', field_names)        # positive
        self.assertIn('avatar_source', field_names)     # positive
        self.assertNotIn('avatar', field_names)         # paired negative
        self.assertNotIn('b2_avatar_url', field_names)  # paired negative


class AvatarSourceChoicesTests(TestCase):
    """163-B avatar_source must reject values outside the choices list."""

    def test_avatar_source_accepts_valid_choices(self):
        user = User.objects.create_user(username='choices_valid')
        profile = user.userprofile
        for source in ('default', 'direct', 'google', 'facebook', 'apple'):
            profile.avatar_source = source
            # Should not raise
            profile.full_clean()

    def test_avatar_source_rejects_invalid_choice(self):
        user = User.objects.create_user(username='choices_invalid')
        profile = user.userprofile
        profile.avatar_source = 'twitter'  # not in choices
        with self.assertRaises(ValidationError):
            profile.full_clean()


class UserProfileAdminRendersTests(TestCase):
    """163-A Gotcha 10 regression guard: admin must not 500 after the
    CloudinaryField drop + fieldset rewrite."""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_163b',
            email='admin163b@example.com',
            password='adminpass',
        )
        self.client.force_login(self.admin_user)

    def test_admin_userprofile_list_renders(self):
        url = reverse('admin:prompts_userprofile_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Paired: page contains the admin list header
        self.assertContains(response, 'User Profile')

    def test_admin_userprofile_detail_renders(self):
        profile = self.admin_user.userprofile
        url = reverse(
            'admin:prompts_userprofile_change', args=[profile.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Paired: the new fieldset label from 163-B is present
        self.assertContains(response, 'Avatar')
        # And the new field names
        self.assertContains(response, 'Avatar url')
        self.assertContains(response, 'Avatar source')
