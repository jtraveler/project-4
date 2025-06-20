from django.urls import path
from . import views

app_name = 'prompts'
urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('<slug:slug>/', views.PromptDetail.as_view(), name='prompt_detail'),  # Changed from <int:pk>
]