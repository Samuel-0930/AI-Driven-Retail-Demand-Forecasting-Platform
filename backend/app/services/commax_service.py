import json
import os
from pathlib import Path

import pandas as pd
from prophet import Prophet

from ...evaluate_commax import SEASONAL_PERIOD, best_sba_forecast, best_tsb_forecast, seasonal_sba_forecast


class CommaxDataNotFoundError(Exception):
    pass


class CommaxItemNotFoundError(Exception):
    pass


class CommaxForecastService:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.data_path = Path(os.getenv("COMMAX_DATA_PATH", self.root / "data/public/commax_dashboard_top20.csv"))
        self.evaluation_path = Path(os.getenv("COMMAX_EVALUATION_PATH", self.root / "data/public/commax_evaluation.json"))

    def _data(self) -> pd.DataFrame:
        if not self.data_path.exists():
            raise CommaxDataNotFoundError
        df = pd.read_csv(self.data_path, usecols=["품목코드", "품목명", "Pattern", "period", "value"])
        df["period"] = pd.to_datetime(df["period"])
        return df

    def list_items(self) -> list[dict]:
        df = self._data()
        summary = df.groupby(["품목코드", "품목명", "Pattern"], as_index=False)["value"].sum()
        return [
            {"item_code": row["품목코드"], "item_name": row["품목명"], "pattern": row["Pattern"]}
            for _, row in summary.nlargest(20, "value").iterrows()
        ]

    def _champion_for_pattern(self, pattern: str) -> tuple[str, dict]:
        if not self.evaluation_path.exists():
            raise CommaxDataNotFoundError
        evaluation = json.loads(self.evaluation_path.read_text(encoding="utf-8"))
        result = next(result for result in evaluation["pattern_results"] if result["pattern"] == pattern)
        return result["champion"], result

    def _predict(self, item: pd.DataFrame, horizon_months: int, champion: str, future_dates: pd.Series):
        values = item["value"].to_numpy()
        if champion == "croston_sba":
            return best_sba_forecast(values, horizon_months)
        if champion == "seasonal_croston_sba":
            return seasonal_sba_forecast(item, future_dates)
        if champion == "tsb":
            return best_tsb_forecast(values, horizon_months)
        if champion == "seasonal_naive":
            return pd.Series(values[-SEASONAL_PERIOD:]).repeat((horizon_months + SEASONAL_PERIOD - 1) // SEASONAL_PERIOD).to_numpy()[:horizon_months]
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        train = item.rename(columns={"period": "ds", "value": "y"})[["ds", "y"]]
        model.fit(train)
        return model.predict(model.make_future_dataframe(periods=horizon_months)).tail(horizon_months)["yhat"].to_numpy()

    def forecast(self, item_code: str, horizon_months: int) -> dict:
        df = self._data()
        item = df[df["품목코드"] == item_code].sort_values("period").reset_index(drop=True)
        if item.empty:
            raise CommaxItemNotFoundError
        pattern = item["Pattern"].iloc[0]
        champion, pattern_result = self._champion_for_pattern(pattern)
        future_dates = pd.date_range(item["period"].iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon_months, freq="MS")
        predictions = self._predict(item, horizon_months, champion, pd.Series(future_dates))
        return {
            "item_code": item_code,
            "item_name": item["품목명"].iloc[0],
            "pattern": pattern,
            "champion": champion,
            "benchmark_wape": pattern_result["models"][champion]["wape"],
            "predictions": [{"date": date.date().isoformat(), "forecast": round(max(0, float(prediction)), 0)} for date, prediction in zip(future_dates, predictions)],
        }

    def backtest(self, item_code: str, horizon_months: int) -> dict:
        df = self._data()
        item = df[df["품목코드"] == item_code].sort_values("period").reset_index(drop=True)
        if item.empty:
            raise CommaxItemNotFoundError
        pattern = item["Pattern"].iloc[0]
        champion, pattern_result = self._champion_for_pattern(pattern)
        train, actual = item.iloc[:-horizon_months], item.iloc[-horizon_months:]
        predictions = self._predict(train, horizon_months, champion, actual["period"])
        rows = []
        for (_, row), prediction in zip(actual.iterrows(), predictions):
            predicted = max(0, round(float(prediction), 0))
            actual_value = float(row["value"])
            rows.append({"date": row["period"].date().isoformat(), "actual": actual_value, "forecast": predicted, "absolute_error": abs(actual_value - predicted)})
        total_actual = sum(row["actual"] for row in rows)
        wape = sum(row["absolute_error"] for row in rows) / total_actual * 100 if total_actual else 0.0
        return {"item_code": item_code, "pattern": pattern, "champion": champion, "benchmark_wape": pattern_result["models"][champion]["wape"], "holdout_wape": round(wape, 2), "points": rows}
