from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from . import views_admin
from .views import api_views
from .views import admin_views  # For prompt ordering functions

app_name = 'prompts'

urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    # 301 redirect: /create-prompt/ → /upload/ (SEO preservation)
    path('create-prompt/',
         RedirectView.as_view(pattern_name='prompts:upload_step1', permanent=True),
         name='prompt_create'),
    path('collaborate/', views.collaborate_request, name='collaborate'),
    # Upload flow (Phase C & D)
    path('upload/', views.upload_step1, name='upload_step1'),
    path('upload/details', views.upload_step2, name='upload_step2'),
    path('upload/submit', views.upload_submit, name='upload_submit'),
    # Upload idle detection endpoints
    path('upload/cancel/', views.cancel_upload, name='cancel_upload'),
    path('upload/extend/', views.extend_upload_time, name='extend_upload_time'),
    # N4d: Processing page (shown while AI generates content)
    path('prompt/processing/<uuid:processing_uuid>/', views.prompt_processing, name='prompt_processing'),
    path('prompt/<slug:slug>/', views.prompt_detail, name='prompt_detail'),
    path('prompt/<slug:slug>/edit/', views.prompt_edit, name='prompt_edit'),
    path('prompt/<slug:slug>/delete/', views.prompt_delete, name='prompt_delete'),
    path('prompt/<slug:slug>/publish/', views.prompt_publish, name='prompt_publish'),
    path('prompt/<slug:slug>/like/', views.prompt_like, name='prompt_like'),
    # Trash bin URLs (Phase D.5)
    path('trash/', views.trash_bin, name='trash_bin'),
    path('trash/<slug:slug>/restore/', views.prompt_restore, name='prompt_restore'),
    path('trash/<slug:slug>/delete-forever/', views.prompt_permanent_delete, name='prompt_permanent_delete'),
    path('trash/empty/', views.empty_trash, name='empty_trash'),
    # User profile URLs (Phase E)
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path('users/<str:username>/trash/', views.user_profile, {'active_tab': 'trash'}, name='user_profile_trash'),
    path('users/<str:username>/collections/', views.user_collections, name='user_collections'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    # Follow system URLs (Phase F Day 1)
    path('users/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('users/<str:username>/unfollow/', views.unfollow_user, name='unfollow_user'),
    path('users/<str:username>/follow-status/', views.get_follow_status, name='follow_status'),
    # Email preferences (Phase E Task 4)
    path('settings/notifications/', views.email_preferences, name='email_preferences'),
    path('unsubscribe/<str:token>/', views.unsubscribe_view, name='unsubscribe'),
    # Rate limit error page (for testing and direct access)
    path('rate-limited/', views.ratelimited, name='ratelimited'),
    # Report prompt URL (Phase E Task 3)
    path('prompt/<slug:slug>/report/', views.report_prompt, name='report_prompt'),
    # Prompts Hub and Generator Category Pages (Phase I URL Migration)
    # NEW primary URL structure at /prompts/
    path('prompts/',
         views.inspiration_index,
         name='prompts_hub'),
    path('prompts/<slug:generator_slug>/',
         views.ai_generator_category,
         name='ai_generator_category'),

    # Legacy redirects (301 permanent) - preserves SEO equity
    path('inspiration/',
         RedirectView.as_view(url='/prompts/', permanent=True),
         name='inspiration_redirect'),
    path('inspiration/ai/<slug:generator_slug>/',
         RedirectView.as_view(pattern_name='prompts:ai_generator_category', permanent=True, query_string=True),
         name='inspiration_ai_redirect'),
    path('ai/<slug:generator_slug>/',
         RedirectView.as_view(pattern_name='prompts:ai_generator_category', permanent=True, query_string=True),
         name='ai_generator_redirect'),
    path('ai/',
         RedirectView.as_view(url='/prompts/', permanent=True),
         name='ai_directory_redirect'),
    # Leaderboard (Phase G Part C)
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # B2 Upload API (Phase L)
    path('api/upload/b2/', views.b2_upload_api, name='b2_upload_api'),
    path('api/upload/b2/variants/', views.b2_generate_variants, name='b2_generate_variants'),
    path('api/upload/b2/variants/status/', views.b2_variants_status, name='b2_variants_status'),

    # B2 Direct Upload API (Phase L8-DIRECT)
    path('api/upload/b2/presign/', views.b2_presign_upload, name='b2_presign_upload'),
    path('api/upload/b2/complete/', views.b2_upload_complete, name='b2_upload_complete'),

    # NSFW Moderation API (Step 1 Blocking)
    path('api/upload/b2/moderate/', views.b2_moderate_upload, name='b2_moderate_upload'),
    path('api/upload/b2/delete/', views.b2_delete_upload, name='b2_delete_upload'),

    # AI Suggestions API (Step 2 Deferred - L8-STEP2-PERF)
    path('api/upload/ai-suggestions/', views.ai_suggestions, name='ai_suggestions'),

    # Collections API (Phase K)
    path('api/collections/', views.api_collections_list, name='api_collections_list'),
    path('api/collections/create/', views.api_collection_create, name='api_collection_create'),
    path('api/collections/<int:collection_id>/add/', views.api_collection_add_prompt, name='api_collection_add_prompt'),
    path('api/collections/<int:collection_id>/remove/', views.api_collection_remove_prompt, name='api_collection_remove_prompt'),

    # Collections pages (Phase K)
    path('collections/', views.collections_list, name='collections_list'),
    path('collections/<slug:slug>/', views.collection_detail, name='collection_detail'),
    path('collections/<slug:slug>/edit/', views.collection_edit, name='collection_edit'),
    path('collections/<slug:slug>/delete/', views.collection_delete, name='collection_delete'),
    path('prompt/<slug:slug>/edit_comment/<int:comment_id>/',
         views.comment_edit, name='comment_edit'),
    path('prompt/<slug:slug>/delete_comment/<int:comment_id>/',
         views.comment_delete, name='comment_delete'),
    
    # Admin ordering URLs (moved to admin_views.py)
    path('prompt/<slug:slug>/move-up/', admin_views.prompt_move_up, name='prompt_move_up'),
    path('prompt/<slug:slug>/move-down/', admin_views.prompt_move_down, name='prompt_move_down'),
    path('prompt/<slug:slug>/set-order/', admin_views.prompt_set_order, name='prompt_set_order'),
    path('prompts-admin/bulk-reorder/', admin_views.bulk_reorder_prompts, name='bulk_reorder_prompts'),
    
    # B2 Upload Status API
    path('api/upload/b2/status/', api_views.b2_upload_status, name='b2_upload_status'),
    # NSFW Moderation API (Phase N2 - Background Validation)
    path('api/upload/nsfw/queue/', api_views.nsfw_queue_task, name='nsfw_queue_task'),
    path('api/upload/nsfw/status/', api_views.nsfw_check_status, name='nsfw_check_status'),
    # Alias for N3 upload template compatibility
    path('api/upload/nsfw/status/', api_views.nsfw_check_status, name='nsfw_status'),

    # N4f: Processing status polling endpoint
    path('api/prompt/status/<uuid:processing_uuid>/', views.prompt_processing_status, name='prompt_processing_status'),

    # N4-Refactor: AI job status polling endpoint (cache-based)
    path('api/ai-job-status/<str:job_id>/', api_views.ai_job_status, name='ai_job_status'),

    # Admin moderation dashboard
    path('admin/moderation-dashboard/', views_admin.moderation_dashboard, name='moderation_dashboard'),
    # Note: admin maintenance tools (media-issues, debug/no-media, fix-media-issues, trash-dashboard)
    # are registered in prompts_manager/urls.py at top-level (no namespace) for clean /admin/* URLs
]