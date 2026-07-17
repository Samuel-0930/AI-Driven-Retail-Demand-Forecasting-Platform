"""Create a reproducible demo dataset and train the model used by the default UI."""

from pathlib import Path

from data_generator import generate_retail_data
from evaluate_backtest import evaluate_and_save
from train_baseline import train_baseline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "retail_sales.csv"
DEFAULT_STORE_ID = 1
DEFAULT_PRODUCT_ID = 1


def ensure_demo_data() -> None:
    if DATA_PATH.exists():
        return

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    generate_retail_data().to_csv(DATA_PATH, index=False)
    print(f"Created deterministic synthetic demo data at {DATA_PATH}")


def main() -> None:
    ensure_demo_data()
    mae, rmse = train_baseline(DATA_PATH, DEFAULT_STORE_ID, DEFAULT_PRODUCT_ID)
    evaluation = evaluate_and_save(DATA_PATH, DEFAULT_STORE_ID, DEFAULT_PRODUCT_ID)
    print(
        "Demo model is ready for "
        f"store {DEFAULT_STORE_ID}, product {DEFAULT_PRODUCT_ID} "
        f"(MAE: {mae:.2f}, RMSE: {rmse:.2f})."
    )
    print(
        "Rolling evaluation: "
        f"Prophet WAPE {evaluation['prophet']['wape']:.2f}% vs "
        f"seasonal naive WAPE {evaluation['seasonal_naive']['wape']:.2f}%."
    )


if __name__ == "__main__":
    main()
