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

---

## 5. ruff para lint e formatação

**Etapa:** 2 (Rede de segurança) · **Data:** 2026-11-14

**Contexto.** Sem ferramenta, problemas simples (import esquecido, variável não usada) só aparecem quando alguém percebe, e cada pessoa formata o código de um jeito, o que gera discussão de estilo em revisão.

**Decisão.** **ruff**, como dependência de desenvolvimento, configurado no `pyproject.toml`: linha de 100 caracteres, Python 3.13, migrações excluídas e as regras E, W, F, I, B, UP e DJ. `ruff check` aponta problemas; `ruff format` padroniza o visual (aspas duplas, espaços, quebras de linha).

**Alternativas.**
- *flake8 + black + isort.* A combinação clássica. Faz o mesmo com três ferramentas e três configurações, e é bem mais lenta.
- *pylint.* Mais regras e mais profundo, mas lento, barulhento por padrão e sem formatação.
- *Sem ferramenta.* Zero configuração, mas o padrão depende de disciplina e de revisão manual.

**Custo.** A primeira formatação mexeu em quase todo o código (ficou em commit separado, tipo `style`). Algumas regras podem ser chatas em casos específicos; quando isso acontecer, desligar a regra de forma pontual e explicada (`# noqa: CÓDIGO`).

---

## 6. pytest e pytest-django para testes

**Etapa:** 2 (Rede de segurança) · **Data:** 2026-11-14

**Contexto.** O Django traz um executor de testes baseado em `unittest` (classes `TestCase`, `self.assertEqual`). Funciona, mas o mercado Python usa majoritariamente o pytest.

**Decisão.** **pytest + pytest-django**, como dependências de desenvolvimento. Testes escritos como funções com `assert`; os que usam o banco levam `@pytest.mark.django_db`. Fixtures do pytest-django (`client`, `admin_client`) para simular requisições. Os testes ficam em `tests.py` dentro de cada app.

**Alternativas.**
- *Executor do Django (`manage.py test`).* Sem dependência nova, mas mais verboso e com saída de erro menos clara. O pytest roda os testes nesse estilo sem mudança, então a troca era barata.
- *Pasta `tests/` por app em vez de `tests.py`.* Melhor quando há muitos testes. Fica para quando um app tiver testes suficientes para justificar.

**Custo.** Duas dependências de desenvolvimento. É preciso lembrar da marca `django_db`: sem ela, o pytest-django bloqueia o acesso ao banco e o teste falha com uma mensagem explicando isso.

---

## 7. CI com GitHub Actions

**Etapa:** 2 (Rede de segurança) · **Data:** 2026-11-14

**Contexto.** Rodar lint e testes dependia de lembrar. Um erro podia chegar à `main` sem ninguém perceber.

**Decisão.** Workflow `.github/workflows/ci.yml` que, numa máquina Ubuntu, roda `uv sync --locked`, `ruff check`, `ruff format --check` e `pytest`.
- Dispara em todo pull request e em todo push na `main`. Push em branch de PR não dispara, para não rodar tudo duas vezes.
- `uv sync --locked` falha se o `uv.lock` estiver desatualizado em relação ao `pyproject.toml`.
- A `SECRET_KEY` do CI é um valor fixo escrito no workflow: a máquina só roda testes e é descartada, então não há o que proteger.

**Alternativas.**
- *GitLab CI, CircleCI e outros.* Equivalentes, mas exigiriam integrar outro serviço; o repositório já está no GitHub.
- *Chave do CI nos secrets do GitHub.* Necessário para segredos reais (ex.: credenciais de deploy). Para uma chave de teste descartável, só esconderia um valor que não precisa ser escondido.
- *pre-commit (rodar o ruff antes de cada commit, na máquina).* Complementa o CI, mas não o substitui (dá para pular). Pode entrar depois se esquecer de formatar virar um problema frequente.

**Custo.** Cada pull request leva um ou dois minutos para ter o resultado. Gratuito para repositório público.

---

## 8. Proteção da branch main

