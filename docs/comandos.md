# Comandos usados no projeto

Comandos em PowerShell, organizados por assunto. Cada um com o que faz e por que foi usado.

## uv (Python, ambiente e dependências)

| Comando | O que faz |
| --- | --- |
| `uv init --python 3.13` | Cria um projeto Python novo (`pyproject.toml`, `.python-version`, `.gitignore`, repositório git) fixando o Python 3.13. |
| `uv add "django>=5.2,<5.3"` | Adiciona uma dependência ao `pyproject.toml`, resolve as versões, grava no `uv.lock` e instala na `.venv`. As aspas protegem o `<` e o `>` do PowerShell. |
| `uv sync` | Deixa a `.venv` idêntica ao `uv.lock`: cria a `.venv` se não existir, instala o que falta e remove o que sobra. |
| `uv run <comando>` | Executa um comando dentro da `.venv` sem precisar ativá-la. Ex.: `uv run python manage.py check`. |

### Recriar a `.venv` (ex.: depois de mover a pasta do projeto)

A `.venv` guarda caminhos absolutos nos executáveis de `.venv\Scripts`. Se a pasta muda de lugar, eles apontam para o caminho antigo. A `.venv` é descartável: apaga e recria.

```powershell
Remove-Item -Recurse -Force .venv
uv sync
```

## Django (manage.py)

| Comando | O que faz |
| --- | --- |
| `uv run django-admin startproject config .` | Cria o projeto Django. `config` é o nome da pasta de configurações; o `.` diz "crie aqui", sem uma pasta extra por fora. |
| `uv run python manage.py check` | Verifica a configuração do projeto e aponta erros, sem subir o servidor. |

## git

| Comando | O que faz |
| --- | --- |
| `git status` | Mostra a branch atual e os arquivos novos, modificados ou preparados para commit. |
| `git add .` | Prepara (coloca na "staging area") todos os arquivos da pasta atual para o próximo commit, respeitando o `.gitignore`. |
| `git commit -m "mensagem"` | Grava um commit com o que foi preparado. `-m` passa a mensagem direto na linha de comando. |

## gh (GitHub CLI)

| Comando | O que faz |
| --- | --- |
| `gh auth status` | Mostra em qual conta do GitHub o `gh` está logado. |
| `gh repo create site_gustavo --public --source . --push` | Cria o repositório no GitHub. `--public`: visível para todos. `--source .`: usa o repositório git local desta pasta. `--push`: envia os commits logo em seguida (e configura o remoto `origin`). |
