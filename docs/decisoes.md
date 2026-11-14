# Decisões de arquitetura

Cada decisão registra o contexto, o que foi escolhido, as alternativas consideradas e o custo de cada uma.
Decisões podem ser revistas: quando isso acontecer, a entrada antiga fica e ganha uma nota apontando para a nova.

---

## 1. O projeto é uma aplicação, não um pacote

**Etapa:** 1 (Fundação) · **Data:** 2026-11-14

**Contexto.** O `uv init` criou o projeto no formato de pacote: `[build-system]` com `uv_build`, um comando em `[project.scripts]` e a pasta `src/`. Nesse formato, o uv "constrói" o projeto e o instala dentro da própria `.venv`, como se fosse uma biblioteca.

**Decisão.** Remover `[build-system]`, `[project.scripts]` e `src/`. O site roda com `manage.py` e o `pyproject.toml` serve só para listar dependências. No `uv.lock`, o projeto aparece como `source = { virtual = "." }`.

**Alternativas.**
- *Manter o formato de pacote.* Não quebra nada, mas acrescenta estrutura sem função (pasta `src/`, comando que só imprime "Hello") e um passo de instalação desnecessário. Só valeria se o código fosse ser instalado por outros projetos, o que não é o caso.

**Custo.** Nenhum relevante. Se um dia parte do código virar biblioteca, ela pode ganhar o próprio pacote.

---

## 2. Configuração por variáveis de ambiente com django-environ

**Etapa:** 1 (Fundação) · **Data:** 2026-11-14

**Contexto.** O `settings.py` gerado pelo Django traz `SECRET_KEY` escrita no código e `DEBUG = True` fixo. Isso expõe o segredo no git (o repositório é público) e obriga a editar código para mudar de ambiente.

**Decisão.** Usar o **django-environ**. `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` e `DATABASE_URL` vêm do ambiente do sistema ou de um arquivo `.env` (fora do git). O `.env.example` (no git) documenta as variáveis.
- `SECRET_KEY` não tem valor padrão: se faltar, o Django não sobe. Melhor quebrar com mensagem clara do que subir em produção com uma chave conhecida.
- `DEBUG` tem padrão `False`: esquecer de configurar erra para o lado seguro.
- O banco é definido por uma URL; sem ela, usa o SQLite local. Trocar para o PostgreSQL (etapa 3) é mudar uma linha do `.env`.
- Variável que existe no ambiente do sistema vale mais que a do `.env`: em produção, a hospedagem define as variáveis.

**Alternativas.**
- *`os.environ` puro.* Sem dependência nova, mas toda conversão é manual: texto `"True"` para booleano, texto separado por vírgula para lista, URL do banco para o dicionário `DATABASES`. Mais código e mais chance de erro.
- *python-decouple.* Simples e popular, mas não interpreta `DATABASE_URL` sozinho (precisaria de outra biblioteca, o dj-database-url).
- *pydantic-settings.* Valida tudo com tipos e mensagens detalhadas, mas exige escrever uma classe de configuração. Mais do que o projeto precisa agora.
- *Vários arquivos de settings (`dev.py`, `prod.py`).* Muito usado em tutoriais antigos. Duplica configuração e ainda precisaria de variáveis de ambiente para os segredos.

**Custo.** Uma dependência a mais. Cuidado com caracteres especiais em valores do `.env` (`#` pode virar comentário, `$` pode ser lido como referência a outra variável). Por isso a chave é gerada com `secrets.token_urlsafe`, que só usa letras, números, `-` e `_`.

---

## 3. Modelo de usuário próprio desde o início

**Etapa:** 1 (Fundação) · **Data:** 2026-11-14

**Contexto.** O Django traz um modelo de usuário pronto (`auth.User`). Trocá-lo depois que o banco foi criado (primeiro `migrate`) é difícil: tabelas e chaves estrangeiras já apontam para ele. A documentação do Django recomenda criar um modelo próprio no começo de todo projeto novo.

**Decisão.** App `accounts` com `class User(AbstractUser)`, sem campos extras por enquanto, definido em `AUTH_USER_MODEL = 'accounts.User'` antes do primeiro `migrate`. No Admin, reaproveita a tela padrão (`UserAdmin`).

**Alternativas.**
- *Manter `auth.User`.* Zero código agora, mas qualquer campo novo no futuro exigiria uma tabela de perfil separada ou uma migração trabalhosa.
- *`AbstractBaseUser`.* Controle total (por exemplo, login por e-mail em vez de username), mas exige escrever o gerenciador (`UserManager`), formulários e a tela do Admin. Não compensa para um site com uma única usuária entrando pelo Admin.

**Custo.** Um app pequeno a mais. Sempre referenciar o usuário por `settings.AUTH_USER_MODEL` (em chaves estrangeiras) ou `get_user_model()` (no código), nunca importando `auth.User` direto.

---

## 4. Horários salvos em UTC e exibidos em America/Sao_Paulo

**Etapa:** 1 (Fundação) · **Data:** 2026-11-14

**Contexto.** A agenda trabalha com horários que podem atravessar a meia-noite. Guardar hora local sem fuso é ambíguo (principalmente se o horário de verão voltar) e complica comparações.

**Decisão.** `USE_TZ = True`, `TIME_ZONE = 'America/Sao_Paulo'` e `LANGUAGE_CODE = 'pt-br'`. O banco guarda tudo em UTC; o Django converte para o fuso de São Paulo ao exibir e ao ler formulários.

**Alternativas.**
- *`USE_TZ = False` com hora local.* Mais simples de ler direto no banco, mas horários ficam ambíguos em mudanças de fuso e comparações ficam frágeis. A própria documentação do Django desaconselha em projetos novos.

**Custo.** Ao consultar o banco direto (ex.: no `psql`), os horários aparecem em UTC (3 horas à frente de Brasília). No código, usar `django.utils.timezone.now()` em vez de `datetime.now()`.
