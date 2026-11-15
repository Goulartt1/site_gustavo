from django.shortcuts import render


def home(request):
    # O perfil do artista chega ao template pelo context processor
    # (artist.context_processors.artist_profile). As próximas etapas
    # acrescentam aqui os dados de cada seção (agenda, galeria...).
    return render(request, "core/home.html")
