from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from core import antispam

from . import services
from .forms import SongSuggestionForm

THANKS_MESSAGE = "Obrigado pela sugestão! Ela vai ser lida antes de entrar no repertório."


def repertoire(request):
    """Página do repertório, com o formulário de sugestão no fim."""
    form = SongSuggestionForm(request.POST or None)
    status = 200

    if request.method == "POST":
        result = antispam.submit_public_form(request, form, services.suggestion_rate_limit)
        if result == antispam.ACCEPTED:
            messages.success(request, THANKS_MESSAGE)
            # Post/Redirect/Get: recarregar a página não reenvia o formulário.
            # Volta direto para o formulário, onde aparece o "obrigado".
            return redirect(reverse("repertoire:index") + "#sugerir")
        if result == antispam.LIMITED:
            status = 429  # Too Many Requests

    context = {"styles": services.public_repertoire(), "form": form}
    return render(request, "repertoire/index.html", context, status=status)
