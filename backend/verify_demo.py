"""Verify that a bootstrapped synthetic demo can serve one prediction end to end."""

from fastapi.testclient import TestClient

from backend.main import app


def main() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={
            "store_id": 1,
            "product_id": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-07",
            "is_promo": False,
        },
    )
    response.raise_for_status()
    payload = response.json()
    if len(payload["predictions"]) != 7:
        raise AssertionError("Expected one forecast for each requested day")

    evaluation = client.get("/api/v1/evaluation?store_id=1&product_id=1")
    evaluation.raise_for_status()
    if evaluation.json()["folds"] != 3:
        raise AssertionError("Expected the three-fold demo evaluation artifact")
    print("Synthetic demo smoke check passed: 7 predictions and a three-fold evaluation are available.")


if __name__ == "__main__":
    main()
