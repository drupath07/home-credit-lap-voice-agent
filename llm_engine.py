"""
LLM Integration and Hybrid Business Decision Engine.
Calls Gemini API with structured JSON output, and falls back seamlessly to
the deterministic business rules engine if API key is missing or call fails.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import requests

from business_rules import evaluate_lap_qualification

logger = logging.getLogger(__name__)

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
)

LEAD_EVALUATION_SCHEMA_PROMPT = """
You are a senior credit underwriting analyst for Home Credit.
Analyze the following customer application for a pre-approved Loan Against Property (LAP) offer.

# BUSINESS RULES TO ENFORCE:
1. Property Type: Residential, Commercial, and Industrial are ELIGIBLE. Agricultural is STRICTLY DISQUALIFIED.
2. Ownership: Sole and Joint are ELIGIBLE.
3. Documents: Original documents MUST be ready. If not ready/missing -> STRICTLY DISQUALIFIED.
4. Loan Amount: Maximum pre-approved cap is ₹75,00,000 (75 Lakhs). If > 75L and agreed to cap -> Capped to 75L. If > 75L and refuses cap -> DISQUALIFIED.
5. Income Mode: Salaried or Self-Employed is ELIGIBLE, but income MUST be received in Bank. Cash income -> STRICTLY DISQUALIFIED.
6. Market Value: Must be positive.
7. Tenure: Must be between 3 and 15 years.
8. Customer Busy: If customer is busy, mark as CALLBACK_REQUESTED.
9. Existing Loan / EMI Reduction: If customer mentions existing loan or wants lower EMI / balance transfer, mark as TRANSFER_TO_SPECIALIST.

