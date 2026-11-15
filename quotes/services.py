"""Regras do pedido de orçamento.

O pedido não é salvo: o site verifica a agenda, monta a mensagem e o link do
WhatsApp, e a conversa segue por lá (ver CLAUDE.md, seção Pedidos de orçamento).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from django.utils import formats, timezone

from agenda.services import is_available
from artist.whatsapp import whatsapp_url

# Resposta de disponibilidade: nunca "ocupado" (decisão 19).
FREE = "free"
TO_CONFIRM = "to_confirm"


@dataclass
class QuoteResult:
    start: datetime
    end: datetime
    availability: str
    message: str
    whatsapp_link: str

    @property
    def is_free(self):
        return self.availability == FREE


def event_period(day, start_time, duration_minutes):
    """Início e fim do evento no fuso do site. O fim pode cair no dia seguinte."""
    start = timezone.make_aware(datetime.combine(day, start_time))
    return start, start + timedelta(minutes=duration_minutes)


def format_duration(minutes):
    """90 -> "1h30"; 120 -> "2h"."""
    hours, rest = divmod(minutes, 60)
    return f"{hours}h{rest:02d}" if rest else f"{hours}h"


def build_message(artist_name, event_type, start, end, duration_minutes, place, notes=""):
    """Texto que chega ao artista no WhatsApp."""
    start = timezone.localtime(start)
    end = timezone.localtime(end)
    greeting = f"Olá, {artist_name}!" if artist_name else "Olá!"
    when = (
        f"{formats.date_format(start, 'l, d/m/Y')}, das {start:%H:%M} às {end:%H:%M} "
        f"({format_duration(duration_minutes)})"
    )
    lines = [
        f"{greeting} Vim pelo site e gostaria de um orçamento.",
        f"Evento: {event_type}",
        f"Data: {when}",
        f"Local: {place}",
    ]
    if notes:
        lines.append(f"Observações: {notes}")
    return "\n".join(lines)


def check_availability(day, start_time, duration_minutes):
    """FREE se a agenda tem o horário livre (com o intervalo entre shows); senão TO_CONFIRM."""
    start, end = event_period(day, start_time, duration_minutes)
    return FREE if is_available(start, end) else TO_CONFIRM


def check_quote(profile, *, day, start_time, duration_minutes, event_type, place, notes=""):
    """Verifica a agenda e monta a mensagem e o link do WhatsApp."""
    start, end = event_period(day, start_time, duration_minutes)
    availability = check_availability(day, start_time, duration_minutes)
    first_name = profile.name.split()[0] if profile.name else ""
    message = build_message(first_name, event_type, start, end, duration_minutes, place, notes)
    return QuoteResult(
        start=start,
        end=end,
        availability=availability,
        message=message,
        whatsapp_link=whatsapp_url(profile.whatsapp, message),
    )
