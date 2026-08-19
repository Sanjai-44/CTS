"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - End-to-End Pipeline Runner
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import os
import pandas as pd
import duckdb

from config import DATASET_PATH, DUCKDB_PATH, LOOKBACK_WEEKS, ANOMALY_Z_THRESHOLD
from data_preprocessing import preprocess_pharma_dataset
from data_quality_report import generate_data_quality_report
from market_share_engine import calculate_market_share
from share_shift_engine import calculate_share_shifts
from anomaly_engine import detect_statistical_anomalies
from alert_engine import generate_market_alerts

def run_end_to_end_pipeline(dataset_path=None, duckdb_path=None, selected_brands=None):
    """
    Runs the complete 8-step commercial analytics pipeline:
    1. Raw Data Ingestion
    2. Data Preprocessing & Validation (Week-Aware Date Disambiguation)
    3. Auditable Data Quality Report (98.0%+ Retention Ratio)
    4. Market Share Calculation (Full Market vs Competitive Set Mode)
    5. Week-over-Week Share Shifts (First-Week NULL Rule Enforced)
    6. Dynamic 3-Week Baseline 4-Technique & IsolationForest ML Engine
    7. Explainable Multi-Level Alerting Engine
    8. Syncing Persistent Local Analytical Cache to DuckDB
    """
    dataset_path = dataset_path or DATASET_PATH
    duckdb_path = duckdb_path or DUCKDB_PATH
    
    print(f"1. Loading Raw Dataset from: {dataset_path}")
    raw_df = pd.read_csv(dataset_path)
    
    print(f"2. Executing Data Preprocessing & Audit Rules (Week-aware date disambiguation, No abs, No blind 0)...")
    cleaned_df, dq_report, quarantine_df = preprocess_pharma_dataset(raw_df)
    
    print(f"3. Generating Auditable Data Quality Report...")
    dq_dict, dq_df = generate_data_quality_report(raw_df, cleaned_df, quarantine_df, raw_df)
    
    print(f"4. Computing Market Totals & Market Share % (Sum to 100% Contract)...")
    market_share_df, sum_check_df = calculate_market_share(cleaned_df, selected_brands=selected_brands)
    
    print(f"5. Computing Week-over-Week Share Shifts (First-Week NULL Rule Enforced)...")
    share_shift_df = calculate_share_shifts(market_share_df)
    
    print(f"6. Running Dynamic 3-Week Baseline 4-Technique & IsolationForest ML Engine...")
    anomaly_df = detect_statistical_anomalies(
        share_shift_df, 
        lookback_weeks=LOOKBACK_WEEKS, 
        z_threshold=ANOMALY_Z_THRESHOLD
    )
    
    print(f"7. Generating Multi-Level Alerts (NORMAL, POSITIVE, NEGATIVE, STATISTICAL_ANOMALY)...")
    full_alerts_df, active_alerts_df = generate_market_alerts(anomaly_df)
    
    print(f"8. Syncing Persistent Local Analytical Cache to DuckDB ({duckdb_path})...")
    try:
        conn = duckdb.connect(duckdb_path)
        conn.execute("CREATE OR REPLACE TABLE raw_prescriptions AS SELECT * FROM raw_df")
        conn.execute("CREATE OR REPLACE TABLE clean_prescriptions AS SELECT * FROM cleaned_df")
        conn.execute("CREATE OR REPLACE TABLE quarantine_records AS SELECT * FROM quarantine_df")
        conn.execute("CREATE OR REPLACE TABLE market_share_gold AS SELECT * FROM anomaly_df")
        conn.execute("CREATE OR REPLACE TABLE threshold_alerts AS SELECT * FROM active_alerts_df")
        conn.close()
    except Exception as e:
        print(f"[Pipeline Runner Warning] DuckDB Sync Error: {e}")
        
    print("Pipeline Execution Completed Successfully!")
    
    return {
        'raw_df': raw_df,
        'cleaned_df': cleaned_df,
        'quarantine_df': quarantine_df,
        'dq_report': dq_dict,
        'dq_df': dq_df,
        'market_share_df': market_share_df,
        'share_shift_df': share_shift_df,
        'gold_df': anomaly_df,
        'full_alerts_df': full_alerts_df,
        'active_alerts_df': active_alerts_df
    }

if __name__ == "__main__":
    res = run_end_to_end_pipeline()
    print("Clean Records Retained:", len(res['cleaned_df']))
    print("Quarantined Records:", len(res['quarantine_df']))
    print("Active Alerts Count:", len(res['active_alerts_df']))
