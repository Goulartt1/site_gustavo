import base64
import json

from logic import parse_budget_message, should_shut_down


def encode(payload):
    return base64.b64encode(json.dumps(payload).encode())


def test_parse_budget_message_decodes_pubsub_data():
    data = encode({"costAmount": 12.5, "budgetAmount": 50.0, "currencyCode": "BRL"})

    assert parse_budget_message(data)["costAmount"] == 12.5


def test_below_budget_keeps_site_online():
    assert not should_shut_down({"costAmount": 49.99, "budgetAmount": 50.0})


def test_reaching_budget_shuts_down():
    assert should_shut_down({"costAmount": 50.0, "budgetAmount": 50.0})
    assert should_shut_down({"costAmount": 73.1, "budgetAmount": 50.0})


def test_missing_budget_never_shuts_down():
    assert not should_shut_down({"costAmount": 10.0})
