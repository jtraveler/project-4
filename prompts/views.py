from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db import models
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from django.core.cache import cache  # Import cache for performance
from taggit.models import Tag
from .models import Prompt, Comment
from .forms import CommentForm, CollaborateForm, PromptForm
from django.http import JsonResponse
import time
import logging

logger = logging.getLogger(__name__)

class PromptList(generic.ListView):
    template_name = "prompts/prompt_list.html"
    paginate_by = 18
    
    def get_queryset(self):
        start_time = time.time()
        
        # Create cache key based on request parameters
        tag_name = self.request.GET.get('tag')
        search_query = self.request.GET.get('search')
        cache_key = f"prompt_list_{tag_name}_{search_query}_{self.request.GET.get('page', 1)}"
        
        # Try to get from cache first (5 minute cache)
        cached_result = cache.get(cache_key)
        if cached_result and not search_query:  # Don't cache search results
            return cached_result
        
        queryset = Prompt.objects.select_related('author').prefetch_related(
            'tags',
            'likes',
            Prefetch('comments', queryset=Comment.objects.filter(approved=True))
        ).filter(status=1).order_by('-created_on')
        
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # Cache the result for 5 minutes (only if not a search query)
        if not search_query:
            cache.set(cache_key, queryset, 300)
        
        end_time = time.time()
        logger.warning(f"DEBUG: Queryset generation took {end_time - start_time:.3f} seconds")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_tag'] = self.request.GET.get('tag')
        context['search_query'] = self.request.GET.get('search')
        return context

def prompt_detail(request, slug):
    start_time = time.time()
    
    # Cache individual prompt details for 10 minutes
    cache_key = f"prompt_detail_{slug}_{request.user.id if request.user.is_authenticated else 'anonymous'}"
    
    prompt_queryset = Prompt.objects.select_related('author').prefetch_related(
        'tags',
        'likes',
        Prefetch('comments', queryset=Comment.objects.select_related('author').order_by('created_on'))
    )
    
    if request.user.is_authenticated:
        prompt = get_object_or_404(prompt_queryset, slug=slug)
        if prompt.status != 1 and prompt.author != request.user:
            raise Http404("Prompt not found")
    else:
        prompt = get_object_or_404(prompt_queryset, slug=slug, status=1)
    
    if request.user.is_authenticated:
        comments = [
            comment for comment in prompt.comments.all() 
            if comment.approved or comment.author == request.user
        ]
    else:
        comments = [comment for comment in prompt.comments.all() if comment.approved]
    
    comment_count = len([c for c in prompt.comments.all() if c.approved])
    
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.prompt = prompt
            comment.save()
            
            # Clear cache when new comment is added
            cache.delete(cache_key)
            
            messages.add_message(
                request, messages.SUCCESS,
                'Comment submitted and awaiting approval'
            )
            return HttpResponseRedirect(request.path_info)
    else:
        comment_form = CommentForm()
    
    liked = False
    if request.user.is_authenticated:
        liked = request.user in prompt.likes.all()

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
            "number_of_likes": prompt.likes.count(),
            "prompt_is_liked": liked,
        },
    )

def comment_edit(request, slug, comment_id):
    prompt = get_object_or_404(Prompt.objects.select_related('author'), slug=slug)
    comment = get_object_or_404(Comment.objects.select_related('author'), pk=comment_id)
    
    if comment.author != request.user:
        messages.add_message(request, messages.ERROR, 'You can only edit your own comments!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
    
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.prompt = prompt
            comment.approved = False
            comment.save()
            
            # Clear relevant caches
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")
            
            messages.add_message(request, messages.SUCCESS, 'Comment updated and awaiting approval!')
            return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
        else:
            messages.add_message(request, messages.ERROR, 'Error updating comment!')
    else:
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
    prompt = get_object_or_404(Prompt.objects.select_related('author'), slug=slug)
    comment = get_object_or_404(Comment.objects.select_related('author'), pk=comment_id)

    if comment.author == request.user:
        comment.delete()
        
        # Clear relevant caches
        cache.delete(f"prompt_detail_{slug}_{request.user.id}")
        
        messages.add_message(request, messages.SUCCESS, 'Comment deleted!')
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own comments!')

    return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))

