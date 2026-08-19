"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Preprocessing & Quality Module
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import datetime
import pandas as pd
import numpy as np

DATE_FORMATS = [
    '%Y-%m-%d', '%Y/%m/%d', '%d-%b-%Y', '%b %d, %Y'
]

REGION_MAPPING = {
    'tn': 'Tamil Nadu', 'tamil nadu': 'Tamil Nadu', 'tamil ndu': 'Tamil Nadu', 'tamilnadu': 'Tamil Nadu', 'tn_state': 'Tamil Nadu',
    'w. bengal': 'West Bengal', 'west bengal': 'West Bengal', 'westbengal': 'West Bengal',
    'andhra pradesh': 'Andhra Pradesh', 'andhrapradesh': 'Andhra Pradesh',
    'karnataka': 'Karnataka', 'karnatka': 'Karnataka', 'kerala': 'Kerala',
    'rajasthan': 'Rajasthan', 'maharashtra': 'Maharashtra', 'delhi': 'Delhi',
    'gujarat': 'Gujarat', 'telangana': 'Telangana'
}

def clean_str_val(val):
    """
    Cleans string input and returns None for missing/null/nan string representations.
    Prevents literal string 'nan' or 'Nan' from slipping into clean dataset.
    """
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s.lower() in ['nan', 'none', 'null', '']:
        return None
    return s

def parse_iso_date_with_week_hint(d_val, week_hint=None):
    """
    Week-Aware Date Disambiguation:
    For ambiguous dates (e.g. 10/03/2025), tests both %m/%d/%Y (Oct 3) and %d/%m/%Y (Mar 10),
    calculates sequential week index for both, and selects the date interpretation consistent with raw week_number hint.
    """
    cleaned_d = clean_str_val(d_val)
    if not cleaned_d:
        return None
        
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(cleaned_d, fmt)
        except ValueError:
            pass
            
    dt_mdy = None
    dt_dmy = None
    
    for fmt in ['%m/%d/%Y', '%m-%d-%Y']:
        try: dt_mdy = datetime.datetime.strptime(cleaned_d, fmt); break
        except ValueError: pass
        
    for fmt in ['%d/%m/%Y', '%d-%m-%Y']:
        try: dt_dmy = datetime.datetime.strptime(cleaned_d, fmt); break
        except ValueError: pass
        
    if dt_mdy and not dt_dmy: return dt_mdy
    if dt_dmy and not dt_mdy: return dt_dmy
    if not dt_mdy and not dt_dmy: return None
    
    if week_hint is not None and not pd.isna(week_hint):
        try:
            raw_w = int(str(week_hint).strip())
            
            y1, w1, _ = dt_mdy.isocalendar()
            seq1 = ((y1 - 2022) * 52) + w1
            
            y2, w2, _ = dt_dmy.isocalendar()
            seq2 = ((y2 - 2022) * 52) + w2
            
            diff1 = min(abs(raw_w - w1), abs(raw_w - seq1))
            diff2 = min(abs(raw_w - w2), abs(raw_w - seq2))
            
            return dt_mdy if diff1 <= diff2 else dt_dmy
        except ValueError:
            pass
            
    return dt_mdy

def normalize_region_name(r_val):
    """Normalizes dirty regional state names into 10 canonical Indian states."""
    cleaned_r = clean_str_val(r_val)
    if not cleaned_r:
        return 'Unknown'
    clean_str = cleaned_r.lower()
    return REGION_MAPPING.get(clean_str, cleaned_r.title())

