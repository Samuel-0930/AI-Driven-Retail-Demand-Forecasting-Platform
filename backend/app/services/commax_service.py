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

    def _historical_absolute_errors(self, item: pd.DataFrame, horizon_months: int, champion: str) -> list[float]:
        """Build an item-level error distribution without looking at the final holdout."""
        errors: list[float] = []
        first_origin = len(item) - (4 * horizon_months)
        for origin in range(first_origin, len(item) - horizon_months, horizon_months):
            train = item.iloc[:origin]
            test = item.iloc[origin:origin + horizon_months]
            if len(train) <= SEASONAL_PERIOD or len(test) != horizon_months:
                continue
            predictions = self._predict(train, horizon_months, champion, test["period"])
            errors.extend(abs(float(actual) - max(0, float(prediction))) for actual, prediction in zip(test["value"], predictions))
        return errors

    @staticmethod
    def _risk_level(forecast_total: float, upper_total: float) -> tuple[str, str]:
        uplift = (upper_total - forecast_total) / forecast_total if forecast_total > 0 else 0.0
        if uplift >= 1:
            return "high", "변동 폭이 커 보수적인 재고 검토가 필요합니다."
        if uplift >= 0.5:
            return "medium", "수요 변동을 고려해 상한 기준 재고를 함께 검토하세요."
        return "low", "예측 대비 변동 폭이 비교적 안정적입니다."

    @staticmethod
    def _inventory_risk(available_inventory: float, forecast_demand: float, planning_demand: float) -> tuple[str, str]:
        if available_inventory < forecast_demand:
            return "high", "가용 재고가 기준 예측 수요보다 부족합니다. 발주 검토가 필요합니다."
        if available_inventory < planning_demand:
            return "medium", "기준 예측은 충족하지만, 선택한 서비스 수준의 안전 재고에는 못 미칩니다."
        return "low", "선택한 서비스 수준의 계획 수요를 충족하는 재고입니다."

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
        historical_errors = self._historical_absolute_errors(item, horizon_months, champion)
        error_margin = float(pd.Series(historical_errors).quantile(0.8)) if historical_errors else 0.0
        rows = []
        for (_, row), prediction in zip(actual.iterrows(), predictions):
            predicted = max(0, round(float(prediction), 0))
            actual_value = float(row["value"])
            lower_bound = max(0, round(predicted - error_margin, 0))
            upper_bound = round(predicted + error_margin, 0)
            rows.append({
                "date": row["period"].date().isoformat(),
                "actual": actual_value,
                "forecast": predicted,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "absolute_error": abs(actual_value - predicted),
            })
        total_actual = sum(row["actual"] for row in rows)
        wape = sum(row["absolute_error"] for row in rows) / total_actual * 100 if total_actual else 0.0
        coverage = sum(row["lower_bound"] <= row["actual"] <= row["upper_bound"] for row in rows) / len(rows) * 100 if rows else 0.0
        forecast_total = sum(row["forecast"] for row in rows)
        upper_total = sum(row["upper_bound"] for row in rows)
        risk_level, risk_message = self._risk_level(forecast_total, upper_total)
        return {
            "item_code": item_code,
            "pattern": pattern,
            "champion": champion,
            "benchmark_wape": pattern_result["models"][champion]["wape"],
            "holdout_wape": round(wape, 2),
            "interval_level": 80,
            "interval_coverage": round(coverage, 1),
            "demand_variability_risk": risk_level,
            "risk_message": risk_message,
            "planning_upper_total": upper_total,
            "forecast_total": forecast_total,
            "points": rows,
        }

    def inventory_plan(
        self,
        item_code: str,
        on_hand_inventory: float,
        incoming_inventory: float,
        lead_time_months: int,
        service_level: float,
    ) -> dict:
        df = self._data()
        item = df[df["품목코드"] == item_code].sort_values("period").reset_index(drop=True)
        if item.empty:
            raise CommaxItemNotFoundError

        pattern = item["Pattern"].iloc[0]
        champion, _ = self._champion_for_pattern(pattern)
        future_dates = pd.date_range(
            item["period"].iloc[-1] + pd.offsets.MonthBegin(1),
            periods=lead_time_months,
            freq="MS",
        )
        predictions = [max(0, float(value)) for value in self._predict(item, lead_time_months, champion, pd.Series(future_dates))]
        historical_errors = self._historical_absolute_errors(item, lead_time_months, champion)
        safety_stock_per_month = float(pd.Series(historical_errors).quantile(service_level)) if historical_errors else 0.0
        forecast_demand = sum(predictions)
        safety_stock = safety_stock_per_month * lead_time_months
        planning_demand = forecast_demand + safety_stock
        available_inventory = on_hand_inventory + incoming_inventory
        recommended_order = max(0.0, planning_demand - available_inventory)
        risk_level, risk_message = self._inventory_risk(available_inventory, forecast_demand, planning_demand)

        return {
            "item_code": item_code,
            "item_name": item["품목명"].iloc[0],
            "pattern": pattern,
            "champion": champion,
            "lead_time_months": lead_time_months,
            "service_level": round(service_level * 100),
            "on_hand_inventory": on_hand_inventory,
            "incoming_inventory": incoming_inventory,
            "available_inventory": round(available_inventory, 0),
            "forecast_demand": round(forecast_demand, 0),
            "safety_stock": round(safety_stock, 0),
            "planning_demand": round(planning_demand, 0),
            "recommended_order": round(recommended_order, 0),
            "inventory_risk": risk_level,
            "risk_message": risk_message,
            "assumption": "현재고와 입고 예정 재고가 리드타임 내 사용 가능하며, 과거 예측 오차가 향후 수요 변동을 대표한다고 가정합니다.",
        }
