from django.contrib import admin
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from .models import ArtistProfile


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    # Link digitado sem "https://" (ex.: instagram.com/...) ganha https, não http.
    # Também já deixa o comportamento igual ao padrão do Django 6.0.
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}
    fieldsets = [
        ("Apresentação", {"fields": ["name", "tagline", "headline", "bio", "photo"]}),
        ("Contato", {"fields": ["whatsapp", "city"]}),
        ("Redes sociais", {"fields": ["instagram_url", "youtube_url", "spotify_url"]}),
        ("Agenda", {"fields": ["min_gap_minutes"]}),
    ]

    # Registro único: não dá para adicionar outro nem apagar.
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Em vez de uma lista com um item só, abre direto o formulário.
        profile = ArtistProfile.load()
        return redirect(reverse("admin:artist_artistprofile_change", args=[profile.pk]))
