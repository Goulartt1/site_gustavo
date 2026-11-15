from django.db import models


class Style(models.Model):
    """Estilo musical (gaúchas, forró...). O artista edita pelo Admin."""

    name = models.CharField("nome", max_length=60, unique=True)
    order = models.PositiveSmallIntegerField(
        "ordem", default=0, help_text="Menor número aparece primeiro no site."
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "estilo"
        verbose_name_plural = "estilos"

    def __str__(self):
        return self.name


class Song(models.Model):
    """Música do repertório."""

    title = models.CharField("título", max_length=150)
    original_artist = models.CharField("artista original", max_length=150, blank=True)
    # PROTECT: não deixa apagar um estilo que ainda tem músicas.
    style = models.ForeignKey(
        Style, on_delete=models.PROTECT, related_name="songs", verbose_name="estilo"
    )
    is_active = models.BooleanField(
        "aparece no site", default=True, help_text="Desmarque para esconder sem apagar."
    )
    created_at = models.DateTimeField("criada em", auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "música"
        verbose_name_plural = "músicas"

    def __str__(self):
        if self.original_artist:
            return f"{self.title} ({self.original_artist})"
        return self.title


class SongSuggestion(models.Model):
    """Música sugerida por um visitante. Fica pendente até o artista decidir."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACCEPTED = "accepted", "Aceita"
        REJECTED = "rejected", "Recusada"

    title = models.CharField("música", max_length=150)
    artist = models.CharField("artista", max_length=150, blank=True)
    suggested_by = models.CharField("sugerida por", max_length=80, blank=True)
    status = models.CharField(
        "situação", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField("enviada em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "sugestão de música"
        verbose_name_plural = "sugestões de músicas"

    def __str__(self):
        return f"{self.title} — {self.artist}" if self.artist else self.title
