"""
Views package for the prompts application.

This package organizes all views into logical modules while maintaining
backward compatibility with the monolithic views.py structure.
"""

# Import redirect utility functions
from .redirect_views import (
    calculate_similarity_score,
    find_best_redirect_match,
)

# Import prompt CRUD and listing views
from .prompt_views import (
    PromptList,
    prompt_detail,
    comment_edit,
    comment_delete,
    prompt_edit,
    prompt_create,
    prompt_delete,
    trash_bin,
    prompt_restore,
    prompt_publish,
    prompt_permanent_delete,
    empty_trash,
)

# Import upload flow views
from .upload_views import (
    upload_step1,
    upload_step2,
    upload_submit,
    cancel_upload,
    extend_upload_time,
)

# Import user profile and settings views
from .user_views import (
    user_profile,
    edit_profile,
    email_preferences,
    report_prompt,
)

# Import social interaction views
from .social_views import (
    follow_user,
    unfollow_user,
    get_follow_status,
)

# Import API/AJAX endpoints
from .api_views import (
    collaborate_request,
    prompt_like,
    prompt_move_up,
    prompt_move_down,
    prompt_set_order,
    bulk_reorder_prompts,
    b2_upload_api,
)

# Import admin utility views
from .admin_views import (
    media_issues_dashboard,
    fix_all_media_issues,
    debug_no_media,
    bulk_delete_no_media,
    bulk_set_draft_no_media,
    bulk_set_published_no_media,
)

# Import AI generator category views
from .generator_views import (
    inspiration_index,
    ai_generator_category,
)

# Import leaderboard views
from .leaderboard_views import (
    leaderboard,
)

# Import collection views (Phase K)
from .collection_views import (
    api_collections_list,
    api_collection_create,
    api_collection_add_prompt,
    api_collection_remove_prompt,
    collections_list,
    collection_detail,
    collection_edit,
    collection_delete,
    user_collections,
)

# Import utility views
from .utility_views import (
    get_client_ip,
    _disable_all_notifications,
    ratelimited,
    _test_rate_limit_trigger,
    unsubscribe_custom,
    unsubscribe_package,
    unsubscribe_view,
)

# Define __all__ for explicit exports
__all__ = [
    # Redirect utilities
    'calculate_similarity_score',
    'find_best_redirect_match',

    # Prompt views
    'PromptList',
    'prompt_detail',
    'comment_edit',
    'comment_delete',
    'prompt_edit',
    'prompt_create',
    'prompt_delete',
    'trash_bin',
    'prompt_restore',
    'prompt_publish',
    'prompt_permanent_delete',
    'empty_trash',

    # Upload views
    'upload_step1',
    'upload_step2',
    'upload_submit',
    'cancel_upload',
    'extend_upload_time',

    # User views
    'user_profile',
    'edit_profile',
    'email_preferences',
    'report_prompt',

    # Social views
    'follow_user',
    'unfollow_user',
    'get_follow_status',

    # API views
    'collaborate_request',
    'prompt_like',
    'prompt_move_up',
    'prompt_move_down',
    'prompt_set_order',
    'bulk_reorder_prompts',
    'b2_upload_api',

    # Admin views
    'media_issues_dashboard',
    'fix_all_media_issues',
    'debug_no_media',
    'bulk_delete_no_media',
    'bulk_set_draft_no_media',
    'bulk_set_published_no_media',

    # Generator views
    'inspiration_index',
    'ai_generator_category',

    # Leaderboard views
    'leaderboard',

    # Collection views (Phase K)
    'api_collections_list',
    'api_collection_create',
    'api_collection_add_prompt',
    'api_collection_remove_prompt',
    'collections_list',
    'collection_detail',
    'collection_edit',
    'collection_delete',
    'user_collections',

    # Utility views
    'get_client_ip',
    '_disable_all_notifications',
    'ratelimited',
    '_test_rate_limit_trigger',
    'unsubscribe_custom',
    'unsubscribe_package',
    'unsubscribe_view',
]
