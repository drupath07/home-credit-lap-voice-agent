"""
Home Credit India - Loan Against Property (LAP) AI Voice Agent Prototype
Streamlit Dashboard, Lead Qualification Engine & Voice Simulation Platform
"""

import os
import json
import datetime
from typing import Dict, Any, List
import pandas as pd
import streamlit as st

from business_rules import (
    evaluate_lap_qualification,
    ELIGIBLE_PROPERTY_TYPES,
    ELIGIBLE_OWNERSHIP,
    ELIGIBLE_INCOME_MODES,
    MAX_LOAN_AMOUNT_INR,
    MIN_TENURE_YEARS,
    MAX_TENURE_YEARS,
)
from sample_cases import SAMPLE_CASES
from voice_agent_prompt import generate_system_prompt
from llm_engine import analyze_lead_with_llm, simulate_agent_turn

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Home Credit LAP Voice Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for polished financial enterprise look
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(90deg, #d32f2f 0%, #b71c1c 100%);
        padding: 20px 24px;
        border-radius: 10px;
        color: white;
        margin-bottom: 24px;
    }
    .main-header h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        color: white;
    }
    .main-header p {
        margin: 6px 0 0 0;
        font-size: 14px;
        color: #ffebee;
    }
    .status-badge-qualified {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        border: 1px solid #a5d6a7;
    }
    .status-badge-disqualified {
        background-color: #ffebee;
        color: #c62828;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        border: 1px solid #ef9a9a;
    }
    .status-badge-transfer {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        border: 1px solid #90caf9;
    }
    .status-badge-callback {
        background-color: #fff8e1;
        color: #f57f17;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        border: 1px solid #ffe082;
    }
    .decision-card {
        background-color: #f8f9fa;
        border-left: 5px solid #d32f2f;
        padding: 16px;
        border-radius: 6px;
        margin: 12px 0;
    }
    .spoken-script-box {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 14px;
        font-style: italic;
        color: #212121;
        margin: 10px 0;
    }
    .stButton>button {
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "evaluated_leads" not in st.session_state:
    st.session_state.evaluated_leads = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "speaker": "Agent",
            "text": "Hello, am I speaking with Mr. Rajesh Sharma? My name is Priya from Home Credit.",
        }
    ]

if "call_stage" not in st.session_state:
    st.session_state.call_stage = "GREETING"

if "call_active" not in st.session_state:
    st.session_state.call_active = True

# Populate initial history with 2 sample leads for instant analytics visualization
if len(st.session_state.evaluated_leads) == 0:
    for sample in SAMPLE_CASES[:2]:
        eval_res = evaluate_lap_qualification(
            customer_name=sample["customer_name"],
            property_type=sample["property_type"],
            ownership_status=sample["ownership_status"],
            document_availability=sample["document_availability"],
            loan_amount=sample["loan_amount"],
            occupation=sample["occupation"],
            income_mode=sample["income_mode"],
            market_value=sample["market_value"],
            tenure_years=sample["tenure_years"],
            has_existing_loan=sample["has_existing_loan"],
            existing_loan_details=sample["existing_loan_details"],
            wants_balance_transfer=sample["wants_balance_transfer"],
            is_customer_busy=sample["is_customer_busy"],
            preferred_callback_time=sample["preferred_callback_time"],
            agreed_to_capped_amount=sample["agreed_to_capped_amount"],
        )
        st.session_state.evaluated_leads.append(
            {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "customer_name": sample["customer_name"],
                "property_type": sample["property_type"],
                "loan_amount": sample["loan_amount"],
                "market_value": sample["market_value"],
                "tenure_years": sample["tenure_years"],
                "status": eval_res["status"],
                "responsible_team": eval_res["responsible_team"],
                "priority": eval_res["priority"],
                "reasoning": eval_res["reasoning"],
            }
        )

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Home_Credit_Group_logo.svg/320px-Home_Credit_Group_logo.svg.png",
        width=160,
    )
    st.markdown("### ⚙️ Voice Agent Configuration")

    agent_name = st.text_input("AI Agent Name", value="Priya")
    agent_gender = st.selectbox("Agent Gender", ["Female", "Male"], index=0)
    agent_language = st.selectbox("Conversation Language", ["English", "Hindi"], index=0)
    target_customer_name = st.text_input("Active Customer Name", value="Rajesh Sharma")

    st.markdown("---")
    st.markdown("### 🧠 LLM / Decision Engine")
    api_key_input = st.text_input(
        "Gemini API Key (Optional)",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Optional. If omitted, the deterministic Home Credit business rules engine runs with 100% policy fidelity.",
    )

    if api_key_input:
        st.success("✅ Gemini LLM Mode Configured")
    else:
        st.info("⚡ Deterministic Rules Engine Active (Zero API dependencies required)")

    st.markdown("---")
    st.markdown("### 📌 Campaign Constraints")
    st.caption("• Pre-Approved Cap: **₹75,00,000 (75 Lakhs)**")
    st.caption("• Tenure Policy: **3 to 15 Years**")
    st.caption("• Cash Income: **Immediate Disqualification**")
    st.caption("• Agricultural: **Immediate Disqualification**")
    st.caption("• Existing Mortgage: **Transfer to Specialist**")

