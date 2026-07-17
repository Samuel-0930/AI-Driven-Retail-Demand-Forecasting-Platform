import mlflow
import pandas as pd
from functools import lru_cache
from ..models.schemas import PredictionRequest, PredictionResponse, PredictionPoint


class ModelNotFoundError(Exception):
    pass


class PredictionService:
    def __init__(self):
        self.experiment_name = "Demand_Sense_Baseline"

    def _get_best_run_id(self, store_id: int, product_id: int):
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if experiment is None:
            return None

        filter_string = (
            "attributes.status = 'FINISHED' "
            f"AND params.store_id = '{store_id}' "
            f"AND params.product_id = '{product_id}'"
        )
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=filter_string,
            order_by=["metrics.mae ASC", "start_time DESC"],
            max_results=1
        )

        if runs.empty:
            return None
        return runs.iloc[0].run_id

    @lru_cache(maxsize=128)
    def _load_model(self, run_id: str):
        return mlflow.prophet.load_model(f"runs:/{run_id}/model")

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        run_id = self._get_best_run_id(request.store_id, request.product_id)
        if not run_id:
            raise ModelNotFoundError

        loaded_model = self._load_model(run_id)
        dates = pd.date_range(start=request.start_date, end=request.end_date)
        future = pd.DataFrame({'ds': dates})
        future['is_promo'] = 1 if request.is_promo else 0
        forecast = loaded_model.predict(future)

        predictions = []
        for _, row in forecast.iterrows():
            predictions.append(PredictionPoint(
                date=row['ds'].date(),
                forecast=row['yhat'],
                lower_bound=row['yhat_lower'],
                upper_bound=row['yhat_upper']
            ))
            
        return PredictionResponse(
            store_id=request.store_id,
            product_id=request.product_id,
            predictions=predictions
        )
