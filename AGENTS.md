# DigitalTwin Project Instructions

## Project Overview

This project develops a **Digital Twin for RainForest Climate Control** at Biosphere 2, including LSTM modeling and a student algorithm competition framework.

**Key objectives:**
- Build LSTM model to predict RainForest climate state from control inputs
- Create digital twin for calibration and inverse problem formulation
- Develop student competition platform with scoring framework
- Support 64 climate control parameters driving 36 measurement sensors

---

## Quick Start

**Python requirements:**
- Python 3.11+ (project uses `tomllib` for configuration)
- Virtual environment via `python -m venv venv`
- Install dependencies: `pip install -r requirements.txt`

**Oracle setup:**
- Oracle credentials in `/home/dimitri/Documents/.env` (preferred) or project `.env` (edit if using project root copy)
  - Scripts currently read from home directory by default; modify env path if needed
- Uses `python-oracledb` in **thick mode** (required for native encryption on this database)
- Oracle Instant Client: `/opt/oracle/instantclient_19_26`
- On Linux: prepend `/opt/oracle/instantclient_19_26` and `/tmp/ora_compat` to `LD_LIBRARY_PATH` to resolve libaio compatibility

**⚠️ KNOWN ISSUE - Path Configuration:**
- All scripts in `scripts/` have hardcoded `ROOT = Path("/home/dimitri/PycharmProjects/CO2Flux")`
- This must be updated to point to the actual DigitalTwin project root before running:
  ```bash
  # Fix: Change all occurrences in scripts/ from:
  ROOT = Path("/home/dimitri/PycharmProjects/CO2Flux")
  # To:
  ROOT = Path(__file__).resolve().parent.parent  # Relative to project root
  ```
- Alternatively, ensure `data/` directories exist in the CO2Flux project or symlink appropriately

**Phase 1: Data Pipeline Scripts**
```bash
# Step 1: Extract and analyze 500K climate timesteps from Oracle
python3 scripts/analyze_climate_data.py

# Step 2: Normalize and prepare data for LSTM training
python3 scripts/prepare_training_data.py
```

**Workbook updaters:**
```bash
# Regenerate RainForest control parameters (64 inputs)
python3 scripts/update_input_sheet.py

# Regenerate RainForest climate response sensors (36 outputs, 4 towers)
python3 scripts/update_rainforest_output_sheet.py

# Regenerate auxiliary climate and soil measurements
python3 scripts/update_moss_sheet.py
```

---

## Project Structure

### `Sensors_Description/`

**RainForest Inventory:**
- `Bio2-Rainforest-Inventory.xlsx` — RainForest biome sensor inventory (36 channels)
- `Bio2-Controls-Inventory-29Jan2026.xlsx` — RainForest climate control system (64 parameters)
- `Bio2-Ocean-Inventory.xlsx` — Ocean biome inventory (reference only)
- `Bio2-Outdoor-Inventory.xlsx` — Outdoor sensors (reference only)

**Workbook & Metadata:**
- `variables_schema.xlsx` — Master workbook with Input/Output sheets
  - **Input sheet:** 64 climate control parameters (setpoints, fan commands, valve positions)
  - **Output sheet:** 36 climate response sensors (temperature & humidity, 4 towers × vertical profiles)
- `output_sheet_notes.md` — Documentation for Output sheet structure and generation

### `scripts/`

**Data Pipeline (Phase 1 - Weeks 1-2):**
- `analyze_climate_data.py` — Extract and analyze ~500K timesteps from Oracle
  - Loads all 36 Output sensors (T and RH)
  - Performs EDA: missing values, outliers, seasonality
  - Generates CSV time series and analysis plots
  - Output: `data/analysis/{temperature,humidity}_data.csv`

- `prepare_training_data.py` — Normalize and prepare data for LSTM
  - Handles missing values (linear interpolation)
  - Normalizes features to [0, 1]
  - Creates sequences: 12-step windows → 1-step predictions
  - Splits: 70% train / 15% val / 15% test (preserves temporal order)
  - Output: numpy arrays in `data/training/`

