"""
Tests for the Notification system (Phase R1).

Covers: model, service layer, signal handlers, template tag,
        API endpoints (R1-B), notifications page (R1-C).
"""
from datetime import timedelta
from unittest.mock import MagicMock

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.utils import timezone

from prompts.models import (
    Collection, CollectionItem, Comment, Follow, Notification,
    NOTIFICATION_TYPE_CATEGORY_MAP, Prompt,
)
from prompts.services.notifications import (
    create_notification, get_unread_count, get_unread_count_by_category,
    mark_all_as_read, mark_as_read,
)


class NotificationTestBase(TestCase):
    """Shared setup for notification tests."""

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user('alice', 'alice@example.com', 'pass')
        cls.user2 = User.objects.create_user('bob', 'bob@example.com', 'pass')
        cls.user3 = User.objects.create_user('carol', 'carol@example.com', 'pass')
        cls.prompt = Prompt.objects.create(
            title='Test Prompt',
            slug='test-prompt',
            author=cls.user1,
            excerpt='Test excerpt',
            status=1,  # published
        )


# ═══════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════

class TestNotificationModel(NotificationTestBase):
    """Tests for the Notification model."""

    def test_notification_creation(self):
        """Basic create with all fields."""
        n = Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            category='likes',
            title='Bob liked your prompt',
            message='Some message',
            link='/prompt/test/',
        )
        self.assertEqual(n.recipient, self.user1)
        self.assertEqual(n.sender, self.user2)
        self.assertFalse(n.is_read)
        self.assertFalse(n.is_admin_notification)
        self.assertIsNotNone(n.created_at)

    def test_notification_str(self):
        """String representation includes type display and recipient."""
        n = Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            category='likes',
            title='Bob liked your prompt',
        )
        self.assertIn('alice', str(n))
        self.assertIn('Liked your prompt', str(n))

    def test_notification_ordering(self):
        """Newest notifications come first."""
        n1 = Notification.objects.create(
            recipient=self.user1,
            notification_type='system',
            category='system',
            title='First',
        )
        n2 = Notification.objects.create(
            recipient=self.user1,
            notification_type='system',
            category='system',
            title='Second',
        )
        notifications = list(Notification.objects.filter(recipient=self.user1))
        self.assertEqual(notifications[0].id, n2.id)
        self.assertEqual(notifications[1].id, n1.id)

    def test_notification_mark_as_read(self):
        """mark_as_read() sets is_read=True."""
        n = Notification.objects.create(
            recipient=self.user1,
            notification_type='system',
            category='system',
            title='Test',
        )
        self.assertFalse(n.is_read)
        n.mark_as_read()
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_as_read_idempotent(self):
        """Calling mark_as_read() on already-read notification is harmless."""
        n = Notification.objects.create(
            recipient=self.user1,
            notification_type='system',
            category='system',
            title='Test',
            is_read=True,
        )
        n.mark_as_read()  # should not error
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_notification_cascade_delete_recipient(self):
        """Deleting a user deletes their notifications."""
        temp_user = User.objects.create_user('temp', 'temp@x.com', 'pass')
        Notification.objects.create(
            recipient=temp_user,
            notification_type='system',
            category='system',
            title='Test',
        )
        user_id = temp_user.id
        self.assertEqual(
            Notification.objects.filter(recipient_id=user_id).count(), 1
        )
        temp_user.delete()
        self.assertEqual(
            Notification.objects.filter(recipient_id=user_id).count(), 0
        )

    def test_notification_system_type_no_sender(self):
        """System notifications can have null sender."""
        n = Notification.objects.create(
            recipient=self.user1,
            sender=None,
            notification_type='system',
            category='system',
            title='System message',
        )
        self.assertIsNone(n.sender)

    def test_type_category_map_complete(self):
        """Every NotificationType has a mapping in NOTIFICATION_TYPE_CATEGORY_MAP."""
        for choice_value, _ in Notification.NotificationType.choices:
            self.assertIn(
                choice_value, NOTIFICATION_TYPE_CATEGORY_MAP,
                f"Missing mapping for {choice_value}"
            )


# ═══════════════════════════════════════════════════
# SERVICE TESTS
# ═══════════════════════════════════════════════════

