from fastapi import APIRouter, HTTPException
from ..models.schemas import PredictionRequest, PredictionResponse
from ..services.prediction_service import PredictionService

router = APIRouter()
service = PredictionService()

@router.post("/predict", response_model=PredictionResponse)
def predict_demand(request: PredictionRequest):
    try:
        return service.predict(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
