"""
api_views.py — Compatibility shim (Session 128 refactor).

This file re-exports all views from the split domain modules so that
prompts/urls.py requires no changes. Future sessions can update urls.py
to import directly from the domain modules and then remove this shim.

Domain modules:
  - social_api_views.py    — collaborate_request, prompt_like
  - upload_api_views.py    — b2_upload_*, b2_presign_upload, b2_generate_*
  - moderation_api_views.py — nsfw_*, b2_moderate_upload, b2_delete_upload
  - ai_api_views.py        — ai_suggestions, ai_job_status, prompt_processing_status
"""

from prompts.views.social_api_views import (
    collaborate_request,
    prompt_like,
)

from prompts.views.upload_api_views import (
    b2_upload_api,
    b2_generate_variants,
    b2_variants_status,
    b2_upload_status,
    b2_presign_upload,
    b2_upload_complete,
    B2_UPLOAD_RATE_LIMIT,
    B2_UPLOAD_RATE_WINDOW,
)

from prompts.views.moderation_api_views import (
    nsfw_queue_task,
    nsfw_check_status,
    b2_moderate_upload,
    b2_delete_upload,
)

from prompts.views.ai_api_views import (
    ai_suggestions,
    ai_job_status,
    prompt_processing_status,
)

__all__ = [
    'collaborate_request',
    'prompt_like',
    'b2_upload_api',
    'b2_generate_variants',
    'b2_variants_status',
    'b2_upload_status',
    'b2_presign_upload',
    'b2_upload_complete',
    'B2_UPLOAD_RATE_LIMIT',
    'B2_UPLOAD_RATE_WINDOW',
    'nsfw_queue_task',
    'nsfw_check_status',
    'b2_moderate_upload',
    'b2_delete_upload',
    'ai_suggestions',
    'ai_job_status',
    'prompt_processing_status',
]
