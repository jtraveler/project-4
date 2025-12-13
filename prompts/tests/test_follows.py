import unittest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
import json

from prompts.models import Follow, UserProfile


class FollowSystemTestCase(TestCase):
    """Test suite for the follow/unfollow system"""

    def setUp(self):
        """Create test users and client"""
        self.client = Client()

        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )

        # Clear cache between tests
        cache.clear()

    def test_follow_user(self):
        """Test following another user"""
        self.client.login(username='testuser1', password='testpass123')

        response = self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'testuser2'})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['following'])
        self.assertEqual(data['follower_count'], 1)

        # Verify follow relationship exists
        self.assertTrue(
            Follow.objects.filter(
                follower=self.user1,
                following=self.user2
            ).exists()
        )

    def test_unfollow_user(self):
        """Test unfollowing a user"""
        # Create initial follow relationship
        Follow.objects.create(follower=self.user1, following=self.user2)

        self.client.login(username='testuser1', password='testpass123')

        response = self.client.post(
            reverse('prompts:unfollow_user', kwargs={'username': 'testuser2'})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['following'])
        self.assertEqual(data['follower_count'], 0)

        # Verify follow relationship removed
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user1,
                following=self.user2
            ).exists()
        )

    def test_cannot_follow_self(self):
        """Test that users cannot follow themselves"""
        self.client.login(username='testuser1', password='testpass123')

        response = self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'testuser1'})
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Cannot follow yourself', data['error'])

    def test_cannot_follow_twice(self):
        """Test that duplicate follows are prevented"""
        self.client.login(username='testuser1', password='testpass123')

        # First follow
        self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'testuser2'})
        )

        # Try to follow again
        response = self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'testuser2'})
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

        # Verify only one follow relationship
        self.assertEqual(
            Follow.objects.filter(
                follower=self.user1,
                following=self.user2
            ).count(),
            1
        )

    def test_follower_count_updates(self):
        """Test that follower counts update correctly"""
        # User1 follows User2
        Follow.objects.create(follower=self.user1, following=self.user2)
        # User3 follows User2
        Follow.objects.create(follower=self.user3, following=self.user2)

        # Check follower count
        self.assertEqual(self.user2.follower_set.count(), 2)
        self.assertEqual(self.user2.following_set.count(), 0)

        # Check following count
        self.assertEqual(self.user1.following_set.count(), 1)
        self.assertEqual(self.user1.follower_set.count(), 0)

    def test_follow_status_endpoint(self):
        """Test the follow status check endpoint"""
        Follow.objects.create(follower=self.user1, following=self.user2)

        self.client.login(username='testuser1', password='testpass123')

        response = self.client.get(
            reverse('prompts:follow_status', kwargs={'username': 'testuser2'})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['following'])
        self.assertEqual(data['follower_count'], 1)

    def test_profile_follow_methods(self):
        """Test UserProfile helper methods"""
        profile1 = self.user1.userprofile
        profile2 = self.user2.userprofile

        # Initially not following
        self.assertFalse(profile1.is_following(self.user2))
        self.assertFalse(profile2.is_followed_by(self.user1))

        # Create follow relationship
        Follow.objects.create(follower=self.user1, following=self.user2)

        # Now following
        self.assertTrue(profile1.is_following(self.user2))
        self.assertTrue(profile2.is_followed_by(self.user1))

        # Reverse relationship should be false
        self.assertFalse(profile2.is_following(self.user1))
        self.assertFalse(profile1.is_followed_by(self.user2))

    def test_follow_requires_authentication(self):
        """Test that following requires login"""
        response = self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'testuser2'})
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_follow_nonexistent_user(self):
        """Test following a user that doesn't exist"""
        self.client.login(username='testuser1', password='testpass123')

        response = self.client.post(
            reverse('prompts:follow_user', kwargs={'username': 'nonexistent'})
        )

        self.assertEqual(response.status_code, 404)

    def test_cascade_delete(self):
        """Test that follows are deleted when user is deleted"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user2, following=self.user3)

        # Save IDs before deletion
        user2_id = self.user2.id

        # Delete user2
        self.user2.delete()

        # All follows involving user2 should be gone (use ID, not deleted model instance)
        self.assertEqual(
            Follow.objects.filter(
                follower_id=user2_id
            ).count(),
            0
        )
        self.assertEqual(
            Follow.objects.filter(
                following_id=user2_id
            ).count(),
            0
        )

        # Follow between user1 and user3 should not exist
        self.assertFalse(
            Follow.objects.filter(
                follower=self.user1
            ).exists()
        )
