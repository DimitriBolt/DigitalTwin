"""
Climate Control Digital Twin - Data Pipeline Guide

This document describes the complete data preparation pipeline for training the LSTM surrogate model.

## Pipeline Overview

The pipeline consists of TWO sequential scripts:

1. **analyze_climate_data.py** - Extract, validate, and analyze raw data
2. **prepare_training_data.py** - Normalize and prepare for LSTM training

## Architecture

```
Oracle SensorDB (500K timesteps, 15 years)
        ↓
[1] analyze_climate_data.py
        ↓
    - Extracts 64 Input parameters + 36 Output sensors
    - EDA analysis (missing values, outliers, seasonality)
    - Generates plots and statistics
    ↓
CSV: temperature_data.csv, humidity_data.csv, analysis statistics
        ↓
[2] prepare_training_data.py
        ↓
    - Combines temperature + humidity
    - Handles missing values (interpolation)
    - Normalizes to [0,1]
    - Creates sequences (12 timestep windows)
    - Splits train/val/test (70/15/15)
    ↓
Numpy arrays: X_train.npy, y_train.npy, X_val.npy, y_val.npy, X_test.npy, y_test.npy
        ↓
Ready for LSTM training!
```

## Execution Steps

### Step 1: Setup Oracle Environment

```bash
cd /home/dimitri/PycharmProjects/CO2Flux

# Create libaio compatibility symlink
mkdir -p /tmp/ora_compat
ln -sf /lib/x86_64-linux-gnu/libaio.so.1t64 /tmp/ora_compat/libaio.so.1

# Set LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_26:/tmp/ora_compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
```

### Step 2: Run Analysis Pipeline

```bash
# Activate virtual environment
source venv/bin/activate

# Install/verify dependencies
pip install -r requirements.txt

# Run analysis (extracts ~500K data points from Oracle)
# ⚠ WARNING: This may take 5-15 minutes depending on network
python3 scripts/analyze_climate_data.py
```

**Output:**
- `data/analysis/temperature_data.csv` - All temperature time series
- `data/analysis/humidity_data.csv` - All humidity time series
- `data/analysis/climate_data_analysis.csv` - Statistics summary
- `data/analysis/climate_data_analysis.png` - Visualization plots

### Step 3: Run Data Preparation

```bash
# Prepare training data
python3 scripts/prepare_training_data.py
```

**Output:**
- `data/training/X_train.npy` - Training inputs (sequences, timesteps, features)
- `data/training/y_train.npy` - Training outputs
- `data/training/X_val.npy` - Validation inputs
- `data/training/y_val.npy` - Validation outputs
- `data/training/X_test.npy` - Test inputs
- `data/training/y_test.npy` - Test outputs
- `data/training/normalization_params.json` - Min/max scales for denormalization
- `data/training/sensor_mapping.json` - Sensor name → index mapping
- `data/training/metadata.json` - Dataset metadata

## Data Specifications

### Step 1 Output: Analysis

**Temperature Data (temperature_data.csv):**
- 18 temperature sensors (4 towers × vertical points)
- Variable: AirTempC, Oracle variable_id=16
- Units: °C
- ~490K-500K data points (depends on availability)

**Humidity Data (humidity_data.csv):**
- 18 relative humidity sensors (4 towers × vertical points)
- Variable: RH, Oracle variable_id=15
- Units: %
- ~490K-500K data points

### Step 2 Output: Training Arrays

**Array Shapes:**
- `X_train`: (346K sequences, 12 timesteps, 36 features) ≈ 150 MB
- `y_train`: (346K sequences, 36 features) ≈ 50 MB
- `X_val`: (73K sequences, 12 timesteps, 36 features) ≈ 32 MB
- `y_val`: (73K sequences, 36 features) ≈ 11 MB
- `X_test`: (73K sequences, 12 timesteps, 36 features) ≈ 32 MB
- `y_test`: (73K sequences, 36 features) ≈ 11 MB

**Total disk usage:** ~280 MB

**Normalization:**
- All 36 features normalized to [0, 1]
- Min/max values stored in `normalization_params.json` for denormalization

**Sequence Structure:**
- Input: 12 timesteps (= 180 minutes = 3 hours of history)
- Output: 1 timestep (predict next 15 minutes)
- Temporal order preserved (no shuffling)

### Sensor Mapping (36 Output Features)

**Temperature (18):**
```
T_MTN_100, T_MTN_300, T_MTN_700, T_MTN_1300,       # Mountain tower (4)
T_NE_100, T_NE_300, T_NE_700, T_NE_1300, T_NE_2000, # NE tower (5)
T_NW_100, T_NW_300, T_NW_700, T_NW_1300,            # NW tower (4)
T_S_100, T_S_300, T_S_700, T_S_1300, T_S_2000       # South tower (5)
```

**Humidity (18):**
```
RH_MTN_100, RH_MTN_300, RH_MTN_700, RH_MTN_1300,
RH_NE_100, RH_NE_300, RH_NE_700, RH_NE_1300, RH_NE_2000,
RH_NW_100, RH_NW_300, RH_NW_700, RH_NW_1300,
RH_S_100, RH_S_300, RH_S_700, RH_S_1300, RH_S_2000
```

## Configuration Parameters

### analyze_climate_data.py

```python
RAINFOREST_SENSORS = {
    "temperature": {
        "MTN_100": 96, "MTN_300": 97, ...  # Oracle sensor IDs
    },
    "humidity": {
        "MTN_100": 114, "MTN_300": 115, ...  # Oracle sensor IDs
    }
}

VARIABLE_IDS = {
    "temperature": 16,  # AirTempC
    "humidity": 15,     # RH
}
```

To modify which sensors are included, edit the sensor ID mappings above.

### prepare_training_data.py

```python
SEQUENCE_LENGTH = 12        # 12 × 15min = 3 hours context window
FORECAST_HORIZON = 1        # Predict 1 timestep ahead (15 min)

TRAIN_SPLIT = 0.70          # 70% training data
VAL_SPLIT = 0.15            # 15% validation data
TEST_SPLIT = 0.15           # 15% test data
```

**Notes on splits:**
- Temporal order is PRESERVED (no shuffling)
- First 70% = training
- Next 15% = validation
- Last 15% = testing
- This is critical for time-series prediction!

## Usage in LSTM Training

### Load prepared data in PyTorch:

```python
import numpy as np

# Load data
X_train = np.load('data/training/X_train.npy')  # (346K, 12, 36)
y_train = np.load('data/training/y_train.npy')  # (346K, 36)
X_val = np.load('data/training/X_val.npy')
y_val = np.load('data/training/y_val.npy')

# Convert to PyTorch tensors
import torch
X_train_t = torch.from_numpy(X_train).float()
y_train_t = torch.from_numpy(y_train).float()

# Create DataLoader
from torch.utils.data import TensorDataset, DataLoader
train_dataset = TensorDataset(X_train_t, y_train_t)
train_loader = DataLoader(train_dataset, batch_size=256, shuffle=False)  # shuffle=False for time-series!

# Train LSTM model...
```

### Load normalization params:

```python
import json

with open('data/training/normalization_params.json') as f:
    norm_params = json.load(f)

# Denormalize predictions
denorm_pred = pred * (norm_params[sensor_name]['max'] - norm_params[sensor_name]['min']) + norm_params[sensor_name]['min']
```

## Troubleshooting

### Oracle Connection Failed

```
ERROR: Oracle connection failed: DPY-3001: cannot create ODBC environment handle
```

**Solution:**
1. Verify `/opt/oracle/instantclient_19_26` exists
2. Create libaio symlink:
   ```bash
   mkdir -p /tmp/ora_compat
   ln -sf /lib/x86_64-linux-gnu/libaio.so.1t64 /tmp/ora_compat/libaio.so.1
   ```
3. Set LD_LIBRARY_PATH before running:
   ```bash
   export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_26:/tmp/ora_compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
   ```

### analyze_climate_data.py takes too long

The script queries 500K+ data points from Oracle. This typically takes 5-15 minutes depending on:
- Network latency
- Oracle server load
- Number of sensors

This is normal for the first run. Subsequent runs will use the cached CSV files.

### Memory error during prepare_training_data.py

The full dataset is ~500K timesteps × 36 sensors ≈ 18M floating point numbers.

If you get memory errors:
1. Reduce number of sensors (edit OUTPUT_SENSORS in script)
2. Reduce number of timesteps (add LIMIT clause in Oracle query)
3. Process in batches (modify pivot/normalization to stream)

## Next Steps

After data preparation:

1. **Train LSTM Model** (Phase 1, weeks 3-5)
   - Architecture: 3-layer LSTM encoder-decoder
   - Input: 12 timesteps × 36 features
   - Output: 36 features (next timestep)
   - Target: 10-15% RMSE

2. **Build REST API** (Phase 1, weeks 6-8)
   - FastAPI endpoint `/predict`
   - Accept: 64 input parameters
   - Return: 36 output predictions

3. **Docker Container** (Phase 1, weeks 6-8)
   - Package LSTM model + API
   - For student algorithm submissions

## References

- **AGENTS.md**: Project conventions and quick start
- **CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md**: Full architecture details
- **variables_schema.xlsx**: Sensor definitions (Output sheet for Oracle mappings)
"""

