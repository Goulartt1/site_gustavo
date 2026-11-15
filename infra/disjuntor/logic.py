"""Regra do disjuntor, separada do Google Cloud para poder ser testada."""

import base64
import json


def parse_budget_message(encoded_data):
    """Decodifica a notificação de orçamento que chega pelo Pub/Sub (base64 + JSON)."""
    return json.loads(base64.b64decode(encoded_data))


def should_shut_down(notification):
    """True quando o gasto do mês chegou ao valor do orçamento do disjuntor."""
    cost = float(notification.get("costAmount", 0))
    budget = float(notification.get("budgetAmount", 0))
    return budget > 0 and cost >= budget
