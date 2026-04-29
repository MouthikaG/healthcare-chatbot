document.addEventListener("DOMContentLoaded", () => {
  const chatArea = document.getElementById("chat-area");
  const input = document.getElementById("message-input");
  const sendBtn = document.getElementById("send-btn");
  const prompts = document.querySelectorAll(".prompt");
  const clearBtn = document.getElementById("clear-chat");
  const collapseBtn = document.getElementById("collapse-btn");
  const expandBtn = document.getElementById("expand-btn");

  if (!chatArea) {
    console.error("chat-area not found in DOM.");
    return;
  }

  function insertIntroIfEmpty() {
    if (chatArea.children.length === 0) {
      const introHTML = `
        <div class="bot-card intro">
          <div class="bot-card-icon">🩺</div>
          <div class="bot-card-body">
            <strong>Hi, I'm MedAI</strong> — Your Healthcare Symptom Checker.<br/>
            You can describe your symptoms in a sentence, for example:
            <ul>
              <li>I have fever and body pain for 3 days</li>
              <li>I feel chest pain and shortness of breath</li>
              <li>I have stomach pain and diarrhoea</li>
            </ul>
            <div class="warning">⚠️ I do <strong>not</strong> replace a doctor or emergency services.</div>
          </div>
        </div>
      `;
      const frag = document.createRange().createContextualFragment(introHTML);
      chatArea.appendChild(frag);
    }
  }

  insertIntroIfEmpty();

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function createBubble(text, who = "bot") {
    const wrap = document.createElement("div");
    wrap.className = "bubble " + (who === "user" ? "user-bubble" : "bot-bubble");
    const p = document.createElement("div");
    p.textContent = text;
    wrap.appendChild(p);
    const ts = document.createElement("span");
    ts.className = "ts";
    ts.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    wrap.appendChild(ts);
    return wrap;
  }

  function appendBotMessage(msg) {
    const paragraphs = msg.split("\n\n");
    paragraphs.forEach(par => {
      const trimmed = par.trim();
      if (!trimmed) return;
      const el = createBubble(trimmed, "bot");
      chatArea.appendChild(el);
    });
    scrollToBottom();
  }

  let pending = false;
  async function sendMessage() {
    if (pending) return;
    const message = input.value.trim();
    if (!message) return;

    const userB = createBubble(message, "user");
    chatArea.appendChild(userB);
    input.value = "";
    scrollToBottom();

    const typing = createBubble("Typing…", "bot");
    typing.style.opacity = 0.8;
    chatArea.appendChild(typing);
    scrollToBottom();

    pending = true;
    sendBtn.disabled = true;
    try {
      const resp = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message})
      });

      let data = {};
      try { data = await resp.json(); } catch(e) { data = {}; }

      typing.remove();

      if (!resp.ok) {
        const errMsg = data.error || "Server error";
        const err = createBubble("Error: " + errMsg, "bot");
        chatArea.appendChild(err);
      } else {
        appendBotMessage(data.reply || "Sorry, I didn't understand that.");
      }
    } catch (e) {
      typing.remove();
      const err = createBubble("Network error. Try again.", "bot");
      chatArea.appendChild(err);
      console.error(e);
    } finally {
      pending = false;
      sendBtn.disabled = false;
      input.focus();
      scrollToBottom();
    }
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  prompts.forEach(btn => {
    btn.addEventListener("click", () => {
      input.value = btn.textContent.trim();
      input.focus();
    });
  });

  clearBtn?.addEventListener("click", () => {
    chatArea.innerHTML = "";
    insertIntroIfEmpty();
    scrollToBottom();
    input.focus();
  });

  collapseBtn?.addEventListener("click", () => {
    document.body.classList.toggle("sidebar-collapsed");
    const collapsed = document.body.classList.contains("sidebar-collapsed");
    collapseBtn.textContent = collapsed ? "»" : "«";
    setTimeout(scrollToBottom, 120);
  });

  expandBtn?.addEventListener("click", () => {
    document.body.classList.remove("sidebar-collapsed");
    collapseBtn.textContent = "«";
    setTimeout(scrollToBottom, 120);
  });

  chatArea.addEventListener("DOMNodeInserted", () => {
    const threshold = 80;
    const atBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < threshold;
    if (atBottom) scrollToBottom();
  });

  input.focus();
});
