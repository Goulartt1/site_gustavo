# Comandos usados no projeto

Comandos em PowerShell, organizados por assunto. Cada um com o que faz e por que foi usado.

## uv (Python, ambiente e dependências)

| Comando | O que faz |
| --- | --- |
| `uv init --python 3.13` | Cria um projeto Python novo (`pyproject.toml`, `.python-version`, `.gitignore`, repositório git) fixando o Python 3.13. |
| `uv add "django>=5.2,<5.3"` | Adiciona uma dependência ao `pyproject.toml`, resolve as versões, grava no `uv.lock` e instala na `.venv`. As aspas protegem o `<` e o `>` do PowerShell. |
| `uv add django-environ` | Mesmo comando, sem restrição de versão: o uv escolhe a mais nova e grava a faixa mínima (`>=0.14.0`). |
| `uv add --dev ruff` | Adiciona uma dependência de desenvolvimento: vai para o grupo `dev` (`[dependency-groups]`) em vez de `dependencies`. Serve para quem programa, não para o site rodar. Aceita várias de uma vez: `uv add --dev pytest pytest-django`. |
| `uv sync` | Deixa a `.venv` idêntica ao `uv.lock`: cria a `.venv` se não existir, instala o que falta e remove o que sobra. Instala também o grupo `dev`. |
| `uv sync --locked` | Igual, mas falha se o `uv.lock` estiver desatualizado em relação ao `pyproject.toml`. Usado no CI. |
| `uv sync --no-dev` | Instala só as dependências principais, sem o grupo `dev`. Para produção. |
| `uv run <comando>` | Executa um comando dentro da `.venv` sem precisar ativá-la. Antes, confere se a `.venv` está em dia com o `uv.lock` (e recria se precisar). Ex.: `uv run python manage.py check`. |

### Recriar a `.venv` (ex.: depois de mover a pasta do projeto)

A `.venv` guarda caminhos absolutos nos executáveis de `.venv\Scripts`. Se a pasta muda de lugar, eles apontam para o caminho antigo. A `.venv` é descartável: apaga e recria.

```powershell
Remove-Item -Recurse -Force .venv
uv sync
```

## Variáveis de ambiente (.env)

| Comando | O que faz |
| --- | --- |
| `Copy-Item .env.example .env` | Copia o modelo para criar o seu `.env` (equivale ao `cp` do Linux). Depois, preencha os valores. |
| `uv run python -c "import secrets; print(secrets.token_urlsafe(50))"` | Gera uma chave secreta aleatória. `-c` roda um trecho de código sem criar arquivo. `token_urlsafe` só usa letras, números, `-` e `_`, seguros dentro do `.env`. |
| `notepad .env` | Abre o arquivo no Bloco de Notas (ou `code .env` para o VS Code). |
| `Rename-Item .env .env.off` | Renomeia um arquivo. Útil para testar o projeto sem o `.env` (e desfazer com `Rename-Item .env.off .env`). |

## PostgreSQL local

### Instalação (uma vez por computador)

**1. Instalar o PostgreSQL 18**

```powershell
winget search --id PostgreSQL.PostgreSQL
winget install --id PostgreSQL.PostgreSQL.18 --interactive
```

- `winget search` lista as versões disponíveis; `--id` filtra pelo identificador do pacote.
- `winget install --id ...` instala aquele pacote. `--interactive` mostra as telas do instalador em vez de instalar em silêncio, para você escolher a senha.
- No instalador: defina a senha do administrador `postgres` (guarde num gerenciador de senhas), mantenha a porta `5432` e desmarque o "Stack Builder" no fim (não é necessário).

**2. Colocar o `psql` no PATH**

O instalador não faz isso. O PATH é a lista de pastas onde o terminal procura programas.

```powershell
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$userPath;C:\Program Files\PostgreSQL\18\bin", "User")
```

- A primeira linha lê o PATH do seu usuário; a segunda grava o mesmo PATH com a pasta do PostgreSQL no fim.
- Feche e abra o terminal, e confira com `psql --version`.

**3. Criar o usuário e o banco do projeto**