**Workbook Generators (executable source of truth):**
- `update_input_sheet.py` → Input sheet (64 RainForest control parameters)
  - Source: `Bio2-Controls-Inventory-29Jan2026.xlsx`
  - Oracle: `BIOMS.DATAVALUES` table

- `update_rainforest_output_sheet.py` → Output sheet (36 RainForest climate sensors)
  - Source: `Bio2-Rainforest-Inventory.xlsx`
  - Oracle: `BIOMS.DATAVALUES` table (variable_id 16 for temp, 15 for humidity)
  - Towers: Mountain, Northeast, Northwest, South
  - Variables: Temperature (T) and Relative Humidity (RH)
  - Heights: 100, 300, 700, 1300 cm (some towers: 2000 cm)

- `update_moss_sheet.py` → Humidity, soilTemp, Other_sensors sheets
  - Auxiliary RainForest measurements

- `filter_input_climate_controls.py` — Analyze and verify 64 input parameters

### `docs/`

**Primary documentation (in order of detail level):**
- `_INDEX.md` — Navigation guide for all Climate control docs
- `CLIMATE_CONTROL_QUICK_START.md` — Quick recall (5-10 min read)
- `CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md` — Full architecture (30+ min read)
- `DATA_PIPELINE_GUIDE.md` — Data extraction & preparation pipeline

### `data/`

**Directory structure (auto-created by scripts):**
```
data/
  analysis/
    temperature_data.csv           # All 18×15-minute T measurements
    humidity_data.csv              # All 18×15-minute RH measurements
    climate_data_analysis.csv      # Summary statistics
    climate_data_analysis.png      # EDA plots
  training/
    X_train.npy                    # Training sequences (346K, 12, 36)
    y_train.npy                    # Training labels (346K, 36)
    X_val.npy                      # Validation sequences (73K, 12, 36)
    y_val.npy                      # Validation labels (73K, 36)
    X_test.npy                     # Test sequences (73K, 12, 36)
    y_test.npy                     # Test labels (73K, 36)
    normalization_params.json      # Min/max scales for [0,1] normalization
    sensor_mapping.json            # Feature name → index mapping
    metadata.json                  # Dataset info, timestamps, stats
```

---

## Conceptual Architecture: Closed-Loop Control Simulator

This project is best understood as a **closed-loop control testing platform** — analogous to
QuantConnect LEAN (algorithmic trading backtester), but for climate control.

### The Control Loop

```
┌──────────────────────────────────────────────────────────┐
│                SIMULATION STEP (15 minutes)              │
│                                                          │
│  ┌─────────────┐   64 commands    ┌──────────────────┐  │
│  │  ALGORITHM  │ ───────────────> │  LSTM DIGITAL    │  │
│  │             │                  │  TWIN            │  │
│  │  observe →  │ <─────────────── │  (environment    │  │
│  │  decide →   │  36 sensor vals  │   simulator)     │  │
│  │  command    │                  │                  │  │
│  └─────────────┘                  └──────────────────┘  │
│                                    ↑                     │
│                         Captures temporal dynamics:      │
│                         - Response delays (thermal mass) │
│                         - Autocorrelation (inertia)      │
│                         - Seasonal patterns              │
└──────────────────────────────────────────────────────────┘
```

### Framing as a Reinforcement Learning Environment

| RL Concept | In This Project |
|---|---|
| **State** | 36 sensor readings + time context |
| **Action** | 64 control parameter values |
| **Reward** | f(comfort, energy efficiency, stability) |
| **Dynamics** | LSTM surrogate model |
| **Episode** | N-day simulation window |

### Analogy with QuantConnect LEAN

