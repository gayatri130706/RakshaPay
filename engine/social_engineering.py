"""ByteShield - Module 2: Social Engineering & Behavioral Telemetry Engine
Detects transaction patterns, NLP notes, and behavioral context associated with
Digital Arrest, Fake Customer Care, Reverse Collect Scams, and Urgency Pressure.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional


# Scam Intent Dictionaries for Indian UPI threat vectors
SCAM_PATTERNS = {
    "digital_arrest": {
        "keywords": [
            r"cbi|police|narcotics|customs|court|arrest|warrant|fir|bail|trai|sim block",
            r"money laundering|illegal parcel|cyber cell|dcp|crime branch|security deposit",
            r"verification charge|case settlement|clearance bond|supreme court|ed office"
        ],
        "category": "Digital Arrest / Institutional Coercion Scam",
        "base_risk": 95,
        "advice": "Police, CBI, or Courts NEVER conduct investigations or demand bail/security deposits via UPI video calls."
    },
    "fake_customer_care": {
        "keywords": [
            r"refund release|customer care|helpdesk|support desk|activation fee|reversal",
            r"anydesk|teamviewer|rustdesk|quicksupport|screen share|apk install",
            r"kyc update|pan link|account block|sim 5g upgrade|card unblock"
        ],
        "category": "Fake Customer Care / Remote Access Scam",
        "base_risk": 85,
        "advice": "Banks and service providers never ask you to install AnyDesk/screen-share apps or send money to receive a refund."
    },
    "reverse_collect_scam": {
        "keywords": [
            r"receive money|accept reward|cashback|cash back|claim|lottery|kbc prize|reward points",
            r"scan qr to receive|enter pin to credit|winner|olx buyer|advance token|receive ₹"
        ],
        "category": "Reverse Collect Request / Fake QR Scam",
        "base_risk": 90,
        "advice": "CRITICAL: You NEVER need to enter your UPI PIN to RECEIVE money. Entering your PIN will DEDUCT funds from your bank account!"
    },
    "utility_threat": {
        "keywords": [
            r"electricity disconnect|power cut|bill update|officer contact|tonight 9:30",
            r"gas connection block|challan overdue|traffic fine|challan payment"
        ],
        "category": "Urgent Utility Disconnection Threat",
        "base_risk": 80,
        "advice": "Electricity boards never send personal UPI IDs for bill clearance with immediate power disconnection threats."
    },
    "task_crypto_scam": {
        "keywords": [
            r"telegram task|youtube like|vip upgrade|daily earning|crypto task|part time job",
            r"double profit|investment return|prepaid task|bonus task|commission"
        ],
        "category": "Part-Time Task & Investment Fraud",
        "base_risk": 88,
        "advice": "Prepaid task schemes that promise high daily returns for rating videos or crypto deposits are fraudulent."
    }
}


class SocialEngineeringEngine:
    """Evaluates Social Engineering and Telemetry Indicators."""

    def __init__(self):
        self.compiled_rules = {}
        for key, config in SCAM_PATTERNS.items():
            self.compiled_rules[key] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in config["keywords"]],
                "category": config["category"],
                "base_risk": config["base_risk"],
                "advice": config["advice"]
            }

    def evaluate_transaction(
        self,
        note: Optional[str] = "",
        transaction_type: str = "DIRECT_PAY",
        amount: float = 0.0,
        sender_baseline_avg: float = 1200.0,
        timestamp_hour: Optional[int] = None,
        recipient_is_new_contact: bool = True,
        call_active_during_payment: bool = False,
        screen_sharing_detected: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze social engineering context, NLP remarks, and user behavioral telemetry.
        """
        note_clean = (note or "").strip()
        matched_scams: List[Dict[str, Any]] = []
        triggers: List[str] = []
        social_risk = 0
        urgency_level = "LOW"

        # 1. Evaluate NLP Note against Scam Patterns
        for scam_key, config in self.compiled_rules.items():
            for regex in config["patterns"]:
                match = regex.search(note_clean)
                if match:
                    matched_scams.append(config)
                    triggers.append(f"Scam Remark Match: Detected '{match.group(0)}' ({config['category']})")
                    social_risk = max(social_risk, config["base_risk"])
                    urgency_level = "HIGH"
                    break

        # 2. Reverse Collect Request Scam Check
        if transaction_type == "COLLECT_REQUEST":
            if any(term in note_clean.lower() for term in ["refund", "credit", "receive", "cashback", "reward", "win", "prize", "accept"]):
                social_risk = max(social_risk, 95)
                triggers.append("Reverse Collect Attack: Incoming Collect Request is masquerading as a refund/credit.")
                urgency_level = "CRITICAL"
                if not matched_scams:
                    matched_scams.append(self.compiled_rules["reverse_collect_scam"])
            elif recipient_is_new_contact:
                social_risk = max(social_risk, 40)
                triggers.append("New Payee Collect Request: Payer is authorizing an unsolicited funds withdrawal.")

        # 3. Telemetry: Active Call or Screen Sharing during payment
        if screen_sharing_detected:
            social_risk += 45
            triggers.append("Active Screen Mirroring / Remote Desktop tool detected on device (AnyDesk/TeamViewer signature).")
            urgency_level = "CRITICAL"

        if call_active_during_payment and recipient_is_new_contact:
            social_risk += 30
            triggers.append("Continuous Active Call during payment to an unknown recipient (Coercion Indicator).")
            if urgency_level != "CRITICAL":
                urgency_level = "HIGH"

        # 4. Telemetry: Amount Deviation vs Sender Baseline
        if sender_baseline_avg > 0 and amount > 0:
            ratio = amount / sender_baseline_avg
            if ratio >= 8.0 and amount >= 15000:
                social_risk += 25
                triggers.append(f"Amount Velocity Spike: ₹{amount:,.2f} is {ratio:.1f}x higher than typical transfer.")
            elif ratio >= 4.0 and amount >= 5000:
                social_risk += 15
                triggers.append(f"Unusual Transaction Size: {ratio:.1f}x higher than average.")

        # 5. Timing / Coercion Window
        current_hour = timestamp_hour if timestamp_hour is not None else datetime.now().hour
        if 1 <= current_hour <= 5 and amount > 5000 and recipient_is_new_contact:
            social_risk += 20
            triggers.append(f"Unusual Time-of-Day ({current_hour}:00 AM): Coercion attacks heavily target late-night hours.")

        social_risk = min(100, max(0, social_risk))
        primary_scam = matched_scams[0] if matched_scams else None

        return {
            "social_risk_score": social_risk,
            "is_social_engineered": social_risk >= 50,
            "urgency_level": urgency_level,
            "detected_triggers": triggers if triggers else ["Normal transaction remarks and telemetry."],
            "scam_category": primary_scam["category"] if primary_scam else "None",
            "protective_advice": primary_scam["advice"] if primary_scam else "Always double check recipient details before entering PIN."
        }


social_engine_instance = SocialEngineeringEngine()