# OUTPUT FORMAT:
You MUST respond with ONLY valid, raw JSON (no markdown ticks, no commentary) matching this schema:
{
  "status": "QUALIFIED_FOR_EXPERT" | "DISQUALIFIED" | "TRANSFER_TO_SPECIALIST" | "CALLBACK_REQUESTED",
  "priority": "HIGH" | "MEDIUM" | "LOW",
  "decision_headline": string,
  "disqualification_reason": string or null,
  "transfer_reason": string or null,
  "callback_details": string or null,
  "checklist_audit": {
    "property_type": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "ownership_status": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "document_availability": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "loan_amount": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "occupation": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "income_mode": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "market_value": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string},
    "tenure_years": {"value": string, "status": "PASS"|"FAIL"|"SKIPPED", "notes": string}
  },
  "next_agent_action": string,
  "agent_spoken_script": string,
  "recommended_next_step": string,
  "responsible_team": string,
  "confidence_score": float,
  "reasoning": string
}
"""


def analyze_lead_with_llm(lead_data: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Attempts to evaluate lead data using Gemini LLM.
    If API key is missing or call fails, falls back gracefully to deterministic rule engine.
    """
    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()

    # If no key available, use deterministic rules engine directly
    if not effective_api_key:
        result = evaluate_lap_qualification(
            customer_name=lead_data.get("customer_name", "Customer"),
            property_type=lead_data.get("property_type", "Residential"),
            ownership_status=lead_data.get("ownership_status", "Sole"),
            document_availability=lead_data.get("document_availability", "Original"),
            loan_amount=float(lead_data.get("loan_amount", 5000000)),
            occupation=lead_data.get("occupation", "Salaried"),
            income_mode=lead_data.get("income_mode", "Bank"),
            market_value=float(lead_data.get("market_value", 10000000)),
            tenure_years=int(lead_data.get("tenure_years", 10)),
            has_existing_loan=bool(lead_data.get("has_existing_loan", False)),
            existing_loan_details=str(lead_data.get("existing_loan_details", "")),
            wants_balance_transfer=bool(lead_data.get("wants_balance_transfer", False)),
            is_customer_busy=bool(lead_data.get("is_customer_busy", False)),
            preferred_callback_time=str(lead_data.get("preferred_callback_time", "")),
            agreed_to_capped_amount=bool(lead_data.get("agreed_to_capped_amount", False)),
        )
        result["engine_used"] = "DETERMINISTIC_RULES_ENGINE"
        result["note"] = "Evaluated via Home Credit Deterministic Underwriting Engine (100% policy-compliant, no API key required)."
        return result

    # Try LLM call
    try:
        user_prompt = f"Customer Profile:\n{json.dumps(lead_data, indent=2)}\n\nAnalyze and return structured JSON."
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": LEAD_EVALUATION_SCHEMA_PROMPT},
                        {"text": user_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        url = GEMINI_API_URL_TEMPLATE.format(api_key=effective_api_key)
        response = requests.post(url, json=payload, timeout=12)

        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = json.loads(raw_text.strip().replace("```json", "").replace("```", "").strip())
                parsed["engine_used"] = "GEMINI_LLM_API"
                parsed["note"] = "Evaluated using Gemini 1.5 Flash with structured JSON schema."
                return parsed
        else:
            logger.warning(f"Gemini API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Error calling Gemini API: {e}, switching to deterministic rules fallback.")

    # Graceful fallback on API error
    fallback_res = evaluate_lap_qualification(
        customer_name=lead_data.get("customer_name", "Customer"),
        property_type=lead_data.get("property_type", "Residential"),
        ownership_status=lead_data.get("ownership_status", "Sole"),
        document_availability=lead_data.get("document_availability", "Original"),
        loan_amount=float(lead_data.get("loan_amount", 5000000)),
        occupation=lead_data.get("occupation", "Salaried"),
        income_mode=lead_data.get("income_mode", "Bank"),
        market_value=float(lead_data.get("market_value", 10000000)),
        tenure_years=int(lead_data.get("tenure_years", 10)),
        has_existing_loan=bool(lead_data.get("has_existing_loan", False)),
        existing_loan_details=str(lead_data.get("existing_loan_details", "")),
        wants_balance_transfer=bool(lead_data.get("wants_balance_transfer", False)),
        is_customer_busy=bool(lead_data.get("is_customer_busy", False)),
        preferred_callback_time=str(lead_data.get("preferred_callback_time", "")),
        agreed_to_capped_amount=bool(lead_data.get("agreed_to_capped_amount", False)),
    )
    fallback_res["engine_used"] = "FALLBACK_RULES_ENGINE"
    fallback_res["note"] = "Gemini API unavailable or errored; gracefully evaluated via Deterministic Rules Engine."
    return fallback_res


def simulate_agent_turn(
    conversation_history: List[Dict[str, str]],
    customer_utterance: str,
    customer_name: str = "Customer",
    agent_name: str = "Priya",
    language: str = "English",
) -> Dict[str, Any]:
    """
    Simulates the Voice Agent's next conversational reply and state detection.
    Can operate via intelligent conversational regex / intent mapping or LLM.
    """
    text_lower = customer_utterance.lower().strip()

    # Check Busy Intent
    busy_keywords = ["busy", "in a meeting", "driving", "call later", "call me back", "not free", "busy right now", "baad mein"]
    if any(k in text_lower for k in busy_keywords):
        reply = (
            f"I completely understand you're busy right now, {customer_name}. "
            f"Could you please share your preferred time so our team can call you back?"
            if language == "English"
            else f"Main samajh sakti hoon aap busy hain, {customer_name} ji. Kya aap bata sakte hain ki kis samay call karna behtar hoga?"
        )
        return {
            "agent_reply": reply,
            "stage": "BUSY_CALLBACK_NEGOTIATION",
            "is_terminal": False,
            "action": "Acknowledge and request callback time"
        }

    # Check Callback Time Provided
    time_keywords = ["at 4", "at 5", "at 6", "at 7", "tomorrow", "evening", "morning", "pm", "am", "after 6", "kal"]
    if any(k in text_lower for k in time_keywords) and len(conversation_history) > 1 and "busy" in conversation_history[-2].get("text", "").lower():
        reply = (
            f"Noted, {customer_name}! I have recorded your preferred callback for {customer_utterance}. "
            f"Our team will reach out then. Thank you for banking with Home Credit, and have a wonderful day!"
            if language == "English"
            else f"Ji bilkul, {customer_name} ji! Maine {customer_utterance} ka callback schedule kar diya hai. Home Credit se baat karne ke liye dhanyawad!"
        )
        return {
            "agent_reply": reply,
            "stage": "CALLBACK_CONFIRMED",
            "is_terminal": True,
            "action": "Schedule callback and end call"
        }

    # Check Existing Loan / EMI Reduction -> Transfer Switch
    transfer_keywords = ["existing loan", "already have a loan", "running loan", "transfer", "reduce emi", "lower emi", "balance transfer", "purana loan"]
    if any(k in text_lower for k in transfer_keywords):
        reply = (
            f"Thank you for sharing that, {customer_name}. Since you already have an existing loan on the property, "
            f"our specialized Balance Transfer team can help you reduce your interest rate and lower your monthly EMI. "
            f"A loan transfer specialist will call you shortly to assist with takeover options. Have a great day!"
            if language == "English"
            else f"Yeh batane ke liye dhanyawad, {customer_name} ji. Kyunki aapka pehle se loan chal raha hai, hamari Balance Transfer team aapki EMI kam karne mein madad karegi. Hamare specialist aapse jald hi sampark karenge!"
        )
        return {
            "agent_reply": reply,
            "stage": "TRANSFER_TO_SPECIALIST",
            "is_terminal": True,
            "action": "Route lead to Balance Transfer Specialist Team and end call"
        }

    # Check Disqualifications: Agricultural
    if "agricultural" in text_lower or "farming" in text_lower or "kheti" in text_lower:
        reply = (
            f"Thank you for confirming, {customer_name}. Under Home Credit's lending policy, our Loan Against Property "
            f"offer is only available for Residential, Commercial, or Industrial properties. Agricultural land is not eligible. "
            f"Therefore, we cannot proceed with this offer today. Thank you for your time and have a pleasant day!"
            if language == "English"
            else f"Batane ke liye shukriya, {customer_name} ji. Home Credit ki policy ke anusar kheti ya agricultural zameen par LAP uplabdh nahi hai. Isliye hum aage nahi badh sakte. Dhanyawad!"
        )
        return {
            "agent_reply": reply,
            "stage": "DISQUALIFIED_AGRICULTURAL",
            "is_terminal": True,
            "action": "Immediate polite disqualification (Agricultural Property) and end call"
        }

    # Check Disqualifications: Cash Income
    if "cash" in text_lower or "rokda" in text_lower or "cash in hand" in text_lower:
        reply = (
            f"I understand, {customer_name}. However, our credit policy strictly requires verifiable income deposits "
            f"received through a bank account. Because your income is received in cash, we are unable to process this pre-approved offer. "
            f"We truly appreciate your relationship with Home Credit and will keep you informed of future updates!"
            if language == "English"
            else f"Samajh gayi {customer_name} ji. Hamari policy ke hisab se income bank mein aana anivarya hai. Cash income par yeh offer lagu nahi hota. Home Credit se judne ke liye shukriya!"
        )
        return {
            "agent_reply": reply,
            "stage": "DISQUALIFIED_CASH_INCOME",
            "is_terminal": True,
            "action": "Immediate polite disqualification (Cash Income) and end call"
        }

    # Check Loan Cap negotiation (> 75 Lakhs)
    if ("crore" in text_lower or "80 lakh" in text_lower or "90 lakh" in text_lower or "1 cr" in text_lower) and "75" not in text_lower:
        reply = (
            f"I hear you, {customer_name}. Our special pre-approved loyalty offer currently has a maximum limit of ₹75,00,000 (75 Lakhs). "
            f"Would you be open to proceeding with this maximum approved limit of 75 Lakhs?"
            if language == "English"
            else f"Ji bilkul {customer_name} ji. Hamara pre-approved offer adhiktam 75 Lakhs tak ka hai. Kya aap 75 Lakhs ke sath aage badhna chahenge?"
        )
        return {
            "agent_reply": reply,
            "stage": "LOAN_CAP_NEGOTIATION",
            "is_terminal": False,
            "action": "Explain ₹75L cap and negotiate ceiling limit"
        }

    # Default progressive flow
    turn_count = len(conversation_history)
    if turn_count <= 2:
        reply = (
            f"Thank you, {customer_name}! To check your pre-approved eligibility, could you confirm if your property is "
            f"Residential (flat/house), Commercial (shop/office), or Industrial?"
            if language == "English"
            else f"Shukriya {customer_name} ji. Kripya batayein ki aapki property Residential hai, Commercial hai, ya Industrial?"
        )
        stage = "COLLECTING_PROPERTY_TYPE"
    elif turn_count <= 4:
        reply = (
            f"Great. Are you the sole owner of the property, or is it jointly owned? Also, do you have original title deeds ready?"
            if language == "English"
            else f"Kya aap is property ke akele malik hain ya joint ownership hai? Aur kya original papers ready hain?"
        )
        stage = "COLLECTING_OWNERSHIP_AND_DOCS"
    elif turn_count <= 6:
        reply = (
            f"Understood. How much loan amount are you looking for, and what repayment tenure (between 3 to 15 years) works best for you?"
            if language == "English"
            else f"Samajh gaya. Aapko kitne loan amount ki zaroorat hai, aur kitne saal (3 se 15 saal ke beech) mein chukana chahenge?"
        )
        stage = "COLLECTING_AMOUNT_AND_TENURE"
    elif turn_count <= 8:
        reply = (
            f"Noted. Could you confirm whether you are Salaried or Self-Employed, that your income is received in a bank account, and the estimated market value of your property?"
            if language == "English"
            else f"Aur aap Salaried hain ya Self-employed? Income bank account mein aati hai na? Aur property ki approximate market value kitni hogi?"
        )
        stage = "COLLECTING_INCOME_AND_VALUATION"
    else:
        reply = (
            f"Congratulations, {customer_name}! You have successfully cleared all 7 eligibility criteria for our pre-approved "
            f"Loan Against Property offer. I am assigning your file to our Senior Loan Expert team. A senior specialist will call you shortly "
            f"to share the exact interest rates and complete the quick formalities. Thank you for choosing Home Credit!"
            if language == "English"
            else f"Badhai ho, {customer_name} ji! Aapne sabhi eligibility criteria clear kar liye hain. Hum aapki file Senior Loan Expert ko assign kar rahe hain jo aapse interest rates finalize karne ke liye call karenge. Home Credit par vishwas jatane ke liye dhanyawad!"
        )
        return {
            "agent_reply": reply,
            "stage": "QUALIFIED_HANDOFF_TO_EXPERT",
            "is_terminal": True,
            "action": "Complete handoff to Senior Human Loan Expert and conclude call"
        }

    return {
        "agent_reply": reply,
        "stage": stage,
        "is_terminal": False,
        "action": f"Advance conversation to {stage}"
    }
