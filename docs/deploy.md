# Deploy: passo a passo

Como o site vai para o ar. Comandos em PowerShell. Faça na ordem; cada parte depende da anterior.

## Visão geral

```
Visitante ──► Cloudflare (DNS, bloqueio de bots, limite de acessos, cache)
                 │
                 ▼
            Worker do Cloudflare ──(com X-Origin-Secret)──► Cloud Run (Django, São Paulo)
                                                              │            │
                                                              ▼            ▼
                                                     Neon (PostgreSQL)   Cloudflare R2 (fotos)
```

| Peça | Serviço | Custo esperado |
| --- | --- | --- |
| Domínio | Registro.br | R$ 40/ano |
| DNS, proteção e Worker | Cloudflare (plano Free) | R$ 0 |
| Site | Google Cloud Run (São Paulo) | ~R$ 0 com pouco acesso (cota gratuita mensal) |
| Banco | Neon (Free, São Paulo) | R$ 0 |
| Fotos | Cloudflare R2 (até 10 GB) | R$ 0 |

Proteções contra gasto inesperado (decisão 15 em `docs/decisoes.md`):

1. Cloud Run com no máximo 1 instância (teto de processamento).
2. Cloudflare: Bot Fight Mode, limite de acessos por IP e cache dos estáticos. O Worker gratuito tem limite de 100 mil acessos por dia: passou disso, ele para de responder até o dia seguinte, sem cobrança.
3. Avisos graduais por e-mail: a cada R$ 5 gastos no mês (R$ 5, 10, 15... até 50), mais o alerta de previsão.
4. Disjuntor: ao chegar em R$ 50 no mês, o site é fechado ao público automaticamente.

Além disso, o Django recusa visitas que não passaram pelo Worker (cabeçalho `X-Origin-Secret`), então ninguém consegue pular o Cloudflare acessando o endereço `.run.app` direto.

> Guarde todas as senhas e chaves num gerenciador de senhas. Nunca as cole em arquivos do projeto: só no painel de cada serviço ou no Secret Manager.

---

## 1. Domínio (Registro.br)

1. Registre `gustavolocks.com.br` em https://registro.br (R$ 40/ano; ative a renovação automática).
2. Deixe a configuração de DNS para o passo 2.

## 2. Cloudflare: conta e DNS

1. Crie a conta em https://dash.cloudflare.com (plano **Free**).
2. **Add a domain** → `gustavolocks.com.br` → plano Free.
3. O Cloudflare mostra dois *nameservers* (ex.: `ana.ns.cloudflare.com`). No Registro.br, em **DNS → Alterar servidores DNS**, troque pelos dois do Cloudflare.
4. Espere o Cloudflare avisar que o domínio está ativo (minutos a algumas horas).
5. Em **Security**:
   - **Bots** → ligue o **Bot Fight Mode**.
   - **WAF → Rate limiting rules** → crie uma regra: se o mesmo IP fizer mais de **30 acessos em 10 segundos**, então **Block** por 10 segundos.
6. Em **SSL/TLS** → modo **Full (strict)**.

## 3. Cloudflare R2: fotos

1. No painel do Cloudflare, **R2 Object Storage** → ative (pode pedir um cartão; dentro da faixa gratuita não há cobrança).
2. **Create bucket** → nome `gustavo-locks-fotos` → localização automática. Deixe o bucket **privado** (sem acesso público): o site gera links temporários assinados.
3. **Manage R2 API Tokens → Create API token**:
   - Permissão: **Object Read & Write**, só para o bucket `gustavo-locks-fotos`.
   - Anote o **Access Key ID**, o **Secret Access Key** e o endereço **S3** (`https://<ID-DA-CONTA>.r2.cloudflarestorage.com`).
4. Em `infra/cloudrun/env.yaml`, troque `<ID-DA-CONTA>` pelo ID real (não é segredo).
5. Opcional: em **Manage Account → Billing → Notifications**, ligue os avisos de cobrança.

## 4. Neon: banco de dados

1. Crie a conta em https://neon.com (plano Free, sem cartão).
2. **New project**:
   - Nome: `site-gustavo`
   - Postgres: **18**
   - Região: **AWS São Paulo (`aws-sa-east-1`)**: não dá para trocar depois.
3. Em **Connect**, desligue **Connection pooling** e copie a connection string. Ela tem o formato `postgresql://usuario:senha@ep-....sa-east-1.aws.neon.tech/neondb?sslmode=require`.
4. Crie as tabelas e o seu login do Admin a partir do seu PC, apontando para o Neon só nesta janela do terminal:

```powershell
$env:DATABASE_URL = "cole-aqui-a-connection-string-do-neon"
uv run python manage.py migrate
uv run python manage.py createsuperuser
Remove-Item Env:DATABASE_URL
```

