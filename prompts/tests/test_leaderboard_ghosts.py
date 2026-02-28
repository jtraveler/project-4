"""
Tests for leaderboard ghost entry fixes.

Ensures deleted users, draft-only users, and soft-deleted prompts
are excluded from leaderboard results.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from prompts.models import Comment, Prompt
from prompts.services.leaderboard import LeaderboardService


class LeaderboardGhostTests(TestCase):
    """Tests that ghost entries are excluded from leaderboard results."""

    def setUp(self):
        """Create base users and prompts for leaderboard testing."""
        # Active user with a published prompt
        self.active_user = User.objects.create_user(
            username='active_user', password='testpass123',
        )
        self.published_prompt = Prompt.objects.create(
            title='Published Prompt',
            slug='published-prompt',
            content='test content',
            author=self.active_user,
            status=1,
        )

    def test_deleted_user_excluded_from_most_viewed(self):
        """Users with is_active=False should not appear on Most Viewed."""
        deleted_user = User.objects.create_user(
            username='deleted_user', password='testpass123',
            is_active=False,
        )
        prompt = Prompt.objects.create(
            title='Deleted User Prompt',
            slug='deleted-user-prompt',
            content='test',
            author=deleted_user,
            status=1,
        )
        # Add a view to give them a score
        prompt.views.create(
            user=self.active_user,
            ip_hash='abc123',
            viewed_at=timezone.now(),
        )

        results = LeaderboardService.get_most_viewed(period='all')
        result_ids = [u.id for u in results]
        self.assertNotIn(deleted_user.id, result_ids)

    def test_deleted_user_excluded_from_most_active(self):
        """Users with is_active=False should not appear on Most Active."""
        deleted_user = User.objects.create_user(
            username='deleted_user', password='testpass123',
            is_active=False,
        )
        Prompt.objects.create(
            title='Deleted User Prompt',
            slug='deleted-user-prompt',
            content='test',
            author=deleted_user,
            status=1,
        )

        results = LeaderboardService.get_most_active(period='all')
        result_ids = [u.id for u in results]
        self.assertNotIn(deleted_user.id, result_ids)

    def test_draft_only_user_excluded_from_most_active(self):
        """Users with only draft prompts should not appear on Most Active."""
        draft_user = User.objects.create_user(
            username='draft_user', password='testpass123',
        )
        # Only a draft prompt (status=0)
        Prompt.objects.create(
            title='Draft Only Prompt',
            slug='draft-only-prompt',
            content='test',
            author=draft_user,
            status=0,
        )
        # Give them activity via a comment on another user's prompt
        Comment.objects.create(
            prompt=self.published_prompt,
            author=draft_user,
            body='Nice prompt!',
            approved=True,
        )

        results = LeaderboardService.get_most_active(period='all')
        result_ids = [u.id for u in results]
        self.assertNotIn(draft_user.id, result_ids)

    def test_mixed_content_user_included(self):
        """Users with at least 1 published prompt should appear on Most Active."""
        mixed_user = User.objects.create_user(
            username='mixed_user', password='testpass123',
        )
        # One draft, one published
        Prompt.objects.create(
            title='Draft Prompt Mixed',
            slug='draft-prompt-mixed',
            content='test',
            author=mixed_user,
            status=0,
        )
        Prompt.objects.create(
            title='Published Prompt Mixed',
            slug='published-prompt-mixed',
            content='test',
            author=mixed_user,
            status=1,
        )

        results = LeaderboardService.get_most_active(period='all')
        result_ids = [u.id for u in results]
        self.assertIn(mixed_user.id, result_ids)

    def test_soft_deleted_prompts_excluded(self):
        """Users whose prompts are all soft-deleted should not appear."""
        soft_del_user = User.objects.create_user(
            username='softdel_user', password='testpass123',
        )
        Prompt.objects.create(
            title='Soft Deleted Prompt',
            slug='soft-deleted-prompt',
            content='test',
            author=soft_del_user,
            status=1,
            deleted_at=timezone.now(),
        )
        # Give them activity via a like
        self.published_prompt.likes.add(soft_del_user)

        results = LeaderboardService.get_most_active(period='all')
        result_ids = [u.id for u in results]
        self.assertNotIn(soft_del_user.id, result_ids)

    def test_soft_deleted_prompts_excluded_from_most_viewed(self):
        """Soft-deleted prompt views should not count on Most Viewed."""
        user = User.objects.create_user(
            username='softdel_viewed_user', password='testpass123',
        )
        prompt = Prompt.objects.create(
            title='Soft Del Viewed',
            slug='soft-del-viewed',
            content='test',
            author=user,
            status=1,
            deleted_at=timezone.now(),
        )
        prompt.views.create(
            user=self.active_user,
            ip_hash='def456',
            viewed_at=timezone.now(),
        )

        results = LeaderboardService.get_most_viewed(period='all')
        result_ids = [u.id for u in results]
        self.assertNotIn(user.id, result_ids)
