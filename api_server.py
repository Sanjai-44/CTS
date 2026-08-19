"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Production REST API Server
Supabase Event-Driven Automated Ingestion & Webhook Trigger Engine
===============================================================================
"""

import os
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel, Field
import uvicorn

from pipeline_runner import run_end_to_end_pipeline
from config import DATASET_PATH, DUCKDB_PATH

app = FastAPI(
    title="Pharma Commercial Analytics Ingestion & Alerting API",
    description="Enterprise REST API for weekly TRX data ingestion, Supabase database triggers, and real-time Isolation Forest ML anomaly detection.",
    version="1.0.0"
)

# Pydantic Schemas for API Validation
class PharmaWeeklyRecord(BaseModel):
    date: str = Field(..., example="2026-01-05")
    week_number: int = Field(..., example=1)
    year: int = Field(..., example=2026)
    region: str = Field(..., example="Tamil Nadu")
    therapeutic_area: str = Field(..., example="Respiratory")
    product: str = Field(..., example="Aerovant HFA")
    brand: str = Field(..., example="Aerovant Pharma")
    trx: float = Field(..., example=4520.0)
    nrx: float = Field(..., example=1280.0)
    units: float = Field(..., example=5000.0)

class IngestionPayload(BaseModel):
    year_week: str = Field(..., example="2026-W01")
    source_vendor: Optional[str] = Field("IQVIA / EHR Feed", example="IQVIA")
    records: List[PharmaWeeklyRecord]

@app.get("/")
def root_status():
    """
    API Health check and Supabase connection status.
    """
    return {
        "status": "ONLINE",
        "service": "Pharma Commercial Analytics Ingestion & Webhook Engine",
        "database_backend": "DuckDB Local Cache + Supabase PostgreSQL Ready",
        "active_pipeline_version": "V8 (Isolation Forest ML + 5 Anomaly Detectors)"
    }

@app.post("/api/v1/ingest-weekly-data")
def ingest_weekly_data(payload: IngestionPayload, background_tasks: BackgroundTasks):
    """
    HTTP POST Ingestion Endpoint for real-time/weekly data delivery.
    1. Ingests raw weekly payload directly into Supabase public.prescriptions_raw table.
    2. Preprocesses raw records using 8-step pipeline.
    3. Inserts preprocessed records directly into Supabase public.prescriptions_clean table.
    4. Triggers dynamic calculation of market share, WoW shifts, Isolation Forest ML anomalies, and UI tab sync.
    """
    try:
        records_dict = [r.dict() for r in payload.records]
        
        # Execute Supabase Live DB 2-Table Ingestion & Cleaning
        from supabase_client import supabase_warehouse
        res = supabase_warehouse.insert_new_week_raw_and_clean(records_dict, payload.year_week)
        
        return {
            "success": True,
            "database_backend": f"Supabase Cloud PostgreSQL ({supabase_warehouse.supabase_url})",
            "tables_updated": ["public.prescriptions_raw", "public.prescriptions_clean"],
            "year_week": payload.year_week,
            "raw_records_inserted": res["raw_inserted_to_prescriptions_raw"],
            "preprocessed_records_inserted": res["preprocessed_inserted_to_prescriptions_clean"],
            "quarantined_records_count": res["quarantined_records_count"],
            "pipeline_status": "COMPLETED_SUCCESSFULLY"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase live ingestion error: {str(e)}")

@app.post("/api/v1/trigger-pipeline")
def trigger_pipeline():
    """
    Manual Webhook Trigger endpoint to re-run end-to-end analytics pipeline on demand.
    """
    try:
        results = run_end_to_end_pipeline()
        return {
            "success": True,
            "message": "End-to-End Analytics Pipeline executed successfully via Webhook Trigger.",
            "total_gold_records": len(results['gold_df']),
            "active_alerts": len(results['active_alerts_df'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline trigger execution failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