def prompt_edit(request, slug):
    prompt = get_object_or_404(Prompt.objects.select_related('author').prefetch_related('tags'), slug=slug)
    
    if prompt.author != request.user:
        messages.add_message(request, messages.ERROR, 'You can only edit your own prompts!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
    
    # Cache popular tags for 1 hour
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all().order_by('name')[:20]
        cache.set('popular_tags', existing_tags, 3600)  # Cache for 1 hour
    
    if request.method == "POST":
        prompt_form = PromptForm(data=request.POST, files=request.FILES, instance=prompt)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            prompt.status = 1
            prompt.save()
            prompt_form.save_m2m()
            
            # Clear relevant caches when prompt is updated
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")
            cache.delete(f"prompt_detail_{slug}_anonymous")
            # Clear list caches
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")
            
            messages.add_message(request, messages.SUCCESS, 'Prompt updated successfully!')
            return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))
        else:
            messages.add_message(request, messages.ERROR, 'Error updating prompt!')
    else:
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
    if request.method == 'POST':
        prompt_form = PromptForm(request.POST, request.FILES)
        if prompt_form.is_valid():
            prompt = prompt_form.save(commit=False)
            prompt.author = request.user
            prompt.status = 1
            prompt.save()
            prompt_form.save_m2m()
            
            # Clear list caches when new prompt is created
            for page in range(1, 5):
                cache.delete(f"prompt_list_None_None_{page}")
            
            messages.success(request, 'Your prompt has been created successfully!')
            return redirect('prompts:prompt_detail', slug=prompt.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        prompt_form = PromptForm()
    
    # Use cached popular tags
    existing_tags = cache.get('popular_tags')
    if existing_tags is None:
        existing_tags = Tag.objects.all()[:20]
        cache.set('popular_tags', existing_tags, 3600)
    
    context = {
        'prompt_form': prompt_form,
        'existing_tags': existing_tags,
    }
    
    return render(request, 'prompts/prompt_create.html', context)

def prompt_delete(request, slug):
    prompt = get_object_or_404(Prompt.objects.select_related('author'), slug=slug)

    if prompt.author == request.user:
        prompt.delete()
        
        # Clear relevant caches when prompt is deleted
        cache.delete(f"prompt_detail_{slug}_{request.user.id}")
        cache.delete(f"prompt_detail_{slug}_anonymous")
        for page in range(1, 5):
            cache.delete(f"prompt_list_None_None_{page}")
        
        messages.add_message(request, messages.SUCCESS, 'Prompt deleted successfully!')
        return HttpResponseRedirect(reverse('prompts:home'))
    else:
        messages.add_message(request, messages.ERROR, 'You can only delete your own prompts!')
        return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[slug]))

def collaborate_request(request):
    if request.method == "POST":
        collaborate_form = CollaborateForm(data=request.POST)
        if collaborate_form.is_valid():
            collaborate_form.save()
            messages.add_message(
                request, messages.SUCCESS,
                'Your message has been received! We generally respond to messages within 2 working days.'
            )
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
    prompt = get_object_or_404(Prompt.objects.select_related('author').prefetch_related('likes'), slug=slug)
    
    if prompt.likes.filter(id=request.user.id).exists():
        prompt.likes.remove(request.user)
        liked = False
    else:
        prompt.likes.add(request.user)
        liked = True
    
    # Clear relevant caches when like status changes
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")
    cache.delete(f"prompt_detail_{slug}_anonymous")
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'liked': liked,
            'like_count': prompt.likes.count(),
        }
        return JsonResponse(data)
    
    return HttpResponseRedirect(reverse('prompts:prompt_detail', args=[str(slug)]))