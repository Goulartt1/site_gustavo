from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Usuário do projeto.

    Por enquanto é idêntico ao usuário padrão do Django (herda tudo de
    AbstractUser). Existe para que campos novos possam ser adicionados
    depois sem trocar o modelo de usuário, o que é difícil de fazer
    depois do primeiro migrate.
    """
