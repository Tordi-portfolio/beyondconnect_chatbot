(function () {
  const cfg = document.getElementById("cfg");
  const CHAT_URL = cfg.dataset.chatUrl;
  const STORAGE_KEY = "beyondconnect_cid";

  const box = document.getElementById("messages");
  const welcome = document.getElementById("welcome");
  const form = document.getElementById("composer");
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("send");

  let cid = null;
  try { cid = localStorage.getItem(STORAGE_KEY); } catch (e) {}
  let busy = false;

  // ---------- safe mini-markdown ----------
  function inline(s) {
    return s
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
      .replace(/(^|[\s(])(https?:\/\/[^\s<)]+)/g, '$1<a href="$2" target="_blank" rel="noopener">$2</a>');
  }
  function render(md) {
    const esc = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    let html = "", inList = false;
    for (const line of esc.split("\n")) {
      const m = line.match(/^\s*[-*•]\s+(.*)$/);
      if (m) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += "<li>" + inline(m[1]) + "</li>";
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        html += line.trim() === "" ? '<div class="gap"></div>' : "<p>" + inline(line) + "</p>";
      }
    }
    if (inList) html += "</ul>";
    return html;
  }

  // ---------- UI helpers ----------
  function addMessage(role, text) {
    if (welcome) welcome.style.display = "none";
    const div = document.createElement("div");
    div.className = "msg " + role;
    if (role === "user") div.textContent = text; else div.innerHTML = render(text);
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
  }
  function addTyping() {
    if (welcome) welcome.style.display = "none";
    const div = document.createElement("div");
    div.className = "msg bot";
    div.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return div;
  }
  function autosize() {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 140) + "px";
  }

  // ---------- chat ----------
  async function send(text) {
    text = text.trim();
    if (!text || busy) return;
    busy = true; sendBtn.disabled = true;
    addMessage("user", text);
    input.value = ""; autosize();
    const typing = addTyping();
    try {
      const res = await fetch(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, conversation_id: cid }),
      });
      const data = await res.json().catch(() => ({}));
      typing.remove();
      if (data.conversation_id) {
        cid = data.conversation_id;
        try { localStorage.setItem(STORAGE_KEY, cid); } catch (e) {}
      }
      if (res.ok && data.reply) addMessage("bot", data.reply);
      else addMessage("error", data.error || "Something went wrong. Please try again.");
    } catch (e) {
      typing.remove();
      addMessage("error", "Network problem. Please check your connection and try again.");
    } finally {
      busy = false; sendBtn.disabled = false; input.focus();
    }
  }

  async function loadHistory() {
    if (!cid) return;
    try {
      const res = await fetch(CHAT_URL + cid + "/");
      const data = await res.json();
      (data.messages || []).forEach((m) => addMessage(m.role === "user" ? "user" : "bot", m.content));
    } catch (e) {}
  }

  form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
  input.addEventListener("input", autosize);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => send(c.textContent)));
  document.getElementById("newChat").addEventListener("click", () => {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    cid = null;
    box.querySelectorAll(".msg").forEach((n) => n.remove());
    welcome.style.display = "";
  });

  loadHistory();
})();
