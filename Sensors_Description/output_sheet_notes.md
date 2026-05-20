# RainForest Output Sheet: Climate State Observation Network

## Purpose

The **Output sheet** in `variables_schema.xlsx` contains all RainForest biome state sensors that respond to climate control inputs.

This is the **observation network for the inverse problem**: when you change Input controls (equipment commands, setpoints), these Output sensors measure the resulting climate state changes.

## Structure

**Total sensors: 36 channels**
- **18 Temperature sensors** (T(x,t), AirTempC): measure air temperature
- **18 Relative Humidity sensors** (RH(x,t)): measure relative humidity

**Organized by 4 vertical measurement towers:**
1. **TRF Mountain Tower** (TRF_MTN): 9 sensors (4 Temperature + 4 RH + 1 other)
2. **TRF Northeast Tower** (TRF_NE): 10 sensors (5 Temperature + 5 RH)
3. **TRF Northwest Tower** (TRF_NW): 8 sensors (4 Temperature + 4 RH)
4. **TRF South Tower** (TRF_S): 10 sensors (5 Temperature + 5 RH)

**Heights above surface (per tower):**
- 100 cm (lowest, near ground)
- 300 cm
- 700 cm
- 1300 cm (highest on most towers)
- 2000 cm (only on NE and S towers)

## Column Structure (37 columns, matching CO2 sheet format)

### Physical description (A–B)
- **A**: Physical quantity (e.g., "Air temperature", "Relative humidity")
- **B**: Physical symbol (e.g., "T(x,t)", "RH(x,t)")

### Spatial coordinates (C–F)
- **C**: X-coordinate [m] — *empty, not applicable for single tower*
- **D**: Y-coordinate [m] — *empty, not applicable for single tower*
- **E**: Z-coordinate [m] — height above surface in meters (1.0 m = 100 cm)
- **F**: Height/depth raw — human-readable (e.g., "DLEVEL = 100 cm")

### Role in problem formulation (G–H)
- **G**: "Pointwise state value constraint"
- **H**: "Measured value of the RainForest climate state at observation point (x, z, t); use for calibration, validation, control verification, or data assimilation."

### Source & inventory (I–M)
- **I**: Source system = "RainForest SensorDB inventory"
- **J**: Inventory file = "Bio2-Rainforest-Inventory.xlsx"
- **K**: Inventory sheet = "Sensors"
- **L**: Series ID (Sensor ID from Oracle)
- **M**: Exact source channel name (e.g., "TRF_MTN_100_HMP45")

### Oracle query path (N–Q)
- **N**: Oracle table / query path = "BIOMS.DATAVALUES"
- **O**: Oracle selector (e.g., "dv.sensorid = 96 AND dv.variableid = 16")
- **P**: Time column = "LOCALDATETIME"
- **Q**: Value column = "DATAVALUE"

### Units & conversion (R–T)
- **R**: Unit raw (e.g., "degC", "%")
- **S**: Unit canonical (e.g., "degC", "%")
- **T**: Conversion formula = "identity" (no conversion needed)

### Location & geometry (U–V)
- **U**: Location descriptive (e.g., "TRF Mountain Tower")
- **V**: Location code (abbreviation, e.g., "TRF_MTN")

### Scientific rationale (W)
- **W**: Rationale (e.g., "RainForest state measurement at TRF Mountain Tower DLEVEL = 100 cm")

### Data availability (X–Y)
- **X**: Data window start (first timestamp available in Oracle)
- **Y**: Data window end (last timestamp or "present")

### Technical metadata (Z–AG)
- **Z**: Notes (reference to sensor code)
- **AA**: Ready-to-run SQL query
- **AB**: Unused
- **AC**: Live-tested in Oracle? (Yes/No status)
- **AD**: Oracle variable ID (16 for AirTempC, 15 for RH)
- **AE**: Oracle variable code (AirTempC, RH)
- **AF**: Oracle variable name (Temperature, Relative humidity)
- **AG**: Oracle variable units (degC, %)

## How to use Output sheet

### Extract time series data from Oracle

For any Output row, use the SQL query in column AA to fetch data:

```sql
SELECT
    dv.LOCALDATETIME,
    dv.DATAVALUE
FROM
    bioms.DATAVALUES dv
WHERE
    dv.sensorid = 96
    AND dv.variableid = 16
ORDER BY
    dv.LOCALDATETIME
```

This query structure is identical for all 36 sensors; only the `sensorid` and `variableid` change.

### Link to Input sheet

**(Future work, planned after Output completion)**

Each Input control row can be mapped to one or more Output sensor rows:

**Example mapping:**
- Input: MiscRF1_LowLndTmp (low-land temperature setpoint)
  - Should affect → Output: TRF Mountain Tower 100–300 cm temperature sensors
  - Observable as: increase/decrease in Output T(x,t) values

- Input: Fan or ventilation speed
  - Should affect → Output: all towers' humidity sensors  
  - Observable as: decrease in RH when ventilation is increased

**Mapping process** (to be implemented):
1. Identify which Input values control climate actuators
2. For each Input, determine which Output sensors should respond
3. Build a control verification model:
   - Change Input → predict Output changes → validate against actual sensor data

## Sheet generation

### To regenerate Output sheet from inventory:

```bash
cd /home/dimitri/PycharmProjects/DigitalTwin
python3 scripts/update_rainforest_output_sheet.py
```

This script:
1. Reads `Bio2-Rainforest-Inventory.xlsx` (RainForest inventory)
2. Filters sensor types: temperature (AirTempC) and humidity (RH)
3. Organizes by tower and height
4. Populates all 37 columns with metadata
5. Generates ready-to-run Oracle SQL for each sensor
6. Marks data availability status (live-tested in Oracle)
7. Writes Output sheet in `variables_schema.xlsx`

### To validate Output sheet rows in Oracle:

The generator flag in column AC shows:
- **"Yes — literal AC query validated in Oracle on YYYY-MM-DD"**: row has been tested, data exists
- **"No — validation pending"**: row exists in metadata but data availability not yet confirmed

To manually test a row in Oracle, copy column AA (SQL) and run in SQL client.

## Constants from code

**Climate measurement towers:**
- Mountain Tower: 4 sensors per variable (100, 300, 700, 1300 cm)
- Northeast Tower: 5 sensors per variable (100, 300, 700, 1300, 2000 cm)
- Northwest Tower: 4 sensors per variable (100, 300, 700, 1300 cm)
- South Tower: 5 sensors per variable (100, 300, 700, 1300, 2000 cm)

**Oracle variable IDs:**
- AirTempC: variable_id = 16
- RH: variable_id = 15

**Oracle table:** `BIOMS.DATAVALUES`

## Related documents

- `scripts/update_rainforest_output_sheet.py` — generator script source code
- `Bio2-Rainforest-Inventory.xlsx` — inventory source (Sensors sheet)

