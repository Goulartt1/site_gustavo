from django.templatetags.static import static


def seo(request):
    """Endereços absolutos usados nas meta tags (o Google e o WhatsApp exigem).

    - canonical_url: o endereço "oficial" da página, sem parâmetros (?a=b),
      para o Google não tratar variações como páginas diferentes;
    - og_image_url: a imagem da prévia de compartilhamento.

    Atrás do Cloudflare, o domínio e o https vêm dos cabeçalhos X-Forwarded-*
    (USE_X_FORWARDED_HOST e SECURE_PROXY_SSL_HEADER no settings).
    """
    return {
        "canonical_url": request.build_absolute_uri(request.path),
        "og_image_url": request.build_absolute_uri(static("img/og-default.png")),
    }
