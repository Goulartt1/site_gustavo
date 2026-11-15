# Site do artista (Projeto 2)

Site para um músico divulgar o trabalho e receber pedidos de orçamento pelo WhatsApp.
Projeto de portfólio e de aprendizado: o dono do projeto é dev iniciante (Python/Django) e quer entender cada decisão.

## Objetivos de aprendizado
- Entender e saber explicar cada escolha; nunca aceitar código que não saiba explicar.
- Arquitetura é foco explícito: onde cada responsabilidade mora, quais são as alternativas e o que cada uma custa.
- Praticar o que o mercado cobra de um dev júnior: testes, CI, git com branches e pull requests, deploy.

## Stack (decidida)
- Linguagem: Python 3.13
- Back-end: Django 5.2 (LTS, suporte até abril de 2028); Django REST Framework a partir da fase 2
- Banco: PostgreSQL (SQLite aceitável só no início do desenvolvimento local)
- Site público: templates Django (por causa do SEO), com Tailwind CSS v4 via django-tailwind-cli (sem Node), recursos modernos de CSS (view transitions, animações na rolagem) e, quando houver necessidade concreta, GSAP e HTMX + Alpine.js
- Design é foco do projeto: visual atual e marcante. Direção visual escolhida: A · Galpão (ver `docs/decisoes.md`, decisão 12)
- Painel do artista: Django Admin na fase 1; React (Vite) consumindo a API DRF na fase 3
- Qualidade: ruff (lint e formatação) e pytest-django; GitHub Actions rodando os dois a cada push
- Métricas: analytics sem cookies e agregado (ex.: Umami ou Cloudflare Web Analytics)
- Armazenamento das fotos: Cloudflare R2 (bucket privado, via django-storages)
- Deploy: Google Cloud Run (São Paulo) + Neon (PostgreSQL, São Paulo) + Cloudflare (DNS, Worker na frente, proteção contra bots); proteção de gastos em camadas (ver `docs/deploy.md` e decisões 14 e 15)

## Arquitetura (princípios do projeto)
- Regras de negócio ficam fora das views e dos templates, em funções próprias (ex.: verificar se um horário está livre). Assim a mesma regra serve ao site em templates (fase 1) e à API (fase 2) sem ser reescrita.
- Apps Django separados por assunto, cada um com responsabilidade clara.
- Configuração por variáveis de ambiente: o mesmo código roda em desenvolvimento e em produção.
- Preferir a solução mais simples que resolve. Um padrão novo só entra quando há um problema concreto que o justifique.
- Toda etapa nomeia a decisão de arquitetura envolvida, as alternativas e o custo de cada uma. A decisão é registrada em `docs/decisoes.md`.

## Ambiente de desenvolvimento
- Windows com PowerShell 7 (`pwsh`). Comandos passados ao dono do projeto devem ser para PowerShell.
- WSL2 adiado: avaliar na fase 4 (Docker exige WSL2) ou levar para o próximo projeto.
- PostgreSQL local instalado no Windows via winget (sem Docker na fase 1).
- `.gitattributes` com `* text=auto eol=lf` para manter quebras de linha no padrão Linux (CI e produção são Linux).
- Ferramentas: git, gh (GitHub CLI), uv (gerencia Python, ambiente e dependências).

## Convenções
- Código (modelos, variáveis, funções) em inglês.
- Textos da interface, documentação e mensagens de commit em português.
- Commits e títulos de pull request no padrão Conventional Commits: `tipo(escopo): descrição` (ex.: `feat(accounts): cria modelo de usuário próprio`).

## O artista (do material de divulgação, recebido em 2026-11-15)
- Gustavo Locks: músico, gaiteiro e cantor; toca desde criança; mais de 400 eventos e bailes.
- Estilos: gaúchas, sertanejo universitário, forró, pagode, modão e reggae. O diferencial é a versatilidade.
- Eventos: bares e restaurantes, aniversários, casamentos, bailes e eventos tradicionais, corporativos.
- "Novo Projeto": uma banda completa em um único músico. O teclado é interligado ao acordeon e ele controla guitarra, bateria, baixo, violão etc., 100% ao vivo, sem playback nem VS. Vantagens: praticidade, menos espaço, contratação simples, variedade e som de banda completa.
- Orçamento personalizado: considera tipo de evento, duração, estrutura e necessidades (o pedido da etapa 10 deve perguntar o tipo de evento).
- Contato: WhatsApp com DDD 48 (região de Florianópolis, SC) e Instagram @locksgustavo. O número entra pelo Admin, não no código.
- Visual do material: fundo grafite, títulos condensados em caixa alta, fotos recortadas de chapéu e acordeon; há uma marca "Gustavo Locks" no teclado.

## Funções
### Visitante
- Apresentação/bio do artista
- Galeria de fotos e vídeos dos shows (vídeos via link do YouTube)
- Repertório
- Ler depoimentos aprovados e enviar depoimento (fica pendente de aprovação)
- Sugerir música para o repertório
- Pedido de orçamento: data, endereço, horário de início e duração (e tipo de evento) → responde "livre" ou "a consultar", nunca "ocupado" → abre o WhatsApp nos dois casos com mensagem pronta. SEM preço no site. O pedido NÃO é salvo no banco; só o clique no WhatsApp é contado (ver seção Pedidos de orçamento).
- Sem calendário público por enquanto: a disponibilidade só aparece no pedido de orçamento (decisão 19)
- Links para Instagram, YouTube e outras redes; botão flutuante do WhatsApp

