"""
Shared module-level constants for the prompts.models package.

Extracted from the pre-split prompts/models.py in Session 168-D.
Exposed at package level via __init__.py where external consumers
exist (notably AI_GENERATOR_CHOICES).
"""

# Add status choices
STATUS = ((0, "Draft"), (1, "Published"))

# Moderation status choices
MODERATION_STATUS = (
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('flagged', 'Flagged for Manual Review'),
)

# Moderation service types
MODERATION_SERVICE = (
    ('profanity', 'Custom Profanity Filter'),
    ('openai', 'OpenAI Moderation API'),
    ('openai_vision', 'OpenAI Vision API'),
)

# AI Generator choices.
#
# Canonical rule (Session 169-B): every key MUST match
# ^[a-z0-9][a-z0-9-]*$ — lowercase letters, digits, dashes only. No
# dots, underscores, slashes, or whitespace. Display strings (second
# tuple position) can be anything including dots and uppercase.
# Enforced by prompts/tests/test_generator_slug_validation.py and by
# RegexValidator on Prompt.ai_generator. See
# docs/REPORT_169_A_GENERATOR_SLUG_DIAGNOSTIC.md for the rationale.
AI_GENERATOR_CHOICES = [
    # Legacy entries (kept for backward compatibility):
    ('midjourney', 'Midjourney'),
    ('dall-e-3', 'DALL-E 3'),
    ('stable-diffusion', 'Stable Diffusion'),
    ('adobe-firefly', 'Adobe Firefly'),
    ('flux', 'Flux'),
    ('sora', 'Sora'),
    ('leonardo-ai', 'Leonardo AI'),
    ('ideogram', 'Ideogram'),
    ('runwayml', 'RunwayML'),
    ('gpt-image-1', 'GPT-Image-1'),
    ('gpt-image-1-5', 'GPT-Image-1.5'),  # CHANGED 169-B: dash form (was 'gpt-image-1.5')
    # GeneratorModel-derived entries (Session 169-B — match GeneratorModel.slug values):
    ('gpt-image-1-5-byok', 'GPT-Image-1.5 (BYOK)'),
    ('gpt-image-2-byok', 'GPT Image 2 (BYOK)'),
    ('flux-schnell', 'Flux Schnell'),
    ('flux-dev', 'Flux Dev'),
    ('flux-1-1-pro', 'Flux 1.1 Pro'),
    ('flux-2-pro', 'FLUX 2 Pro'),
    ('grok-imagine', 'Grok Imagine'),
    ('nano-banana-2', 'Nano Banana 2'),
    # Catch-all:
    ('other', 'Other'),
]

# Deletion reason choices
DELETION_REASONS = [
    ('user', 'User Deleted'),
    ('orphaned_image', 'Orphaned Cloudinary File'),
    ('missing_image', 'Prompt Missing Image'),
    ('moderation', 'Content Moderation'),
    ('admin_manual', 'Admin Manual Delete'),
    ('expired_upload', 'Abandoned Upload Session'),
]


# --- Type-to-Category mapping for notifications ---
NOTIFICATION_TYPE_CATEGORY_MAP = {
    'comment_on_prompt': 'comments',
    'reply_to_comment': 'comments',
    'prompt_liked': 'likes',
    'new_follower': 'follows',
    'prompt_saved': 'collections',
    'system': 'system',
    'bulk_gen_job_completed': 'system',
    'bulk_gen_job_failed': 'system',
    'bulk_gen_published': 'system',
    'bulk_gen_partial': 'system',
    'nsfw_repeat_offender': 'system',
    'openai_quota_alert': 'system',
}


# Module-level display map for BulkGenerationJob sizes.
# List comprehensions in class bodies cannot reference class-level names,
# so this must live at module scope.
_BULK_SIZE_DISPLAY = {
    '1024x1024': 'Square (1:1)',
    '1024x1536': 'Portrait (2:3)',
    '1536x1024': 'Landscape (3:2)',
    '1792x1024': 'Wide (16:9) — UNSUPPORTED (future use)',
}