def preprocess_pharma_dataset(raw_df):
    """
    Executes Data Preprocessing & Quality Pipeline:
    1. Week-Aware Date Disambiguation & ISO calendar week extraction
    2. Strict Missing Categorical Detection: Rejects literal "nan"/"none"/missing into Quarantine
    3. 10-state canonical entity normalization
    4. Numeric casting & Preserved Chargebacks (NO abs on negative TRX)
    5. Segment Median Imputation for valid numeric missing fields (NO blind 0.0 fillna)
    6. NRx > TRx Validation & Composite Key Deduplication
    7. Quarantine Dataset Creation
    """
    df = raw_df.copy()
    
    # 1. Clean Categorical Fields BEFORE string conversion (prevents "nan" literal string issue)
    df['raw_region'] = df['region'].apply(clean_str_val)
    df['raw_ta'] = df['therapeutic_area'].apply(clean_str_val)
    df['raw_product'] = df['product'].apply(clean_str_val)
    df['raw_brand'] = df['brand'].apply(clean_str_val)
    
    # Flag missing categoricals
    df['is_missing_categorical'] = (
        df['raw_region'].isna() |
        df['raw_ta'].isna() |
        df['raw_product'].isna() |
        df['raw_brand'].isna()
    )
    
    # 2. Week-Aware Date Parsing & Calendar Week Extraction
    parsed_dates = []
    for idx, row in df.iterrows():
        w_hint = row.get('week_number', None)
        parsed_dates.append(parse_iso_date_with_week_hint(row['date'], week_hint=w_hint))
        
    df['parsed_date'] = parsed_dates
    df['iso_date'] = df['parsed_date'].apply(lambda d: d.strftime('%Y-%m-%d') if d else None)
    
    def extract_year_week(dt):
        if not dt: return None, None, None
        iso_year, iso_week, _ = dt.isocalendar()
        # ISO week numbers are strictly bounded between 1 and 52 for every calendar year
        iso_w_clamped = max(1, min(52, int(iso_week)))
        return iso_year, iso_w_clamped, f"{iso_year}-W{iso_w_clamped:02d}"
        
    yw_info = df['parsed_date'].apply(extract_year_week)
    df['iso_year'] = [x[0] for x in yw_info]
    df['iso_week'] = [x[1] for x in yw_info]
    df['year_week'] = [x[2] for x in yw_info]
    
    # 3. Smart Sequential & ISO Week Mismatch Validation
    def validate_week_semantics(row):
        if pd.isna(row['iso_week']) or 'week_number' not in row or pd.isna(row['week_number']):
            return False
        try:
            raw_w = int(str(row['week_number']).strip())
            iso_w = int(row['iso_week'])
            iso_y = int(row['iso_year'])
            
            expected_seq_w = ((iso_y - 2022) * 52) + iso_w
            
            is_valid_iso = abs(raw_w - iso_w) <= 1
            is_valid_seq = abs(raw_w - expected_seq_w) <= 2
            
            return not (is_valid_iso or is_valid_seq)
        except ValueError:
            return True
            
    df['is_week_mismatch'] = df.apply(validate_week_semantics, axis=1)
    
    # 4. Canonical Region Normalization
    df['clean_region'] = df['raw_region'].apply(normalize_region_name)
    df['clean_therapeutic_area'] = df['raw_ta'].apply(lambda s: str(s).title() if (pd.notna(s) and s) else 'Unknown')
    df['clean_product'] = df['raw_product'].apply(lambda s: str(s).title() if (pd.notna(s) and s) else 'Unknown')
    df['clean_brand'] = df['raw_brand'].apply(lambda s: str(s).title() if (pd.notna(s) and s) else 'Unknown')
    
    # 5. Numeric Casting & Quality Flags
    def clean_num(val):
        cleaned_s = clean_str_val(val)
        if not cleaned_s: return np.nan
        val_s = cleaned_s.replace(',', '')
        try: return float(val_s)
        except ValueError: return np.nan
        
    df['clean_trx'] = df['trx'].apply(clean_num)
    df['clean_nrx'] = df['nrx'].apply(clean_num)
    df['clean_units'] = df['units'].apply(clean_num)
    
    df['is_negative_trx'] = df['clean_trx'] < 0
    df['is_missing_numeric'] = df['clean_trx'].isna() | df['clean_nrx'].isna() | df['clean_units'].isna()
    df['is_nrx_gt_trx_error'] = (df['clean_nrx'] > df['clean_trx']) & (df['clean_trx'] > 0)
    
    comp_keys = ['iso_date', 'clean_region', 'clean_therapeutic_area', 'clean_product', 'clean_brand']
    df['is_duplicate'] = df.duplicated(subset=comp_keys, keep='first')
    
    quarantine_mask = (
        df['parsed_date'].isna() |
        df['is_missing_categorical'] |
        (df['clean_region'] == 'Unknown') |
        (df['clean_brand'].isin(['Unknown', 'Nan', 'nan', ''])) |
        df['is_nrx_gt_trx_error'] |
        df['is_duplicate'] |
        df['is_week_mismatch']
    )
    
    quarantine_df = df[quarantine_mask].copy()
    
    def assign_rejection_reason(row):
        reasons = []
        if pd.isna(row['parsed_date']): reasons.append('INVALID_DATE')
        if row['is_missing_categorical']: reasons.append('MISSING_CATEGORICAL_FIELD')
        if row['clean_region'] == 'Unknown': reasons.append('UNKNOWN_REGION')
        if row['clean_brand'] in ['Unknown', 'Nan', 'nan', '']: reasons.append('UNKNOWN_BRAND')
        if row['is_nrx_gt_trx_error']: reasons.append('NRX_GREATER_THAN_TRX')
        if row['is_duplicate']: reasons.append('DUPLICATE_RECORD')
        if row['is_week_mismatch']: reasons.append('WEEK_DATE_MISMATCH')
        return " | ".join(reasons) if reasons else 'DATA_QUALITY_ERROR'
        
    if not quarantine_df.empty:
        quarantine_df['rejection_reason'] = quarantine_df.apply(assign_rejection_reason, axis=1)
        
    cleaned_df = df[~quarantine_mask].copy()
    
    for col in ['clean_trx', 'clean_nrx', 'clean_units']:
        if col in cleaned_df.columns and cleaned_df[col].isna().any():
            median_map = cleaned_df.groupby(['clean_region', 'clean_therapeutic_area', 'clean_brand'])[col].transform('median')
            cleaned_df[col] = cleaned_df[col].fillna(median_map)
            
    audit_report = {
        'total_raw_records': len(raw_df),
        'clean_records_retained': len(cleaned_df),
        'quarantined_records_count': len(quarantine_df),
        'duplicate_composite_keys_count': df['is_duplicate'].sum(),
        'missing_categorical_count': df['is_missing_categorical'].sum(),
        'negative_trx_chargebacks_count': df['is_negative_trx'].sum(),
        'nrx_gt_trx_errors_count': df['is_nrx_gt_trx_error'].sum(),
        'week_mismatch_count': df['is_week_mismatch'].sum()
    }
    
    return cleaned_df, audit_report, quarantine_df
