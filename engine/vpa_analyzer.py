"""ByteShield - Module 1: VPA & Domain Anomaly Analyzer
Performs string Levenshtein distance, homoglyph detection, typosquatting analysis,
and banking domain spoof classification on UPI Virtual Payment Addresses (VPAs).
"""

import re
from typing import Dict, Any, List, Tuple


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein edit distance between two strings."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # Deletion
                dp[i][j - 1] + 1,      # Insertion
                dp[i - 1][j - 1] + cost  # Substitution
            )
    return dp[m][n]


def normalized_similarity(s1: str, s2: str) -> float:
    """Compute normalized similarity ratio (0.0 to 1.0)."""
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return max(0.0, 1.0 - (dist / max_len))


# Official Verified Banking & Merchant VPA References in India
OFFICIAL_ENTITIES: Dict[str, Dict[str, Any]] = {
    "support.sbi@ybl": {"name": "State Bank of India (Official Support)", "type": "bank_official", "category": "banking"},
    "nodal.sbi@sbi": {"name": "SBI Nodal Desk", "type": "bank_official", "category": "banking"},
    "support@icici": {"name": "ICICI Bank Customer Desk", "type": "bank_official", "category": "banking"},
    "customercare@hdfcbank": {"name": "HDFC Bank Customer Support", "type": "bank_official", "category": "banking"},
    "support@axisbank": {"name": "Axis Bank Helpdesk", "type": "bank_official", "category": "banking"},
    "helpdesk@pnb": {"name": "Punjab National Bank Care", "type": "bank_official", "category": "banking"},
    "support@paytm": {"name": "Paytm Payments Bank Care", "type": "fintech_official", "category": "payments"},
    "care@phonepe": {"name": "PhonePe Support", "type": "fintech_official", "category": "payments"},
    "swiggy@icici": {"name": "Swiggy Food Ordering", "type": "merchant_official", "category": "food"},
    "zomato@hdfcbank": {"name": "Zomato Online", "type": "merchant_official", "category": "food"},
    "amazonpay@apl": {"name": "Amazon Pay India", "type": "merchant_official", "category": "ecommerce"},
    "flipkart@axis": {"name": "Flipkart Internet Pvt Ltd", "type": "merchant_official", "category": "ecommerce"},
    "tatapower@icici": {"name": "Tata Power Mumbai Utility", "type": "utility_official", "category": "utility"},
    "bsesdelhi@sbi": {"name": "BSES Rajdhani Delhi Electricity", "type": "utility_official", "category": "utility"},
    "irctc@sbi": {"name": "IRCTC Ticketing Official", "type": "gov_official", "category": "travel"},
    "mumbaipolice@sbi": {"name": "Mumbai Police Welfare Fund", "type": "gov_official", "category": "government"},
}

# Suspicious Brand Spoofing Keywords used by scammers in prefix
SUSPICIOUS_KEYWORD_PATTERNS = [
    r"sbi[-_.]?(support|help|desk|care|kyc|service|customercare)",
    r"hdfc[-_.]?(support|help|desk|care|kyc|service|customercare)",
    r"icici[-_.]?(support|help|desk|care|kyc|service|customercare)",
    r"axis[-_.]?(support|help|desk|care|kyc|service|customercare)",
    r"paytm[-_.]?(refund|cashback|help|support|care|kyc|bonus)",
    r"phonepe[-_.]?(refund|cashback|support|lottery|reward|claim)",
    r"gpay[-_.]?(reward|bonus|support|refund|lucky)",
    r"cbi[-_.]?(officer|case|investigation|cell|court|police)",
    r"police[-_.]?(cyber|arrest|warrant|fine|challan|bail)",
    r"electricity[-_.]?(bill|officer|power|disconnect|urgent)",
    r"airtel[-_.]?(support|care|5g|esim|kyc)",
    r"jio[-_.]?(support|care|5g|offer|kyc)",
    r"(refund|claim|lottery|reward|bonus|airdrop|crypto|task|earn)[-_.]?(desk|official|desk|pay)",
]

# Homoglyphs often used in lookalike VPAs
HOMOGLYPH_MAP = {
    '0': 'o', '1': 'l', '5': 's', '8': 'b', 'vv': 'w', 'rn': 'm'
}


