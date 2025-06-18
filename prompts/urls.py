from django.urls import path
from . import views

urlpatterns = [
    path('prompts/', views.my_prompts, name='prompts'),
]