"""ByteShield - Master Fraud Detection & Interception Pipeline
Orchestrates all 7 detection engines with sub-100ms response latency,
fuses multi-model signals, and coordinates pre-PIN interception workflows.
"""

import time
from typing import Dict, Any, Optional

from .vpa_analyzer import vpa_analyzer_instance
from .social_engineering import social_engine_instance
from .mule_graph import mule_graph_instance
from .ml_engine import ml_engine_instance
from .xai_engine import xai_engine_instance
from .tokenizer import tokenizer_instance
from .step_up import step_up_instance


class ByteShieldPipeline:
    """Master Orchestrator for Real-Time UPI Pre-PIN Fraud Interception."""

    def __init__(self):
        self.vpa_engine = vpa_analyzer_instance
        self.social_engine = social_engine_instance
        self.mule_engine = mule_graph_instance
        self.ml_engine = ml_engine_instance
        self.xai_engine = xai_engine_instance
        self.tokenizer = tokenizer_instance
        self.step_up_engine = step_up_instance
        self.audit_log: list = []

    def evaluate_transaction(
        self,
        sender_vpa: str,
        recipient_vpa: str,
        amount: float,
        note: str = "",
        transaction_type: str = "DIRECT_PAY",
        sender_baseline_avg: float = 1200.0,
        hour_of_day: Optional[int] = None,
        is_new_device: bool = False,
        call_active: bool = False,
        screen_sharing: bool = False,
        geo_distance_km: float = 12.0
    ) -> Dict[str, Any]:
        """
        Evaluate full transaction risk and generate pre-PIN interception payload.
        Strict latency target: < 100ms.
        """
        start_time = time.perf_counter()

        # Step 1: VPA Levenshtein
        vpa_result = self.vpa_engine.analyze_vpa(recipient_vpa)

        # Step 2: Social Engineering NLP
        social_result = self.social_engine.evaluate_transaction(
            note=note,
            transaction_type=transaction_type,
            amount=amount,
            sender_baseline_avg=sender_baseline_avg,
            timestamp_hour=hour_of_day,
            recipient_is_new_contact=True,
            call_active_during_payment=call_active,
            screen_sharing_detected=screen_sharing
        )

        # Step 3: Graph Mule Ring
        graph_result = self.mule_engine.evaluate_graph_risk(
            sender_vpa=sender_vpa,
            receiver_vpa=recipient_vpa,
            amount=amount
        )

        # Step 4: Multi-Model Tabular ML
        ml_result = self.ml_engine.predict_risk(
            amount=amount,
            sender_baseline_avg=sender_baseline_avg,
            account_age_hours=graph_result.get("account_age_hours", 24),
            vpa_similarity_score=vpa_result.get("similarity_score", 0.0),
            social_risk_score=social_result.get("social_risk_score", 0),
            graph_risk_score=graph_result.get("graph_risk_score", 0),
            hour_of_day=hour_of_day if hour_of_day is not None else time.localtime().tm_hour,
            is_collect_request=(transaction_type == "COLLECT_REQUEST"),
            is_new_device=is_new_device,
            geo_distance_km=geo_distance_km
        )

        # Step 5: Multi-Signal Risk Aggregation
        vpa_score = vpa_result.get("risk_score", 0)
        social_score = social_result.get("social_risk_score", 0)
        graph_score = graph_result.get("graph_risk_score", 0)
        ml_score = ml_result.get("ml_risk_score", 0)

        if graph_result.get("is_blacklisted"):
            fused_score = 100
        elif vpa_result.get("is_official") and social_score < 20:
            fused_score = 5
        else:
            fused_score = int(
                (vpa_score * 0.30) +
                (social_score * 0.35) +
                (graph_score * 0.25) +
                (ml_score * 0.10)
            )
            max_single = max(vpa_score, social_score, graph_score)
            if max_single >= 85 and fused_score < 75:
                fused_score = int((fused_score * 0.4) + (max_single * 0.6))

        fused_score = min(100, max(0, fused_score))

        if fused_score >= 75:
            risk_tier = "CRITICAL"
            action_code = "INTERCEPT_AND_WARN"
        elif fused_score >= 50:
            risk_tier = "HIGH"
            action_code = "STEP_UP_CHALLENGE"
        elif fused_score >= 30:
            risk_tier = "MEDIUM"
            action_code = "ADVISORY_PROMPT"
        else:
            risk_tier = "LOW"
            action_code = "ALLOW_DIRECT_PIN"

        # Step 6: Tokenized UPI Masking
        token_info = self.tokenizer.generate_token_and_badge(
            vpa=recipient_vpa,
            risk_level=risk_tier,
            is_official=vpa_result.get("is_official", False)
        )

        # Step 7: Explainable AI
        xai_result = self.xai_engine.generate_explanation(
            vpa_result=vpa_result,
            social_result=social_result,
            graph_result=graph_result,
            ml_result=ml_result,
            amount=amount,
            final_risk_score=fused_score
        )

        # Step 8: Pre-PIN Step-Up Challenge
        step_up_challenge = self.step_up_engine.generate_challenge(
            risk_level=risk_tier,
            scam_category=social_result.get("scam_category", ""),
            amount=amount,
            is_new_payee=True
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        response_payload = {
            "risk_score": fused_score,
            "risk_tier": risk_tier,
            "action_code": action_code,
            "latency_ms": round(elapsed_ms, 2),
            "recipient_vpa": recipient_vpa,
            "tokenized_info": token_info,
            "xai_explanation": xai_result,
            "step_up_challenge": step_up_challenge,
            "engine_breakdowns": {
                "vpa_analyzer": vpa_result,
                "social_engineering": social_result,
                "mule_graph": graph_result,
                "ml_ensemble": ml_result
            },
            "timestamp": time.time()
        }

        self.audit_log.insert(0, {
            "id": f"TXN-{int(time.time()*1000)%1000000:06d}",
            "time": time.strftime("%H:%M:%S"),
            "sender": sender_vpa,
            "recipient_masked": token_info["masked_vpa"],
            "amount": amount,
            "note": note,
            "risk_score": fused_score,
            "risk_tier": risk_tier,
            "latency_ms": round(elapsed_ms, 2),
            "scam_category": social_result.get("scam_category", "None"),
            "badge": token_info["badge_label"]
        })
        if len(self.audit_log) > 100:
            self.audit_log.pop()

        return response_payload

    def get_audit_feed(self) -> list:
        return self.audit_log


master_pipeline = ByteShieldPipeline()