**Etapa:** 2 (Rede de segurança) · **Data:** 2026-11-14

**Contexto.** Com o CI pronto, ainda seria possível fazer push direto na `main` ou fazer merge de um pull request com o CI vermelho.

**Decisão.** Regra de proteção na `main`: mudanças só por pull request, e o merge só é liberado com o CI verde.

**Alternativas.**
- *Sem proteção, confiando na disciplina.* Funciona até o primeiro descuido.
- *Exigir também aprovação de outra pessoa.* É o padrão em times, mas o projeto tem um só desenvolvedor, e o GitHub não deixa aprovar o próprio pull request: o merge ficaria impossível.

**Custo.** Até correções pequenas precisam de branch e pull request. É justamente o fluxo que o projeto quer praticar.

---

## 9. PostgreSQL nativo no Windows, com usuário próprio do projeto

**Etapa:** 3 (PostgreSQL local) · **Data:** 2026-11-14

**Contexto.** A produção vai usar PostgreSQL. Desenvolver em SQLite esconde diferenças (o PostgreSQL é mais rígido com tipos, tamanhos de texto e consultas com datas), que só apareceriam no deploy.

**Decisão.**
- PostgreSQL 18 instalado no Windows pelo `winget` (instalador interativo, para o dono do projeto definir a senha do administrador).
- O projeto usa um usuário próprio (`site_gustavo`), dono do banco `site_gustavo`, com permissão `CREATEDB` (o pytest cria e apaga um banco de teste a cada execução). O administrador `postgres` fica só para manutenção.
- O CI roda os testes num contêiner `postgres:18`, a mesma versão.

**Alternativas.**
- *Docker.* Banco isolado e fácil de recriar, mas exige WSL2, adiado para a fase 4.
- *Banco na nuvem para desenvolvimento (ex.: Neon).* Sem instalação, mas depende de internet e de conta externa.
- *Continuar no SQLite.* Zero instalação, mas diverge da produção.
- *Usar o administrador `postgres` no projeto.* Menos passos, mas uma senha vazada daria acesso a tudo no servidor de banco. O usuário próprio limita o estrago ao banco do projeto.
- *CI em SQLite.* Um pouco mais rápido, mas deixaria passar erros que só acontecem no PostgreSQL.

**Custo.** Um serviço a mais rodando no Windows (inicia junto com o sistema). O SQLite continua funcionando como reserva (sem `DATABASE_URL`), mas não é mais o padrão.

---

## 10. Driver psycopg 3 (binary)

**Etapa:** 3 (PostgreSQL local) · **Data:** 2026-11-14

**Contexto.** O Django precisa de um driver para conversar com o PostgreSQL.

**Decisão.** `psycopg[binary]` (psycopg 3), nas dependências principais. O extra `binary` traz a biblioteca já compilada.

**Alternativas.**
- *psycopg2.* O driver clássico, ainda muito encontrado em tutoriais e projetos antigos. Funciona, mas está só em manutenção; o Django recomenda o psycopg 3 em projetos novos.
- *psycopg 3 sem `binary` (ou com `c`).* Exige ter a biblioteca do PostgreSQL (`libpq`) e ferramentas de compilação na máquina. Ganho de desempenho irrelevante para este projeto.

**Custo.** Nenhum relevante. Se a hospedagem exigir, trocar o extra é uma linha no `pyproject.toml`.

---

## 11. Front-end do site público: templates do Django com Tailwind CSS v4

**Etapa:** 4 (Template base e home) · **Data:** 2026-11-14

**Contexto.** O design é o foco do projeto: o site precisa de um visual atual e marcante, sem perder o SEO dos templates do Django.

