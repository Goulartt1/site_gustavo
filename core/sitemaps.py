from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PublicPagesSitemap(Sitemap):
    """Páginas públicas do site, para o Google encontrar todas."""

    changefreq = "weekly"

    # Nome da rota e prioridade relativa (0.0 a 1.0) de cada página.
    pages = {
        "core:home": 1.0,
        "quotes:index": 0.9,
        "repertoire:index": 0.7,
        "testimonials:index": 0.6,
    }

    def items(self):
        return list(self.pages)

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.pages[item]
