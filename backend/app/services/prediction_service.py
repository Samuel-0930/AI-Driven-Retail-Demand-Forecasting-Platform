import mlflow
import pandas as pd
from datetime import timedelta
from ..models.schemas import PredictionRequest, PredictionResponse, PredictionPoint

class PredictionService:
    def __init__(self):
        self.experiment_name = "Demand_Sense_Baseline"
        mlflow.set_experiment(self.experiment_name)

    def _get_latest_run_id(self, store_id: int, product_id: int):
        """
        Finds the latest successful run for the given store and product.
        """
        filter_string = f"params.store_id = '{store_id}' AND params.product_id = '{product_id}'"
        runs = mlflow.search_runs(
            experiment_ids=[mlflow.get_experiment_by_name(self.experiment_name).experiment_id],
            filter_string=filter_string,
            order_by=["start_time DESC"],
            max_results=1
        )
        
        if runs.empty:
            return None
        return runs.iloc[0].run_id

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        # 1. Find Model
        run_id = self._get_latest_run_id(request.store_id, request.product_id)
        if not run_id:
            raise ValueError(f"No model found for Store {request.store_id}, Product {request.product_id}")
            
        # 2. Load Model
        model_uri = f"runs:/{run_id}/model"
        loaded_model = mlflow.prophet.load_model(model_uri)
        
        # 3. Prepare Future Dataframe
        dates = pd.date_range(start=request.start_date, end=request.end_date)
        future = pd.DataFrame({'ds': dates})
        
        # Add Regressors (Assuming constant promo for simplicity or user input)
        # In a real app, we might look up a promo calendar
        future['is_promo'] = 1 if request.is_promo else 0
        
        # 4. Predict
        forecast = loaded_model.predict(future)
        
        # 5. Format Response
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
