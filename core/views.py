from django.shortcuts import render

from testimonials.services import approved_testimonials

# Quantos depoimentos aparecem na página inicial (os mais novos).
HOME_TESTIMONIALS = 3


def home(request):
    # O perfil do artista chega ao template pelo context processor
    # (artist.context_processors.artist_profile). Aqui entram os dados de cada
    # seção, buscados pelas regras de negócio de cada app.
    context = {"testimonials": approved_testimonials(limit=HOME_TESTIMONIALS)}
    return render(request, "core/home.html", context)
