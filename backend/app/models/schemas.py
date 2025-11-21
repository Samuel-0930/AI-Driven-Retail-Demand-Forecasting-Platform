from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class PredictionRequest(BaseModel):
    store_id: int
    product_id: int
    start_date: date
    end_date: date
    is_promo: Optional[bool] = False

class PredictionPoint(BaseModel):
    date: date
    forecast: float
    lower_bound: float
    upper_bound: float

class PredictionResponse(BaseModel):
    store_id: int
    product_id: int
    predictions: List[PredictionPoint]
