import logging

from fastapi import APIRouter, HTTPException
from ..models.schemas import PredictionRequest, PredictionResponse
from ..services.prediction_service import ModelNotFoundError, PredictionService

router = APIRouter()
service = PredictionService()
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