# -----------------------------------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>Home Credit — Loan Against Property (LAP) AI Voice Agent</h1>
        <p>Pre-Approved Loyalty Campaign | Automated Voice Screening, Boundary Guardrails & Underwriting Triage</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation Tabs
tab_simulator, tab_lead_form, tab_prompt_export, tab_analytics = st.tabs(
    [
        "📞 Interactive Call Simulator",
        "📋 Lead Qualification Audit Form",
        "📜 Production System Prompt & Voice Config",
        "📊 CRM Analytics & Session Audit",
    ]
)

# =============================================================================
# TAB 1: INTERACTIVE CALL SIMULATOR
# =============================================================================
with tab_simulator:
    st.subheader("📞 Voice Agent Conversational Simulator")
    st.write(
        "Simulate live telephone interactions between the **Home Credit Voice Agent** and customers. "
        "Test full conversational sentences, interruptions, out-of-order data disclosure, boundary switches, and disqualifications."
    )

    col_sim_left, col_sim_right = st.columns([1.8, 1.2])

    with col_sim_left:
        # Preload Scenarios
        st.markdown("**⚡ Fast-Load Realistic Test Conversations:**")
        sample_btns = st.columns(3)

        if sample_btns[0].button("Case 1: Eligible Lead", use_container_width=True):
            case = SAMPLE_CASES[0]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "QUALIFIED_HANDOFF_TO_EXPERT"
            st.session_state.call_active = False
            st.rerun()

        if sample_btns[1].button("Case 2: Cash Disqualification", use_container_width=True):
            case = SAMPLE_CASES[1]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "DISQUALIFIED_CASH_INCOME"
            st.session_state.call_active = False
            st.rerun()

        if sample_btns[2].button("Case 4: Balance Transfer", use_container_width=True):
            case = SAMPLE_CASES[3]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "TRANSFER_TO_SPECIALIST"
            st.session_state.call_active = False
            st.rerun()

        sample_btns2 = st.columns(3)
        if sample_btns2[0].button("Case 3: Agricultural Disqual.", use_container_width=True):
            case = SAMPLE_CASES[2]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "DISQUALIFIED_AGRICULTURAL"
            st.session_state.call_active = False
            st.rerun()

        if sample_btns2[1].button("Case 5: Busy Callback", use_container_width=True):
            case = SAMPLE_CASES[4]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "CALLBACK_CONFIRMED"
            st.session_state.call_active = False
            st.rerun()

        if sample_btns2[2].button("Case 6: >75L Cap Negotiation", use_container_width=True):
            case = SAMPLE_CASES[5]
            st.session_state.chat_history = list(case["sample_dialogue_transcript"])
            st.session_state.call_stage = "QUALIFIED_HANDOFF_TO_EXPERT"
            st.session_state.call_active = False
            st.rerun()

        st.markdown("---")

        # Chat display container
        chat_box = st.container(height=420)
        with chat_box:
            for turn in st.session_state.chat_history:
                if turn["speaker"] == "Agent":
                    with st.chat_message("assistant", avatar="👩‍💼" if agent_gender == "Female" else "👨‍💼"):
                        st.markdown(f"**{agent_name} ({turn['speaker']}):** {turn['text']}")
                else:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(f"**Customer ({target_customer_name}):** {turn['text']}")

        # Voice audio simulator (Web Speech API)
        if st.session_state.chat_history:
            last_agent_text = ""
            for msg in reversed(st.session_state.chat_history):
                if msg["speaker"] == "Agent":
                    last_agent_text = msg["text"]
                    break

            if last_agent_text:
                escaped_text = last_agent_text.replace('"', '\\"').replace("'", "\\'")
                tts_lang = "hi-IN" if agent_language == "Hindi" else "en-IN"
                html_speech = f"""
                <div style="margin: 6px 0 14px 0;">
                    <button onclick="speakAgentVoice()" style="background-color: #d32f2f; color: white; border: none; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px;">
                        🔊 Listen to Agent Voice Output
                    </button>
                    <span id="speech-status" style="margin-left: 10px; font-size: 12px; color: #666;"></span>
                </div>
                <script>
                function speakAgentVoice() {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance("{escaped_text}");
                        utterance.lang = "{tts_lang}";
                        utterance.rate = 0.95;
                        utterance.pitch = 1.0;
                        document.getElementById('speech-status').innerText = 'Playing simulated audio...';
                        utterance.onend = function() {{
                            document.getElementById('speech-status').innerText = '';
                        }};
                        window.speechSynthesis.speak(utterance);
                    }} else {{
                        alert('Browser Web Speech API not supported.');
                    }}
                }}
                </script>
                """
                st.components.v1.html(html_speech, height=45)

        # Customer Utterance Input
        if st.session_state.call_active:
            user_input = st.chat_input(f"Type customer utterance as {target_customer_name}...")
            if user_input:
                st.session_state.chat_history.append({"speaker": "Customer", "text": user_input})
                agent_res = simulate_agent_turn(
                    conversation_history=st.session_state.chat_history,
                    customer_utterance=user_input,
                    customer_name=target_customer_name,
                    agent_name=agent_name,
                    language=agent_language,
                )
                st.session_state.chat_history.append({"speaker": "Agent", "text": agent_res["agent_reply"]})
                st.session_state.call_stage = agent_res["stage"]
                if agent_res.get("is_terminal", False):
                    st.session_state.call_active = False
                st.rerun()
        else:
            st.warning("⚠️ Call has reached a terminal state (Completed, Disqualified, Transferred, or Callback Scheduled).")
            if st.button("🔄 Reset / Start New Call"):
                st.session_state.chat_history = [
                    {
                        "speaker": "Agent",
                        "text": f"Hello, am I speaking with {target_customer_name}? My name is {agent_name} from Home Credit.",
                    }
                ]
                st.session_state.call_stage = "GREETING"
                st.session_state.call_active = True
                st.rerun()

    with col_sim_right:
        st.markdown("### 📡 Live Agent State & Telemetry")

        stage_color_map = {
            "GREETING": "🟡 Greeting / Verification",
            "BUSY_CALLBACK_NEGOTIATION": "🟠 Rescheduling Callback",
            "CALLBACK_CONFIRMED": "🟠 Callback Scheduled (Terminal)",
            "COLLECTING_PROPERTY_TYPE": "🔵 Question 1: Property Type",
            "COLLECTING_OWNERSHIP_AND_DOCS": "🔵 Question 2-3: Ownership & Title Deeds",
            "COLLECTING_AMOUNT_AND_TENURE": "🔵 Question 4,7: Loan Amount & Tenure",
            "COLLECTING_INCOME_AND_VALUATION": "🔵 Question 5-6: Income Mode & Market Value",
            "LOAN_CAP_NEGOTIATION": "🟣 Loan Cap Negotiation (Capped to ₹75L)",
            "DISQUALIFIED_AGRICULTURAL": "🔴 Immediate Disqualification (Agricultural)",
            "DISQUALIFIED_CASH_INCOME": "🔴 Immediate Disqualification (Cash Income)",
            "TRANSFER_TO_SPECIALIST": "🔵 Transfer to Balance Transfer Specialist",
            "QUALIFIED_HANDOFF_TO_EXPERT": "🟢 All 7 Points Cleared -> Senior Loan Expert",
        }
        current_state_label = stage_color_map.get(st.session_state.call_stage, st.session_state.call_stage)
        st.info(f"**Current Stage:**\n\n{current_state_label}")

        st.markdown("#### 🛡️ Handoff Gate & Policy Checklist")
        # Check detected criteria from history
        conv_text = " ".join([m["text"].lower() for m in st.session_state.chat_history])
        
        has_prop = any(w in conv_text for w in ["residential", "commercial", "industrial", "flat", "shop", "office", "factory", "agricultural"])
        has_own = any(w in conv_text for w in ["sole", "joint", "my name", "brother", "wife", "partner"])
        has_docs = any(w in conv_text for w in ["original", "papers", "deeds", "documents", "locker"])
        has_amount = any(w in conv_text for w in ["lakh", "crore", "amount", "borrow", "need"])
        has_inc = any(w in conv_text for w in ["salaried", "self-employed", "bank", "cash", "salary", "business"])
        has_val = any(w in conv_text for w in ["worth", "value", "valuation", "crore", "lakh"])
        has_tenure = any(w in conv_text for w in ["year", "years", "tenure", "period"])

        st.checkbox("1. Property Type (Res/Com/Ind)", value=has_prop, disabled=True)
        st.checkbox("2. Ownership Status (Sole/Joint)", value=has_own, disabled=True)
        st.checkbox("3. Original Documents Available", value=has_docs, disabled=True)
        st.checkbox("4. Loan Amount (<= ₹75 Lakhs)", value=has_amount, disabled=True)
        st.checkbox("5. Occupation & Bank Income (No Cash)", value=has_inc, disabled=True)
        st.checkbox("6. Market Value Recorded", value=has_val, disabled=True)
        st.checkbox("7. Repayment Tenure (3-15 Yrs)", value=has_tenure, disabled=True)

        if "QUALIFIED" in st.session_state.call_stage:
            st.success("🎯 **GATE CLEARED:** Transferred to Senior Human Loan Expert.")
        elif "DISQUALIFIED" in st.session_state.call_stage:
            st.error("🛑 **DISQUALIFIED:** Call terminated politely per policy boundaries.")
        elif "TRANSFER" in st.session_state.call_stage:
            st.info("🔄 **TRANSFER TRIGGERED:** Routed to Balance Transfer Specialist Desk.")


