"""
Collection views for Phase K: Collections Feature.

This module provides:
- API endpoints for AJAX operations (create, add, remove)
- Page views for collection management (list, detail, edit, delete)
"""

import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Count
from django.urls import reverse

from ..models import Collection, CollectionItem, Prompt

logger = logging.getLogger(__name__)


# =============================================================================
# API ENDPOINTS (AJAX)
# =============================================================================

@login_required
@require_GET
def api_collections_list(request):
    """
    API endpoint to get user's collections with prompt membership status.

    GET /api/collections/
    GET /api/collections/?prompt_id=123

    Query params:
        prompt_id: Optional - if provided, includes whether each collection contains this prompt

    Returns:
        JSON with collections list including item_count and thumbnail_url
    """
    try:
        prompt_id = request.GET.get('prompt_id')
        user = request.user

        # Get user's non-deleted collections with item count
        collections = Collection.objects.filter(
            user=user,
            is_deleted=False
        ).annotate(
            items_count=Count('items')
        ).order_by('-updated_at')

        # If prompt_id provided, get set of collection IDs that contain it
        collections_with_prompt = set()
        if prompt_id:
            try:
                prompt_id_int = int(prompt_id)
                collections_with_prompt = set(
                    CollectionItem.objects.filter(
                        collection__user=user,
                        collection__is_deleted=False,
                        prompt_id=prompt_id_int
                    ).values_list('collection_id', flat=True)
                )
            except (ValueError, TypeError):
                pass  # Invalid prompt_id, just skip

        # Build response data
        collections_data = []
        for collection in collections:
            # Get thumbnail from most recent item
            thumbnail_url = None
            latest_item = CollectionItem.objects.filter(
                collection=collection
            ).select_related('prompt').order_by('-added_at').first()

            if latest_item and latest_item.prompt:
                thumbnail_url = latest_item.prompt.get_thumbnail_url(width=300)

            collections_data.append({
                'id': collection.id,
                'title': collection.title,
                'slug': collection.slug,
                'is_private': collection.is_private,
                'item_count': collection.items_count,
                'thumbnail_url': thumbnail_url,
                'has_prompt': collection.id in collections_with_prompt,
            })

        return JsonResponse({
            'success': True,
            'collections': collections_data,
            'count': len(collections_data),
        })

    except Exception as e:
        logger.error(f"Error in api_collections_list: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Something went wrong',
        }, status=500)


@login_required
@require_POST
def api_collection_create(request):
    """
    API endpoint to create a new collection.

    POST data:
        title: Collection title (required, max 50 chars)
        is_private: Boolean (optional, default False)
        prompt_id: Optional - if provided, add this prompt to the new collection

    Returns:
        JSON with new collection data or error
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    title = data.get('title', '').strip()
    if not title:
        return JsonResponse({
            'success': False,
            'error': 'Collection title is required'
        }, status=400)

    if len(title) > 50:
        return JsonResponse({
            'success': False,
            'error': 'Collection title must be 50 characters or less'
        }, status=400)

    # Get is_private from frontend (default False = public)
    is_private = data.get('is_private', False)
    # Handle string 'true'/'false' from form data
    if isinstance(is_private, str):
        is_private = is_private.lower() == 'true'
    prompt_id = data.get('prompt_id')

    # Create the collection
    collection = Collection.objects.create(
        title=title,
        user=request.user,
        is_private=is_private
    )

    # Optionally add prompt to collection
    prompt_added = False
    if prompt_id:
        try:
            prompt = Prompt.objects.get(id=prompt_id)
            CollectionItem.objects.create(
                collection=collection,
                prompt=prompt,
                order=0
            )
            prompt_added = True
        except Prompt.DoesNotExist:
            pass  # Ignore if prompt doesn't exist

    logger.info(f"User {request.user.username} created collection '{title}' (ID: {collection.id})")

    return JsonResponse({
        'success': True,
        'collection': {
            'id': collection.id,
            'title': collection.title,
            'slug': collection.slug,
            'item_count': 1 if prompt_added else 0,
            'is_private': collection.is_private,
        },
        'prompt_added': prompt_added
    })


@login_required
@require_POST
def api_collection_add_prompt(request, collection_id):
    """
    API endpoint to add a prompt to a collection.

    POST data:
        prompt_id: ID of prompt to add (required)

    Returns:
        JSON with success status
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    prompt_id = data.get('prompt_id')
    if not prompt_id:
        return JsonResponse({
            'success': False,
            'error': 'Prompt ID is required'
        }, status=400)

    # Get collection (must be owned by user, not deleted)
    collection = get_object_or_404(
        Collection, id=collection_id, user=request.user, is_deleted=False
    )

    # Get prompt
    try:
        prompt = Prompt.objects.get(id=prompt_id)
    except Prompt.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prompt not found'
        }, status=404)

    # Check if already in collection
    if CollectionItem.objects.filter(collection=collection, prompt=prompt).exists():
        return JsonResponse({
            'success': False,
            'error': 'Prompt is already in this collection',
            'already_exists': True
        }, status=400)

    # Get next order number
    max_order = CollectionItem.objects.filter(collection=collection).count()

    # Add prompt to collection
    CollectionItem.objects.create(
        collection=collection,
        prompt=prompt,
        order=max_order
    )

    # Update collection's updated_at
    collection.save()  # This will auto-update updated_at

    logger.info(f"User {request.user.username} added prompt {prompt_id} to collection '{collection.title}'")

    # Get updated item count
    item_count = CollectionItem.objects.filter(collection=collection).count()

    return JsonResponse({
        'success': True,
        'message': f'Added to {collection.title}',
        'collection': {
            'id': collection.id,
            'title': collection.title,
            'item_count': item_count
        }
    })


