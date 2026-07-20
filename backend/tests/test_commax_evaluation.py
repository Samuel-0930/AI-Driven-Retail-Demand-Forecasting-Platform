from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from backend.evaluate_commax import (
    aggregate,
    aggregate_inventory_policy,
    calibration_residuals,
    classify_demand_pattern,
    conformal_bounds,
    conformal_quantile,
    forecast_model,
    metrics,
    evaluate_commax,
)


def test_classify_demand_pattern_uses_adi_and_cv_squared():
    assert classify_demand_pattern(np.ones(24)) == "Smooth"
    assert classify_demand_pattern(np.tile([1.0, 10.0], 12)) == "Erratic"
    assert classify_demand_pattern(np.tile([0.0, 1.0], 12)) == "Intermittent"
    assert classify_demand_pattern(np.tile([0.0, 1.0, 0.0, 10.0], 6)) == "Lumpy"


def test_metrics_marks_mase_unavailable_when_the_seasonal_scale_is_zero():
    result = metrics(
        actual=np.array([5.0]),
        predicted=np.array([4.0]),
        train=np.full(13, 5.0),
    )

    assert result["mase"] is None


def test_aggregate_averages_per_series_mase_without_crossing_sku_boundaries():
    first_train = np.arange(13, dtype=float)
    second_train = np.arange(100, 113, dtype=float)
    rows = [
        (np.array([12.0]), np.array([0.0]), first_train),
        (np.array([112.0]), np.array([100.0]), second_train),
    ]

    result = aggregate(rows)

    assert result["mae"] == 12.0
    assert result["wape"] == pytest.approx(19.35)
    assert result["mase"] == 1.0


def test_prophet_forecast_requests_month_start_periods():
    train = pd.DataFrame(
        {
            "period": pd.date_range("2023-01-01", periods=13, freq="MS"),
            "value": np.arange(13, dtype=float),
        }
    )
    future_dates = pd.Series(pd.date_range("2024-02-01", periods=2, freq="MS"))
    model = MagicMock()
    model.make_future_dataframe.return_value = pd.DataFrame(
        {"ds": pd.date_range("2023-01-01", periods=15, freq="MS")}
    )
    model.predict.return_value = pd.DataFrame({"yhat": np.arange(15, dtype=float)})

    with patch("backend.evaluate_commax.Prophet", return_value=model):
        result = forecast_model("prophet", train, future_dates)

    model.make_future_dataframe.assert_called_once_with(periods=2, freq="MS")
    np.testing.assert_array_equal(result, np.array([13.0, 14.0]))


def test_split_conformal_uses_the_finite_sample_higher_quantile():
    residuals = [1.0, 2.0, 3.0, 4.0, 5.0]

    assert conformal_quantile(residuals, 0.8) == 5.0
    lower, upper, radius = conformal_bounds([10.0], residuals, 0.8)

    assert radius == 5.0
    np.testing.assert_array_equal(lower, np.array([5.0]))
    np.testing.assert_array_equal(upper, np.array([15.0]))


def test_calibration_residuals_do_not_read_the_target_or_future_periods(monkeypatch):
    item = pd.DataFrame(
        {
            "period": pd.date_range("2020-01-01", periods=26, freq="MS"),
            "value": np.arange(26, dtype=float),
        }
    )
    monkeypatch.setattr(
        "backend.evaluate_commax.forecast_model",
        lambda _name, _train, future_dates: np.zeros(len(future_dates)),
    )
    baseline = calibration_residuals(item, "croston_sba", origin=20, horizon_months=2)
    changed_future = item.copy()
    changed_future.loc[20:, "value"] = 1_000_000

    np.testing.assert_array_equal(
        baseline,
        calibration_residuals(changed_future, "croston_sba", origin=20, horizon_months=2),
    )


def test_inventory_policy_reports_the_service_cost_tradeoff():
    rows = [(np.array([10.0, 4.0]), np.array([5.0, 8.0]), np.array([5.0]))]

    point = aggregate_inventory_policy(rows)
    conformal = aggregate_inventory_policy(rows, coverage=0.8)

    assert point["stockout_units"] == 5.0
    assert point["excess_units"] == 4.0
    assert point["assumed_cost"] == 29.0
    assert point["fill_rate"] == pytest.approx(64.29)
    assert conformal["stockout_units"] == 0.0
    assert conformal["excess_units"] == 9.0
    assert conformal["assumed_cost"] == 9.0


def test_evaluation_uses_fold_local_patterns_and_returns_auditable_rows(tmp_path, monkeypatch):
    periods = pd.date_range("2022-01-01", periods=20, freq="MS")
    values = [1.0] * 16 + [100.0, 1.0, 100.0, 1.0]
    frame = pd.DataFrame(
        {
            "품목코드": "sku-1",
            "품목명": "SKU 1",
            "period": periods,
            "value": values,
        }
    )
    data_path = tmp_path / "shipments.csv"
    frame.to_csv(data_path, index=False)
    monkeypatch.setattr(
        "backend.evaluate_commax.forecast_model",
        lambda _name, _train, future_dates: np.zeros(len(future_dates)),
    )

    result = evaluate_commax(data_path, horizon_months=2, folds=2, top_items=1)

    assert result["schema_version"] == 2
    assert result["selection_cutoff"] == "2023-05-01"
    assert {row["pattern_at_origin"] for row in result["fold_metrics"]} == {"Smooth", "Erratic"}
    assert len(result["fold_metrics"]) == 2
    assert result["fold_metrics"][0]["models"]["croston_sba"]["mase"] is None
    assert result["fold_metrics"][1]["models"]["croston_sba"]["mase"] is not None
    interval = result["interval_metrics"]["croston_sba"]
    assert set(interval) == {"80", "90"}
    assert interval["80"]["evaluation_points"] == 4
    assert 0 <= interval["90"]["empirical_coverage"] <= 100
    assert interval["90"]["mean_interval_width"] >= interval["80"]["mean_interval_width"]
    policy = result["inventory_policy_metrics"]
    assert policy["assumptions"]["cost_ratio"] == "5:1"
    assert policy["models"]["croston_sba"]["80"]["evaluation_points"] == 4
