from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db import models
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Import Q objects for complex search following LearnDjango tutorial
from taggit.models import Tag
from .models import Prompt, Comment
from .forms import CommentForm, CollaborateForm, PromptForm
from django.http import JsonResponse
import time  # DEBUG: Add timing to measure performance
import logging  # DEBUG: Add logging to track queries

# DEBUG: Set up logger for performance tracking
logger = logging.getLogger(__name__)

class PromptList(generic.ListView):
    template_name = "prompts/prompt_list.html"
    paginate_by = 100
    
    def get_queryset(self):
        # DEBUG: Time the queryset generation
        start_time = time.time()
        
        queryset = Prompt.objects.filter(status=1)
        
        # Check for tag filter parameter (following URL parameter tutorial)
        tag_name = self.request.GET.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)
        
        # Enhanced search functionality using Q objects following LearnDjango tutorial
        # https://learndjango.com/tutorials/django-search-tutorial
        search_query = self.request.GET.get('search')
        if search_query:
            # Multi-field search using Q objects with OR logic
            # Search across: title, content, excerpt, author username, and tags
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()  # Use distinct() to avoid duplicate results from tag matches
        
        # DEBUG: Log timing
        end_time = time.time()
        logger.warning(f"DEBUG: Queryset generation took {end_time - start_time:.3f} seconds")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the current tag filter to context for display
        context['current_tag'] = self.request.GET.get('tag')
        # Add search query to context for display
        context['search_query'] = self.request.GET.get('search')
        return context

def prompt_detail(request, slug):
    """
    Display an individual prompt and handle comment submission.
    """
    # DEBUG: Time the view execution
    start_time = time.time()
    
    if request.user.is_authenticated:
        prompt = get_object_or_404(Prompt, slug=slug)
        # Check if prompt is published OR user is the author
        if prompt.status != 1 and prompt.author != request.user:
            # Prompt is draft and user is not the author
            raise Http404("Prompt not found")
    else:
        prompt = get_object_or_404(Prompt, slug=slug, status=1)
    
    # Show approved comments for everyone, plus user's own unapproved comments
    if request.user.is_authenticated:
        comments = prompt.comments.filter(
            models.Q(approved=True) | models.Q(author=request.user)
        ).order_by('created_on')
    else:
        comments = prompt.comments.filter(approved=True).order_by('created_on')
    
    comment_count = prompt.comments.filter(approved=True).count()
    
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.prompt = prompt
            comment.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )
            return HttpResponseRedirect(request.path_info)
    else:
        comment_form = CommentForm()
    
    liked = False
    if request.user.is_authenticated:
        if prompt.likes.filter(id=request.user.id).exists():
            liked = True

    # DEBUG: Log timing
    end_time = time.time()
    logger.warning(f"DEBUG: prompt_detail view took {end_time - start_time:.3f} seconds")

    return render(
        request,
        "prompts/prompt_detail.html",
        {
            "prompt": prompt,
            "comments": comments,
            "comment_count": comment_count,
            "comment_form": comment_form,
            "number_of_likes": prompt.number_of_likes(),  # This will cause another query!
            "prompt_is_liked": liked,
        },
    )

def comment_edit(request, slug, comment_id):
    """
    View to edit comments
    """
    prompt = get_object_or_404(Prompt, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Check if user owns the comment
    if comment.author != request.user:
        messages.add_message(request, messages.ERROR, 'You can only edit your own comments!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
    
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.prompt = prompt
            comment.approved = False  # Requires re-approval after edit
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Comment updated and awaiting approval!')
            return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
        else:
            messages.add_message(request, messages.ERROR, 'Error updating comment!')
    else:
        # GET request - show the edit form
        comment_form = CommentForm(instance=comment)
    
    return render(
        request,
        'prompts/comment_edit.html',
        {
            'comment_form': comment_form,
            'prompt': prompt,
            'comment': comment,
        }
    )

def comment_delete(request, slug, comment_id):
    """
    View to delete comment
    """
    prompt = get_object_or_404(Prompt, slug=slug)
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own comments!')

    return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))

def prompt_edit(request, slug):
    """
    View to edit prompts
    """
    prompt = get_object_or_404(Prompt, slug=slug)
    
    # Check if user owns the prompt
    if prompt.author != request.user:
        messages.add_message(request, messages.ERROR, 'You can only edit your own prompts!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
    
    existing_tags = Tag.objects.all().order_by('name')[:20]  # Show top 20 most common tags
    
    if request.method == "POST":
        prompt_form = PromptForm(data=request.POST, files=request.FILES, instance=prompt)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            prompt.status = 1  # Always publish immediately
            prompt.save()
            # Save tags (many-to-many relationship)
            prompt_form.save_m2m()
            messages.add_message(request, messages.SUCCESS, 'Prompt updated successfully!')
            return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
        else:
            messages.add_message(request, messages.ERROR, 'Error updating prompt!')
    else:
        # GET request - show the edit form
        prompt_form = PromptForm(instance=prompt)
    
    return render(
        request,
        'prompts/prompt_edit.html',
        {
            'prompt_form': prompt_form,
            'prompt': prompt,
            'existing_tags': existing_tags,
        }
    )

@login_required
def prompt_create(request):
    """
    View for creating new prompts
    """
    if request.method == 'POST':
        prompt_form = PromptForm(request.POST, request.FILES)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            prompt.status = 1  # Published
            prompt.save()
            prompt_form.save_m2m()  # Save tags
            
            messages.success(request, 'Your prompt has been created successfully!')
            return redirect('prompts:prompt_detail', slug=prompt.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        prompt_form = PromptForm()
    
    existing_tags = Tag.objects.all()[:20]
    
    context = {
        'prompt_form': prompt_form,
        'existing_tags': existing_tags,
    }
    
    return render(request, 'prompts/prompt_create.html', context)

def prompt_delete(request, slug):
    """
    View to delete prompt
    """
    prompt = get_object_or_404(Prompt, slug=slug)

    if prompt.author == request.user:
        prompt.delete()
        messages.add_message(request, messages.SUCCESS, 'Prompt deleted successfully!')
        return HttpResponseRedirect(reverse('prompts:home'))
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own prompts!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))

def collaborate_request(request):
    """
    View to handle collaboration requests
    """
    if request.method == "POST":
        collaborate_form = CollaborateForm(data=request.POST)
        if collaborate_form.is_valid():
            collaborate_form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Collaboration request received! I endeavour to respond within 2 working days.'
            )
            # Redirect to the same page to prevent form resubmission
            return HttpResponseRedirect(reverse('prompts:collaborate'))
        else:
            messages.add_message(
                request, messages.ERROR,
                'There was an error with your submission. Please check the form and try again.'
            )
    
    collaborate_form = CollaborateForm()
    
    return render(
        request,
        "prompts/collaborate.html",
        {
            "collaborate_form": collaborate_form,
        },
    )

@login_required
def prompt_like(request, slug):
    """
    Handle like/unlike functionality for prompts.
    Supports both AJAX and regular POST requests.
    Following Simple is Better Than Complex AJAX tutorial.
    """
    prompt = get_object_or_404(Prompt, slug=slug)
    
    # Check if user already liked the prompt
    if prompt.likes.filter(id=request.user.id).exists():
        # User already liked it, so unlike it
        prompt.likes.remove(request.user)
        liked = False
    else:
        # User hasn't liked it, so add the like
        prompt.likes.add(request.user)
        liked = True
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'liked': liked,
            'like_count': prompt.number_of_likes(),
        }
        return JsonResponse(data)
    
    # Otherwise, redirect back to the prompt detail page (existing functionality)
    return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[str(slug)]))