"""
prompt_views.py — shim for backwards compatibility.

All views have been split into domain modules:
  - prompt_list_views.py   (PromptList, prompt_detail, related_prompts_ajax)
  - prompt_edit_views.py   (prompt_edit, prompt_create)
  - prompt_comment_views.py (comment_edit, comment_delete)
  - prompt_trash_views.py  (prompt_delete, trash_bin, prompt_restore,
                             prompt_publish, prompt_permanent_delete, empty_trash)

This shim exists so any code importing from prompt_views continues to work.
"""

from prompts.views.prompt_list_views import (
    PromptList,
    prompt_detail,
    related_prompts_ajax,
)
from prompts.views.prompt_edit_views import (
    prompt_edit,
    prompt_create,
)
from prompts.views.prompt_comment_views import (
    comment_edit,
    comment_delete,
)
from prompts.views.prompt_trash_views import (
    prompt_delete,
    trash_bin,
    prompt_restore,
    prompt_publish,
    prompt_permanent_delete,
    empty_trash,
)

__all__ = [
    'PromptList',
    'prompt_detail',
    'related_prompts_ajax',
    'prompt_edit',
    'prompt_create',
    'comment_edit',
    'comment_delete',
    'prompt_delete',
    'trash_bin',
    'prompt_restore',
    'prompt_publish',
    'prompt_permanent_delete',
    'empty_trash',
]