**Decisão.**
- Templates do Django continuam montando o HTML.
- **Tailwind CSS v4** via `django-tailwind-cli`, que baixa o executável oficial do Tailwind (sem Node). Versão fixa em `TAILWIND_CLI_VERSION`. A identidade visual (cores, fontes, animações) fica no bloco `@theme` de `tailwind/source.css`, fora da pasta de estáticos.
- O CSS final (`assets/css/tailwind.css`) é gerado (`tailwind build`) e não vai para o git; o deploy gera o dele.
- Recursos modernos de CSS sem JavaScript: transição entre páginas (`@view-transition`), seções que aparecem ao rolar (`animation-timeline: view()`), animações respeitando `prefers-reduced-motion`.
- **GSAP** e **HTMX + Alpine.js** entram quando houver uma necessidade concreta (animação especial, formulário de orçamento com resposta na hora).

**Alternativas.**
- *Front-end separado em Astro ou Next.js consumindo uma API.* Componentes e otimização de imagem melhores para quem desenvolve, mas o resultado visual é o mesmo (HTML, CSS e JS no navegador), e exigiria antecipar a API (fase 2), manter dois projetos e dois deploys.
- *Pico.css.* Deixa o HTML apresentável sem esforço, mas não chega a um visual próprio.
- *CSS escrito à mão.* Controle total, mas bem mais lento para chegar no mesmo resultado.
- *Bootstrap.* Pesado e com cara de template.
- *Tailwind via Node (npm).* Mesmo resultado, com uma ferramenta a mais no ambiente e no deploy.

**Custo.** Um passo de build do CSS em desenvolvimento (`tailwind watch` ou `tailwind runserver`) e no deploy. As fontes vêm do Google Fonts por enquanto; avaliar hospedar as fontes no próprio site antes do lançamento (desempenho e privacidade).

---

## 12. Direção visual: A · Galpão

**Etapa:** 4 (Template base e home) · **Data:** 2026-11-14

**Contexto.** O artista toca música gaúcha e forró. Foram feitos três protótipos da página inicial para comparar.

**Decisão.** Direção **A · Galpão**: rústico e elegante. Madeira escura (`#17110d`), creme (`#f3e9da`), caramelo (`#e3a75b`) e vermelho de couro (`#8e2b1f`); Fraunces (serifada, itálica nos destaques) nos títulos e Inter Tight no texto; bordas tracejadas que lembram o pesponto do couro; moldura em arco para a foto.

**Alternativas.** *B · Arrasta-pé* (cores de chita, festivo, tipografia pesada) e *C · Pampa* (quase preto e dourado, editorial e cinematográfico). Protótipos: https://claude.ai/artifact/TTKrnBMkqGiVSDNSHGeeD6 (privado).

**Custo.** O visual depende de boas fotos do artista em ambiente quente (palco, galpão). Sem elas, a moldura fica com o espaço reservado.

---

## 13. Perfil do artista como registro único editado no Admin

**Etapa:** 4 (Template base e home) · **Data:** 2026-11-14

**Contexto.** Nome, frases de apresentação, biografia, foto, WhatsApp e redes aparecem no site inteiro e precisam ser editados pelo artista, sem mexer em código.

**Decisão.** Modelo `ArtistProfile` no app `artist`, com um único registro (`save()` sempre grava no `pk=1`; `ArtistProfile.load()` busca ou cria). No Admin, não dá para adicionar nem apagar, e a lista abre direto o formulário. Um *context processor* deixa o perfil e o link do WhatsApp disponíveis em todos os templates. Uma migração de dados cria o perfil com dados de exemplo. A regra do link do WhatsApp (`artist/whatsapp.py`) fica fora das views, para servir também à API na fase 2.

**Alternativas.**
- *Textos fixos nos templates.* Mais simples, mas o artista dependeria de um programador para trocar uma frase.
- *Pacote django-solo.* Faz o registro único pronto, mas é uma dependência para algo que cabe em poucas linhas.
- *Variáveis de ambiente.* São para configuração técnica, não para conteúdo editável.

**Custo.** Uma consulta ao banco por página (o perfil). Irrelevante no volume deste site; se um dia pesar, dá para usar cache.

---

## 14. Hospedagem: Google Cloud Run + Neon + Cloudflare (R2 e Worker)

**Etapa:** 5 (Deploy) · **Data:** 2026-11-15

