from .models import ArtistProfile
from .whatsapp import whatsapp_url


def artist_profile(request):
    """Disponibiliza o perfil e o link do WhatsApp em todos os templates.

    O cabeçalho, o rodapé e o botão flutuante do WhatsApp aparecem em todas
    as páginas, então todas precisam desses dados.
    """
    profile = ArtistProfile.load()
    return {
        "artist": profile,
        "whatsapp_link": whatsapp_url(profile.whatsapp),
    }
