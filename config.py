"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - System Configuration
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env environment variables if present
dotenv_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(dotenv_path):
    with open(dotenv_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

# File Paths
DATASET_PATH = os.path.join(BASE_DIR, "synthetic_pharma_market_data_no_target (2).csv")
DUCKDB_PATH = os.path.join(BASE_DIR, "pharma_warehouse.duckdb")

# Credential Helper (Supports both .env / os.environ and Streamlit Cloud st.secrets)
def get_secret(key: str, default: str = "") -> str:
    # 1. Direct environment variable
    val = os.environ.get(key)
    if val:
        return val
    # 2. Streamlit Cloud Secrets (st.secrets)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default

# Supabase & Gemini Credentials
SUPABASE_URL = get_secret("SUPABASE_URL", "https://rtaeoyzaghgeluqouboa.supabase.co")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "sb_publishable_OAjEA7Pu8cl54oW-YJzdig_VqGztdwi")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")

# Centralized Statistical & Model Configuration Parameters
LOOKBACK_WEEKS = 3
ANOMALY_Z_THRESHOLD = 3.0
MA_DEV_FACTOR = 2.0
ENVELOPE_STD_FACTOR = 3.0
ISOLATION_FOREST_CONTAMINATION = 0.04
SUBSTANTIAL_SHIFT_PP = 1.5

