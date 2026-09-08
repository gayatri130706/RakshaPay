"""ByteShield - Module 6: Tokenized UPI ID Display & Anti-Harvesting Masking Engine
Generates privacy-preserving tokens and screen masks for UPI VPAs to prevent
screen-scraping malware and screenshot harvesting by fraudsters.
"""

import hashlib
from typing import Dict, Any


class UPITokenizer:
    """Masks and tokenizes UPI identifiers for secure screen display and zero-leak logging."""

    @staticmethod
    def mask_vpa(vpa: str) -> str:
        """Mask a VPA for safe on-screen display."""
        vpa_clean = (vpa or "").strip()
        if "@" not in vpa_clean:
            return vpa_clean

        prefix, handle = vpa_clean.split("@", 1)
        length = len(prefix)

        if prefix.isdigit() and length == 10:
            masked_prefix = prefix[:2] + "****" + prefix[-4:]
        elif length <= 3:
            masked_prefix = prefix[0] + "**"
        elif length <= 6:
            masked_prefix = prefix[:2] + "***" + prefix[-1:]
        elif "-" in prefix:
            parts = prefix.split("-")
            masked_prefix = parts[0] + "-***-" + parts[-1]
        elif "." in prefix:
            parts = prefix.split(".")
            masked_prefix = parts[0] + ".***." + parts[-1]
        else:
            visible_chars = 3
            masked_prefix = prefix[:visible_chars] + "****" + prefix[-2:]

        return f"{masked_prefix}@{handle}"

    @staticmethod
    def generate_token_and_badge(vpa: str, risk_level: str, is_official: bool) -> Dict[str, Any]:
        """
        Generate opaque token ID, security badge, and masked representation.
        """
        vpa_clean = (vpa or "").strip().lower()
        sha256_hash = hashlib.sha256(vpa_clean.encode("utf-8")).hexdigest()
        token_id = f"TOK-UPI-{sha256_hash[:8].upper()}"

        masked = UPITokenizer.mask_vpa(vpa_clean)

        if is_official:
            badge = "VERIFIED_OFFICIAL_MERCHANT"
            badge_color = "#059669"
            badge_label = "🛡️ Verified Bank / Merchant"
        elif risk_level == "CRITICAL":
            badge = "FLAGGED_FRAUD_THREAT"
            badge_color = "#dc2626"
            badge_label = "🚨 High-Risk Impersonation Threat"
        elif risk_level == "HIGH":
            badge = "SUSPICIOUS_UNVERIFIED"
            badge_color = "#ea580c"
            badge_label = "⚠️ Suspicious Unverified Account"
        elif risk_level == "MEDIUM":
            badge = "NEW_UNVERIFIED_PAYEE"
            badge_color = "#d97706"
            badge_label = "ℹ️ New Payee / Unverified"
        else:
            badge = "STANDARD_INDIVIDUAL"
            badge_color = "#2563eb"
            badge_label = "👤 Individual Payee"

        return {
            "masked_vpa": masked,
            "token_id": token_id,
            "badge": badge,
            "badge_label": badge_label,
            "badge_color": badge_color,
            "secure_hash": sha256_hash
        }


tokenizer_instance = UPITokenizer()
