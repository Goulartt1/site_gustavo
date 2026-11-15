import pytest
from django.core.cache import cache
from django.db.models import ProtectedError
from django.urls import reverse

from . import services
from .models import Song, SongSuggestion, Style

URL = reverse("repertoire:index")


@pytest.fixture(autouse=True)
def clear_cache():
    # O limite de envios é guardado no cache; cada teste começa do zero.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def forro(db):
    # A migração 0002 já cria os estilos do material de divulgação.
    return Style.objects.get(name="Forró")


def valid_data(**extra):
    return {"title": "Asa Branca", "artist": "Luiz Gonzaga", **extra}


# Estilos e músicas


@pytest.mark.django_db
def test_styles_from_press_kit_are_created_in_order():
    names = list(Style.objects.values_list("name", flat=True))

    assert names == ["Gaúchas", "Sertanejo universitário", "Forró", "Pagode", "Modão", "Reggae"]


def test_style_with_songs_cannot_be_deleted(forro):
    Song.objects.create(title="Asa Branca", style=forro)

    with pytest.raises(ProtectedError):
        forro.delete()


# Repertório público (regra de negócio)


def test_public_repertoire_shows_only_active_songs_and_hides_empty_styles(forro):
    Song.objects.create(title="Asa Branca", style=forro)
    Song.objects.create(title="Escondida", style=forro, is_active=False)

    styles = services.public_repertoire()

    assert [style.name for style in styles] == ["Forró"]
    assert [song.title for song in styles[0].active_songs] == ["Asa Branca"]


def test_public_repertoire_uses_two_queries(forro, django_assert_num_queries):
    gauchas = Style.objects.get(name="Gaúchas")
    Song.objects.create(title="Asa Branca", style=forro)
    Song.objects.create(title="Querência Amada", style=gauchas)

    with django_assert_num_queries(2):
        styles = services.public_repertoire()
        [song.title for style in styles for song in style.active_songs]


# Aceitar e recusar sugestões


@pytest.mark.django_db
def test_accept_and_reject_change_status_without_creating_songs():
    first = SongSuggestion.objects.create(title="Música 1")
    second = SongSuggestion.objects.create(title="Música 2")

    assert services.accept_suggestions(SongSuggestion.objects.filter(pk=first.pk)) == 1
    assert services.reject_suggestions(SongSuggestion.objects.filter(pk=second.pk)) == 1

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.status == SongSuggestion.Status.ACCEPTED
    assert second.status == SongSuggestion.Status.REJECTED
    assert Song.objects.count() == 0


# Página


def test_page_lists_songs_by_style_and_shows_form(client, forro):
    Song.objects.create(title="Asa Branca", original_artist="Luiz Gonzaga", style=forro)

    response = client.get(URL)
    html = response.content.decode()

    assert response.status_code == 200
    assert "Forró" in html
    assert "Asa Branca" in html
    assert 'id="sugerir"' in html
    assert "csrfmiddlewaretoken" in html


@pytest.mark.django_db
def test_page_has_friendly_message_when_repertoire_is_empty(client):
    assert "está sendo preparado" in client.get(URL).content.decode()


@pytest.mark.django_db
def test_header_links_to_repertoire(client):
    html = client.get(reverse("core:home")).content.decode()

    assert f'href="{URL}"' in html


# Formulário de sugestão


@pytest.mark.django_db
def test_valid_suggestion_is_saved_as_pending_and_redirects(client):
    response = client.post(URL, valid_data(), follow=True)

    suggestion = SongSuggestion.objects.get()
    assert suggestion.title == "Asa Branca"
    assert suggestion.status == SongSuggestion.Status.PENDING
    assert response.redirect_chain == [(f"{URL}#sugerir", 302)]
    assert "Obrigado pela sugestão" in response.content.decode()


@pytest.mark.django_db
def test_title_is_required(client):
    response = client.post(URL, {"title": "", "artist": "Alguém"})

    assert response.status_code == 200
    assert SongSuggestion.objects.count() == 0
    assert "Este campo é obrigatório" in response.content.decode()


@pytest.mark.django_db
def test_name_requires_consent(client):
    response = client.post(URL, valid_data(suggested_by="Maria"))

    assert SongSuggestion.objects.count() == 0
    assert "marque a autorização" in response.content.decode()


@pytest.mark.django_db
def test_name_with_consent_is_saved(client):
    client.post(URL, valid_data(suggested_by="Maria", consent="on"))

    assert SongSuggestion.objects.get().suggested_by == "Maria"


@pytest.mark.django_db
def test_honeypot_filled_looks_successful_but_saves_nothing(client):
    response = client.post(URL, valid_data(website="http://spam.example"), follow=True)

    assert SongSuggestion.objects.count() == 0
    assert "Obrigado pela sugestão" in response.content.decode()


@pytest.mark.django_db
def test_suggestions_are_limited_per_ip(client):
    for _ in range(services.suggestion_rate_limit.limit):
        client.post(URL, valid_data())

    response = client.post(URL, valid_data())

    assert response.status_code == 429
    assert SongSuggestion.objects.count() == services.suggestion_rate_limit.limit
    assert "Tente de novo mais tarde" in response.content.decode()


@pytest.mark.django_db
def test_limit_counts_each_ip_separately(client):
    for _ in range(services.suggestion_rate_limit.limit):
        client.post(URL, valid_data(), REMOTE_ADDR="10.0.0.1")

    response = client.post(URL, valid_data(), REMOTE_ADDR="10.0.0.2")

    assert response.status_code == 302
    assert SongSuggestion.objects.count() == services.suggestion_rate_limit.limit + 1


# Admin


@pytest.mark.django_db
def test_admin_accept_action(admin_client):
    suggestion = SongSuggestion.objects.create(title="Música")

    admin_client.post(
        reverse("admin:repertoire_songsuggestion_changelist"),
        {"action": "accept", "_selected_action": [suggestion.pk]},
    )

    suggestion.refresh_from_db()
    assert suggestion.status == SongSuggestion.Status.ACCEPTED


@pytest.mark.django_db
def test_admin_lists_pending_suggestions_first(admin_client):
    SongSuggestion.objects.create(title="Pendente antiga")
    SongSuggestion.objects.create(title="Aceita nova", status=SongSuggestion.Status.ACCEPTED)

    response = admin_client.get(reverse("admin:repertoire_songsuggestion_changelist"))
    titles = [s.title for s in response.context["cl"].result_list]

    assert titles == ["Pendente antiga", "Aceita nova"]
