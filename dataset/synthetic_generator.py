"""ByteShield - Synthetic Dataset & Demo Scenario Catalog
Generates benchmark Indian UPI metadata and pre-configured real-world threat scenarios.
"""

from typing import Dict, Any, List

DEMO_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "digital_arrest",
        "title": "🚨 Scenario 1: 'Digital Arrest' Coercion Scam",
        "subtitle": "Impostor posing as CBI/Police on video call demanding urgent clearance deposit",
        "sender_vpa": "gayatri@okaxis",
        "recipient_vpa": "cbi-investigation-cell@ybl",
        "amount": 48500,
        "note": "Urgent security deposit bond clearance case CBI-40291",
        "transaction_type": "DIRECT_PAY",
        "call_active": True,
        "screen_sharing": False,
        "hour_of_day": 2,
        "expected_risk": "CRITICAL",
        "explanation_focus": "Digital Arrest NLP match, shared device ring, late-night coercion window."
    },
    {
        "id": "sbi_typosquatting",
        "title": "⚠️ Scenario 2: Fake SBI Customer Care Spoof",
        "subtitle": "Spoofed bank helpdesk handle discovered via fake Google ad",
        "sender_vpa": "gayatri@okaxis",
        "recipient_vpa": "sbi-customercare-support@ybl",
        "amount": 24999,
        "note": "SBI credit card refund reversal charge",
        "transaction_type": "DIRECT_PAY",
        "call_active": True,
        "screen_sharing": True,
        "hour_of_day": 15,
        "expected_risk": "CRITICAL",
        "explanation_focus": "Levenshtein similarity to official SBI support, AnyDesk screen sharing signature."
    },
    {
        "id": "zero_day_mule",
        "title": "⚡ Scenario 3: Zero-Day Mule Account & Task Scam",
        "subtitle": "Unregistered 1-hour old account part of a Telegram investment fraud ring",
        "sender_vpa": "gayatri@okaxis",
        "recipient_vpa": "earn-daily-bonus99@okicici",
        "amount": 15000,
        "note": "Telegram VIP task prepaid upgrade level 3",
        "transaction_type": "DIRECT_PAY",
        "call_active": False,
        "screen_sharing": False,
        "hour_of_day": 18,
        "expected_risk": "HIGH",
        "explanation_focus": "Account age < 2 hours, graph mule fan-out detection, rapid fund dispersal."
    },
    {
        "id": "reverse_collect",
        "title": "🔄 Scenario 4: Reverse Collect Request Fraud",
        "subtitle": "Scammer sends Collect Request promising victim will receive money by entering PIN",
        "sender_vpa": "gayatri@okaxis",
        "recipient_vpa": "refund-collector-99@paytm",
        "amount": 8500,
        "note": "Accept to receive ₹8,500 cashback reward",
        "transaction_type": "COLLECT_REQUEST",
        "call_active": False,
        "screen_sharing": False,
        "hour_of_day": 11,
        "expected_risk": "CRITICAL",
        "explanation_focus": "Collect Request inverted intent: user entering PIN will lose funds."
    },
    {
        "id": "legit_merchant",
        "title": "✅ Scenario 5: Legitimate Food Delivery Payment",
        "subtitle": "Normal consumer payment to verified merchant Swiggy with zero anomaly flags",
        "sender_vpa": "gayatri@okaxis",
        "recipient_vpa": "swiggy@icici",
        "amount": 450,
        "note": "Dinner order Swiggy #88219",
        "transaction_type": "DIRECT_PAY",
        "call_active": False,
        "screen_sharing": False,
        "hour_of_day": 20,
        "expected_risk": "LOW",
        "explanation_focus": "Verified merchant VPA, established account age, low risk score."
    }
]


def get_demo_scenarios() -> List[Dict[str, Any]]:
    return DEMO_SCENARIOS
