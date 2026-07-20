"""Leakage-safe benchmark for top-volume monthly COMMAX shipment items."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from prophet import Prophet


HORIZON_MONTHS = 6
FOLDS = 3
SEASONAL_PERIOD = 12
TOP_ITEMS = 20
MONTHLY_FREQ = "MS"
SBA_ALPHAS = (0.05, 0.1, 0.2, 0.3)
TSB_ALPHAS = (0.05, 0.1, 0.2, 0.3)
MODEL_NAMES = (
    "seasonal_naive",
    "croston_sba",
    "seasonal_croston_sba",
    "tsb",
    "prophet",
)
INTERVAL_LEVELS = (0.8, 0.9)
CALIBRATION_ORIGINS = 3


@dataclass(frozen=True)
class PatternStats:
    label: str
    adi: float | None
    cv2: float | None
    periods: int
    nonzero_periods: int


def demand_pattern_stats(values: np.ndarray) -> PatternStats:
    """Classify demand using only the values available at one forecast origin."""
    values = np.asarray(values, dtype=float)
    positive = values[values > 0]
    if len(positive) == 0:
        return PatternStats("AllZero", None, None, len(values), 0)

    adi = len(values) / len(positive)
    if len(positive) < 2 or np.isclose(positive.mean(), 0):
        return PatternStats("InsufficientHistory", adi, None, len(values), len(positive))

    cv2 = float((positive.std(ddof=1) / positive.mean()) ** 2)
    if adi < 1.32 and cv2 < 0.49:
        label = "Smooth"
    elif adi < 1.32:
        label = "Erratic"
    elif cv2 < 0.49:
        label = "Intermittent"
    else:
        label = "Lumpy"
    return PatternStats(label, round(float(adi), 4), round(cv2, 4), len(values), len(positive))


def classify_demand_pattern(values: np.ndarray) -> str:
    return demand_pattern_stats(values).label


def metrics(actual: np.ndarray, predicted: np.ndarray, train: np.ndarray) -> dict[str, float | None]:
    """Return row-level metrics without treating an undefined MASE as zero."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    train = np.asarray(train, dtype=float)
    errors = np.abs(actual - predicted)
    mae = float(errors.mean())
    wape = float(errors.sum() / np.abs(actual).sum() * 100) if np.abs(actual).sum() else 0.0
    seasonal_differences = np.abs(train[SEASONAL_PERIOD:] - train[:-SEASONAL_PERIOD])
    scale = float(seasonal_differences.mean()) if len(seasonal_differences) else 0.0
    mase = float(mae / scale) if scale > 0 else None
    return {"mae": round(mae, 2), "wape": round(wape, 2), "mase": round(mase, 3) if mase is not None else None}


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


def prophet_forecast(train: pd.DataFrame, horizon: int) -> np.ndarray:
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    prophet_train = train.rename(columns={"period": "ds", "value": "y"})[["ds", "y"]]
    model.fit(prophet_train)
    future = model.make_future_dataframe(periods=horizon, freq=MONTHLY_FREQ)
    return model.predict(future).tail(horizon)["yhat"].to_numpy()


def forecast_model(model_name: str, train: pd.DataFrame, future_dates: pd.Series) -> np.ndarray:
    """Produce a monthly forecast through the same implementation used by evaluation and API."""
    horizon = len(future_dates)
    values = train["value"].to_numpy()
    if model_name == "croston_sba":
        return best_sba_forecast(values, horizon)
    if model_name == "seasonal_croston_sba":
        return seasonal_sba_forecast(train, future_dates)
    if model_name == "tsb":
        return best_tsb_forecast(values, horizon)
    if model_name == "seasonal_naive":
        return np.resize(values[-SEASONAL_PERIOD:], horizon)
    if model_name == "prophet":
        return prophet_forecast(train, horizon)
    raise ValueError(f"Unknown model: {model_name}")


def conformal_quantile(absolute_residuals: Sequence[float], coverage: float) -> float:
    """Finite-sample split-conformal radius for a two-sided prediction interval."""
    if not 0 < coverage < 1:
        raise ValueError("coverage must be between 0 and 1")
    residuals = np.sort(np.asarray(absolute_residuals, dtype=float))
    if len(residuals) == 0:
        raise ValueError("at least one calibration residual is required")
    rank = min(int(np.ceil((len(residuals) + 1) * coverage)), len(residuals))
    return float(residuals[rank - 1])