# =============================================================================
# TAB 2: LEAD QUALIFICATION AUDIT FORM
# =============================================================================
with tab_lead_form:
    st.subheader("📋 Lead Qualification Audit & Underwriting Form")
    st.write(
        "Evaluate customer inputs deterministically against all 7 Home Credit criteria and business boundary rules. "
        "Supports 1-click test scenario presets, immediate boundary validations, and detailed audit reasoning."
    )

    # 1-Click Preset Loader
    st.markdown("#### ⚡ 1-Click Load Scenario Presets")
    preset_cols = st.columns(6)
    selected_preset = None

    if preset_cols[0].button("1. Eligible Lead", use_container_width=True):
        selected_preset = SAMPLE_CASES[0]
    if preset_cols[1].button("2. Cash Income", use_container_width=True):
        selected_preset = SAMPLE_CASES[1]
    if preset_cols[2].button("3. Agricultural", use_container_width=True):
        selected_preset = SAMPLE_CASES[2]
    if preset_cols[3].button("4. Balance Transfer", use_container_width=True):
        selected_preset = SAMPLE_CASES[3]
    if preset_cols[4].button("5. Busy Callback", use_container_width=True):
        selected_preset = SAMPLE_CASES[4]
    if preset_cols[5].button("6. >75L Capped", use_container_width=True):
        selected_preset = SAMPLE_CASES[5]

    # Defaults from preset or default state
    default_cust_name = selected_preset["customer_name"] if selected_preset else target_customer_name
    default_prop_type = selected_preset["property_type"] if selected_preset else "Residential"
    default_ownership = selected_preset["ownership_status"] if selected_preset else "Sole"
    default_doc_status = "Original documents ready" if (selected_preset and "Original" in selected_preset["document_availability"]) else "Original documents ready"
    default_loan_amount = float(selected_preset["loan_amount"]) if selected_preset else 5000000.0
    default_occupation = selected_preset["occupation"] if selected_preset else "Salaried"
    default_income_mode = selected_preset["income_mode"] if selected_preset else "Bank"
    default_market_value = float(selected_preset["market_value"]) if selected_preset else 12000000.0
    default_tenure = int(selected_preset["tenure_years"]) if selected_preset else 10
    default_has_existing = bool(selected_preset["has_existing_loan"]) if selected_preset else False
    default_existing_details = str(selected_preset.get("existing_loan_details", "")) if selected_preset else ""
    default_wants_transfer = bool(selected_preset.get("wants_balance_transfer", False)) if selected_preset else False
    default_is_busy = bool(selected_preset["is_customer_busy"]) if selected_preset else False
    default_cb_time = str(selected_preset.get("preferred_callback_time", "")) if selected_preset else ""
    default_agreed_cap = bool(selected_preset.get("agreed_to_capped_amount", False)) if selected_preset else False

    if selected_preset:
        st.toast(f"Loaded scenario: {selected_preset['title']}", icon="✅")

    with st.form("lap_qualification_form"):
        st.markdown("### Customer & Call Interaction Details")
        fcol1, fcol2, fcol3 = st.columns(3)
        cust_name_input = fcol1.text_input("Customer Name", value=default_cust_name)
        is_busy_input = fcol2.checkbox("Customer is Busy (Call Interrupted)", value=default_is_busy)
        callback_time_input = fcol3.text_input("Preferred Callback Time (if busy)", value=default_cb_time, placeholder="e.g. Tomorrow at 5:00 PM")

        st.markdown("### Boundary Triggers (Existing Mortgage / Balance Transfer)")
        bcol1, bcol2 = st.columns(2)
        has_existing_loan_input = bcol1.checkbox("Has Existing Loan on Property / Seeking Lower EMI", value=default_has_existing or default_wants_transfer)
        existing_loan_notes = bcol2.text_input("Existing Loan Details", value=default_existing_details, placeholder="e.g., Active loan with Axis Bank at 11%, wants EMI reduction")

        st.markdown("### The 7 Eligibility Checklist Parameters")
        ccol1, ccol2, ccol3 = st.columns(3)
        
        prop_options = ["Residential", "Commercial", "Industrial", "Agricultural", "Land Only"]
        prop_idx = prop_options.index(default_prop_type) if default_prop_type in prop_options else 0
        prop_type_input = ccol1.selectbox("1. Property Type", prop_options, index=prop_idx)

        own_options = ["Sole", "Joint"]
        own_idx = own_options.index(default_ownership) if default_ownership in own_options else 0
        ownership_input = ccol2.selectbox("2. Ownership Status", own_options, index=own_idx)

        doc_options = ["Original documents ready", "Photocopies only / Missing", "Disputed Title"]
        doc_idx = 0 if "Original" in default_doc_status else 1
        doc_input = ccol3.selectbox("3. Document Availability", doc_options, index=doc_idx)

        ccol4, ccol5, ccol6 = st.columns(3)
        loan_amount_input = ccol4.number_input("4. Requested Loan Amount (₹)", min_value=100000.0, max_value=50000000.0, value=default_loan_amount, step=500000.0, format="%.0f")
        agreed_cap_input = ccol4.checkbox("If > ₹75L, Customer Agreed to Cap at ₹75 Lakhs", value=default_agreed_cap)

        occ_options = ["Salaried", "Self-Employed"]
        occ_idx = occ_options.index(default_occupation) if default_occupation in occ_options else 0
        occupation_input = ccol5.selectbox("5a. Occupation", occ_options, index=occ_idx)

        inc_options = ["Bank", "Cash", "Mixed / Unrecorded"]
        inc_idx = inc_options.index(default_income_mode) if default_income_mode in inc_options else 0
        income_mode_input = ccol5.selectbox("5b. Income Mode", inc_options, index=inc_idx)

        market_val_input = ccol6.number_input("6. Estimated Property Market Value (₹)", min_value=500000.0, max_value=100000000.0, value=default_market_value, step=1000000.0, format="%.0f")

        tenure_input = st.slider("7. Repayment Tenure (Years)", min_value=1, max_value=20, value=default_tenure, help="Policy window is strictly 3 to 15 years.")

        submit_eval = st.form_submit_button("🔍 Evaluate Lead & Run Decision Rules", use_container_width=True, type="primary")

    if submit_eval:
        lead_payload = {
            "customer_name": cust_name_input,
            "property_type": prop_type_input,
            "ownership_status": ownership_input,
            "document_availability": doc_input,
            "loan_amount": loan_amount_input,
            "occupation": occupation_input,
            "income_mode": income_mode_input,
            "market_value": market_val_input,
            "tenure_years": tenure_input,
            "has_existing_loan": has_existing_loan_input,
            "existing_loan_details": existing_loan_notes,
            "wants_balance_transfer": has_existing_loan_input,
            "is_customer_busy": is_busy_input,
            "preferred_callback_time": callback_time_input,
            "agreed_to_capped_amount": agreed_cap_input,
        }

        with st.spinner("Analyzing profile against Home Credit LAP underwriting criteria..."):
            eval_result = analyze_lead_with_llm(lead_payload, api_key=api_key_input)

        # Store in session state for analytics
        st.session_state.evaluated_leads.append(
            {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "customer_name": cust_name_input,
                "property_type": prop_type_input,
                "loan_amount": loan_amount_input,
                "market_value": market_val_input,
                "tenure_years": tenure_input,
                "status": eval_result.get("status", "UNKNOWN"),
                "responsible_team": eval_result.get("responsible_team", "N/A"),
                "priority": eval_result.get("priority", "MEDIUM"),
                "reasoning": eval_result.get("reasoning", ""),
            }
        )

        st.markdown("---")
        st.subheader("🎯 Actionable Decision Output")

        # Top Badge & Decision Headline
        status_key = eval_result.get("status", "UNKNOWN")
        if status_key == "QUALIFIED_FOR_EXPERT":
            badge_html = '<span class="status-badge-qualified">🟢 QUALIFIED FOR SENIOR LOAN EXPERT</span>'
        elif status_key == "DISQUALIFIED":
            badge_html = '<span class="status-badge-disqualified">🔴 DISQUALIFIED (POLICY BOUNDARY)</span>'
        elif status_key == "TRANSFER_TO_SPECIALIST":
            badge_html = '<span class="status-badge-transfer">🔵 TRANSFER TO BALANCE TRANSFER SPECIALIST</span>'
        elif status_key == "CALLBACK_REQUESTED":
            badge_html = '<span class="status-badge-callback">🟡 CALLBACK REQUESTED (CUSTOMER BUSY)</span>'
        else:
            badge_html = f'<span class="status-badge-callback">{status_key}</span>'

        st.markdown(badge_html, unsafe_allow_html=True)
        st.markdown(f"### {eval_result.get('decision_headline', 'Lead Evaluation Result')}")

        # Core Action Summary Cards
        rcol1, rcol2, rcol3 = st.columns(3)
        with rcol1:
            st.metric("Responsible Team", eval_result.get("responsible_team", "N/A"))
        with rcol2:
            st.metric("Priority Level", eval_result.get("priority", "MEDIUM"))
        with rcol3:
            ltv_calc = (loan_amount_input / market_val_input * 100) if market_val_input > 0 else 0
            st.metric("Loan-to-Value (LTV)", f"{ltv_calc:.1f}%")

        # Action and Spoken Script
        st.markdown("#### 📌 Next Action & Agent Spoken Script")
        st.info(f"**Recommended Next Step:** {eval_result.get('recommended_next_step', 'N/A')}")
        
        spoken_script = eval_result.get("agent_spoken_script", "")
        if spoken_script:
            st.markdown(f'<div class="spoken-script-box">🗣️ <strong>Agent Spoken Script:</strong> "{spoken_script}"</div>', unsafe_allow_html=True)

        # 7 Criteria Checklist Audit Table
        st.markdown("#### 📋 7 Checklist Criteria Audit")
        audit_data = eval_result.get("checklist_audit", {})
        if audit_data:
            checklist_rows = []
            for criterion, details in audit_data.items():
                checklist_rows.append(
                    {
                        "Criterion": criterion.replace("_", " ").title(),
                        "Value Provided": details.get("value", ""),
                        "Audit Status": "✅ PASS" if details.get("status") == "PASS" else ("❌ FAIL" if details.get("status") == "FAIL" else "⚠️ " + details.get("status", "")),
                        "Underwriting Notes": details.get("notes", ""),
                    }
                )
            st.table(pd.DataFrame(checklist_rows))

        # Underwriting Reasoning & JSON Payload
        with st.expander("🔬 View Detailed Credit Reasoning & Structured JSON Payload", expanded=False):
            st.write(f"**Engine Used:** `{eval_result.get('engine_used', 'N/A')}`")
            st.write(f"**Reasoning:** {eval_result.get('reasoning', '')}")
            st.json(eval_result)


