"""
Optional Enhancements for UserProfile Model

These are production-ready code snippets you can integrate into your
UserProfile implementation. Each enhancement is optional but recommended
for a polished production experience.

Copy the relevant methods into prompts/models.py (UserProfile class)
and signal handlers into prompts/signals.py.
"""

import re
import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
import cloudinary.uploader

logger = logging.getLogger(__name__)


# =============================================================================
# ENHANCEMENT 1: Profile Completeness Tracker (Add to UserProfile model)
# =============================================================================

def get_profile_completion(self):
    """
    Calculate profile completion percentage for onboarding UX.

    Helps track user onboarding progress and encourage profile completion.
    Used in dashboard widgets, profile settings, and completion badges.

    Returns:
        int: Completion percentage (0-100)

    Example:
        profile = user.userprofile
        completion = profile.get_profile_completion()  # 60
        if completion < 100:
            show_completion_prompt(user)
    """
    fields_to_check = {
        'bio': bool(self.bio),
        'avatar': bool(self.avatar),
        'website_url': bool(self.website_url),
        'twitter_url': bool(self.twitter_url),
        'instagram_url': bool(self.instagram_url),
    }

    filled_count = sum(fields_to_check.values())
    total_fields = len(fields_to_check)

    return int((filled_count / total_fields) * 100)


def is_profile_complete(self):
    """
    Check if profile meets minimum completion threshold (60%).

    Property method for easy template usage:
    {% if user.userprofile.is_profile_complete %}
        <span class="badge badge-success">Complete Profile</span>
    {% endif %}

    Returns:
        bool: True if profile is at least 60% complete
    """
    return self.get_profile_completion() >= 60


# =============================================================================
# ENHANCEMENT 2: Social Handle Extractors (Add to UserProfile model)
# =============================================================================

def has_social_links(self):
    """
    Check if user has any social media links configured.

    Property method for conditional rendering in templates:
    {% if user.userprofile.has_social_links %}
        <div class="social-links">...</div>
    {% endif %}

    Returns:
        bool: True if user has Twitter or Instagram URL
    """
    return bool(self.twitter_url or self.instagram_url)


def twitter_handle(self):
    """
    Extract Twitter handle from URL for cleaner display.

    Converts 'https://twitter.com/username' to '@username'
    Handles various Twitter URL formats.

    Returns:
        str: Twitter handle with @ symbol, or None if no URL

    Example:
        profile.twitter_url = "https://twitter.com/promptfinder"
        profile.twitter_handle  # Returns "@promptfinder"
    """
    if self.twitter_url:
        # Match twitter.com/username or x.com/username
        match = re.search(r'(?:twitter|x)\.com/([^/?]+)', self.twitter_url)
        if match:
            return f"@{match.group(1)}"
    return None


def instagram_handle(self):
    """
    Extract Instagram handle from URL for cleaner display.

    Converts 'https://instagram.com/username' to '@username'

    Returns:
        str: Instagram handle with @ symbol, or None if no URL

    Example:
        profile.instagram_url = "https://instagram.com/promptfinder"
        profile.instagram_handle  # Returns "@promptfinder"
    """
    if self.instagram_url:
        match = re.search(r'instagram\.com/([^/?]+)', self.instagram_url)
        if match:
            return f"@{match.group(1)}"
    return None


# =============================================================================
# ENHANCEMENT 3: Avatar Cleanup Signal (Add to prompts/signals.py)
# =============================================================================

