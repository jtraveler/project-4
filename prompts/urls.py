from django.urls import path
from . import views

app_name = 'prompts'
urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('<int:pk>/', views.PromptDetail.as_view(), name='prompt_detail'),
]