- `$env:DATABASE_URL = "..."` define a variável só nesta janela (ela vale mais que a do `.env`).
- `Remove-Item Env:DATABASE_URL` apaga a variável no fim, para você não mexer no banco de produção sem querer.

## 5. Google Cloud: conta, projeto e ferramentas

1. Instale a CLI do Google Cloud e faça login:

```powershell
winget install --id Google.CloudSDK
gcloud init
```

- `gcloud init` abre o navegador para login e pergunta o projeto padrão. Crie um projeto novo, ex.: `gustavo-locks`.

2. No console (https://console.cloud.google.com), em **Faturamento**, vincule uma conta de faturamento ao projeto (pede cartão; a cota gratuita continua valendo).
3. Ative os serviços usados:

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com pubsub.googleapis.com eventarc.googleapis.com cloudfunctions.googleapis.com billingbudgets.googleapis.com
```

4. Descubra o número do projeto (usado nos próximos comandos):

```powershell
gcloud projects describe gustavo-locks --format="value(projectNumber)"
```

## 6. Orçamento: avisos graduais e disjuntor

Um único orçamento faz as duas coisas: manda os e-mails graduais e aciona o disjuntor. Os avisos são gratuitos; o valor do orçamento é só a régua.

No console: **Faturamento → Orçamentos e alertas → Criar orçamento**.

- Nome: `Avisos e disjuntor`; projeto `gustavo-locks`; período **mensal**; valor **R$ 50**.
- Limites de gasto **real**: **10%, 20%, 30%, 40%, 50%, 60%, 70%, 80%, 90% e 100%**. Cada um manda um e-mail:

  | Limite | Gasto no mês |
  | --- | --- |
  | 10% | R$ 5 |
  | 20% | R$ 10 |
  | 30% | R$ 15 |
  | 40% | R$ 20 |
  | 50% | R$ 25 |
  | 60% | R$ 30 |
  | 70% | R$ 35 |
  | 80% | R$ 40 |
  | 90% | R$ 45 |
  | 100% | R$ 50: o disjuntor fecha o site |

- Mais um limite de gasto **previsto** em **20% (R$ 10)**: avisa logo nos primeiros dias se o ritmo indicar que o mês vai passar de R$ 10, antes de o gasto acontecer.
- Notificações: e-mail para administradores de faturamento (você).
- Em **Gerenciar notificações**, marque **Conectar um tópico do Pub/Sub** e crie o tópico `orcamento-disjuntor`. É por ele que o disjuntor (passo 10) recebe o gasto do mês.

> O Google atualiza os gastos com algumas horas de atraso. Por isso o teto de 1 instância (passo 8) é a proteção imediata; os orçamentos são a segunda linha.

## 7. Segredos (Secret Manager)

No console: **Segurança → Secret Manager → Criar secret**. Crie cinco, colando o valor no campo "Valor do secret":

| Nome | Valor |
| --- | --- |
| `SECRET_KEY` | uma chave nova: `uv run python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `ORIGIN_SECRET` | outra chave nova, gerada do mesmo jeito (anote: vai também no Worker) |
| `DATABASE_URL` | a connection string do Neon |
| `R2_ACCESS_KEY_ID` | o Access Key ID do R2 |
| `R2_SECRET_ACCESS_KEY` | o Secret Access Key do R2 |

Dê ao serviço permissão de ler os segredos (troque `NUMERO` pelo número do projeto):

```powershell
gcloud projects add-iam-policy-binding gustavo-locks --member="serviceAccount:NUMERO-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

## 8. Primeiro deploy do site

Na pasta do projeto, na branch `main` atualizada:

```powershell
gcloud run deploy gustavo-locks `
  --source . `
  --region southamerica-east1 `
  --allow-unauthenticated `
  --max-instances 1 `
  --min-instances 0 `
  --cpu 1 `
  --memory 512Mi `
  --cpu-throttling `
  --concurrency 40 `
  --timeout 60 `
  --env-vars-file infra/cloudrun/env.yaml `
  --set-secrets "SECRET_KEY=SECRET_KEY:latest,ORIGIN_SECRET=ORIGIN_SECRET:latest,DATABASE_URL=DATABASE_URL:latest,R2_ACCESS_KEY_ID=R2_ACCESS_KEY_ID:latest,R2_SECRET_ACCESS_KEY=R2_SECRET_ACCESS_KEY:latest"
```

O que cada parte faz:

| Parte | O quê |
| --- | --- |
| `gcloud run deploy gustavo-locks` | Cria (ou atualiza) o serviço `gustavo-locks` no Cloud Run. |
| `--source .` | Envia a pasta; o Cloud Build monta a imagem na nuvem usando o `Dockerfile`. |
| `--region southamerica-east1` | São Paulo, perto dos visitantes e do banco no Neon. |
| `--allow-unauthenticated` | O site é público (quem filtra é o Worker + `ORIGIN_SECRET`). |
| `--max-instances 1` | **Teto de gasto**: nunca mais de uma cópia do site rodando. |
| `--min-instances 0` | Desliga quando ninguém acessa (é o que deixa o custo perto de zero). |
| `--cpu 1 --memory 512Mi` | Tamanho da máquina. |
| `--cpu-throttling` | Cobra CPU só enquanto responde a uma visita. |
| `--concurrency 40` | Até 40 visitas ao mesmo tempo na mesma cópia. |
| `--timeout 60` | Uma visita que demorar mais de 60 s é cortada. |
| `--env-vars-file` | Variáveis não secretas (`infra/cloudrun/env.yaml`). |
| `--set-secrets` | Variáveis secretas, lidas do Secret Manager. |

Na primeira vez, o `gcloud` pergunta se pode criar o repositório de imagens: responda **Y**. No fim, ele mostra o endereço `https://gustavo-locks-....run.app`. Anote: vai no Worker. Abrir esse endereço direto deve mostrar **"Acesso direto não permitido."** (é a proteção funcionando).

Limpeza automática das imagens antigas (guarda só as 2 mais recentes; evita custo de armazenamento):

```powershell
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy --location=southamerica-east1 --policy=infra/cloudrun/cleanup-policy.json --no-dry-run
```

## 9. Worker do Cloudflare: a porta de entrada

1. No painel do Cloudflare: **Workers & Pages → Create → Create Worker** → nome `gustavo-locks-proxy` → **Deploy**.
2. **Edit code**: apague o exemplo, cole o conteúdo de `infra/cloudflare-worker/worker.js` e clique **Deploy**.
3. **Settings → Variables and Secrets**:
   - `CLOUD_RUN_URL` (tipo **Text**): o endereço `.run.app` do passo 8.
   - `ORIGIN_SECRET` (tipo **Secret**): o mesmo valor do segredo `ORIGIN_SECRET` do Google.
4. **Settings → Domains & Routes → Add → Custom domain**: adicione `gustavolocks.com.br` e depois `www.gustavolocks.com.br`. O Cloudflare cria os registros de DNS sozinho.
5. Abra https://gustavolocks.com.br. O site deve aparecer, e https://gustavolocks.com.br/admin deve abrir o login.

## 10. Disjuntor

Publica a função que fecha o site quando o orçamento chega a 100% (R$ 50):

```powershell
gcloud functions deploy disjuntor `
  --gen2 `
  --runtime python313 `
  --region southamerica-east1 `
  --source infra/disjuntor `
  --entry-point handle_budget_alert `
  --trigger-topic orcamento-disjuntor `
  --max-instances 1 `
  --set-env-vars "PROJECT_ID=gustavo-locks,REGION=southamerica-east1,SERVICE=gustavo-locks"
```

Permissão para a função alterar o serviço (troque `NUMERO`):

```powershell
gcloud run services add-iam-policy-binding gustavo-locks --region=southamerica-east1 --member="serviceAccount:NUMERO-compute@developer.gserviceaccount.com" --role="roles/run.admin"
gcloud iam service-accounts add-iam-policy-binding NUMERO-compute@developer.gserviceaccount.com --member="serviceAccount:NUMERO-compute@developer.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
```

Teste sem fechar o site (simula um gasto de R$ 0,50):

```powershell
gcloud pubsub topics publish orcamento-disjuntor --message='{\"costAmount\": 0.5, \"budgetAmount\": 50}'
gcloud functions logs read disjuntor --region=southamerica-east1 --limit=5
```

O log deve mostrar "Gasto 0.5 de 50: site continua no ar."

### Se o disjuntor fechar o site

1. Veja nos orçamentos e em **Cloud Run → gustavo-locks → Métricas** o que causou o gasto.
2. O gasto continua acima do limite até o fim do mês: antes de reabrir, aumente temporariamente o valor do orçamento (senão a função fecha de novo na próxima notificação).
3. Reabra o site:

```powershell
gcloud run services update gustavo-locks --region=southamerica-east1 --ingress=all
```

## Próximos deploys

Depois que um pull request entra na `main`:

```powershell
git switch main
git pull
gcloud run deploy gustavo-locks --source . --region southamerica-east1
```

O `gcloud` reaproveita as configurações do primeiro deploy (teto, segredos, variáveis). Se o pull request tiver migrações novas, rode antes o `migrate` apontando para o Neon (passo 4). Na fase 4, esse deploy passa a ser automático.
