"""Regras de negócio dos depoimentos (fora das views, para a API reaproveitar)."""

from core.antispam import RateLimit

from .models import Testimonial

# No máximo 3 depoimentos por hora por endereço de internet (IP).
testimonial_rate_limit = RateLimit("testimonial", limit=3, window=60 * 60)


def approved_testimonials(limit=None):
    """Depoimentos aprovados, do mais novo para o mais antigo."""
    testimonials = Testimonial.objects.filter(status=Testimonial.Status.APPROVED)
    if limit is not None:
        testimonials = testimonials[:limit]
    return list(testimonials)


def approve_testimonials(testimonials):
    """Aprova: os depoimentos passam a aparecer no site. Devolve quantos mudaram."""
    return testimonials.update(status=Testimonial.Status.APPROVED)


def reject_testimonials(testimonials):
    """Recusa: os depoimentos não aparecem no site. Devolve quantos mudaram."""
    return testimonials.update(status=Testimonial.Status.REJECTED)
