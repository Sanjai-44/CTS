"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Data Quality Audit Report Engine
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd

def generate_data_quality_report(raw_df, cleaned_df, quarantine_df, full_processed_df):
    """Generates an auditable, structured Data Quality Summary Report dictionary and DataFrame."""
    total_raw = len(raw_df)
    valid_cnt = len(cleaned_df)
    quarantine_cnt = len(quarantine_df)
    
    valid_pct = (valid_cnt / total_raw * 100.0) if total_raw > 0 else 0.0
    quarantine_pct = (quarantine_cnt / total_raw * 100.0) if total_raw > 0 else 0.0
    
    missing_trx = full_processed_df['clean_trx'].isna().sum() if 'clean_trx' in full_processed_df else 0
    missing_nrx = full_processed_df['clean_nrx'].isna().sum() if 'clean_nrx' in full_processed_df else 0
    missing_units = full_processed_df['clean_units'].isna().sum() if 'clean_units' in full_processed_df else 0
    
    negative_trx_cnt = full_processed_df['is_negative_trx'].sum() if 'is_negative_trx' in full_processed_df else 0
    nrx_gt_trx_cnt = full_processed_df['is_nrx_gt_trx_error'].sum() if 'is_nrx_gt_trx_error' in full_processed_df else 0
    duplicate_cnt = full_processed_df['is_duplicate'].sum() if 'is_duplicate' in full_processed_df else 0
    
    report_dict = {
        'total_raw_records': total_raw,
        'valid_cleaned_records': valid_cnt,
        'valid_percentage': round(valid_pct, 2),
        'quarantined_records': quarantine_cnt,
        'quarantine_percentage': round(quarantine_pct, 2),
        'missing_trx_count': missing_trx,
        'missing_nrx_count': missing_nrx,
        'missing_units_count': missing_units,
        'negative_trx_count': negative_trx_cnt,
        'nrx_gt_trx_violations': nrx_gt_trx_cnt,
        'duplicate_records_count': duplicate_cnt,
        'canonical_regions_count': cleaned_df['clean_region'].nunique() if 'clean_region' in cleaned_df else 0,
        'unique_brands_count': cleaned_df['clean_brand'].nunique() if 'clean_brand' in cleaned_df else 0,
        'therapeutic_areas_count': cleaned_df['clean_therapeutic_area'].nunique() if 'clean_therapeutic_area' in cleaned_df else 0
    }
    
    report_df = pd.DataFrame([
        {'Metric': 'Total Raw Records', 'Count': total_raw, 'Details': '100% Raw Ingestion'},
        {'Metric': 'Valid Cleaned Records', 'Count': valid_cnt, 'Details': f"{valid_pct:.2f}% Silver Layer Retention"},
        {'Metric': 'Quarantined Invalid Records', 'Count': quarantine_cnt, 'Details': f"{quarantine_pct:.2f}% Routed to Quarantine"},
        {'Metric': 'Missing TRX Values', 'Count': missing_trx, 'Details': 'Imputed via Segment Median'},
        {'Metric': 'Negative TRX Records', 'Count': negative_trx_cnt, 'Details': 'Preserved Chargeback Magnitude Flagged'},
        {'Metric': 'NRx > TRx Violations', 'Count': nrx_gt_trx_cnt, 'Details': 'Isolated in Quarantine Log'},
        {'Metric': 'Duplicate Composite Keys', 'Count': duplicate_cnt, 'Details': 'Deduplicated via Composite Key'}
    ])
    
    return report_dict, report_df
