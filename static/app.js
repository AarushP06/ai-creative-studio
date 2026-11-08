// AI Creative Studio — browser code.
// The browser never sees the API key. It only talks to OUR server (/api/...),
// and our server talks to Gemini.

const $ = (id) => document.getElementById(id);

const CTA_ICONS = { book: "📅", contact: "✉️", visit: "📍" };

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => (toast.hidden = true), 4500);
}

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
  return res.json();
}

async function loadPage() {
  const [status, brief, sims] = await Promise.all([
    getJSON("/api/status"),
    getJSON("/api/brief"),
    getJSON("/api/simulations"),
  ]);

  const chip = $("mode-chip");
  chip.classList.add(status.mode);
  chip.textContent = status.mode === "live" ? `● Live · ${status.model}` : "● Mock mode";

  document.title = `${brief.name} · AI Creative Studio`;
  $("brand-name").textContent = brief.name;
  $("brand-mark").textContent = brief.name.trim().charAt(0).toUpperCase() || "★";
  $("brief-kicker").textContent = [brief.type, brief.city].filter(Boolean).join(" · ");
  $("brief-tagline").textContent = brief.tagline;

  const select = $("source-select");
  for (const name of sims.simulations) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = `Simulate: ${name.replaceAll("-", " ")}`;
    select.appendChild(opt);
  }
}

function renderCard(card, source) {
  $("empty-state")?.remove();
  const node = $("card-template").content.firstElementChild.cloneNode(true);
  node.querySelector(".source-badge").textContent = source === "live" ? "Live AI" : "Mock";
  node.querySelector(".source-badge").classList.add(source === "live" ? "live" : "mock");
  const img = node.querySelector(".card-img");
  img.src = `/static/img/${card.image}.svg`;
  img.alt = `${card.image} illustration`;
  node.querySelector(".tone-chip").textContent = card.tone;
  node.querySelector(".card-title").textContent = card.title;      // textContent, never innerHTML:
  node.querySelector(".card-summary").textContent = card.summary;  // model output is untrusted
  node.querySelector(".card-cta").textContent = `${CTA_ICONS[card.cta_action] || ""} ${card.cta_text}`;
  $("card-grid").prepend(node);
}

function renderTrace(data) {
  const trace = $("trace");
  trace.innerHTML = "";
  for (const step of data.trace || []) {
    const li = document.createElement("li");
    li.className = step.ok ? "ok" : "fail";
    li.textContent = step.step;
    if (step.detail) {
      const span = document.createElement("span");
      span.className = "detail";
      span.textContent = ` · ${step.detail}`;
      li.appendChild(span);
    }
    trace.appendChild(li);
  }

  const verdict = $("verdict");
  verdict.hidden = false;
  verdict.className = `verdict ${data.status}`;
  verdict.textContent = data.status === "accepted"
    ? `Accepted · source: ${data.source}`
    : `Rejected by the validator · source: ${data.source} — this card was NOT shown`;

  const list = $("violations");
  list.innerHTML = "";
  for (const v of data.violations || []) {
    const li = document.createElement("li");
    li.textContent = v;
    list.appendChild(li);
  }

  $("raw-box").hidden = !data.raw;
  $("raw-output").textContent = data.raw || "";
}

async function requestCard(body, button) {
  button.disabled = true;
  button.classList.add("loading");
  try {
    const res = await fetch("/api/service-card", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    renderTrace(data);
    if (data.status === "accepted" && data.card) renderCard(data.card, data.source);
    if (data.fallback?.card) renderCard(data.fallback.card, "mock");
    if (data.message) showToast(data.message);
    if (data.fallback?.message) showToast(data.fallback.message);
    if (data.status === "rejected" && data.source === "simulated") {
      showToast("Simulated bad response rejected — nothing reached the website.");
    }
  } catch (err) {
    showToast(`Request failed: ${err.message}. Is the server still running?`);
  } finally {
    button.disabled = false;
    button.classList.remove("loading");
  }
}

$("generate-btn").addEventListener("click", (e) =>
  requestCard({}, e.currentTarget));

$("lab-run-btn").addEventListener("click", (e) => {
  const simulate = $("source-select").value || null;
  const brief = $("injected-check").checked ? "injected" : "main";
  requestCard({ simulate, brief }, e.currentTarget);
});

// ---------- Plan your visit: the runtime agent (Architecture C) ----------
const TRACE_ICONS = { fallback: "⏭", question: "❓", instructions: "📄", model: "🤖", permission: "🛡", tool: "🔧", check: "✅" };

function renderAgent(data) {
  const box = $("ask-answer");
  box.hidden = false;
  $("ask-text").textContent = data.answer;                 // model output → textContent only
  const badge = $("ask-source");
  badge.textContent = data.source === "live" ? "Live agent" : "Mock agent";
  badge.className = `source-badge ${data.source === "live" ? "live" : "mock"}`;

  const list = $("ask-trace");
  list.innerHTML = "";
  for (const step of data.trace || []) {
    const li = document.createElement("li");
    li.className = step.kind === "fallback" ? "fallback" : step.ok ? "ok" : "fail";
    const icon = document.createElement("span");
    icon.className = "icon";
    icon.textContent = step.ok || step.kind !== "check" ? TRACE_ICONS[step.kind] || "•" : "⛔";
    const title = document.createElement("b");
    title.textContent = step.step;
    li.append(icon, title);
    if (step.detail) {
      const detail = document.createElement("code");
      detail.textContent = step.detail;
      li.appendChild(detail);
    }
    list.appendChild(li);
  }
}

async function ask(question) {
  question = question.trim();
  if (!question) return;
  const button = $("ask-btn");
  button.disabled = true;
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    renderAgent(await res.json());
  } catch (err) {
    showToast(`Question failed: ${err.message}. Is the server still running?`);
  } finally {
    button.disabled = false;
  }
}

$("ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  ask($("ask-input").value);
});
for (const chip of document.querySelectorAll("#ask-chips button")) {
  chip.addEventListener("click", () => {
    $("ask-input").value = chip.dataset.q;
    ask(chip.dataset.q);
  });
}

loadPage().catch((err) => showToast(`Could not load the page data: ${err.message}`));
