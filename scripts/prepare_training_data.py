"""
Climate Control Digital Twin - Training Data Preparation (Part 2)

Prepares normalized, processed data for LSTM model training:
- Loads raw analyzed data (from analyze_climate_data.py output)
- Handles missing values (interpolation, forward-fill)
- Normalizes inputs/outputs to [0, 1] range
- Creates sequences for time-series prediction
- Generates train/val/test split respecting temporal order
- Exports numpy arrays ready for PyTorch/TensorFlow

Expected input:
- temperature_data.csv (from analyze_climate_data.py)
- humidity_data.csv (from analyze_climate_data.py)

Output:
- train_inputs.npy, val_inputs.npy, test_inputs.npy
- train_outputs.npy, val_outputs.npy, test_outputs.npy
- normalization_params.npy (scales/means for denormalization)
- sensor_mapping.json (sensor names to indices)

Usage:
    python3 scripts/prepare_training_data.py

Configuration:
    SEQUENCE_LENGTH: 12 (12 × 15min = 180 min = 3 hours of context)
    TRAIN_SPLIT: 0.70 (70% training)
    VAL_SPLIT: 0.15 (15% validation)
    TEST_SPLIT: 0.15 (15% testing)

Author: Dimitri Bolt
Project: RainForest Climate Control Digital Twin (May 2026)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT = Path("/home/dimitri/PycharmProjects/CO2Flux")
DATA_DIR = ROOT / "data" / "analysis"
OUTPUT_DIR = ROOT / "data" / "training"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Time series parameters
SEQUENCE_LENGTH = 12  # 12 × 15min = 3 hours context window
FORECAST_HORIZON = 1  # Predict next 1 timestep

# Data split (temporal order preserved)
TRAIN_SPLIT = 0.70
VAL_SPLIT = 0.15
TEST_SPLIT = 0.15

# Sensor names (from Output sheet)
OUTPUT_SENSORS = {
    "T": [
        "T_MTN_100", "T_MTN_300", "T_MTN_700", "T_MTN_1300",
        "T_NE_100", "T_NE_300", "T_NE_700", "T_NE_1300", "T_NE_2000",
        "T_NW_100", "T_NW_300", "T_NW_700", "T_NW_1300",
        "T_S_100", "T_S_300", "T_S_700", "T_S_1300", "T_S_2000",
    ],
    "RH": [
        "RH_MTN_100", "RH_MTN_300", "RH_MTN_700", "RH_MTN_1300",
        "RH_NE_100", "RH_NE_300", "RH_NE_700", "RH_NE_1300", "RH_NE_2000",
        "RH_NW_100", "RH_NW_300", "RH_NW_700", "RH_NW_1300",
        "RH_S_100", "RH_S_300", "RH_S_700", "RH_S_1300", "RH_S_2000",
    ]
}

INPUT_SENSORS = [
    # 64 control parameters (placeholder names - actual names from variables_schema.xlsx)
    f"u_{i}" for i in range(64)
]


# ============================================================================
# DATA LOADING & PREPROCESSING
# ============================================================================

def load_and_pivot_data(csv_path: Path, prefix: str) -> pd.DataFrame:
    """Load CSV and pivot to wide format (timestamp x sensors)."""
    if not csv_path.exists():
        print(f"⚠ File not found: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    # Rename sensors with prefix
    df["sensor"] = prefix + "_" + df["sensor"]

    # Pivot to wide format
    pivot_df = df.pivot_table(
        index="timestamp",
        columns="sensor",
        values="value",
        aggfunc="mean"  # Handle duplicates by averaging
    )

    return pivot_df


def handle_missing_values(df: pd.DataFrame, method: str = "linear") -> pd.DataFrame:
    """Handle missing values in time series."""
    print(f"  Missing values before: {df.isna().sum().sum()}")

    # Remove columns with >50% missing
    missing_pct = df.isna().sum() / len(df) * 100
    cols_to_drop = missing_pct[missing_pct > 50].index
    df = df.drop(columns=cols_to_drop)
    print(f"  Dropped {len(cols_to_drop)} columns (>50% missing)")

    # Interpolate remaining missing values
    if method == "linear":
        df = df.interpolate(method="linear", limit_direction="both", axis=0)
    elif method == "forward_fill":
        df = df.ffill().bfill()

    # Fill any remaining NaNs
    df = df.fillna(df.mean())

    print(f"  Missing values after: {df.isna().sum().sum()}")
    return df


def normalize_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Normalize data to [0, 1] range.

    Returns:
        (normalized_df, normalization_params)
    """
    norm_params: dict = {}
    df_normalized = df.copy()

    for col in df.columns:
        col_values = df[col].values
        min_val = float(np.nanmin(col_values))
        max_val = float(np.nanmax(col_values))

        # Avoid division by zero
        range_val = max_val - min_val
        if range_val < 1e-10:
            df_normalized[col] = 0.5
            norm_params[col] = {"min": float(min_val), "max": float(min_val + 1.0)}
        else:
            df_normalized[col] = (df[col] - min_val) / range_val
            norm_params[col] = {"min": float(min_val), "max": float(max_val)}

    return df_normalized, norm_params


