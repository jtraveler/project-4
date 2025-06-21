from django.urls import path
from . import views

app_name = 'prompts'
urlpatterns = [
    path('', views.PromptList.as_view(), name='home'),
    path('<slug:slug>/', views.prompt_detail, name='prompt_detail'),  # Ths is sett to use function-based view
]