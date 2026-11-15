from datetime import date, datetime, timedelta

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from artist.models import ArtistProfile

from . import services
from .forms import BusySlotAdminForm
from .models import BusySlot

NO_GAP = timedelta(0)
TWO_HOURS = timedelta(hours=2)


def at(day, hour, minute=0):
    """Data e hora no fuso do site (America/Sao_Paulo)."""
    return timezone.make_aware(datetime(2027, 1, day, hour, minute))


@pytest.fixture
def show(db):
    # Show das 20h às 23h do dia 10.
    return BusySlot.objects.create(start=at(10, 20), end=at(10, 23))


# Regra: horário livre (is_available)


def test_free_when_agenda_is_empty(db):
    assert services.is_available(at(10, 20), at(10, 23), gap=NO_GAP)


def test_overlapping_time_is_not_free(show):
    assert not services.is_available(at(10, 22), at(11, 1), gap=NO_GAP)


def test_touching_the_edge_is_free_without_gap(show):
    assert services.is_available(at(10, 23), at(11, 2), gap=NO_GAP)
    assert services.is_available(at(10, 17), at(10, 20), gap=NO_GAP)


def test_gap_blocks_events_too_close(show):
    # Termina às 23h; com 2h de folga, só fica livre a partir de 01h.
    assert not services.is_available(at(11, 0, 30), at(11, 3), gap=TWO_HOURS)
    assert services.is_available(at(11, 1), at(11, 4), gap=TWO_HOURS)
    # Antes: começa às 20h, então um evento precisa acabar até 18h.
    assert not services.is_available(at(10, 16), at(10, 19), gap=TWO_HOURS)
    assert services.is_available(at(10, 15), at(10, 18), gap=TWO_HOURS)


def test_show_crossing_midnight_blocks_the_next_day(db):
    BusySlot.objects.create(start=at(10, 22), end=at(11, 2))

    assert not services.is_available(at(11, 1), at(11, 3), gap=NO_GAP)
    assert services.is_available(at(11, 2), at(11, 5), gap=NO_GAP)


def test_more_than_one_show_on_the_same_day(db):
    BusySlot.objects.create(start=at(10, 12), end=at(10, 15))
    BusySlot.objects.create(start=at(10, 21), end=at(10, 23))

    assert services.is_available(at(10, 16), at(10, 19), gap=timedelta(hours=1))
    assert not services.is_available(at(10, 16), at(10, 20, 30), gap=timedelta(hours=1))


def test_gap_comes_from_artist_profile_by_default(show):
    profile = ArtistProfile.load()
    profile.min_gap_minutes = 60
    profile.save()

    assert not services.is_available(at(10, 23, 30), at(11, 2))
    assert services.is_available(at(11, 0), at(11, 2))


def test_end_before_start_is_an_error(db):
    with pytest.raises(ValueError):
        services.is_available(at(10, 23), at(10, 20))


def test_conflicts_can_exclude_the_slot_itself(show):
    assert not services.conflicting_slots(show.start, show.end, gap=NO_GAP, exclude_pk=show.pk)


# Dias inteiros


def test_whole_days_go_from_midnight_to_midnight_after_last_day():
    start, end = services.whole_days(date(2027, 1, 10), date(2027, 1, 12))

    assert start == at(10, 0)
    assert end == at(13, 0)


def test_whole_days_reject_inverted_period():
    with pytest.raises(ValueError):
        services.whole_days(date(2027, 1, 12), date(2027, 1, 10))


def test_is_whole_days(db):
    vacation = BusySlot(start=at(10, 0), end=at(13, 0))
    show = BusySlot(start=at(10, 20), end=at(10, 23))

    assert services.is_whole_days(vacation)
    assert not services.is_whole_days(show)


# Banco e modelo


def test_database_refuses_end_before_start(db):
    with pytest.raises(IntegrityError):
        BusySlot.objects.create(start=at(10, 23), end=at(10, 20))


def test_str_shows_local_times(show):
    assert str(show) == "10/01/2027 das 20:00 às 23:00"


# Formulário do Admin


