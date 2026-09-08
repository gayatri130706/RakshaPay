/**
 * RakshaPay — AI Fraud Advisor Chat Widget
 * Powered by Gemini 1.5 Flash via /api/ai-chat
 */
class AIChatWidget {
  constructor() {
    this.history = [];
    this.isOpen = false;
  }

  getToken() {
    return localStorage.getItem("rp_token") || "";
  }

  init() {
    const fab = document.getElementById("ai-chat-fab");
    this.panel = document.getElementById("ai-chat-panel");
    this.input = document.getElementById("ai-chat-input");
    this.messages = document.getElementById("ai-chat-messages");
    if (!fab || !this.panel) return;

    fab.addEventListener("click", () => this.toggle());
    document.getElementById("ai-chat-close")?.addEventListener("click", () => this.close());
    document.getElementById("ai-chat-send")?.addEventListener("click", () => this.send());
    this.input?.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });

    document.querySelectorAll(".ai-suggest-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        if (this.input) {
          this.input.value = chip.textContent;
          this.send();
        }
      });
    });

    this.addMessage("bot", "Hi! I am the RakshaPay AI Fraud Advisor, powered by Gemini. Ask me anything about UPI fraud, scam patterns, risk scores, or how to stay safe.");
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  open() {
    this.isOpen = true;
    this.panel.classList.add("open");
    this.input?.focus();
    const badge = document.getElementById("ai-chat-badge");
    if (badge) badge.style.display = "none";
  }

  close() {
    this.isOpen = false;
    this.panel.classList.remove("open");
  }

  addMessage(role, text, isLoading = false) {
    if (!this.messages) return null;
    const div = document.createElement("div");
    div.className = "ai-msg ai-msg-" + role;
    if (isLoading) {
      div.innerHTML = "<span class='ai-typing'><span></span><span></span><span></span></span>";
    } else {
      const bubble = document.createElement("div");
      bubble.className = "ai-msg-bubble";
      bubble.innerHTML = String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
      div.appendChild(bubble);
    }
    this.messages.appendChild(div);
    this.messages.scrollTop = this.messages.scrollHeight;
    return div;
  }

  async send() {
    const text = this.input?.value?.trim();
    if (!text) return;
    this.input.value = "";
    this.addMessage("user", text);
    this.history.push({ role: "user", content: text });
    const loadingEl = this.addMessage("bot", "", true);

    try {
      const res = await fetch("/api/ai-chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + this.getToken()
        },
        body: JSON.stringify({ message: text, history: this.history.slice(-6) })
      });

      if (res.status === 401) {
        loadingEl?.remove();
        this.addMessage("bot", "Session expired. Please log in again.");
        setTimeout(() => { window.location.href = "/"; }, 2000);
        return;
      }
      if (!res.ok) throw new Error("API error " + res.status);
      const data = await res.json();
      loadingEl?.remove();
      const reply = data.reply || "Sorry, I could not get a response.";
      this.addMessage("bot", reply);
      this.history.push({ role: "assistant", content: reply });
      if (this.history.length > 20) this.history = this.history.slice(-20);
    } catch (e) {
      loadingEl?.remove();
      this.addMessage("bot", "Network error. Please try again.");
    }
  }

  injectTransactionContext(data) {
    if (!data) return;
    const msg = "New analysis: " + (data.recipient_vpa || "") + " — Risk " + data.risk_score + "/100 (" + data.risk_tier + "). Action: " + (data.action_code || "").replace(/_/g, " ") + ". What would you like to know?";
    this.history = [];
    this.addMessage("bot", msg);
    this.history.push({ role: "assistant", content: msg });
    if (!this.isOpen) {
      const badge = document.getElementById("ai-chat-badge");
      if (badge) badge.style.display = "flex";
    }
  }
}

window.aiChatWidget = null;
document.addEventListener("DOMContentLoaded", () => {
  window.aiChatWidget = new AIChatWidget();
  window.aiChatWidget.init();
});