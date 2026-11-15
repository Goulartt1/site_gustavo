"""Rotas do projeto. Cada app tem as suas em <app>/urls.py."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("repertorio/", include("repertoire.urls")),
    path("depoimentos/", include("testimonials.urls")),
    path("orcamento/", include("quotes.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Em desenvolvimento, o próprio Django serve as fotos enviadas pelo Admin.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
