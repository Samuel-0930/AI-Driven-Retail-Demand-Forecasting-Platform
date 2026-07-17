from fastapi.testclient import TestClient
from backend.main import app
from backend.app.api import routes
from backend.app.services.prediction_service import ModelNotFoundError

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Demand Signal API"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_predict_rejects_invalid_forecast_window():
    response = client.post("/api/v1/predict", json={
        "store_id": 1,
        "product_id": 1,
        "start_date": "2025-02-01",
        "end_date": "2025-01-01",
    })

    assert response.status_code == 422

def test_predict_rejects_horizon_longer_than_90_days():
    response = client.post("/api/v1/predict", json={
        "store_id": 1,
        "product_id": 1,
        "start_date": "2025-01-01",
        "end_date": "2025-04-02",
    })

def test_predict_hides_internal_errors(monkeypatch):
    def raise_internal_error(_):
        raise RuntimeError("database password should never be exposed")

    monkeypatch.setattr(routes.service, "predict", raise_internal_error)
    response = client.post("/api/v1/predict", json={
        "store_id": 1,
        "product_id": 1,
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
    })

    assert response.status_code == 500
    assert response.json() == {"detail": "Prediction is temporarily unavailable"}

def test_predict_returns_404_when_model_is_missing(monkeypatch):
    def raise_model_not_found(_):
        raise ModelNotFoundError

    monkeypatch.setattr(routes.service, "predict", raise_model_not_found)
    response = client.post("/api/v1/predict", json={
        "store_id": 1,
        "product_id": 1,
        "start_date": "2025-01-01",
        "end_date": "2025-01-02",
    })

    assert response.status_code == 404


def test_evaluation_returns_404_when_results_are_missing(monkeypatch):
    def raise_evaluation_not_found(_, __):
        from backend.app.services.prediction_service import EvaluationNotFoundError
        raise EvaluationNotFoundError

    monkeypatch.setattr(routes.service, "get_evaluation", raise_evaluation_not_found)
    response = client.get("/api/v1/evaluation?store_id=1&product_id=1")

    assert response.status_code == 404
    assert "No evaluation is available" in response.json()["detail"]
