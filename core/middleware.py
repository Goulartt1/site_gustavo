import hmac

from django.conf import settings
from django.http import HttpResponseForbidden


class RequireOriginSecretMiddleware:
    """Recusa visitas que não passaram pelo Worker do Cloudflare.

    O Worker envia o cabeçalho X-Origin-Secret com o valor de ORIGIN_SECRET.
    Sem ORIGIN_SECRET definido (desenvolvimento e testes), não faz nada.
    """

    header = "HTTP_X_ORIGIN_SECRET"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        expected = settings.ORIGIN_SECRET
        if expected:
            received = request.META.get(self.header, "")
            # compare_digest compara sem vazar, pelo tempo de resposta,
            # quantos caracteres estavam certos.
            if not hmac.compare_digest(received, expected):
                return HttpResponseForbidden("Acesso direto não permitido.")
        return self.get_response(request)
