# CTS - Commercial Analytics Market Share & Share-Shift Tracker

Enterprise-grade Commercial Pharmaceutical Analytics Platform built for tracking brand prescription trends, calculating granular market share & week-over-week share shifts (percentage points & basis points), detecting multi-signal statistical/ML anomalies, generating regional alerts, forecasting time-series trajectories with ARIMA, and providing a GenAI commercial assistant.

---

## 🌟 Key Features

- **8-Step Analytical Pipeline**:
  1. Raw Data Ingestion & Audit
  2. Week-Aware Date Disambiguation & 10 Canonical Indian State Normalization
  3. Auditable Data Quality Report (>98% retention)
  4. Market Share Calculation (Full Market vs. Competitive Set Mode, Sum-to-100% Contract)
  5. Week-over-Week Share Shifts (First-Week NULL Rule Enforced)
  6. Dynamic 3-Week Baseline Anomaly Detection (5 distinct techniques including Scikit-Learn `IsolationForest`)
  7. Evidence-Based Regional Alert Engine (`REGIONAL GROWTH SPIKE` and `REGIONAL SHARE DECLINE`)
  8. Persistent Dual-Storage Sync (DuckDB OLAP Cache + Supabase Cloud PostgreSQL)

- **Interactive Streamlit Dashboard**:
  - **Tab 1: Market Trends & Share Trajectory** (Plotly Dark theme)
  - **Tab 2: Regional Share Shift & Alert Breakdown** (Spike vs. Decline analysis)
  - **Tab 3: ARIMA Time-Series Future Forecast** (2–26 week slider, 95% Confidence Intervals, AIC model selection, MAE/RMSE validation)
  - **Tab 4: GenAI Commercial Assistant** (Powered by Google Gemini `gemini-flash-latest`)

- **FastAPI REST API Server**:
  - Production weekly batch ingestion endpoint (`/api/v1/ingest-weekly-data`)
  - On-demand analytics pipeline webhook (`/api/v1/trigger-pipeline`)
  - Live Swagger/OpenAPI documentation (`/docs`)

- **Database Triggers & Sync**:
  - Native PostgreSQL triggers (`process_weekly_prescriptions_trg`)
  - 5-table star schema (`prescriptions_raw`, `prescriptions_clean`, `quarantine_records`, `market_share_gold`, `threshold_alerts`)

---

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/Sanjai-44/CTS.git
cd CTS

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-publishable-key
GEMINI_API_KEY=your-google-gemini-api-key
```

### 3. Run the Applications

- **Streamlit Web Dashboard**:
  ```bash
  streamlit run app.py
  ```
  Accessible at: `http://localhost:8501`

- **FastAPI REST Server**:
  ```bash
  uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
  ```
  Swagger Docs at: `http://localhost:8000/docs`

- **Execute Test Suite**:
  ```bash
  python run_tests.py
  ```

---

## 🧪 Testing

The repository includes a comprehensive 10-point unit and integration test suite:
```bash
python run_tests.py
```
```text
================================================================================
RUNNING V8 COMPREHENSIVE UNIT & INTEGRATION TEST SUITE
================================================================================
  [PASSED] Negative TRX Chargebacks Preserved (No abs)
  [PASSED] Missing Categorical Field Quarantine
  [PASSED] Invalid Date Quarantine (No CURRENT_DATE Fallback)
  [PASSED] Week-Aware Date Disambiguation
  [PASSED] Competitive Set Denominator Propagation
  [PASSED] Configurable Parameters & Detector Isolation
  [PASSED] Evidence-Based Corroborated Alerts
  [PASSED] Scikit-Learn IsolationForest ML Model Execution
  [PASSED] ARIMA Model Selection (AIC) & Dynamic Dates
  [PASSED] Full End-to-End Pipeline Integration Test
================================================================================
TEST RESULTS: 10 PASSED | 0 FAILED | SUCCESS RATIO: 100.0%
================================================================================
```

---

## 📁 Repository Structure

```
├── app.py                     # Streamlit multi-tab analytics dashboard
├── api_server.py              # FastAPI REST API server
├── config.py                  # System & statistical configuration
├── data_preprocessing.py      # Silver layer cleaning & date disambiguation
├── data_quality_report.py     # Auditable DQ metrics engine
├── market_share_engine.py     # Market share computation engine
├── share_shift_engine.py      # WoW percentage point / basis point shifts
├── anomaly_engine.py          # 5-signal ML/statistical anomaly detector
├── alert_engine.py            # Regional growth spike / decline alerts
├── forecasting_engine.py      # ARIMA time-series forecasting engine
├── llm_agent.py               # Google Gemini GenAI assistant
├── pipeline_runner.py         # End-to-end 8-step pipeline orchestrator
├── supabase_client.py         # Supabase PostgreSQL database integration
├── sync_to_supabase.py        # Table export & batch synchronization
├── supabase_triggers.sql      # PostgreSQL DDL & cleaning trigger
├── test_pipeline.py           # Comprehensive unit & integration tests
├── run_tests.py               # Master test suite runner
├── test_api_ingestion.py      # API payload simulation test
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variables template
```
