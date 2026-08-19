-- ===============================================================================
-- Cognizant (CTS) Nurture Placement Hackathon - Supabase PostgreSQL Trigger Script
-- Replaces Prefect Automation with Native PostgreSQL Database Triggers
-- Architecture: Tier 1 DB Trigger (Silver Cleaning) + Tier 2 Python Analytics Worker (Gold Marts)
-- Strict Parity with Python Validation: No CURRENT_DATE fallback, Quarantines invalid dates & missing categoricals
-- ===============================================================================

-- 1. BRONZE LAYER TABLE: Raw Prescription Feed Ingestion
CREATE TABLE IF NOT EXISTS prescriptions_raw (
    raw_id BIGSERIAL PRIMARY KEY,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    date_str TEXT,
    week_number TEXT,
    year_str TEXT,
    region TEXT,
    therapeutic_area TEXT,
    product TEXT,
    brand TEXT,
    trx TEXT,
    nrx TEXT,
    units TEXT
);

-- 2. SILVER LAYER TABLE: Cleaned & Validated Schema
CREATE TABLE IF NOT EXISTS prescriptions_clean (
    clean_id BIGSERIAL PRIMARY KEY,
    raw_id BIGINT REFERENCES prescriptions_raw(raw_id),
    iso_date DATE NOT NULL,
    year_week VARCHAR(16) NOT NULL,
    clean_region VARCHAR(64) NOT NULL,
    clean_therapeutic_area VARCHAR(64) NOT NULL,
    clean_product VARCHAR(64) NOT NULL,
    clean_brand VARCHAR(64) NOT NULL,
    clean_trx NUMERIC(12, 2),
    clean_nrx NUMERIC(12, 2),
    clean_units NUMERIC(12, 2),
    is_negative_trx BOOLEAN DEFAULT FALSE,
    is_missing_flag BOOLEAN DEFAULT FALSE,
    is_nrx_gt_trx_error BOOLEAN DEFAULT FALSE
);

-- 3. QUARANTINE LOG TABLE: Invalid / Rejected Records
CREATE TABLE IF NOT EXISTS quarantine_records (
    quarantine_id BIGSERIAL PRIMARY KEY,
    raw_id BIGINT REFERENCES prescriptions_raw(raw_id),
    quarantined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rejection_reason TEXT,
    raw_payload JSONB
);

-- 4. GOLD LAYER TABLE: Market Share & Share Shifts Star Schema Mart
CREATE TABLE IF NOT EXISTS market_share_gold (
    gold_id BIGSERIAL PRIMARY KEY,
    year_week VARCHAR(16) NOT NULL,
    clean_region VARCHAR(64) NOT NULL,
    clean_therapeutic_area VARCHAR(64) NOT NULL,
    clean_brand VARCHAR(64) NOT NULL,
    brand_trx NUMERIC(14, 2),
    total_segment_trx NUMERIC(14, 2),
    market_share_trx_pct NUMERIC(6, 3),
    market_share_nrx_pct NUMERIC(6, 3),
    prev_market_share_pp NUMERIC(6, 3),
    share_shift_pp NUMERIC(6, 3),
    share_shift_bps NUMERIC(8, 2),
    momentum_ratio NUMERIC(6, 3),
    prev_3wk_rolling_mean_pp NUMERIC(6, 3),
    statistical_z_score NUMERIC(6, 3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year_week, clean_region, clean_therapeutic_area, clean_brand)
);

-- 5. REAL-TIME EVIDENCE-BASED THRESHOLD ALERT TABLE
CREATE TABLE IF NOT EXISTS threshold_alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    alert_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    year_week VARCHAR(16) NOT NULL,
    clean_region VARCHAR(64) NOT NULL,
    clean_therapeutic_area VARCHAR(64) NOT NULL,
    clean_brand VARCHAR(64) NOT NULL,
    alert_type VARCHAR(32) NOT NULL, -- STATISTICAL_ANOMALY, POSITIVE_SHARE_SHIFT, NEGATIVE_SHARE_SHIFT
    severity_level VARCHAR(16) NOT NULL, -- CRITICAL, SIGNIFICANT, WATCH, NORMAL
    previous_share_pp NUMERIC(6, 3),
    current_share_pp NUMERIC(6, 3),
    share_shift_pp NUMERIC(6, 3),
    share_shift_bps NUMERIC(8, 2),
    z_score NUMERIC(6, 3),
    isolation_forest_score NUMERIC(6, 3),
    triggered_techniques TEXT,
    executive_brief TEXT
);

