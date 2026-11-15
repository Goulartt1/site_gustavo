"""Regras de negócio do repertório.

Ficam fora das views para que a página (fase 1) e a API (fase 2) usem as
mesmas funções.
"""

from django.db.models import Prefetch

from core.antispam import RateLimit

from .models import Song, SongSuggestion, Style

# No máximo 5 sugestões por hora por endereço de internet (IP).
suggestion_rate_limit = RateLimit("song-suggestion", limit=5, window=60 * 60)


def public_repertoire():
    """Estilos que têm músicas ativas, cada um com as suas músicas.

    Duas consultas ao banco no total (estilos + músicas), não uma por estilo.
    """
    active_songs = Song.objects.filter(is_active=True)
    styles = (
        Style.objects.filter(songs__is_active=True)
        .distinct()
        .prefetch_related(Prefetch("songs", queryset=active_songs, to_attr="active_songs"))
    )
    return list(styles)


def accept_suggestions(suggestions):
    """Marca as sugestões como aceitas ("vou aprender"). Devolve quantas mudaram.

    Não cria a música no repertório: o artista cadastra quando já estiver
    tocando, para o site nunca anunciar o que ainda não está pronto.
    """
    return suggestions.update(status=SongSuggestion.Status.ACCEPTED)


def reject_suggestions(suggestions):
    """Marca as sugestões como recusadas. Devolve quantas mudaram."""
    return suggestions.update(status=SongSuggestion.Status.REJECTED)
