from django.contrib import admin, messages
from django.db.models import Case, Value, When

from . import services
from .models import Song, SongSuggestion, Style


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "song_count"]
    # Muda a ordem direto na lista, sem abrir cada estilo.
    list_editable = ["order"]

    @admin.display(description="músicas")
    def song_count(self, obj):
        return obj.songs.count()


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ["title", "original_artist", "style", "is_active"]
    list_filter = ["style", "is_active"]
    search_fields = ["title", "original_artist"]
    list_editable = ["is_active"]


@admin.register(SongSuggestion)
class SongSuggestionAdmin(admin.ModelAdmin):
    list_display = ["title", "artist", "suggested_by", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["title", "artist"]
    actions = ["accept", "reject"]
    # As sugestões chegam pelo site; o artista só decide a situação.
    readonly_fields = ["title", "artist", "suggested_by", "created_at"]

    def get_ordering(self, request):
        # Pendentes primeiro, depois as mais novas. O banco calcula, para cada
        # linha, 0 se estiver pendente e 1 se não, e ordena por esse número.
        pending_first = Case(
            When(status=SongSuggestion.Status.PENDING, then=Value(0)), default=Value(1)
        )
        return [pending_first.asc(), "-created_at"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Aceitar as sugestões selecionadas")
    def accept(self, request, queryset):
        count = services.accept_suggestions(queryset)
        self.message_user(request, f"{count} sugestão(ões) aceita(s).", messages.SUCCESS)

    @admin.action(description="Recusar as sugestões selecionadas")
    def reject(self, request, queryset):
        count = services.reject_suggestions(queryset)
        self.message_user(request, f"{count} sugestão(ões) recusada(s).", messages.SUCCESS)
