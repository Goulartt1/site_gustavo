import pytest
from django.core.cache import cache
from django.urls import reverse

from . import services
from .models import Testimonial

URL = reverse("testimonials:index")
APPROVED = Testimonial.Status.APPROVED


@pytest.fixture(autouse=True)
def clear_cache():
    # O limite de envios é guardado no cache; cada teste começa do zero.
    cache.clear()
    yield
    cache.clear()


def valid_data(**extra):
    return {"name": "Ana", "text": "Animou o casamento do início ao fim!", "consent": "on", **extra}


# Regras de negócio


@pytest.mark.django_db
def test_only_approved_testimonials_are_public_newest_first():
    Testimonial.objects.create(name="Pendente", text="...")
    Testimonial.objects.create(name="Recusado", text="...", status=Testimonial.Status.REJECTED)
    Testimonial.objects.create(name="Antigo", text="...", status=APPROVED)
    Testimonial.objects.create(name="Novo", text="...", status=APPROVED)

    names = [t.name for t in services.approved_testimonials()]

    assert names == ["Novo", "Antigo"]


@pytest.mark.django_db
def test_approved_testimonials_respects_limit():
    for i in range(5):
        Testimonial.objects.create(name=f"Pessoa {i}", text="...", status=APPROVED)

    assert len(services.approved_testimonials(limit=3)) == 3


@pytest.mark.django_db
def test_approve_and_reject_change_status():
    first = Testimonial.objects.create(name="A", text="...")
    second = Testimonial.objects.create(name="B", text="...")

    services.approve_testimonials(Testimonial.objects.filter(pk=first.pk))
    services.reject_testimonials(Testimonial.objects.filter(pk=second.pk))

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.status == APPROVED
    assert second.status == Testimonial.Status.REJECTED


# Página


@pytest.mark.django_db
def test_page_shows_only_approved_testimonials(client):
    Testimonial.objects.create(name="Ana", text="Texto aprovado", status=APPROVED)
    Testimonial.objects.create(name="Bia", text="Texto pendente")

    html = client.get(URL).content.decode()

    assert "Texto aprovado" in html
    assert "Texto pendente" not in html
    assert 'id="deixar"' in html


@pytest.mark.django_db
def test_page_has_friendly_message_without_testimonials(client):
    assert "Ainda não há depoimentos" in client.get(URL).content.decode()


@pytest.mark.django_db
def test_testimonial_text_is_escaped(client):
    Testimonial.objects.create(name="X", text="<script>alert(1)</script>", status=APPROVED)

    html = client.get(URL).content.decode()

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# Formulário


@pytest.mark.django_db
def test_valid_testimonial_is_saved_as_pending_and_not_shown(client):
    response = client.post(URL, valid_data(), follow=True)

    testimonial = Testimonial.objects.get()
    html = response.content.decode()
    assert testimonial.status == Testimonial.Status.PENDING
    assert response.redirect_chain == [(f"{URL}#deixar", 302)]
    assert "Obrigado pelo depoimento" in html
    assert "Animou o casamento" not in html


@pytest.mark.django_db
def test_consent_is_required(client):
    response = client.post(URL, valid_data(consent=""))

    assert Testimonial.objects.count() == 0
    assert "marque a autorização de publicação" in response.content.decode()


@pytest.mark.django_db
def test_name_and_text_are_required(client):
    client.post(URL, valid_data(name="", text=""))

    assert Testimonial.objects.count() == 0


@pytest.mark.django_db
def test_text_longer_than_limit_is_refused(client):
    client.post(URL, valid_data(text="a" * (Testimonial.TEXT_MAX_LENGTH + 1)))

    assert Testimonial.objects.count() == 0


@pytest.mark.django_db
def test_honeypot_filled_saves_nothing(client):
    response = client.post(URL, valid_data(website="http://spam.example"), follow=True)

    assert Testimonial.objects.count() == 0
    assert "Obrigado pelo depoimento" in response.content.decode()


@pytest.mark.django_db
def test_testimonials_are_limited_per_ip(client):
    for _ in range(services.testimonial_rate_limit.limit):
        client.post(URL, valid_data())

    response = client.post(URL, valid_data())

    assert response.status_code == 429
    assert Testimonial.objects.count() == services.testimonial_rate_limit.limit


# Página inicial e menu


@pytest.mark.django_db
def test_home_shows_latest_three_approved_testimonials(client):
    for i in range(4):
        Testimonial.objects.create(name=f"Pessoa {i}", text=f"Texto {i}", status=APPROVED)

    html = client.get(reverse("core:home")).content.decode()

    assert 'id="depoimentos"' in html
    assert "Texto 3" in html
    assert "Texto 0" not in html


@pytest.mark.django_db
def test_home_hides_section_without_approved_testimonials(client):
    Testimonial.objects.create(name="Pendente", text="...")

    html = client.get(reverse("core:home")).content.decode()

    assert 'id="depoimentos"' not in html
    assert f'href="{URL}"' in html  # o link do menu continua


# Admin


@pytest.mark.django_db
def test_admin_approve_action(admin_client):
    testimonial = Testimonial.objects.create(name="Ana", text="...")

    admin_client.post(
        reverse("admin:testimonials_testimonial_changelist"),
        {"action": "approve", "_selected_action": [testimonial.pk]},
    )

    testimonial.refresh_from_db()
    assert testimonial.status == APPROVED


@pytest.mark.django_db
def test_admin_lists_pending_first(admin_client):
    Testimonial.objects.create(name="Pendente antigo", text="...")
    Testimonial.objects.create(name="Aprovado novo", text="...", status=APPROVED)

    response = admin_client.get(reverse("admin:testimonials_testimonial_changelist"))
    names = [t.name for t in response.context["cl"].result_list]

    assert names == ["Pendente antigo", "Aprovado novo"]
