"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Comprehensive V8 Unit & Integration Test Suite
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd
import numpy as np

from data_preprocessing import preprocess_pharma_dataset, parse_iso_date_with_week_hint
from market_share_engine import calculate_market_share
from share_shift_engine import calculate_share_shifts
from anomaly_engine import detect_statistical_anomalies
from alert_engine import generate_threshold_alerts
from forecasting_engine import forecast_brand_market_share
from pipeline_runner import run_end_to_end_pipeline
from config import ANOMALY_Z_THRESHOLD, SUBSTANTIAL_SHIFT_PP

def test_negative_trx_flag_preserved():
    df = pd.DataFrame({
        'date': ['2025-01-06'],
        'week_number': ['2'],
        'year': ['2025'],
        'region': ['Tamil Nadu'],
        'therapeutic_area': ['Cardiology'],
        'product': ['Vascolin'],
        'brand': ['Brand A'],
        'trx': ['-150.0'],
        'nrx': ['20.0'],
        'units': ['300.0']
    })
    clean_df, audit, quar = preprocess_pharma_dataset(df)
    assert len(clean_df) == 1
    assert clean_df['clean_trx'].iloc[0] == -150.0
    assert clean_df['is_negative_trx'].iloc[0] == True

def test_missing_categorical_quarantine():
    df = pd.DataFrame({
        'date': ['2025-01-06'],
        'week_number': ['2'],
        'year': ['2025'],
        'region': ['nan'],
        'therapeutic_area': ['Cardiology'],
        'product': ['Vascolin'],
        'brand': ['Brand A'],
        'trx': ['100.0'],
        'nrx': ['20.0'],
        'units': ['300.0']
    })
    clean_df, audit, quar = preprocess_pharma_dataset(df)
    assert len(quar) == 1
    assert 'MISSING_CATEGORICAL_FIELD' in quar['rejection_reason'].iloc[0]

def test_invalid_date_quarantine_no_fallback():
    # Test that completely invalid date is rejected/quarantined (No CURRENT_DATE fallback)
    df = pd.DataFrame({
        'date': ['invalid-date-string'],
        'week_number': ['2'],
        'year': ['2025'],
        'region': ['Tamil Nadu'],
        'therapeutic_area': ['Cardiology'],
        'product': ['Vascolin'],
        'brand': ['Brand A'],
        'trx': ['100.0'],
        'nrx': ['20.0'],
        'units': ['300.0']
    })
    clean_df, audit, quar = preprocess_pharma_dataset(df)
    assert len(quar) == 1
    assert 'INVALID_DATE' in quar['rejection_reason'].iloc[0]

def test_week_aware_date_disambiguation():
    dt1 = parse_iso_date_with_week_hint('10/03/2025', week_hint='167')
    assert dt1.month == 3
    assert dt1.day == 10

def test_competitive_set_denominator_propagation():
    df = pd.DataFrame({
        'year_week': ['2025-W01', '2025-W01', '2025-W01'],
        'clean_region': ['Tamil Nadu'] * 3,
        'clean_therapeutic_area': ['Cardiology'] * 3,
        'clean_product': ['Vascolin', 'Vascolin', 'Vascolin'],
        'clean_brand': ['Brand A', 'Brand B', 'Brand C'],
        'clean_trx': [500.0, 500.0, 1000.0],
        'clean_nrx': [100.0, 100.0, 200.0],
        'clean_units': [1000.0, 1000.0, 2000.0]
    })
    ms_df, sum_check = calculate_market_share(df, selected_brands=['Brand A', 'Brand B'])
    assert len(ms_df) == 2
    assert (ms_df['market_share_trx_pct'] == 50.0).all()

def test_configurable_threshold_and_detectors():
    df = pd.DataFrame({
        'year_week': ['2025-W01', '2025-W02', '2025-W03', '2025-W04'],
        'clean_region': ['Tamil Nadu'] * 4,
        'clean_therapeutic_area': ['Cardiology'] * 4,
        'clean_brand': ['Brand A'] * 4,
        'brand_trx': [100] * 4,
        'clean_trx': [100] * 4,
        'total_segment_trx': [1000] * 4,
        'market_share_trx_pct': [10.0, 12.0, 14.0, 25.0],
        'share_shift_pp': [np.nan, 2.0, 2.0, 11.0],
        'momentum_ratio': [1.0] * 4
    })
    anomaly_df = detect_statistical_anomalies(df, z_threshold=ANOMALY_Z_THRESHOLD)
    assert 'dynamic_upper_threshold' in anomaly_df
    assert 't1_moving_average_anomaly' in anomaly_df
    assert 't4_dynamic_threshold_anomaly' in anomaly_df

def test_evidence_based_corroborated_alerts():
    anomaly_df = pd.DataFrame({
        'year_week': ['2025-W04'],
        'clean_region': ['Tamil Nadu'],
        'clean_therapeutic_area': ['Cardiology'],
        'clean_brand': ['Brand A'],
        'market_share_trx_pct': [25.0],
        'share_shift_pp': [3.5],
        'share_shift_bps': [350.0],
        'dynamic_upper_threshold': [15.0],
        'dynamic_lower_threshold': [5.0],
        'statistical_z_score': [4.2],
        'isolation_forest_score': [-0.15],
        'isolation_forest_anomaly': [True],
        't1_moving_average_anomaly': [True],
        't2_z_score_anomaly': [True],
        't3_erosion_anomaly': [False],
        't4_dynamic_threshold_anomaly': [True],
        'triggered_techniques': ['MA Trend Deviation, Robust Z-Score Spike, Volatility Envelope Breach, Isolation Forest ML']
    })
    full_alerts, active_alerts = generate_threshold_alerts(anomaly_df, substantial_shift_pp=SUBSTANTIAL_SHIFT_PP)
    assert len(active_alerts) == 1
    assert active_alerts['alert_category'].iloc[0] == 'REGIONAL GROWTH SPIKE'

def test_isolation_forest_execution():
    df = pd.DataFrame({
        'year_week': [f'2025-W{i:02d}' for i in range(1, 20)],
        'clean_region': ['Tamil Nadu'] * 19,
        'clean_therapeutic_area': ['Cardiology'] * 19,
        'clean_brand': ['Brand A'] * 19,
        'brand_trx': [100] * 18 + [5000],
        'clean_trx': [100] * 18 + [5000],
        'total_segment_trx': [1000] * 19,
        'market_share_trx_pct': [10.0] * 18 + [70.0],
        'share_shift_pp': [0.0] * 18 + [60.0],
        'momentum_ratio': [1.0] * 19
    })
    anomaly_df = detect_statistical_anomalies(df)
    assert 'isolation_forest_anomaly' in anomaly_df
    assert 'triggered_techniques' in anomaly_df

def test_arima_model_selection_and_forecast():
    gold_df = pd.DataFrame({
        'year_week': [f'2025-W{i:02d}' for i in range(1, 15)],
        'clean_region': ['Tamil Nadu'] * 14,
        'clean_therapeutic_area': ['Cardiology'] * 14,
        'clean_brand': ['Brand A'] * 14,
        'market_share_trx_pct': [20.0 + (i * 0.5) for i in range(14)]
    })
    f_df = forecast_brand_market_share(gold_df, 'Brand A', 'Tamil Nadu', forecast_horizon=4)
    assert len(f_df) == 4
    assert 'best_model_order' in f_df.columns

def test_end_to_end_pipeline_integration():
    res = run_end_to_end_pipeline()
    assert len(res['cleaned_df']) > 15000
    assert len(res['quarantine_df']) < 5000
    assert not res['gold_df'].empty
    assert not res['active_alerts_df'].empty