def conformal_bounds(
    predictions: Sequence[float], absolute_residuals: Sequence[float], coverage: float
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return non-negative split-conformal bounds and their shared residual radius."""
    radius = conformal_quantile(absolute_residuals, coverage)
    prediction = np.maximum(0, np.asarray(predictions, dtype=float))
    return np.maximum(0, prediction - radius), prediction + radius, radius


def calibration_residuals(
    item: pd.DataFrame,
    model_name: str,
    origin: int,
    horizon_months: int,
    calibration_origins: int = CALIBRATION_ORIGINS,
) -> np.ndarray:
    """Use only origins strictly before ``origin`` to calibrate its forecast interval."""
    residuals: list[float] = []
    first_origin = origin - calibration_origins * horizon_months
    for calibration_origin in range(first_origin, origin, horizon_months):
        train = item.iloc[:calibration_origin]
        test = item.iloc[calibration_origin:calibration_origin + horizon_months]
        if len(train) <= SEASONAL_PERIOD or len(test) != horizon_months:
            continue
        prediction = forecast_model(model_name, train, test["period"])
        residuals.extend(
            abs(float(actual) - max(0, float(predicted)))
            for actual, predicted in zip(test["value"], prediction)
        )
    return np.asarray(residuals, dtype=float)


def aggregate_intervals(
    interval_rows: list[tuple[np.ndarray, np.ndarray, np.ndarray]], coverage: float
) -> dict[str, float | int]:
    """Evaluate coverage and width for intervals calibrated independently at each origin."""
    covered = 0
    points = 0
    widths: list[float] = []
    calibration_counts: list[int] = []
    for actual, prediction, residuals in interval_rows:
        lower, upper, _ = conformal_bounds(prediction, residuals, coverage)
        covered += int(np.sum((actual >= lower) & (actual <= upper)))
        points += len(actual)
        widths.extend((upper - lower).tolist())
        calibration_counts.append(len(residuals))
    return {
        "nominal_coverage": round(coverage * 100),
        "empirical_coverage": round(covered / points * 100, 2) if points else 0.0,
        "mean_interval_width": round(float(np.mean(widths)), 2) if widths else 0.0,
        "evaluation_points": points,
        "calibration_residuals_min": min(calibration_counts) if calibration_counts else 0,
        "calibration_residuals_max": max(calibration_counts) if calibration_counts else 0,
    }


def aggregate(model_rows: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[str, float | int | None]:
    """Aggregate MAE/WAPE globally and MASE as a macro average over valid SKU-fold rows."""
    actual = np.concatenate([row[0] for row in model_rows])
    prediction = np.concatenate([row[1] for row in model_rows])
    errors = np.abs(actual - prediction)
    row_metrics = [metrics(*row) for row in model_rows]
    valid_mase = [result["mase"] for result in row_metrics if result["mase"] is not None]
    return {
        "mae": round(float(errors.mean()), 2),
        "wape": round(float(errors.sum() / np.abs(actual).sum() * 100), 2) if np.abs(actual).sum() else 0.0,
        "mase": round(float(np.mean(valid_mase)), 3) if valid_mase else None,
        "mase_valid_rows": len(valid_mase),
        "mase_excluded_rows": len(model_rows) - len(valid_mase),
    }


def _evaluation_start(df: pd.DataFrame, required_periods: int) -> pd.Timestamp:
    periods = df["period"].drop_duplicates().sort_values().to_list()
    if len(periods) <= required_periods:
        raise ValueError("The dataset does not contain enough monthly periods for the requested folds.")
    return pd.Timestamp(periods[-required_periods])


def _top_item_codes(df: pd.DataFrame, evaluation_start: pd.Timestamp, top_items: int) -> list[str]:
    training_only = df[df["period"] < evaluation_start]
    return training_only.groupby("품목코드")["value"].sum().nlargest(top_items).index.to_list()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _code_revision(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _working_tree_is_dirty(root: Path) -> bool | None:
    try:
        return subprocess.run(
            ["git", "diff", "--quiet", "--", "backend/evaluate_commax.py"],
            cwd=root,
            check=False,
        ).returncode != 0
    except OSError:
        return None


def evaluate_commax(
    data_path: str | Path,
    *,
    horizon_months: int = HORIZON_MONTHS,
    folds: int = FOLDS,
    top_items: int = TOP_ITEMS,
) -> dict:
    data_path = Path(data_path)
    df = pd.read_csv(data_path, usecols=["품목코드", "품목명", "period", "value"])
    df["period"] = pd.to_datetime(df["period"])
    evaluation_start = _evaluation_start(df, folds * horizon_months)
    top_codes = _top_item_codes(df, evaluation_start, top_items)
    by_pattern: dict[str, dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]]] = {}
    pattern_codes: dict[str, set[str]] = {}
    all_models = {name: [] for name in MODEL_NAMES}
    all_intervals: dict[str, list[tuple[np.ndarray, np.ndarray, np.ndarray]]] = {name: [] for name in MODEL_NAMES}
    fold_metrics: list[dict] = []
    skipped_pattern_rows = 0
    item_manifest = []

    for code in top_codes:
        item = df[df["품목코드"] == code].sort_values("period").reset_index(drop=True)
        item_manifest.append(
            {
                "item_code": code,
                "item_name": item["품목명"].iloc[0],
                "serving_pattern": classify_demand_pattern(item["value"].to_numpy()),
            }
        )
        for fold, origin in enumerate(
            range(len(item) - folds * horizon_months, len(item), horizon_months),
            start=1,
        ):
            train, test = item.iloc[:origin].copy(), item.iloc[origin:origin + horizon_months].copy()
            train_values, actual = train["value"].to_numpy(), test["value"].to_numpy()
            pattern = classify_demand_pattern(train_values)
            if pattern in {"AllZero", "InsufficientHistory"}:
                skipped_pattern_rows += 1
                continue
            by_pattern.setdefault(pattern, {name: [] for name in MODEL_NAMES})
            pattern_codes.setdefault(pattern, set()).add(code)
            row_models = {}
            for name in MODEL_NAMES:
                prediction = forecast_model(name, train, test["period"])
                row = (actual, prediction, train_values)
                by_pattern[pattern][name].append(row)
                all_models[name].append(row)
                residuals = calibration_residuals(item, name, origin, horizon_months)
                if len(residuals):
                    all_intervals[name].append((actual, prediction, residuals))
                row_models[name] = metrics(*row)
            fold_metrics.append(
                {
                    "item_code": code,
                    "fold": fold,
                    "train_start": train["period"].iloc[0].date().isoformat(),
                    "train_end": train["period"].iloc[-1].date().isoformat(),
                    "test_start": test["period"].iloc[0].date().isoformat(),
                    "test_end": test["period"].iloc[-1].date().isoformat(),
                    "pattern_at_origin": pattern,
                    "models": row_models,
                }
            )

    pattern_results = []
    for pattern, model_rows in sorted(by_pattern.items()):
        model_metrics = {name: aggregate(rows) for name, rows in model_rows.items()}
        champion = min(model_metrics, key=lambda name: model_metrics[name]["wape"])
        pattern_results.append(
            {
                "pattern": pattern,
                "items": len(pattern_codes[pattern]),
                "evaluation_rows": len(next(iter(model_rows.values()))),
                "models": model_metrics,
                "champion": champion,
            }
        )

    model_metrics = {name: aggregate(rows) for name, rows in all_models.items()}
    interval_metrics = {
        name: {
            str(round(coverage * 100)): aggregate_intervals(rows, coverage)
            for coverage in INTERVAL_LEVELS
        }
        for name, rows in all_intervals.items()
    }
    global_champion = min(model_metrics, key=lambda name: model_metrics[name]["wape"])
    champion_manifest = {result["pattern"]: result["champion"] for result in pattern_results}
    champion_manifest["global_fallback"] = global_champion
    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_fingerprint": _file_sha256(data_path),
        "code_revision": _code_revision(Path(__file__).resolve().parents[1]),
        "evaluation_code_fingerprint": _file_sha256(Path(__file__)),
        "evaluation_code_dirty": _working_tree_is_dirty(Path(__file__).resolve().parents[1]),
        "dataset_type": "commax_monthly_shipments",
        "scope": "Top 20 items by cumulative shipments before the first evaluation holdout",
        "selection_cutoff": evaluation_start.date().isoformat(),
        "period": f"{df['period'].min().date()} to {df['period'].max().date()}",
        "evaluation_method": "Three rolling 6-month origins. Demand patterns are recalculated from each fold's training history; Prophet uses month-start future periods. Prediction intervals use split conformal absolute residuals from the three preceding origins only.",
        "items": len(top_codes),
        "item_codes": top_codes,
        "item_manifest": item_manifest,
        "champion_manifest": champion_manifest,
        "horizon_months": horizon_months,
        "folds": folds,
        "models": model_metrics,
        "interval_metrics": interval_metrics,
        "pattern_results": pattern_results,
        "fold_metrics": fold_metrics,
        "skipped_pattern_rows": skipped_pattern_rows,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", type=Path, default=root / "data/raw/Final_KR_modeling_long_with_external_data.csv")
    parser.add_argument("--output", type=Path, default=root / "data/processed/commax_evaluation.json")
    args = parser.parse_args()

    result = evaluate_commax(args.data_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved Commax benchmark to {args.output}")
    for result_by_pattern in result["pattern_results"]:
        print(result_by_pattern["pattern"], result_by_pattern["champion"], result_by_pattern["models"])


if __name__ == "__main__":
    main()
