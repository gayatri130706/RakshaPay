/**
 * RakshaPay — Interactive Mule Network & Fraud Ring Graph Visualizer
 * Canvas-based force-directed physics, particle flow animation,
 * node inspector, and live graph refresh as transactions are analyzed.
 *
 * ANIMATION PRESERVED: moving dots, force physics, glow halos — unchanged.
 * NEW: periodic graph refresh so new transactions appear as real nodes.
 */

class MuleGraphVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext("2d");
        this.nodes = [];
        this.links = [];
        if (this.selectedNode) {
            this.selectedNode = this.nodes.find(n => n.id === this.selectedNode.id) || null;
            if (this.selectedNode) this.updateInspector(this.selectedNode);
        }
        if (this.hoveredNode) {
            this.hoveredNode = this.nodes.find(n => n.id === this.hoveredNode.id) || null;
        }

        this.particles = [];
        this.selectedNode = null;
        this.hoveredNode = null;
        this.draggedNode = null;
        this.currentFilter = "all";

        // Canvas transform
        this.scale = 1;
        this.panX = 0;
        this.panY = 0;
        this.isPanning = false;
        this.startX = 0;
        this.startY = 0;

        // Live refresh: poll for new nodes every 15s
        this._lastNodeCount = 0;
        this._refreshInterval = null;

        this.initCanvasSize();
        this.bindEvents();
        this.fetchGraphData();
        this.animate();
        this._startLiveRefresh();
    }

    initCanvasSize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        this.canvas.width = rect.width || 900;
        this.canvas.height = 540;
    }

    /** Fetch graph data; if node count changed, re-layout new nodes at edges */
    async fetchGraphData() {
        try {
            const token = localStorage.getItem("rp_token") || "";
            const res = await fetch("/api/network-graph", {
                headers: {
                    "Authorization": "Bearer " + token
                }
            });
            if (!res.ok) {
                console.warn("network-graph returned status:", res.status);
                return;
            }
            const data = await res.json();
            if (data && data.nodes && data.links) {
                this.setupGraph(data.nodes, data.links);
            }
        } catch (e) {
            console.error("Failed to load graph data:", e);
        }
    }

    /** Poll for new nodes silently in background */
    _startLiveRefresh() {
        this._refreshInterval = setInterval(() => {
            this.fetchGraphData();
        }, 15000);
    }

    setupGraph(rawNodes, rawLinks) {
        const cx = this.canvas.width / 2;
        const cy = this.canvas.height / 2;

        // Build position map for existing nodes so they don't jump on refresh
        const existingPos = new Map(this.nodes.map(n => [n.id, { x: n.x, y: n.y, vx: n.vx, vy: n.vy }]));

        this.nodes = rawNodes.map((n, idx) => {
            const existing = existingPos.get(n.id);
            if (existing) {
                return { ...n, ...existing, radius: n.size || 14 };
            }
            // New node: place at edge of canvas so it "arrives" into view
            const angle = (idx / rawNodes.length) * Math.PI * 2;
            const dist = 140 + (idx % 3) * 60;
            return {
                ...n,
                x: cx + Math.cos(angle) * dist + (Math.random() - 0.5) * 40,
                y: cy + Math.sin(angle) * dist + (Math.random() - 0.5) * 40,
                vx: 0,
                vy: 0,
                radius: n.size || 14
            };
        });

        const nodeMap = new Map(this.nodes.map(n => [n.id, n]));

        this.links = rawLinks.map(l => ({
            ...l,
            sourceNode: nodeMap.get(l.source),
            targetNode: nodeMap.get(l.target)
        })).filter(l => l.sourceNode && l.targetNode);

        // Spawn animated particles along edges for visual fund flow — PRESERVED
        if (this.selectedNode) {
            this.selectedNode = this.nodes.find(n => n.id === this.selectedNode.id) || null;
            if (this.selectedNode) this.updateInspector(this.selectedNode);
        }
        if (this.hoveredNode) {
            this.hoveredNode = this.nodes.find(n => n.id === this.hoveredNode.id) || null;
        }

        this.particles = [];
        const numParticles = Math.min(30, this.links.length * 2 + 10);
        for (let i = 0; i < numParticles; i++) {
            const randomLink = this.links[Math.floor(Math.random() * this.links.length)];
            if (randomLink) {
                this.particles.push({
                    link: randomLink,
                    progress: Math.random(),
                    speed: 0.006 + Math.random() * 0.008
                });
            }
        }
    }

    bindEvents() {
        window.addEventListener("resize", () => this.initCanvasSize());

        this.canvas.addEventListener("mousedown", (e) => this.onMouseDown(e));
        this.canvas.addEventListener("mousemove", (e) => this.onMouseMove(e));
        this.canvas.addEventListener("mouseup", () => this.onMouseUp());
        this.canvas.addEventListener("wheel", (e) => this.onWheel(e), { passive: false });

        // Filter buttons
        document.querySelectorAll(".filter-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.currentFilter = btn.dataset.filter;
            });
        });
    }

    getCanvasPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left - this.panX) / this.scale,
            y: (e.clientY - rect.top - this.panY) / this.scale
        };
    }

    findNodeAt(pos) {
        for (let i = this.nodes.length - 1; i >= 0; i--) {
            const n = this.nodes[i];
            if (!this.isNodeVisible(n)) continue;
            const dx = pos.x - n.x;
            const dy = pos.y - n.y;
            if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) {
                return n;
            }
        }
        return null;
    }

    isNodeVisible(node) {
        if (this.currentFilter === "all") return true;
        if (this.currentFilter === "fraud") return node.category === "scammer_hub" || node.category === "cashout_node";
        if (this.currentFilter === "mule") return node.category === "mule_account" || node.category === "scammer_hub";
        if (this.currentFilter === "device") return node.device_id && node.device_id !== "N/A" && node.device_id !== "UNKNOWN";
        return true;
    }

    onMouseDown(e) {
        const pos = this.getCanvasPos(e);
        const clickedNode = this.findNodeAt(pos);
        if (clickedNode) {
            this.draggedNode = clickedNode;
            this.selectedNode = clickedNode;
            this.updateInspector(clickedNode);
        } else {
            this.isPanning = true;
            this.startX = e.clientX - this.panX;
            this.startY = e.clientY - this.panY;
        }
    }

    onMouseMove(e) {
        const pos = this.getCanvasPos(e);
        if (this.draggedNode) {
            this.draggedNode.x = pos.x;
            this.draggedNode.y = pos.y;
            this.draggedNode.vx = 0;
            this.draggedNode.vy = 0;
        } else if (this.isPanning) {
            this.panX = e.clientX - this.startX;
            this.panY = e.clientY - this.startY;
        } else {
            this.hoveredNode = this.findNodeAt(pos);
            this.canvas.style.cursor = this.hoveredNode ? "pointer" : "grab";
        }
    }

    onMouseUp() {
        this.draggedNode = null;
        this.isPanning = false;
    }

    onWheel(e) {
        e.preventDefault();
        const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
        this.scale = Math.min(2.5, Math.max(0.4, this.scale * zoomFactor));
    }

    escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    updateInspector(node) {
        const container = document.getElementById("inspector-content");
        if (!container || !node) return;

        const age = (node.account_age_hours !== undefined && node.account_age_hours !== null)
            ? Number(node.account_age_hours).toFixed(1)
            : "24.0";

        const devId = String(node.device_id || "DEV-UNKNOWN");
        const isMuleDevice = devId.includes("MULE") || devId.includes("JAM") || devId.includes("NUH") || devId.includes("CASHOUT") || devId.includes("SIM");

        const riskScore = node.risk_score !== undefined ? Number(node.risk_score) : (node.category === "scammer_hub" ? 95 : 15);
        const riskTier = node.risk_tier || (riskScore >= 75 ? "CRITICAL" : (riskScore >= 50 ? "HIGH" : (riskScore >= 30 ? "MEDIUM" : "LOW")));
        const tierClass = riskTier.toLowerCase();

        let riskTag = `<span class="tier-badge ${tierClass}">${riskTier} (${riskScore}/100)</span>`;
        if (node.is_blacklisted) {
            riskTag = `<span class="tier-badge critical">🚨 BLACKLISTED FRAUD HUB (${riskScore}/100)</span>`;
        } else if (node.category === "scammer_hub") {
            riskTag = `<span class="tier-badge critical">FLAGGED FRAUD HUB (${riskScore}/100)</span>`;
        } else if (node.category === "mule_account") {
            riskTag = `<span class="tier-badge high">MULE DISPERSAL NODE (${riskScore}/100)</span>`;
        } else if (node.category === "cashout_node") {
            riskTag = `<span class="tier-badge critical">OFFSHORE CASHOUT (${riskScore}/100)</span>`;
        }

        const ringBadge = (node.ring_id || riskScore >= 50)
            ? `<div class="insp-row"><span class="insp-label">Fraud Ring ID:</span><span class="insp-val mono" style="color:#c62828;font-weight:700;">RING-${node.ring_id || 409} (Fan-out Dispersal Ring)</span></div>`
            : "";

        const scamRow = (node.scam_category && node.scam_category !== "None")
            ? `<div class="insp-row"><span class="insp-label">Scam Vector:</span><span class="insp-val" style="color:#c62828;font-weight:600;">${this.escapeHtml(node.scam_category)}</span></div>`
            : "";

        const lastAmountRow = node.last_amount
            ? `<div class="insp-row"><span class="insp-label">Last Evaluated Txn:</span><span class="insp-val mono" style="font-weight:700;">₹${Number(node.last_amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</span></div>`
            : "";

        const actionRow = node.action_code
            ? `<div class="insp-row"><span class="insp-label">System Verdict:</span><span class="insp-val" style="color:${riskScore >= 50 ? '#c62828' : '#2e7d32'};font-weight:700;">${this.escapeHtml(node.action_code.replace(/_/g, ' '))}</span></div>`
            : "";

        container.innerHTML = `
            <div class="inspector-details" style="animation: fadeIn 0.2s ease;">
                <div class="insp-row">
                    <span class="insp-label">UPI VPA:</span>
                    <span class="insp-val mono" style="font-weight:700;color:#8458B3;">${this.escapeHtml(node.id)}</span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">Entity Name:</span>
                    <span class="insp-val" style="font-weight:600;">${this.escapeHtml(node.label || node.id)}</span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">Node Category:</span>
                    <span class="insp-val" style="text-transform:capitalize;font-weight:600;color:${node.color || '#3b82f6'};">● ${(node.category || 'User Node').replace(/_/g, ' ')}</span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">Risk Evaluation:</span>
                    <span class="insp-val">${riskTag}</span>
                </div>
                ${scamRow}
                ${ringBadge}
                ${actionRow}
                ${lastAmountRow}
                <div class="insp-row">
                    <span class="insp-label">Account Age:</span>
                    <span class="insp-val" style="${parseFloat(age) < 24 ? 'color:#c62828;font-weight:700;' : ''}">
                        ${age} hrs ${parseFloat(age) < 24 ? '⚠️ (Zero-Day Fresh)' : '✓ (Established)'}
                    </span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">Inflow / Outflow:</span>
                    <span class="insp-val mono">${node.in_degree || 0} Inflow  ⇄  ${node.out_degree || 0} Outflow</span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">Hardware Device ID:</span>
                    <span class="insp-val mono" style="${isMuleDevice ? 'color:#d97706;font-weight:700;' : ''}">${this.escapeHtml(devId)}</span>
                </div>
                <div class="insp-row">
                    <span class="insp-label">National Registry:</span>
                    <span class="insp-val" style="${node.is_blacklisted ? 'color:#c62828;font-weight:700;' : 'color:#2e7d32;font-weight:600;'}">
                        ${node.is_blacklisted ? '🚨 Listed on National Cyber Crime Portal' : '✅ Clear (No prior reports)'}
                    </span>
                </div>
            </div>
        `;
    }

    applyForces() {
        const k = 0.04;
        const repulsion = 2200;
        const damping = 0.86;
        const cx = this.canvas.width / 2;
        const cy = this.canvas.height / 2;

        // Node repulsion
        for (let i = 0; i < this.nodes.length; i++) {
            const n1 = this.nodes[i];
            if (!this.isNodeVisible(n1)) continue;

            for (let j = i + 1; j < this.nodes.length; j++) {
                const n2 = this.nodes[j];
                if (!this.isNodeVisible(n2)) continue;

                const dx = n2.x - n1.x;
                const dy = n2.y - n1.y;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;

                if (dist < 260) {
                    const force = repulsion / (dist * dist);
                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;
                    n1.vx -= fx;
                    n1.vy -= fy;
                    n2.vx += fx;
                    n2.vy += fy;
                }
            }

            // Center gravity
            n1.vx += (cx - n1.x) * 0.0015;
            n1.vy += (cy - n1.y) * 0.0015;
        }

        // Link attraction
        for (const link of this.links) {
            const n1 = link.sourceNode;
            const n2 = link.targetNode;
            if (!this.isNodeVisible(n1) || !this.isNodeVisible(n2)) continue;

            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const desiredDist = 120;
            const force = (dist - desiredDist) * k;

            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            n1.vx += fx;
            n1.vy += fy;
            n2.vx -= fx;
            n2.vy -= fy;
        }

        // Apply velocities
        for (const n of this.nodes) {
            if (n === this.draggedNode) continue;
            n.vx *= damping;
            n.vy *= damping;
            n.x += n.vx;
            n.y += n.vy;
        }
    }

    animate() {
        this.applyForces();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.save();

        this.ctx.translate(this.panX, this.panY);
        this.ctx.scale(this.scale, this.scale);

        // Draw Links
        for (const link of this.links) {
            const u = link.sourceNode;
            const v = link.targetNode;
            if (!this.isNodeVisible(u) || !this.isNodeVisible(v)) continue;

            const isHighRiskEdge = u.category === "scammer_hub" || u.category === "mule_account" || v.category === "cashout_node";

            this.ctx.beginPath();
            this.ctx.moveTo(u.x, u.y);
            this.ctx.lineTo(v.x, v.y);
            this.ctx.strokeStyle = isHighRiskEdge ? "rgba(220, 38, 38, 0.85)" : "rgba(110, 96, 83, 0.45)";
            this.ctx.lineWidth = isHighRiskEdge ? 2.5 : 1.2;
            this.ctx.stroke();

            // Draw Edge Amount Label
            const midX = (u.x + v.x) / 2;
            const midY = (u.y + v.y) / 2;
            this.ctx.fillStyle = isHighRiskEdge ? "#dc2626" : "#2d2219";
            this.ctx.font = "bold 9px 'JetBrains Mono'";
            this.ctx.textAlign = "center";
            this.ctx.fillText(`₹${link.amount.toLocaleString()}`, midX, midY - 4);
        }

        // ── ANIMATED PARTICLES (Money Flow) — PRESERVED EXACTLY ──
        for (const p of this.particles) {
            if (!p.link || !this.isNodeVisible(p.link.sourceNode) || !this.isNodeVisible(p.link.targetNode)) continue;

            p.progress += p.speed;
            if (p.progress >= 1) p.progress = 0;

            const u = p.link.sourceNode;
            const v = p.link.targetNode;
            const px = u.x + (v.x - u.x) * p.progress;
            const py = u.y + (v.y - u.y) * p.progress;

            this.ctx.beginPath();
            this.ctx.arc(px, py, 3.5, 0, Math.PI * 2);
            this.ctx.fillStyle = "#1e40af";
            this.ctx.shadowColor = "#1e40af";
            this.ctx.shadowBlur = 4;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;
        }

        // Draw Nodes
        for (const n of this.nodes) {
            if (!this.isNodeVisible(n)) continue;

            const isSelected = this.selectedNode === n;
            const isHovered = this.hoveredNode === n;

            // Glowing Halo for Scammer & Mule Nodes
            if (n.category === "scammer_hub" || n.category === "mule_account" || isSelected) {
                this.ctx.beginPath();
                this.ctx.arc(n.x, n.y, n.radius + (isSelected ? 10 : 6), 0, Math.PI * 2);
                this.ctx.fillStyle = isSelected ? "rgba(15, 43, 92, 0.25)" : "rgba(220, 38, 38, 0.2)";
                this.ctx.fill();
            }

            // Node Circle
            this.ctx.beginPath();
            this.ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = n.color || "#3b82f6";
            this.ctx.fill();
            this.ctx.strokeStyle = isSelected ? "#0f2b5c" : "rgba(15, 43, 92, 0.35)";
            this.ctx.lineWidth = isSelected ? 3 : 1.2;
            this.ctx.stroke();

            // Node Label
            this.ctx.fillStyle = isSelected || isHovered ? "#0f2b5c" : "#2d2219";
            this.ctx.font = `${isSelected ? 'bold ' : ''}11px 'Plus Jakarta Sans'`;
            this.ctx.textAlign = "center";
            this.ctx.fillText(n.label, n.x, n.y + n.radius + 14);

            // Subtitle / VPA
            this.ctx.fillStyle = "#6e6053";
            this.ctx.font = "9px 'JetBrains Mono'";
            this.ctx.fillText(n.id, n.x, n.y + n.radius + 25);
        }

        this.ctx.restore();
    }
}

// Expose globally and instantiate on DOM ready
window.graphVisualizerInstance = null;
document.addEventListener("DOMContentLoaded", () => {
    window.graphVisualizerInstance = new MuleGraphVisualizer("mule-graph-canvas");
});