class VPAAnalyzer:
    """Real-Time VPA Similarity & Spoofing Detection Engine."""

    def __init__(self):
        self.official_vpas = OFFICIAL_ENTITIES
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_KEYWORD_PATTERNS]

    def analyze_vpa(self, vpa: str) -> Dict[str, Any]:
        """
        Analyze a candidate UPI VPA for impersonation, typosquatting, and anomalous patterns.
        """
        vpa_clean = (vpa or "").strip().lower()
        if not vpa_clean or "@" not in vpa_clean:
            return {
                "vpa": vpa,
                "is_spoof": True,
                "risk_score": 90,
                "spoof_target": None,
                "similarity_score": 0.0,
                "detection_reasons": ["Invalid VPA format: Missing handle/provider structure."],
                "is_official": False
            }

        # Check if exactly matching an official verified entity
        if vpa_clean in self.official_vpas:
            entity = self.official_vpas[vpa_clean]
            return {
                "vpa": vpa,
                "is_spoof": False,
                "risk_score": 0,
                "spoof_target": None,
                "similarity_score": 1.0,
                "detection_reasons": [f"Verified Official VPA: {entity['name']}"],
                "is_official": True,
                "official_name": entity["name"]
            }

        prefix, handle = vpa_clean.split("@", 1)
        reasons: List[str] = []
        highest_similarity = 0.0
        target_entity_name = None
        target_vpa = None
        risk_score = 0

        # 1. Compare against official directory using Levenshtein distance
        for official_vpa, meta in self.official_vpas.items():
            off_prefix, off_handle = official_vpa.split("@", 1)
            
            full_sim = normalized_similarity(vpa_clean, official_vpa)
            prefix_sim = normalized_similarity(prefix, off_prefix)
            combined_sim = (prefix_sim * 0.7) + (full_sim * 0.3)

            if combined_sim > highest_similarity:
                highest_similarity = combined_sim
                target_entity_name = meta["name"]
                target_vpa = official_vpa

        if 0.70 <= highest_similarity < 1.0:
            risk_score += int(highest_similarity * 80)
            reasons.append(
                f"VPA Typosquatting: High resemblance ({int(highest_similarity * 100)}%) to official '{target_vpa}' ({target_entity_name})"
            )

        # 2. Check for suspicious brand impersonation keywords in the prefix
        for pattern in self.compiled_patterns:
            if pattern.search(prefix):
                risk_score += 65
                reasons.append(
                    f"Brand Impersonation Trigger: Prefix '{prefix}' mimics regulated authority/banking service desk."
                )
                break

        # 3. Check for hyphen/separator replacement spoofing
        if "-" in prefix and any(bank in prefix for bank in ["sbi", "hdfc", "icici", "axis", "pnb", "paytm", "cbi", "police"]):
            risk_score += 35
            reasons.append(
                "Deceptive Punctuation: Uses hyphenated bank/authority name on a generic third-party UPI handle."
            )

        # 4. Check for homoglyph / numerical substitutions
        normalized_prefix = prefix
        for k, v in HOMOGLYPH_MAP.items():
            if k in normalized_prefix:
                normalized_prefix = normalized_prefix.replace(k, v)
        
        if normalized_prefix != prefix:
            for official_vpa, meta in self.official_vpas.items():
                off_prefix = official_vpa.split("@")[0]
                if normalized_similarity(normalized_prefix, off_prefix) > 0.85:
                    risk_score += 50
                    reasons.append(
                        f"Homoglyph / Character Substitution: '{prefix}' substitutes characters to mimic '{off_prefix}'."
                    )
                    break

        risk_score = min(100, max(0, risk_score))
        is_spoof = risk_score >= 50

        return {
            "vpa": vpa,
            "is_spoof": is_spoof,
            "risk_score": risk_score,
            "spoof_target": target_vpa if is_spoof else None,
            "target_entity_name": target_entity_name if is_spoof else None,
            "similarity_score": round(highest_similarity, 3),
            "detection_reasons": reasons if reasons else ["Standard individual/merchant VPA format."],
            "is_official": False
        }


vpa_analyzer_instance = VPAAnalyzer()
