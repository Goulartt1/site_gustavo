from django.shortcuts import render

from artist.models import ArtistProfile

from . import services
from .forms import QuoteForm


def quote(request):
    """Pedido de orçamento: verifica a agenda e prepara a mensagem do WhatsApp.

    Atende três tipos de requisição (nada é salvo em nenhuma delas):
    - sem JavaScript: o formulário é enviado e a página inteira volta com a
      resposta (o site funciona mesmo se o HTMX falhar);
    - HTMX "ao vivo" (live=1): a cada campo alterado, devolve só o quadro da
      resposta, sem mexer no formulário que a pessoa está preenchendo;
    - HTMX ao enviar: devolve o bloco do formulário + resposta, com os erros.
    """
    form = QuoteForm(request.POST or None)
    context = {"form": form}
    if request.method == "POST":
        context.update(_answer(form, ArtistProfile.load()))

    if request.headers.get("HX-Request") == "true":
        if request.POST.get("live") == "1":
            return render(request, "quotes/_result.html", context)
        return render(request, "quotes/_block.html", context)
    return render(request, "quotes/index.html", context)


def _answer(form, profile):
    """O que mostrar no quadro da resposta, conforme o que já foi preenchido."""
    if form.is_valid():
        data = form.cleaned_data
        result = services.check_quote(
            profile,
            day=data["day"],
            start_time=data["start_time"],
            duration_minutes=data["duration"],
            event_type=data["event_type"],
            place=data["place"],
            notes=data["notes"],
        )
        return {"result": result}

    if not form.has_availability_fields():
        return {}
    errors = [e for name in form.AVAILABILITY_FIELDS for e in form.errors.get(name, [])]
    if errors:
        return {"availability_errors": errors}
    # Data, horário e duração estão certos: já dá para responder a disponibilidade,
    # mesmo que faltem outros campos para montar a mensagem.
    data = form.cleaned_data
    availability = services.check_availability(data["day"], data["start_time"], data["duration"])
    return {"availability": availability}
