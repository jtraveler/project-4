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
    # Step 2 will be added in Phase D
    path('prompt/<slug:slug>/', views.prompt_detail, name='prompt_detail'),
    path('prompt/<slug:slug>/edit/', views.prompt_edit, name='prompt_edit'),
    path('prompt/<slug:slug>/delete/', views.prompt_delete, name='prompt_delete'),
    path('prompt/<slug:slug>/like/', views.prompt_like, name='prompt_like'),
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
]