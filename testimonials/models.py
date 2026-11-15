from django.db import models


class Testimonial(models.Model):
    """Depoimento enviado por um visitante. Só aparece no site depois de aprovado."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Recusado"

    TEXT_MAX_LENGTH = 600

    name = models.CharField("nome", max_length=80)
    text = models.TextField("depoimento", max_length=TEXT_MAX_LENGTH)
    status = models.CharField(
        "situação", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField("enviado em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "depoimento"
        verbose_name_plural = "depoimentos"

    def __str__(self):
        return f"{self.name}: {self.text[:40]}"
