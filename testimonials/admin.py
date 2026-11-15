from django.contrib import admin, messages
from django.db.models import Case, Value, When

from . import services
from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["name", "short_text", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "text"]
    actions = ["approve", "reject"]
    # O texto é de quem escreveu: o artista aprova ou recusa, mas não edita.
    readonly_fields = ["name", "text", "created_at"]

    @admin.display(description="depoimento")
    def short_text(self, obj):
        return obj.text if len(obj.text) <= 80 else f"{obj.text[:80]}…"

    def get_ordering(self, request):
        # Pendentes primeiro, depois os mais novos (mesma ideia das sugestões).
        pending_first = Case(
            When(status=Testimonial.Status.PENDING, then=Value(0)), default=Value(1)
        )
        return [pending_first.asc(), "-created_at"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Aprovar os depoimentos selecionados")
    def approve(self, request, queryset):
        count = services.approve_testimonials(queryset)
        self.message_user(request, f"{count} depoimento(s) aprovado(s).", messages.SUCCESS)

    @admin.action(description="Recusar os depoimentos selecionados")
    def reject(self, request, queryset):
        count = services.reject_testimonials(queryset)
        self.message_user(request, f"{count} depoimento(s) recusado(s).", messages.SUCCESS)
