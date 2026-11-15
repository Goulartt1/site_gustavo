import json

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


# SEO: meta tags, prévias de compartilhamento, robots.txt e sitemap


@pytest.mark.django_db
def test_home_has_title_description_canonical_and_open_graph(client, profile):
    profile.headline = "Frase de apresentação de teste."
    profile.save()

    html = client.get(reverse("core:home"), {"utm_source": "teste"}).content.decode()

    assert f"<title>{profile.name}</title>" in html
    assert '<meta name="description" content="Frase de apresentação de teste.">' in html
    # Canônico e og:url sem os parâmetros (?utm_source=...).
    assert '<link rel="canonical" href="http://testserver/">' in html
    assert '<meta property="og:url" content="http://testserver/">' in html
    assert 'property="og:image" content="http://testserver/static/img/og-default.png"' in html
    assert 'rel="icon" href="/static/img/favicon.svg"' in html


@pytest.mark.django_db
def test_each_page_has_its_own_title_and_description(client):
    pages = {
        "repertoire:index": "Repertório · ",
        "testimonials:index": "Depoimentos · ",
        "quotes:index": "Pedir orçamento · ",
    }
    for name, title_start in pages.items():
        html = client.get(reverse(name)).content.decode()
        assert f"<title>{title_start}" in html, name
        assert f'<link rel="canonical" href="http://testserver{reverse(name)}">' in html
        assert html.count("<title>") == 1


@pytest.mark.django_db
def test_home_has_structured_data_with_social_profiles(client, profile):
    profile.instagram_url = "https://www.instagram.com/exemplo/"
    profile.city = "Florianópolis · SC"
    profile.save()

    html = client.get(reverse("core:home")).content.decode()
    raw = html.split('<script type="application/ld+json">')[1].split("</script>")[0]
    data = json.loads(raw)

    assert data["@type"] == "MusicGroup"
    assert data["name"] == profile.name
    assert data["sameAs"] == ["https://www.instagram.com/exemplo/"]
    assert data["location"]["name"] == "Florianópolis · SC"
    assert "Forró" in data["genre"]


@pytest.mark.django_db
def test_structured_data_cannot_close_the_script_tag(client, profile):
    profile.headline = "</script><script>alert(1)</script>"
    profile.save()

    html = client.get(reverse("core:home")).content.decode()
    block = html.split('<script type="application/ld+json">')[1].split("</script>")[0]

    assert r"\u003C/script\u003E" in block
    assert json.loads(block)["description"] == profile.headline  # o JSON continua válido


@pytest.mark.django_db
def test_robots_txt_blocks_admin_and_points_to_sitemap(client):
    response = client.get("/robots.txt")
    text = response.content.decode()

    assert response["Content-Type"].startswith("text/plain")
    assert "Disallow: /admin/" in text
    assert "Sitemap: http://testserver/sitemap.xml" in text


@pytest.mark.django_db
def test_sitemap_lists_public_pages(client):
    xml = client.get("/sitemap.xml").content.decode()

    for path in ["/", "/orcamento/", "/repertorio/", "/depoimentos/"]:
        assert f"<loc>http://testserver{path}</loc>" in xml
    assert "/admin/" not in xml


def test_footer_links_social_profiles_with_rel_me(client, profile):
    profile.instagram_url = "https://www.instagram.com/exemplo/"
    profile.whatsapp = "5548999990000"
    profile.save()

    html = client.get(reverse("core:home")).content.decode()

    assert 'href="https://www.instagram.com/exemplo/" target="_blank" rel="me noopener"' in html
    assert 'aria-label="WhatsApp"' in html
