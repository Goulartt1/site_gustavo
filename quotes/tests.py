from datetime import date, datetime, time, timedelta
from urllib.parse import unquote

import pytest
from django.urls import reverse
from django.utils import timezone

from agenda.models import BusySlot
from artist.models import ArtistProfile

from . import services
from .forms import QuoteForm

URL = reverse("quotes:index")
HTMX = {"HTTP_HX_REQUEST": "true"}


@pytest.fixture
def profile(db):
    profile = ArtistProfile.load()
    profile.name = "Gustavo Locks"
    profile.whatsapp = "5548999990000"
    profile.min_gap_minutes = 120
    profile.save()
    return profile


@pytest.fixture
def next_month():
    return timezone.localdate() + timedelta(days=30)


def aware(day, hour, minute=0):
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


def data(day, **extra):
    base = {
        "event_type": "Casamento",
        "day": day.isoformat(),
        "start_time": "20:00",
        "duration": "240",
        "place": "Palhoça, bairro Pagani",
        "notes": "",
    }
    base.update(extra)
    return base


# Regras (services)


def test_format_duration():
    assert services.format_duration(60) == "1h"
    assert services.format_duration(90) == "1h30"
    assert services.format_duration(480) == "8h"


def test_event_period_can_cross_midnight():
    start, end = services.event_period(date(2027, 3, 20), time(22, 0), 240)

    assert timezone.localtime(end).date() == date(2027, 3, 21)
    assert timezone.localtime(end).hour == 2
    assert end - start == timedelta(hours=4)


def test_message_has_all_details():
    start, end = services.event_period(date(2027, 3, 20), time(20, 0), 240)

    message = services.build_message(
        "Gustavo", "Casamento", start, end, 240, "Palhoça", notes="Festa ao ar livre"
    )

    assert message.splitlines() == [
        "Olá, Gustavo! Vim pelo site e gostaria de um orçamento.",
        "Evento: Casamento",
        "Data: Sábado, 20/03/2027, das 20:00 às 00:00 (4h)",
        "Local: Palhoça",
        "Observações: Festa ao ar livre",
    ]


def test_free_when_agenda_is_empty(profile, next_month):
    assert services.check_availability(next_month, time(20, 0), 240) == services.FREE


def test_to_confirm_when_agenda_has_conflict(profile, next_month):
    BusySlot.objects.create(start=aware(next_month, 14), end=aware(next_month, 17))

    # Termina às 17h; com 2h de intervalo, um evento às 18h fica "a consultar".
    assert services.check_availability(next_month, time(18, 0), 120) == services.TO_CONFIRM
    assert services.check_availability(next_month, time(19, 0), 120) == services.FREE


def test_check_quote_builds_whatsapp_link_with_first_name(profile, next_month):
    result = services.check_quote(
        profile,
        day=next_month,
        start_time=time(20, 0),
        duration_minutes=240,
        event_type="Aniversário",
        place="Florianópolis",
    )

    assert result.is_free
    assert result.whatsapp_link.startswith("https://wa.me/5548999990000?text=")
    assert "Olá, Gustavo!" in unquote(result.whatsapp_link)
    assert "Evento: Aniversário" in unquote(result.whatsapp_link)


# Formulário


@pytest.mark.django_db
def test_form_refuses_past_dates():
    form = QuoteForm(data(timezone.localdate() - timedelta(days=1)))

    assert not form.is_valid()
    assert "a partir de hoje" in str(form.errors["day"])


@pytest.mark.django_db
def test_form_refuses_time_that_already_passed_today():
    now = timezone.localtime()
    if now.hour == 0:
        pytest.skip("Logo depois da meia-noite não há horário anterior no mesmo dia.")
    form = QuoteForm(data(now.date(), start_time="00:00"))

    assert not form.is_valid()
    assert "já passou" in str(form.errors["start_time"])


@pytest.mark.django_db
def test_form_refuses_dates_too_far_ahead():
    form = QuoteForm(data(timezone.localdate() + timedelta(days=800)))

    assert not form.is_valid()


