"""Pattern-aware benchmark for the top-volume Commax monthly shipment items."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet


HORIZON_MONTHS = 6
FOLDS = 3
SEASONAL_PERIOD = 12
TOP_ITEMS = 20
SBA_ALPHAS = (0.05, 0.1, 0.2, 0.3)
TSB_ALPHAS = (0.05, 0.1, 0.2, 0.3)


def metrics(actual: np.ndarray, predicted: np.ndarray, train: np.ndarray) -> dict[str, float]:
    errors = np.abs(actual - predicted)
    mae = float(errors.mean())
    wape = float(errors.sum() / np.abs(actual).sum() * 100) if np.abs(actual).sum() else 0.0
    scale = np.abs(train[SEASONAL_PERIOD:] - train[:-SEASONAL_PERIOD]).mean()
    mase = float(mae / scale) if scale else 0.0
    return {"mae": round(mae, 2), "wape": round(wape, 2), "mase": round(mase, 3)}


def sba_forecast(train: np.ndarray, horizon: int, alpha: float) -> np.ndarray:
    nonzero = np.flatnonzero(train > 0)
    if len(nonzero) == 0:
        return np.zeros(horizon)
    demand = float(train[nonzero[0]])
    interval = float(nonzero[0] + 1)
    elapsed = 1
    for value in train[nonzero[0] + 1:]:
        if value > 0:
            demand += alpha * (value - demand)
            interval += alpha * (elapsed - interval)
            elapsed = 1
        else:
            elapsed += 1
    return np.full(horizon, (1 - alpha / 2) * demand / max(interval, 1))


def best_sba_forecast(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) <= SEASONAL_PERIOD:
        return sba_forecast(train, horizon, 0.1)
    actual = train[SEASONAL_PERIOD:]
    candidates = []
    for alpha in SBA_ALPHAS:
        one_step = np.array([sba_forecast(train[:index], 1, alpha)[0] for index in range(SEASONAL_PERIOD, len(train))])
        candidates.append((np.abs(actual - one_step).mean(), alpha))
    return sba_forecast(train, horizon, min(candidates)[1])


def tsb_forecast(train: np.ndarray, horizon: int, alpha_demand: float, alpha_probability: float) -> np.ndarray:
    nonzero = np.flatnonzero(train > 0)
    if len(nonzero) == 0:
        return np.zeros(horizon)
    demand = float(train[nonzero[0]])
    probability = float(np.mean(train[:nonzero[0] + 1] > 0))
    for value in train[nonzero[0] + 1:]:
        occurrence = float(value > 0)
        probability += alpha_probability * (occurrence - probability)
        if occurrence:
            demand += alpha_demand * (value - demand)
    return np.full(horizon, demand * probability)


def best_tsb_forecast(train: np.ndarray, horizon: int) -> np.ndarray:
    if len(train) <= SEASONAL_PERIOD:
        return tsb_forecast(train, horizon, 0.1, 0.1)
    actual = train[SEASONAL_PERIOD:]
    candidates = []
    for alpha_demand in TSB_ALPHAS:
        for alpha_probability in TSB_ALPHAS:
            one_step = np.array([tsb_forecast(train[:index], 1, alpha_demand, alpha_probability)[0] for index in range(SEASONAL_PERIOD, len(train))])
            candidates.append((np.abs(actual - one_step).mean(), alpha_demand, alpha_probability))
    _, alpha_demand, alpha_probability = min(candidates)
    return tsb_forecast(train, horizon, alpha_demand, alpha_probability)


def seasonal_sba_forecast(train: pd.DataFrame, future_dates: pd.Series) -> np.ndarray:
    base = best_sba_forecast(train["value"].to_numpy(), len(future_dates))
    monthly_mean = train.groupby(train["period"].dt.month)["value"].mean()
    overall_mean = train["value"].mean()
    indices = (monthly_mean / overall_mean).clip(lower=0.25, upper=4.0) if overall_mean else monthly_mean * 0 + 1
    multiplier = future_dates.dt.month.map(indices).fillna(1.0).to_numpy()
    return base * multiplier


def aggregate(model_rows: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[str, float]:
    actual = np.concatenate([row[0] for row in model_rows])
    prediction = np.concatenate([row[1] for row in model_rows])
    train = np.concatenate([row[2] for row in model_rows])
    return metrics(actual, prediction, train)


def evaluate_commax(data_path: str | Path) -> dict:
    df = pd.read_csv(data_path, usecols=["품목코드", "품목명", "Pattern", "period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    top_codes = df.groupby("품목코드")["value"].sum().nlargest(TOP_ITEMS).index
    by_pattern: dict[str, dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]]] = {}

    for code in top_codes:
        item = df[df["품목코드"] == code].sort_values("period").reset_index(drop=True)
        pattern = item["Pattern"].iloc[0]
        by_pattern.setdefault(pattern, {"seasonal_naive": [], "croston_sba": [], "seasonal_croston_sba": [], "tsb": [], "prophet": []})
        for origin in range(len(item) - FOLDS * HORIZON_MONTHS, len(item), HORIZON_MONTHS):
            train, test = item.iloc[:origin], item.iloc[origin:origin + HORIZON_MONTHS]
            train_values, actual = train["value"].to_numpy(), test["value"].to_numpy()
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            model.fit(train.rename(columns={"period": "ds", "value": "y"})[["ds", "y"]])
            prophet = model.predict(model.make_future_dataframe(periods=len(test))).tail(len(test))["yhat"].to_numpy()
            seasonal_naive = np.resize(train_values[-SEASONAL_PERIOD:], len(test))
            croston_sba = best_sba_forecast(train_values, len(test))
            seasonal_croston_sba = seasonal_sba_forecast(train, test["period"])
            tsb = best_tsb_forecast(train_values, len(test))
            for name, prediction in (("seasonal_naive", seasonal_naive), ("croston_sba", croston_sba), ("seasonal_croston_sba", seasonal_croston_sba), ("tsb", tsb), ("prophet", prophet)):
                by_pattern[pattern][name].append((actual, prediction, train_values))

    pattern_results = []
    all_models = {"seasonal_naive": [], "croston_sba": [], "seasonal_croston_sba": [], "tsb": [], "prophet": []}
    for pattern, model_rows in sorted(by_pattern.items()):
        model_metrics = {name: aggregate(rows) for name, rows in model_rows.items()}
        champion = min(model_metrics, key=lambda name: model_metrics[name]["wape"])
        pattern_results.append({"pattern": pattern, "items": len({code for code in top_codes if df[df['품목코드'] == code]['Pattern'].iloc[0] == pattern}), "models": model_metrics, "champion": champion})
        for name, rows in model_rows.items():
            all_models[name].extend(rows)

    model_metrics = {name: aggregate(rows) for name, rows in all_models.items()}
    return {
        "dataset_type": "commax_monthly_shipments",
        "scope": "Top 20 items by cumulative shipments",
        "period": f"{df['period'].min().date()} to {df['period'].max().date()}",
        "evaluation_method": "Three rolling 6-month origins. Prophet has no external variables; seasonal-naive repeats prior-year month; Croston/SBA and TSB tune parameters using training history only.",
        "items": len(top_codes), "horizon_months": HORIZON_MONTHS, "folds": FOLDS,
        "models": model_metrics,
        "pattern_results": pattern_results,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = evaluate_commax(root / "data/raw/Final_KR_modeling_long_with_external_data.csv")
    output = root / "data/processed/commax_evaluation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved Commax benchmark to {output}")
    for result_by_pattern in result["pattern_results"]:
        print(result_by_pattern["pattern"], result_by_pattern["champion"], result_by_pattern["models"])


if __name__ == "__main__":
    main()
