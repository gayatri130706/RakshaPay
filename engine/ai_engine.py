import os, time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
_gemini_model = None

def _get_model():
    global _gemini_model
    if _gemini_model:
        return _gemini_model
    if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here':
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print('[AI] Gemini 1.5 Flash engine loaded')
        return _gemini_model
    except Exception as e:
        print(f'[AI] Gemini load failed: {e}')
        return None

def generate_fraud_narrative(transaction_data: Dict[str, Any]) -> str:
    model = _get_model()
    risk_score = transaction_data.get('risk_score', 0)
    risk_tier = transaction_data.get('risk_tier', 'LOW')
    vpa = transaction_data.get('recipient_vpa', '')
    amount = transaction_data.get('amount', 0)
    scam_cat = transaction_data.get('scam_category', 'unknown')
    xai = transaction_data.get('xai_explanation', {})

    if not model:
        return _fallback_narrative(risk_score, risk_tier, scam_cat, amount, vpa)

    prompt = f"""You are RakshaPay, an AI fraud detection system for Indian UPI payments.
Analyse this transaction and give a 2-3 sentence plain-English fraud warning for the user.
Be specific, cite the signals detected, and tell the user what action to take.

Transaction details:
- Recipient VPA: {vpa}
- Amount: Rs {amount}
- Risk Score: {risk_score}/100
- Risk Tier: {risk_tier}
- Detected Scam Category: {scam_cat}
- Top AI signals: {xai.get('top_factors', [])}

Write the warning in simple Hindi-English (Hinglish) or plain English. Maximum 3 sentences. Start with the risk level."""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return _fallback_narrative(risk_score, risk_tier, scam_cat, amount, vpa)

def chat_with_fraud_advisor(user_message: str, conversation_history: list = None) -> str:
    model = _get_model()
    if not model:
        return _fallback_chat(user_message)

    system = """You are RakshaPay's AI Fraud Advisor - an expert in UPI payment fraud, 
Indian cybercrime patterns, and digital safety. Help users understand:
- How UPI fraud works
- How to identify scams
- What to do if they sent money to a fraudster
- How to report cybercrime (helpline: 1930, cybercrime.gov.in)
- RakshaPay's detection engines and how they work
Be concise, factual, and helpful. Use simple language. Respond in 2-4 sentences max."""

    try:
        history = conversation_history or []
        chat = model.start_chat(history=[
            {'role': h['role'], 'parts': [h['content']]} for h in history[-6:]
        ])
        response = chat.send_message(f"System context: {system}\n\nUser: {user_message}")
        return response.text.strip()
    except Exception as e:
        return _fallback_chat(user_message)

def _fallback_narrative(risk_score, risk_tier, scam_cat, amount, vpa):
    if risk_tier == 'CRITICAL':
        return f'CRITICAL ALERT: This transaction to {vpa} has a fraud risk score of {risk_score}/100. Detected pattern matches {scam_cat} scam. Do NOT proceed - disconnect any calls and contact 1930 immediately.'
    elif risk_tier == 'HIGH':
        return f'HIGH RISK: Transaction to {vpa} scored {risk_score}/100. This matches known {scam_cat} fraud patterns. Verify the recipient independently before sending Rs {amount}.'
    elif risk_tier == 'MEDIUM':
        return f'CAUTION: Moderate risk detected for this transaction. Verify that you know and trust the recipient before proceeding.'
    return f'Transaction appears safe. Risk score: {risk_score}/100. Proceed with standard caution.'

def _fallback_chat(message):
    msg = message.lower()
    if 'kyc' in msg or 'otp' in msg:
        return 'Never share your OTP or KYC details with anyone over call or message. Banks never ask for this. If asked, it is a scam - report on 1930.'
    if 'report' in msg or 'helpline' in msg or '1930' in msg:
        return 'Report UPI fraud immediately on National Cyber Crime Helpline: 1930 or online at cybercrime.gov.in. Act within 24 hours to maximize chance of fund recovery.'
    if 'score' in msg or 'risk' in msg:
        return 'RakshaPay calculates a 0-100 risk score using 4 AI engines: VPA spoofing detector, NLP scam phrase analyzer, fraud ring graph detector, and ML ensemble. Scores above 75 trigger CRITICAL alerts.'
    if 'refund' in msg or 'money back' in msg:
        return 'If you were scammed, file a complaint on cybercrime.gov.in within 24 hours. Also call 1930 and contact your bank to freeze the beneficiary account. Speed is critical.'
    return 'I am RakshaPay AI Fraud Advisor. I can help you understand UPI fraud patterns, explain risk scores, or guide you on what to do if you suspect a scam. What would you like to know?'

_get_model()