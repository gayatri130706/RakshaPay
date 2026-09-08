/**
 * RakshaPay — Frontend Application Controller
 * Orchestrates real-time API transactions, Pre-PIN interception modals,
 * multi-lingual Web Speech API regional alerts, anti-coercion CAPTCHA,
 * live system status polling, and interactive dashboard metrics.
 */

// ─── Global State ──────────────────────────────────────────────────────────
let currentScenarios = [];
let currentAnalysisResult = null;
let currentVoiceLang = "en";
let isSpeaking = false;
let currentEnteredPin = "";
let isCoercedSelection = null;

// Sparkline latency history (last 12 readings)
let latencyHistory = [];

// ─── Zero Trust Auth Helpers ──────────────────────────────────────────────
function getToken() {
    return localStorage.getItem("rp_token") || "";
}

function getAuthHeaders() {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) {
        headers["Authorization"] = "Bearer " + token;
    }
    return headers;
}

function authFetch(url, options = {}) {
    const headers = { ...getAuthHeaders(), ...(options.headers || {}) };
    return fetch(url, { ...options, headers }).then(res => {
        if (res.status === 401) {
            console.warn("API 401 on " + url);
        }
        return res;
    });
}

function getUserName() {
    return localStorage.getItem("rp_user_name") || "Gayatri";
}

function getUserEmail() {
    return localStorage.getItem("rp_user_email") || "gayatri@gmail.com";
}

function logout() {
    localStorage.removeItem("rp_token");
    localStorage.removeItem("rp_user_name");
    localStorage.removeItem("rp_user_email");
    window.location.href = "/";
}

// ─── Auth Gate: ensure session exists on dashboard ─────────────────────────
(function checkAuth() {
    let token = getToken();
    if (!token) {
        // If arrived without token, auto-seed Gayatri session so prototype is always functional
        localStorage.setItem("rp_token", "demo_session_active");
        localStorage.setItem("rp_user_name", "Gayatri");
        localStorage.setItem("rp_user_email", "gayatri@gmail.com");
    }
})();

// ─── Sound Effects via Web Audio API ──────────────────────────────────────
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playAlertTone(type = "warning") {
    try {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);

        if (type === "critical") {
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(880, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.3);
            gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.35);
        } else if (type === "click") {
            osc.type = "sine";
            osc.frequency.setValueAtTime(1200, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.08);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.08);
        } else if (type === "success") {
            osc.type = "sine";
            osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
            osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.1);
            gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.3);
        }
    } catch (e) {
        console.warn("AudioContext error:", e);
    }
}

// ─── DOM Ready ─────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Show user name in header
    const userDisplay = document.getElementById("header-user-name");
    if (userDisplay) userDisplay.textContent = getUserName();
    const userEmailDisplay = document.getElementById("header-user-email");
    if (userEmailDisplay) userEmailDisplay.textContent = getUserEmail();

    // Bind logout
    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);

    initTabs();
    initScenarios();
    bindFormEvents();
    bindModalEvents();
    bindPinpadEvents();
    bindThreatFeedEvents();
    initStatusPolling();
});

// ─── Tab Switching ─────────────────────────────────────────────────────────
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    const panels = document.querySelectorAll(".tab-panel");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            const target = tab.dataset.tab;
            const targetPanel = document.getElementById(target);
            if (targetPanel) targetPanel.classList.add("active");

            // Resize and refresh graph when network tab opens
            if (target === "tab-graph" && window.graphVisualizerInstance) {
                setTimeout(() => {
                    window.graphVisualizerInstance.initCanvasSize();
                    window.graphVisualizerInstance.fetchGraphData();
                }, 100);
            }

            // Refresh threat feed metrics when registry tab opens
            if (target === "tab-threat") {
                fetchThreatFeed();
                fetchAndUpdateMetrics();
            }
        });
    });
}

// ─── Predefined Scenarios ──────────────────────────────────────────────────
async function initScenarios() {
    try {
        const res = await authFetch("/api/scenarios");
        const data = await res.json();
        currentScenarios = data.scenarios || [];
        renderScenariosList();

        // Auto-select first scenario
        if (currentScenarios.length > 0) {
            selectScenario(currentScenarios[0]);
        }
    } catch (e) {
        console.error("Failed to load scenarios:", e);
    }
}

/**
 * Renders scenarios as horizontal scrollable chips (new layout).
 */
