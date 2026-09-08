"""ByteShield - Module 5: Explainable AI (XAI) & SHAP-Style Reason Engine
Translates multi-model fraud predictions into human-interpretable feature attributions,
evidence bullet points, and multi-lingual voice alerts (Hindi, Marathi, Tamil, English).
"""

from typing import Dict, Any, List


class XAIEngine:
    """Generates human-explainable rationales and localized alerts for fraud interception."""

    def generate_explanation(
        self,
        vpa_result: Dict[str, Any],
        social_result: Dict[str, Any],
        graph_result: Dict[str, Any],
        ml_result: Dict[str, Any],
        amount: float,
        final_risk_score: int
    ) -> Dict[str, Any]:
        """
        Synthesize explainable attributions and multi-lingual alerts from all engine outputs.
        """
        attributions: List[Dict[str, Any]] = []
        key_reasons: List[str] = []

        total_risk = max(1, final_risk_score)
        
        vpa_contrib = vpa_result.get("risk_score", 0) * 0.30
        social_contrib = social_result.get("social_risk_score", 0) * 0.35
        graph_contrib = graph_result.get("graph_risk_score", 0) * 0.25
        ml_contrib = ml_result.get("ml_risk_score", 0) * 0.10

        raw_sum = vpa_contrib + social_contrib + graph_contrib + ml_contrib
        scale = (final_risk_score / max(1.0, raw_sum)) if raw_sum > 0 else 1.0

        if vpa_contrib > 0:
            attributions.append({
                "factor": "VPA Anomaly & Spoofing",
                "weight_percent": round((vpa_contrib * scale / total_risk) * 100, 1),
                "impact": "HIGH" if vpa_contrib > 20 else "MEDIUM",
                "description": "Similarity to protected banking/merchant handles (Levenshtein typosquatting)"
            })
            key_reasons.extend(vpa_result.get("detection_reasons", []))

        if social_contrib > 0:
            attributions.append({
                "factor": "Social Engineering Heuristics",
                "weight_percent": round((social_contrib * scale / total_risk) * 100, 1),
                "impact": "CRITICAL" if social_contrib > 25 else "HIGH",
                "description": "Scam keywords, coercion markers, or reverse collect request patterns"
            })
            key_reasons.extend(social_result.get("detected_triggers", []))

        if graph_contrib > 0:
            attributions.append({
                "factor": "Mule Graph & Zero-Day Risk",
                "weight_percent": round((graph_contrib * scale / total_risk) * 100, 1),
                "impact": "CRITICAL" if graph_result.get("is_blacklisted") else "HIGH",
                "description": "Network topology, rapid fan-out money laundering, or newly created account"
            })
            key_reasons.extend(graph_result.get("graph_reasons", []))

        if ml_contrib > 0:
            attributions.append({
                "factor": "Behavioral Anomaly & Velocity",
                "weight_percent": round((ml_contrib * scale / total_risk) * 100, 1),
                "impact": "MEDIUM",
                "description": "Deviation from typical transaction baseline, time-of-day, or geo-jump"
            })

        cleaned_reasons = []
        seen = set()
        for r in key_reasons:
            if r not in seen and not r.startswith("Standard individual"):
                seen.add(r)
                cleaned_reasons.append(r)

        if not cleaned_reasons:
            cleaned_reasons = ["Transaction parameters align with verified recipient baseline."]

        voice_alerts = self._generate_regional_voice_scripts(final_risk_score, social_result, vpa_result)

        if final_risk_score >= 75:
            action_recommendation = (
                "🚨 HIGH RISK INTERCEPTION: We strongly recommend CANCELING this payment. "
                "Legitimate police, CBI, or bank officials will NEVER ask you to make a UPI transfer."
            )
        elif final_risk_score >= 40:
            action_recommendation = (
                "⚠️ CAUTION REQUIRED: This transaction has suspicious attributes. "
                "Verify recipient identity before entering your secret UPI PIN."
            )
        else:
            action_recommendation = "✅ Safe to proceed with UPI PIN."

        return {
            "attributions": attributions,
            "key_evidence_reasons": cleaned_reasons,
            "action_recommendation": action_recommendation,
            "voice_alerts": voice_alerts,
            "scam_category": social_result.get("scam_category", "None")
        }

    def _generate_regional_voice_scripts(
        self,
        risk_score: int,
        social_result: Dict[str, Any],
        vpa_result: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate voice alert text for regional audio warning in Hindi, Marathi, Tamil, English."""
        if risk_score < 40:
            return {
                "en": "Transaction verified. You may proceed safely.",
                "hi": "लेन-देन सुरक्षित है। आप आगे बढ़ सकते हैं।",
                "mr": "व्यवहार सुरक्षित आहे. आपण पुढे जाऊ शकता.",
                "ta": "பரிவர்த்தனை சரிபார்க்கப்பட்டது. தொடரலாம்."
            }

        scam_cat = social_result.get("scam_category", "")

        if "Digital Arrest" in scam_cat or "Coercion" in scam_cat:
            return {
                "en": "Warning! Potential Digital Arrest scam detected. Police or CBI never demand money on video calls. Do not enter your UPI PIN!",
                "hi": "सावधान! डिजिटल अरेस्ट फ्रॉड का खतरा। पुलिस या सीबीआई कभी भी वीडियो कॉल पर पैसे नहीं मांगते। अपना यूपीआई पिन दर्ज न करें!",
                "mr": "सावधान! डिजिटल अरेस्ट घोटाळ्याचा धोका. पोलीस किंवा सीबीआय कधीही यूपीआय द्वारे पैसे मागत नाहीत. पिन टाकू नका!",
                "ta": "எச்சரிக்கை! இது ஒரு போலி காவல் அல்லது சிபிஐ மோசடி. உங்கள் யுபிஐ பின்னை உள்ளிட வேண்டாம்!"
            }
        elif "Reverse Collect" in scam_cat or "QR" in scam_cat:
            return {
                "en": "Stop! You are sending money, not receiving it. You never need to enter your PIN to receive money!",
                "hi": "रुकिए! आप पैसे भेज रहे हैं, पा नहीं रहे। पैसे प्राप्त करने के लिए कभी यूपीआई पिन की आवश्यकता नहीं होती!",
                "mr": "थांबा! आपण पैसे पाठवत आहात. पैसे मिळवण्यासाठी कधीही यूपीआई पिन टाकण्याची गरज नसते!",
                "ta": "நில்லுங்கள்! பணம் பெற யுபிஐ பின் தேவையில்லை. இது ஒரு மோசடி!"
            }
        elif vpa_result.get("is_spoof"):
            target = vpa_result.get("target_entity_name", "official bank")
            return {
                "en": f"Warning! Fake UPI ID detected. This account is pretending to be {target}. Do not pay!",
                "hi": f"चेतावनी! नकली यूपीआई आईडी पाई गई है। यह खाता {target} होने का झूठा दावा कर रहा है। भुगतान न करें!",
                "mr": f"सावधान! बनावट यूपीआय आयडी आढळला. हे {target} ची बतावणी करत आहे. पैसे पाठवू नका!",
                "ta": f"எச்சரிக்கை! இந்த யுபிஐ ஐடி போலியானது. பணத்தை செலுத்த வேண்டாம்!"
            }
        else:
            return {
                "en": "High risk transaction detected! Recipient account is unverified or newly created. Please cancel.",
                "hi": "उच्च जोखिम वाला लेन-देन! प्राप्तकर्ता का खाता संदिग्ध या नया है। कृपया भुगतान रद्द करें।",
                "mr": "धोकादायक व्यवहार! प्राप्तकर्त्याचे खाते संशयास्पद किंवा नवीन आहे. कृपया व्यवहार रद्द करा.",
                "ta": "அதிக ஆபத்துள்ள பரிவர்த்தனை! தயவுசெய்து பணம் செலுத்துவதை ரத்து செய்யவும்."
            }


xai_engine_instance = XAIEngine()