class TestNotificationService(NotificationTestBase):
    """Tests for the notification service module."""

    def test_create_notification_happy_path(self):
        """Create notification returns the instance."""
        n = create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Bob liked your prompt',
            link='/prompt/test/',
        )
        self.assertIsNotNone(n)
        self.assertEqual(n.recipient, self.user1)
        self.assertEqual(n.category, 'likes')

    def test_no_self_notification(self):
        """sender == recipient returns None."""
        n = create_notification(
            recipient=self.user1,
            sender=self.user1,
            notification_type='prompt_liked',
            title='You liked your own prompt',
        )
        self.assertIsNone(n)
        self.assertEqual(
            Notification.objects.filter(recipient=self.user1).count(), 0
        )

    def test_inactive_recipient_skipped(self):
        """Inactive user doesn't receive notifications."""
        self.user3.is_active = False
        self.user3.save()
        n = create_notification(
            recipient=self.user3,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Test',
        )
        self.assertIsNone(n)
        self.user3.is_active = True
        self.user3.save()

    def test_duplicate_prevention(self):
        """Same notification within 60s returns None."""
        n1 = create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Bob liked your prompt',
        )
        self.assertIsNotNone(n1)
        n2 = create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Bob liked your prompt',
        )
        self.assertIsNone(n2)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1, notification_type='prompt_liked'
            ).count(),
            1,
        )

    def test_different_types_not_duplicate(self):
        """Different notification types from same sender are not duplicates."""
        n1 = create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Liked',
        )
        n2 = create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Followed',
        )
        self.assertIsNotNone(n1)
        self.assertIsNotNone(n2)

    def test_unknown_type_returns_none(self):
        """Unknown notification type returns None."""
        n = create_notification(
            recipient=self.user1,
            notification_type='nonexistent_type',
            title='Test',
        )
        self.assertIsNone(n)

    def test_get_unread_count(self):
        """Returns correct unread count."""
        create_notification(
            recipient=self.user1,
            notification_type='system',
            title='One',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Two',
        )
        self.assertEqual(get_unread_count(self.user1), 2)

    def test_get_unread_count_excludes_read(self):
        """Read notifications not counted."""
        n = create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        n.mark_as_read()
        self.assertEqual(get_unread_count(self.user1), 0)

    def test_get_unread_count_anonymous(self):
        """Anonymous user returns 0."""
        self.assertEqual(get_unread_count(None), 0)

    def test_get_unread_count_by_category(self):
        """Returns correct per-category counts."""
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like 1',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user3,
            notification_type='prompt_liked',
            title='Like 2',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Follow',
        )
        counts = get_unread_count_by_category(self.user1)
        self.assertEqual(counts['likes'], 2)
        self.assertEqual(counts['follows'], 1)
        self.assertEqual(counts['comments'], 0)

    def test_mark_as_read_service(self):
        """mark_as_read() marks single notification."""
        n = create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        result = mark_as_read(n.id, self.user1)
        self.assertTrue(result)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_mark_as_read_wrong_user(self):
        """Can't mark another user's notification."""
        n = create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        result = mark_as_read(n.id, self.user2)
        self.assertFalse(result)
        n.refresh_from_db()
        self.assertFalse(n.is_read)

    def test_mark_all_as_read(self):
        """Bulk mark all as read."""
        create_notification(
            recipient=self.user1,
            notification_type='system',
            title='One',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Two',
        )
        count = mark_all_as_read(self.user1)
        self.assertEqual(count, 2)
        self.assertEqual(get_unread_count(self.user1), 0)

    def test_mark_all_as_read_by_category(self):
        """Category-filtered mark all as read."""
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Follow',
        )
        count = mark_all_as_read(self.user1, category='likes')
        self.assertEqual(count, 1)
        self.assertEqual(get_unread_count(self.user1), 1)  # follow still unread


# ═══════════════════════════════════════════════════
# SIGNAL TESTS
# ═══════════════════════════════════════════════════

