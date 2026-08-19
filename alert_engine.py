"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Regional Shift Alert Engine
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd
import numpy as np
from config import SUBSTANTIAL_SHIFT_PP

def generate_threshold_alerts(anomaly_df, substantial_shift_pp=SUBSTANTIAL_SHIFT_PP):
    """
    Generates Clean Region-Wise Growth Spikes and Share Decline Alerts:
    Categorizes alerts into REGIONAL GROWTH SPIKES and REGIONAL SHARE DECLINES based on
    dynamic historical baseline breaches and multi-detector evidence.
    Completely removes technical jargon words like CRITICAL, SEVERE, WATCH.
    """
    df = anomaly_df.copy()
    alerts = []
    
    for idx, row in df.iterrows():
        shift = row.get('share_shift_pp', np.nan)
        z_score = row.get('statistical_z_score', np.nan)
        iforest_score = row.get('isolation_forest_score', 0.0)
        is_iforest_anomaly = row.get('isolation_forest_anomaly', False)
        triggered_techs = row.get('triggered_techniques', 'None')
        
        if pd.isna(shift):
            continue
            
        t1 = row.get('t1_moving_average_anomaly', False)
        t2 = row.get('t2_z_score_anomaly', False)
        t3 = row.get('t3_erosion_anomaly', False)
        t4 = row.get('t4_dynamic_threshold_anomaly', False)
        
        stat_count = sum([t1, t2, t3, t4])
        
        alert_category = 'NORMAL'
        brief = ""
        
        # Qualified Regional Shift Classification
        is_qualified_shift = (stat_count >= 1 or is_iforest_anomaly) and abs(shift) >= substantial_shift_pp
        
        if is_qualified_shift or t3:
            if shift < 0 or t3:
                alert_category = 'REGIONAL SHARE DECLINE'
                brief = f"Regional Share Decline for {row['clean_brand']} in {row['clean_region']} (Shift: {shift:+.2f} pp / {row.get('share_shift_bps', 0.0):+.0f} bps). Current Share: {row.get('market_share_trx_pct', 0.0):.2f}%."
            else:
                alert_category = 'REGIONAL GROWTH SPIKE'
                brief = f"Regional Growth Spike for {row['clean_brand']} in {row['clean_region']} (Shift: {shift:+.2f} pp / {row.get('share_shift_bps', 0.0):+.0f} bps). Current Share: {row.get('market_share_trx_pct', 0.0):.2f}%."
                
        alerts.append({
            'year_week': row['year_week'],
            'clean_region': row['clean_region'],
            'clean_therapeutic_area': row['clean_therapeutic_area'],
            'clean_brand': row['clean_brand'],
            'alert_category': alert_category,
            'alert_type': alert_category,
            'severity_level': alert_category,
            'previous_share_pp': row.get('market_share_trx_pct', 0.0) - shift,
            'current_share_pp': row.get('market_share_trx_pct', 0.0),
            'share_shift_pp': shift,
            'share_shift_bps': row.get('share_shift_bps', 0.0),
            'dynamic_upper_threshold': row.get('dynamic_upper_threshold', np.nan),
            'dynamic_lower_threshold': row.get('dynamic_lower_threshold', np.nan),
            'statistical_z_score': z_score if pd.notna(z_score) else np.nan,
            'isolation_forest_score': iforest_score,
            'triggered_techniques': triggered_techs,
            'executive_brief': brief
        })
        
    full_alerts_df = pd.DataFrame(alerts)
    active_alerts_df = full_alerts_df[full_alerts_df['alert_category'].isin(['REGIONAL GROWTH SPIKE', 'REGIONAL SHARE DECLINE'])].copy() if not full_alerts_df.empty else pd.DataFrame()
    return full_alerts_df, active_alerts_df

# Alias for backward compatibility
generate_market_alerts = generate_threshold_alerts
