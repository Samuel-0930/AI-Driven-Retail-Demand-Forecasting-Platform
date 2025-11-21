import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_retail_data(start_date='2023-01-01', days=730, n_stores=5, n_products=10):
    """
    Generates synthetic retail sales data with seasonality, trend, and causal factors.
    """
    np.random.seed(42)
    dates = pd.date_range(start=start_date, periods=days)
    
    data = []
    
    for store_id in range(1, n_stores + 1):
        for product_id in range(1, n_products + 1):
            # Base demand per product/store
            base_demand = np.random.randint(50, 200)
            
            # Store factor (some stores are busier)
            store_factor = np.random.uniform(0.8, 1.2)
            
            for date in dates:
                # 1. Weekly Seasonality (Higher on weekends)
                weekday = date.weekday()
                weekly_seasonality = 1.3 if weekday >= 5 else 0.9
                
                # 2. Yearly Seasonality (Sine wave)
                day_of_year = date.timetuple().tm_yday
                yearly_seasonality = 1 + 0.2 * np.sin(2 * np.pi * day_of_year / 365)
                
                # 3. Trend (Slight growth over time)
                trend = 1 + 0.0005 * (date - dates[0]).days
                
                # 4. Causal Factors: Promotions & Holidays
                is_promo = 0
                if np.random.random() < 0.15: # 15% chance of promotion
                    is_promo = 1
                
                promo_effect = 1.5 if is_promo else 1.0
                
                # Random Noise
                noise = np.random.normal(0, 0.1)
                
                # Calculate Sales
                expected_sales = base_demand * store_factor * weekly_seasonality * yearly_seasonality * trend * promo_effect
                sales = int(max(0, expected_sales * (1 + noise)))
                
                data.append({
                    'date': date,
                    'store_id': store_id,
                    'product_id': product_id,
                    'sales': sales,
                    'is_promo': is_promo,
                    'weekday': weekday
                })
                
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    print("Generating data...")
    df = generate_retail_data()
    
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "retail_sales.csv")
    
    df.to_csv(output_path, index=False)
    print(f"Data generated and saved to {output_path}")
    print(df.head())
