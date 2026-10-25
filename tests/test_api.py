import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.app.main import FEATURES, MODEL_PATH, app
from src.train.train import train


@pytest.fixture(scope="session", autouse=True)
def trained_model():
    train()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def customer():
    return {
        "tenure_months": 5,
        "monthly_fee": 89.9,
        "contract": "month-to-month",
        "internet_service": "fiber",
        "support_calls": 3,
    }


def test_health_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_loads_and_predicts(customer):
    model = joblib.load(MODEL_PATH)
    frame = pd.DataFrame([customer], columns=FEATURES)
    probabilities = model.predict_proba(frame)
    assert probabilities.shape == (1, 2)
    assert probabilities.sum() == pytest.approx(1.0)


def test_prediction_contract(client, customer):
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    assert set(response.json()) == {"churn_probability"}
    assert isinstance(response.json()["churn_probability"], float)
    assert 0 <= response.json()["churn_probability"] <= 1


@pytest.mark.parametrize("field", FEATURES)
def test_missing_required_field(client, customer, field):
    del customer[field]
    assert client.post("/predict", json=customer).status_code == 422


@pytest.mark.parametrize("field,value", [
    ("tenure_months", -1), ("tenure_months", "5"),
    ("tenure_months", 1.5), ("tenure_months", True),
    ("monthly_fee", -1), ("monthly_fee", "89.9"),
    ("contract", "unknown"), ("internet_service", "satellite"),
    ("support_calls", -1), ("support_calls", None),
])
def test_invalid_schema(client, customer, field, value):
    customer[field] = value
    assert client.post("/predict", json=customer).status_code == 422


def test_unexpected_field(client, customer):
    customer["customer_id"] = 1
    assert client.post("/predict", json=customer).status_code == 422


def test_zero_edge_case(client, customer):
    customer.update(tenure_months=0, monthly_fee=0.0, support_calls=0)
    response = client.post("/predict", json=customer)
    assert response.status_code == 200
    assert 0 <= response.json()["churn_probability"] <= 1


def test_deterministic_prediction(client, customer):
    first = client.post("/predict", json=customer)
    second = client.post("/predict", json=customer)
    model = joblib.load(MODEL_PATH)
    expected = round(float(model.predict_proba(pd.DataFrame([customer], columns=FEATURES))[0, 1]), 3)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"churn_probability": expected}
