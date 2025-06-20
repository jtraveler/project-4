"""
URL configuration for prompts_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# Customize admin site headers
admin.site.site_header = "Prompts Manager Administration"
admin.site.site_title = "Prompts Manager Admin"
admin.site.index_title = "Welcome to Prompts Manager Administration"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("summernote/", include('django_summernote.urls')),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("prompts.urls"), name="prompts-urls"),
]