class TestNotificationSignals(NotificationTestBase):
    """Tests for signal-based notification creation."""

    def test_comment_creates_notification(self):
        """New comment notifies prompt author."""
        Comment.objects.create(
            prompt=self.prompt,
            author=self.user2,
            body='Great prompt!',
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='comment_on_prompt',
            ).count(),
            1,
        )

    def test_comment_no_self_notification(self):
        """Author commenting on own prompt gets no notification."""
        Comment.objects.create(
            prompt=self.prompt,
            author=self.user1,  # author == prompt.author
            body='My own comment',
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='comment_on_prompt',
            ).count(),
            0,
        )

    def test_comment_notification_has_link(self):
        """Comment notification links to the prompt."""
        Comment.objects.create(
            prompt=self.prompt,
            author=self.user2,
            body='Nice!',
        )
        n = Notification.objects.get(
            recipient=self.user1, notification_type='comment_on_prompt'
        )
        self.assertIn(self.prompt.slug, n.link)

    def test_comment_update_no_duplicate(self):
        """Updating existing comment doesn't create new notification."""
        comment = Comment.objects.create(
            prompt=self.prompt,
            author=self.user2,
            body='Original',
        )
        comment.body = 'Updated'
        comment.save()
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='comment_on_prompt',
            ).count(),
            1,
        )

    def test_like_creates_notification(self):
        """New like notifies prompt author."""
        self.prompt.likes.add(self.user2)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='prompt_liked',
            ).count(),
            1,
        )

    def test_like_no_self_notification(self):
        """Author liking own prompt gets no notification."""
        self.prompt.likes.add(self.user1)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='prompt_liked',
            ).count(),
            0,
        )

    def test_like_remove_no_notification(self):
        """Removing a like does not create notification."""
        self.prompt.likes.add(self.user2)
        initial_count = Notification.objects.filter(
            recipient=self.user1, notification_type='prompt_liked'
        ).count()
        self.prompt.likes.remove(self.user2)
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1, notification_type='prompt_liked'
            ).count(),
            initial_count,
        )

    def test_follow_creates_notification(self):
        """Follow notifies the followed user."""
        Follow.objects.create(
            follower=self.user2,
            following=self.user1,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='new_follower',
            ).count(),
            1,
        )

    def test_follow_notification_links_to_follower_profile(self):
        """Follow notification links to the follower's profile."""
        Follow.objects.create(
            follower=self.user2,
            following=self.user1,
        )
        n = Notification.objects.get(
            recipient=self.user1, notification_type='new_follower'
        )
        self.assertIn(self.user2.username, n.link)

    def test_collection_save_creates_notification(self):
        """Saving prompt to public collection notifies prompt author."""
        collection = Collection.objects.create(
            user=self.user2,
            title='My Collection',
            slug='my-collection',
            is_private=False,
        )
        CollectionItem.objects.create(
            collection=collection,
            prompt=self.prompt,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='prompt_saved',
            ).count(),
            1,
        )

    def test_collection_save_private_no_notification(self):
        """Private collection save does NOT notify prompt author."""
        collection = Collection.objects.create(
            user=self.user2,
            title='Private Collection',
            slug='private-collection',
            is_private=True,
        )
        CollectionItem.objects.create(
            collection=collection,
            prompt=self.prompt,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='prompt_saved',
            ).count(),
            0,
        )

    def test_collection_save_own_prompt_no_notification(self):
        """Saving own prompt to collection doesn't notify."""
        collection = Collection.objects.create(
            user=self.user1,  # same as prompt author
            title='My Saves',
            slug='my-saves',
            is_private=False,
        )
        CollectionItem.objects.create(
            collection=collection,
            prompt=self.prompt,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.user1,
                notification_type='prompt_saved',
            ).count(),
            0,
        )


# ═══════════════════════════════════════════════════
# TEMPLATE TAG TESTS
# ═══════════════════════════════════════════════════

class TestNotificationTemplateTag(NotificationTestBase):
    """Tests for the unread_notification_count template tag."""

    def test_unread_count_tag(self):
        """Returns correct count for authenticated user."""
        create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user1
        template = Template(
            '{% load notification_tags %}'
            '{% unread_notification_count as count %}'
            '{{ count }}'
        )
        context = Context({'request': request})
        rendered = template.render(context)
        self.assertEqual(rendered.strip(), '1')

    def test_unread_count_anonymous(self):
        """Returns 0 for anonymous users."""
        from django.contrib.auth.models import AnonymousUser
        factory = RequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()
        template = Template(
            '{% load notification_tags %}'
            '{% unread_notification_count as count %}'
            '{{ count }}'
        )
        context = Context({'request': request})
        rendered = template.render(context)
        self.assertEqual(rendered.strip(), '0')



# ═══════════════════════════════════════════════════
# API ENDPOINT TESTS (Phase R1-B)
# ═══════════════════════════════════════════════════

