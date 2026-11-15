import pytest
from django.urls import reverse

from .models import ArtistProfile
from .whatsapp import whatsapp_url

# Link do WhatsApp (regra de negócio, sem banco)


def test_whatsapp_url_keeps_only_digits_and_encodes_message():
    url = whatsapp_url("+55 (51) 99999-8888", "Olá, tudo bem?")

    assert url == "https://wa.me/5551999998888?text=Ol%C3%A1%2C%20tudo%20bem%3F"


def test_whatsapp_url_is_empty_without_number():
    assert whatsapp_url("") == ""
    assert whatsapp_url(None) == ""


# Perfil único


@pytest.mark.django_db
def test_load_creates_profile_once():
    first = ArtistProfile.load()
    second = ArtistProfile.load()

    assert first.pk == second.pk == ArtistProfile.SINGLETON_PK
    assert ArtistProfile.objects.count() == 1


@pytest.mark.django_db
def test_saving_a_new_profile_overwrites_the_single_record():
    ArtistProfile(name="Primeiro").save()
    ArtistProfile(name="Segundo").save()

    assert ArtistProfile.objects.count() == 1
    assert ArtistProfile.load().name == "Segundo"


# Admin


@pytest.mark.django_db
def test_admin_list_redirects_to_the_profile_form(admin_client):
    response = admin_client.get(reverse("admin:artist_artistprofile_changelist"))

    assert response.status_code == 302
    assert response.url == reverse("admin:artist_artistprofile_change", args=[1])


@pytest.mark.django_db
def test_admin_cannot_add_another_profile(admin_client):
    response = admin_client.get(reverse("admin:artist_artistprofile_add"))

    assert response.status_code == 403
