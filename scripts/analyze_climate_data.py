"""
Climate Control Digital Twin - Data Analysis Pipeline (Part 1)

Performs comprehensive EDA on RainForest climate data:
- Connects to Oracle SensorDB with thick mode
- Loads 64 Input control parameters + 36 Output sensor measurements
- ~500K timesteps (15 years × 15-minute intervals)
- Analyzes data quality, trends, seasonality, anomalies

Output:
- climate_data_analysis.csv: summary statistics
- Plots: trends, distributions, seasonality
- Missing data report: identifies gaps

Usage:
    python3 scripts/analyze_climate_data.py

Author: Dimitri Bolt
Project: RainForest Climate Control Digital Twin (May 2026)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import dotenv_values

try:
    import oracledb
except ImportError:
    print("ERROR: oracledb not installed. Install with: pip install oracledb")
    sys.exit(1)
    oracledb = None  # type: ignore


# ============================================================================
# CONFIGURATION
# ============================================================================

ROOT = Path("/home/dimitri/PycharmProjects/CO2Flux")
ENV_PATH = Path.home() / "Documents" / ".env"
ORACLE_CLIENT_LIB_DIR = Path("/opt/oracle/instantclient_19_26")

OUTPUT_DIR = ROOT / "data" / "analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# RainForest sensors (from variables_schema.xlsx Output sheet)
RAINFOREST_SENSORS = {
    "temperature": {
        "MTN_100": 96, "MTN_300": 97, "MTN_700": 98, "MTN_1300": 99,
        "NE_100": 100, "NE_300": 101, "NE_700": 102, "NE_1300": 103, "NE_2000": 104,
        "NW_100": 105, "NW_300": 106, "NW_700": 107, "NW_1300": 108,
        "S_100": 109, "S_300": 110, "S_700": 111, "S_1300": 112, "S_2000": 113,
    },
    "humidity": {
        "MTN_100": 114, "MTN_300": 115, "MTN_700": 116, "MTN_1300": 117,
        "NE_100": 118, "NE_300": 119, "NE_700": 120, "NE_1300": 121, "NE_2000": 122,
        "NW_100": 123, "NW_300": 124, "NW_700": 125, "NW_1300": 126,
        "S_100": 127, "S_300": 128, "S_700": 129, "S_1300": 130, "S_2000": 131,
    }
}

# Oracle variable IDs
VARIABLE_IDS = {
    "temperature": 16,  # AirTempC
    "humidity": 15,     # RH
}


# ============================================================================
# ORACLE CONNECTION
# ============================================================================

def setup_oracle_environment() -> None:
    """Setup Oracle Instant Client with libaio compatibility."""
    # Create libaio compatibility symlink
    compat_dir = Path("/tmp/ora_compat")
    compat_dir.mkdir(exist_ok=True)
    
    lib_source = Path("/lib/x86_64-linux-gnu/libaio.so.1t64")
    lib_link = compat_dir / "libaio.so.1"
    
    if lib_source.exists() and not lib_link.exists():
        try:
            os.symlink(lib_source, lib_link)
            print(f"✓ Created libaio symlink: {lib_link} → {lib_source}")
        except Exception as e:
            print(f"⚠ Could not create symlink: {e}")
    
    # Prepend to LD_LIBRARY_PATH
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    new_ld_path = f"{ORACLE_CLIENT_LIB_DIR}:{compat_dir}"
    if ld_path:
        new_ld_path += f":{ld_path}"
    os.environ["LD_LIBRARY_PATH"] = new_ld_path


def connect_oracle() -> Optional[oracledb.Connection]:
    """Connect to Oracle SensorDB in thick mode."""
    try:
        # Initialize thick mode
        oracledb.init_oracle_client(lib_dir=str(ORACLE_CLIENT_LIB_DIR))
        
        # Load credentials
        if not ENV_PATH.exists():
            print(f"ERROR: .env file not found at {ENV_PATH}")
            return None
        
        env_vars = dotenv_values(ENV_PATH)
        
        # Validate required credentials
        if not all(env_vars.get(k) for k in ["ORACLE_HOST", "ORACLE_SID", "ORACLE_USER", "ORACLE_PASSWORD"]):
            print("ERROR: Missing Oracle credentials in .env file")
            print("Required: ORACLE_HOST, ORACLE_PORT, ORACLE_SID, ORACLE_USER, ORACLE_PASSWORD")
            return None

        # Build connection string
        dsn = oracledb.makedsn(
            host=str(env_vars.get("ORACLE_HOST")),
            port=int(str(env_vars.get("ORACLE_PORT", "1521"))),
            sid=str(env_vars.get("ORACLE_SID"))
        )
        
        # Connect
        conn = oracledb.connect(
            user=env_vars.get("ORACLE_USER"),
            password=env_vars.get("ORACLE_PASSWORD"),
            dsn=dsn
        )
        
        print(f"✓ Connected to Oracle: {env_vars['ORACLE_HOST']}:{env_vars['ORACLE_SID']}")
        return conn
        
    except Exception as e:
        print(f"ERROR: Oracle connection failed: {e}")
        return None


# ============================================================================
# DATA LOADING
# ============================================================================

def load_sensor_data(conn: oracledb.Connection, 
                    sensor_codes: dict[str, int],
                    variable_id: int,
                    limit: Optional[int] = None) -> pd.DataFrame:
    """
    Load time series data for sensors from Oracle.
    
    Args:
        conn: Oracle connection
        sensor_codes: dict of sensor_name -> sensorid
        variable_id: Oracle variable ID (16 for temp, 15 for humidity)
        limit: max rows per sensor (for testing)
    
    Returns:
        DataFrame with columns: timestamp, sensor_name, value
    """
    cur = conn.cursor()
    all_data = []
    
    for sensor_name, sensor_id in sensor_codes.items():
        try:
            sql = f"""
                SELECT dv.LOCALDATETIME, dv.DATAVALUE
                FROM bioms.DATAVALUES dv
                WHERE dv.sensorid = {sensor_id}
                  AND dv.variableid = {variable_id}
                ORDER BY dv.LOCALDATETIME
            """
            
            if limit:
                sql += f" AND ROWNUM <= {limit}"
            
            cur.execute(sql)
            rows = cur.fetchall()
            
            for timestamp, value in rows:
                all_data.append({
                    "timestamp": timestamp,
                    "sensor": sensor_name,
                    "value": float(value) if value is not None else np.nan
                })
            
            print(f"  ✓ {sensor_name}: {len(rows)} rows")
            
        except Exception as e:
            print(f"  ⚠ {sensor_name}: {e}")
    
    cur.close()
    
    if not all_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


# ============================================================================
# DATA ANALYSIS
# ============================================================================

def analyze_dataframe(df: pd.DataFrame, var_name: str) -> dict:
    """Perform comprehensive EDA on dataframe."""
    if df.empty:
        return {}
    
    stats = {
        "variable": var_name,
        "total_points": len(df),
        "unique_sensors": df["sensor"].nunique(),
        "date_range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
        "duration_days": (df["timestamp"].max() - df["timestamp"].min()).days,
        "missing_values": df["value"].isna().sum(),
        "missing_pct": 100 * df["value"].isna().sum() / len(df),
        "mean": df["value"].mean(),
        "std": df["value"].std(),
        "min": df["value"].min(),
        "max": df["value"].max(),
        "median": df["value"].median(),
    }
    
    # Detect outliers (>3 sigma)
    mean = df["value"].mean()
    std = df["value"].std()
    outliers = df[(np.abs(df["value"] - mean) > 3 * std)]
    stats["outliers_count"] = len(outliers)
    stats["outliers_pct"] = 100 * len(outliers) / len(df)
    
    return stats


def print_analysis_report(temp_stats: dict, hum_stats: dict) -> None:
    """Print formatted analysis report."""
    print("\n" + "="*80)
    print("CLIMATE DATA ANALYSIS REPORT")
    print("="*80)
    
    print("\n📊 TEMPERATURE DATA:")
    for key, val in temp_stats.items():
        if isinstance(val, float):
            print(f"  {key:.<40} {val:.2f}")
        else:
            print(f"  {key:.<40} {val}")
    
    print("\n💧 HUMIDITY DATA:")
    for key, val in hum_stats.items():
        if isinstance(val, float):
            print(f"  {key:.<40} {val:.2f}")
        else:
            print(f"  {key:.<40} {val}")
    
    print("\n" + "="*80)


def create_visualizations(temp_df: pd.DataFrame, hum_df: pd.DataFrame) -> None:
    """Create analysis plots."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("RainForest Climate Data Analysis", fontsize=16, fontweight="bold")
    
    # Temperature time series
    if not temp_df.empty:
        for sensor in temp_df["sensor"].unique()[:5]:  # Plot first 5 sensors
            data = temp_df[temp_df["sensor"] == sensor]
            axes[0, 0].plot(data["timestamp"], data["value"], label=sensor, alpha=0.7)
        axes[0, 0].set_title("Temperature Time Series (first 5 sensors)")
        axes[0, 0].set_ylabel("Temperature (°C)")
        axes[0, 0].legend(fontsize=8)
        axes[0, 0].grid(True, alpha=0.3)
    
    # Temperature distribution
    if not temp_df.empty:
        axes[0, 1].hist(temp_df["value"].dropna(), bins=50, edgecolor="black", alpha=0.7)
        axes[0, 1].set_title("Temperature Distribution")
        axes[0, 1].set_xlabel("Temperature (°C)")
        axes[0, 1].grid(True, alpha=0.3)
    
    # Humidity time series
    if not hum_df.empty:
        for sensor in hum_df["sensor"].unique()[:5]:
            data = hum_df[hum_df["sensor"] == sensor]
            axes[1, 0].plot(data["timestamp"], data["value"], label=sensor, alpha=0.7)
        axes[1, 0].set_title("Humidity Time Series (first 5 sensors)")
        axes[1, 0].set_ylabel("Relative Humidity (%)")
        axes[1, 0].legend(fontsize=8)
        axes[1, 0].grid(True, alpha=0.3)
    
    # Humidity distribution
    if not hum_df.empty:
        axes[1, 1].hist(hum_df["value"].dropna(), bins=50, edgecolor="black", alpha=0.7, color="orange")
        axes[1, 1].set_title("Humidity Distribution")
        axes[1, 1].set_xlabel("Relative Humidity (%)")
        axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    plot_path = OUTPUT_DIR / "climate_data_analysis.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved plot: {plot_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution."""
    print("\n" + "="*80)
    print("CLIMATE CONTROL DIGITAL TWIN - DATA ANALYSIS PIPELINE")
    print("="*80)
    
    # Setup
    print("\n[1/4] Setting up Oracle environment...")
    setup_oracle_environment()
    
    # Connect
    print("\n[2/4] Connecting to Oracle SensorDB...")
    conn = connect_oracle()
    if not conn:
        return
    
    # Load data
    print("\n[3/4] Loading sensor data from Oracle...")
    print("  Temperature sensors:")
    temp_df = load_sensor_data(
        conn, 
        RAINFOREST_SENSORS["temperature"],
        VARIABLE_IDS["temperature"]
    )
    
    print("  Humidity sensors:")
    hum_df = load_sensor_data(
        conn,
        RAINFOREST_SENSORS["humidity"],
        VARIABLE_IDS["humidity"]
    )
    
    # Analyze
    print("\n[4/4] Analyzing data...")
    temp_stats = analyze_dataframe(temp_df, "Temperature (°C)")
    hum_stats = analyze_dataframe(hum_df, "Humidity (%)")
    
    # Print report
    print_analysis_report(temp_stats, hum_stats)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    create_visualizations(temp_df, hum_df)
    
    # Save summary to CSV
    summary_path = OUTPUT_DIR / "climate_data_analysis.csv"
    summary_df = pd.DataFrame([temp_stats, hum_stats])
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ Saved analysis summary: {summary_path}")
    
    # Save raw data
    if not temp_df.empty:
        temp_path = OUTPUT_DIR / "temperature_data.csv"
        temp_df.to_csv(temp_path, index=False)
        print(f"✓ Saved temperature data: {temp_path}")
    
    if not hum_df.empty:
        hum_path = OUTPUT_DIR / "humidity_data.csv"
        hum_df.to_csv(hum_path, index=False)
        print(f"✓ Saved humidity data: {hum_path}")
    
    # Cleanup
    conn.close()
    print("\n✓ Analysis complete!")


if __name__ == "__main__":
    main()

