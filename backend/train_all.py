import pandas as pd
from train_baseline import train_baseline
import os

def train_all_models():
    data_path = "data/raw/retail_sales.csv"
    if not os.path.exists(data_path):
        print("Data file not found.")
        return

    df = pd.read_csv(data_path)
    
    # Get unique combinations
    combinations = df[['store_id', 'product_id']].drop_duplicates().values
    
    print(f"Found {len(combinations)} combinations. Starting training...")
    
    for store_id, product_id in combinations:
        print(f"Training for Store {store_id}, Product {product_id}...")
        try:
            train_baseline(data_path, store_id, product_id)
        except Exception as e:
            print(f"Failed to train for Store {store_id}, Product {product_id}: {e}")

if __name__ == "__main__":
    train_all_models()