**Contexto.** Músico iniciante, com pouquíssimos acessos previstos. O plano gratuito do Render (site dorme e leva ~1 minuto para acordar; banco expira em 30 dias) foi descartado pelo dono do projeto. Orçamento: o menor possível, com proteção contra gastos inesperados.

**Decisão.**
- **Site:** Google Cloud Run em São Paulo (`southamerica-east1`), imagem montada pelo Cloud Build a partir do `Dockerfile`. Desliga quando ninguém acessa e só cobra enquanto responde; com pouco acesso, fica dentro da cota gratuita mensal (em São Paulo a cota rende ~30% menos que nas regiões mais baratas, ainda assim sobra). Contrapartida: alguns segundos de espera na primeira visita depois de um tempo parado.
- **Banco:** Neon Free em São Paulo (1 GB, sem prazo de validade, sem cartão).
- **Fotos:** Cloudflare R2 (10 GB grátis), bucket privado com links assinados, via `django-storages`.
- **Estáticos:** WhiteNoise (nomes com hash e compressão) e cache no Cloudflare.
- **Domínio e entrada:** `gustavolocks.com.br` no Registro.br, DNS no Cloudflare e um Cloudflare Worker repassando as visitas ao Cloud Run (em São Paulo o Cloud Run não liga domínio próprio diretamente, e o plano gratuito do Cloudflare não troca o cabeçalho Host sem um Worker).
- **Segredos:** Google Secret Manager (dentro da cota gratuita).
- **Migrações:** por enquanto rodadas do PC apontando para o Neon, antes do deploy. Deploy manual com `gcloud run deploy`; automatizar na fase 4.

**Alternativas.**
- *Render Starter (US$ 7/mês, ~R$ 40).* Sempre ligado e mais simples, mas paga capacidade ociosa num site com pouco acesso. Caminho natural se o movimento crescer ou a espera incomodar.
- *Tudo no Render (~US$ 13/mês, ~R$ 77).* Uma conta só, mas pesado para o orçamento.
- *Fly.io com desligamento automático.* Também cobra só o uso (alguns reais/mês), mas o banco gerenciado deles é caro (US$ 38/mês) e o gratuito acabou.
- *AWS Lightsail (US$ 5/mês).* Servidor "cru": exigiria manter Linux, servidor web, HTTPS e atualizações. O plano gratuito da AWS expira em 6 meses.
- *Supabase.* Não hospeda o Django; o plano gratuito pausa o projeto após 7 dias com pouca atividade (exatamente o caso aqui) e o Pro custa US$ 25/mês.
- *Cloudinary para fotos.* Gratuito, mas o pacote de integração com o Django está praticamente abandonado e tem bug conhecido no Django 5.1+.

**Custo.** Mais peças para entender (Docker, Cloud Run, Worker). A espera de alguns segundos na primeira visita. Domínio passa a ser necessário (R$ 40/ano) para o Cloudflare ficar na frente.

---

## 15. Proteção contra gastos inesperados

**Etapa:** 5 (Deploy) · **Data:** 2026-11-15

**Contexto.** No Cloud Run, um robô acessando sem parar poderia gerar custo de processamento e de tráfego. O padrão do Cloud Run é subir até 100 cópias do site, e os orçamentos do Google só avisam, não cortam.

**Decisão.** Defesa em camadas:
1. **Teto técnico:** `--max-instances 1`, CPU cobrada só durante as visitas.
2. **Cloudflare na frente:** Bot Fight Mode, limite de 30 acessos a cada 10 s por IP, cache dos estáticos. O Worker gratuito para de responder após 100 mil acessos/dia, sem cobrança.
3. **Porta única:** o Django recusa (403) visitas sem o cabeçalho `X-Origin-Secret`, que só o Worker envia (`core/middleware.py`). Ninguém pula o Cloudflare usando o endereço `.run.app`.
4. **Avisos graduais:** um orçamento de R$ 50/mês manda e-mail a cada R$ 5 gastos (10% a 100%), mais um alerta de previsão em R$ 10. Os avisos são gratuitos.
5. **Disjuntor:** o mesmo orçamento publica o gasto num tópico Pub/Sub; uma função (`infra/disjuntor`) muda a entrada do serviço para "somente interna" quando o gasto chega a R$ 50. Reversível com um comando; nada é apagado.

