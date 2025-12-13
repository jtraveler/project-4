import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompts_manager.settings')
django.setup()

from prompts.models import Prompt
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("DATABASE AUDIT")
print("=" * 80)

total = Prompt.objects.count()
print(f"\nTotal prompts: {total}")

draft = Prompt.objects.filter(status='DRAFT').count()
published = Prompt.objects.filter(status='PUBLISHED').count()
print(f"DRAFT: {draft}")
print(f"PUBLISHED: {published}")

no_media = Prompt.objects.filter(featured_image__isnull=True, featured_video__isnull=True).count()
print(f"\nPrompts without ANY media: {no_media}")

print("\n" + "=" * 80)
print("THE 3 PROMPTS (152, 145, 128)")
print("=" * 80)
for pid in [152, 145, 128]:
    try:
        p = Prompt.objects.get(id=pid)
        print(f"\nPrompt {pid}: {p.title}")
        print(f"  Status: {p.status}")
        print(f"  Has Image: {p.featured_image is not None}")
        print(f"  Has Video: {p.featured_video is not None}")
    except:
        print(f"\nPrompt {pid} NOT FOUND")

print("\n" + "=" * 80)
print("GHOST PROMPTS (149, 146, 145)")
print("=" * 80)
for pid in [149, 146, 145]:
    try:
        p = Prompt.objects.get(id=pid)
        print(f"\nPrompt {pid} EXISTS: {p.title}")
        print(f"  Status: {p.status}")
    except:
        print(f"\nPrompt {pid} DOES NOT EXIST")

print("\n" + "=" * 80)
print("UNTITLED PROMPTS")
print("=" * 80)
untitled = Prompt.objects.filter(title__icontains='untitled')
print(f"\nFound {untitled.count()} untitled prompts")
for p in untitled[:10]:
    print(f"  ID {p.id}: {p.title} (Status: {p.status})")

print("\n" + "=" * 80)
print("ADMIN PROMPTS")
print("=" * 80)
admin = User.objects.filter(is_superuser=True).first()
if admin:
    admin_prompts = Prompt.objects.filter(author=admin)
    print(f"\nAdmin '{admin.username}' has {admin_prompts.count()} prompts")
    admin_no_media = admin_prompts.filter(featured_image__isnull=True, featured_video__isnull=True).count()
    print(f"Admin prompts without media: {admin_no_media}")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)