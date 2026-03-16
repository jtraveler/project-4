"""
prompt_comment_views.py — Comment edit and delete views.

Split from prompt_views.py in Session 134.
Contains: comment_edit, comment_delete
"""

from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from prompts.models import Prompt, Comment
from django.core.cache import cache
from prompts.forms import CommentForm
import logging

logger = logging.getLogger(__name__)


@login_required
def comment_edit(request, slug, comment_id):
    """
    Allow users to edit their own comments on prompts.

    Users can only edit comments they authored. Edited comments are reset to
    unapproved status and must be re-approved by admin. Clears relevant caches
    after successful edit.

    Variables:
        slug: URL slug of the prompt
        comment_id: ID of the comment being edited
        prompt: The Prompt object the comment belongs to
        comment: The Comment object being edited
        comment_form: Form for editing the comment

    Template: prompts/comment_edit.html
    URL: /prompt/<slug>/edit_comment/<comment_id>/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author'), slug=slug
    )
    comment = get_object_or_404(
        Comment.objects.select_related('author'), pk=comment_id
    )

    if comment.author != request.user:
        messages.add_message(
            request, messages.ERROR,
            'You can only edit your own comments!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.prompt = prompt
            comment.approved = False
            comment.save()

            # Clear relevant caches
            cache.delete(f"prompt_detail_{slug}_{request.user.id}")

            messages.add_message(
                request, messages.SUCCESS,
                'Comment updated and awaiting approval!'
            )
            return HttpResponseRedirect(
                reverse('prompts:prompt_detail', args=[slug])
            )
        else:
            messages.add_message(
                request, messages.ERROR, 'Error updating comment!'
            )
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


@login_required
@require_POST
def comment_delete(request, slug, comment_id):
    """
    Allow users to delete their own comments.

    Users can only delete comments they authored. Permanently removes the
    comment from the database and clears relevant caches. Redirects back to
    the prompt detail page.

    Variables:
        slug: URL slug of the prompt
        comment_id: ID of the comment being deleted
        prompt: The Prompt object the comment belongs to
        comment: The Comment object being deleted

    Template: None (immediate redirect)
    URL: /prompt/<slug>/delete_comment/<comment_id>/
    """
    prompt = get_object_or_404(
        Prompt.objects.select_related('author'), slug=slug
    )
    comment = get_object_or_404(
        Comment.objects.select_related('author'), pk=comment_id
    )

    if comment.author != request.user:
        messages.add_message(
            request, messages.ERROR,
            'You can only delete your own comments!'
        )
        return HttpResponseRedirect(
            reverse('prompts:prompt_detail', args=[slug])
        )

    comment.delete()

    # Clear relevant caches
    cache.delete(f"prompt_detail_{slug}_{request.user.id}")

    messages.add_message(
        request, messages.SUCCESS,
        'Comment deleted successfully!'
    )
    return HttpResponseRedirect(
        reverse('prompts:prompt_detail', args=[slug])
    )