**Alternativas.**
- *Só os avisos por e-mail.* Não cortam o gasto e chegam com horas de atraso.
- *Disjuntor que desliga o faturamento do projeto (exemplo da documentação do Google).* Corta tudo, mas pode levar à exclusão de recursos se o faturamento não for religado a tempo. Fechar só a entrada do serviço é mais seguro.
- *Load balancer do Google com Cloud Armor.* Proteção mais completa, mas custa por volta de US$ 18/mês só para existir.

**Custo.** Configuração inicial maior (passos 6 e 10 do `docs/deploy.md`). Num ataque extremo, o site fica fora do ar até ser reaberto, o que é a troca escolhida: site fechado em vez de conta alta.

---

## 16. Repertório: app próprio, estilos editáveis e sugestões que só mudam de situação

**Etapa:** 7 (Repertório) · **Data:** 2026-11-15

**Contexto.** O site mostra as músicas que o artista toca e recebe sugestões dos visitantes. O material de divulgação lista seis estilos (gaúchas, sertanejo universitário, forró, pagode, modão e reggae), e a lista pode mudar.

**Decisão.**
- **App `repertoire`**, separado de `artist`: repertório é um assunto à parte.
- **Estilo como tabela (`Style`)**, editável no Admin e criada já com os seis estilos (migração `0002_seed_styles`). A música aponta para o estilo com `on_delete=PROTECT`: não dá para apagar um estilo que ainda tem músicas.
- **Situação da sugestão como lista fixa no código (`TextChoices`)**: pendente, aceita ou recusada. Quem decide essas opções é o sistema, não o artista.
- **Aceitar só muda a situação** (`services.accept_suggestions`). "Aceitar" quer dizer "vou aprender"; o artista cadastra a música quando ela estiver pronta, e o site nunca anuncia o que ele ainda não toca.
- As regras ficam em `repertoire/services.py`, para a API da fase 2 reaproveitar.

**Alternativas.**
- *Tudo no app `artist`.* Mais rápido agora, mas mistura responsabilidades.
- *Estilo como `TextChoices`.* Mais simples, mas criar um estilo novo exigiria mudar o código e fazer deploy.
- *Aceitar cria a música automaticamente.* Mais prático, mas a sugestão chega sem estilo e apareceria no site antes da hora.

**Custo.** Uma tabela a mais e um passo a mais ao cadastrar música (escolher o estilo). O artista aceita a sugestão e depois cadastra a música à mão.

---

## 17. Proteção contra spam nos formulários públicos: campo-isca e limite por IP

**Etapa:** 7 (Repertório) · **Data:** 2026-11-15

**Contexto.** A sugestão de música é o primeiro formulário que qualquer visitante pode enviar. O CLAUDE.md exige proteção contra spam.

**Decisão.** Duas defesas, sem serviço externo e sem clique extra para o visitante. Desde a etapa 8, ficam em `core/antispam.py` e servem a todos os formulários públicos:
1. **Campo-isca:** um campo `website` fora da tela e escondido de leitores de tela. Robôs costumam preencher tudo; se vier preenchido, o envio é descartado, mas a resposta é a mesma de sucesso, para o robô não descobrir o truque.
2. **Limite por IP:** no máximo 5 sugestões por hora por endereço (`RateLimit` em `core/antispam.py`). Passou disso, a página responde 429 (Too Many Requests). A contagem fica no cache em memória do Django, suficiente porque o Cloud Run roda uma cópia só do site (`--max-instances 1`); se o site reiniciar, a contagem zera, o que é aceitável.

