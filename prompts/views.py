from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Prompt, Comment
from .forms import CommentForm

class PromptList(generic.ListView):
    queryset = Prompt.objects.filter(status=1)  # Only show published prompts
    template_name = "prompts/prompt_list.html"  # Updated to correct path
    paginate_by = 6

def prompt_detail(request, slug):
    """
    Display an individual prompt and handle comment submission.
    """
    prompt = get_object_or_404(Prompt, slug=slug, status=1)
    comments = prompt.comments.filter(approved=True).order_by('created_on')
    comment_count = comments.count()
    
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
        comment_form = CommentFo