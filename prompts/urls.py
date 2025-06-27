from django.urls import path
from . import views

app_name = 'prompts'
urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('collaborate/', views.collaborate_request, name='collaborate'),
    path('create-prompt/', views.prompt_create, name='prompt_create'),
    path('<slug:slug>/', views.prompt_detail, name='prompt_detail'),
    path('<slug:slug>/edit/', views.prompt_edit, name='prompt_edit'),
    path('<slug:slug>/delete/', views.prompt_delete, name='prompt_delete'),
    path('<slug:slug>/edit_comment/<int:comment_id>/', views.comment_edit, name='comment_edit'),
    path('<slug:slug>/delete_comment/<int:comment_id>/', views.comment_delete, name='comment_delete'),
    path('<slug:slug>/like/', views.prompt_like, name='prompt_like'),
]