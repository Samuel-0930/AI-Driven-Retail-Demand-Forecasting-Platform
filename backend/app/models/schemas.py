from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List
from datetime import date

class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    store_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    start_date: date
    end_date: date
    is_promo: bool = False

    @model_validator(mode="after")
    def validate_forecast_window(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days + 1 > 90:
            raise ValueError("forecast horizon must not exceed 90 days")
        return self

class PredictionPoint(BaseModel):
    date: date
    forecast: float
    lower_bound: float
    upper_bound: float

class PredictionResponse(BaseModel):
    store_id: int
    product_id: int
    predictions: List[PredictionPoint]


class MetricSummary(BaseModel):
    mae: float
    wape: float
    mase: float


class BacktestFold(BaseModel):
    fold: int
    train_end: date
    test_start: date
    test_end: date
    prophet: MetricSummary
    seasonal_naive: MetricSummary


class BacktestResponse(BaseModel):
    store_id: int
    product_id: int
    dataset_type: str
    evaluation_method: str
    horizon_days: int
    folds: int
    prophet: MetricSummary
    seasonal_naive: MetricSummary
    fold_results: List[BacktestFold]
