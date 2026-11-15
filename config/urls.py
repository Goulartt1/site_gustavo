"""Rotas do projeto. Cada app tem as suas em <app>/urls.py."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from core.sitemaps import PublicPagesSitemap
from core.views import robots_txt

urlpatterns = [
    path("admin/", admin.site.urls),
    # Para buscadores: o que podem ler e a lista de páginas do site.
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"pages": PublicPagesSitemap}},
        name="sitemap",
    ),
    path("repertorio/", include("repertoire.urls")),
    path("depoimentos/", include("testimonials.urls")),
    path("orcamento/", include("quotes.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    # Em desenvolvimento, o próprio Django serve as fotos enviadas pelo Admin.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