| QuantConnect LEAN | This Project |
|---|---|
| Historical market data | Historical sensor data (500K timesteps) |
| Simulated market (order book) | LSTM digital twin (environment simulator) |
| Trading algorithm (strategy) | Climate control algorithm |
| P&L / Sharpe ratio | Comfort + energy + stability score |
| Backtesting | Algorithm testing on historical sequences |

### Algorithm Types Supported

- **Classical:** PID controllers, rule-based bang-bang
- **Predictive:** MPC (Model Predictive Control)
- **Learning:** RL agents (can train directly against LSTM surrogate)

---

## RainForest System Overview

### Control & Measurement Architecture

```
64 Input Control Parameters
  ├─ Temperature Setpoints (15)
  ├─ Supply Fan Commands (7)
  └─ Valve/Damper/Occupancy Commands (42)
        ↓
    [RainForest Climate System]
        ↓
36 Output Measurement Sensors (4 Towers)
  ├─ Mountain Tower (MTN): 9 sensors (4T + 4RH + 1 other)
  ├─ Northeast Tower (NE): 10 sensors (5T + 5RH)
  ├─ Northwest Tower (NW): 8 sensors (4T + 4RH)
  └─ South Tower (S): 10 sensors (5T + 5RH)
```

### Spatial Structure

**Measurement heights per tower:** 100, 300, 700, 1300 cm (NE & S: also 2000 cm)

**Oracle references:**
- Temperature: variable_id = 16 (AirTempC)
- Relative Humidity: variable_id = 15 (RH)
- Oracle table: `BIOMS.DATAVALUES`

---

## Phase 1: Data Preparation Pipeline

### Goal

Extract and prepare ~500K historical timesteps (15 years at 15-minute intervals) for LSTM training.

### Pipeline Steps

#### Step 1: analyze_climate_data.py

```bash
python3 scripts/analyze_climate_data.py
```

**Input:** Oracle SensorDB (BIOMS.DATAVALUES)

**Processing:**
- Connects to Oracle (thick mode, native encryption)
- Fetches 36 Output sensors across all time windows
- Performs exploratory data analysis (EDA)
- Detects: missing values, outliers, seasonality patterns
- Generates statistics and plots

**Output:**
- `data/analysis/temperature_data.csv` — T(x,t) time series
- `data/analysis/humidity_data.csv` — RH(x,t) time series
- `data/analysis/climate_data_analysis.csv` — Summary statistics
- `data/analysis/climate_data_analysis.png` — Visualization

**Expected runtime:** 5-15 minutes (first run); faster on subsequent runs

#### Step 2: prepare_training_data.py

```bash
python3 scripts/prepare_training_data.py
```

**Input:** CSV files from Step 1

**Processing:**
- Loads analyzed data
- Imputes missing values (linear interpolation)
- Normalizes all 36 features to [0, 1] range
- Creates sliding windows: 12-step input → 1-step output
- Splits temporally: 70% train / 15% val / 15% test

**Output:**
- `data/training/X_train.npy` — Shape (346K, 12, 36)
- `data/training/y_train.npy` — Shape (346K, 36)
- `data/training/X_val.npy` — Shape (73K, 12, 36)
- `data/training/y_val.npy` — Shape (73K, 36)
- `data/training/X_test.npy` — Shape (73K, 12, 36)
- `data/training/y_test.npy` — Shape (73K, 36)
- `data/training/normalization_params.json` — Scales for denormalization
- `data/training/sensor_mapping.json` — Channel ID ↔ sensor name
- `data/training/metadata.json` — Dataset statistics and info

**Total disk:** ~280 MB

**Next steps:** Feed numpy arrays into PyTorch/TensorFlow LSTM model

---

## Workbook: variables_schema.xlsx

### Input Sheet Structure

**Purpose:** Define 64 RainForest climate control parameters for the inverse problem

**Columns:** Physical description, spatial location, Oracle metadata, units, conversion

**Filtering:**
1. Column A (Physical quantity): include temperature setpoints, fan commands, valve commands
2. Column G (PDE role): filter to "Inventory BIOM=1, BIOMNAME=Rainforest"
3. Result: 64 RainForest control inputs