### Artista (área logada)
- Gerenciar fotos, vídeos e repertório
- Ver e aceitar/recusar sugestões de músicas
- Aprovar/recusar depoimentos
- Gerenciar agenda (marcar horários ocupados/livres)
- Métricas simples: acessos, região aproximada, data/horário, cliques no WhatsApp

## Agenda
- Funciona por horário, não por dia: o músico pode fazer mais de um show no mesmo dia.
- Um compromisso tem início e fim com data e hora, e pode atravessar a meia-noite.
- Intervalo mínimo entre shows: um valor único no perfil do artista (padrão 2h), aplicado antes e depois de cada compromisso.
- Dia inteiro (folga, férias): o mesmo modelo BusySlot, com atalho no Admin (00:00 do primeiro dia até 00:00 do dia seguinte ao último).
- Conflito no Admin gera aviso, não bloqueio: a decisão é do artista.
- A agenda é interna. Mostrar "ocupado" ao público faria o músico perder contatos (encaixe após cancelamento, ajuste de horário, outra data); ver decisão 19. Calendário público pode voltar se a agenda lotar.

## Pedidos de orçamento
- Não são salvos no banco. O site monta a mensagem e abre o WhatsApp; a negociação e o histórico ficam no WhatsApp.
- Considerado e descartado: salvar histórico de pedidos. O site não sabe se a mensagem foi enviada nem se o show aconteceu, então o histórico não seria confiável e ainda guardaria dado pessoal (LGPD).
- Pode ser revisto se o artista sentir falta; é uma decisão barata de mudar depois.

## Modelos iniciais (proposta, revisar antes de implementar)
- User: usuário customizado, criado no início do projeto
- ArtistProfile: name, bio, photo, whatsapp, links das redes (registro único)
- BusySlot: start, end, internal_note (nunca exibida ao público)
- Photo: image, caption, order, is_active
- Video: youtube_url, title, order, is_active
- Song: title, original_artist, is_active
- SongSuggestion: title, artist, suggested_by (opcional), status (pendente/aceita/recusada), created_at
- Testimonial: name, text, status (pendente/aprovado/recusado), created_at

## Fases
1. Site público em templates + Django Admin como painel + testes + CI + deploy
2. API com DRF + autenticação + testes da API
3. Painel do artista em React (Vite) substituindo o Admin
4. Aplicação inteira em Docker (exige WSL2), deploy automático, analytics

### Etapas da fase 1
1. Fundação: repositório, ambiente, projeto Django, configurações por variáveis de ambiente
2. Rede de segurança: ruff, pytest, primeiro teste, CI
3. PostgreSQL local (instalado no Windows via winget)
4. Template base, home e ArtistProfile no Admin
5. Deploy do esqueleto
6. Galeria: fotos e vídeos do YouTube
7. Repertório e sugestão de música (primeiro formulário público)
8. Depoimentos com aprovação (candidata a ser feita pelo dono do projeto, com revisão)
9. Agenda interna por horário (sem calendário público)
10. Pedido de orçamento que abre o WhatsApp
11. Redes, botão flutuante e SEO básico

## Pendências
- Nome, estilos, WhatsApp e Instagram recebidos (ver seção O artista); faltam a cidade exata e a área de atendimento, nome do "Novo Projeto" (se houver), canal do YouTube e a lista real de músicas
- Fotos e vídeos reais
- Visual: direção A · Galpão definida (cores, fontes, estilo); faltam o arquivo do logotipo (se houver) e fotos reais; as fotos do material podem servir de provisórias, se o artista autorizar
- Contas de produção a criar pelo dono do projeto (Registro.br, Cloudflare, Neon, Google Cloud): passo a passo em `docs/deploy.md`

## Regras de segurança e privacidade
- Formulários públicos com proteção anti-spam (captcha ou limite de envios)
- Aviso de consentimento (LGPD) onde houver coleta de nome
- Segredos só em variáveis de ambiente (.env fora do git)

## Como trabalhar comigo (importante)
- Estou aprendendo. Antes de escrever código, explique o plano da etapa e POR QUE dessa escolha, com alternativas quando houver.
- Trabalhe em etapas pequenas e peça minha aprovação antes de cada uma.
- Cada etapa em uma branch própria, com pull request que eu reviso antes de entrar na principal.
- Depois de cada etapa, resuma o que foi feito e quais conceitos apareceram (ex.: migrations, ORM, CSRF).
- Ao fim de cada etapa, faça duas ou três perguntas para eu responder com as minhas palavras antes de seguirmos.
- Não faça mudanças grandes ou fora do escopo sem perguntar.
- Escreva testes junto com as funcionalidades.
- Commits pequenos, com mensagens em português explicando o que mudou.
- De vez em quando, me proponha fazer uma alteração pequena sozinho e depois revise o que eu fiz.

### Terminal e fluxo de trabalho
- Quero aprender a usar o terminal em vez de interfaces gráficas (git, gh, uv, manage.py, psql, curl etc.).
- Fluxo padrão: eu rodo os comandos na minha máquina; Claude escreve o código numa branch e envia ao GitHub; eu reviso, testo e aprovo o pull request pelo terminal. Exceções: quando eu pedir, Claude executa por mim.
- Todo comando novo é explicado parte por parte (programa, subcomando, opções).
- Os comandos usados se acumulam em `docs/comandos.md`, organizados por assunto.
- De vez em quando, propor pequenos exercícios de terminal.
