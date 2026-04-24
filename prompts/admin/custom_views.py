"""
Custom admin views for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- trash_dashboard — staff-only dashboard for trash bin and orphaned files,
  routed at ``/admin/trash-dashboard/`` via ``prompts_manager/urls.py``.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render

from prompts.models import Prompt


@staff_member_required
def trash_dashboard(request):
    """
    Admin dashboard for trash bin and orphaned file management.

    Displays:
    - Count of deleted prompts
    - Count of orphaned images (Cloudinary files without prompts)
    - Count of orphaned videos
    - Recent deletions with restore options
    - Status of previously reported "ghost" prompts (149, 146, 145)
    """
    # Count deleted prompts (soft-deleted, in trash)
    deleted_count = Prompt.all_objects.filter(deleted_at__isnull=False).count()

    # Note: Orphaned file counts require Cloudinary API calls
    # For now, show placeholder counts (run detect_orphaned_files for real data)
    orphaned_images = 0  # Placeholder
    orphaned_videos = 0  # Placeholder

    # Get recent 10 deletions
    recent_deletions = Prompt.all_objects.filter(
        deleted_at__isnull=False
    ).select_related('author', 'deleted_by').order_by('-deleted_at')[:10]

    # Force fresh database query for ghost prompts
    ghost_ids = [149, 146, 145]
    ghost_info = []

    for prompt_id in ghost_ids:
        try:
            # Direct database query - no caching
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, title, status, featured_image, user_id FROM prompts_prompt WHERE id = %s",
                    [prompt_id]
                )
                row = cursor.fetchone()
                if row:
                    ghost_info.append({
                        'id': row[0],
                        'title': row[1][:50] if row[1] else 'No Title',
                        'status': 'Draft' if row[2] == 0 else 'Active',
                        'has_media': 'Yes' if row[3] else 'No',
                        'author': User.objects.get(id=row[4]).username if row[4] else 'Unknown'
                    })
        except Exception as e:
            print(f"Error with prompt {prompt_id}: {e}")

    # Get Django admin context for sidebar and logout button
    from django.contrib.admin.sites import site as admin_site
    context = admin_site.each_context(request)

    # Add custom context
    context.update({
        'deleted_count': deleted_count,
        'orphaned_images': orphaned_images,
        'orphaned_videos': orphaned_videos,
        'recent_deletions': recent_deletions,
        'ghost_prompts': ghost_info,
        'title': 'Trash & Orphaned Files Dashboard',
    })

    return render(request, 'admin/trash_dashboard.html', context)