@receiver(pre_save, sender=UserProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    """
    Delete old Cloudinary avatar when user uploads a new one.

    Prevents orphaned avatar files from accumulating in Cloudinary storage.
    Only deletes if avatar actually changed (not on every save).

    This is similar to the Prompt cleanup signal but for user avatars.

    Args:
        sender: The model class (UserProfile)
        instance: The UserProfile instance being saved
        **kwargs: Additional signal arguments

    Example:
        # User uploads new avatar
        profile.avatar = new_cloudinary_file
        profile.save()  # Signal fires, old avatar deleted from Cloudinary
    """
    if not instance.pk:
        return  # New profile, no old avatar to delete

    try:
        # Get the current version from database
        old_profile = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return  # Profile doesn't exist yet

    # Check if avatar actually changed
    old_avatar = old_profile.avatar
    new_avatar = instance.avatar

    # Compare Cloudinary public_ids (None-safe)
    old_public_id = old_avatar.public_id if old_avatar else None
    new_public_id = new_avatar.public_id if new_avatar else None

    if old_public_id and old_public_id != new_public_id:
        try:
            # Delete old avatar from Cloudinary
            result = cloudinary.uploader.destroy(
                old_public_id,
                invalidate=True  # Clear CDN cache
            )
            logger.info(
                f"Deleted old avatar for user {instance.user.username}: "
                f"{old_public_id} (result: {result})"
            )
        except Exception as e:
            # Log error but don't block the save operation
            logger.error(
                f"Failed to delete old avatar for user {instance.user.username}: {e}",
                exc_info=True
            )


# =============================================================================
# ENHANCEMENT 4: Data Migration Template
# =============================================================================

"""
Create this migration with:
    python manage.py makemigrations --empty prompts --name create_missing_user_profiles

Then paste the migration code below:
"""

MIGRATION_TEMPLATE = '''
# prompts/migrations/XXXX_create_missing_user_profiles.py

from django.db import migrations


def create_profiles_for_existing_users(apps, schema_editor):
    """
    Create UserProfile for all existing users who don't have one.

    This is a one-time data migration to ensure all users have profiles.
    New users will get profiles automatically via signal handler.
    """
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('prompts', 'UserProfile')

    # Find users without profiles
    users_without_profiles = User.objects.filter(userprofile__isnull=True)

    # Bulk create profiles
    profiles_to_create = [
        UserProfile(user=user) for user in users_without_profiles
    ]

    if profiles_to_create:
        created = UserProfile.objects.bulk_create(profiles_to_create)
        print(f"Created {len(created)} user profiles for existing users")
    else:
        print("All users already have profiles")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - delete profiles created by this migration.

    WARNING: This will delete user profile data!
    Only use in development/testing.
    """
    # You could delete profiles here, but it's safer to leave them
    # Just mark this as irreversible if needed
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('prompts', 'XXXX_userprofile'),  # Replace with your UserProfile migration number
    ]

    operations = [
        migrations.RunPython(
            create_profiles_for_existing_users,
            reverse_migration
        ),
    ]
'''


# =============================================================================
# ENHANCEMENT 5: View Optimization Helper
# =============================================================================

"""
Example view optimizations using select_related() to prevent N+1 queries.

BEFORE (N+1 queries):
    users = User.objects.all()
    for user in users:
        print(user.userprofile.bio)  # Triggers query per user!

AFTER (Single query):
    users = User.objects.select_related('userprofile').all()
    for user in users:
        print(user.userprofile.bio)  # No extra queries
"""

# Example for user list view
def user_list_view(request):
    """
    Display list of users with their profiles.

    Optimized to avoid N+1 queries by using select_related.
    """
    users = User.objects.select_related('userprofile').all()

    return render(request, 'users/list.html', {
        'users': users
    })


# Example for author display in prompt list
def prompt_list_view(request):
    """
    Display prompts with author profile information.

    Uses select_related to fetch author and their profile in single query.
    """
    prompts = Prompt.objects.select_related(
        'author',
        'author__userprofile'
    ).filter(status=1, deleted_at__isnull=True)

    return render(request, 'prompts/list.html', {
        'prompts': prompts
    })


# =============================================================================
# ENHANCEMENT 6: Template Safety Patterns
# =============================================================================

TEMPLATE_EXAMPLES = '''
<!-- Profile display with fallbacks -->
<div class="user-card">
    <h3>{{ user.username }}</h3>

    <!-- Bio with fallback -->
    <p>{{ user.userprofile.bio|default:"No bio provided" }}</p>

    <!-- Avatar with default -->
    {% if user.userprofile.avatar %}
        <img src="{{ user.userprofile.avatar.url }}" alt="{{ user.username }}'s avatar">
    {% else %}
        <div class="default-avatar avatar-color-{{ user.userprofile.get_avatar_color_index }}">
            {{ user.username|slice:":1"|upper }}
        </div>
    {% endif %}

    <!-- Social links (conditional) -->
    {% if user.userprofile.has_social_links %}
        <div class="social-links">
            {% if user.userprofile.twitter_url %}
                <a href="{{ user.userprofile.twitter_url }}" target="_blank">
                    {{ user.userprofile.twitter_handle }}
                </a>
            {% endif %}
            {% if user.userprofile.instagram_url %}
                <a href="{{ user.userprofile.instagram_url }}" target="_blank">
                    {{ user.userprofile.instagram_handle }}
                </a>
            {% endif %}
        </div>
    {% endif %}

    <!-- Profile completion badge (for user's own profile) -->
    {% if user == request.user %}
        {% with completion=user.userprofile.get_profile_completion %}
            <div class="profile-completion">
                <div class="progress">
                    <div class="progress-bar" style="width: {{ completion }}%">
                        {{ completion }}%
                    </div>
                </div>
                {% if completion < 100 %}
                    <a href="{% url 'profile_edit' %}" class="btn btn-sm">
                        Complete Your Profile
                    </a>
                {% endif %}
            </div>
        {% endwith %}
    {% endif %}
</div>
'''


# =============================================================================
# ENHANCEMENT 7: Unit Test Examples
# =============================================================================

UNIT_TEST_TEMPLATE = '''
# prompts/tests/test_userprofile.py

from django.test import TestCase
from django.contrib.auth.models import User
from prompts.models import UserProfile


class UserProfileCreationTests(TestCase):
    """Test automatic UserProfile creation via signals"""

    def test_profile_created_on_user_creation(self):
        """Test that UserProfile is auto-created for new users"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Profile should exist
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertIsInstance(user.userprofile, UserProfile)

    def test_profile_not_duplicated_on_user_save(self):
        """Test that re-saving user doesn't create duplicate profiles"""
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        original_profile_id = user.userprofile.id

        # Save user again
        user.email = 'newemail@example.com'
        user.save()

        # Should still have same profile
        self.assertEqual(user.userprofile.id, original_profile_id)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)


class UserProfileMethodTests(TestCase):
    """Test UserProfile helper methods"""

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.profile = self.user.userprofile

    def test_avatar_color_consistency(self):
        """Test that same username always returns same color index"""
        color1 = self.profile.get_avatar_color_index()
        color2 = self.profile.get_avatar_color_index()

        self.assertEqual(color1, color2)
        self.assertIn(color1, range(1, 9))  # Between 1-8

    def test_profile_completion_empty(self):
        """Test completion percentage with empty profile"""
        completion = self.profile.get_profile_completion()
        self.assertEqual(completion, 0)
        self.assertFalse(self.profile.is_profile_complete())

    def test_profile_completion_partial(self):
        """Test completion percentage with some fields filled"""
        self.profile.bio = "Test bio"
        self.profile.website_url = "https://example.com"
        self.profile.save()

        completion = self.profile.get_profile_completion()
        self.assertEqual(completion, 40)  # 2 out of 5 fields

    def test_twitter_handle_extraction(self):
        """Test Twitter handle extraction from URL"""
        self.profile.twitter_url = "https://twitter.com/promptfinder"
        self.assertEqual(self.profile.twitter_handle, "@promptfinder")

    def test_instagram_handle_extraction(self):
        """Test Instagram handle extraction from URL"""
        self.profile.instagram_url = "https://instagram.com/promptfinder"
        self.assertEqual(self.profile.instagram_handle, "@promptfinder")

    def test_has_social_links(self):
        """Test social links detection"""
        self.assertFalse(self.profile.has_social_links)

        self.profile.twitter_url = "https://twitter.com/test"
        self.assertTrue(self.profile.has_social_links)
'''


# =============================================================================
# INTEGRATION CHECKLIST
# =============================================================================

INTEGRATION_CHECKLIST = """
## Integration Checklist

Follow these steps to integrate enhancements:

### 1. Add Methods to UserProfile Model (models.py)

Add these methods to your UserProfile class:
- [ ] get_profile_completion()
- [ ] is_profile_complete (property)
- [ ] has_social_links (property)
- [ ] twitter_handle (property)
- [ ] instagram_handle (property)

### 2. Add Signal to signals.py

Add to prompts/signals.py:
- [ ] delete_old_avatar_on_change signal handler
- [ ] Import pre_save from django.db.models.signals
- [ ] Import cloudinary.uploader

### 3. Create Data Migration

Run these commands:
```bash
python manage.py makemigrations --empty prompts --name create_missing_user_profiles
# Edit the migration file to add RunPython operation
python manage.py migrate
```

### 4. Optimize Views

Update these views to use select_related:
- [ ] User list view
- [ ] Prompt list view (for author profiles)
- [ ] Profile detail view
- [ ] Any view displaying multiple users

### 5. Update Templates

Add to templates:
- [ ] Profile completion widget (dashboard)
- [ ] Social handle display
- [ ] Default avatar with color system
- [ ] Profile completion badge

### 6. Add Tests

Create prompts/tests/test_userprofile.py:
- [ ] test_profile_created_on_user_creation
- [ ] test_profile_not_duplicated
- [ ] test_avatar_color_consistency
- [ ] test_profile_completion_*
- [ ] test_social_handle_extraction

### 7. Verify in Production

Before deploying:
- [ ] Test signal registration (create new user)
- [ ] Test profile completion calculation
- [ ] Test avatar upload/replacement
- [ ] Verify Cloudinary cleanup works
- [ ] Check query optimization (Django Debug Toolbar)
- [ ] Run all tests: `python manage.py test prompts.tests.test_userprofile`

---

**Estimated Integration Time:** 2-3 hours
**Priority:** Medium (nice-to-have enhancements, not critical)
**Risk:** Low (all backward-compatible additions)
"""

print(INTEGRATION_CHECKLIST)
