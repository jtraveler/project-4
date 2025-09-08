from django.urls import path
from . import views

app_name = 'prompts'
urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('collaborate/', views.collaborate_request, name='collaborate'),
    path('prompt/create/', views.prompt_create, name='prompt_create'),
    path('prompt/<slug:slug>/', views.prompt_detail, name='prompt_detail'),
    path('prompt/<slug:slug>/edit/', views.prompt_edit, name='prompt_edit'),
    path(
        'prompt/<slug:slug>/delete/',
        views.prompt_delete,
        name='prompt_delete'
    ),
    path(
        'prompt/<slug:slug>/edit_comment/<int:comment_id>/',
        views.comment_edit,
        name='comment_edit'
    ),
    path(
        'prompt/<slug:slug>/delete_comment/<int:comment_id>/',
        views.comment_delete,
        name='comment_delete'
    ),
    path('prompt/<slug:slug>/like/', views.prompt_like, name='prompt_like'),
    
    # New ordering URLs
    path(
        'prompt/<slug:slug>/move-up/',
        views.prompt_move_up,
        name='prompt_move_up'
    ),
    path(
        'prompt/<slug:slug>/move-down/',
        views.prompt_move_down,
        name='prompt_move_down'
    ),
    path(
        'prompt/<slug:slug>/set-order/',
        views.prompt_set_order,
        name='prompt_set_order'
    ),
]