**Update:** `python3 scripts/update_input_sheet.py`

### Output Sheet Structure

**Purpose:** Define 36 RainForest climate measurement sensors (observation network)

**Columns:** Physical description (T/RH), tower location, height, Oracle metadata, ready-to-run SQL

**Sensors:** 
- 18 Temperature channels (all towers, all heights)
- 18 Relative Humidity channels (all towers, all heights)

**Update:** `python3 scripts/update_rainforest_output_sheet.py`

**Reference:** See `Sensors_Description/output_sheet_notes.md` for full details

---

## Database Configuration

### Oracle Connection

- **Credentials:** `/home/dimitri/Documents/.env`
- **Mode:** Thick (required; thin mode fails with DPY-3001)
- **Instant Client:** `/opt/oracle/instantclient_19_26`
- **Linux symlink:** `/tmp/ora_compat/libaio.so.1` for compatibility

### Connection Pattern

```python
oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_LIB_DIR)
dsn = oracledb.makedsn(host, port, sid=ORACLE_SID)
conn = oracledb.connect(user=user, password=password, dsn=dsn)
```

Always close: `cur.close()` and `conn.close()`

### Environment Setup for Scripts

All scripts use this pattern:

```python
# At module top (after imports)
from dotenv import dotenv_values

ENV_PATH = Path.home() / "Documents" / ".env"
env = dotenv_values(str(ENV_PATH))

ORACLE_HOST = env.get("ORACLE_HOST")
ORACLE_PORT = int(env.get("ORACLE_PORT", 1521))
ORACLE_SID = env.get("ORACLE_SID")
ORACLE_USER = env.get("ORACLE_USER")
ORACLE_PASSWORD = env.get("ORACLE_PASSWORD")
ORACLE_CLIENT_LIB_DIR = Path(env.get("ORACLE_CLIENT_LIB_DIR", "/opt/oracle/instantclient_19_26"))

# Setup thick mode
def setup_oracle_environment():
    """Initialize Oracle client (must be called before connection)."""
    oracledb.init_oracle_client(lib_dir=str(ORACLE_CLIENT_LIB_DIR))
    # Also setup libaio symlink on Linux
```

When making Oracle changes, ensure this pattern is followed.

### Query Windows

- Fetch time series by time windows (not all history at once)
- Standard Oracle table: `BIOMS.DATAVALUES`
- Access patterns: use sensor ID + variable ID to locate specific channels

---

## AI Agent Workflow & Debugging

### Before Making Changes

1. **Read all paths in the code.** Hardcoded ROOT paths are the most common issue.
   - Scripts in `scripts/` currently point to `CO2Flux`; verify they should point to DigitalTwin
   - Always use relative paths or `Path(__file__).resolve().parent.parent` if possible

2. **Check configuration first.** Before editing functions, locate and understand:
   - `ROOT`, `OUTPUT_DIR`, `DATA_DIR` constants
   - `RAINFOREST_SENSORS` dictionary (sensor ID mappings)
   - `SEQUENCE_LENGTH`, split ratios, other tunable parameters

3. **Verify Oracle credentials.** If any script fails with connection errors:
   - Check `.env` file exists at `/home/dimitri/Documents/.env`
   - Verify `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SID`, `ORACLE_USER`, `ORACLE_PASSWORD`
   - Ensure `LD_LIBRARY_PATH` is set correctly (use `echo $LD_LIBRARY_PATH` to verify)

### Common Debugging Patterns

**Script fails with "DPY-3001" or connection error:**
- Missing `oracledb.init_oracle_client()` call
- Or `LD_LIBRARY_PATH` not set
- Or credentials in `.env` file are wrong

**"FileNotFoundError" when writing output:**
- Check `OUTPUT_DIR.mkdir(parents=True, exist_ok=True)` is called
- Verify ROOT path is correct (mentioned above)

