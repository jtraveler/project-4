import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prompts_manager.settings')
django.setup()

from prompts.models import Prompt

print("=" * 80)
print("INVESTIGATING PLACEHOLDER/EMPTY MEDIA PROMPTS")
print("=" * 80)

# Get all admin's prompts
admin_prompts = Prompt.objects.filter(author__is_superuser=True)

print(f"\nTotal admin prompts: {admin_prompts.count()}")

# Check for various "empty" media patterns
print("\n" + "=" * 80)
print("CHECKING FOR DIFFERENT 'EMPTY' PATTERNS")
print("=" * 80)

for p in admin_prompts.order_by('-id')[:10]:
    print(f"\nPrompt {p.id}: {p.title}")
    print(f"  Status: {p.status} (0=draft, 1=published)")
    print(f"  featured_image: {repr(p.featured_image)}")
    print(f"  featured_video: {repr(p.featured_video)}")
    
    # Check if it's the placeholder
    if p.featured_image:
        img_str = str(p.featured_image)
        if 'placeholder' in img_str.lower():
            print(f"  ⚠️  HAS PLACEHOLDER IMAGE: {img_str}")
        elif img_str == '':
            print(f"  ⚠️  EMPTY STRING IMAGE")
    
    if p.featured_video:
        vid_str = str(p.featured_video)
        if 'placeholder' in vid_str.lower():
            print(f"  ⚠️  HAS PLACEHOLDER VIDEO: {vid_str}")
        elif vid_str == '':
            print(f"  ⚠️  EMPTY STRING VIDEO")

print("\n" + "=" * 80)
print("PROMPTS WITH 'placeholder' IN MEDIA FIELD")
print("=" * 80)

# Check for placeholder in featured_image
placeholder_image = Prompt.objects.filter(featured_image__icontains='placeholder')
print(f"\nPrompts with 'placeholder' in featured_image: {placeholder_image.count()}")
for p in placeholder_image[:10]:
    status_text = "DRAFT" if p.status == 0 else "PUBLISHED"
    print(f"  ID {p.id}: {p.title} ({status_text})")
    print(f"    Image: {p.featured_image}")

# Check for empty string (not NULL)
print("\n" + "=" * 80)
print("CHECKING FOR EMPTY STRINGS (not NULL)")
print("=" * 80)

all_prompts = Prompt.objects.all()
empty_string_count = 0
for p in all_prompts:
    if (str(p.featured_image) == '' and p.featured_image is not None) or \
       (str(p.featured_video) == '' and p.featured_video is not None):
        empty_string_count += 1
        print(f"  ID {p.id}: {p.title}")
        print(f"    Image: '{p.featured_image}' (is None: {p.featured_image is None})")
        print(f"    Video: '{p.featured_video}' (is None: {p.featured_video is None})")

print(f"\nTotal prompts with empty strings: {empty_string_count}")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)