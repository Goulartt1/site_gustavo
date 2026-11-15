"""Descobre o endereço de internet (IP) de quem está visitando."""

from django.conf import settings


def get_client_ip(request):
    """IP do visitante.

    Em produção, quem fala com o Django é o Worker do Cloudflare, então
    REMOTE_ADDR seria o endereço do Cloudflare, igual para todo mundo. O Worker
    repassa o IP verdadeiro no cabeçalho X-Client-IP.

    Só confiamos nesse cabeçalho quando ORIGIN_SECRET está definido: aí o
    middleware já garantiu que a visita veio do Worker. Sem ele (desenvolvimento),
    qualquer um poderia inventar o cabeçalho, então usamos REMOTE_ADDR.
    """
    if settings.ORIGIN_SECRET:
        forwarded = request.META.get("HTTP_X_CLIENT_IP", "").strip()
        if forwarded:
            return forwarded
    return request.META.get("REMOTE_ADDR", "")
