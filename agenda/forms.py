from datetime import timedelta

from django import forms
from django.contrib.admin.widgets import AdminDateWidget, AdminSplitDateTime
from django.utils import timezone

from . import services
from .models import BusySlot


class BusySlotAdminForm(forms.ModelForm):
    """Formulário do Admin com duas formas de cadastrar.

    - Horário: início e fim com data e hora (ex.: show das 20h às 02h).
    - Dias inteiros: só o primeiro e o último dia (ex.: férias).
    No segundo caso, o formulário calcula início e fim (services.whole_days).
    """

    first_day = forms.DateField(label="primeiro dia", required=False, widget=AdminDateWidget)
    last_day = forms.DateField(
        label="último dia",
        required=False,
        widget=AdminDateWidget,
        help_text="Para um dia só, repita a data ou deixe em branco.",
    )

    class Meta:
        model = BusySlot
        fields = ["start", "end", "first_day", "last_day", "internal_note"]
        # Data e hora em caixas separadas, como o Admin já faz por padrão.
        # Declarado aqui para o formulário se comportar igual também nos testes.
        field_classes = {"start": forms.SplitDateTimeField, "end": forms.SplitDateTimeField}
        widgets = {"start": AdminSplitDateTime, "end": AdminSplitDateTime}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Início e fim deixam de ser obrigatórios aqui: no modo "dias inteiros"
        # eles são calculados. O clean abaixo garante que um dos modos foi usado.
        self.fields["start"].required = False
        self.fields["end"].required = False

        # Ao editar um bloqueio de dias inteiros, mostra os dias, não os horários.
        slot = self.instance
        if slot.pk and services.is_whole_days(slot):
            self.initial["first_day"] = timezone.localtime(slot.start).date()
            self.initial["last_day"] = timezone.localtime(slot.end).date() - timedelta(days=1)
            self.initial["start"] = None
            self.initial["end"] = None

    def clean(self):
        cleaned = super().clean()
        first_day = cleaned.get("first_day")
        last_day = cleaned.get("last_day")
        start = cleaned.get("start")
        end = cleaned.get("end")

        if first_day or last_day:
            if start or end:
                raise forms.ValidationError(
                    "Preencha só um dos dois: o horário ou os dias inteiros."
                )
            if not first_day:
                self.add_error("first_day", "Informe o primeiro dia.")
                return cleaned
            last_day = last_day or first_day
            if last_day < first_day:
                self.add_error("last_day", "O último dia precisa ser igual ou depois do primeiro.")
                return cleaned
            cleaned["start"], cleaned["end"] = services.whole_days(first_day, last_day)
        else:
            if not start:
                self.add_error("start", "Informe o início (ou preencha os dias inteiros).")
            if not end:
                self.add_error("end", "Informe o fim (ou preencha os dias inteiros).")
        return cleaned