```powershell
psql -U postgres
```

`psql` é o terminal do PostgreSQL; `-U postgres` entra como administrador (pede a senha do passo 1). Dentro dele (o prompt muda para `postgres=#`):

```sql
CREATE ROLE site_gustavo WITH LOGIN PASSWORD 'escolha-uma-senha' CREATEDB;
CREATE DATABASE site_gustavo OWNER site_gustavo;
\q
```

- `CREATE ROLE ... LOGIN` cria um usuário que pode se conectar. `CREATEDB` deixa ele criar bancos (o pytest precisa, para o banco de teste).
- `CREATE DATABASE ... OWNER` cria o banco do projeto com esse usuário como dono.
- `\q` sai do `psql`. Comandos SQL terminam com `;`; comandos do próprio `psql` começam com `\`.
- Na senha, use só letras e números: ela vai dentro de uma URL no `.env`, onde `@`, `:` e `/` têm significado especial.

**4. Apontar o projeto para o PostgreSQL**

No `.env`, acrescente (ou ajuste) a linha, com a senha do passo 3:

```
DATABASE_URL=postgres://site_gustavo:escolha-uma-senha@localhost:5432/site_gustavo
```

**5. Criar as tabelas e conferir**

```powershell
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run pytest
```

O banco novo começa vazio: o `migrate` cria as tabelas e o `createsuperuser` cria o seu login do Admin. O `db.sqlite3` antigo pode ser apagado (`Remove-Item db.sqlite3`).

### Comandos do dia a dia

| Comando | O que faz |
| --- | --- |
| `psql -U site_gustavo -d site_gustavo` | Entra no banco do projeto com o usuário do projeto. `-d` escolhe o banco. |
| `\dt` (dentro do `psql`) | Lista as tabelas do banco. |
| `\d accounts_user` (dentro do `psql`) | Mostra as colunas de uma tabela. |
| `SELECT id, username, is_superuser FROM accounts_user;` | Consulta SQL: lista os usuários. Horários aparecem em UTC (ver decisão 4). |
| `uv run python manage.py dbshell` | Abre o `psql` já conectado com os dados do `DATABASE_URL`. |

## Django (manage.py)

| Comando | O que faz |
| --- | --- |
| `uv run django-admin startproject config .` | Cria o projeto Django. `config` é o nome da pasta de configurações; o `.` diz "crie aqui", sem uma pasta extra por fora. |
| `uv run python manage.py check` | Verifica a configuração do projeto e aponta erros, sem subir o servidor. |
| `uv run python manage.py runserver` | Sobe o servidor de desenvolvimento em http://127.0.0.1:8000. Recarrega sozinho quando um arquivo muda. `Ctrl+C` para parar. |
| `uv run python manage.py startapp accounts` | Cria a estrutura de um app novo (`models.py`, `admin.py`, `apps.py`, `tests.py`, `views.py`, `migrations/`). Depois, é preciso adicioná-lo em `INSTALLED_APPS`. |
| `uv run python manage.py makemigrations` | Compara os modelos com as migrações existentes e gera um arquivo novo com a diferença. Não mexe no banco. Os arquivos gerados vão para o git. |
| `uv run python manage.py makemigrations --check --dry-run` | Só confere se algum modelo mudou sem migração criada. `--dry-run` não grava nada; `--check` termina com erro se faltar migração. |
| `uv run python manage.py showmigrations repertoire` | Lista as migrações do app `repertoire`, com `[X]` nas já aplicadas no banco. |
| `uv run python manage.py migrate` | Aplica no banco as migrações ainda não aplicadas (cria e altera tabelas). |
| `uv run python manage.py test` | Executor de testes do próprio Django. Desde a etapa 2, o projeto usa o `pytest` (ver abaixo). |
| `uv run python manage.py createsuperuser` | Cria um usuário com acesso total ao Admin (http://127.0.0.1:8000/admin). Pede usuário, e-mail e senha. |
| `uv run python manage.py shell -c "..."` | Executa um trecho de Python com o projeto carregado e sai. Sem `-c`, abre o terminal interativo. |

## Qualidade: ruff e pytest

| Comando | O que faz |
| --- | --- |
| `uv run ruff check .` | Lint: procura problemas no código sem executá-lo (import sem uso, variável indefinida, sintaxe antiga). O `.` é a pasta atual. |
| `uv run ruff check . --fix` | Igual, e corrige sozinho o que for seguro corrigir (marcado com `[*]` na saída). |
| `uv run ruff format .` | Reescreve os arquivos no padrão de formatação (aspas, espaços, quebras de linha). |
| `uv run ruff format --check .` | Só verifica se há arquivo fora do padrão, sem alterar. Usado no CI. |
| `uv run ruff format --diff .` | Mostra o que a formatação mudaria, sem alterar. |
| `uv run pytest` | Roda todos os testes. Cria um banco de teste separado e apaga no fim. |
| `uv run pytest -v` | Lista cada teste pelo nome, com `PASSED` ou `FAILED`. |
| `uv run pytest -k admin` | Roda só os testes cujo nome contém `admin`. |
| `uv run pytest -x` | Para no primeiro teste que falhar. |
| `uv run pytest repertoire -v` | Roda só os testes de uma pasta (aqui, o app `repertoire`). |

Antes de abrir um pull request, rodar os três: `ruff check .`, `ruff format --check .` e `pytest`. São os mesmos passos do CI.

## Tailwind CSS (visual do site)

O CSS do site é gerado a partir de `tailwind/source.css` e das classes usadas nos templates. Sem esse passo, o site abre sem estilo.

| Comando | O que faz |
| --- | --- |
| `uv run python manage.py tailwind build` | Gera `assets/css/tailwind.css` uma vez, minificado. Na primeira vez, baixa o executável oficial do Tailwind para `.django_tailwind_cli/`. |
| `uv run python manage.py tailwind watch` | Fica observando os templates e o `source.css` e regera o CSS a cada mudança. `Ctrl+C` para parar. |
| `uv run python manage.py tailwind runserver` | Sobe o `runserver` e o `watch` juntos, num terminal só. É o jeito mais prático de trabalhar no visual. |

## Baixar arquivos (curl)

| Comando | O que faz |
| --- | --- |
| `curl -sSfL -o assets/js/htmx.min.js https://cdn.jsdelivr.net/npm/htmx.org@2.0.4/dist/htmx.min.js` | Baixa o HTMX para dentro do projeto. `-o` diz onde salvar; `-L` segue redirecionamentos; `-f` falha (em vez de salvar a página de erro) se o endereço não existir; `-sS` esconde a barra de progresso, mas mostra erros. A versão (`@2.0.4`) fica no endereço, então todo mundo baixa o mesmo arquivo. |
| `Get-FileHash assets/js/htmx.min.js` | (PowerShell) Mostra a impressão digital (SHA-256) do arquivo. Serve para conferir que é o mesmo arquivo de outra máquina. |

