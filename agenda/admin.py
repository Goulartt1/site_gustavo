from django.contrib import admin, messages
from django.db.models import Case, Value, When
from django.utils import timezone

from . import services
from .forms import BusySlotAdminForm
from .models import BusySlot


class PeriodFilter(admin.SimpleListFilter):
    title = "período"
    parameter_name = "periodo"

    def lookups(self, request, model_admin):
        return [("proximos", "Próximos"), ("passados", "Passados")]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "proximos":
            return queryset.filter(end__gte=now)
        if self.value() == "passados":
            return queryset.filter(end__lt=now)
        return queryset


@admin.register(BusySlot)
class BusySlotAdmin(admin.ModelAdmin):
    form = BusySlotAdminForm
    list_display = ["__str__", "whole_days", "internal_note"]
    list_filter = [PeriodFilter]
    search_fields = ["internal_note"]
    date_hierarchy = "start"
    fieldsets = [
        ("Horário", {"fields": ["start", "end"]}),
        (
            "Ou bloqueie dias inteiros",
            {
                "fields": ["first_day", "last_day"],
                "description": "Para folgas e férias. Deixe o horário acima em branco.",
            },
        ),
        ("Detalhes", {"fields": ["internal_note"]}),
    ]

    @admin.display(description="dia inteiro", boolean=True)
    def whole_days(self, obj):
        return services.is_whole_days(obj)

    def get_ordering(self, request):
        # Próximos primeiro (do mais perto ao mais longe), depois os passados.
        past_last = Case(When(end__lt=timezone.now(), then=Value(1)), default=Value(0))
        return [past_last.asc(), "start"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Avisa (sem impedir) se o compromisso fica perto demais de outro:
        # às vezes o artista sabe que dá tempo, e a decisão é dele.
        conflicts = services.conflicting_slots(obj.start, obj.end, exclude_pk=obj.pk)
        if conflicts.exists():
            gap = services.min_gap()
            listed = "; ".join(str(slot) for slot in conflicts[:5])
            self.message_user(
                request,
                f"Atenção: este horário fica a menos de {int(gap.total_seconds() // 60)} "
                f"minutos de outro compromisso ({listed}). Foi salvo mesmo assim.",
                messages.WARNING,
            )