**De onde vem o IP.** Em produção, quem fala com o Django é o Worker do Cloudflare, então o endereço da conexão é o do Cloudflare. O Worker repassa o IP real no cabeçalho `X-Client-IP`, e o Django só confia nele quando `ORIGIN_SECRET` está definido, ou seja, quando o middleware já garantiu que a visita veio do Worker (`core/client_ip.py`).

**Alternativas.**
- *Captcha (Cloudflare Turnstile, reCAPTCHA).* Mais forte contra robôs sofisticados, mas exige conta e chaves, coloca um serviço externo na página e, no caso do reCAPTCHA, cookies de terceiros. Fica como reforço se aparecer spam de verdade.
- *Limite guardado no banco ou no Redis.* Funciona com várias cópias do site, mas hoje há uma só; seria peça a mais sem necessidade.

**Custo.** Robôs que respeitam o CSS (raros) passam pela isca; o limite segura o volume. Pessoas que compartilham o mesmo IP (uma empresa, uma rede de celular) dividem o limite de 5 por hora.

---

## 18. Depoimentos: publicação só com aprovação e autorização obrigatória

**Etapa:** 8 (Depoimentos) · **Data:** 2026-11-15

**Contexto.** Visitantes enviam depoimentos que, aprovados, aparecem no site com o nome de quem escreveu. É o segundo formulário público, muito parecido com a sugestão de música.

**Decisão.**
- **App `testimonials`** com o modelo `Testimonial` (nome, texto de até 600 caracteres, situação e data). Só os aprovados aparecem (`services.approved_testimonials`).
- **Autorização obrigatória (LGPD).** Na sugestão de música o nome é opcional e fica só com o artista; aqui ele é publicado, então o formulário só passa com a caixa de autorização marcada.
- **O artista aprova ou recusa, mas não edita** o texto (campos somente leitura no Admin): o depoimento continua sendo de quem escreveu.
- **Página `/depoimentos/`** com todos os aprovados e o formulário, e **os 3 mais novos na página inicial**. A seção da home some enquanto não houver nenhum aprovado.
- **Anti-spam compartilhado.** O campo-isca, o limite por IP e o fluxo de envio saíram do repertório para `core/antispam.py` (`HoneypotForm`, `RateLimit`, `submit_public_form`). Depoimento: 3 por hora por IP (um texto longo, ninguém manda muitos).

**Alternativas.**
- *Copiar o anti-spam do repertório.* Mais rápido, mas duas cópias da mesma regra tendem a ficar diferentes com o tempo. Com dois formulários, já havia o problema concreto que justifica extrair.
- *Depoimentos só na página inicial.* Menos uma página, mas a home ficaria comprida conforme os depoimentos chegam.
- *Deixar o artista corrigir erros de digitação.* Prático, mas publicaria com o nome da pessoa um texto que ela não escreveu.

**Custo.** O artista precisa aprovar cada depoimento antes de aparecer. O `core` passa a conhecer o app `testimonials` (a página inicial reúne as seções dos outros apps).

---

## 19. Agenda interna, sem calendário público: "livre" ou "a consultar"

**Etapa:** 9 (Agenda) · **Data:** 2026-11-15

**Contexto.** O plano original previa um calendário público com horários livres e ocupados. Na análise da etapa surgiu a pergunta de negócio: mostrar "ocupado" ajuda o músico? Um cliente que vê "ocupado" fecha o site, e o artista nunca fica sabendo. Perde a chance de encaixar o show se outro for cancelado, de ajustar o horário, de sugerir outra data ou de indicar um colega, e perde o termômetro de procura de cada data. Para um artista em início de carreira, uma agenda quase vazia também passa impressão de pouca procura.

