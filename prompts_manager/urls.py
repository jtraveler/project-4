"""
URL configuration for prompts_manager project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from prompts.admin import trash_dashboard
from prompts import views as maintenance_views
from prompts.views import admin_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

# Customize admin site headers
admin.site.site_header = "Prompts Manager Administration"
admin.site.site_title = "Prompts Manager Admin"
admin.site.index_title = "Welcome to Prompts Manager Administration"

urlpatterns = [
    # Admin maintenance tools - registered at top level for clean URLs
    path('admin/trash-dashboard/', trash_dashboard, name='admin_trash_dashboard'),
    path('admin/media-issues/', maintenance_views.media_issues_dashboard, name='admin_media_issues_dashboard'),
    path('admin/fix-media-issues/', maintenance_views.fix_all_media_issues, name='admin_fix_media_issues'),
    path('admin/debug-no-media/', maintenance_views.debug_no_media, name='admin_debug_no_media'),
    path('admin/bulk-delete-no-media/', maintenance_views.bulk_delete_no_media, name='bulk_delete_no_media'),
    path('admin/bulk-set-published-no-media/', maintenance_views.bulk_set_published_no_media, name='bulk_set_published_no_media'),
    path('admin/bulk-set-draft-no-media/', maintenance_views.bulk_set_draft_no_media, name='bulk_set_draft_no_media'),

    # SEO Review Queue (L10c)
    path('admin/seo-review/', admin_views.seo_review_queue, name='admin_seo_review_queue'),
    path('admin/seo-review/<int:prompt_id>/complete/', admin_views.mark_seo_complete, name='admin_mark_seo_complete'),

    # Tag autocomplete (django-autocomplete-light)
    path('admin/tag-autocomplete/', admin_views.TagAutocomplete.as_view(), name='tag-autocomplete'),

    # Django admin
    path('admin/', admin.site.urls),

    # Favicon route
    path('favicon.ico', RedirectView.as_view(
        url=staticfiles_storage.url('favicon.ico'),
        permanent=True
    ), name='favicon'),

    # robots.txt served by WhiteNoise via WHITENOISE_ROOT setting

    # Other apps
    path("summernote/", include('django_summernote.urls')),
    path("about/", include("about.urls")),
    path("accounts/", include("allauth.urls")),

    # Prompts app (last to avoid conflicts)
    path("", include("prompts.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