-- -------------------------------------------------------------------------------
-- POSTGRESQL DATABASE TRIGGER FUNCTION (TIER 1 SILVER DATA CLEANING)
-- -------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_weekly_prescriptions_trg()
RETURNS TRIGGER AS $$
DECLARE
    parsed_dt DATE := NULL;
    extracted_yw TEXT := NULL;
    is_valid_date BOOLEAN := FALSE;
    is_missing_cat BOOLEAN := FALSE;
    rej_reason TEXT := '';
BEGIN
    -- 1. Multi-Format Date Parsing (No CURRENT_DATE Fallback)
    IF NEW.date_str IS NOT NULL AND TRIM(NEW.date_str) <> '' THEN
        BEGIN
            parsed_dt := TO_DATE(TRIM(NEW.date_str), 'YYYY-MM-DD');
            is_valid_date := TRUE;
        EXCEPTION WHEN OTHERS THEN
            BEGIN
                parsed_dt := TO_DATE(TRIM(NEW.date_str), 'YYYY/MM/DD');
                is_valid_date := TRUE;
            EXCEPTION WHEN OTHERS THEN
                BEGIN
                    parsed_dt := TO_DATE(TRIM(NEW.date_str), 'DD/MM/YYYY');
                    is_valid_date := TRUE;
                EXCEPTION WHEN OTHERS THEN
                    BEGIN
                        parsed_dt := TO_DATE(TRIM(NEW.date_str), 'MM/DD/YYYY');
                        is_valid_date := TRUE;
                    EXCEPTION WHEN OTHERS THEN
                        is_valid_date := FALSE;
                        parsed_dt := NULL;
                    END;
                END;
            END;
        END;
    END IF;
    
    -- 2. Check Missing Categoricals
    IF NEW.brand IS NULL OR LOWER(TRIM(NEW.brand)) IN ('nan', 'none', 'null', '') OR
       NEW.region IS NULL OR LOWER(TRIM(NEW.region)) IN ('nan', 'none', 'null', '') THEN
        is_missing_cat := TRUE;
    END IF;
    
    -- 3. Quarantine Invalid Records (NO CURRENT_DATE fallback)
    IF NOT is_valid_date OR is_missing_cat THEN
        IF NOT is_valid_date THEN rej_reason := 'INVALID_DATE'; END IF;
        IF is_missing_cat THEN 
            IF rej_reason <> '' THEN rej_reason := rej_reason || ' | '; END IF;
            rej_reason := rej_reason || 'MISSING_CATEGORICAL_FIELD'; 
        END IF;
        
        INSERT INTO quarantine_records (raw_id, rejection_reason, raw_payload)
        VALUES (
            NEW.raw_id, 
            rej_reason, 
            to_jsonb(NEW)
        );
        RETURN NEW;
    END IF;
    
    -- 4. Derive Canonical ISO Year-Week string (e.g. 2025-W50)
    extracted_yw := EXTRACT(YEAR FROM parsed_dt)::TEXT || '-W' || LPAD(EXTRACT(WEEK FROM parsed_dt)::TEXT, 2, '0');
    
    -- 5. Insert into Silver Clean Table
    INSERT INTO prescriptions_clean (
        raw_id, iso_date, year_week, clean_region, clean_therapeutic_area, 
        clean_product, clean_brand, clean_trx, clean_nrx, clean_units, 
        is_negative_trx, is_nrx_gt_trx_error
    )
    VALUES (
        NEW.raw_id,
        parsed_dt,
        extracted_yw,
        TRIM(INITCAP(NEW.region)),
        TRIM(INITCAP(NEW.therapeutic_area)),
        TRIM(NEW.product),
        TRIM(NEW.brand),
        NULLIF(REGEXP_REPLACE(NEW.trx, '[^0-9.-]', '', 'g'), '')::NUMERIC,
        NULLIF(REGEXP_REPLACE(NEW.nrx, '[^0-9.-]', '', 'g'), '')::NUMERIC,
        NULLIF(REGEXP_REPLACE(NEW.units, '[^0-9.-]', '', 'g'), '')::NUMERIC,
        (NULLIF(REGEXP_REPLACE(NEW.trx, '[^0-9.-]', '', 'g'), '')::NUMERIC < 0),
        (NULLIF(REGEXP_REPLACE(NEW.nrx, '[^0-9.-]', '', 'g'), '')::NUMERIC > NULLIF(REGEXP_REPLACE(NEW.trx, '[^0-9.-]', '', 'g'), '')::NUMERIC)
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ATTACH DATABASE TRIGGER TO SUPABASE TABLE
DROP TRIGGER IF EXISTS trg_process_prescriptions ON prescriptions_raw;
CREATE TRIGGER trg_process_prescriptions
AFTER INSERT ON prescriptions_raw
FOR EACH ROW EXECUTE FUNCTION process_weekly_prescriptions_trg();
