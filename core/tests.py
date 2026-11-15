import pytest
from django.core.cache import cache
from django.urls import reverse

from artist.models import ArtistProfile
from core.antispam import RateLimit
from core.client_ip import get_client_ip


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


# IP do visitante (core.client_ip.get_client_ip)


def test_client_ip_ignores_forwarded_header_without_origin_secret(rf, settings):
    settings.ORIGIN_SECRET = ""
    request = rf.get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_CLIENT_IP="1.2.3.4")

    assert get_client_ip(request) == "10.0.0.1"


def test_client_ip_uses_worker_header_with_origin_secret(rf, settings):
    settings.ORIGIN_SECRET = "segredo-de-teste"
    request = rf.get("/", REMOTE_ADDR="10.0.0.1", HTTP_X_CLIENT_IP="1.2.3.4")

    assert get_client_ip(request) == "1.2.3.4"


# Anti-spam comum (core.antispam)


@pytest.fixture
def empty_cache():
    cache.clear()
    yield
    cache.clear()


def test_rate_limit_counts_per_scope_and_ip(empty_cache):
    limit = RateLimit("teste", limit=2, window=60)

    limit.hit("1.1.1.1")
    assert not limit.reached("1.1.1.1")
    limit.hit("1.1.1.1")

    assert limit.reached("1.1.1.1")
    assert not limit.reached("2.2.2.2")
    assert not RateLimit("outro", limit=2, window=60).reached("1.1.1.1")
