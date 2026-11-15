"""Dados estruturados (JSON-LD) para o Google entender quem é o artista.

O Google lê um bloco <script type="application/ld+json"> com o vocabulário do
schema.org e pode usar essas informações nos resultados de busca (nome,
estilos, redes sociais).
"""

import json

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from repertoire.models import Style

register = template.Library()

# Mesmos escapes do json_script do Django: impedem que um texto com "</script>"
# feche o bloco antes da hora.
# Strings cruas (r"..."): a barra invertida fica no texto, como o JSON espera.
_ESCAPES = {ord("<"): r"\u003C", ord(">"): r"\u003E", ord("&"): r"\u0026"}


def artist_structured_data(request, artist):
    """Dicionário schema.org (MusicGroup) com os dados públicos do artista."""
    same_as = [url for url in (artist.instagram_url, artist.youtube_url, artist.spotify_url) if url]
    data = {
        "@context": "https://schema.org",
        "@type": "MusicGroup",
        "name": artist.name,
        "url": request.build_absolute_uri("/"),
        "image": request.build_absolute_uri(static("img/og-default.png")),
        "genre": list(Style.objects.values_list("name", flat=True)),
    }
    if artist.headline:
        data["description"] = artist.headline
    if artist.city:
        data["location"] = {"@type": "Place", "name": artist.city}
    if same_as:
        data["sameAs"] = same_as
    return data


@register.simple_tag(takes_context=True)
def artist_jsonld(context):
    data = artist_structured_data(context["request"], context["artist"])
    payload = json.dumps(data, ensure_ascii=False).translate(_ESCAPES)
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')