| `curl http://127.0.0.1:8000/robots.txt` | Faz uma visita como um navegador sem tela e mostra a resposta no terminal. Bom para conferir páginas de texto (robots.txt, sitemap.xml). Com o `runserver` ligado. |
| `curl -I http://127.0.0.1:8000/` | `-I` pede só os cabeçalhos da resposta (código 200, tipo do conteúdo), sem o HTML. |

## Admin e conteúdo

| Comando | O que faz |
| --- | --- |
| http://127.0.0.1:8000/admin → Artista → Perfil do artista | Onde o artista edita nome, frases, biografia, foto, WhatsApp e redes. A foto enviada fica em `media/` (fora do git). |

## git

| Comando | O que faz |
| --- | --- |
| `git rm <arquivo>` | Apaga o arquivo e já prepara a remoção para o próximo commit. |
| `git fetch --prune` | Baixa as novidades do GitHub sem mexer nos seus arquivos e apaga as referências locais a branches que já não existem lá. |
| `git status` | Mostra a branch atual e os arquivos novos, modificados ou preparados para commit. |
| `git diff` | Mostra as linhas alteradas e ainda não preparadas (`+` entrou, `-` saiu). Com um arquivo no fim, mostra só ele. `q` para sair. |
| `git add <arquivos>` | Prepara arquivos para o próximo commit. Nomear os arquivos (em vez de `git add .`) garante que só entra o que você escolheu. |
| `git add .` | Prepara todos os arquivos da pasta atual, respeitando o `.gitignore`. |
| `git commit -m "título" -m "corpo"` | Grava um commit. O primeiro `-m` é o título; o segundo, o corpo da mensagem. |
| `git log --oneline` | Lista os commits, um por linha (código curto e título). |
| `git switch -c <branch>` | Cria uma branch nova a partir do commit atual e troca para ela. Sem `-c`, só troca para uma branch existente. |
| `git push -u origin <branch>` | Envia a branch para o GitHub. `origin` é o apelido do repositório remoto; `-u` liga a branch local à remota, para os próximos `git push` não precisarem de argumentos. |

