from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import User


class UserModelTests(TestCase):
    def test_project_uses_custom_user(self):
        # get_user_model() devolve o modelo apontado por AUTH_USER_MODEL.
        self.assertIs(get_user_model(), User)

    def test_create_user_hashes_password(self):
        user = User.objects.create_user(username="artista", password="senha-de-teste-123")

        self.assertNotEqual(user.password, "senha-de-teste-123")
        self.assertTrue(user.check_password("senha-de-teste-123"))
        self.assertFalse(user.is_staff)

    def test_create_superuser_can_access_admin(self):
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="senha-de-teste-123"
        )

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
