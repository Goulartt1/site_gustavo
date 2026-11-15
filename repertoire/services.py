"""Regras de negócio do repertório.

Ficam fora das views para que a página (fase 1) e a API (fase 2) usem as
mesmas funções.
"""

from django.core.cache import cache
from django.db.models import Prefetch

from .models import Song, SongSuggestion, Style

# Limite de sugestões por endereço de internet (IP) em uma janela de tempo.
SUGGESTION_LIMIT = 5
SUGGESTION_WINDOW_SECONDS = 60 * 60


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


def suggestion_limit_reached(ip):
    """Diz se este IP já enviou o máximo de sugestões permitido na janela."""
    return cache.get(_suggestion_key(ip), 0) >= SUGGESTION_LIMIT


def register_suggestion_attempt(ip):
    """Conta mais um envio deste IP. A contagem some sozinha ao fim da janela."""
    key = _suggestion_key(ip)
    # add só cria se não existir: o prazo conta a partir do primeiro envio.
    if not cache.add(key, 1, SUGGESTION_WINDOW_SECONDS):
        cache.incr(key)


def _suggestion_key(ip):
    return f"song-suggestion:{ip}"
