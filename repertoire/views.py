from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from core.client_ip import get_client_ip

from . import services
from .forms import SongSuggestionForm

LIMIT_MESSAGE = (
    "Recebemos várias sugestões deste endereço na última hora. Tente de novo mais tarde."
)
THANKS_MESSAGE = "Obrigado pela sugestão! Ela vai ser lida antes de entrar no repertório."


def repertoire(request):
    """Página do repertório, com o formulário de sugestão no fim."""
    form = SongSuggestionForm(request.POST or None)
    status = 200

    if request.method == "POST":
        ip = get_client_ip(request)
        if services.suggestion_limit_reached(ip):
            form.add_error(None, LIMIT_MESSAGE)
            status = 429  # Too Many Requests
        elif form.is_valid():
            services.register_suggestion_attempt(ip)
            # Robô que caiu na isca recebe a mesma resposta de sucesso, mas
            # nada é salvo: assim ele não descobre o truque.
            if not form.is_spam():
                form.save()
            messages.success(request, THANKS_MESSAGE)
            # Post/Redirect/Get: recarregar a página não reenvia o formulário.
            # Volta direto para o formulário, onde aparece o "obrigado".
            return redirect(reverse("repertoire:index") + "#sugerir")

    context = {"styles": services.public_repertoire(), "form": form}
    return render(request, "repertoire/index.html", context, status=status)
