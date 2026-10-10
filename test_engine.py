"""
Test script to verify all sample cases run correctly through the underwriting engine.
"""

from sample_cases import SAMPLE_CASES
from business_rules import evaluate_lap_qualification
from llm_engine import analyze_lead_with_llm

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def run_all_tests():
    print("==================================================================")
    print("Testing Home Credit LAP Voice Agent Underwriting Engine")
    print("==================================================================")
    passed = 0
    total = len(SAMPLE_CASES)

    for case in SAMPLE_CASES:
        print(f"\nTesting {case['id']}: {case['title']}")
        result = evaluate_lap_qualification(
            customer_name=case["customer_name"],
            property_type=case["property_type"],
            ownership_status=case["ownership_status"],
            document_availability=case["document_availability"],
            loan_amount=case["loan_amount"],
            occupation=case["occupation"],
            income_mode=case["income_mode"],
            market_value=case["market_value"],
            tenure_years=case["tenure_years"],
            has_existing_loan=case["has_existing_loan"],
            existing_loan_details=case["existing_loan_details"],
            wants_balance_transfer=case["wants_balance_transfer"],
            is_customer_busy=case["is_customer_busy"],
            preferred_callback_time=case["preferred_callback_time"],
            agreed_to_capped_amount=case["agreed_to_capped_amount"],
        )

        actual_status = result["status"]
        expected_status = case["expected_status"]
        actual_team = result["responsible_team"]
        expected_team = case["expected_team"]

        print(f"  Actual Status:   {actual_status}")
        print(f"  Expected Status: {expected_status}")
        print(f"  Responsible Team: {actual_team}")

        assert actual_status == expected_status, f"Mismatch in status for {case['id']}: got {actual_status}, expected {expected_status}"
        assert actual_team == expected_team, f"Mismatch in team for {case['id']}: got {actual_team}, expected {expected_team}"
        
        # Also test analyze_lead_with_llm in fallback/deterministic mode
        llm_res = analyze_lead_with_llm(case, api_key=None)
        assert llm_res["status"] == expected_status, f"Mismatch in fallback engine for {case['id']}"

        print(f"  Result: PASS [OK]")
        passed += 1

    print("\n==================================================================")
    print(f"Test Summary: {passed}/{total} Test Cases Passed Successfully!")
    print("==================================================================")

if __name__ == "__main__":
    run_all_tests()