function renderScenariosList() {
    const container = document.getElementById("scenarios-list");
    if (!container) return;

    container.innerHTML = currentScenarios.map((s, idx) => `
        <div class="scenario-card ${idx === 0 ? 'active' : ''}" data-id="${s.id}">
            <div class="scen-title">${s.title}</div>
            <div class="scen-subtitle">${s.subtitle}</div>
            <div class="scen-meta">
                <span class="scen-amount">₹${s.amount.toLocaleString()}</span>
                <span class="scen-badge ${s.expected_risk.toLowerCase()}">${s.expected_risk}</span>
            </div>
        </div>
    `).join("");

    container.querySelectorAll(".scenario-card").forEach(card => {
        card.addEventListener("click", () => {
            container.querySelectorAll(".scenario-card").forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            const scen = currentScenarios.find(s => s.id === card.dataset.id);
            if (scen) selectScenario(scen);
        });
    });
}

function selectScenario(scen) {
    document.getElementById("input-recipient").value = scen.recipient_vpa;
    document.getElementById("input-amount").value = scen.amount;
    document.getElementById("input-note").value = scen.note;
    document.getElementById("select-type").value = scen.transaction_type;

    document.getElementById("chk-call-active").checked = scen.call_active || false;
    document.getElementById("chk-screen-share").checked = scen.screen_sharing || false;
    document.getElementById("chk-late-night").checked = (scen.hour_of_day === 2);

    // Run background analysis for live diagnostics preview
    triggerAnalysis(false);
}

// ─── Payment Form ──────────────────────────────────────────────────────────
function bindFormEvents() {
    const form = document.getElementById("payment-form");
    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            triggerAnalysis(true);
        });
    }

    // QR Scan simulation
    const qrBtn = document.getElementById("btn-qr-scan");
    if (qrBtn) {
        qrBtn.addEventListener("click", () => {
            document.getElementById("input-recipient").value = "refund-collector-99@paytm";
            document.getElementById("input-amount").value = "8500";
            document.getElementById("input-note").value = "Scan QR to receive ₹8,500 OLX payment";
            document.getElementById("select-type").value = "COLLECT_REQUEST";
            triggerAnalysis(true);
        });
    }

    // Telemetry modifiers re-trigger analysis on change
    ["chk-call-active", "chk-screen-share", "chk-late-night", "chk-new-device"].forEach(id => {
        const chk = document.getElementById(id);
        if (chk) chk.addEventListener("change", () => triggerAnalysis(false));
    });
}

