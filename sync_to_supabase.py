"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Supabase Sync Engine
Syncs Pipeline Preprocessed Data directly into your Supabase PostgreSQL Tables:
1. prescriptions_raw
2. prescriptions_clean
3. quarantine_records
4. market_share_gold
5. threshold_alerts
===============================================================================
"""

import os
import pandas as pd
from pipeline_runner import run_end_to_end_pipeline
from data_preprocessing import preprocess_pharma_dataset
from data_quality_report import generate_data_quality_report
from config import DATASET_PATH

def export_all_tables_for_supabase():
    print("=" * 80)
    print("RUNNING PIPELINE & EXPORTING TABLES FOR YOUR EXACT SUPABASE SCHEMA")
    print("=" * 80)
    
    # 1. Run Pipeline
    results = run_end_to_end_pipeline(dataset_path=DATASET_PATH)
    
    cleaned_df = results['cleaned_df']
    gold_df = results['gold_df']
    alerts_df = results['active_alerts_df']
    quarantine_df = results['quarantine_df'] if 'quarantine_df' in results else pd.DataFrame()
    raw_df = pd.read_csv(DATASET_PATH)
    
    # Create export directory
    export_dir = "supabase_exports"
    os.makedirs(export_dir, exist_ok=True)
    
    # 2. Save CSV Exports Matching your exact Supabase Table names
    raw_path = os.path.join(export_dir, "prescriptions_raw.csv")
    clean_path = os.path.join(export_dir, "prescriptions_clean.csv")
    quarantine_path = os.path.join(export_dir, "quarantine_records.csv")
    gold_path = os.path.join(export_dir, "market_share_gold.csv")
    alerts_path = os.path.join(export_dir, "threshold_alerts.csv")
    
    raw_df.to_csv(raw_path, index=False)
    cleaned_df.to_csv(clean_path, index=False)
    quarantine_df.to_csv(quarantine_path, index=False)
    gold_df.to_csv(gold_path, index=False)
    alerts_df.to_csv(alerts_path, index=False)
    
    print(f"[SUCCESS] 1. prescriptions_raw.csv ({len(raw_df):,} rows) -> Saved to {raw_path}")
    print(f"[SUCCESS] 2. prescriptions_clean.csv ({len(cleaned_df):,} rows) -> Saved to {clean_path}")
    print(f"[SUCCESS] 3. quarantine_records.csv ({len(quarantine_df):,} rows) -> Saved to {quarantine_path}")
    print(f"[SUCCESS] 4. market_share_gold.csv ({len(gold_df):,} rows) -> Saved to {gold_path}")
    print(f"[SUCCESS] 5. threshold_alerts.csv ({len(alerts_df):,} rows) -> Saved to {alerts_path}")
    print("=" * 80)
    print("ALL 5 SUPABASE TABLES EXPORTED SUCCESSFULLY!")
    print("You can import these CSVs directly into your Supabase Dashboard under 'Tables -> Import CSV'!")
    print("=" * 80)

def push_to_live_supabase(supabase_url: str, supabase_key: str):
    """
    Directly pushes pipeline results into your live Supabase project via Python SDK.
    """
    from supabase import create_client
    print(f"Connecting to Supabase at {supabase_url}...")
    supabase = create_client(supabase_url, supabase_key)
    
    results = run_end_to_end_pipeline()
    gold_df = results['gold_df']
    alerts_df = results['active_alerts_df']
    
    # Chunked batch upsert into market_share_gold
    batch_size = 500
    gold_records = gold_df.to_dict(orient="records")
    for i in range(0, len(gold_records), batch_size):
        chunk = gold_records[i:i + batch_size]
        supabase.table("market_share_gold").upsert(chunk).execute()
        print(f"Pushed batch {i//batch_size + 1} ({len(chunk)} rows) to market_share_gold")
        
    # Chunked batch upsert into threshold_alerts
    alert_records = alerts_df.to_dict(orient="records")
    for i in range(0, len(alert_records), batch_size):
        chunk = alert_records[i:i + batch_size]
        supabase.table("threshold_alerts").upsert(chunk).execute()
        print(f"Pushed batch {i//batch_size + 1} ({len(chunk)} rows) to threshold_alerts")

if __name__ == "__main__":
    export_all_tables_for_supabase()