class TestUnreadCountAPI(NotificationTestBase):
    """Tests for GET /api/notifications/unread-count/."""

    def test_returns_counts(self):
        """Returns total and per-category counts."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Follow',
        )
        response = self.client.get(
            reverse('prompts:notification_unread_count_api')
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 2)
        self.assertEqual(data['categories']['likes'], 1)
        self.assertEqual(data['categories']['follows'], 1)
        self.assertEqual(data['categories']['comments'], 0)

    def test_requires_login(self):
        """Anonymous request redirects to login."""
        response = self.client.get(
            reverse('prompts:notification_unread_count_api')
        )
        self.assertEqual(response.status_code, 302)

    def test_post_not_allowed(self):
        """POST returns 405."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('prompts:notification_unread_count_api')
        )
        self.assertEqual(response.status_code, 405)

    def test_zero_when_empty(self):
        """Returns 0 when no notifications exist."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse('prompts:notification_unread_count_api')
        )
        data = response.json()
        self.assertEqual(data['total'], 0)


class TestMarkAllReadAPI(NotificationTestBase):
    """Tests for POST /api/notifications/mark-all-read/."""

    def test_marks_all_read(self):
        """Marks all notifications as read."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            notification_type='system',
            title='One',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Two',
        )
        response = self.client.post(
            reverse('prompts:notification_mark_all_read_api')
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['marked'], 2)
        self.assertEqual(get_unread_count(self.user1), 0)

    def test_marks_by_category(self):
        """Category filter only marks that category."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Follow',
        )
        response = self.client.post(
            reverse('prompts:notification_mark_all_read_api') + '?category=likes'
        )
        data = response.json()
        self.assertEqual(data['marked'], 1)
        self.assertEqual(get_unread_count(self.user1), 1)

    def test_requires_login(self):
        """Anonymous request redirects."""
        response = self.client.post(
            reverse('prompts:notification_mark_all_read_api')
        )
        self.assertEqual(response.status_code, 302)

    def test_get_not_allowed(self):
        """GET returns 405."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse('prompts:notification_mark_all_read_api')
        )
        self.assertEqual(response.status_code, 405)


class TestMarkReadAPI(NotificationTestBase):
    """Tests for POST /api/notifications/<id>/read/."""

    def test_marks_single_read(self):
        """Marks a specific notification as read."""
        self.client.force_login(self.user1)
        n = create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        response = self.client.post(
            reverse('prompts:notification_mark_read_api', args=[n.id])
        )
        self.assertEqual(response.status_code, 200)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_wrong_user_gets_404(self):
        """Can't mark another user's notification."""
        self.client.force_login(self.user2)
        n = create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        response = self.client.post(
            reverse('prompts:notification_mark_read_api', args=[n.id])
        )
        self.assertEqual(response.status_code, 404)
        n.refresh_from_db()
        self.assertFalse(n.is_read)

    def test_nonexistent_notification(self):
        """Non-existent ID returns 404."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('prompts:notification_mark_read_api', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_requires_login(self):
        """Anonymous request redirects."""
        response = self.client.post(
            reverse('prompts:notification_mark_read_api', args=[1])
        )
        self.assertEqual(response.status_code, 302)


class TestNotificationsPage(NotificationTestBase):
    """Tests for GET /notifications/ page."""

    def test_page_loads(self):
        """Notifications page returns 200 for logged-in user."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('prompts:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'prompts/notifications.html')

    def test_requires_login(self):
        """Anonymous users get redirected."""
        response = self.client.get(reverse('prompts:notifications'))
        self.assertEqual(response.status_code, 302)

    def test_defaults_to_comments_category(self):
        """Page defaults to comments category when no param provided."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse('prompts:notifications'))
        self.assertEqual(response.context['active_category'], 'comments')

    def test_shows_notifications(self):
        """Notifications appear in context for the active category."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Bob started following you',
        )
        response = self.client.get(
            reverse('prompts:notifications') + '?category=follows'
        )
        self.assertEqual(len(response.context['notifications']), 1)

    def test_category_filter(self):
        """Category query param filters notifications."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like',
        )
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='new_follower',
            title='Follow',
        )
        response = self.client.get(
            reverse('prompts:notifications') + '?category=likes'
        )
        self.assertEqual(len(response.context['notifications']), 1)
        self.assertEqual(response.context['active_category'], 'likes')

    def test_invalid_category_defaults_to_comments(self):
        """Invalid category param falls back to comments."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            notification_type='system',
            title='Test',
        )
        response = self.client.get(
            reverse('prompts:notifications') + '?category=invalid'
        )
        self.assertEqual(response.context['active_category'], 'comments')
        # System notification not shown when viewing comments
        self.assertEqual(len(response.context['notifications']), 0)

    def test_only_own_notifications(self):
        """User only sees their own notifications."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user2,
            notification_type='system',
            title='Not mine',
        )
        response = self.client.get(reverse('prompts:notifications'))
        self.assertEqual(len(response.context['notifications']), 0)

    def test_context_has_category_tabs(self):
        """Response context includes category tabs with unread counts."""
        self.client.force_login(self.user1)
        create_notification(
            recipient=self.user1,
            sender=self.user2,
            notification_type='prompt_liked',
            title='Like',
        )
        response = self.client.get(reverse('prompts:notifications'))
        self.assertIn('category_tabs', response.context)
        likes_tab = next(
            t for t in response.context['category_tabs'] if t['value'] == 'likes'
        )
        self.assertEqual(likes_tab['count'], 1)