**Decisão.**
- **Agenda só interna** (app `agenda`, modelo `BusySlot`): é a memória do artista e evita dois shows ao mesmo tempo. Sem página pública por enquanto.
- **Regra `services.is_available(início, fim)`**, com o **intervalo mínimo entre shows** (campo no perfil, padrão 120 minutos) aplicado antes e depois de cada compromisso. Encostar na borda não é conflito; show que atravessa a meia-noite bloqueia os dois dias.
- **No pedido de orçamento (etapa 10)**, a resposta será "livre" ou "a consultar", e o WhatsApp abre nos dois casos. Os erros não têm o mesmo peso: dizer "livre" quando não está quebra uma promessa; dizer "a consultar" quando está livre não custa nada.
- **Dias inteiros** usam o mesmo modelo, com atalho no Admin (`services.whole_days`). Uma tabela só para a regra consultar.
- **Conflito no Admin vira aviso, não bloqueio**: às vezes o artista sabe que dá tempo.
- O fim depois do início é garantido no formulário e também no banco (`CheckConstraint`).

**Alternativas.**
- *Calendário público com livre/parcial/ocupado e os horários indisponíveis.* Transparente e poupa mensagens, o que vale para quem tem agenda cheia. Aqui custaria contatos. Fica fácil de acrescentar depois, porque a regra já existe.
- *Intervalo por compromisso.* Mais preciso, mais trabalho a cada cadastro; o intervalo único resolve hoje.
- *Modelo separado para dias bloqueados.* Mais claro no Admin, mas toda regra teria de consultar duas tabelas.

**Custo.** O visitante não vê a agenda sozinho e precisa perguntar. Pedidos para datas ocupadas chegam ao WhatsApp e exigem resposta do artista, o que é justamente a oportunidade de negociar.

---

## 20. Pedido de orçamento: resposta ao vivo com HTMX, funcionando também sem JavaScript

**Etapa:** 10 (Pedido de orçamento) · **Data:** 2026-11-15

**Contexto.** O visitante informa tipo de evento, data, horário, duração e local; o site responde "livre" ou "a consultar" (decisão 19) e abre o WhatsApp com a mensagem pronta. Nada é salvo.

**Decisão.**
- **Resposta ao vivo com HTMX** (escolha do dono do projeto, para agregar valor à entrega): assim que data, horário e duração estão preenchidos, o quadro ao lado já mostra a disponibilidade, sem recarregar a página; com todos os campos, aparece a prévia da mensagem e o botão do WhatsApp. Só o quadro é trocado, então quem está digitando não perde o foco.
- **Melhoria progressiva:** é o mesmo formulário e a mesma view. Sem JavaScript (ou se o HTMX falhar), o envio recarrega a página com a resposta. A view sabe o que devolver pelo cabeçalho `HX-Request` e pelo campo `live`.
- **HTMX servido pelo próprio site** (`assets/js/htmx.min.js`, versão 2.0.4 fixa), carregado só na página de orçamento. O navegador do visitante não faz pedido a terceiros.
- **Privacidade:** pede cidade e bairro (ou o nome do local), não o endereço completo. Os dados vão por POST (fora dos logs do Cloud Run) e o botão leva direto ao `wa.me`.
- **Sem anti-spam neste formulário:** ele não salva nem envia nada; um robô não tem o que ganhar. O limite do Cloudflare segura excesso de acessos.
- **Sem contagem por enquanto:** cliques e procura por data ficam para o analytics da fase 4.
- **Botões "Pedir orçamento"** (cabeçalho e página inicial) levam ao formulário; o botão flutuante continua abrindo o WhatsApp direto, para quem só quer conversar.
- Regras em `quotes/services.py` (`check_availability`, `build_message`, `check_quote`), reaproveitando `agenda.services.is_available`.

**Alternativas.**
- *Dois passos sem JavaScript.* Mais simples e já funciona (é o modo reserva), mas a resposta só aparece depois de enviar.
- *Contar os pedidos verificados agora.* Daria um termômetro de procura imediato, mas seria um modelo a mais antes da ferramenta de métricas.
- *HTMX por CDN.* Menos arquivos no projeto, mas cada visita avisaria um servidor de terceiros.

**Custo.** Primeira biblioteca JavaScript do projeto (50 KB, só nesta página) e três templates parciais (`_block`, `_result`, `_availability`). A view atende três tipos de requisição, o que exige testes para cada um.

