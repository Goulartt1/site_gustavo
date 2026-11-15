"""Regras de negócio da agenda.

A principal é is_available: diz se um horário está livre, respeitando o
intervalo mínimo entre shows. O pedido de orçamento (etapa 10) vai usá-la para
responder "livre" ou "a consultar" (nunca "ocupado"; ver decisão 19).
"""

from datetime import datetime, time, timedelta

from django.utils import timezone

from artist.models import ArtistProfile

from .models import BusySlot


def min_gap():
    """Intervalo mínimo entre shows, definido pelo artista no Admin."""
    return timedelta(minutes=ArtistProfile.load().min_gap_minutes)


def conflicting_slots(start, end, gap=None, exclude_pk=None):
    """Compromissos que impedem um evento de start a end.

    Um compromisso atrapalha se, somada a folga (gap) antes e depois, ele se
    sobrepõe ao evento. Encostar exatamente na borda não conta como conflito:
    um show que termina às 22h não impede outro que começa às 22h com gap zero.
    """
    if end <= start:
        raise ValueError("O fim precisa ser depois do início.")
    if gap is None:
        gap = min_gap()
    slots = BusySlot.objects.filter(start__lt=end + gap, end__gt=start - gap)
    if exclude_pk is not None:
        slots = slots.exclude(pk=exclude_pk)
    return slots


def is_available(start, end, gap=None):
    """True se não há compromisso (com a folga) entre start e end."""
    return not conflicting_slots(start, end, gap=gap).exists()


def whole_days(first_day, last_day):
    """Converte um período de dias inteiros em início e fim com horário.

    Do primeiro dia às 00:00 até o dia seguinte ao último, às 00:00, no fuso
    do site (America/Sao_Paulo). Ex.: de 10/01 a 12/01 vira 10/01 00:00 até
    13/01 00:00.
    """
    if last_day < first_day:
        raise ValueError("O último dia precisa ser igual ou depois do primeiro.")
    start = timezone.make_aware(datetime.combine(first_day, time.min))
    end = timezone.make_aware(datetime.combine(last_day + timedelta(days=1), time.min))
    return start, end


def is_whole_days(slot):
    """True se o compromisso cobre dias inteiros (começa e termina à meia-noite)."""
    start = timezone.localtime(slot.start)
    end = timezone.localtime(slot.end)
    return start.time() == time.min and end.time() == time.min
