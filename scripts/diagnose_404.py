#!/usr/bin/env python3
"""
Quick diagnostic script to identify the exact 404 URL
Run with: python scripts/diagnose_404.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompts_manager.settings')
django.setup()

from django.contrib.auth.models import User
from prompts.models import UserProfile, Prompt


def diagnose_admin_404():
    """Identify exact source of 404 error on admin profile"""

    print("=" * 60)
    print("404 DIAGNOSTIC REPORT - Admin User")
    print("=" * 60)

    try:
        admin = User.objects.get(username='admin')
        print(f"\n✓ Found admin user: {admin.username}")
    except User.DoesNotExist:
        print("\n✗ Admin user not found!")
        return

    # Check avatar
    print("\n" + "=" * 60)
    print("1. AVATAR CHECK")
    print("=" * 60)

    try:
        profile = UserProfile.objects.get(user=admin)
        print(f"Profile exists: Yes")
        print(f"Has avatar: {bool(profile.avatar)}")

        if profile.avatar:
            print(f"\nAvatar Details:")
            print(f"  Raw value: {profile.avatar}")
            print(f"  Type: {type(profile.avatar)}")

            # Try to get URL
            try:
                url = profile.avatar.url
                print(f"  URL: {url}")

                # Check if URL is malformed
                if url and not url.startswith('http'):
                    print(f"  ⚠️  WARNING: URL is missing domain!")
                    print(f"  ⚠️  This is likely the 404 source!")

            except Exception as e:
                print(f"  ✗ Error getting URL: {e}")
                print(f"  ⚠️  This is likely the 404 source!")
        else:
            print("  ✓ No avatar set (using default letter avatar)")

    except UserProfile.DoesNotExist:
        print("✗ Admin has no profile!")

    # Check admin's prompts
    print("\n" + "=" * 60)
    print("2. PROMPT IMAGES CHECK")
    print("=" * 60)

    prompts = Prompt.objects.filter(author=admin)
    print(f"Admin has {prompts.count()} prompts")

    if prompts.exists():
        print("\nChecking first 5 prompts:")

        for idx, prompt in enumerate(prompts[:5], 1):
            print(f"\n  Prompt #{idx}: {prompt.title[:50]}")

            if prompt.featured_image:
                print(f"    Has image: Yes")
                print(f"    Raw value: {prompt.featured_image}")

                try:
                    url = prompt.featured_image.url
                    print(f"    URL: {url}")

                    # Check if URL is malformed
                    if url and not url.startswith('http'):
                        print(f"    ⚠️  WARNING: URL is missing domain!")
                        print(f"    ⚠️  This could be a 404 source!")

                except Exception as e:
                    print(f"    ✗ Error getting URL: {e}")
                    print(f"    ⚠️  This could be a 404 source!")
            else:
                print(f"    Has image: No")

    # Summary
    print("\n" + "=" * 60)
    print("3. SUMMARY & RECOMMENDATIONS")
    print("=" * 60)

    issues_found = []

    # Re-check avatar
    try:
        profile = UserProfile.objects.get(user=admin)
        if profile.avatar:
            avatar_str = str(profile.avatar)
            if avatar_str and not avatar_str.startswith('http'):
                issues_found.append(f"Avatar URL malformed: {avatar_str}")
    except:
        pass

    # Re-check prompts
    for prompt in Prompt.objects.filter(author=admin):
        if prompt.featured_image:
            img_str = str(prompt.featured_image)
            if img_str and not img_str.startswith('http'):
                issues_found.append(
                    f"Prompt '{prompt.title[:30]}' image malformed: {img_str}"
                )

    if issues_found:
        print(f"\n⚠️  FOUND {len(issues_found)} ISSUE(S):\n")
        for idx, issue in enumerate(issues_found, 1):
            print(f"  {idx}. {issue}")

        print("\n📋 RECOMMENDED ACTION:")
        print("  1. Run: python manage.py fix_admin_avatar --fix")
        print("  2. Refresh browser page")
        print("  3. Check console for 404 errors")

    else:
        print("\n✓ No obvious issues found in database")
        print("\n📋 NEXT STEPS:")
        print("  1. Check browser DevTools Network tab")
        print("  2. Find the exact 404 URL")
        print("  3. Search HTML source for that URL")

    print("\n" + "=" * 60)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * 60)


if __name__ == '__main__':
    diagnose_admin_404()
