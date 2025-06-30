"""
URL configuration for prompts_manager project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site headers
admin.site.site_header = "Prompts Manager Administration"
admin.site.site_title = "Prompts Manager Admin"
admin.site.index_title = "Welcome to Prompts Manager Administration"

urlpatterns = [
    path("about/", include("about.urls"), name="about-urls"),
    path("admin/", admin.site.urls),
    path("summernote/", include('django_summernote.urls')),
    path("accounts/", include("allauth.urls")),
    path("", include("prompts.urls"), name="prompts-urls"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)