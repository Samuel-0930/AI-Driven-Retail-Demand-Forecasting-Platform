"""Portfolio evaluation for the top-volume Commax monthly shipment items."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet


HORIZON_MONTHS = 6
FOLDS = 3
SEASONAL_PERIOD = 12
TOP_ITEMS = 20


def metrics(actual: np.ndarray, predicted: np.ndarray, train: np.ndarray) -> dict[str, float]:
    errors = np.abs(actual - predicted)
    mae = float(errors.mean())
    wape = float(errors.sum() / np.abs(actual).sum() * 100) if np.abs(actual).sum() else 0.0
    scale = np.abs(train[SEASONAL_PERIOD:] - train[:-SEASONAL_PERIOD]).mean()
    mase = float(mae / scale) if scale else 0.0
    return {"mae": round(mae, 2), "wape": round(wape, 2), "mase": round(mase, 3)}


def evaluate_commax(data_path: str | Path) -> dict:
    df = pd.read_csv(data_path, usecols=["품목코드", "품목명", "period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    top_codes = df.groupby("품목코드")["value"].sum().nlargest(TOP_ITEMS).index
    results = []
    prophet_actuals: list[float] = []
    prophet_predictions: list[float] = []
    naive_actuals: list[float] = []
    naive_predictions: list[float] = []

    for code in top_codes:
        item = df[df["품목코드"] == code].sort_values("period").reset_index(drop=True)
        fold_metrics = []
        for fold, origin in enumerate(range(len(item) - FOLDS * HORIZON_MONTHS, len(item), HORIZON_MONTHS), start=1):
            train, test = item.iloc[:origin], item.iloc[origin:origin + HORIZON_MONTHS]
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(train.rename(columns={"period": "ds", "value": "y"})[["ds", "y"]])
            prediction = model.predict(model.make_future_dataframe(periods=len(test))).tail(len(test))["yhat"].to_numpy()
            naive = np.resize(train["value"].to_numpy()[-SEASONAL_PERIOD:], len(test))
            actual = test["value"].to_numpy()
            fold_metrics.append({"fold": fold, "prophet": metrics(actual, prediction, train["value"].to_numpy()), "seasonal_naive": metrics(actual, naive, train["value"].to_numpy())})
            prophet_actuals.extend(actual); prophet_predictions.extend(prediction)
            naive_actuals.extend(actual); naive_predictions.extend(naive)
        results.append({"item_code": code, "item_name": item["품목명"].iloc[0], "total_shipments": float(item["value"].sum()), "folds": fold_metrics})

    train_scale = df[df["품목코드"].isin(top_codes)].sort_values(["품목코드", "period"])["value"].to_numpy()
    return {
        "dataset_type": "commax_monthly_shipments",
        "scope": "Top 20 items by cumulative shipments",
        "period": f"{df['period'].min().date()} to {df['period'].max().date()}",
        "evaluation_method": "Three rolling 6-month origins; Prophet uses no external variables. Baseline repeats the same month from the previous year.",
        "items": len(results), "horizon_months": HORIZON_MONTHS, "folds": FOLDS,
        "prophet": metrics(np.asarray(prophet_actuals), np.asarray(prophet_predictions), train_scale),
        "seasonal_naive": metrics(np.asarray(naive_actuals), np.asarray(naive_predictions), train_scale),
        "item_results": results,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = evaluate_commax(root / "data/raw/Final_KR_modeling_long_with_external_data.csv")
    output = root / "data/processed/commax_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved Commax evaluation to {output}")
    print(result["prophet"], result["seasonal_naive"])


if __name__ == "__main__":
    main()
