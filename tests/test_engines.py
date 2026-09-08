"""ByteShield - Automated Test Suite
Validates all 7 fraud detection engines, pre-PIN interception, and latency constraints.
"""

import unittest
import time

from engine.vpa_analyzer import VPAAnalyzer, levenshtein_distance
from engine.social_engineering import SocialEngineeringEngine
from engine.mule_graph import MuleGraphEngine
from engine.ml_engine import MLEngine
from engine.xai_engine import XAIEngine
from engine.tokenizer import UPITokenizer
from engine.step_up import StepUpEngine
from engine.fraud_pipeline import ByteShieldPipeline


class TestByteShieldEngines(unittest.TestCase):

    def setUp(self):
        self.vpa_analyzer = VPAAnalyzer()
        self.social_engine = SocialEngineeringEngine()
        self.mule_engine = MuleGraphEngine()
        self.ml_engine = MLEngine()
        self.xai_engine = XAIEngine()
        self.tokenizer = UPITokenizer()
        self.step_up_engine = StepUpEngine()
        self.pipeline = ByteShieldPipeline()

    def test_levenshtein_and_vpa_spoof(self):
        # 1. Official VPA
        res_official = self.vpa_analyzer.analyze_vpa("support.sbi@ybl")
        self.assertTrue(res_official["is_official"])
        self.assertEqual(res_official["risk_score"], 0)

        # 2. Typosquatted / Impersonation VPA
        res_spoof = self.vpa_analyzer.analyze_vpa("sbi-customercare-support@ybl")
        self.assertTrue(res_spoof["is_spoof"])
        self.assertGreaterEqual(res_spoof["risk_score"], 60)
        self.assertTrue(any("Typosquatting" in r or "Impersonation" in r for r in res_spoof["detection_reasons"]))

        # 3. Edit distance algorithm test
        dist = levenshtein_distance("support.sbi", "support-sbi")
        self.assertEqual(dist, 1)

    def test_social_engineering_detection(self):
        # 1. Digital Arrest scam remark
        res_arrest = self.social_engine.evaluate_transaction(
            note="Urgent CBI investigation security deposit bond case 402",
            call_active_during_payment=True,
            amount=45000
        )
        self.assertTrue(res_arrest["is_social_engineered"])
        self.assertGreaterEqual(res_arrest["social_risk_score"], 80)
        self.assertIn("Digital Arrest", res_arrest["scam_category"])

        # 2. Reverse Collect Request Scam
        res_collect = self.social_engine.evaluate_transaction(
            note="Click to receive ₹5000 cashback reward",
            transaction_type="COLLECT_REQUEST",
            amount=5000
        )
        self.assertTrue(res_collect["is_social_engineered"])
        self.assertIn("Reverse Collect", res_collect["scam_category"])

    def test_mule_graph_and_zero_day(self):
        # 1. Fresh Zero-Day account (<2 hours old)
        res_graph = self.mule_engine.evaluate_graph_risk(
            sender_vpa="gayatri@okaxis",
            receiver_vpa="earn-daily-bonus99@okicici",
            amount=15000
        )
        self.assertTrue(res_graph["is_zero_day"])
        self.assertGreaterEqual(res_graph["graph_risk_score"], 60)

        # 2. Fan-out mule ring member
        res_mule = self.mule_engine.evaluate_graph_risk(
            sender_vpa="gayatri@okaxis",
            receiver_vpa="cbi-investigation-cell@ybl",
            amount=48000
        )
        self.assertTrue(res_mule["is_blacklisted"] or res_mule["is_mule_ring_member"])
        self.assertGreaterEqual(res_mule["graph_risk_score"], 90)

    def test_upi_tokenization_and_masking(self):
        # 1. Hyphenated spoof masking
        masked = self.tokenizer.mask_vpa("cbi-investigation-cell@ybl")
        self.assertIn("-***-", masked)
        self.assertTrue(masked.endswith("@ybl"))

        # 2. Phone number masking
        masked_phone = self.tokenizer.mask_vpa("9876543210@paytm")
        self.assertEqual(masked_phone, "98****3210@paytm")

        # 3. Token & Badge metadata
        badge_info = self.tokenizer.generate_token_and_badge("cbi-investigation-cell@ybl", "CRITICAL", False)
        self.assertTrue(badge_info["token_id"].startswith("TOK-UPI-"))
        self.assertEqual(badge_info["badge"], "FLAGGED_FRAUD_THREAT")

    def test_step_up_anti_coercion(self):
        # 1. High-risk transaction generates challenge
        challenge = self.step_up_engine.generate_challenge(
            risk_level="CRITICAL",
            scam_category="Digital Arrest / Institutional Coercion Scam",
            amount=48500,
            is_new_payee=True
        )
        self.assertTrue(challenge["requires_challenge"])
        self.assertEqual(challenge["challenge_type"], "ANTI_COERCION_CHECK")
        self.assertIsNotNone(challenge["math_question"])

        # 2. If user admits to fake police coercion -> block payment
        verify_block = self.step_up_engine.verify_challenge(
            challenge_type="ANTI_COERCION_CHECK",
            user_math_answer=challenge["expected_math_answer"],
            expected_math_answer=challenge["expected_math_answer"],
            acknowledged_checkbox=True,
            is_coerced_answer=True
        )
        self.assertFalse(verify_block["success"])
        self.assertEqual(verify_block["action"], "BLOCK_TRANSACTION")

    def test_end_to_end_pipeline_and_sub_100ms_latency(self):
        start = time.perf_counter()
        result = self.pipeline.evaluate_transaction(
            sender_vpa="gayatri@okaxis",
            recipient_vpa="cbi-investigation-cell@ybl",
            amount=48500,
            note="Urgent CBI investigation security deposit bond case 402",
            transaction_type="DIRECT_PAY",
            call_active=True
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Latency check: strict < 100ms
        self.assertLess(elapsed_ms, 100.0, f"Latency {elapsed_ms}ms exceeded 100ms budget!")
        
        # Risk score check
        self.assertEqual(result["risk_tier"], "CRITICAL")
        self.assertGreaterEqual(result["risk_score"], 80)
        self.assertEqual(result["action_code"], "INTERCEPT_AND_WARN")
        
        # Multi-lingual voice alert check
        voice_alerts = result["xai_explanation"]["voice_alerts"]
        self.assertIn("hi", voice_alerts)
        self.assertIn("en", voice_alerts)
        self.assertIn("mr", voice_alerts)
        self.assertIn("ta", voice_alerts)


if __name__ == "__main__":
    unittest.main()
