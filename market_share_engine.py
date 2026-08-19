"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Market Share Calculation Engine
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd
import numpy as np

def calculate_market_share(cleaned_df, selected_brands=None):
    """
    Computes Segment Market Total Volume and Brand Market Share %
    Supports 2 Denominator Modes:
    1. Full Market Segment Mode (selected_brands=None): Denominator = Sum of ALL brands in segment
    2. Selected Competitive Set Mode (selected_brands=[...]): Denominator = Sum of SELECTED brands only
    Validates that brand shares sum to ~100% per market segment.
    """
    df = cleaned_df.copy()
    
    # Filter by selected competitive set if specified
    if selected_brands and len(selected_brands) > 0:
        df = df[df['clean_brand'].isin(selected_brands)].copy()
        
    # Market Segment Grain: [year_week, clean_region]
    segment_group = ['year_week', 'clean_region']
    brand_group = segment_group + ['clean_brand']
    
    # Aggregate Brand TRX, NRX, Units
    brand_agg = df.groupby(brand_group).agg({
        'clean_trx': 'sum',
        'clean_nrx': 'sum',
        'clean_units': 'sum'
    }).reset_index().rename(columns={'clean_trx': 'brand_trx'})
    
    # Aggregate Total Segment Volume
    segment_totals = df.groupby(segment_group).agg({
        'clean_trx': 'sum',
        'clean_nrx': 'sum',
        'clean_units': 'sum'
    }).reset_index().rename(columns={
        'clean_trx': 'total_segment_trx',
        'clean_nrx': 'total_segment_nrx',
        'clean_units': 'total_segment_units'
    })
    
    # Merge Segment Totals
    merged = pd.merge(brand_agg, segment_totals, on=segment_group, how='left')
    
    # Merge Therapeutic Area Mapping for each brand
    brand_ta_map = df[['clean_brand', 'clean_therapeutic_area']].drop_duplicates()
    merged = pd.merge(merged, brand_ta_map, on='clean_brand', how='left')
    
    # Compute Brand Market Share % (TRX & NRX)
    merged['market_share_trx_pct'] = np.where(
        merged['total_segment_trx'] > 0,
        (merged['brand_trx'] / merged['total_segment_trx']) * 100.0,
        0.0
    )
    
    merged['market_share_nrx_pct'] = np.where(
        merged['total_segment_nrx'] > 0,
        (merged['clean_nrx'] / merged['total_segment_nrx']) * 100.0,
        0.0
    )
    
    # Compute NRX/TRX Momentum Ratio
    merged['momentum_ratio'] = np.where(
        merged['market_share_trx_pct'] > 0,
        merged['market_share_nrx_pct'] / merged['market_share_trx_pct'],
        1.0
    )
    
    # Add clean_trx column for pipeline compatibility
    merged['clean_trx'] = merged['brand_trx']
    
    # Validate sum to ~100% contract
    sum_check = merged.groupby(segment_group)['market_share_trx_pct'].sum().reset_index()
    sum_check['is_valid_100_pct'] = np.isclose(sum_check['market_share_trx_pct'], 100.0, atol=0.5)
    
    return merged, sum_check
