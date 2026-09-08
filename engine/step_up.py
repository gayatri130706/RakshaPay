"""ByteShield - Module 7: Pre-PIN Step-Up Anti-Coercion & Dynamic CAPTCHA Engine
Generates anti-coercion awareness verification and human math challenges to break
psychological panic manipulation and stop automated/remote bot payments.
"""

import random
from typing import Dict, Any, Optional


class StepUpEngine:
    """Generates dynamic anti-coercion challenges and human CAPTCHA checks."""

    @staticmethod
    def generate_challenge(
        risk_level: str,
        scam_category: str,
        amount: float,
        is_new_payee: bool
    ) -> Dict[str, Any]:
        """
        Create a tailored step-up challenge based on transaction risk and threat vector.
        """
        requires_challenge = (risk_level in ["MEDIUM", "HIGH", "CRITICAL"]) or (amount >= 10000 and is_new_payee)

        if not requires_challenge:
            return {
                "requires_challenge": False,
                "challenge_type": "NONE",
                "challenge_data": None
            }

        captcha_text = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=5))
        math_question = f"Type this code to verify: {captcha_text}"
        correct_math_answer = captcha_text

        if "Digital Arrest" in scam_category or "Coercion" in scam_category or risk_level == "CRITICAL":
            awareness_statement = "Official Advisory: Government enforcement agencies (CBI, Police, ED) NEVER demand money transfers or video call deposits under Indian Law."
            confirmation_question = "Are you being instructed by someone claiming to be Law Enforcement / Police on a call right now?"
            required_checkbox = "I understand that police never ask for UPI payments, and I take personal responsibility for this transfer."
            challenge_type = "ANTI_COERCION_CHECK"
        elif "Reverse Collect" in scam_category or "QR" in scam_category:
            awareness_statement = "Warning: You are transferring OUT funds. You never need to enter a UPI PIN to receive money."
            confirmation_question = "Are you expecting to RECEIVE money from this transaction?"
            required_checkbox = "I confirm that I intend to SEND money, and no one instructed me to enter PIN for receiving a refund."
            challenge_type = "REVERSE_SCAM_CHECK"
        elif amount >= 15000:
            awareness_statement = f"High-Value Transfer Alert: You are transferring a substantial amount (₹{amount:,.2f}) to a new or unverified recipient."
            confirmation_question = "Have you personally met or verbally verified this recipient outside of Telegram/WhatsApp?"
            required_checkbox = "I have verified this recipient independently."
            challenge_type = "HIGH_VALUE_CAPTCHA"
        else:
            awareness_statement = "Security Verification: This transaction has triggered anomalous risk indicators."
            confirmation_question = "Do you wish to proceed despite security alerts?"
            required_checkbox = "I acknowledge the security advisory."
            challenge_type = "STANDARD_STEP_UP"

        return {
            "requires_challenge": True,
            "challenge_type": challenge_type,
            "awareness_statement": awareness_statement,
            "confirmation_question": confirmation_question,
            "required_checkbox": required_checkbox,
            "math_question": math_question,
            "expected_math_answer": correct_math_answer,
            "cooldown_seconds": 5 if risk_level == "CRITICAL" else 3
        }

    @staticmethod
    def verify_challenge(
        challenge_type: str,
        user_math_answer: Optional[str],
        expected_math_answer: Optional[str],
        acknowledged_checkbox: bool,
        is_coerced_answer: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Verify the user's submitted response to the challenge."""
        if is_coerced_answer is True and challenge_type == "ANTI_COERCION_CHECK":
            return {
                "success": False,
                "action": "BLOCK_TRANSACTION",
                "message": "🚨 TRANSACTION BLOCKED: You indicated you are on a call with alleged law enforcement. Disconnect the call immediately and dial 1930 (National Cyber Crime Helpline)."
            }

        if str(user_math_answer or "").strip() != str(expected_math_answer or "").strip():
            return {
                "success": False,
                "action": "RETRY_CAPTCHA",
                "message": "Incorrect verification answer. Please recalculate the anti-bot check."
            }

        if not acknowledged_checkbox:
            return {
                "success": False,
                "action": "REQUIRE_CHECKBOX",
                "message": "You must acknowledge the security advisory before entering your UPI PIN."
            }

        return {
            "success": True,
            "action": "ALLOW_PIN_ENTRY",
            "message": "Challenge passed. You may proceed to enter your UPI PIN."
        }


step_up_instance = StepUpEngine()
