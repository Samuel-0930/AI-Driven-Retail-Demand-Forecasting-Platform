import logging

from fastapi import APIRouter, HTTPException, Query
from ..models.schemas import BacktestResponse, PredictionRequest, PredictionResponse
from ..services.prediction_service import EvaluationNotFoundError, ModelNotFoundError, PredictionService
from ..services.commax_service import CommaxDataNotFoundError, CommaxForecastService, CommaxItemNotFoundError

router = APIRouter()
service = PredictionService()
commax_service = CommaxForecastService()
logger = logging.getLogger(__name__)

@router.post("/predict", response_model=PredictionResponse)
def predict_demand(request: PredictionRequest):
    try:
        return service.predict(request)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="No trained model is available for this store and product")
    except Exception:
        logger.exception("Prediction request failed")
        raise HTTPException(status_code=500, detail="Prediction is temporarily unavailable")


@router.get("/evaluation", response_model=BacktestResponse)
def get_evaluation(store_id: int = Query(gt=0), product_id: int = Query(gt=0)):
    try:
        return service.get_evaluation(store_id, product_id)
    except EvaluationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="No evaluation is available for this store and product. Run bootstrap_demo.py first.",
        )
    except Exception:
        logger.exception("Evaluation request failed")
        raise HTTPException(status_code=500, detail="Evaluation results are temporarily unavailable")


@router.get("/commax/evaluation")
def get_commax_evaluation():
    try:
        return service.get_commax_evaluation()
    except EvaluationNotFoundError:
        raise HTTPException(status_code=404, detail="Commax evaluation has not been generated yet.")


@router.get("/commax/items")
def get_commax_items():
    try:
        return commax_service.list_items()
    except CommaxDataNotFoundError:
        raise HTTPException(status_code=404, detail="Commax source data is not available locally.")


@router.get("/commax/forecast")
def get_commax_forecast(item_code: str, horizon_months: int = Query(default=6, ge=1, le=12)):
    try:
        return commax_service.forecast(item_code, horizon_months)
    except CommaxItemNotFoundError:
        raise HTTPException(status_code=404, detail="Commax item was not found.")
    except CommaxDataNotFoundError:
        raise HTTPException(status_code=404, detail="Commax source data or benchmark is not available locally.")


@router.get("/commax/backtest")
def get_commax_backtest(item_code: str, horizon_months: int = Query(default=6, ge=1, le=12)):
    try:
        return commax_service.backtest(item_code, horizon_months)
    except CommaxItemNotFoundError:
        raise HTTPException(status_code=404, detail="Commax item was not found.")
    except CommaxDataNotFoundError:
        raise HTTPException(status_code=404, detail="Commax source data or benchmark is not available locally.")


@router.get("/commax/inventory-plan")
def get_commax_inventory_plan(
    item_code: str,
    on_hand_inventory: float = Query(default=0, ge=0),
    incoming_inventory: float = Query(default=0, ge=0),
    lead_time_months: int = Query(default=1, ge=1, le=6),
    service_level: float = Query(default=0.8, ge=0.5, le=0.99),
):
    try:
        return commax_service.inventory_plan(
            item_code,
            on_hand_inventory,
            incoming_inventory,
            lead_time_months,
            service_level,
        )
    except CommaxItemNotFoundError:
        raise HTTPException(status_code=404, detail="Commax item was not found.")
    except CommaxDataNotFoundError:
        raise HTTPException(status_code=404, detail="Commax source data or benchmark is not available locally.")