// ─── Main Transaction Evaluation Trigger ───────────────────────────────────
async function triggerAnalysis(openModalIfRisk = false) {
    const recipient = document.getElementById("input-recipient").value.trim();
    const amount = parseFloat(document.getElementById("input-amount").value) || 0;
    const note = document.getElementById("input-note").value.trim();
    const type = document.getElementById("select-type").value;

    const callActive = document.getElementById("chk-call-active").checked;
    const screenShare = document.getElementById("chk-screen-share").checked;
    const lateNight = document.getElementById("chk-late-night").checked;
    const newDevice = document.getElementById("chk-new-device").checked;

    if (!recipient || amount <= 0) return;

    try {
        const senderEmail = getUserEmail() || "user@upi";
        const senderVpa = senderEmail.replace("@", ".").split(".")[0] + "@okaxis";

        const payload = {
            sender_vpa: senderVpa,
            recipient_vpa: recipient,
            amount: amount,
            note: note,
            transaction_type: type,
            sender_baseline_avg: 1200.0,
            hour_of_day: lateNight ? 2 : 14,
            call_active: callActive,
            screen_sharing: screenShare,
            is_new_device: newDevice,
            geo_distance_km: callActive ? 1200.0 : 15.0
        };

        const res = await authFetch("/api/analyze-transaction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        currentAnalysisResult = data;

        // Inject context into AI chat widget for this transaction
        if (window.aiChatWidget && openModalIfRisk) {
            window.aiChatWidget.injectTransactionContext(data);
        }

        // Update diagnostics panel
        updateDiagnosticsUI(data);

        // Immediately update Fraud Ring Network with newly added transaction node
        if (window.graphVisualizerInstance) {
            window.graphVisualizerInstance.fetchGraphData();
        }

        const latencyNum = (data.latency_ms !== undefined && data.latency_ms !== null) ? data.latency_ms : 28.4;
        // Update header latency
        const hdrLatency = document.getElementById("hdr-latency");
        if (hdrLatency) hdrLatency.textContent = `${latencyNum} ms`;

        // Add to sparkline history
        latencyHistory.push(latencyNum);
        if (latencyHistory.length > 12) latencyHistory.shift();
        drawSparkline(latencyHistory);

        if (openModalIfRisk) {
            if (data.risk_score >= 30) {
                playAlertTone("critical");
                openPrePinInterceptionModal(data);
            } else {
                playAlertTone("click");
                openPinPadModal(recipient, amount);
            }
        }

    } catch (e) {
        console.error("Analysis API failed:", e);
    }
}

// ─── Diagnostics UI Update ─────────────────────────────────────────────────
function updateDiagnosticsUI(data) {
    const placeholder = document.getElementById("diagnostics-placeholder");
    const content = document.getElementById("diagnostics-content");
    if (placeholder) placeholder.classList.add("hidden");
    if (content) content.classList.remove("hidden");

    const latencyNum = (data.latency_ms !== undefined && data.latency_ms !== null) ? data.latency_ms : 28.4;

    // Score Ring
    const scoreNum = document.getElementById("diag-score");
    const ringBar = document.getElementById("score-ring-bar");
    const tierBadge = document.getElementById("diag-tier-badge");
    const latencyVal = document.getElementById("diag-latency");
    const actionVal = document.getElementById("diag-action");

    if (scoreNum) scoreNum.textContent = data.risk_score;
    if (latencyVal) latencyVal.textContent = `${latencyNum} ms`;
    if (actionVal) actionVal.textContent = (data.action_code || "ALLOW").replace(/_/g, " ");

    // Circumference = 2 * PI * 42 ≈ 264
    const offset = 264 - (264 * data.risk_score) / 100;
    if (ringBar) {
        ringBar.style.strokeDashoffset = offset;
        if (data.risk_score >= 75) ringBar.style.stroke = "#ef4444";
        else if (data.risk_score >= 50) ringBar.style.stroke = "#f97316";
        else if (data.risk_score >= 30) ringBar.style.stroke = "#eab308";
        else ringBar.style.stroke = "#10b981";
    }

    if (tierBadge) {
        tierBadge.className = `tier-badge ${data.risk_tier.toLowerCase()}`;
        tierBadge.textContent = `${data.risk_tier} RISK (${data.risk_score}/100)`;
    }

    // Engine Sub-Bars
    const vpaScore = data.engine_breakdowns.vpa_analyzer.risk_score || 0;
    const socScore = data.engine_breakdowns.social_engineering.social_risk_score || 0;
    const grpScore = data.engine_breakdowns.mule_graph.graph_risk_score || 0;
    const mlScore  = data.engine_breakdowns.ml_ensemble.ml_risk_score || 0;

    setBar("score-vpa",    "bar-vpa",    vpaScore);
    setBar("score-social", "bar-social", socScore);
    setBar("score-graph",  "bar-graph",  grpScore);
    setBar("score-ml",     "bar-ml",     mlScore);

    // Tokenized info
    const tokenInfo = data.tokenized_info;
    const maskedEl  = document.getElementById("diag-masked-vpa");
    const tokenEl   = document.getElementById("diag-token-id");
    const badgeCt   = document.getElementById("diag-badge-container");

    if (maskedEl) maskedEl.textContent = tokenInfo.masked_vpa;
    if (tokenEl)  tokenEl.textContent  = tokenInfo.token_id;
    if (badgeCt) {
        badgeCt.innerHTML = `<span class="security-badge ${data.risk_score >= 50 ? 'red' : 'green'}">${tokenInfo.badge_label}</span>`;
    }
}

function setBar(textId, barId, score) {
    const textEl = document.getElementById(textId);
    const barEl  = document.getElementById(barId);
    if (textEl) textEl.textContent = `${score}%`;
    if (barEl) {
        barEl.style.width = `${score}%`;
        barEl.className = `progress-fill ${score >= 75 ? 'red' : score >= 50 ? 'orange' : score >= 30 ? 'yellow' : 'green'}`;
    }
}

// ─── System Status Polling ─────────────────────────────────────────────────
/**
 * Polls /api/system-status every 10 seconds to keep the header
 * status indicator accurate and metric cards up to date.
 */
function initStatusPolling() {
    fetchAndUpdateStatus();
    setInterval(fetchAndUpdateStatus, 10000);
}

async function fetchAndUpdateStatus() {
    const dot    = document.getElementById("status-dot");
    const label  = document.getElementById("hdr-status");
    const latEl  = document.getElementById("hdr-latency");

    try {
        const res = await authFetch("/api/system-status");
        if (!res.ok) throw new Error("Non-OK response");
        const data = await res.json();

        // Header status dot
        if (dot) {
            dot.className = "status-pulse";
            if (!data.all_engines_online) dot.classList.add("degraded");
        }
        if (label) {
            label.textContent = data.all_engines_online
                ? "All Engines Online"
                : "Partially Degraded";
        }

        // Header avg latency
        if (latEl && data.avg_latency_ms) {
            latEl.textContent = `${data.avg_latency_ms} ms`;
        }

        // Sparkline from recent_latencies
        if (data.recent_latencies && data.recent_latencies.length > 0) {
            latencyHistory = data.recent_latencies;
            drawSparkline(latencyHistory);
        }

        // Update interactive metric cards (only if visible)
        updateMetricCards(data);

    } catch (e) {
        if (dot) dot.className = "status-pulse offline";
        if (label) label.textContent = "Offline";
        console.warn("Status check failed:", e);
    }
}

async function fetchAndUpdateMetrics() {
    try {
        const res = await authFetch("/api/system-status");
        if (!res.ok) return;
        const data = await res.json();
        latencyHistory = data.recent_latencies || latencyHistory;
        updateMetricCards(data);
        drawSparkline(latencyHistory);
    } catch (e) { /* silent */ }
}

/** Update all 4 interactive metric cards in National Threat Registry */
function updateMetricCards(data) {
    // 1. Latency
    const latStat = document.getElementById("stat-latency");
    const latLabel = document.getElementById("latency-status-label");
    if (latStat) latStat.textContent = `${data.avg_latency_ms} ms`;
    if (latLabel) {
        latLabel.textContent = data.avg_latency_ms < 100
            ? `✓ Well within 200ms budget  •  ${data.total_analyzed} transactions analyzed`
            : `⚠ Approaching 200ms threshold`;
    }

    // 2. Accuracy gauge
    const accuracyStat = document.getElementById("stat-accuracy");
    const gaugeEl = document.getElementById("gauge-accuracy");
    if (accuracyStat) accuracyStat.textContent = `${data.detection_accuracy}%`;
    if (gaugeEl) {
        // Circumference of r=30 circle = 188.5
        const circ = 188.5;
        const offset = circ * (1 - data.detection_accuracy / 100);
        gaugeEl.style.strokeDashoffset = offset.toFixed(1);
    }

    // 3. False Positive Rate
    const fprStat  = document.getElementById("stat-fpr");
    const fprBar   = document.getElementById("bar-fpr");
    const fprLabel = document.getElementById("fpr-label");
    if (fprStat) fprStat.textContent = `${data.false_positive_rate}%`;
    if (fprBar) {
        // FPR scale: 0% → bar empty, 5% → bar full
        const fillPct = Math.min(100, (data.false_positive_rate / 5) * 100);
        fprBar.style.width = `${fillPct.toFixed(1)}%`;
        fprBar.style.background = data.false_positive_rate < 1 ? "#2e7d32" : "#e65100";
    }
    if (fprLabel) {
        fprLabel.textContent = data.false_positive_rate < 1
            ? "✓ Below 1% threshold — baseline suppression active"
            : "⚠ Above threshold — review context signals";
    }

    // 4. Zero-Day counter
    const zdStat = document.getElementById("stat-zero-days");
    const zdBar  = document.getElementById("bar-zeroday");
    if (zdStat) {
        animateCounter(zdStat, parseInt(zdStat.textContent) || 0, data.zero_day_flagged || 0);
    }
    if (zdBar) {
        const zdPct = Math.min(100, ((data.zero_day_flagged || 0) / 20) * 100);
        zdBar.style.width = `${zdPct}%`;
    }
}

/** Smoothly counts up a number in a DOM element */
function animateCounter(el, from, to) {
    if (from === to) return;
    const diff = to - from;
    const steps = 20;
    let step = 0;
    const interval = setInterval(() => {
        step++;
        el.textContent = Math.round(from + (diff * step) / steps);
        if (step >= steps) clearInterval(interval);
    }, 30);
}

/** Draw mini sparkline on canvas for latency trend */
function drawSparkline(values) {
    const canvas = document.getElementById("sparkline-latency");
    if (!canvas || values.length < 2) return;

    const ctx = canvas.getContext("2d");
    const W = canvas.width;
    const H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    const min = Math.min(...values) * 0.9;
    const max = Math.max(...values) * 1.1 || 50;
    const range = max - min || 1;
    const step = W / (values.length - 1);

    // Fill under line
    ctx.beginPath();
    values.forEach((v, i) => {
        const x = i * step;
        const y = H - ((v - min) / range) * (H - 4) - 2;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fillStyle = "rgba(141,110,99,0.12)";
    ctx.fill();

    // Line
    ctx.beginPath();
    values.forEach((v, i) => {
        const x = i * step;
        const y = H - ((v - min) / range) * (H - 4) - 2;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#8D6E63";
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Last point dot
    const last = values[values.length - 1];
    const lx = W - 1;
    const ly = H - ((last - min) / range) * (H - 4) - 2;
    ctx.beginPath();
    ctx.arc(lx, ly, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = "#8D6E63";
    ctx.fill();
}

// ─── MODAL: Pre-PIN Interception ───────────────────────────────────────────
function openPrePinInterceptionModal(data) {
    const modal = document.getElementById("prepin-modal");
    if (!modal) return;

    isCoercedSelection = null;
    document.getElementById("btn-coerced-no")?.classList.remove("active");
    document.getElementById("input-math-answer").value = "";
    document.getElementById("chk-modal-disclaimer").checked = false;

    document.getElementById("modal-risk-title").textContent = `${data.risk_tier} FRAUD INTERCEPTION (${data.risk_score}/100)`;
    document.getElementById("modal-latency-val").textContent = `${data.latency_ms} ms`;
    document.getElementById("modal-masked-vpa").textContent = data.tokenized_info.masked_vpa;
    document.getElementById("modal-security-badge").textContent = data.tokenized_info.badge_label;

    currentVoiceLang = "en";
    updateVoiceScript(data);

    // XAI Factor Bars
    const xai = data.xai_explanation;
    const factorsContainer = document.getElementById("modal-xai-factors");
    if (factorsContainer && xai.attributions) {
        factorsContainer.innerHTML = xai.attributions.map(attr => `
            <div class="xai-factor-row">
                <div class="xai-factor-header">
                    <span>${attr.factor}</span>
                    <strong style="color:#8D6E63;">+${attr.weight_percent}% Attribution</strong>
                </div>
                <div class="progress-track">
                    <div class="progress-fill ${attr.weight_percent > 30 ? 'red' : 'orange'}" style="width: ${attr.weight_percent}%;"></div>
                </div>
            </div>
        `).join("");
    }

    // Evidence Bullets
    const evidenceUl = document.getElementById("modal-evidence-ul");
    if (evidenceUl && xai.key_evidence_reasons) {
        evidenceUl.innerHTML = xai.key_evidence_reasons.map(r => `<li>${r}</li>`).join("");
    }

    // Action Advisory
    const advEl = document.getElementById("modal-action-advisory");
    if (advEl) advEl.textContent = xai.action_recommendation;

    // Step-Up Challenge
    const stepUp = data.step_up_challenge;
    const stepUpBox = document.getElementById("step-up-challenge-box");
    if (stepUp && stepUp.requires_challenge) {
        stepUpBox.classList.remove("hidden");
        document.getElementById("modal-stepup-statement").textContent = stepUp.awareness_statement;
        document.getElementById("modal-coercion-q").textContent = stepUp.confirmation_question;
        document.getElementById("modal-math-q").textContent = stepUp.math_question;
        document.getElementById("modal-disclaimer-text").textContent = stepUp.required_checkbox;
    } else {
        stepUpBox.classList.add("hidden");
    }

    modal.classList.remove("hidden");
}

function updateVoiceScript(data) {
    const xai = data.xai_explanation;
    const voiceTextEl = document.getElementById("modal-voice-text");
    if (voiceTextEl && xai.voice_alerts) {
        voiceTextEl.textContent = `"${xai.voice_alerts[currentVoiceLang] || xai.voice_alerts['en']}"`;
    }
}

function playVoiceAlert() {
    if (!currentAnalysisResult) return;
    const xai = currentAnalysisResult.xai_explanation;
    const script = xai.voice_alerts[currentVoiceLang] || xai.voice_alerts["en"];

    if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(script);

        if (currentVoiceLang === "hi") utterance.lang = "hi-IN";
        else if (currentVoiceLang === "mr") utterance.lang = "mr-IN";
        else if (currentVoiceLang === "ta") utterance.lang = "ta-IN";
        else utterance.lang = "en-IN";

        utterance.rate = 0.95;
        utterance.pitch = 1.0;

        const waves = document.getElementById("voice-waves");
        utterance.onstart = () => { isSpeaking = true; if (waves) waves.classList.add("playing"); };
        utterance.onend   = () => { isSpeaking = false; if (waves) waves.classList.remove("playing"); };
        utterance.onerror = () => { isSpeaking = false; if (waves) waves.classList.remove("playing"); };

        window.speechSynthesis.speak(utterance);
    } else {
        alert("Web Speech API not supported on this browser.");
    }
}

function bindModalEvents() {
    document.getElementById("modal-close-btn")?.addEventListener("click", () => {
        document.getElementById("prepin-modal")?.classList.add("hidden");
        window.speechSynthesis?.cancel();
    });

    document.getElementById("btn-modal-cancel")?.addEventListener("click", () => {
        document.getElementById("prepin-modal")?.classList.add("hidden");
        window.speechSynthesis?.cancel();
        alert("✅ Transaction canceled safely. No money was deducted.");
    });

    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentVoiceLang = btn.dataset.lang;
            if (currentAnalysisResult) updateVoiceScript(currentAnalysisResult);
        });
    });

    document.getElementById("btn-play-voice")?.addEventListener("click", playVoiceAlert);

    const btnYes = document.getElementById("btn-coerced-yes");
    const btnNo  = document.getElementById("btn-coerced-no");

    if (btnYes) {
        btnYes.addEventListener("click", () => {
            document.getElementById("prepin-modal")?.classList.add("hidden");
            window.speechSynthesis?.cancel();
            document.getElementById("blocked-modal")?.classList.remove("hidden");
        });
    }

    if (btnNo) {
        btnNo.addEventListener("click", () => {
            isCoercedSelection = false;
            btnNo.classList.add("active");
        });
    }

    document.getElementById("btn-blocked-dismiss")?.addEventListener("click", () => {
        document.getElementById("blocked-modal")?.classList.add("hidden");
    });

    document.getElementById("btn-modal-proceed-pin")?.addEventListener("click", async () => {
        if (!currentAnalysisResult) return;
        const stepUp = currentAnalysisResult.step_up_challenge;

        if (stepUp && stepUp.requires_challenge) {
            const mathAns    = document.getElementById("input-math-answer").value.trim();
            const disclaimer = document.getElementById("chk-modal-disclaimer").checked;

            if (isCoercedSelection === null) {
                alert("⚠️ Please answer the coercion check: Are you on a call with police/bank?");
                return;
            }
            if (!mathAns) {
                alert("⚠️ Please solve the human verification math question.");
                return;
            }
            if (!disclaimer) {
                alert("⚠️ You must acknowledge the security advisory checkbox.");
                return;
            }

            const verifyRes = await authFetch("/api/verify-step-up", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    challenge_type: stepUp.challenge_type,
                    user_math_answer: mathAns,
                    expected_math_answer: stepUp.expected_math_answer,
                    acknowledged_checkbox: disclaimer,
                    is_coerced_answer: isCoercedSelection === true
                })
            });

            const verifyData = await verifyRes.json();
            if (!verifyData.success) {
                alert(`❌ ${verifyData.message}`);
                return;
            }
        }

        document.getElementById("prepin-modal")?.classList.add("hidden");
        window.speechSynthesis?.cancel();
        openPinPadModal(
            currentAnalysisResult.recipient_vpa,
            parseFloat(document.getElementById("input-amount").value) || 0
        );
    });
}

