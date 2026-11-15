from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from core import antispam

from . import services
from .forms import TestimonialForm

THANKS_MESSAGE = "Obrigado pelo depoimento! Ele aparece aqui depois de aprovado."


def testimonials(request):
    """Depoimentos aprovados, com o formulário para deixar o seu no fim."""
    form = TestimonialForm(request.POST or None)
    status = 200

    if request.method == "POST":
        result = antispam.submit_public_form(request, form, services.testimonial_rate_limit)
        if result == antispam.ACCEPTED:
            messages.success(request, THANKS_MESSAGE)
            return redirect(reverse("testimonials:index") + "#deixar")
        if result == antispam.LIMITED:
            status = 429

    context = {"testimonials": services.approved_testimonials(), "form": form}
    return render(request, "testimonials/index.html", context, status=status)
