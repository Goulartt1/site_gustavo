from django import forms

from core.antispam import HoneypotForm

from .models import Testimonial


class TestimonialForm(HoneypotForm, forms.ModelForm):
    """Formulário público "Deixe o seu depoimento" (com campo-isca)."""

    # LGPD: o nome é publicado junto com o depoimento, então a autorização é
    # obrigatória (diferente da sugestão de música, em que o nome é opcional).
    consent = forms.BooleanField(
        required=True,
        label=(
            "Autorizo publicar meu nome e este depoimento no site, depois da "
            "aprovação do artista. Posso pedir a remoção quando quiser."
        ),
        error_messages={"required": "Para enviar, marque a autorização de publicação."},
    )

    class Meta:
        model = Testimonial
        fields = ["name", "text"]
        labels = {"name": "Seu nome", "text": "Seu depoimento"}
        help_texts = {
            "name": "Aparece no site junto com o depoimento.",
            "text": f"Até {Testimonial.TEXT_MAX_LENGTH} caracteres.",
        }
        widgets = {
            "text": forms.Textarea(attrs={"rows": 5, "maxlength": Testimonial.TEXT_MAX_LENGTH}),
        }
