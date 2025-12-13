#!/usr/bin/env python
"""
Investigation script to find malformed Cloudinary URLs in the database.
Run with: python manage.py shell < investigate_cloudinary_urls.py
"""

from prompts.models import UserProfile, Prompt
from django.conf import settings

print("\n" + "="*80)
print("CLOUDINARY URL INVESTIGATION")
print("="*80)

# Get Cloudinary configuration
cloud_name = settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'unknown')
print(f"\nConfigured Cloud Name: {cloud_name}")

# Check UserProfile avatars
print("\n" + "-"*80)
print("CHECKING USER PROFILE AVATARS")
print("-"*80)

profiles = UserProfile.objects.all()
malformed_avatars = []
problematic_id = "8ee87aee-3c11-4f23-9749-c737914598dd_lk4gpu"

for profile in profiles:
    if profile.avatar and hasattr(profile.avatar, 'url'):
        url = str(profile.avatar.url)
        if url:
            # Check if URL is malformed (doesn't start with http)
            if not url.startswith('http'):
                malformed_avatars.append({
                    'username': profile.user.username,
                    'url': url,
                    'type': 'relative'
                })
                print(f"\n❌ User: {profile.user.username}")
                print(f"   Malformed URL: {url}")

            # Check for the specific problematic ID
            if problematic_id in url:
                print(f"\n⚠️  FOUND PROBLEMATIC ID in avatar!")
                print(f"   User: {profile.user.username}")
                print(f"   Full URL: {url}")
                print(f"   Public ID: {profile.avatar.public_id if hasattr(profile.avatar, 'public_id') else 'N/A'}")

print(f"\n📊 Summary: {len(malformed_avatars)} malformed avatar URLs found")

# Check Prompt images
print("\n" + "-"*80)
print("CHECKING PROMPT IMAGES")
print("-"*80)

prompts = Prompt.objects.all()[:100]  # Check first 100 to avoid overwhelming output
malformed_images = []

for prompt in prompts:
    # Check featured_image
    if prompt.featured_image and hasattr(prompt.featured_image, 'url'):
        url = str(prompt.featured_image.url)
        if url and not url.startswith('http'):
            malformed_images.append({
                'prompt_id': prompt.id,
                'title': prompt.title,
                'url': url,
                'type': 'image'
            })

        # Check for problematic ID
        if url and problematic_id in url:
            print(f"\n⚠️  FOUND PROBLEMATIC ID in prompt image!")
            print(f"   Prompt ID: {prompt.id}")
            print(f"   Title: {prompt.title}")
            print(f"   URL: {url}")

    # Check featured_video
    if prompt.featured_video and hasattr(prompt.featured_video, 'url'):
        url = str(prompt.featured_video.url)
        if url and not url.startswith('http'):
            malformed_images.append({
                'prompt_id': prompt.id,
                'title': prompt.title,
                'url': url,
                'type': 'video'
            })

        # Check for problematic ID
        if url and problematic_id in url:
            print(f"\n⚠️  FOUND PROBLEMATIC ID in prompt video!")
            print(f"   Prompt ID: {prompt.id}")
            print(f"   Title: {prompt.title}")
            print(f"   URL: {url}")

print(f"\n📊 Summary: {len(malformed_images)} malformed prompt image/video URLs found")

# Print overall summary
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"Total malformed avatar URLs: {len(malformed_avatars)}")
print(f"Total malformed prompt media URLs: {len(malformed_images)}")
print(f"Total issues found: {len(malformed_avatars) + len(malformed_images)}")

if len(malformed_avatars) + len(malformed_images) == 0:
    print("\n✅ No malformed URLs found in database!")
    print("   The issue may be in template rendering or JavaScript manipulation.")
else:
    print("\n⚠️  Malformed URLs found! Data migration needed.")

print("\n" + "="*80)
