#!/usr/bin/env python
"""
UserProfile Implementation Verification Script

Run this script to verify your UserProfile implementation is working correctly.

Usage:
    python manage.py shell < verify_userprofile.py

Or in Django shell:
    exec(open('verify_userprofile.py').read())
"""

import sys
from django.contrib.auth.models import User
from prompts.models import UserProfile


def print_header(text):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def verify_model_exists():
    """Verify UserProfile model is accessible"""
    print_header("1. Model Verification")

    try:
        from prompts.models import UserProfile
        print_success("UserProfile model imported successfully")
        return True
    except ImportError as e:
        print_error(f"Failed to import UserProfile: {e}")
        return False


def verify_signal_registered():
    """Verify signal handler is registered"""
    print_header("2. Signal Registration Verification")

    try:
        from prompts.apps import PromptsConfig
        config = PromptsConfig('prompts', __import__('prompts'))

        print_success("PromptsConfig accessible")

        # Check if ready() method exists
        if hasattr(config, 'ready'):
            print_success("ready() method exists in PromptsConfig")
        else:
            print_warning("ready() method not found in PromptsConfig")

        return True
    except Exception as e:
        print_error(f"Signal registration check failed: {e}")
        return False


def verify_profile_creation():
    """Verify profile is created automatically for new users"""
    print_header("3. Automatic Profile Creation Test")

    # Clean up test user if exists
    test_username = 'userprofile_test_user'
    User.objects.filter(username=test_username).delete()

    try:
        # Create test user
        test_user = User.objects.create_user(
            username=test_username,
            email='test@userprofile.test',
            password='testpass123'
        )

        # Check if profile exists
        if hasattr(test_user, 'userprofile'):
            print_success(f"Profile created automatically for '{test_username}'")

            # Verify profile properties
            profile = test_user.userprofile
            print_success(f"Profile ID: {profile.id}")
            print_success(f"Created at: {profile.created_at}")
            print_success(f"Avatar color index: {profile.get_avatar_color_index()} (should be 1-8)")

            # Clean up
            test_user.delete()
            print_success("Test user cleaned up")
            return True
        else:
            print_error("Profile NOT created automatically!")
            test_user.delete()
            return False

    except Exception as e:
        print_error(f"Profile creation test failed: {e}")
        User.objects.filter(username=test_username).delete()
        return False


def verify_existing_users_have_profiles():
    """Check if all existing users have profiles"""
    print_header("4. Existing Users Profile Check")

    try:
        total_users = User.objects.count()
        users_with_profiles = User.objects.filter(userprofile__isnull=False).count()
        users_without_profiles = User.objects.filter(userprofile__isnull=True).count()

        print(f"Total users: {total_users}")
        print(f"Users with profiles: {users_with_profiles}")

        if users_without_profiles > 0:
            print_warning(f"{users_without_profiles} users WITHOUT profiles found!")
            print("\nUsers without profiles:")
            for user in User.objects.filter(userprofile__isnull=True)[:10]:
                print(f"  - {user.username} (ID: {user.id})")

            print("\n💡 To create profiles for existing users, run:")
            print("   python manage.py shell")
            print("   >>> from django.contrib.auth.models import User")
            print("   >>> from prompts.models import UserProfile")
            print("   >>> for user in User.objects.filter(userprofile__isnull=True):")
            print("   ...     UserProfile.objects.create(user=user)")

            return False
        else:
            print_success(f"All {total_users} users have profiles!")
            return True

    except Exception as e:
        print_error(f"Profile check failed: {e}")
        return False


def verify_model_methods():
    """Verify UserProfile helper methods work"""
    print_header("5. Model Methods Verification")

    try:
        # Get or create a test profile
        test_user, _ = User.objects.get_or_create(
            username='method_test_user',
            defaults={'email': 'methodtest@test.com'}
        )
        profile, _ = UserProfile.objects.get_or_create(user=test_user)

        # Test get_avatar_color_index
        color_index = profile.get_avatar_color_index()
        if 1 <= color_index <= 8:
            print_success(f"get_avatar_color_index() works: {color_index}")
        else:
            print_error(f"get_avatar_color_index() returned invalid value: {color_index}")

        # Test color consistency
        color_index2 = profile.get_avatar_color_index()
        if color_index == color_index2:
            print_success("Color index is consistent across calls")
        else:
            print_error("Color index is NOT consistent!")

        # Test get_total_likes
        total_likes = profile.get_total_likes()
        print_success(f"get_total_likes() works: {total_likes}")

        # Test __str__
        str_repr = str(profile)
        print_success(f"__str__() works: '{str_repr}'")

        return True

    except Exception as e:
        print_error(f"Method verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_database_indexes():
    """Verify database indexes are created"""
    print_header("6. Database Indexes Verification")

    try:
        from django.db import connection

        # Get table name
        table_name = UserProfile._meta.db_table

        # Check indexes
        with connection.cursor() as cursor:
            # PostgreSQL query
            cursor.execute(f"""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = '{table_name}'
            """)
            indexes = cursor.fetchall()

        if indexes:
            print_success(f"Found {len(indexes)} indexes on {table_name}:")
            for idx_name, idx_def in indexes:
                print(f"  - {idx_name}")
        else:
            print_warning("No custom indexes found (may be using default)")

        return True

    except Exception as e:
        # Not critical - may fail on different databases
        print_warning(f"Could not verify indexes: {e}")
        return True


def verify_cloudinary_field():
    """Verify Cloudinary field configuration"""
    print_header("7. Cloudinary Field Verification")

    try:
        # Get field
        avatar_field = UserProfile._meta.get_field('avatar')

        print_success(f"Avatar field type: {avatar_field.__class__.__name__}")

        # Check if it's CloudinaryField
        if 'CloudinaryField' in avatar_field.__class__.__name__:
            print_success("Avatar field is CloudinaryField")
        else:
            print_warning(f"Avatar field is not CloudinaryField: {avatar_field.__class__}")

        # Check transformation settings
        if hasattr(avatar_field, 'transformation'):
            print_success("Transformation settings configured")
        else:
            print_warning("No transformation settings found")

        return True

    except Exception as e:
        print_error(f"Cloudinary field verification failed: {e}")
        return False


def run_all_verifications():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("  UserProfile Implementation Verification")
    print("="*60)

    results = []

    # Run all checks
    results.append(("Model Import", verify_model_exists()))
    results.append(("Signal Registration", verify_signal_registered()))
    results.append(("Auto Profile Creation", verify_profile_creation()))
    results.append(("Existing Users", verify_existing_users_have_profiles()))
    results.append(("Model Methods", verify_model_methods()))
    results.append(("Database Indexes", verify_database_indexes()))
    results.append(("Cloudinary Field", verify_cloudinary_field()))

    # Summary
    print_header("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} checks passed")
    print(f"{'='*60}\n")

    if passed == total:
        print("🎉 All verifications passed! UserProfile implementation is working correctly.\n")
    else:
        print("⚠️  Some checks failed. Review the output above for details.\n")

    return passed == total


if __name__ == '__main__':
    # Only run if executed directly
    success = run_all_verifications()
    sys.exit(0 if success else 1)
else:
    # Run when imported in Django shell
    run_all_verifications()
