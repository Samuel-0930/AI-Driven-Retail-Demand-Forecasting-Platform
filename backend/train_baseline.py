import pandas as pd
import numpy as np
from prophet import Prophet
import mlflow
import mlflow.prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import argparse

def train_baseline(data_path, store_id, product_id):
    """
    Trains a baseline Prophet model for a specific store and product.
    Logs parameters and metrics to MLflow.
    """
    # 1. Load Data
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter for specific store/product
    mask = (df['store_id'] == store_id) & (df['product_id'] == product_id)
    item_df = df[mask].copy()
    
    if item_df.empty:
        print(f"No data found for Store {store_id}, Product {product_id}")
        return

    # Prophet requires columns 'ds' and 'y'
    item_df = item_df.rename(columns={'date': 'ds', 'sales': 'y'})
    
    # Split Train/Test (Last 30 days for testing)
    train_df = item_df.iloc[:-30]
    test_df = item_df.iloc[-30:]
    
    # 2. Setup MLflow
    mlflow.set_experiment("Demand_Sense_Baseline")
    
    with mlflow.start_run(run_name=f"Store_{store_id}_Product_{product_id}"):
        # 3. Train Model
        # Adding regressors (optional, but good for demo)
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.add_regressor('is_promo')
        
        # Fit
        model.fit(train_df)
        
        # 4. Evaluate
        future = model.make_future_dataframe(periods=30)
        # Add regressor values for future (assuming we know promo schedule)
        # For simplicity, we use the actual promo values from test set
        future['is_promo'] = pd.concat([train_df['is_promo'], test_df['is_promo']]).values
        
        forecast = model.predict(future)
        
        # Calculate Metrics on Test Set
        predictions = forecast.iloc[-30:]['yhat'].values
        actuals = test_df['y'].values
        
        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        
        print(f"Store {store_id}, Product {product_id} - MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        # 5. Log to MLflow
        mlflow.log_param("store_id", store_id)
        mlflow.log_param("product_id", product_id)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        
        # Log Model
        mlflow.prophet.log_model(model, "model")
        
        return mae, rmse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store_id", type=int, default=1)
    parser.add_argument("--product_id", type=int, default=1)
    args = parser.parse_args()
    
    data_path = "data/raw/retail_sales.csv"
    if not os.path.exists(data_path):
        print("Data file not found. Please run data_generator.py first.")
    else:
        train_baseline(data_path, args.store_id, args.product_id)
