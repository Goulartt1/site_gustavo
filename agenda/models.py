from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class BusySlot(models.Model):
    """Período em que o artista está ocupado (show, folga, férias...).

    Pode atravessar a meia-noite e durar vários dias. Os detalhes ficam na nota
    interna, que nunca é exibida ao público.
    """

    start = models.DateTimeField("início")
    end = models.DateTimeField("fim")
    internal_note = models.CharField(
        "nota interna",
        max_length=200,
        blank=True,
        help_text="Só você vê. Ex.: Casamento da Ana, salão em Palhoça.",
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        ordering = ["start"]
        verbose_name = "horário ocupado"
        verbose_name_plural = "horários ocupados"
        indexes = [models.Index(fields=["start", "end"])]
        # Garantia também no banco: mesmo fora do Admin, o fim vem depois do início.
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F("start")), name="busyslot_end_after_start"
            )
        ]

    def __str__(self):
        start = timezone.localtime(self.start)
        end = timezone.localtime(self.end)
        if start.date() == end.date():
            return f"{start:%d/%m/%Y} das {start:%H:%M} às {end:%H:%M}"
        return f"{start:%d/%m/%Y %H:%M} até {end:%d/%m/%Y %H:%M}"

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({"end": "O fim precisa ser depois do início."})
