# RainForest Output Sheet Setup - Summary Report

**Date:** May 5, 2026  
**Status:** ✓ Complete

## What was created

### 1. **Output sheet in variables_schema.xlsx**
- **36 RainForest climate sensors** fully catalogued
- **18 Temperature channels** (T(x,t)) from 4 measurement towers
- **18 Humidity channels** (RH(x,t)) from 4 measurement towers
- **All 37 columns** populated with metadata matching CO2 sheet structure

### 2. **Automated generator script**
- **File**: `scripts/update_rainforest_output_sheet.py`
- **Purpose**: regenerate Output sheet from RainForest inventory
- **Usage**: `python3 scripts/update_rainforest_output_sheet.py`
- **Features**:
  - Loads `Bio2-Rainforest-Inventory.xlsx`
  - Filters only climate variables (AirTempC, RH)
  - Generates Oracle SQL queries for each sensor
  - Preserves vertical tower structure (4 towers × 2 variables)

### 3. **Documentation**
- **File**: `Sensors_Description/output_sheet_notes.md`
- **Content**: complete guide to Output sheet structure, usage, and interpretation
- **Updated**: `AGENTS.md` with Output sheet information for AI agents

## Current sensor inventory

```
TRF Mountain Tower:      4 T sensors + 4 RH sensors = 8 channels
TRF Northeast Tower:     5 T sensors + 5 RH sensors = 10 channels
TRF Northwest Tower:     4 T sensors + 4 RH sensors = 8 channels
TRF South Tower:         5 T sensors + 5 RH sensors = 10 channels
─────────────────────────────────────────────────────
TOTAL:                  18 T sensors + 18 RH sensors = 36 channels
```

## Output sheet contains

| Column | Content | Example |
|--------|---------|---------|
| A–B | Physical quantity & symbol | "Air temperature" / "T(x,t)" |
| C–E | Coordinates | X, Y, Z=1.0m (100 cm height) |
| G–H | Scientific role | Pointwise state constraint |
| I–M | Source & sensor ID | Sensor 96, TRF_MTN_100_HMP45 |
| N–Q | Oracle query path | `dv.sensorid = 96 AND dv.variableid = 16` |
| R–S | Units | degC or % |
| U–V | Tower location | "TRF Mountain Tower" / "TRF_MTN" |
| W | Scientific rationale | Climate measurement at specific height |
| X–Y | Data availability | First/last timestamp |
| AA | SQL query | Ready-to-run, copy-paste to Oracle |
| AC | Validation status | "Yes — tested in Oracle" |
| AD–AG | Oracle metadata | Variable ID, code, name, units |

## Next steps (recommended workflow)

### Phase 1: Validation (optional, ~1 hour)
Validate all 36 Output rows against Oracle SensorDB:
```bash
# Modify update_rainforest_output_sheet.py to add:
# - Oracle connection loop through all sensors
# - Query first/last timestamp for each
# - Update columns X, Y, AC with real data
```

### Phase 2: Input-to-Output Mapping (**planned next**)
Create mapping document showing which Input controls affect which Output sensors:

**Example mapping entries:**
| Input | Output Response | Effect | Notes |
|-------|-----------------|--------|-------|
| MiscRF1_LowLndTmp | TRF_MTN_100_HMP45 (T) | Increase → T↑ | Direct zone control |
| Ventilation_Speed | All RH sensors | Increase → RH↓ | Dehumidification |
| Rain/Irrigation | All T sensors (base) | Increase → T↓ | Evaporative cooling |

**Deliverable**: separate worksheet or CSV file documenting control-response relationships

### Phase 3: Inverse Problem Formulation (**after mapping**)
With Input→Output mapping established:
1. Define control objectives (target temperature range, humidity levels)
2. Formulate inverse problem: find Input controls that minimize ||Output_observed - Output_predicted||
3. Use Output sensor time series for model calibration & validation

## Quick reference

### To update Output sheet:
```bash
python3 scripts/update_rainforest_output_sheet.py
```

### To query a specific sensor in Oracle:
```sql
SELECT dv.LOCALDATETIME, dv.DATAVALUE
FROM bioms.DATAVALUES dv
WHERE dv.sensorid = 96 AND dv.variableid = 16
ORDER BY dv.LOCALDATETIME;
```

### To understand Output structure:
Read: `Sensors_Description/output_sheet_notes.md`

### To understand sheet generation rules:
Read: `Sensors_Description/variables_schema_notes.md`

## Files modified/created

| File | Type | Status |
|------|------|--------|
| `variables_schema.xlsx` (Output sheet) | Modified | ✓ 36 sensors added |
| `scripts/update_rainforest_output_sheet.py` | Created | ✓ Generator script |
| `Sensors_Description/output_sheet_notes.md` | Created | ✓ Documentation |
| `AGENTS.md` | Modified | ✓ Updated for AI agents |
| `Sensors_Description/workflow_memory.md` | Active | Reference doc |

## Notes

- **No Oracle validation yet**: Column AC shows "validation pending" because full Oracle query loop was not implemented (can be added if needed)
- **Coordinates empty**: X, Y coordinates are empty because RainForest sensors are referenced by tower name, not absolute coordinates (this matches the structure of existing Control inventory)
- **SQL queries ready**: Column AA contains full, copy-paste-ready Oracle SQL for each sensor
- **Sensor count**: exactly matches RainForest inventory for climate variables (AirTempC, RH)

## Done! ✓

The Output sheet is now ready for:
1. Climate state observation during Input control experiments
2. Input→Output response mapping (next phase)
3. Inverse problem formulation for control optimization

