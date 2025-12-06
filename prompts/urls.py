from django.urls import path
from . import views
from . import views_admin

app_name = 'prompts'

urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('create-prompt/', views.prompt_create, name='prompt_create'),
    path('collaborate/', views.collaborate_request, name='collaborate'),
    # Upload flow (Phase C & D)
    path('upload/', views.upload_step1, name='upload_step1'),
    path('upload/details', views.upload_step2, name='upload_step2'),
    path('upload/submit', views.upload_submit, name='upload_submit'),
    # Upload idle detection endpoints
    path('upload/cancel/', views.cancel_upload, name='cancel_upload'),
    path('upload/extend/', views.extend_upload_time, name='extend_upload_time'),
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
    # AI Generator Category Pages (SEO Phase 3)
    path('ai/<slug:generator_slug>/', views.ai_generator_category, name='ai_generator_category'),
    # Leaderboard (Phase G Part C)
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('prompt/<slug:slug>/edit_comment/<int:comment_id>/',
         views.comment_edit, name='comment_edit'),
    path('prompt/<slug:slug>/delete_comment/<int:comment_id>/',
         views.comment_delete, name='comment_delete'),
    # Admin ordering URLs
    path('prompt/<slug:slug>/move-up/', views.prompt_move_up, name='prompt_move_up'),
    path('prompt/<slug:slug>/move-down/', views.prompt_move_down, name='prompt_move_down'),
    path('prompt/<slug:slug>/set-order/', views.prompt_set_order, name='prompt_set_order'),
    path('prompts-admin/bulk-reorder/', views.bulk_reorder_prompts, name='bulk_reorder_prompts'),
    # Admin moderation dashboard
    path('admin/moderation-dashboard/', views_admin.moderation_dashboard, name='moderation_dashboard'),
    # Note: admin maintenance tools (media-issues, debug/no-media, fix-media-issues, trash-dashboard)
    # are registered in prompts_manager/urls.py at top-level (no namespace) for clean /admin/* URLs
]