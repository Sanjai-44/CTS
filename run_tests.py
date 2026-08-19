"""
===============================================================================
Cognizant (CTS) Nurture Placement Hackathon - V8 Master Unit & Integration Test Runner
Commercial Analytics Market Share & Share-Shift Tracker
===============================================================================
"""

import sys
import os

from test_pipeline import (
    test_negative_trx_flag_preserved,
    test_missing_categorical_quarantine,
    test_invalid_date_quarantine_no_fallback,
    test_week_aware_date_disambiguation,
    test_competitive_set_denominator_propagation,
    test_configurable_threshold_and_detectors,
    test_evidence_based_corroborated_alerts,
    test_isolation_forest_execution,
    test_arima_model_selection_and_forecast,
    test_end_to_end_pipeline_integration
)

def run_all_tests():
    print("=" * 80)
    print("RUNNING V8 COMPREHENSIVE UNIT & INTEGRATION TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Negative TRX Chargebacks Preserved (No abs)", test_negative_trx_flag_preserved),
        ("Missing Categorical Field Quarantine", test_missing_categorical_quarantine),
        ("Invalid Date Quarantine (No CURRENT_DATE Fallback)", test_invalid_date_quarantine_no_fallback),
        ("Week-Aware Date Disambiguation", test_week_aware_date_disambiguation),
        ("Competitive Set Denominator Propagation", test_competitive_set_denominator_propagation),
        ("Configurable Parameters & Detector Isolation", test_configurable_threshold_and_detectors),
        ("Evidence-Based Corroborated Alerts (CRITICAL/SIGNIFICANT/WATCH)", test_evidence_based_corroborated_alerts),
        ("Scikit-Learn IsolationForest ML Model Execution", test_isolation_forest_execution),
        ("ARIMA Model Selection (AIC) & Dynamic Dates", test_arima_model_selection_and_forecast),
        ("Full End-to-End Pipeline Integration Test", test_end_to_end_pipeline_integration)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            print(f"  [PASSED] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAILED] {name}: {e}")
            failed += 1
            
    print("=" * 80)
    total = passed + failed
    ratio = (passed / total) * 100 if total > 0 else 0
    print(f"TEST RESULTS: {passed} PASSED | {failed} FAILED | SUCCESS RATIO: {ratio:.1f}%")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