def form_data(**fields):
    data = {
        "start_0": "",
        "start_1": "",
        "end_0": "",
        "end_1": "",
        "first_day": "",
        "last_day": "",
        "internal_note": "",
    }
    data.update(fields)
    return data


@pytest.mark.django_db
def test_form_with_start_and_end():
    form = BusySlotAdminForm(
        form_data(start_0="10/01/2027", start_1="20:00", end_0="11/01/2027", end_1="02:00")
    )

    assert form.is_valid(), form.errors
    slot = form.save()
    assert (slot.start, slot.end) == (at(10, 20), at(11, 2))


@pytest.mark.django_db
def test_form_with_whole_days():
    form = BusySlotAdminForm(form_data(first_day="10/01/2027", last_day="12/01/2027"))

    assert form.is_valid(), form.errors
    slot = form.save()
    assert (slot.start, slot.end) == (at(10, 0), at(13, 0))


@pytest.mark.django_db
def test_form_single_whole_day_without_last_day():
    form = BusySlotAdminForm(form_data(first_day="10/01/2027"))

    assert form.is_valid(), form.errors
    assert (form.instance.start, form.instance.end) == (at(10, 0), at(11, 0))


@pytest.mark.django_db
def test_form_refuses_both_modes_at_once():
    form = BusySlotAdminForm(
        form_data(
            start_0="10/01/2027",
            start_1="20:00",
            end_0="10/01/2027",
            end_1="23:00",
            first_day="10/01/2027",
        )
    )

    assert not form.is_valid()
    assert "só um dos dois" in str(form.errors)


@pytest.mark.django_db
def test_form_requires_some_period():
    form = BusySlotAdminForm(form_data(internal_note="Sem data"))

    assert not form.is_valid()
    assert "start" in form.errors and "end" in form.errors


@pytest.mark.django_db
def test_form_refuses_end_before_start():
    form = BusySlotAdminForm(
        form_data(start_0="10/01/2027", start_1="23:00", end_0="10/01/2027", end_1="20:00")
    )

    assert not form.is_valid()
    assert "depois do início" in str(form.errors)


@pytest.mark.django_db
def test_editing_whole_days_shows_days_instead_of_times():
    vacation = BusySlot.objects.create(start=at(10, 0), end=at(13, 0))

    form = BusySlotAdminForm(instance=vacation)

    assert form.initial["first_day"] == date(2027, 1, 10)
    assert form.initial["last_day"] == date(2027, 1, 12)


# Admin


@pytest.mark.django_db
def test_admin_warns_about_conflict_but_saves(admin_client, show):
    response = admin_client.post(
        reverse("admin:agenda_busyslot_add"),
        form_data(start_0="11/01/2027", start_1="00:00", end_0="11/01/2027", end_1="02:00"),
        follow=True,
    )

    assert BusySlot.objects.count() == 2
    assert "Atenção: este horário fica a menos de 120 minutos" in response.content.decode()


@pytest.mark.django_db
def test_admin_lists_upcoming_before_past(admin_client):
    now = timezone.now()
    BusySlot.objects.create(
        start=now - timedelta(days=3),
        end=now - timedelta(days=3, hours=-2),
        internal_note="passado",
    )
    BusySlot.objects.create(
        start=now + timedelta(days=5), end=now + timedelta(days=5, hours=2), internal_note="depois"
    )
    BusySlot.objects.create(
        start=now + timedelta(days=1), end=now + timedelta(days=1, hours=2), internal_note="logo"
    )

    response = admin_client.get(reverse("admin:agenda_busyslot_changelist"))
    notes = [slot.internal_note for slot in response.context["cl"].result_list]

    assert notes == ["logo", "depois", "passado"]


@pytest.mark.django_db
def test_admin_add_page_offers_both_modes(admin_client):
    html = admin_client.get(reverse("admin:agenda_busyslot_add")).content.decode()

    assert "Horário" in html
    assert "Ou bloqueie dias inteiros" in html
    assert 'name="first_day"' in html


@pytest.mark.django_db
def test_artist_profile_admin_shows_gap_field(admin_client):
    profile = ArtistProfile.load()
    url = reverse("admin:artist_artistprofile_change", args=[profile.pk])

    assert 'name="min_gap_minutes"' in admin_client.get(url).content.decode()
