# Views Package Structure

This directory contains the modular views structure for the prompts application.

## Migration History

| When | What |
|------|------|
| December 2025 | Original 11-module split from monolithic `views.py` (3,929 lines) |
| Session 128 (March 2026) | `api_views.py` split into 4 domain modules + compatibility shim |
| Session 134 (March 2026) | `prompt_views.py` split into 4 domain modules + compatibility shim |
| Session 135 (March 2026) | `prompt_create()` removed from `prompt_edit_views.py` |

## Package Structure (22 modules)

```
prompts/views/
├── __init__.py                  # Re-exports all views (259 lines)
├── STRUCTURE.txt                # ASCII tree diagram
├── README.md                    # This file
│
├── SHIMS (re-export only)
│   ├── prompt_views.py          # → prompt_list/edit/comment/trash (51 lines)
│   └── api_views.py             # → ai_api/moderation_api/social_api/upload_api (62 lines)
│
├── PROMPT DOMAIN MODULES
│   ├── prompt_list_views.py     # PromptList, prompt_detail, related_prompts_ajax (620 lines)
│   ├── prompt_edit_views.py     # prompt_edit (323 lines)
│   ├── prompt_comment_views.py  # comment_edit, comment_delete (139 lines)
│   └── prompt_trash_views.py    # prompt_delete, trash_bin, restore, publish, perm_delete, empty (396 lines)
│
├── API DOMAIN MODULES
│   ├── ai_api_views.py          # ai_suggestions, ai_job_status, prompt_processing_status (298 lines)
│   ├── moderation_api_views.py  # nsfw_queue_task, nsfw_check_status, b2_moderate, b2_delete (340 lines)
│   ├── social_api_views.py      # collaborate_request, prompt_like (111 lines)
│   └── upload_api_views.py      # b2_upload, variants, presign, paste_upload (812 lines)
│
├── UPLOAD & MEDIA
│   ├── upload_views.py          # Upload flow: step1, step2, submit, cancel, extend (751 lines)
│   └── collection_views.py      # Collection CRUD + API endpoints (792 lines)
│
├── USER & SOCIAL
│   ├── user_views.py            # user_profile, edit_profile, email_preferences, report (630 lines)
│   ├── social_views.py          # follow, unfollow, get_follow_status (216 lines)
│   └── notification_views.py    # Notification page + API endpoints (185 lines)
│
├── TOOLS & ADMIN
│   ├── bulk_generator_views.py  # Bulk AI image generator + 8 API endpoints (754 lines)
│   └── admin_views.py           # Admin utilities, ordering, bulk actions (577 lines)
│
├── CONTENT PAGES
│   ├── generator_views.py       # inspiration_index, ai_generator_category (238 lines)
│   └── leaderboard_views.py     # leaderboard (64 lines)
│
├── REDIRECTS
│   └── redirect_views.py        # SEO redirect utilities (119 lines)
│
└── UTILITIES
    └── utility_views.py         # get_client_ip, ratelimited, unsubscribe (448 lines)
```

**Total: 22 modules, 8,185 lines**

## Shim Architecture

Two files exist solely for backward compatibility. They re-export views from domain
modules so that `urls.py` and `__init__.py` imports continue to work:

### prompt_views.py (51 lines — shim)
Re-exports from: `prompt_list_views`, `prompt_edit_views`, `prompt_comment_views`, `prompt_trash_views`

### api_views.py (62 lines — shim)
Re-exports from: `ai_api_views`, `moderation_api_views`, `social_api_views`, `upload_api_views`

## Backward Compatibility

The `__init__.py` file re-exports all views, ensuring complete backward compatibility:

```python
from prompts.views import PromptList, prompt_detail, upload_step1, ...
```

All existing imports continue to work without modification.

## Testing

```bash
python manage.py test
# Expected: 1193+ tests, 0 failures
```

Last updated: Session 136 (March 16, 2026)
