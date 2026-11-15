import pytest
from django.urls import reverse

from artist.models import ArtistProfile


@pytest.fixture
def profile(db):
    # A migração 0002 já cria o perfil de exemplo; aqui ajustamos por teste.
    return ArtistProfile.load()


@pytest.mark.django_db
def test_home_renders_with_example_profile(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert "core/home.html" in [t.name for t in response.templates]
    assert "Gustavo" in response.content.decode()


def test_home_shows_whatsapp_buttons_when_number_is_set(client, profile):
    profile.whatsapp = "5551999998888"
    profile.save()

    html = client.get(reverse("core:home")).content.decode()

    assert "https://wa.me/5551999998888" in html
    assert 'aria-label="Falar no WhatsApp"' in html


def test_home_hides_whatsapp_buttons_without_number(client, profile):
    profile.whatsapp = ""
    profile.save()

    html = client.get(reverse("core:home")).content.decode()

    assert "wa.me" not in html


def test_about_section_only_appears_with_bio(client, profile):
    profile.bio = ""
    profile.save()
    assert 'id="sobre"' not in client.get(reverse("core:home")).content.decode()

    profile.bio = "Texto de teste da biografia."
    profile.save()
    html = client.get(reverse("core:home")).content.decode()
    assert 'id="sobre"' in html
    assert "Texto de teste da biografia." in html


# Porta de entrada só pelo Cloudflare (core.middleware.RequireOriginSecretMiddleware)


@pytest.mark.django_db
def test_direct_access_is_refused_when_origin_secret_is_set(client, settings):
    settings.ORIGIN_SECRET = "segredo-de-teste"

    response = client.get(reverse("core:home"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_access_through_worker_is_allowed(client, settings):
    settings.ORIGIN_SECRET = "segredo-de-teste"

    response = client.get(reverse("core:home"), headers={"X-Origin-Secret": "segredo-de-teste"})

    assert response.status_code == 200


@pytest.mark.django_db
def test_wrong_secret_is_refused(client, settings):
    settings.ORIGIN_SECRET = "segredo-de-teste"

    response = client.get(reverse("core:home"), headers={"X-Origin-Secret": "chute"})

    assert response.status_code == 403