**"ImportError: No module named 'oracledb'":**
- Dependencies not installed: `pip install -r requirements.txt`
- Virtual environment not activated: `source venv/bin/activate`

### Documentation Convention

When you modify a script, update its module docstring to reflect changes:
```python
"""
[Old description preserved]

Changes (Date, Agent):
- [What changed and why]
"""
```

### Testing Changes

After editing a script:
1. Check syntax: `python3 -m py_compile scripts/script_name.py`
2. Check type hints: Run with `--strict` if you use a type checker
3. For Oracle scripts: Test with a small data window first, not full 500K timesteps
4. Verify output files are created in expected `data/` subdirectories

---

## Project Status & Current Phase

### Phase 1: ✅ DATA PREPARATION COMPLETE (May 2026)

**What's done:**
- `analyze_climate_data.py` (382 lines) — Oracle extraction & EDA  
- `prepare_training_data.py` (351 lines) — Data normalization & sequencing  
- Complete documentation (DATA_PIPELINE_GUIDE.md, etc.)
- ~500K timesteps extracted, normalized, and split into train/val/test
- Output: Ready for LSTM training (numpy arrays in `data/training/`)

**Reference reports:**
- `PHASE1_COMPLETE.md` — Summary of Phase 1 completion (May 10, 2026)
- `FINAL_REPORT_PHASE1.md` — Detailed completion report with metrics

**Status for AI agents:** Assume data pipeline is functional baseline. Focus on:
- Phase 2: LSTM model training (not yet started)
- Phase 3: REST API & Docker (not yet started)
- Student competition framework (planned, not implemented)

---

## Phase Roadmap & AI Agent Guidance

### Phase 1: Data Preparation ✅ COMPLETE

**For AI agents working on Phase 1 enhancements:**
- Do NOT rewrite core scripts (analyze_climate_data.py, prepare_training_data.py) unless critical bug found
- Focus on: path fixes, documentation improvements, utility functions
- Fix the hardcoded path issue if touching script files
- Ensure all output files are properly indexed and documented

**Reference:** See above for completion reports

### Phase 2: LSTM Model Training 🔜 COMING NEXT (Weeks 3-5)

**Expected architecture:**
- 3-layer encoder-decoder LSTM
- Input: 12 timesteps × 36 features
- Output: 1 timestep × 36 features (next 15-minute prediction)
- Target performance: 10-15% RMSE

**For AI agents approaching Phase 2:**
1. Use training data from `data/training/X_train.npy`, etc. (Phase 1 outputs)
2. Load normalization params from `data/training/normalization_params.json`
3. Build model with PyTorch or TensorFlow (use whichever matches project choice)
4. Save denormalization logic for inference
5. Export model to ONNX format for deployment

**Files to create:** `models/lstm_model.py` or `models/train_lstm.py`

### Phase 3: REST API & Docker 🔜 LATER (Weeks 6-8)

**Expected deliverables:**
- FastAPI server with `/predict` endpoint
- Docker container with preloaded model
- Inference time < 50ms per sample
- API documentation (OpenAPI/Swagger)

**For AI agents approaching Phase 3:**
- Use trained model from Phase 2
- Create `src/api.py` or `api/server.py`
- Load model weights at startup
- Ensure thread-safe inference

### Phase 4: Evaluation Framework 🔜 LATER (Weeks 9-12)

**Expected deliverables:**
- Scoring system (energy, comfort, stability)
- Constraint validation (hard limits on outputs)
- Leaderboard database
- CI/CD pipeline for student submissions

---

## Student Competition Framework

### Scoring (Future Implementation)

- **Energy efficiency:** 40%
- **Comfort (target climate state):** 35%
- **Stability (smooth transitions):** 25%

### Submission Format

- Docker container with REST API
- Input: 64 control parameters (JSON payload)
- Output: predicted 36 sensor values
- Inference time requirement: ~50ms per 15-minute timestep

### Digital Twin Validation