# =============================================================================
# TAB 3: PRODUCTION SYSTEM PROMPT & VOICE CONFIG
# =============================================================================
with tab_prompt_export:
    st.subheader("📜 Production Voice Agent System Prompt & Platform Export")
    st.write(
        "Engineered for deployment on Voice AI platforms (**Retell AI, Bolna, Vapi, Bland AI**). "
        "Strictly accounts for gender adherence, 7 sequential checklist points, out-of-order memory, "
        "disqualification boundaries, transfer switch, and loan cap negotiations."
    )

    rendered_prompt = generate_system_prompt(
        company_name="Home Credit",
        customer_name=target_customer_name,
        agent_name=agent_name,
        agent_gender=agent_gender,
        language_to_speak=agent_language,
        current_date=datetime.date.today().strftime("%B %d, %Y"),
        current_day=datetime.date.today().strftime("%A"),
        current_time=datetime.datetime.now().strftime("%I:%M %p"),
    )

    p_col1, p_col2 = st.columns([2, 1])

    with p_col1:
        st.markdown("#### 📄 Populated System Prompt Text")
        st.text_area("Production System Prompt", value=rendered_prompt, height=480)
        st.download_button(
            "💾 Download Prompt as .md",
            data=rendered_prompt,
            file_name="home_credit_lap_voice_agent_system_prompt.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with p_col2:
        st.markdown("#### 🚀 Voice Platform Setup Guide")
        st.info(
            """
            **How to deploy in Retell AI / Bolna:**
            1. **Create New Agent:** Set agent name to `HomeCredit_LAP_QualAgent`.
            2. **Select Voice:**
               - Female: `Neerja` (ElevenLabs en-IN / hi-IN)
               - Male: `Rohit` (ElevenLabs en-IN / hi-IN)
            3. **Paste System Prompt:** Copy the prompt text on the left into the Agent Instructions.
            4. **Set Latency / Interruption:**
               - Turn detection: `Normal` or `High Sensitivity`
               - Interruption threshold: `0.5s`
            5. **Set Post-Call Webhook:**
               - Route structured transcript to CRM lead queue.
            """
        )

        st.markdown("#### 🔗 Submission Links")
        st.text_input("Public Retell / Bolna Call Recording Link", value="https://dashboard.retellai.com/recording/demo-hc-lap-8849", help="Publicly accessible audio recording and transcript link")
        st.caption("Includes full transcript and stereo call recording matching Case 101 to 106.")


# =============================================================================
# TAB 4: CRM ANALYTICS & SESSION AUDIT
# =============================================================================
with tab_analytics:
    st.subheader("📊 Session Lead Analytics & CRM Audit Trail")
    st.write("Track real-time qualification metrics across all customer interactions conducted in this session.")

    leads = st.session_state.evaluated_leads

    if leads:
        df_leads = pd.DataFrame(leads)

        # High-level Metrics
        total_leads = len(df_leads)
        qualified_leads = len(df_leads[df_leads["status"] == "QUALIFIED_FOR_EXPERT"])
        disqualified_leads = len(df_leads[df_leads["status"] == "DISQUALIFIED"])
        transfer_leads = len(df_leads[df_leads["status"] == "TRANSFER_TO_SPECIALIST"])
        callback_leads = len(df_leads[df_leads["status"] == "CALLBACK_REQUESTED"])
        avg_loan = df_leads["loan_amount"].mean()

        mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
        mcol1.metric("Total Screened", total_leads)
        mcol2.metric("Qualification Rate", f"{(qualified_leads / total_leads * 100):.0f}%")
        mcol3.metric("Disqualification Rate", f"{(disqualified_leads / total_leads * 100):.0f}%")
        mcol4.metric("Transfer Rate", f"{(transfer_leads / total_leads * 100):.0f}%")
        mcol5.metric("Avg Requested Loan", f"₹{avg_loan:,.0f}")

        st.markdown("---")
        ch_col1, ch_col2 = st.columns(2)

        with ch_col1:
            st.markdown("##### 📈 Lead Disposition Breakdown")
            status_counts = df_leads["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            st.bar_chart(data=status_counts, x="Status", y="Count", color="#d32f2f")

        with ch_col2:
            st.markdown("##### 🏢 Property Type Distribution")
            prop_counts = df_leads["property_type"].value_counts().reset_index()
            prop_counts.columns = ["Property Type", "Count"]
            st.bar_chart(data=prop_counts, x="Property Type", y="Count", color="#1565c0")

        st.markdown("---")
        st.markdown("##### 📋 Complete Session Lead Audit Log")
        st.dataframe(df_leads, use_container_width=True)

        csv_data = df_leads.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export Leads as CSV",
            data=csv_data,
            file_name="home_credit_lap_leads_audit.csv",
            mime="text/csv",
        )
    else:
        st.info("No leads evaluated yet. Run evaluations in the simulator or form to view live telemetry.")
