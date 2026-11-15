"""Regra de negócio: montar links do WhatsApp.

Fica fora das views e dos templates para servir igual ao site (fase 1)
e à API (fase 2).
"""

from urllib.parse import quote

DEFAULT_MESSAGE = "Olá! Vi o site e gostaria de um orçamento para um show."


def whatsapp_url(number, message=DEFAULT_MESSAGE):
    """Link que abre uma conversa no WhatsApp com a mensagem já escrita.

    Devolve "" quando não há número, para o template esconder o botão.
    """
    digits = "".join(ch for ch in (number or "") if ch.isdigit())
    if not digits:
        return ""
    return f"https://wa.me/{digits}?text={quote(message)}"
