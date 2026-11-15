from datetime import timedelta

from django import forms
from django.utils import timezone

from . import services

EVENT_TYPES = [
    "Bar ou restaurante",
    "Aniversário",
    "Casamento",
    "Baile ou evento tradicional",
    "Evento corporativo",
    "Outro",
]

# De 1h a 8h, de meia em meia hora (valores em minutos).
DURATION_CHOICES = [(m, services.format_duration(m)) for m in range(60, 8 * 60 + 1, 30)]

MAX_DAYS_AHEAD = 2 * 365


class QuoteForm(forms.Form):
    """Pedido de orçamento. Nada é salvo: os dados viram a mensagem do WhatsApp."""

    event_type = forms.ChoiceField(
        label="Tipo de evento", choices=[("", "Escolha…")] + [(t, t) for t in EVENT_TYPES]
    )
    day = forms.DateField(label="Data", widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(
        label="Horário de início", widget=forms.TimeInput(attrs={"type": "time"})
    )
    duration = forms.TypedChoiceField(
        label="Duração", coerce=int, choices=[("", "Escolha…")] + DURATION_CHOICES
    )
    place = forms.CharField(
        label="Cidade e bairro, ou nome do local",
        max_length=120,
        help_text="Não precisa do endereço completo: serve para calcular o deslocamento.",
    )
    notes = forms.CharField(
        label="Observações (opcional)",
        required=False,
        max_length=300,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 300}),
    )

    # Campos que bastam para responder "livre" ou "a consultar".
    AVAILABILITY_FIELDS = ("day", "start_time", "duration")

    def clean_day(self):
        day = self.cleaned_data["day"]
        today = timezone.localdate()
        if day < today:
            raise forms.ValidationError("Escolha uma data a partir de hoje.")
        if day > today + timedelta(days=MAX_DAYS_AHEAD):
            raise forms.ValidationError("Para datas tão distantes, fale direto pelo WhatsApp.")
        return day

    def clean(self):
        cleaned = super().clean()
        day, start_time = cleaned.get("day"), cleaned.get("start_time")
        if day and start_time:
            start, _ = services.event_period(day, start_time, 60)
            if start < timezone.now():
                self.add_error("start_time", "Esse horário já passou.")
        return cleaned

    def has_availability_fields(self):
        """True quando data, horário e duração foram preenchidos (mesmo com erro)."""
        return all(self.data.get(name) for name in self.AVAILABILITY_FIELDS)
