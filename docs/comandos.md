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

## Django (manage.py)

| Comando | O que faz |
| --- | --- |
| `uv run django-admin startproject config .` | Cria o projeto Django. `config` é o nome da pasta de configurações; o `.` diz "crie aqui", sem uma pasta extra por fora. |
| `uv run python manage.py check` | Verifica a configuração do projeto e aponta erros, sem subir o servidor. |
| `uv run python manage.py runserver` | Sobe o servidor de desenvolvimento em http://127.0.0.1:8000. Recarrega sozinho quando um arquivo muda. `Ctrl+C` para parar. |
| `uv run python manage.py startapp accounts` | Cria a estrutura de um app novo (`models.py`, `admin.py`, `apps.py`, `tests.py`, `views.py`, `migrations/`). Depois, é preciso adicioná-lo em `INSTALLED_APPS`. |
| `uv run python manage.py makemigrations` | Compara os modelos com as migrações existentes e gera um arquivo novo com a diferença. Não mexe no banco. Os arquivos gerados vão para o git. |
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

Antes de abrir um pull request, rodar os três: `ruff check .`, `ruff format --check .` e `pytest`. São os mesmos passos do CI.

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
