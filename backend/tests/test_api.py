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


def test_public_commax_dashboard_data_is_available():
    evaluation = client.get("/api/v1/commax/evaluation")
    items = client.get("/api/v1/commax/items")

    assert evaluation.status_code == 200
    artifact = evaluation.json()
    assert artifact["schema_version"] == 2
    assert artifact["items"] == 20
    assert len(artifact["item_manifest"]) == 20
    assert len(artifact["fold_metrics"]) == 60
    assert "interval_metrics" in artifact
    assert artifact["public_data_fingerprint"]
    assert items.status_code == 200
    assert len(items.json()) == 20


def test_commax_backtest_includes_interval_and_risk_context():
    response = client.get("/api/v1/commax/backtest?item_code=SDC000036AXX&horizon_months=6&interval_level=0.9")

    assert response.status_code == 200
    result = response.json()
    assert result["interval_level"] == 90
    assert result["interval_method"] == "split_conformal_absolute_residuals"
    assert result["calibration_residuals"] == 18
    assert result["demand_variability_risk"] in {"low", "medium", "high"}
    assert 0 <= result["interval_coverage"] <= 100
    assert result["planning_upper_total"] >= result["forecast_total"]
    assert all(point["lower_bound"] <= point["forecast"] <= point["upper_bound"] for point in result["points"])


def test_commax_inventory_plan_recommends_order_from_user_inputs():
    response = client.get(
        "/api/v1/commax/inventory-plan?item_code=SDC000036AXX&on_hand_inventory=1000&incoming_inventory=500&lead_time_months=2&service_level=0.9"
    )

    assert response.status_code == 200
    result = response.json()
    assert result["service_level"] == 90
    assert result["available_inventory"] == 1500
    assert result["planning_demand"] >= result["forecast_demand"]
    assert result["recommended_order"] == result["planning_demand"] - result["available_inventory"]
    assert result["inventory_risk"] in {"low", "medium", "high"}

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

    assert response.status_code == 422

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