@login_required
@require_POST
def api_collection_remove_prompt(request, collection_id):
    """
    API endpoint to remove a prompt from a collection.

    POST data:
        prompt_id: ID of prompt to remove (required)

    Returns:
        JSON with success status
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)

    prompt_id = data.get('prompt_id')
    if not prompt_id:
        return JsonResponse({
            'success': False,
            'error': 'Prompt ID is required'
        }, status=400)

    # Get collection (must be owned by user, not deleted)
    collection = get_object_or_404(
        Collection, id=collection_id, user=request.user, is_deleted=False
    )

    # Find and delete the collection item
    try:
        item = CollectionItem.objects.get(collection=collection, prompt_id=prompt_id)
        item.delete()

        # Update collection's updated_at
        collection.save()

        logger.info(f"User {request.user.username} removed prompt {prompt_id} from collection '{collection.title}'")

        # Get updated item count
        item_count = CollectionItem.objects.filter(collection=collection).count()

        return JsonResponse({
            'success': True,
            'message': f'Removed from {collection.title}',
            'collection': {
                'id': collection.id,
                'title': collection.title,
                'item_count': item_count
            }
        })
    except CollectionItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Prompt is not in this collection'
        }, status=404)


# =============================================================================
# PAGE VIEWS
# =============================================================================

@login_required
def collections_list(request):
    """
    Display list of user's collections.

    Shows:
        - All user's collections with prompt counts
        - Create new collection button
        - Edit/Delete actions
    """
    user = request.user

    # Get user's non-deleted collections with prompt counts
    collections = Collection.objects.filter(
        user=user,
        is_deleted=False
    ).annotate(
        items_count=Count('items')
    ).order_by('-updated_at')

    # Pagination
    paginator = Paginator(collections, 12)  # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collections': page_obj,
        'page_obj': page_obj,
        'total_collections': collections.count(),
    }

    return render(request, 'prompts/collections_list.html', context)


def collection_detail(request, slug):
    """
    Display a collection's contents.

    - Public collections: visible to everyone
    - Private collections: only visible to owner
    """
    # Try to get the collection (must not be deleted)
    collection = get_object_or_404(Collection, slug=slug, is_deleted=False)

    # Check view permission: private collections only visible to owner
    is_owner = request.user.is_authenticated and request.user == collection.user
    if collection.is_private and not is_owner:
        messages.error(request, "You don't have permission to view this collection.")
        return redirect('prompts:home')

    # Get collection items with prompts
    items = collection.items.select_related(
        'prompt', 'prompt__author', 'prompt__author__userprofile'
    ).order_by('order', '-added_at')

    # Pagination
    paginator = Paginator(items, 24)  # 24 prompts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'collection': collection,
        'items': page_obj,
        'page_obj': page_obj,
        'can_edit': is_owner,
        'is_owner': is_owner,
    }

    return render(request, 'prompts/collection_detail.html', context)


@login_required
def collection_edit(request, slug):
    """
    Edit a collection's details.

    - Only owner can edit
    - Can update: title, visibility
    """
    collection = get_object_or_404(
        Collection, slug=slug, user=request.user, is_deleted=False
    )

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        is_private = request.POST.get('is_private') == 'on'

        # Validate
        if not title:
            messages.error(request, 'Collection title is required.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        if len(title) > 50:
            messages.error(request, 'Collection title must be 50 characters or less.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        # Update collection
        collection.title = title
        collection.is_private = is_private
        collection.save()

        messages.success(request, f'Collection "{title}" updated successfully.')
        return redirect('prompts:collection_detail', slug=collection.slug)

    context = {
        'collection': collection,
    }

    return render(request, 'prompts/collection_edit.html', context)


@login_required
def collection_delete(request, slug):
    """
    Delete a collection (soft delete).

    - Only owner can delete
    - Uses soft delete pattern
    """
    collection = get_object_or_404(
        Collection, slug=slug, user=request.user, is_deleted=False
    )

    if request.method == 'POST':
        collection_title = collection.title
        collection.soft_delete(request.user)

        messages.success(request, f'Collection "{collection_title}" has been deleted.')
        logger.info(f"User {request.user.username} deleted collection '{collection_title}' (ID: {collection.id})")

        return redirect('prompts:collections_list')

    context = {
        'collection': collection,
    }

    return render(request, 'prompts/collection_delete.html', context)
