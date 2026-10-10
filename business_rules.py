"""
Home Credit - Loan Against Property (LAP) Qualification Business Rules Engine
Deterministic business logic enforcing all criteria and boundaries.
"""

from typing import Dict, Any, Tuple, Optional
import datetime

# Eligible property types
ELIGIBLE_PROPERTY_TYPES = ["Residential", "Commercial", "Industrial"]
DISQUALIFIED_PROPERTY_TYPES = ["Agricultural", "Land Only", "Other"]

# Eligible ownership types
ELIGIBLE_OWNERSHIP = ["Sole", "Joint"]

# Eligible income modes
ELIGIBLE_INCOME_MODES = ["Bank", "Direct Bank Transfer", "Cheque"]
DISQUALIFIED_INCOME_MODES = ["Cash", "Cash in Hand", "Unrecorded"]

# Maximum allowed pre-approved LAP amount in INR
MAX_LOAN_AMOUNT_INR = 7500000  # 75 Lakhs

# Tenure range in years
MIN_TENURE_YEARS = 3
MAX_TENURE_YEARS = 15


def evaluate_lap_qualification(
    customer_name: str,
    property_type: str,
    ownership_status: str,
    document_availability: str,
    loan_amount: float,
    occupation: str,
    income_mode: str,
    market_value: float,
    tenure_years: int,
    has_existing_loan: bool = False,
    existing_loan_details: str = "",
    wants_balance_transfer: bool = False,
    is_customer_busy: bool = False,
    preferred_callback_time: str = "",
    agreed_to_capped_amount: bool = False,
) -> Dict[str, Any]:
    """
    Evaluates customer data against Home Credit LAP eligibility criteria.
    Returns a structured decision dictionary.
    """
    audit_checklist = {}
    disqualification_reasons = []
    transfer_reasons = []

    # 1. Check Busy / Callback first
    if is_customer_busy:
        cb_time = preferred_callback_time.strip() or "at customer's earliest convenience"
        return {
            "status": "CALLBACK_REQUESTED",
            "priority": "MEDIUM",
            "decision_headline": f"Customer Busy - Reschedule Call for {customer_name}",
            "disqualification_reason": None,
            "transfer_reason": None,
            "callback_details": cb_time,
            "checklist_audit": {
                "property_type": {"value": property_type or "Pending", "status": "SKIPPED"},
                "ownership_status": {"value": ownership_status or "Pending", "status": "SKIPPED"},
                "document_availability": {"value": document_availability or "Pending", "status": "SKIPPED"},
                "loan_amount": {"value": f"₹{loan_amount:,.0f}" if loan_amount else "Pending", "status": "SKIPPED"},
                "occupation": {"value": occupation or "Pending", "status": "SKIPPED"},
                "income_mode": {"value": income_mode or "Pending", "status": "SKIPPED"},
                "market_value": {"value": f"₹{market_value:,.0f}" if market_value else "Pending", "status": "SKIPPED"},
                "tenure_years": {"value": f"{tenure_years} yrs" if tenure_years else "Pending", "status": "SKIPPED"},
            },
            "next_agent_action": f"Acknowledge busy status politely and record callback for {cb_time}.",
            "agent_spoken_script": (
                f"I completely understand you're busy right now, {customer_name}. "
                f"I will arrange for our team to call you back at {cb_time}. "
                f"Thank you for your time with Home Credit, and have a wonderful day!"
            ),
            "recommended_next_step": f"Schedule outbound auto-dialer retry for {cb_time}.",
            "responsible_team": "Outbound Scheduling & CRM Queue",
            "confidence_score": 1.0,
            "reasoning": f"Customer indicated they are busy. Policy requires recording preferred callback time ({cb_time}) and immediately ending the call courteously.",
        }

    # 2. Check Transfer Logic Switch (Existing Loan / EMI Reduction)
    if has_existing_loan or wants_balance_transfer:
        reason_desc = "Customer has an existing loan on the property" if has_existing_loan else "Customer seeking EMI reduction / balance transfer"
        if existing_loan_details:
            reason_desc += f" ({existing_loan_details})"
        transfer_reasons.append(reason_desc)

        return {
            "status": "TRANSFER_TO_SPECIALIST",
            "priority": "HIGH",
            "decision_headline": f"Transfer to Balance Transfer Specialist - {customer_name}",
            "disqualification_reason": None,
            "transfer_reason": "; ".join(transfer_reasons),
            "callback_details": None,
            "checklist_audit": {
                "property_type": {"value": property_type or "Pending", "status": "PASS" if property_type in ELIGIBLE_PROPERTY_TYPES else "NEEDS_CHECK"},
                "ownership_status": {"value": ownership_status or "Pending", "status": "PASS" if ownership_status in ELIGIBLE_OWNERSHIP else "NEEDS_CHECK"},
                "document_availability": {"value": document_availability or "Pending", "status": "INFO"},
                "loan_amount": {"value": f"₹{loan_amount:,.0f}" if loan_amount else "Pending", "status": "INFO"},
                "occupation": {"value": occupation or "Pending", "status": "INFO"},
                "income_mode": {"value": income_mode or "Pending", "status": "INFO"},
                "market_value": {"value": f"₹{market_value:,.0f}" if market_value else "Pending", "status": "INFO"},
                "tenure_years": {"value": f"{tenure_years} yrs" if tenure_years else "Pending", "status": "INFO"},
            },
            "next_agent_action": "Route lead to Loan Balance Transfer specialist desk and terminate call gracefully.",
            "agent_spoken_script": (
                f"Thank you for letting me know, {customer_name}. Since you already have an existing loan on the property, "
                f"our specialized Balance Transfer and Refinancing team can offer you tailored lower EMI options. "
                f"A loan transfer specialist will contact you shortly to assist with this. Thank you for banking with Home Credit!"
            ),
            "recommended_next_step": "Assign ticket to Balance Transfer Specialist Team within 15 minutes.",
            "responsible_team": "Balance Transfer & Refinancing Specialist Desk",
            "confidence_score": 1.0,
            "reasoning": "Standard flow is reserved for fresh loans. Customers with existing mortgages require specialized balance transfer underwriting.",
        }

    # 3. Evaluate 7 Eligibility Checklist Criteria

    # Criterion 1: Property Type
    is_prop_eligible = property_type in ELIGIBLE_PROPERTY_TYPES
    if property_type == "Agricultural":
        audit_checklist["property_type"] = {
            "value": property_type,
            "status": "FAIL",
            "notes": "Agricultural property is strictly not eligible under Home Credit LAP policy."
        }
        disqualification_reasons.append("Property type is Agricultural (Home Credit only accepts Residential, Commercial, or Industrial)")
    elif is_prop_eligible:
        audit_checklist["property_type"] = {
            "value": property_type,
            "status": "PASS",
            "notes": "Eligible category."
        }
    else:
        audit_checklist["property_type"] = {
            "value": property_type or "Unspecified",
            "status": "FAIL",
            "notes": "Unrecognized or ineligible property type."
        }
        disqualification_reasons.append(f"Property type '{property_type}' is not in approved categories (Residential, Commercial, Industrial).")

    # Criterion 2: Ownership Status
    is_ownership_eligible = ownership_status in ELIGIBLE_OWNERSHIP
    if is_ownership_eligible:
        audit_checklist["ownership_status"] = {
            "value": ownership_status,
            "status": "PASS",
            "notes": f"{ownership_status} ownership is eligible."
        }
    else:
        audit_checklist["ownership_status"] = {
            "value": ownership_status or "Unspecified",
            "status": "FAIL",
            "notes": "Ownership status must be Sole or Joint."
        }
        disqualification_reasons.append(f"Ownership status '{ownership_status}' is invalid (Must be Sole or Joint).")

    # Criterion 3: Document Availability
    docs_ready = "Original" in document_availability or document_availability.strip().lower() == "yes"
    if docs_ready:
        audit_checklist["document_availability"] = {
            "value": document_availability,
            "status": "PASS",
            "notes": "Original title deeds ready for verification."
        }
    else:
        audit_checklist["document_availability"] = {
            "value": document_availability or "Not Available",
            "status": "FAIL",
            "notes": "Original property documents are mandatory for verification."
        }
        disqualification_reasons.append("Customer does not have original property documents ready for verification.")

    # Criterion 4: Loan Amount
    effective_loan_amount = loan_amount
    loan_amount_capped = False
    if loan_amount <= 0:
        audit_checklist["loan_amount"] = {
            "value": f"₹{loan_amount:,.0f}",
            "status": "FAIL",
            "notes": "Requested loan amount must be greater than zero."
        }
        disqualification_reasons.append("Loan amount must be greater than zero.")
    elif loan_amount > MAX_LOAN_AMOUNT_INR:
        if agreed_to_capped_amount:
            effective_loan_amount = MAX_LOAN_AMOUNT_INR
            loan_amount_capped = True
            audit_checklist["loan_amount"] = {
                "value": f"₹{loan_amount:,.0f} (Capped to ₹75,00,000 with customer consent)",
                "status": "PASS",
                "notes": "Customer accepted the ₹75 Lakhs pre-approved ceiling."
            }
        else:
            audit_checklist["loan_amount"] = {
                "value": f"₹{loan_amount:,.0f}",
                "status": "FAIL",
                "notes": f"Requested amount exceeds the maximum pre-approved cap of ₹75,00,000 (75 Lakhs)."
            }
            disqualification_reasons.append(f"Requested loan amount (₹{loan_amount:,.0f}) exceeds ₹75 Lakhs cap and customer did not accept the ceiling.")
    else:
        audit_checklist["loan_amount"] = {
            "value": f"₹{loan_amount:,.0f}",
            "status": "PASS",
            "notes": f"Within pre-approved limit of ₹75 Lakhs."
        }

    # Criterion 5: Occupation & Income Mode
    is_occ_eligible = occupation in ["Salaried", "Self-Employed"]
    is_income_mode_bank = any(b.lower() in income_mode.lower() for b in ELIGIBLE_INCOME_MODES)
    is_income_mode_cash = any(c.lower() in income_mode.lower() for c in DISQUALIFIED_INCOME_MODES)

    if is_income_mode_cash or not is_income_mode_bank:
        audit_checklist["income_mode"] = {
            "value": f"{occupation} - {income_mode}",
            "status": "FAIL",
            "notes": "Income received in cash is strictly disqualified; must be verifiable via bank account."
        }
        disqualification_reasons.append(f"Income mode is '{income_mode}' (Cash). Policy requires verifiable income via bank.")
    elif is_occ_eligible and is_income_mode_bank:
        audit_checklist["income_mode"] = {
            "value": f"{occupation} - {income_mode}",
            "status": "PASS",
            "notes": "Verifiable bank income satisfies lending norms."
        }
    else:
        audit_checklist["income_mode"] = {
            "value": f"{occupation} - {income_mode}",
            "status": "FAIL",
            "notes": "Occupation or income mode does not meet criteria."
        }
        disqualification_reasons.append(f"Occupation/Income combination ({occupation}, {income_mode}) is ineligible.")

    # Criterion 6: Market Value & LTV check
    ltv_ratio = (effective_loan_amount / market_value * 100) if market_value > 0 else 0
    if market_value <= 0:
        audit_checklist["market_value"] = {
            "value": f"₹{market_value:,.0f}",
            "status": "FAIL",
            "notes": "Market value must be a valid positive figure."
        }
        disqualification_reasons.append("Invalid or missing estimated property market value.")
    else:
        audit_checklist["market_value"] = {
            "value": f"₹{market_value:,.0f} (LTV: {ltv_ratio:.1f}%)",
            "status": "PASS",
            "notes": f"Estimated market value recorded. Loan-to-Value (LTV) ratio is {ltv_ratio:.1f}%."
        }

    # Criterion 7: Tenure
    if tenure_years < MIN_TENURE_YEARS or tenure_years > MAX_TENURE_YEARS:
        audit_checklist["tenure_years"] = {
            "value": f"{tenure_years} years",
            "status": "FAIL",
            "notes": f"Repayment tenure must be between {MIN_TENURE_YEARS} and {MAX_TENURE_YEARS} years."
        }
        disqualification_reasons.append(f"Requested tenure of {tenure_years} years is outside policy window ({MIN_TENURE_YEARS}-{MAX_TENURE_YEARS} years).")
    else:
        audit_checklist["tenure_years"] = {
            "value": f"{tenure_years} years",
            "status": "PASS",
            "notes": f"Valid tenure within policy window ({MIN_TENURE_YEARS}-{MAX_TENURE_YEARS} years)."
        }

    # 4. Final Disposition
    if disqualification_reasons:
        primary_reason = disqualification_reasons[0]
        return {
            "status": "DISQUALIFIED",
            "priority": "LOW",
            "decision_headline": f"Not Eligible for LAP Offer - {customer_name}",
            "disqualification_reason": "; ".join(disqualification_reasons),
            "transfer_reason": None,
            "callback_details": None,
            "checklist_audit": audit_checklist,
            "next_agent_action": "Politely inform customer of ineligibility and end the call respectfully.",
            "agent_spoken_script": (
                f"Thank you for sharing those details, {customer_name}. Unfortunately, based on our current lending criteria "
                f"regarding {primary_reason.lower()}, we will not be able to proceed with this specific Loan Against Property offer today. "
                f"We truly value your relationship with Home Credit, and we will keep you updated as new tailored products become available. Have a great day!"
            ),
            "recommended_next_step": "Log disqualification in CRM archive and tag reason for re-targeting in 6 months.",
            "responsible_team": "Disqualification Archive & Automated Lead Nurturing",
            "confidence_score": 1.0,
            "reasoning": f"Failed criteria: {'; '.join(disqualification_reasons)}. Immediate disqualification boundary triggered.",
        }

    # All 7 points passed!
    cap_note = " (Adjusted to ₹75 Lakhs cap)" if loan_amount_capped else ""
    return {
        "status": "QUALIFIED_FOR_EXPERT",
        "priority": "HIGH",
        "decision_headline": f"Fully Qualified Lead - Ready for Senior Loan Expert ({customer_name})",
        "disqualification_reason": None,
        "transfer_reason": None,
        "callback_details": None,
        "checklist_audit": audit_checklist,
        "next_agent_action": "Confirm qualification and handoff to Senior Human Loan Expert.",
        "agent_spoken_script": (
            f"Great news, {customer_name}! Based on your details, your property and profile qualify for our pre-approved "
            f"Loan Against Property offer of up to ₹{effective_loan_amount:,.0f}{cap_note}. "
            f"I am now handing your file over to one of our Senior Loan Experts, who will call you shortly to provide the exact interest rates "
            f"and finalize your personalized loan terms. Thank you for choosing Home Credit!"
        ),
        "recommended_next_step": "Dispatch hot lead notification to Senior Loan Expert Team for immediate callback (< 30 mins).",
        "responsible_team": "Senior Human Loan Expert Team",
        "confidence_score": 0.99,
        "reasoning": "All 7 checklist parameters passed policy criteria. Property is eligible, title deeds ready, income received via bank, loan amount within ceiling, and tenure within 3-15 years.",
    }
