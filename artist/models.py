from django.core.validators import RegexValidator
from django.db import models

whatsapp_validator = RegexValidator(
    regex=r"^\d{12,13}$",
    message="Use só números, com DDI e DDD. Ex.: 5551999998888",
)


class ArtistProfile(models.Model):
    """Dados do artista exibidos no site. Existe um único registro (pk=1)."""

    SINGLETON_PK = 1

    name = models.CharField("nome artístico", max_length=80)
    tagline = models.CharField(
        "estilos musicais",
        max_length=120,
        blank=True,
        help_text="Linha curta acima do nome. Ex.: Música gaúcha · Forró · Bailes e eventos",
    )
    headline = models.CharField(
        "frase de apresentação",
        max_length=200,
        blank=True,
        help_text="Uma ou duas frases logo abaixo do nome.",
    )
    bio = models.TextField("biografia", blank=True)
    photo = models.ImageField("foto principal", upload_to="artist/", blank=True)
    whatsapp = models.CharField(
        "WhatsApp",
        max_length=13,
        blank=True,
        validators=[whatsapp_validator],
        help_text="Só números, com DDI 55 e DDD. Ex.: 5551999998888",
    )
    city = models.CharField("cidade", max_length=80, blank=True, help_text="Ex.: Porto Alegre · RS")
    instagram_url = models.URLField("Instagram", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    spotify_url = models.URLField("Spotify", blank=True)
    min_gap_minutes = models.PositiveSmallIntegerField(
        "intervalo mínimo entre shows (minutos)",
        default=120,
        help_text=(
            "Tempo para desmontar, se deslocar e montar de novo. Um horário só é "
            "considerado livre se houver essa folga antes e depois dos compromissos."
        ),
    )

    class Meta:
        verbose_name = "perfil do artista"
        verbose_name_plural = "perfil do artista"

    def __str__(self):
        return self.name or "Perfil do artista"

    def save(self, *args, **kwargs):
        # Garante o registro único: qualquer save grava sempre no mesmo id.
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Devolve o perfil, criando um em branco na primeira vez."""
        profile, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return profile
