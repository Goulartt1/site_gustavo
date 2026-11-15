from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from testimonials.services import approved_testimonials

# Quantos depoimentos aparecem na página inicial (os mais novos).
HOME_TESTIMONIALS = 3


def home(request):
    # O perfil do artista chega ao template pelo context processor
    # (artist.context_processors.artist_profile). Aqui entram os dados de cada
    # seção, buscados pelas regras de negócio de cada app.
    context = {"testimonials": approved_testimonials(limit=HOME_TESTIMONIALS)}
    return render(request, "core/home.html", context)


@require_GET
def robots_txt(request):
    """Instruções para robôs de busca: podem ler tudo, menos o Admin."""
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = ["User-agent: *", "Disallow: /admin/", "", f"Sitemap: {sitemap_url}", ""]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")
