"""Create the minimal, versioned dataset required by the public dashboard."""

from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

import pandas as pd

from backend.evaluate_commax import classify_demand_pattern


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/raw/Final_KR_modeling_long_with_external_data.csv"
EVALUATION_PATH = ROOT / "data/processed/commax_evaluation.json"
PUBLIC_DIR = ROOT / "data/public"
PUBLIC_DATA_PATH = PUBLIC_DIR / "commax_dashboard_top20.csv"
PUBLIC_EVALUATION_PATH = PUBLIC_DIR / "commax_evaluation.json"
PUBLIC_CARD_PATH = PUBLIC_DIR / "README.md"
REQUIRED_COLUMNS = ["품목코드", "품목명", "period", "value"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-path", type=Path, default=RAW_PATH)
    parser.add_argument("--evaluation-path", type=Path, default=EVALUATION_PATH)
    args = parser.parse_args()

    if not args.raw_path.exists():
        raise FileNotFoundError(f"Raw Commax CSV was not found: {args.raw_path}")
    if not args.evaluation_path.exists():
        raise FileNotFoundError(
            "Commax evaluation was not found. Run `PYTHONPATH=. venv/bin/python backend/evaluate_commax.py` first."
        )

    frame = pd.read_csv(args.raw_path, usecols=REQUIRED_COLUMNS)
    evaluation = json.loads(args.evaluation_path.read_text(encoding="utf-8"))
    top_codes = evaluation["item_codes"]
    public_frame = frame[frame["품목코드"].isin(top_codes)].sort_values(["품목코드", "period"])
    patterns = public_frame.groupby("품목코드")["value"].apply(
        lambda values: classify_demand_pattern(values.to_numpy())
    )
    public_frame["Pattern"] = public_frame["품목코드"].map(patterns)
    public_frame = public_frame[["품목코드", "품목명", "Pattern", "period", "value"]]

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    public_frame.to_csv(PUBLIC_DATA_PATH, index=False)
    public_fingerprint = hashlib.sha256(PUBLIC_DATA_PATH.read_bytes()).hexdigest()

    evaluation["public_data_fingerprint"] = public_fingerprint
    evaluation["public_rows"] = len(public_frame)
    PUBLIC_EVALUATION_PATH.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    PUBLIC_CARD_PATH.write_text(
        "# Public dashboard data\n\n"
        "This directory contains the minimal derived dataset required for the public Demand Signal dashboard. "
        "It is limited to the 20 items selected by cumulative shipment volume and the five columns used by the UI: "
        "item code, item name, demand pattern, month, and shipment value.\n\n"
        "The original source CSV and its additional fields are intentionally excluded. "
        "`commax_evaluation.json` is the schema-versioned three-fold, six-month rolling validation result used by the dashboard. "
        "Demand patterns are recalculated using only each fold's training history.\n",
        encoding="utf-8",
    )
    print(f"Saved {len(public_frame):,} rows to {PUBLIC_DATA_PATH}")
    print(f"Saved evaluation artifact to {PUBLIC_EVALUATION_PATH}")


if __name__ == "__main__":
    main()
