"""Cria os estilos do material de divulgação do artista.

O artista pode renomear, reordenar ou criar outros pelo Admin. As músicas não
vêm prontas: só o artista sabe o que toca de verdade.
"""

from django.db import migrations

STYLES = [
    "Gaúchas",
    "Sertanejo universitário",
    "Forró",
    "Pagode",
    "Modão",
    "Reggae",
]


def create_styles(apps, schema_editor):
    Style = apps.get_model("repertoire", "Style")
    for order, name in enumerate(STYLES, start=1):
        Style.objects.get_or_create(name=name, defaults={"order": order})


class Migration(migrations.Migration):
    dependencies = [
        ("repertoire", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_styles, migrations.RunPython.noop),
    ]
