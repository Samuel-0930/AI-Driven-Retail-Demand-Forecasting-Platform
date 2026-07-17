import json
from pathlib import Path

import pandas as pd
from prophet import Prophet

from ...evaluate_commax import SEASONAL_PERIOD, best_sba_forecast


class CommaxDataNotFoundError(Exception):
    pass


class CommaxItemNotFoundError(Exception):
    pass


class CommaxForecastService:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[3]
        self.data_path = self.root / "data/raw/Final_KR_modeling_long_with_external_data.csv"
        self.evaluation_path = self.root / "data/processed/commax_evaluation.json"

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

    def forecast(self, item_code: str, horizon_months: int) -> dict:
        df = self._data()
        item = df[df["품목코드"] == item_code].sort_values("period").reset_index(drop=True)
        if item.empty:
            raise CommaxItemNotFoundError
        if not self.evaluation_path.exists():
            raise CommaxDataNotFoundError

        evaluation = json.loads(self.evaluation_path.read_text(encoding="utf-8"))
        pattern = item["Pattern"].iloc[0]
        pattern_result = next(result for result in evaluation["pattern_results"] if result["pattern"] == pattern)
        champion = pattern_result["champion"]
        values = item["value"].to_numpy()

        if champion == "croston_sba":
            predictions = best_sba_forecast(values, horizon_months)
        elif champion == "seasonal_naive":
            predictions = pd.Series(values[-SEASONAL_PERIOD:]).repeat((horizon_months + SEASONAL_PERIOD - 1) // SEASONAL_PERIOD).to_numpy()[:horizon_months]
        else:
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            train = item.rename(columns={"period": "ds", "value": "y"})[["ds", "y"]]
            model.fit(train)
            predictions = model.predict(model.make_future_dataframe(periods=horizon_months)).tail(horizon_months)["yhat"].to_numpy()

        future_dates = pd.date_range(item["period"].iloc[-1] + pd.offsets.MonthBegin(1), periods=horizon_months, freq="MS")
        return {
            "item_code": item_code,
            "item_name": item["품목명"].iloc[0],
            "pattern": pattern,
            "champion": champion,
            "benchmark_wape": pattern_result["models"][champion]["wape"],
            "predictions": [{"date": date.date().isoformat(), "forecast": round(max(0, float(prediction)), 0)} for date, prediction in zip(future_dates, predictions)],
        }
