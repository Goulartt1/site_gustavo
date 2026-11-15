"""Proteção contra spam dos formulários públicos (decisão 17).

Duas defesas, usadas juntas por todos os formulários que qualquer visitante
pode enviar (sugestão de música, depoimento...):
- campo-isca (HoneypotForm);
- limite de envios por IP (RateLimit).
"""

from django import forms
from django.core.cache import cache

from .client_ip import get_client_ip

LIMIT_MESSAGE = "Recebemos vários envios deste endereço na última hora. Tente de novo mais tarde."


class HoneypotForm(forms.Form):
    """Base para formulários públicos: acrescenta o campo-isca "website".

    Ele fica fora da tela e escondido de leitores de tela, mas robôs costumam
    preencher tudo. Uso: class MeuForm(HoneypotForm, forms.ModelForm).
    """

    website = forms.CharField(
        required=False,
        label="Deixe este campo vazio",
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))


class RateLimit:
    """No máximo `limit` envios por IP a cada `window` segundos.

    A contagem fica no cache do Django, com uma chave por formulário (`scope`)
    e por IP. Ela some sozinha quando a janela termina.
    """

    def __init__(self, scope, limit, window):
        self.scope = scope
        self.limit = limit
        self.window = window

    def reached(self, ip):
        return cache.get(self._key(ip), 0) >= self.limit

    def hit(self, ip):
        key = self._key(ip)
        # add só cria se não existir: o prazo conta a partir do primeiro envio.
        if not cache.add(key, 1, self.window):
            cache.incr(key)

    def _key(self, ip):
        return f"rate-limit:{self.scope}:{ip}"


ACCEPTED = "accepted"
INVALID = "invalid"
LIMITED = "limited"


def submit_public_form(request, form, rate_limit):
    """Processa o envio de um formulário público. Devolve ACCEPTED, INVALID ou LIMITED.

    ACCEPTED também vale para robôs que caíram na isca: recebem a mesma
    resposta de sucesso, mas nada é salvo, e assim não descobrem o truque.
    """
    ip = get_client_ip(request)
    if rate_limit.reached(ip):
        form.add_error(None, LIMIT_MESSAGE)
        return LIMITED
    if not form.is_valid():
        return INVALID
    rate_limit.hit(ip)
    if not form.is_spam():
        form.save()
    return ACCEPTED