- Compare student predictions vs. actual RainForest sensor data
- Calibration: use Phase 1 LSTM as baseline model
- Scenarios: test with historical control sequences

---

## Coding Patterns & Conventions

### Python Style
- **Python version:** 3.11+ (required for `tomllib`)
- **Type hints:** Use `from __future__ import annotations` at module top
  - Mostly complete but not required for all functions; focus on public APIs
- **Configuration:** Hardcoded at module top (immediately after imports)
  - `ROOT`, file paths, sensor mappings, API parameters
  - Make these discoverable so agents can locate and modify settings
- **Error handling:** Graceful degradation with try/except for optional dependencies (e.g., oracledb)
- **Dependencies:** Minimal; keep `requirements.txt` lean

### File Organization
- **Scripts:** Single-file design with clear sections (CONFIGURATION, FUNCTIONS, MAIN)
- **Documentation:** Docstrings at module top describe purpose, inputs, outputs, usage
- **Comments:** Section headers with `# ============` for navigation

### Common Imports Pattern
```python
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    import oracledb
except ImportError:
    print("ERROR: oracledb not installed...")
    sys.exit(1)
```

---


## Common Development Tasks

### Running the Data Pipeline

```bash
# Verify environment
export LD_LIBRARY_PATH=/opt/oracle/instantclient_19_26:/tmp/ora_compat${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
source venv/bin/activate

# Step 1: Extract & analyze data (⚠️ Fix ROOT path first)
cd /home/dimitri/PycharmProjects/DigitalTwin
python3 scripts/analyze_climate_data.py        # ~5-15 min

# Step 2: Prepare training data
python3 scripts/prepare_training_data.py       # ~1-2 min

# Verify output
ls -lh data/training/
```

### Modifying Sensor Mappings

All sensor IDs are hardcoded at the top of scripts. To change:
1. Open script (e.g., `analyze_climate_data.py`)
2. Find `RAINFOREST_SENSORS` dict (line ~54)
3. Update sensor IDs (from `variables_schema.xlsx` Output sheet)
4. Same pattern in all workbook update scripts

### Configuration Parameters

Key parameters for AI agents to know:
- **`SEQUENCE_LENGTH = 12`** — 3-hour context window (12 × 15 min)
- **`TRAIN_SPLIT = 0.70`** — Train/val/test ratio
- **`RAINFOREST_SENSORS`** — Sensor ID mapping (oracle channel → name)
- **`VARIABLE_IDS`** — Oracle variable_id for T=16, RH=15

Edit these at module top to change pipeline behavior.

---

**Note:** This repository was separated from the larger CO2Flux project in May 2026.

- **Separate project:** `CO2Flux` — CO2 vertical profile analysis
  - Location: `/home/dimitri/PycharmProjects/CO2Flux/`
  - Focus: CO2 influx/outflux on LEO Center/East/West slopes
  - Not covered by this document

---

## Implementation Timeline

- **Phase 1 (Weeks 1-12):** MVP with data pipeline, LSTM training, API, evaluation framework
- **Phase 2 (Weeks 13-24):** Ensemble models, uncertainty quantification, scenarios
- **Phase 3 (Weeks 25+):** Production, live integration, extended competitions

---

## Key Stakeholders

- **John Adams** (jadamsb2@arizona.edu) — Biosphere 2 Operations Director
- **Professor Gabitov** — Academic advisor
- **Dimitri Bolt** (dimitribolt@arizona.edu) — Project lead

---

## References

- `docs/CLIMATE_CONTROL_QUICK_START.md` — Quick reference
- `docs/CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md` — Full architecture
- `docs/DATA_PIPELINE_GUIDE.md` — Detailed pipeline guide
- `Sensors_Description/output_sheet_notes.md` — Output sensor reference
- `FINAL_REPORT_PHASE1.md` — Phase 1 completion report
- `/home/dimitri/PycharmProjects/CO2Flux/` — CO2 project (separate)

