# Receita da imagem do site para o Google Cloud Run.
# O Cloud Build monta a imagem na nuvem (gcloud run deploy --source .),
# então não é preciso ter Docker instalado no PC.
FROM python:3.13-slim

# uv na mesma versão usada no desenvolvimento, copiado da imagem oficial.
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# 1) Dependências antes do código: enquanto o uv.lock não muda, o Docker
#    reaproveita esta etapa e o build fica mais rápido.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev

# 2) Código do projeto (o .dockerignore deixa de fora .env, .venv, media...).
COPY . .

# 3) CSS do Tailwind e estáticos. A SECRET_KEY aqui é fictícia, só para o
#    Django carregar durante o build; a real vem do Secret Manager ao rodar.
RUN SECRET_KEY=build-only DEBUG=False .venv/bin/python manage.py tailwind build \
    && SECRET_KEY=build-only DEBUG=False .venv/bin/python manage.py collectstatic --noinput \
    && rm -rf .django_tailwind_cli

# Roda sem privilégios de administrador.
RUN useradd --create-home app
USER app

ENV PATH="/app/.venv/bin:$PATH"

# O Cloud Run informa a porta em $PORT. Um processo com 8 threads é o
# recomendado pelo Google para o Cloud Run; o timeout fica a cargo dele.
CMD exec gunicorn config.wsgi:application --bind :$PORT --workers 1 --threads 8 --timeout 0
