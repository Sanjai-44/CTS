"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - API Ingestion & Supabase Trigger Test
Simulates IQVIA / EHR Data Feed Pushing New Week Data via REST API
===============================================================================
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/v1/ingest-weekly-data"

# Sample Payload for New ISO Week 2026-W01 Data
sample_payload = {
    "year_week": "2026-W01",
    "source_vendor": "IQVIA Weekly Prescription Feed",
    "records": [
        {
            "date": "2026-01-05",
            "week_number": 1,
            "year": 2026,
            "region": "Tamil Nadu",
            "therapeutic_area": "Respiratory",
            "product": "Aerovant HFA",
            "brand": "Aerovant Pharma",
            "trx": 4850.0,
            "nrx": 1320.0,
            "units": 5200.0
        },
        {
            "date": "2026-01-05",
            "week_number": 1,
            "year": 2026,
            "region": "Tamil Nadu",
            "therapeutic_area": "Respiratory",
            "product": "Breathex Inhaler",
            "brand": "Breathex Labs",
            "trx": 2100.0,
            "nrx": 580.0,
            "units": 2300.0
        },
        {
            "date": "2026-01-05",
            "week_number": 1,
            "year": 2026,
            "region": "Tamil Nadu",
            "therapeutic_area": "Cardiology",
            "product": "Corvyx TAB",
            "brand": "Corvyx Pharma",
            "trx": 1450.0,
            "nrx": 410.0,
            "units": 1600.0
        },
        {
            "date": "2026-01-05",
            "week_number": 1,
            "year": 2026,
            "region": "Tamil Nadu",
            "therapeutic_area": "Diabetes",
            "product": "Glucera XR",
            "brand": "Glucera Health",
            "trx": 3200.0,
            "nrx": 910.0,
            "units": 3500.0
        }
    ]
}

def send_test_ingestion():
    print("=" * 80)
    print("SIMULATING REAL-WORLD REST API / SUPABASE INGESTION TRIGGER")
    print("=" * 80)
    print(f"Target API Endpoint: {API_URL}")
    print(f"Ingesting New Week Data: {sample_payload['year_week']}")
    print(f"Vendor Source: {sample_payload['source_vendor']}")
    print(f"Records Count: {len(sample_payload['records'])}")
    print("-" * 80)
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=sample_payload, headers={"Content-Type": "application/json"})
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            res_data = response.json()
            print("[SUCCESS] INGESTION & DATABASE TRIGGER COMPLETED SUCCESSFULLY!")
            print(f"[*] Total Response Time: {elapsed:.2f} seconds")
            print(f"[*] Response Summary:")
            print(json.dumps(res_data, indent=2))
        else:
            print(f"[FAIL] API Request Failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Connection error: Could not reach API server on {API_URL}. Ensure api_server.py is running! Error: {e}")

if __name__ == "__main__":
    send_test_ingestion()
