"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - Share-Shift Calculation Engine
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import pandas as pd
import numpy as np

def calculate_share_shifts(market_share_df):
    """
    Calculates Week-over-Week (WoW) Share Shift.
    CRITICAL RULE (MUST-FIX 5): First week's share shift is NULL (np.nan / None), NOT 0.0!
    Explicitly labels metrics as percentage points (pp) and basis points (bps).
    """
    df = market_share_df.copy()
    
    # Chronological Sorting by [clean_region, clean_therapeutic_area, clean_brand, year_week]
    df = df.sort_values(by=['clean_region', 'clean_therapeutic_area', 'clean_brand', 'year_week']).reset_index(drop=True)
    
    # Calculate Previous Share (Shifted by 1 week per brand/region/TA group)
    group_cols = ['clean_region', 'clean_therapeutic_area', 'clean_brand']
    df['prev_market_share_pp'] = df.groupby(group_cols)['market_share_trx_pct'].shift(1)
    
    # Share Shift in Percentage Points (pp): Current Share - Previous Share
    df['share_shift_pp'] = df['market_share_trx_pct'] - df['prev_market_share_pp']
    
    # Share Shift in Basis Points (bps): 1 pp = 100 bps
    df['share_shift_bps'] = df['share_shift_pp'] * 100.0
    
    # Verify First Week is NULL Rule
    # Where prev_market_share_pp is NaN, share_shift_pp MUST BE NaN (NULL)
    first_week_mask = df['prev_market_share_pp'].isna()
    df.loc[first_week_mask, 'share_shift_pp'] = np.nan
    df.loc[first_week_mask, 'share_shift_bps'] = np.nan
    
    return df
