"""
DATABASE AUDIT SCRIPT FOR PHASE F DAY 1 INVESTIGATION
Run this in Django shell: python manage.py shell < database_audit_script.py

Purpose: Understand what happened to the "19 prompts with issues"
"""

from prompts.models import Prompt, PromptImage, PromptVideo
from django.contrib.auth import get_user_model

print("=" * 80)
print("PHASE F DAY 1 - DATABASE AUDIT")
print("=" * 80)

User = get_user_model()

# ============================================================================
# SECTION 1: OVERALL PROMPT COUNTS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 1: OVERALL PROMPT COUNTS")
print("=" * 80)

total_prompts = Prompt.objects.count()
print(f"\n📊 Total prompts in database: {total_prompts}")

# Status breakdown
draft_count = Prompt.objects.filter(status='DRAFT').count()
published_count = Prompt.objects.filter(status='PUBLISHED').count()

print(f"\n📋 Status Breakdown:")
print(f"   ├─ DRAFT prompts: {draft_count}")
print(f"   └─ PUBLISHED prompts: {published_count}")

# ============================================================================
# SECTION 2: MEDIA STATUS ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 2: MEDIA STATUS ANALYSIS")
print("=" * 80)

no_image = Prompt.objects.filter(featured_image__isnull=True).count()
no_video = Prompt.objects.filter(featured_video__isnull=True).count()
no_media = Prompt.objects.filter(
    featured_image__isnull=True,
    featured_video__isnull=True
).count()
has_both = Prompt.objects.filter(
    featured_image__isnull=False,
    featured_video__isnull=False
).count()
has_image_only = Prompt.objects.filter(
    featured_image__isnull=False,
    featured_video__isnull=True
).count()
has_video_only = Prompt.objects.filter(
    featured_image__isnull=True,
    featured_video__isnull=False
).count()

print(f"\n📸 Media Status:")
print(f"   ├─ No featured_image: {no_image}")
print(f"   ├─ No featured_video: {no_video}")
print(f"   ├─ No media at all (NULL/NULL): {no_media}")
print(f"   ├─ Has both image AND video: {has_both}")
print(f"   ├─ Has image only: {has_image_only}")
print(f"   └─ Has video only: {has_video_only}")

# ============================================================================
# SECTION 3: THE MYSTERIOUS "3 PROMPTS" - WHO ARE THEY?
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 3: THE 3 PROMPTS WITHOUT MEDIA (from screenshots)")
print("=" * 80)

mystery_ids = [152, 145, 128]
print(f"\n🔍 Investigating prompts: {mystery_ids}")

for pid in mystery_ids:
    try:
        p = Prompt.objects.get(id=pid)
        print(f"\n📄 Prompt {pid}:")
        print(f"   ├─ Title: {p.title}")
        print(f"   ├─ Slug: {p.slug}")
        print(f"   ├─ Status: {p.status}")
        print(f"   ├─ Author: {p.author.username}")
        print(f"   ├─ Featured Image: {p.featured_image}")
        print(f"   └─ Featured Video: {p.featured_video}")
    except Prompt.DoesNotExist:
        print(f"\n❌ Prompt {pid} DOES NOT EXIST in database!")

# ============================================================================
# SECTION 4: GHOST PROMPTS INVESTIGATION (149, 146, 145)
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 4: GHOST PROMPTS INVESTIGATION")
print("=" * 80)

ghost_ids = [149, 146, 145]
print(f"\n👻 Investigating ghost prompts: {ghost_ids}")

for pid in ghost_ids:
    try:
        p = Prompt.objects.get(id=pid)
        print(f"\n✅ Prompt {pid} EXISTS:")
        print(f"   ├─ Title: {p.title}")
        print(f"   ├─ Slug: {p.slug}")
        print(f"   ├─ Status: {p.status}")
        print(f"   ├─ Author: {p.author.username}")
        print(f"   ├─ Featured Image: {p.featured_image}")
        print(f"   ├─ Featured Video: {p.featured_video}")
        print(f"   └─ Created: {p.created_at}")
    except Prompt.DoesNotExist:
        print(f"\n❌ Prompt {pid} DOES NOT EXIST in database")
        
        # Check for orphaned references
        orphaned_images = PromptImage.objects.filter(prompt_id=pid).count()
        orphaned_videos = PromptVideo.objects.filter(prompt_id=pid).count()
        
        if orphaned_images or orphaned_videos:
            print(f"   ⚠️  But found orphaned references:")
            print(f"      ├─ PromptImage records: {orphaned_images}")
            print(f"      └─ PromptVideo records: {orphaned_videos}")

# ============================================================================
# SECTION 5: "UNTITLED" PROMPTS (the suspicious ones)
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 5: 'UNTITLED' PROMPTS INVESTIGATION")
print("=" * 80)

untitled = Prompt.objects.filter(title__icontains='untitled')
print(f"\n📝 Found {untitled.count()} prompts with 'untitled' in title:")

for p in untitled:
    print(f"\n   Prompt {p.id}:")
    print(f"   ├─ Title: {p.title}")
    print(f"   ├─ Slug: {p.slug}")
    print(f"   ├─ Status: {p.status}")
    print(f"   ├─ Has Image: {'✓' if p.featured_image else '✗'}")
    print(f"   └─ Has Video: {'✓' if p.featured_video else '✗'}")