### Mensagens de commit (Conventional Commits)

Formato `tipo(escopo): descrição`, com a descrição em português. Ex.: `feat(accounts): cria modelo de usuário próprio`.
Tipos usados: `feat` (funcionalidade), `fix` (correção), `docs` (documentação), `test` (testes), `refactor` (reorganização sem mudar comportamento), `build` (dependências), `ci` (integração contínua), `chore` (manutenção).

## Google Cloud (gcloud)

O passo a passo completo do deploy está em `docs/deploy.md`. Os mais usados:

| Comando | O que faz |
| --- | --- |
| `winget install --id Google.CloudSDK` | Instala a CLI do Google Cloud (`gcloud`). |
| `gcloud init` | Faz login (abre o navegador) e escolhe o projeto padrão. |
| `gcloud run deploy gustavo-locks --source . --region southamerica-east1` | Monta a imagem a partir do `Dockerfile` e publica a versão nova do site. |
| `gcloud run services describe gustavo-locks --region southamerica-east1` | Mostra a configuração atual do serviço (endereço, teto de instâncias, variáveis). |
| `gcloud run services logs read gustavo-locks --region southamerica-east1 --limit 50` | Mostra os últimos registros (logs) do site, inclusive erros. |
| `gcloud run services update gustavo-locks --region southamerica-east1 --ingress=all` | Reabre o site ao público depois que o disjuntor o fechou. |
| `gcloud functions logs read disjuntor --region southamerica-east1` | Mostra o que o disjuntor decidiu nas últimas notificações de gasto. |

### Rodar comandos do Django no banco de produção (Neon)

```powershell
$env:DATABASE_URL = "connection-string-do-neon"
uv run python manage.py migrate
Remove-Item Env:DATABASE_URL
```

A variável vale só nesta janela do terminal e é apagada no fim, para não mexer em produção sem querer.

## gh (GitHub CLI)

| Comando | O que faz |
| --- | --- |
| `gh auth status` | Mostra em qual conta do GitHub o `gh` está logado. |
| `gh repo create site_gustavo --public --source . --push` | Cria o repositório no GitHub. `--public`: visível para todos. `--source .`: usa o repositório git local desta pasta. `--push`: envia os commits logo em seguida (e configura o remoto `origin`). |
| `gh pr create` | Abre um pull request da branch atual para a `main`. `--title` e `--body` definem título e descrição. |
| `gh pr view` | Mostra o resumo do pull request da branch atual. `--web` abre no navegador. |
| `gh pr diff` | Mostra todas as mudanças do pull request. |
| `gh pr merge` | Junta o pull request na `main`. `--squash` junta tudo num commit só; `--merge` mantém os commits separados. `--delete-branch` apaga a branch depois. |
| `gh pr checks` | Mostra o resultado do CI no pull request da branch atual (cada verificação com ✓ ou X). |
| `gh run list` | Lista as últimas execuções do GitHub Actions. |
| `gh run view <id> --log-failed` | Mostra o log só dos passos que falharam numa execução. É o primeiro comando a rodar quando o CI fica vermelho. |
