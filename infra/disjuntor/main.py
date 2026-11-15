"""Disjuntor de gastos (Cloud Run function).

O orçamento do projeto no Google Cloud publica o gasto do mês num tópico do
Pub/Sub várias vezes ao dia. Esta função recebe cada publicação e, quando o
gasto chega ao valor do orçamento (R$ 50), muda a entrada do serviço do Cloud
Run para "somente interna": o site para de responder à internet e o custo
para de crescer. Nada é apagado. Como reabrir: docs/deploy.md.

Variáveis de ambiente: PROJECT_ID, REGION, SERVICE.
"""

import os

import functions_framework
from google.cloud import run_v2
from logic import parse_budget_message, should_shut_down


@functions_framework.cloud_event
def handle_budget_alert(cloud_event):
    notification = parse_budget_message(cloud_event.data["message"]["data"])
    cost = notification.get("costAmount")
    budget = notification.get("budgetAmount")

    if not should_shut_down(notification):
        print(f"Gasto {cost} de {budget}: site continua no ar.")
        return

    client = run_v2.ServicesClient()
    name = (
        f"projects/{os.environ['PROJECT_ID']}/locations/{os.environ['REGION']}"
        f"/services/{os.environ['SERVICE']}"
    )
    service = client.get_service(name=name)
    internal = run_v2.IngressTraffic.INGRESS_TRAFFIC_INTERNAL_ONLY
    if service.ingress == internal:
        print("Site já estava fechado ao público.")
        return

    service.ingress = internal
    client.update_service(service=service).result()
    print(f"Orçamento atingido ({cost} de {budget}): site fechado ao público.")
