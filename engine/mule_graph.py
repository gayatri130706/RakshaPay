"""
ByteShield — Mule Account & Fraud Ring Graph Engine
Tracks inter-account transaction graphs using NetworkX.
Detects:
1. Fast dispersal (Fan-out topology from scammer hub to multiple mule accounts).
2. Mule ring consolidation into cash-out / crypto exchange nodes.
3. Shared hardware device IDs across multiple seemingly unrelated VPAs.
4. Zero-Day fresh accounts (<24h age) receiving high-velocity funds.
"""

import time
import networkx as nx
from typing import Dict, List, Any, Optional, Set


class MuleGraphEngine:
    def __init__(self):
        # Directed graph: edges point from sender -> receiver
        self.graph = nx.DiGraph()
        # In-memory account metadata cache: vpa -> metadata dict
        self.account_metadata: Dict[str, Dict[str, Any]] = {}
        # Device-to-VPA map: device_id -> set of VPAs
        self.device_map: Dict[str, Set[str]] = {}
        # Global blacklist cache
        self.blacklist_vpas: Set[str] = set()

        self._init_seed_topology()

    def _init_seed_topology(self):
        """Seed the graph with realistic Indian UPI fraud ring topologies."""
        # 1. Gayatri (Verified User)
        self.add_or_update_account(
            "gayatri@okaxis",
            name="Gayatri (Sender/User)",
            account_age_hours=8760.0,
            is_verified=True,
            kyc_tier="FULL_KYC",
            risk_baseline=5,
            device_id="DEV-USER-GAYATRI"
        )

        # 2. Known Scammer Hub: "Digital Arrest" Ring
        self.add_or_update_account(
            "cbi-investigation-cell@ybl",
            name="CBI Impersonation Hub",
            account_age_hours=4.5,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=95,
            device_id="DEV-JAM-4091"
        )
        self.add_or_update_account(
            "mule_layer1_arun@paytm",
            name="Mule L1 Arun K.",
            account_age_hours=18.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=75,
            device_id="DEV-JAM-4091"
        )
        self.add_or_update_account(
            "mule_layer1_vikas@okicici",
            name="Mule L1 Vikas S.",
            account_age_hours=12.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=70,
            device_id="DEV-JAM-9982"
        )
        self.add_or_update_account(
            "mule_layer2_subhash@ybl",
            name="Consolidation Mule Subhash",
            account_age_hours=48.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=80,
            device_id="DEV-JAM-9982"
        )
        self.add_or_update_account(
            "cashout_p2p_crypto@axl",
            name="P2P Crypto Cashout Node",
            account_age_hours=720.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=98,
            device_id="DEV-CASHOUT-99"
        )

        # Connect the scam ring edges
        self.record_transaction("cbi-investigation-cell@ybl", "mule_layer1_arun@paytm", 45000, "Rapid Dispersal Layer 1", risk_score=95, risk_tier="CRITICAL", scam_category="Digital Arrest Video Call Threat")
        self.record_transaction("cbi-investigation-cell@ybl", "mule_layer1_vikas@okicici", 48000, "Rapid Dispersal Layer 1", risk_score=95, risk_tier="CRITICAL", scam_category="Digital Arrest Video Call Threat")
        self.record_transaction("mule_layer1_arun@paytm", "mule_layer2_subhash@ybl", 42000, "Mule Consolidation", risk_score=80, risk_tier="HIGH", scam_category="Mule Dispersal Network")
        self.record_transaction("mule_layer1_vikas@okicici", "mule_layer2_subhash@ybl", 46000, "Mule Consolidation", risk_score=80, risk_tier="HIGH", scam_category="Mule Dispersal Network")
        self.record_transaction("mule_layer2_subhash@ybl", "cashout_p2p_crypto@axl", 85000, "Crypto Off-ramp Cashout", risk_score=98, risk_tier="CRITICAL", scam_category="Offshore Crypto Cashout")

        # 3. Fake SBI Customer Care Spoof Ring
        self.add_or_update_account(
            "sbi-customercare-support@ybl",
            name="Fake SBI Support Desk",
            account_age_hours=3.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=90,
            device_id="DEV-NUH-5542"
        )
        self.add_or_update_account(
            "sbi-helpdesk-agent@okaxis",
            name="Fake SBI Helpdesk Agent",
            account_age_hours=5.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=88,
            device_id="DEV-NUH-5542"
        )
        self.add_or_update_account(
            "refund-collector-99@paytm",
            name="Mule Pool Collector",
            account_age_hours=10.0,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=86,
            device_id="DEV-MULE-303"
        )
        self.record_transaction("sbi-customercare-support@ybl", "refund-collector-99@paytm", 24999, "Victim Fund Exfiltration", risk_score=90, risk_tier="CRITICAL", scam_category="Fake Customer Care AnyDesk")
        self.record_transaction("sbi-helpdesk-agent@okaxis", "refund-collector-99@paytm", 32000, "Victim Fund Exfiltration", risk_score=88, risk_tier="CRITICAL", scam_category="Fake Customer Care AnyDesk")

        # 4. Zero-Day Task Scam Account
        self.add_or_update_account(
            "earn-daily-bonus99@okicici",
            name="Telegram VIP Task Pool",
            account_age_hours=1.2,
            is_verified=False,
            kyc_tier="MINIMAL",
            risk_baseline=92,
            device_id="DEV-TASK-883"
        )

        # 5. Legitimate transfers
        self.record_transaction("gayatri@okaxis", "swiggy@icici", 450, "Food Delivery", risk_score=5, risk_tier="LOW", scam_category="Verified Merchant")
        self.record_transaction("gayatri@okaxis", "tatapower@icici", 1850, "Electricity Bill", risk_score=8, risk_tier="LOW", scam_category="Utility Bill Payment")
        self.record_transaction("gayatri@okaxis", "rohit_friend@okhdfcbank", 500, "Split lunch", risk_score=12, risk_tier="LOW", scam_category="P2P Friend Transfer")

        # Blacklisted known bad VPAs
        self.blacklist_vpas.add("cbi-investigation-cell@ybl")
        self.blacklist_vpas.add("cashout_p2p_crypto@axl")
        self.blacklist_vpas.add("sbi-customercare-support@ybl")

    def add_or_update_account(
        self,
        vpa: str,
        name: str,
        account_age_hours: float,
        is_verified: bool = False,
        kyc_tier: str = "MINIMAL",
        risk_baseline: int = 0,
        device_id: Optional[str] = None
    ):
        """Register or update an account node in the graph."""
        vpa_clean = vpa.strip().lower()
        dev = device_id or f"DEV-NODE-{abs(hash(vpa_clean)) % 9000 + 1000}"
        self.account_metadata[vpa_clean] = {
            "vpa": vpa_clean,
            "name": name,
            "account_age_hours": float(account_age_hours),
            "is_verified": is_verified,
            "kyc_tier": kyc_tier,
            "risk_baseline": risk_baseline,
            "device_id": dev,
            "created_at": time.time() - (account_age_hours * 3600)
        }
        
        if not self.graph.has_node(vpa_clean):
            self.graph.add_node(
                vpa_clean,
                name=name,
                account_age_hours=float(account_age_hours),
                is_verified=is_verified,
                risk=risk_baseline,
                device_id=dev
            )
        else:
            self.graph.nodes[vpa_clean]["account_age_hours"] = float(account_age_hours)
            self.graph.nodes[vpa_clean]["risk"] = risk_baseline
            self.graph.nodes[vpa_clean]["device_id"] = dev

        if dev not in self.device_map:
            self.device_map[dev] = set()
        self.device_map[dev].add(vpa_clean)

    def record_transaction(
        self,
        sender_vpa: str,
        receiver_vpa: str,
        amount: float,
        remark: str = "",
        risk_score: Optional[int] = None,
        risk_tier: Optional[str] = None,
        scam_category: Optional[str] = None,
        action_code: Optional[str] = None,
        device_id: Optional[str] = None
    ):
        """Add or update an edge and store rich node telemetry for live inspection."""
        s, r = sender_vpa.strip().lower(), receiver_vpa.strip().lower()

        # 1. Sender node
        if not self.graph.has_node(s):
            self.add_or_update_account(
                s,
                name="Gayatri (Sender/User)" if "gayatri" in s else f"User ({s.split('@')[0]})",
                account_age_hours=8760.0,
                is_verified=True,
                device_id="DEV-USER-GAYATRI"
            )

        # 2. Receiver node determination
        is_risky = (risk_score is not None and risk_score >= 50) or (
            "cbi" in r or "refund" in r or "police" in r or "bonus" in r or r in self.blacklist_vpas
        )
        default_age = 1.5 if is_risky else 720.0
        assigned_device = device_id or (
            f"DEV-MULE-{abs(hash(r)) % 9000 + 1000}" if is_risky else f"DEV-PEER-{abs(hash(r)) % 9000 + 1000}"
        )

        existing_name = self.account_metadata.get(r, {}).get("name")
        if existing_name and existing_name != r:
            assigned_name = existing_name
        elif is_risky:
            assigned_name = f"Flagged Node ({scam_category or 'High-Risk Payee'})"
        else:
            assigned_name = f"Payee ({r.split('@')[0]})"

        if not self.graph.has_node(r):
            self.add_or_update_account(
                r,
                name=assigned_name,
                account_age_hours=default_age,
                is_verified=not is_risky,
                risk_baseline=risk_score if risk_score is not None else (85 if is_risky else 15),
                device_id=assigned_device
            )
        else:
            # Update existing metadata with latest telemetry
            meta = self.account_metadata.get(r, {})
            if risk_score is not None:
                meta["risk_baseline"] = max(meta.get("risk_baseline", 0), risk_score)
            if assigned_device:
                meta["device_id"] = assigned_device
            if scam_category:
                meta["scam_category"] = scam_category

        # 3. Store rich live inspection telemetry on receiver
        if r in self.account_metadata:
            self.account_metadata[r]["last_amount"] = amount
            self.account_metadata[r]["last_remark"] = remark or "UPI Transaction"
            if risk_score is not None:
                self.account_metadata[r]["last_risk_score"] = risk_score
            if risk_tier:
                self.account_metadata[r]["last_risk_tier"] = risk_tier
            if scam_category:
                self.account_metadata[r]["last_scam_category"] = scam_category
            if action_code:
                self.account_metadata[r]["last_action_code"] = action_code

        # 4. Edge record
        if self.graph.has_edge(s, r):
            self.graph[s][r]["amount"] += amount
            self.graph[s][r]["count"] += 1
            self.graph[s][r]["last_timestamp"] = time.time()
            if remark:
                self.graph[s][r]["remark"] = remark
        else:
            self.graph.add_edge(
                s, r,
                amount=amount,
                count=1,
                remark=remark,
                last_timestamp=time.time()
            )

    def evaluate_graph_risk(self, sender_vpa: str, receiver_vpa: str, amount: float) -> Dict[str, Any]:
        """Analyze network topology, mule ring proximity, shared devices, and Zero-Day account indicators."""
        s = sender_vpa.strip().lower()
        r = receiver_vpa.strip().lower()
        reasons: List[str] = []
        graph_risk = 0
        is_zero_day = False
        is_mule_ring_member = False
        is_blacklisted = r in self.blacklist_vpas

        # 1. Blacklist check
        if is_blacklisted:
            graph_risk = 100
            reasons.append("🚨 Threat Intelligence Blacklist: Recipient UPI ID is actively blacklisted in National Cyber Crime Registry.")

        # 2. Account Age / Zero-Day Assessment
        meta = self.account_metadata.get(r)
        if meta:
            age_hours = meta.get("account_age_hours", 24)
            if age_hours < 6.0:
                is_zero_day = True
                graph_risk = max(graph_risk, 85)
                reasons.append(f"Zero-Day Scam Account: Recipient VPA was created only {age_hours:.1f} hours ago with no prior legitimate history.")
            elif age_hours < 24.0:
                is_zero_day = True
                graph_risk = max(graph_risk, 60)
                reasons.append(f"Fresh Account Risk: Recipient VPA is less than {int(age_hours)} hours old.")
        else:
            is_zero_day = True
            graph_risk = max(graph_risk, 45)
            reasons.append("Unseen New VPA: Recipient has no prior transaction history in national graph database.")

        # 3. Fan-out / Mule Dispersal Topology Detection
        if self.graph.has_node(r):
            out_degree = self.graph.out_degree(r)
            out_edges = list(self.graph.out_edges(r, data=True))
            
            if out_degree >= 2:
                total_out = sum(data.get("amount", 0) for _, _, data in out_edges)
                is_mule_ring_member = True
                graph_risk = max(graph_risk, 90)
                reasons.append(f"Graph Mule Detection: Recipient exhibits fan-out dispersal topology (splitting ₹{total_out:,.0f} across {out_degree} downstream mule accounts).")

            for _, target_node in self.graph.out_edges(r):
                if target_node in self.blacklist_vpas or "cashout" in target_node or "crypto" in target_node:
                    is_mule_ring_member = True
                    graph_risk = max(graph_risk, 92)
                    reasons.append(f"Money Laundering Chain: Recipient routes directly to high-risk cashout node '{target_node}'.")
                    break

        # 4. Shared Device Fingerprint Ring Check
        r_device = meta.get("device_id") if meta else None
        if r_device and r_device in self.device_map:
            co_devices = self.device_map[r_device]
            if len(co_devices) > 1:
                other_vpas = [v for v in co_devices if v != r]
                graph_risk = max(graph_risk, 88)
                is_mule_ring_member = True
                reasons.append(f"Shared Device Mule Ring: Device '{r_device}' operates {len(co_devices)} distinct UPI IDs ({', '.join(other_vpas[:2])}).")

        # 5. Graph Proximity to Known Fraud Hubs
        if not is_blacklisted:
            for bad_seed in self.blacklist_vpas:
                if self.graph.has_node(bad_seed) and self.graph.has_node(r):
                    try:
                        dist = nx.shortest_path_length(self.graph, source=bad_seed, target=r)
                        if dist == 1:
                            graph_risk = max(graph_risk, 85)
                            reasons.append(f"Direct Hop from Known Fraud Hub: 1-hop distance from blacklisted node '{bad_seed}'.")
                        elif dist == 2:
                            graph_risk = max(graph_risk, 65)
                            reasons.append(f"2-Hop Network Proximity to Scam Ring: Connected via intermediary mule to '{bad_seed}'.")
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        pass

        if not reasons:
            reasons.append("Peer-to-Peer Graph Node: No anomalous fan-out, shared hardware devices, or mule cluster proximity identified.")

        return {
            "graph_risk_score": graph_risk,
            "is_zero_day": is_zero_day,
            "is_mule_ring_member": is_mule_ring_member,
            "is_blacklisted": is_blacklisted,
            "reasons": reasons,
            "in_degree": self.graph.in_degree(r) if self.graph.has_node(r) else 0,
            "out_degree": self.graph.out_degree(r) if self.graph.has_node(r) else 0,
            "device_id": r_device or "N/A"
        }

    def get_full_graph_visualization_data(self) -> Dict[str, Any]:
        """Serialize the complete directed graph with rich metadata for Canvas visualization and live node inspection."""
        nodes = []
        links = []

        for node_id in self.graph.nodes():
            meta = self.account_metadata.get(node_id, {})
            in_deg = self.graph.in_degree(node_id)
            out_deg = self.graph.out_degree(node_id)
            is_blacklisted = node_id in self.blacklist_vpas
            node_risk = meta.get("last_risk_score", meta.get("risk_baseline", 0))

            if is_blacklisted or "cbi" in node_id or "sbi-customercare" in node_id or "police" in node_id or node_risk >= 75:
                category = "scammer_hub"
                color = "#dc2626"
                size = 20
            elif "cashout" in node_id or "crypto" in node_id:
                category = "cashout_node"
                color = "#7c3aed"
                size = 20
            elif "mule" in node_id or "collector" in node_id or (node_risk >= 50 and out_deg >= 1):
                category = "mule_account"
                color = "#ea580c"
                size = 16
            elif "swiggy" in node_id or "tatapower" in node_id or meta.get("is_verified", False):
                category = "verified_merchant"
                color = "#059669"
                size = 16
            else:
                category = "user"
                color = "#2563eb"
                size = 14

            raw_age = meta.get("account_age_hours")
            age_float = float(raw_age) if raw_age is not None else 24.0

            nodes.append({
                "id": node_id,
                "label": meta.get("name", node_id),
                "category": category,
                "color": color,
                "size": size,
                "account_age_hours": age_float,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "device_id": str(meta.get("device_id") or "DEV-SHARED-409"),
                "is_blacklisted": bool(is_blacklisted),
                "risk_score": int(node_risk),
                "risk_tier": meta.get("last_risk_tier", "CRITICAL" if node_risk >= 75 else ("HIGH" if node_risk >= 50 else ("MEDIUM" if node_risk >= 30 else "LOW"))),
                "scam_category": meta.get("last_scam_category", meta.get("scam_category", "Identified Scam Network" if node_risk >= 50 else "Legitimate Peer")),
                "last_amount": meta.get("last_amount", 0.0),
                "last_remark": meta.get("last_remark", ""),
                "action_code": meta.get("last_action_code", "INTERCEPT_AND_WARN" if node_risk >= 50 else "ALLOW"),
                "ring_id": 409 if (category in ("scammer_hub", "mule_account", "cashout_node") or node_risk >= 50) else None
            })

        for u, v, data in self.graph.edges(data=True):
            links.append({
                "source": u,
                "target": v,
                "amount": data.get("amount", 0),
                "count": data.get("count", 1),
                "remark": data.get("remark", "")
            })

        return {
            "nodes": nodes,
            "links": links,
            "total_nodes": len(nodes),
            "total_edges": len(links),
            "blacklisted_count": len(self.blacklist_vpas)
        }

    def blacklist_vpa(self, vpa: str, reason: str = "User Reported / Cyber Crime Feed"):
        """Add a VPA to real-time blacklist."""
        vpa_clean = vpa.strip().lower()
        self.blacklist_vpas.add(vpa_clean)
        if vpa_clean in self.account_metadata:
            self.account_metadata[vpa_clean]["risk_baseline"] = 100
        if self.graph.has_node(vpa_clean):
            self.graph.nodes[vpa_clean]["risk"] = 100


mule_graph_instance = MuleGraphEngine()
