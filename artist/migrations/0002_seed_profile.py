"""Cria o perfil com dados de exemplo, para o site já abrir com conteúdo.

O artista substitui tudo pelo Admin. Se o perfil já existir, nada muda.
"""

from django.db import migrations

EXAMPLE = {
    "name": "Gustavo Locks",
    "tagline": "Música gaúcha · Forró · Bailes e eventos",
    "headline": (
        "Do galpão ao salão: vanerão, chamamé, xote e baião tocados ao vivo, "
        "do primeiro acorde até o último arrasta-pé."
    ),
}


def create_example_profile(apps, schema_editor):
    # Nas migrações, usa-se o modelo "histórico" (apps.get_model), não o import
    # direto: assim a migração continua funcionando mesmo se o modelo mudar.
    ArtistProfile = apps.get_model("artist", "ArtistProfile")
    ArtistProfile.objects.get_or_create(pk=1, defaults=EXAMPLE)


class Migration(migrations.Migration):
    dependencies = [
        ("artist", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_example_profile, migrations.RunPython.noop),
    ]