# ============================================================================
# SECTION 6: WHERE ARE THE "19 PROMPTS"?
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 6: SEARCHING FOR THE MISSING '19 PROMPTS'")
print("=" * 80)

# Theory: Maybe they were all set to DRAFT status?
drafts_no_media = Prompt.objects.filter(
    status='DRAFT',
    featured_image__isnull=True,
    featured_video__isnull=True
).count()

print(f"\n🔍 DRAFT prompts without media: {drafts_no_media}")

# Theory: Maybe only missing ONE type of media?
missing_image_only = Prompt.objects.filter(
    featured_image__isnull=True
).exclude(
    featured_video__isnull=True
)

missing_video_only = Prompt.objects.filter(
    featured_video__isnull=True
).exclude(
    featured_image__isnull=True
)

print(f"🔍 Prompts missing ONLY image (have video): {missing_image_only.count()}")
print(f"🔍 Prompts missing ONLY video (have image): {missing_video_only.count()}")

# Show some examples if they exist
if missing_image_only.exists():
    print(f"\n   Examples of prompts with video but no image:")
    for p in missing_image_only[:5]:
        print(f"   ├─ Prompt {p.id}: {p.title[:50]} (Status: {p.status})")

if missing_video_only.exists():
    print(f"\n   Examples of prompts with image but no video:")
    for p in missing_video_only[:5]:
        print(f"   ├─ Prompt {p.id}: {p.title[:50]} (Status: {p.status})")

# ============================================================================
# SECTION 7: ADMIN USER'S PROMPTS (console errors source)
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 7: ADMIN USER ANALYSIS")
print("=" * 80)

admin = User.objects.filter(is_superuser=True).first()

if admin:
    admin_prompts = Prompt.objects.filter(author=admin)
    print(f"\n👤 Admin user: {admin.username}")
    print(f"📊 Total prompts: {admin_prompts.count()}")
    
    admin_draft = admin_prompts.filter(status='DRAFT').count()
    admin_published = admin_prompts.filter(status='PUBLISHED').count()
    
    print(f"   ├─ DRAFT: {admin_draft}")
    print(f"   └─ PUBLISHED: {admin_published}")
    
    # Check for media issues in admin's prompts
    admin_no_media = admin_prompts.filter(
        featured_image__isnull=True,
        featured_video__isnull=True
    ).count()
    
    print(f"\n📸 Admin prompts without media: {admin_no_media}")
    
    # Check for malformed Cloudinary URLs
    print(f"\n🔍 Checking for malformed Cloudinary URLs...")
    malformed_count = 0
    
    for prompt in admin_prompts:
        issues = []
        
        if prompt.featured_image:
            url = str(prompt.featured_image)
            if not url.startswith('http'):
                malformed_count += 1
                issues.append(f"Image: {url[:50]}")
        
        if prompt.featured_video:
            url = str(prompt.featured_video)
            if not url.startswith('http'):
                malformed_count += 1
                issues.append(f"Video: {url[:50]}")
        
        if issues:
            print(f"\n   ⚠️  Prompt {prompt.id}: {prompt.title[:40]}")
            for issue in issues:
                print(f"      └─ {issue}")
    
    print(f"\n📊 Total malformed URLs found: {malformed_count}")

# ============================================================================
# SECTION 8: ORPHANED MEDIA RECORDS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 8: ORPHANED MEDIA RECORDS")
print("=" * 80)

orphaned_images = PromptImage.objects.filter(prompt__isnull=True)
orphaned_videos = PromptVideo.objects.filter(prompt__isnull=True)

print(f"\n🗑️  Orphaned PromptImage records: {orphaned_images.count()}")
print(f"🗑️  Orphaned PromptVideo records: {orphaned_videos.count()}")

if orphaned_images.exists():
    print(f"\n   Orphaned images:")
    for img in orphaned_images[:5]:
        print(f"   ├─ PromptImage {img.id} (no prompt association)")

if orphaned_videos.exists():
    print(f"\n   Orphaned videos:")
    for vid in orphaned_videos[:5]:
        print(f"   ├─ PromptVideo {vid.id} (no prompt association)")

# ============================================================================
# SECTION 9: SUMMARY & CONCLUSIONS
# ============================================================================
print("\n" + "=" * 80)
print("SECTION 9: SUMMARY & CONCLUSIONS")
print("=" * 80)

print(f"\n📊 FINAL COUNTS:")
print(f"   ├─ Total prompts: {total_prompts}")
print(f"   ├─ Prompts without ANY media: {no_media}")
print(f"   ├─ DRAFT status: {draft_count}")
print(f"   ├─ PUBLISHED status: {published_count}")
print(f"   └─ Ghost prompts found: [see Section 4]")

print(f"\n🔍 MYSTERY SOLVED?")
print(f"   The screenshots show 3 prompts (152, 145, 128)")
print(f"   But the session notes mention 19 prompts with issues")
print(f"   Difference: {19 - 3} = 16 prompts unaccounted for")
print(f"   ")
print(f"   Possible explanations:")
print(f"   1. They were set to DRAFT status ({draft_count} total drafts)")
print(f"   2. They were deleted (but some like 'untitled' still accessible)")
print(f"   3. Detection logic changed to only show NULL/NULL prompts")
print(f"   4. They had ONE media type but not both")

print("\n" + "=" * 80)
print("END OF AUDIT")
print("=" * 80)
print("\nNext steps: Review this output and determine fix strategy\n")
