from django import forms

from core.antispam import HoneypotForm

from .models import SongSuggestion


class SongSuggestionForm(HoneypotForm, forms.ModelForm):
    """Formulário público "Sugira uma música" (com campo-isca, ver core.antispam)."""

    consent = forms.BooleanField(
        required=False,
        label=(
            "Autorizo guardar meu nome junto com a sugestão. Ele é visto só pelo "
            "artista e não aparece no site."
        ),
    )

    class Meta:
        model = SongSuggestion
        fields = ["title", "artist", "suggested_by"]
        labels = {
            "title": "Música",
            "artist": "Artista ou banda",
            "suggested_by": "Seu nome (opcional)",
        }

    def clean(self):
        cleaned = super().clean()
        # LGPD: o nome só é guardado com consentimento.
        if cleaned.get("suggested_by") and not cleaned.get("consent"):
            self.add_error(
                "consent",
                "Para enviar com o seu nome, marque a autorização. Ou deixe o nome em branco.",
            )
        return cleaned
