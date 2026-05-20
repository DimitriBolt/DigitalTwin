# DigitalTwin: RainForest Climate Control Modeling

RainForest Digital Twin for Biosphere 2 - LSTM-based climate prediction and student algorithm competition platform.

---

## Quick Start

### 1) Python Requirements

Use **Python 3.11 or newer** (project uses `tomllib` for TOML configuration).

- Download: https://www.python.org/downloads/
- Windows: Enable "Add Python to PATH" during install

Check your installation:
```bash
python --version  # Should show 3.11+
```

### 2) Oracle Instant Client Setup

This project uses `python-oracledb` for Oracle database connections.

**Windows:** See [Oracle Database Setup Guide (Windows)](../CO2Flux/Oracle_Database_Setup_Windows.md)

**Linux/macOS:**
- Install Oracle Instant Client: `/opt/oracle/instantclient_19_26`
- Set environment: `LD_LIBRARY_PATH` must include client path
- Linux symlink workaround: Create `/tmp/ora_compat/libaio.so.1`

### 3) Virtual Environment

From repo root:

```bash
# Create
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

### 4) Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5) Credentials (.env)

**Security:** Never commit real credentials.

Copy template to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your Oracle credentials:
```ini
ORACLE_HOST=your_host
ORACLE_PORT=your_port
ORACLE_SID=your_sid
ORACLE_USER=your_user
ORACLE_PASSWORD=your_password
ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient_19_26
```

---

## Running Scripts

### Phase 1: Data Extraction & Preparation

**Step 1: Analyze Climate Data**
```bash
cd /home/dimitri/PycharmProjects/DigitalTwin
python3 scripts/analyze_climate_data.py
```
- Extracts ~500K timesteps from Oracle
- Performs EDA (missing values, outliers, seasonality)
- Output: `data/analysis/{temperature,humidity}_data.csv`
- Runtime: 5-15 minutes (first run)

**Step 2: Prepare Training Data**
```bash
python3 scripts/prepare_training_data.py
```
- Imputes missing values
- Normalizes features to [0, 1]
- Creates sliding windows for LSTM
- Splits: 70% train / 15% val / 15% test
- Output: numpy arrays in `data/training/`

### Workbook Generators

Update RainForest control & measurement sheets:

```bash
# Update Input sheet (64 control parameters)
python3 scripts/update_input_sheet.py

# Update Output sheet (36 climate sensors)
python3 scripts/update_rainforest_output_sheet.py

# Update auxiliary sheets (humidity, soil temp, etc.)
python3 scripts/update_moss_sheet.py
```

---

## Project Structure

```
DigitalTwin/
├── scripts/                          # Executable scripts
│   ├── analyze_climate_data.py       # Oracle extraction & EDA
│   ├── prepare_training_data.py      # Data normalization for LSTM
│   ├── update_input_sheet.py         # 64 control parameters
│   ├── update_rainforest_output_sheet.py  # 36 sensors
│   ├── update_moss_sheet.py          # Auxiliary measurements
│   └── filter_input_climate_controls.py   # Analysis tool
├── Sensors_Description/              # Inventory & metadata
│   ├── Bio2-Rainforest-Inventory.xlsx      # 36 sensors
│   ├── Bio2-Controls-Inventory-29Jan2026.xlsx  # 64 controls
│   ├── Bio2-Ocean-Inventory.xlsx           # Reference
│   ├── Bio2-Outdoor-Inventory.xlsx         # Reference
│   ├── variables_schema.xlsx               # Input/Output sheets
│   └── output_sheet_notes.md               # Documentation
├── docs/                             # Documentation
│   ├── _INDEX.md                     # Navigation guide
│   ├── CLIMATE_CONTROL_QUICK_START.md
│   ├── CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md
│   └── DATA_PIPELINE_GUIDE.md
├── data/                             # Data directories (auto-created)
│   ├── analysis/                     # EDA outputs
│   └── training/                     # LSTM training data
├── AGENTS.md                         # Detailed project instructions
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## System Overview

### RainForest Climate Control Loop

```
64 Input Parameters          [LSTM Model]          36 Output Sensors
├─ Temperature Setpoints     ──predictor──>       ├─ Temp (18 channels)
├─ Fan Commands                                   └─ RH (18 channels)
└─ Valve/Damper Controls                           (4 towers × heights)
```

### Control Parameters (64 total)
- **Temperature setpoints:** 15
- **Supply fan commands:** 7
- **Valve/damper/occupancy:** 42

### Measurement Sensors (36 total)
- **Temperature (T):** 18 channels
  - 4 towers × 4-5 heights per tower
- **Relative Humidity (RH):** 18 channels
  - 4 towers × 4-5 heights per tower

**Towers:** Mountain, Northeast, Northwest, South
**Heights:** 100, 300, 700, 1300 cm (NE & S also: 2000 cm)

