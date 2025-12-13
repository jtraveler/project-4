# Views Package Structure

This directory contains the modular views structure for the prompts application.

## Migration from Monolithic views.py

**Date**: December 13, 2025
**Original File**: `prompts/views.py` (3,929 lines)
**Backup**: `prompts/views.py.backup`

The monolithic `views.py` file has been split into 11 focused modules for better organization and maintainability.

## Package Structure

```
prompts/views/
├── __init__.py                 # Re-exports all views for backward compatibility
├── redirect_views.py           # SEO redirect utilities (119 lines)
├── prompt_views.py             # Prompt CRUD operations (1,711 lines)
├── upload_views.py             # Upload flow (514 lines)
├── user_views.py               # User profiles & settings (521 lines)
├── social_views.py             # Follow/unfollow social features (209 lines)
├── api_views.py                # AJAX/API endpoints (280 lines)
├── admin_views.py              # Admin utility views (251 lines)
├── generator_views.py          # AI generator category pages (225 lines)
├── leaderboard_views.py        # Leaderboard views (68 lines)
├── utility_views.py            # Utility functions (447 lines)
└── README.md                   # This file
```

**Total Lines**: 4,508 (includes module-specific imports)

## Module Breakdown

### redirect_views.py (2 functions)
**Purpose**: SEO utilities for handling deleted prompts
- `calculate_similarity_score()` - Calculate similarity between prompts
- `find_best_redirect_match()` - Find best redirect for deleted prompts

### prompt_views.py (12 functions/classes)
**Purpose**: Core prompt CRUD operations and listing
- `PromptList` - Homepage listing with filtering
- `prompt_detail()` - Display single prompt
- `comment_edit()` - Edit comment
- `comment_delete()` - Delete comment
- `prompt_edit()` - Edit prompt
- `prompt_create()` - Create new prompt
- `prompt_delete()` - Soft delete prompt
- `trash_bin()` - View deleted prompts
- `prompt_restore()` - Restore from trash
- `prompt_publish()` - Publish draft prompt
- `prompt_permanent_delete()` - Hard delete prompt
- `empty_trash()` - Empty entire trash bin

### upload_views.py (5 functions)
**Purpose**: Two-step upload flow
- `upload_step1()` - Initial file upload
- `upload_step2()` - Prompt details form
- `upload_submit()` - Process submission
- `cancel_upload()` - Cancel upload session
- `extend_upload_time()` - Extend upload session

### user_views.py (4 functions)
**Purpose**: User profiles and settings
- `user_profile()` - Display user profile
- `edit_profile()` - Edit profile settings
- `email_preferences()` - Manage email notifications
- `report_prompt()` - Report inappropriate content

### social_views.py (3 functions)
**Purpose**: Social interactions
- `follow_user()` - Follow a user
- `unfollow_user()` - Unfollow a user
- `get_follow_status()` - Check follow status (AJAX)

### api_views.py (6 functions)
**Purpose**: AJAX/API endpoints
- `collaborate_request()` - Collaboration requests
- `prompt_like()` - Like/unlike prompt
- `prompt_move_up()` - Move prompt up in order
- `prompt_move_down()` - Move prompt down in order
- `prompt_set_order()` - Set prompt order
- `bulk_reorder_prompts()` - Bulk reorder (admin)

### admin_views.py (6 functions)
**Purpose**: Admin utility views
- `media_issues_dashboard()` - View media issues
- `fix_all_media_issues()` - Fix all issues
- `debug_no_media()` - Debug missing media
- `bulk_delete_no_media()` - Bulk delete prompts
- `bulk_set_draft_no_media()` - Bulk set as draft
- `bulk_set_published_no_media()` - Bulk publish

### generator_views.py (2 functions)
**Purpose**: AI generator category pages
- `inspiration_index()` - Browse inspiration
- `ai_generator_category()` - Generator-specific pages

### leaderboard_views.py (1 function)
**Purpose**: Community leaderboard
- `leaderboard()` - Display leaderboard rankings

### utility_views.py (6 functions)
**Purpose**: Utility and helper functions
- `get_client_ip()` - Extract client IP address
- `_disable_all_notifications()` - Disable all email notifications
- `ratelimited()` - Rate limit error handler
- `_test_rate_limit_trigger()` - Test rate limiting
- `unsubscribe_custom()` - Custom unsubscribe handler
- `unsubscribe_package()` - Package unsubscribe handler

## Backward Compatibility

The `__init__.py` file re-exports all 47 views, ensuring complete backward compatibility:

```python
from prompts.views import PromptList, prompt_detail, upload_step1, ...
```

All existing imports will continue to work without modification.

## Import Structure

Each module has its own minimal imports. Common imports across all modules:

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from prompts.models import Prompt, Comment, UserProfile
```

Module-specific imports are added as needed.

## Testing

After splitting, verify all tests pass:

```bash
python manage.py test prompts
```

Expected: All 70+ tests should pass without modification.

## Benefits of Modular Structure

1. **Maintainability**: Easier to locate and modify specific views
2. **Code Organization**: Logical grouping by functionality
3. **Readability**: Smaller files are easier to navigate
4. **Team Collaboration**: Reduced merge conflicts
5. **Performance**: Potential for selective imports
6. **Testing**: Easier to write focused unit tests

## Migration Checklist

- [x] Backup original views.py
- [x] Create views/ package directory
- [x] Split functions into 11 modules
- [x] Create __init__.py with re-exports
- [x] Verify Python syntax (all files valid)
- [ ] Run full test suite
- [ ] Verify all URLs still work
- [ ] Check for import errors in production
- [ ] Update documentation references
- [ ] Remove views.py.backup after verification

## Rollback Plan

If issues occur, restore the original:

```bash
mv prompts/views.py.backup prompts/views.py
rm -rf prompts/views/
```

## Future Improvements

- Add docstrings to module-level __init__.py
- Consider further splitting prompt_views.py (largest module)
- Add type hints for better IDE support
- Create views/tests/ subdirectory for module-specific tests