def create_sequences(data: np.ndarray,
                    seq_len: int,
                    forecast_horizon: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create input-output sequences for time series prediction.

    Args:
        data: (n_timesteps, n_features) array
        seq_len: input sequence length
        forecast_horizon: steps to predict ahead

    Returns:
        (X, y) where X shape (n_sequences, seq_len, n_features)
                  y shape (n_sequences, n_features)
    """
    X, y = [], []

    for i in range(len(data) - seq_len - forecast_horizon + 1):
        X.append(data[i:i + seq_len])
        y.append(data[i + seq_len + forecast_horizon - 1])

    return np.array(X), np.array(y)


def train_val_test_split(X: np.ndarray, y: np.ndarray) -> dict:
    """Split sequences into train/val/test maintaining temporal order."""
    n_sequences = X.shape[0]

    train_idx = int(n_sequences * TRAIN_SPLIT)
    val_idx = int(n_sequences * (TRAIN_SPLIT + VAL_SPLIT))

    split = {
        "X_train": X[:train_idx],
        "y_train": y[:train_idx],
        "X_val": X[train_idx:val_idx],
        "y_val": y[train_idx:val_idx],
        "X_test": X[val_idx:],
        "y_test": y[val_idx:],
    }

    return split


# ============================================================================
# VALIDATION & REPORTING
# ============================================================================

def print_data_report(df: pd.DataFrame, split: dict, norm_params: dict) -> None:
    """Print data preparation report."""
    print("\n" + "="*80)
    print("DATA PREPARATION REPORT")
    print("="*80)

    print(f"\n📊 LOADED DATA:")
    print(f"  Timesteps: {df.shape[0]:,}")
    print(f"  Sensors: {df.shape[1]}")
    print(f"  Date range: {df.index.min()} to {df.index.max()}")
    print(f"  Duration: {(df.index.max() - df.index.min()).days} days")

    print(f"\n🔄 SEQUENCE CREATION:")
    print(f"  Sequence length: {SEQUENCE_LENGTH} timesteps (= {SEQUENCE_LENGTH * 15} minutes = {SEQUENCE_LENGTH * 15 / 60:.1f} hours)")
    print(f"  Total sequences: {split['X_train'].shape[0] + split['X_val'].shape[0] + split['X_test'].shape[0]:,}")

    print(f"\n📈 TRAIN/VAL/TEST SPLIT:")
    print(f"  Train:  {split['X_train'].shape[0]:,} sequences ({100*TRAIN_SPLIT:.0f}%)")
    print(f"  Val:    {split['X_val'].shape[0]:,} sequences ({100*VAL_SPLIT:.0f}%)")
    print(f"  Test:   {split['X_test'].shape[0]:,} sequences ({100*TEST_SPLIT:.0f}%)")

    print(f"\n📐 ARRAY SHAPES:")
    print(f"  X_train: {split['X_train'].shape} (sequences, timesteps, features)")
    print(f"  y_train: {split['y_train'].shape}")
    print(f"  X_val:   {split['X_val'].shape}")
    print(f"  y_val:   {split['y_val'].shape}")
    print(f"  X_test:  {split['X_test'].shape}")
    print(f"  y_test:  {split['y_test'].shape}")

    print(f"\n✅ NORMALIZATION APPLIED:")
    print(f"  Method: Min-Max scaling to [0, 1]")
    print(f"  Sensors normalized: {len(norm_params)}")

    print("\n" + "="*80)


def save_data(split: dict,
             sensor_names: list,
             norm_params: dict,
             df_dates) -> None:
    """Save train/val/test data and metadata."""

    # Save numpy arrays
    for key, arr in split.items():
        path = OUTPUT_DIR / f"{key}.npy"
        np.save(path, arr)
        print(f"✓ Saved {key}: {arr.shape} → {path}")

    # Save normalization parameters
    norm_path = OUTPUT_DIR / "normalization_params.json"
    with open(norm_path, "w") as f:
        json.dump(norm_params, f, indent=2)
    print(f"✓ Saved normalization params: {norm_path}")

    # Save sensor mapping
    sensor_map = {
        "output_sensors": {name: i for i, name in enumerate(OUTPUT_SENSORS["T"] + OUTPUT_SENSORS["RH"])},
        "input_sensors": {name: i for i, name in enumerate(INPUT_SENSORS)},
    }
    sensor_path = OUTPUT_DIR / "sensor_mapping.json"
    with open(sensor_path, "w") as f:
        json.dump(sensor_map, f, indent=2)
    print(f"✓ Saved sensor mapping: {sensor_path}")

    # Save metadata
    metadata = {
        "creation_date": pd.Timestamp.now().isoformat(),
        "total_timesteps_original": len(df_dates),
        "date_range": f"{df_dates.min()} to {df_dates.max()}",
        "sequence_length": SEQUENCE_LENGTH,
        "forecast_horizon": FORECAST_HORIZON,
        "n_features": len(sensor_names),
        "n_sequences_total": split["X_train"].shape[0] + split["X_val"].shape[0] + split["X_test"].shape[0],
        "train_val_test_split": [TRAIN_SPLIT, VAL_SPLIT, TEST_SPLIT],
    }
    meta_path = OUTPUT_DIR / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata: {meta_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("\n" + "="*80)
    print("CLIMATE CONTROL DIGITAL TWIN - DATA PREPARATION PIPELINE")
    print("="*80)

    # Step 1: Load data
    print("\n[1/5] Loading analyzed data...")
    temp_df = load_and_pivot_data(DATA_DIR / "temperature_data.csv", "T")
    hum_df = load_and_pivot_data(DATA_DIR / "humidity_data.csv", "RH")

    if temp_df.empty or hum_df.empty:
        print("ERROR: Could not load data. Run analyze_climate_data.py first.")
        return

    # Combine
    print("  Combining temperature and humidity...")
    df = pd.concat([temp_df, hum_df], axis=1)
    df = df.sort_index()
    print(f"  Combined shape: {df.shape}")

    # Step 2: Handle missing values
    print("\n[2/5] Handling missing values...")
    df = handle_missing_values(df, method="linear")

    # Step 3: Normalize
    print("\n[3/5] Normalizing data...")
    df_normalized, norm_params = normalize_data(df)
    print(f"  ✓ Normalized {len(norm_params)} sensors to [0, 1]")

    # Step 4: Create sequences
    print("\n[4/5] Creating sequences...")
    X, y = create_sequences(
        df_normalized.values,
        seq_len=SEQUENCE_LENGTH,
        forecast_horizon=FORECAST_HORIZON
    )
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")

    # Step 5: Train/val/test split
    print("\n[5/5] Splitting data (train/val/test)...")
    split = train_val_test_split(X, y)

    # Report
    print_data_report(df, split, norm_params)

    # Save
    print("\nSaving files...")
    save_data(split, df.columns.tolist(), norm_params, df.index)

    print("\n✓ Data preparation complete!")
    print(f"  Next step: Train LSTM model using data in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