---

## Data Pipeline

### Phase 1 Output

After running both scripts, you'll have:

```
data/
├── analysis/
│   ├── temperature_data.csv          # 500K rows × 18 columns (T)
│   ├── humidity_data.csv             # 500K rows × 18 columns (RH)
│   ├── climate_data_analysis.csv     # Statistical summary
│   └── climate_data_analysis.png     # EDA visualizations
└── training/
    ├── X_train.npy                   # (346K, 12, 36) sequences
    ├── y_train.npy                   # (346K, 36) labels
    ├── X_val.npy                     # (73K, 12, 36)
    ├── y_val.npy                     # (73K, 36)
    ├── X_test.npy                    # (73K, 12, 36)
    ├── y_test.npy                    # (73K, 36)
    ├── normalization_params.json     # Scales for denormalization
    ├── sensor_mapping.json           # Feature name → index
    └── metadata.json                 # Dataset info & stats
```

**Total disk:** ~280 MB

**Next steps:**
- Use numpy arrays to train PyTorch or TensorFlow LSTM
- Denormalize predictions using `normalization_params.json`

---

## Workbook: variables_schema.xlsx

### Input Sheet
**Purpose:** 64 RainForest climate control parameters

**To view:**
1. Open `variables_schema.xlsx`
2. Go to **Input** sheet
3. Filter Column A (Physical quantity) to:
   - ✓ Temperature setpoint
   - ✓ Supply fan command
   - ✓ Cooling valve command
   - ✓ Heating valve command
   - ✓ Economizer / damper control
   - ✓ Valve command / position
   - ✓ Occupancy / schedule command
4. Filter Column G (PDE role) to: ✓ Inventory BIOM=1, BIOMNAME=Rainforest

Result: 64 RainForest control inputs

### Output Sheet
**Purpose:** 36 RainForest climate measurement sensors

**To view:**
1. Open `variables_schema.xlsx`
2. Go to **Output** sheet
3. All 36 rows are already RainForest-only (TRF_ prefix)

Result: 18 Temperature + 18 Relative Humidity channels

---

## Database Configuration

### Oracle Connection Details

**Engine:** `python-oracledb` (thick mode)

**Credentials:** `/home/dimitri/Documents/.env` or project `.env`

**Data source:** `BIOMS.DATAVALUES` table

**Variables:**
- Temperature (AirTempC): `variable_id = 16`
- Relative Humidity (RH): `variable_id = 15`

**Time range:** ~500K timesteps (15 years × 15-minute intervals)

---

## Troubleshooting

### "DPY-3001" Error
- **Cause:** Using thin-mode connection
- **Solution:** Ensure `oracledb.init_oracle_client()` is called with thick mode

### "libaio.so.1" Error (Linux)
- **Cause:** Missing Oracle client library
- **Solution:** Create symlink at `/tmp/ora_compat/libaio.so.1`

### "No module named..." Error
- **Cause:** Dependencies not installed
- **Solution:** `pip install -r requirements.txt`

### Connection timeout
- **Cause:** Wrong host/port/SID credentials
- **Solution:** Verify `.env` file matches your Oracle database

---

## Documentation

- **AGENTS.md** — Full project instructions and technical details
- **docs/_INDEX.md** — Navigation guide for all documentation
- **docs/CLIMATE_CONTROL_QUICK_START.md** — Quick reference
- **docs/CLIMATE_CONTROL_DIGITAL_TWIN_PLAN.md** — Architecture and design
- **docs/DATA_PIPELINE_GUIDE.md** — Detailed pipeline walkthrough
- **Sensors_Description/output_sheet_notes.md** — Output sensor reference

---

## Competition Framework (Future)

**Scoring:**
- Energy efficiency: 40%
- Comfort: 35%
- Stability: 25%

**Submission format:** Docker container + REST API

**Validation:** Digital twin predictions vs. real RainForest sensor data

---

## Related Projects

**Note:** Separated in May 2026 from larger Biosphere 2 initiative.

- **CO2Flux** — CO2 vertical profile analysis
  - Location: `/home/dimitri/PycharmProjects/CO2Flux/`
  - Focus: CO2 influx/outflux on LEO slopes
  - Independent project (separate documentation)

---

## Key Contacts

- **John Adams** — Biosphere 2 Operations (jadamsb2@arizona.edu)
- **Professor Gabitov** — Academic advisor
- **Dimitri Bolt** — Project lead (dimitribolt@arizona.edu)

---

## Implementation Timeline

- **Phase 1 (Weeks 1-12):** Data pipeline, LSTM training, API scaffold, evaluation
- **Phase 2 (Weeks 13-24):** Ensemble models, uncertainty quantification, scenarios
- **Phase 3 (Weeks 25+):** Production deployment, live integration

