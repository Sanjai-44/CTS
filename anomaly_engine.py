"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Statistical & ML Anomaly Engine
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd
import numpy as np
from config import LOOKBACK_WEEKS, ANOMALY_Z_THRESHOLD, MA_DEV_FACTOR, ENVELOPE_STD_FACTOR, ISOLATION_FOREST_CONTAMINATION

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

def compute_robust_mad_zscore(shift, rolling_median, rolling_mad):
    """
    Computes Robust Standardized Z-Score using Median Absolute Deviation (MAD):
    Z_MAD = 0.6745 * (shift - median) / MAD
    Uses a minimal MAD floor (0.20 pp) to prevent division by zero in low-volatility regimes.
    """
    if pd.isna(shift) or pd.isna(rolling_median):
        return np.nan
    mad_val = max(rolling_mad, 0.20) if pd.notna(rolling_mad) else 0.20
    return (0.6745 * (shift - rolling_median)) / mad_val

def detect_statistical_anomalies(
    share_shift_df, 
    lookback_weeks=LOOKBACK_WEEKS, 
    z_threshold=ANOMALY_Z_THRESHOLD,
    ma_dev_factor=MA_DEV_FACTOR,
    envelope_std_factor=ENVELOPE_STD_FACTOR,
    iforest_contamination=ISOLATION_FOREST_CONTAMINATION
):
    """
    5-Signal Dynamic Baseline & Machine Learning Anomaly Detection Engine:
    1. Previous-Weeks-Only Baseline (t-1, t-2, t-3). Current week t NEVER calculates its own threshold.
    2. All detection thresholds passed as explicit configuration parameters.
    3. 5 Genuinely Distinct Detectors:
       - T1 Moving-Average Trend Deviation: Rate of shift change relative to rolling trend velocity
       - T2 Configured Robust Z-Score Spike: |Z_MAD| >= z_threshold
       - T3 Consecutive Share Erosion: 3 consecutive weekly share drops
       - T4 Dynamic Volatility Envelope Breach: Shift outside dynamic u3 +- envelope_std_factor * sigma3
       - T5 Isolation Forest ML Model: Unsupervised multi-feature ML model
    """
    df = share_shift_df.copy()
    group_cols = ['clean_region', 'clean_therapeutic_area', 'clean_brand']
    
    # 1. Compute Rolling Mean, Std, Median, and MAD over PREVIOUS WEEKS ONLY
    shifted_shifts = df.groupby(group_cols)['share_shift_pp'].shift(1)
    df['_group_key'] = df[group_cols[0]] + '_' + df[group_cols[1]] + '_' + df[group_cols[2]]
    
    rolling_prev_mean = shifted_shifts.groupby(df['_group_key']).rolling(window=lookback_weeks, min_periods=2).mean().reset_index(level=0, drop=True)
    rolling_prev_std = shifted_shifts.groupby(df['_group_key']).rolling(window=lookback_weeks, min_periods=2).std().reset_index(level=0, drop=True)
    rolling_prev_median = shifted_shifts.groupby(df['_group_key']).rolling(window=lookback_weeks, min_periods=2).median().reset_index(level=0, drop=True)
    
    def calc_mad(arr):
        valid = arr[~np.isnan(arr)]
        if len(valid) < 2: return np.nan
        med = np.median(valid)
        return np.median(np.abs(valid - med))
        
    rolling_prev_mad = shifted_shifts.groupby(df['_group_key']).rolling(window=lookback_weeks, min_periods=2).apply(calc_mad, raw=True).reset_index(level=0, drop=True)
    
    df['prev_3wk_rolling_mean_pp'] = rolling_prev_mean
    df['prev_3wk_rolling_std_pp'] = rolling_prev_std
    df['prev_3wk_rolling_median_pp'] = rolling_prev_median
    df['prev_3wk_rolling_mad_pp'] = rolling_prev_mad
    
    # 2. Dynamic Volatility Envelope Bounds (u3 +- envelope_std_factor * sigma3)
    robust_std_envelope = np.maximum(df['prev_3wk_rolling_std_pp'].fillna(0.20), 0.20)
    df['dynamic_upper_threshold'] = df['prev_3wk_rolling_mean_pp'] + (envelope_std_factor * robust_std_envelope)
    df['dynamic_lower_threshold'] = df['prev_3wk_rolling_mean_pp'] - (envelope_std_factor * robust_std_envelope)
    
    # 3. Robust MAD Standardized Z-Score
    z_scores = []
    for idx, row in df.iterrows():
        shift = row['share_shift_pp']
        med = row['prev_3wk_rolling_median_pp']
        mad = row['prev_3wk_rolling_mad_pp']
        z_scores.append(compute_robust_mad_zscore(shift, med, mad))
        
    df['statistical_z_score'] = z_scores
    df['statistical_z_score'] = df['statistical_z_score'].clip(-10.0, 10.0)
    
    # 4. 4 Distinct Statistical Technique Evaluations
    # Technique 1 — Moving Average Trend Deviation (|shift - mean| >= ma_dev_factor * MAD)
    robust_mad_scale = np.maximum(df['prev_3wk_rolling_mad_pp'].fillna(0.20), 0.20)
    df['t1_moving_average_anomaly'] = (
        df['share_shift_pp'].notna() & df['prev_3wk_rolling_mean_pp'].notna() &
        (np.abs(df['share_shift_pp'] - df['prev_3wk_rolling_mean_pp']) >= (ma_dev_factor * robust_mad_scale))
    )
    
    # Technique 2 — Configured Robust MAD Z-Score Spike (|Z_MAD| >= z_threshold)
    df['t2_z_score_anomaly'] = np.abs(df['statistical_z_score']) >= z_threshold
    
    # Technique 3 — Consecutive Share Erosion (3 consecutive weekly share drops)
    s1 = df.groupby(group_cols)['share_shift_pp'].shift(0) < 0
    s2 = df.groupby(group_cols)['share_shift_pp'].shift(1) < 0
    s3 = df.groupby(group_cols)['share_shift_pp'].shift(2) < 0
    df['t3_erosion_anomaly'] = s1 & s2 & s3
    
    # Technique 4 — Dynamic Volatility Envelope Breach (Shift outside u3 +- envelope_std_factor * sigma3)
    df['t4_dynamic_threshold_anomaly'] = (
        df['share_shift_pp'].notna() & df['dynamic_upper_threshold'].notna() &
        ((df['share_shift_pp'] > df['dynamic_upper_threshold']) | (df['share_shift_pp'] < df['dynamic_lower_threshold']))
    )
    
    # 5. Technique 5 — Scikit-Learn IsolationForest ML Model Execution
    df['isolation_forest_label'] = 1
    df['isolation_forest_score'] = 0.0
    df['isolation_forest_anomaly'] = False
    
    if SKLEARN_AVAILABLE:
        try:
            ml_features = ['clean_trx', 'market_share_trx_pct', 'share_shift_pp', 'momentum_ratio']
            ml_df = df[ml_features].fillna(0.0)
            
            iso_model = IsolationForest(n_estimators=100, contamination=iforest_contamination, random_state=42)
            df['isolation_forest_label'] = iso_model.fit_predict(ml_df)
            df['isolation_forest_score'] = iso_model.decision_function(ml_df)
            df['isolation_forest_anomaly'] = df['isolation_forest_label'] == -1
        except Exception as e:
            print(f"[Anomaly Engine Warning] IsolationForest ML Execution Error: {e}")
            
    # Combined Detector Signal Flag
    df['combined_anomaly'] = (
        df['t1_moving_average_anomaly'] |
        df['t2_z_score_anomaly'] |
        df['t3_erosion_anomaly'] |
        df['t4_dynamic_threshold_anomaly'] |
        df['isolation_forest_anomaly']
    )
    df['is_statistical_anomaly'] = df['combined_anomaly']
    
    def build_triggered_techniques(row):
        techs = []
        if row['t1_moving_average_anomaly']: techs.append('MA Trend Deviation')
        if row['t2_z_score_anomaly']: techs.append('Robust Z-Score Spike')
        if row['t3_erosion_anomaly']: techs.append('3-Wk Erosion')
        if row['t4_dynamic_threshold_anomaly']: techs.append('Volatility Envelope Breach')
        if row['isolation_forest_anomaly']: techs.append('Isolation Forest ML')
        return ", ".join(techs) if techs else 'None'
        
    df['triggered_techniques'] = df.apply(build_triggered_techniques, axis=1)
    
    df = df.drop(columns=['_group_key'], errors='ignore')
    return df
