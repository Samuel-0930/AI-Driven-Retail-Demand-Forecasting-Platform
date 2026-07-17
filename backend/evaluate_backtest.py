"""Rolling-origin evaluation for the reproducible synthetic demo data."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet


HORIZON_DAYS = 30
FOLDS = 3
SEASONAL_PERIOD = 7


def _metric_summary(actual: np.ndarray, predicted: np.ndarray, train_values: np.ndarray) -> dict[str, float]:
    absolute_errors = np.abs(actual - predicted)
    mae = float(np.mean(absolute_errors))
    denominator = float(np.sum(np.abs(actual)))
    wape = float(np.sum(absolute_errors) / denominator * 100) if denominator else 0.0
    scale = float(np.mean(np.abs(train_values[SEASONAL_PERIOD:] - train_values[:-SEASONAL_PERIOD])))
    mase = float(mae / scale) if scale else 0.0
    return {"mae": round(mae, 2), "wape": round(wape, 2), "mase": round(mase, 3)}


def _fit_prophet(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
    model.add_regressor("is_promo")
    model.fit(train_df[["ds", "y", "is_promo"]])
    future = model.make_future_dataframe(periods=len(test_df))
    future["is_promo"] = pd.concat([train_df["is_promo"], test_df["is_promo"]]).to_numpy()
    return model.predict(future).tail(len(test_df))["yhat"].to_numpy()


def _seasonal_naive(train_values: np.ndarray, horizon: int) -> np.ndarray:
    history = list(train_values)
    predictions = []
    for _ in range(horizon):
        prediction = history[-SEASONAL_PERIOD]
        predictions.append(prediction)
        history.append(prediction)
    return np.asarray(predictions)


def evaluate_rolling_backtest(data_path: str | Path, store_id: int, product_id: int) -> dict:
    """Compare Prophet with a weekly seasonal-naive baseline over three 30-day origins."""
    df = pd.read_csv(data_path, parse_dates=["date"])
    item_df = df[(df["store_id"] == store_id) & (df["product_id"] == product_id)].copy()
    item_df = item_df.sort_values("date").rename(columns={"date": "ds", "sales": "y"})
    minimum_rows = FOLDS * HORIZON_DAYS + SEASONAL_PERIOD + 1
    if len(item_df) < minimum_rows:
        raise ValueError(f"At least {minimum_rows} rows are required for rolling evaluation")

    fold_results = []
    prophet_actuals: list[float] = []
    prophet_predictions: list[float] = []
    naive_actuals: list[float] = []
    naive_predictions: list[float] = []

    first_origin = len(item_df) - FOLDS * HORIZON_DAYS
    for fold_index, origin in enumerate(range(first_origin, len(item_df), HORIZON_DAYS), start=1):
        train_df = item_df.iloc[:origin].copy()
        test_df = item_df.iloc[origin:origin + HORIZON_DAYS].copy()
        actuals = test_df["y"].to_numpy(dtype=float)
        prophet_predictions_for_fold = _fit_prophet(train_df, test_df)
        naive_predictions_for_fold = _seasonal_naive(train_df["y"].to_numpy(dtype=float), len(test_df))

        fold_results.append(
            {
                "fold": fold_index,
                "train_end": train_df["ds"].iloc[-1].date().isoformat(),
                "test_start": test_df["ds"].iloc[0].date().isoformat(),
                "test_end": test_df["ds"].iloc[-1].date().isoformat(),
                "prophet": _metric_summary(actuals, prophet_predictions_for_fold, train_df["y"].to_numpy(dtype=float)),
                "seasonal_naive": _metric_summary(actuals, naive_predictions_for_fold, train_df["y"].to_numpy(dtype=float)),
            }
        )
        prophet_actuals.extend(actuals)
        prophet_predictions.extend(prophet_predictions_for_fold)
        naive_actuals.extend(actuals)
        naive_predictions.extend(naive_predictions_for_fold)
    prophet_summary = _metric_summary(
        np.asarray(prophet_actuals),
        np.asarray(prophet_predictions),
        item_df["y"].to_numpy(dtype=float),
    )
    naive_summary = _metric_summary(
        np.asarray(naive_actuals),
        np.asarray(naive_predictions),
        item_df["y"].to_numpy(dtype=float),
    )
    prophet_summary["mase"] = round(float(np.mean([fold["prophet"]["mase"] for fold in fold_results])), 3)
    naive_summary["mase"] = round(float(np.mean([fold["seasonal_naive"]["mase"] for fold in fold_results])), 3)

    return {
        "store_id": store_id,
        "product_id": product_id,
        "dataset_type": "synthetic_demo",
        "evaluation_method": "Three rolling 30-day origins; Prophet uses observed holdout promotion values.",
        "horizon_days": HORIZON_DAYS,
        "folds": FOLDS,
        "prophet": prophet_summary,
        "seasonal_naive": naive_summary,
        "fold_results": fold_results,
    }


def evaluation_path(data_path: str | Path, store_id: int, product_id: int) -> Path:
    return Path(data_path).resolve().parent.parent / "processed" / f"evaluation_store_{store_id}_product_{product_id}.json"


def evaluate_and_save(data_path: str | Path, store_id: int, product_id: int) -> dict:
    result = evaluate_rolling_backtest(data_path, store_id, product_id)
    output_path = evaluation_path(data_path, store_id, product_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved rolling backtest results to {output_path}")
    return result
