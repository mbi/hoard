from apps.hoarder.views import record
from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve as static_serve
from django_otp.admin import OTPAdminSite

# Enforce 2FA only in production.
if not settings.DEBUG:
    admin.site.__class__ = OTPAdminSite

admin.autodiscover()


urlpatterns = [
    path("api/hoard/<slug:slug>", record, name="record"),
]

if settings.DEBUG:
    urlpatterns = [
        re_path(
            r"^media/(?P<path>.*)$",
            static_serve,
            {"document_root": settings.MEDIA_ROOT, "show_indexes": True},
        ),
    ] + urlpatterns

    for prefix, root in settings.DEV_STATIC_URLS.items():
        urlpatterns.append(
            re_path(prefix, static_serve, {"document_root": root, "show_indexes": True})
        )

urlpatterns += [
    path("", admin.site.urls),
]
