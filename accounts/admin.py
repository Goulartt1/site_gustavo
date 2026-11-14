from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

# UserAdmin é a tela de usuários que o Django já traz (listagem, busca,
# troca de senha, permissões). Reaproveitamos para o nosso User.
admin.site.register(User, UserAdmin)