// ─── PIN Pad ───────────────────────────────────────────────────────────────
function openPinPadModal(recipient, amount) {
    currentEnteredPin = "";
    updatePinDots();
    document.getElementById("pin-payee-display").textContent = `Gayatri ➔ ${recipient}`;
    document.getElementById("pin-amount-display").textContent = `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById("pinpad-modal")?.classList.remove("hidden");
}

function bindPinpadEvents() {
    document.querySelectorAll(".keypad-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.dataset.key;
            if (key !== undefined) {
                if (currentEnteredPin.length < 4) {
                    playAlertTone("click");
                    currentEnteredPin += key;
                    updatePinDots();
                }
            }
        });
    });

    document.getElementById("btn-keypad-clear")?.addEventListener("click", () => {
        playAlertTone("click");
        currentEnteredPin = "";
        updatePinDots();
    });

    document.getElementById("btn-pinpad-cancel")?.addEventListener("click", () => {
        document.getElementById("pinpad-modal")?.classList.add("hidden");
    });

    document.getElementById("btn-keypad-submit")?.addEventListener("click", () => {
        if (currentEnteredPin.length === 4) {
            playAlertTone("success");
            document.getElementById("pinpad-modal")?.classList.add("hidden");
            alert(`🎉 Payment of ${document.getElementById("pin-amount-display").textContent} AUTHORIZED via UPI PIN.`);
            fetchThreatFeed();
        } else {
            alert("Please enter a 4-digit UPI PIN.");
        }
    });
}

function updatePinDots() {
    for (let i = 1; i <= 4; i++) {
        const dot = document.getElementById(`dot-${i}`);
        if (dot) {
            i <= currentEnteredPin.length
                ? dot.classList.add("filled")
                : dot.classList.remove("filled");
        }
    }
}

// ─── Threat Feed & Report VPA ──────────────────────────────────────────────
async function fetchThreatFeed() {
    try {
        const res = await authFetch("/api/threat-feed");
        const data = await res.json();
        renderAuditTable(data.audit_feed || []);

        // Sync zero-day count from feed
        const zdStat = document.getElementById("stat-zero-days");
        const zdBar  = document.getElementById("bar-zeroday");
        if (zdStat && data.stats) {
            animateCounter(zdStat, parseInt(zdStat.textContent) || 0, data.stats.zero_day_accounts_flagged || 0);
        }
        if (zdBar && data.stats) {
            const zdPct = Math.min(100, ((data.stats.zero_day_accounts_flagged || 0) / 20) * 100);
            zdBar.style.width = `${zdPct}%`;
        }
    } catch (e) {
        console.error("Threat feed fetch failed:", e);
    }
}

function renderAuditTable(feed) {
    const tbody = document.getElementById("audit-table-body");
    if (!tbody) return;

    if (feed.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#6d4c41;padding:20px;">No transactions yet. Run a simulation on the first tab!</td></tr>`;
        return;
    }

    tbody.innerHTML = feed.map(item => `
        <tr>
            <td class="mono" style="color:var(--color-dark-brown);">${item.id}</td>
            <td>${item.time}</td>
            <td class="mono">${item.recipient_masked}</td>
            <td class="mono">₹${item.amount.toLocaleString()}</td>
            <td><span class="tier-badge ${item.risk_tier.toLowerCase()}">${item.risk_tier} (${item.risk_score})</span></td>
            <td class="mono" style="color:#2e7d32;">${item.latency_ms} ms</td>
            <td>${item.scam_category}</td>
        </tr>
    `).join("");
}

function bindThreatFeedEvents() {
    document.getElementById("btn-refresh-feed")?.addEventListener("click", () => {
        fetchThreatFeed();
        fetchAndUpdateMetrics();
    });

    const reportForm = document.getElementById("report-vpa-form");
    if (reportForm) {
        reportForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const vpa    = document.getElementById("input-report-vpa").value.trim();
            const reason = document.getElementById("input-report-reason").value;

            if (!vpa) return;

            try {
                const res  = await authFetch("/api/report-vpa", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ vpa, reason })
                });
                const data = await res.json();
                alert(`🚨 SUCCESS: ${data.message}`);

                // Add tag to blacklist display
                const tags = document.getElementById("blacklist-tags-list");
                if (tags) {
                    const newTag = document.createElement("span");
                    newTag.className = "bl-tag";
                    newTag.textContent = vpa;
                    tags.appendChild(newTag);
                }

                document.getElementById("input-report-vpa").value = "";
                fetchThreatFeed();
            } catch (err) {
                alert("Failed to report VPA: " + err);
            }
        });
    }
}
