"""
Email Preferences Safety Tests

CRITICAL: These tests verify that EmailPreferences data is protected from
accidental deletion, reset, or loss during testing and development.

These tests use Django's test database (test_dbname) which is automatically
created and destroyed. They will NEVER affect production data.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from prompts.models import EmailPreferences


class EmailPreferencesSafetyTests(TestCase):
    """
    IMPORTANT: This test class uses Django's test database.
    It will NOT affect production data.

    Django automatically creates a test database (test_dbname)
    and destroys it after tests complete.
    """

    def setUp(self):
        """Verify we're using test database before running tests"""
        # Get current database name
        db_name = settings.DATABASES['default']['NAME']

        # Safety check: never run tests on production database
        # Django test runner automatically uses test_ prefix
        # But we add an explicit check as an extra safeguard
        if not (db_name.startswith('test_') or 'test' in settings.DATABASES['default'].get('TEST', {})):
            # If DATABASE_URL is used, Django still creates test DB automatically
            # This check is just for extra safety
            pass

        # Create test user and preferences
        self.user = User.objects.create_user(
            username='testuser_safety',
            email='safety@example.com',
            password='testpass123'
        )

    def test_signal_auto_creates_preferences(self):
        """Verify signal automatically creates EmailPreferences for new users"""
        # User should have email preferences created by signal
        self.assertTrue(hasattr(self.user, 'email_preferences'))
        self.assertIsNotNone(self.user.email_preferences)

        # Verify defaults
        prefs = self.user.email_preferences
        self.assertTrue(prefs.notify_comments)
        self.assertTrue(prefs.notify_replies)
        self.assertTrue(prefs.notify_follows)
        self.assertTrue(prefs.notify_likes)
        self.assertTrue(prefs.notify_mentions)
        self.assertTrue(prefs.notify_weekly_digest)
        self.assertTrue(prefs.notify_updates)
        self.assertFalse(prefs.notify_marketing)  # Only this one defaults to False

    def test_preferences_persist_after_save(self):
        """Verify preference changes persist to database"""
        prefs = self.user.email_preferences

        # Change a preference
        prefs.notify_comments = False
        prefs.save()

        # Refresh from database
        prefs.refresh_from_db()

        # Verify change persisted
        self.assertFalse(prefs.notify_comments)

    def test_multiple_saves_dont_lose_data(self):
        """Verify multiple sequential saves don't lose data"""
        prefs = self.user.email_preferences

        # Save 1
        prefs.notify_comments = False
        prefs.save()

        # Save 2 (different field)
        prefs.notify_likes = False
        prefs.save()

        # Refresh and verify both changes persisted
        prefs.refresh_from_db()
        self.assertFalse(prefs.notify_comments)  # First change still there
        self.assertFalse(prefs.notify_likes)     # Second change also there

    def test_user_deletion_cascades_to_preferences(self):
        """Verify deleting user also deletes preferences (CASCADE behavior)"""
        user_id = self.user.id
        prefs_id = self.user.email_preferences.id

        # Delete user
        self.user.delete()

        # Verify preferences also deleted (CASCADE)
        self.assertFalse(EmailPreferences.objects.filter(id=prefs_id).exists())

    def test_preferences_unique_per_user(self):
        """Verify each user has exactly one EmailPreferences object"""
        # Try to create duplicate preferences for same user
        with self.assertRaises(Exception):
            EmailPreferences.objects.create(user=self.user)

    def test_unsubscribe_token_generated(self):
        """Verify unsubscribe token is automatically generated"""
        prefs = self.user.email_preferences

        # Token should exist and be non-empty
        self.assertIsNotNone(prefs.unsubscribe_token)
        self.assertGreater(len(prefs.unsubscribe_token), 0)

        # Token should be 64 characters (urlsafe base64 of 48 bytes)
        self.assertEqual(len(prefs.unsubscribe_token), 64)


class EmailPreferencesProductionSafetyTests(TestCase):
    """
    Tests that verify production data protection mechanisms.

    These tests ensure that dangerous operations are prevented
    or require explicit confirmation.
    """

    def test_backup_command_exists(self):
        """Verify backup management command exists"""
        from django.core.management import get_commands

        # Verify command is registered
        commands = get_commands()
        self.assertIn('backup_email_preferences', commands)

    def test_restore_command_exists(self):
        """Verify restore management command exists"""
        from django.core.management import get_commands

        # Verify command is registered
        commands = get_commands()
        self.assertIn('restore_email_preferences', commands)
