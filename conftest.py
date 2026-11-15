"""Ajustes que valem para todos os testes (o pytest lê este arquivo sozinho)."""

import pytest


@pytest.fixture(autouse=True)
def _test_friendly_settings(settings):
    # Nos testes não roda o collectstatic, então não há o manifesto com os
    # nomes com hash: usa o armazenamento simples de estáticos.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    # O cliente de teste usa HTTP; sem isto, tudo viraria redirecionamento 301.
    settings.SECURE_SSL_REDIRECT = False
