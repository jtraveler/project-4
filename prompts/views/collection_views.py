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

    Query params:
        prompt_id: Optional - if provided, includes whether each collection contains this prompt

    Returns:
        JSON with collections list including thumbnail_urls for grid display
    """
    prompt_id = request.GET.get('prompt_id')
    user = request.user

    # Get user's active collections with prefetched items for thumbnails
    collections = Collection.objects.filter(owner=user).prefetch_related(
        'items__prompt'
    ).order_by('-updated_at')

    # Build response data
    collections_data = []
    for collection in collections:
        # Get up to 3 thumbnail URLs from prompts in collection
        thumbnail_urls = []
        for item in collection.items.all()[:3]:
            if item.prompt:
                thumb_url = item.prompt.get_thumbnail_url(width=300)
                if thumb_url:
                    thumbnail_urls.append(thumb_url)

        collection_data = {
            'id': collection.id,
            'name': collection.name,
            'slug': collection.slug,
            'prompt_count': collection.prompt_count,
            'is_public': collection.is_public,
            'is_private': not collection.is_public,  # For frontend convenience
            'cover_url': collection.cover_url,
            'thumbnail_urls': thumbnail_urls,  # For Pexels-style grid display
        }

        # Check if prompt is in this collection
        if prompt_id:
            try:
                prompt_id_int = int(prompt_id)
                collection_data['contains_prompt'] = CollectionItem.objects.filter(
                    collection=collection,
                    prompt_id=prompt_id_int
                ).exists()
            except (ValueError, TypeError):
                collection_data['contains_prompt'] = False

        collections_data.append(collection_data)

    return JsonResponse({
        'success': True,
        'collections': collections_data,
        'count': len(collections_data)
    })


@login_required
@require_POST
def api_collection_create(request):
    """
    API endpoint to create a new collection.

    POST data:
        name: Collection name (required)
        is_public: Boolean (optional, default True)
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

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({
            'success': False,
            'error': 'Collection name is required'
        }, status=400)

    if len(name) > 100:
        return JsonResponse({
            'success': False,
            'error': 'Collection name must be 100 characters or less'
        }, status=400)

    # Support both is_public and is_private from frontend
    is_private = data.get('is_private', False)
    is_public = data.get('is_public', not is_private)  # is_private takes precedence
    prompt_id = data.get('prompt_id')

    # Create the collection
    collection = Collection.objects.create(
        name=name,
        owner=request.user,
        is_public=is_public
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

    logger.info(f"User {request.user.username} created collection '{name}' (ID: {collection.id})")

    return JsonResponse({
        'success': True,
        'collection': {
            'id': collection.id,
            'name': collection.name,
            'slug': collection.slug,
            'prompt_count': 1 if prompt_added else 0,
            'is_public': collection.is_public,
            'url': reverse('prompts:collection_detail', args=[collection.slug])
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

    # Get collection (must be owned by user)
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)

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
    max_order = CollectionItem.objects.filter(collection=collection).aggregate(
        max_order=Count('order')
    )['max_order'] or 0

    # Add prompt to collection
    CollectionItem.objects.create(
        collection=collection,
        prompt=prompt,
        order=max_order
    )

    # Update collection's updated_at
    collection.save()  # This will auto-update updated_at

    logger.info(f"User {request.user.username} added prompt {prompt_id} to collection '{collection.name}'")

    return JsonResponse({
        'success': True,
        'message': f'Added to {collection.name}',
        'collection': {
            'id': collection.id,
            'name': collection.name,
            'prompt_count': collection.prompt_count
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

    # Get collection (must be owned by user)
    collection = get_object_or_404(Collection, id=collection_id, owner=request.user)

    # Find and delete the collection item
    try:
        item = CollectionItem.objects.get(collection=collection, prompt_id=prompt_id)
        item.delete()

        # Update collection's updated_at
        collection.save()

        logger.info(f"User {request.user.username} removed prompt {prompt_id} from collection '{collection.name}'")

        return JsonResponse({
            'success': True,
            'message': f'Removed from {collection.name}',
            'collection': {
                'id': collection.id,
                'name': collection.name,
                'prompt_count': collection.prompt_count
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

    # Get user's collections with prompt counts
    collections = Collection.objects.filter(owner=user).annotate(
        item_count=Count('items')
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
    # Try to get the collection (including checking permissions)
    collection = get_object_or_404(Collection, slug=slug)

    # Check view permission
    if not collection.can_view(request.user):
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

    # Check if user can edit this collection
    can_edit = collection.can_edit(request.user)

    context = {
        'collection': collection,
        'items': page_obj,
        'page_obj': page_obj,
        'can_edit': can_edit,
        'is_owner': request.user == collection.owner,
    }

    return render(request, 'prompts/collection_detail.html', context)


@login_required
def collection_edit(request, slug):
    """
    Edit a collection's details.

    - Only owner can edit
    - Can update: name, description, visibility, cover image
    """
    collection = get_object_or_404(Collection, slug=slug, owner=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_public = request.POST.get('is_public') == 'on'

        # Validate
        if not name:
            messages.error(request, 'Collection name is required.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        if len(name) > 100:
            messages.error(request, 'Collection name must be 100 characters or less.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        if len(description) > 500:
            messages.error(request, 'Description must be 500 characters or less.')
            return render(request, 'prompts/collection_edit.html', {'collection': collection})

        # Update collection
        collection.name = name
        collection.description = description
        collection.is_public = is_public
        collection.save()

        messages.success(request, f'Collection "{name}" updated successfully.')
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
    collection = get_object_or_404(Collection, slug=slug, owner=request.user)

    if request.method == 'POST':
        collection_name = collection.name
        collection.soft_delete()

        messages.success(request, f'Collection "{collection_name}" has been deleted.')
        logger.info(f"User {request.user.username} deleted collection '{collection_name}' (ID: {collection.id})")

        return redirect('prompts:collections_list')

    context = {
        'collection': collection,
    }

    return render(request, 'prompts/collection_delete.html', context)
