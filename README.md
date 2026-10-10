# Home Credit — Loan Against Property (LAP) AI Voice Agent Prototype

An end-to-end AI Voice Agent qualification and underwriting triage prototype built for **Home Credit**. Designed to engage existing valued customers, present pre-approved Loan Against Property (LAP) loyalty offers up to ₹75,00,000 (75 Lakhs), capture 7 key underwriting parameters sequentially (with out-of-order conversational handling), enforce strict business boundaries, and hand off qualified leads to Senior Human Loan Experts.

---

## 🎯 Business Architecture & Problem Overview

### 1. Usecase
Deploy an automated AI Voice Agent for **Home Credit** to contact existing valued customers to:
- Acknowledge their loyalty.
- Offer a pre-approved Loan Against Property (LAP) up to **₹75,00,000 (75 Lakhs)**.
- Act as the first point of contact to conduct a preliminary eligibility check across 7 core underwriting parameters.
- Route qualified leads to a senior human loan expert or appropriate specialized teams.

---

## 📋 The 7 Eligibility Checklist Parameters

| # | Parameter | Accepted / Eligible Criteria | Immediate Disqualification / Action |
|---|---|---|---|
| **1** | **Property Type** | Residential (flat/house), Commercial (shop/office), Industrial (factory) | **Agricultural land is strictly ineligible.** Call ends politely. |
| **2** | **Ownership Status** | Sole ownership or Joint ownership (family/business partners) | Unverified ownership flagged. |
| **3** | **Document Availability** | **Original title deeds ready** for verification | Photocopies only or missing original papers is ineligible. |
| **4** | **Loan Amount** | Up to **₹75,00,000 (75 Lakhs)** | If > ₹75L requested, bot explains limit and negotiates to proceed with ₹75L cap. |
| **5** | **Occupation & Income Mode** | Salaried or Self-Employed with **Bank transfer / credit** | **Income received in CASH is strictly disqualified.** |
| **6** | **Market Value** | Positive estimated valuation (used for LTV calculation) | Flagged if zero or unreasonable. |
| **7** | **Repayment Tenure** | **3 to 15 years** (36 to 180 months) | Tenures < 3 yrs or > 15 yrs guided back into policy range. |

---

## 🛡️ Business Boundaries & Logic Switches

1. **Immediate Disqualification Boundary:**
   - If the customer reveals that their property is Agricultural, or their income is received in Cash, or they lack original documents, the agent does not continue interrogation. It politely explains the policy constraint and immediately ends the call.
2. **The "Transfer" Logic Switch:**
   - The primary flow is for **Fresh Loans**. If the customer mentions an existing loan on the property or wants to reduce their current EMI, the agent triggers the Balance Transfer switch, promises a callback from the specialized Loan Transfer Desk, and concludes the call.
3. **Loan Amount Negotiation:**
   - If the customer asks for > ₹75 Lakhs (e.g. ₹1.2 Crore), the agent explains the ₹75L campaign ceiling and asks if they want to proceed with the maximum ₹75 Lakhs.
4. **Busy State Protocol:**
   - If the customer states they are in a meeting, driving, or busy, the agent immediately acknowledges, asks for a preferred callback time, records it, and ends the call courteously.
5. **Strict Handoff Gate:**
   - Transitions to a Senior Human Loan Expert only when all 7 checklist points are satisfied.

---

## 🏗️ System Architecture & Tech Stack

```
home-credit-lap-voice-agent/
├── app.py                   # Streamlit interactive application & dashboard
├── business_rules.py        # 100% Deterministic policy engine & boundary validator
├── llm_engine.py            # Hybrid engine: Gemini LLM API + Automatic Deterministic Fallback
├── voice_agent_prompt.py    # Production-ready System Prompt for Voice AI platforms
├── sample_cases.py          # 6 Real-world end-to-end customer test scenarios
├── requirements.txt         # Dependencies (streamlit, pandas, requests)
└── README.md                # Comprehensive documentation
```

- **Python 3.8+**
- **Streamlit** for reactive enterprise dashboarding.
- **Pandas** for CRM lead management, tabular audit logs, and analytics.
- **Gemini API (via REST)** with strict JSON schema, paired with a deterministic Python rules engine for 100% offline fallback resilience.
- **Web Speech API** integration for in-browser speech synthesis of agent responses.

---

## ⚡ Quick Start: Running the Prototype

### 1. Ensure Dependencies
```powershell
pip install -r requirements.txt
```
*(Dependencies `streamlit`, `pandas`, and `requests` are already installed).*

### 2. Launch the Application
Run the following command from this directory:
```powershell
streamlit run app.py
```

### 3. Optional: Set Gemini API Key
To enable Gemini LLM evaluation in addition to the deterministic engine:
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
```
*Note: The prototype is fully functional without an API key thanks to the built-in deterministic underwriting rule engine.*

---

## 🧪 Included Representative Test Cases

| Case ID | Scenario Name | Profile Highlights | Expected Disposition | Destination Team |
|---|---|---|---|---|
| **CASE-101** | **Eligible Fresh Loan** | Residential flat, Sole, Originals ready, ₹45L, Salaried/Bank, 10 yrs | `QUALIFIED_FOR_EXPERT` | Senior Human Loan Expert Team |
| **CASE-102** | **Cash Income Disqualification** | Commercial shop, Joint, ₹35L, Self-Employed, **Income in Cash** | `DISQUALIFIED` | Disqualification CRM Archive |
| **CASE-103** | **Agricultural Disqualification** | **Agricultural land (5 acres)**, ₹50L, Salaried/Bank | `DISQUALIFIED` | Disqualification CRM Archive |
| **CASE-104** | **Balance Transfer Switch** | Residential, ₹60L, **Active mortgage with another NBFC / seeks lower EMI** | `TRANSFER_TO_SPECIALIST` | Balance Transfer Specialist Desk |
| **CASE-105** | **Busy Customer Callback** | Customer in urgent board meeting; callback at 6:30 PM | `CALLBACK_REQUESTED` | Outbound Auto-Dialer Queue |
| **CASE-106** | **Loan Ceiling Negotiation** | Commercial office, asks ₹1.2 Cr; **accepts ₹75 Lakhs pre-approved cap** | `QUALIFIED_FOR_EXPERT` | Senior Human Loan Expert Team |

---

## 🎙️ Retell AI / Bolna / Voice Platform Deployment

1. **System Prompt**: Access the complete, parameterized prompt in Tab 3 of the application or view `voice_agent_prompt.py`.
2. **Variables Supported**:
   - `company_name`: "Home Credit"
   - `customer_name`: Dynamically injected per call
   - `agent_name`: "Priya" (Female) or "Aarav" (Male)
   - `agent_gender`: Strictly adhered to
   - `current_date`, `current_day`, `current_time`
   - `language_to_speak`: English / Hindi
   - `additional_context_from_rag`: Interest rates (from 9.25% p.a.), pre-approved limits, 50% processing fee waiver.
3. **Platform Audio Setup**:
   - Voice: `Neerja` (ElevenLabs en-IN/hi-IN) or `Rohit`
   - Turn detection: Low latency (`0.5s` interruption threshold).
