from django import forms

from .models import SongSuggestion


class SongSuggestionForm(forms.ModelForm):
    """Formulário público "Sugira uma música"."""

    # Campo-isca: escondido de pessoas (CSS e leitores de tela), mas robôs
    # costumam preencher tudo. Se vier preenchido, a view descarta o envio.
    website = forms.CharField(
        required=False,
        label="Deixe este campo vazio",
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

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

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