@pytest.mark.django_db
def test_form_only_accepts_listed_event_types(next_month):
    assert not QuoteForm(data(next_month, event_type="Invasão")).is_valid()


# Página sem JavaScript (envio normal)


@pytest.mark.django_db
def test_page_renders_with_htmx_and_hint(client):
    html = client.get(URL).content.decode()

    assert "js/htmx" in html
    assert "Escolha a data, o horário e a duração" in html
    assert 'name="event_type"' in html


def test_full_post_shows_free_result_and_whatsapp_button(client, profile, next_month):
    response = client.post(URL, data(next_month))
    html = response.content.decode()

    assert response.status_code == 200
    assert "quotes/index.html" in [t.name for t in response.templates]
    assert "esse horário está livre" in html
    assert "https://wa.me/5548999990000?text=" in html


def test_full_post_with_conflict_says_to_confirm_never_busy(client, profile, next_month):
    BusySlot.objects.create(start=aware(next_month, 19), end=aware(next_month, 23))

    html = client.post(URL, data(next_month)).content.decode()

    assert "Esse horário está concorrido" in html
    assert "ocupado" not in html.lower()
    assert "https://wa.me/" in html  # o contato continua possível


def test_full_post_with_errors_shows_them_in_the_form(client, profile, next_month):
    html = client.post(URL, data(next_month, place="")).content.decode()

    assert "Este campo é obrigatório" in html
    assert "esse horário está livre" in html  # a disponibilidade já aparece


def test_without_whatsapp_number_shows_message_without_button(client, profile, next_month):
    profile.whatsapp = ""
    profile.save()

    html = client.post(URL, data(next_month)).content.decode()

    assert "ainda não foi cadastrado" in html
    assert "wa.me" not in html


def test_nothing_is_saved(client, profile, next_month, django_assert_max_num_queries):
    # Só leituras (perfil e agenda). Nenhum INSERT no banco.
    with django_assert_max_num_queries(5) as captured:
        client.post(URL, data(next_month))

    assert not any("INSERT" in q["sql"].upper() for q in captured.captured_queries)


# HTMX


def test_live_request_returns_only_the_result_box(client, profile, next_month):
    response = client.post(URL, {**data(next_month), "live": "1"}, **HTMX)

    assert [t.name for t in response.templates][0] == "quotes/_result.html"
    assert "esse horário está livre" in response.content.decode()


def test_live_request_with_only_date_time_and_duration_shows_availability(
    client, profile, next_month
):
    partial = {"day": next_month.isoformat(), "start_time": "20:00", "duration": "120", "live": "1"}

    html = client.post(URL, partial, **HTMX).content.decode()

    assert "esse horário está livre" in html
    assert "Complete os outros campos" in html
    assert "Este campo é obrigatório" not in html  # não cobra o que ainda não foi preenchido


def test_live_request_with_past_date_shows_the_error(client, profile):
    yesterday = timezone.localdate() - timedelta(days=1)
    partial = {"day": yesterday.isoformat(), "start_time": "20:00", "duration": "120", "live": "1"}

    html = client.post(URL, partial, **HTMX).content.decode()

    assert "a partir de hoje" in html


def test_live_request_before_choosing_date_shows_hint(client, profile):
    html = client.post(URL, {"event_type": "Casamento", "live": "1"}, **HTMX).content.decode()

    assert "Escolha a data, o horário e a duração" in html


def test_htmx_submit_returns_form_and_result_block(client, profile, next_month):
    response = client.post(URL, data(next_month, place=""), **HTMX)
    names = [t.name for t in response.templates]

    assert names[0] == "quotes/_block.html"
    assert "Este campo é obrigatório" in response.content.decode()


# Botões de orçamento


@pytest.mark.django_db
def test_quote_buttons_lead_to_the_form(client):
    html = client.get(reverse("core:home")).content.decode()

    assert html.count(f'href="{URL}"') >= 3  # cabeçalho, abertura e chamada final
