import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import User

PASSWORD = "senha-de-teste-123"


# Modelo


def test_project_uses_custom_user():
    # get_user_model() devolve o modelo apontado por AUTH_USER_MODEL.
    assert get_user_model() is User


# django_db libera o acesso ao banco de teste. Sem a marca, o pytest-django
# bloqueia o banco, para que só os testes que precisam dele paguem o custo.
@pytest.mark.django_db
def test_create_user_hashes_password():
    user = User.objects.create_user(username="artista", password=PASSWORD)

    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)
    assert not user.is_staff


@pytest.mark.django_db
def test_create_superuser_can_access_admin():
    admin_user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password=PASSWORD
    )

    assert admin_user.is_staff
    assert admin_user.is_superuser


# Admin
# client e admin_client são fixtures do pytest-django: o pytest entrega um
# navegador de teste (client) ou um já logado como superusuário (admin_client)
# só por ter o nome no parâmetro da função.


@pytest.mark.django_db
def test_admin_login_page_is_in_portuguese(client):
    response = client.get(reverse("admin:login"))

    html = response.content.decode()
    assert response.status_code == 200
    assert 'lang="pt-br"' in html
    assert "Senha:" in html


@pytest.mark.django_db
def test_admin_requires_login(client):
    response = client.get(reverse("admin:index"))

    # 302 = redirecionamento: visitante não logado é mandado para o login.
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


@pytest.mark.django_db
def test_user_is_registered_in_admin(admin_client):
    response = admin_client.get(reverse("admin:accounts_user_changelist"))

    assert response.status_code == 200
