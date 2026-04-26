/**
 * content.js — HerSafe AI Content Script
 *
 * Injected into Instagram, Twitter/X, and WhatsApp Web.
 * Scans incoming messages and overlays threat badges in real-time.
 */

const API_URL = "http://localhost:5000/analyze";
const SCAN_INTERVAL_MS = 2500;

// Track already-scanned messages to avoid re-scanning
const scanned = new WeakSet();

// ── Platform selectors ─────────────────────────────────────────────────────────
// Each platform has different DOM structures for message bubbles.
function getMessageElements() {
  const host = location.hostname;

  if (host.includes("instagram.com")) {
    return document.querySelectorAll(
      'div[role="row"] span, div[class*="message"] span'
    );
  }
  if (host.includes("twitter.com") || host.includes("x.com")) {
    return document.querySelectorAll(
      'div[data-testid="messageEntry"] span, ' +
      'div[data-testid="tweetText"]'
    );
  }
  if (host.includes("whatsapp.com")) {
    return document.querySelectorAll(
      '[data-pre-plain-text] span'
    );
  }
  return [];
}

// ── Analyze a single message element ──────────────────────────────────────────
async function analyzeElement(el) {
  if (scanned.has(el)) return;
  const text = el.innerText?.trim();
  if (!text || text.length < 5) return;

  scanned.add(el);

  let result;
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    result = await res.json();
  } catch {
    // Backend offline — run local fallback
    result = localAnalysis(text);
  }

  if (result.category === "Safe") return;

  injectBadge(el, result);
  if (result.category === "Dangerous") sendNotification(text, result);
}

// ── Inject threat badge next to message ───────────────────────────────────────
function injectBadge(el, result) {
  // Avoid double-injecting
  if (el.parentElement?.querySelector(".hs-badge")) return;

  const { category, severity_score } = result;
  const colors = {
    Suspicious: { bg: "#FAEEDA", text: "#854F0B", dot: "#BA7517" },
    Dangerous:  { bg: "#FCEBEB", text: "#A32D2D", dot: "#E24B4A" },
  };
  const c = colors[category] || colors["Suspicious"];

  const badge = document.createElement("span");
  badge.className = "hs-badge";
  badge.dataset.category = category;
  badge.dataset.score = severity_score;
  badge.title = `HerSafe AI: ${category} (${severity_score}% severity)\n${result.alert}`;
  badge.innerHTML = `
    <span class="hs-dot"></span>
    <span class="hs-label">${category}</span>
    <span class="hs-score">${severity_score}%</span>
  `;
  badge.style.cssText = `
    display:inline-flex;align-items:center;gap:4px;
    background:${c.bg};color:${c.text};
    border:1px solid ${c.dot}60;
    border-radius:20px;padding:2px 8px;
    font-size:11px;font-weight:600;
    margin-left:8px;cursor:pointer;
    vertical-align:middle;white-space:nowrap;
    font-family:'Helvetica Neue',Arial,sans-serif;
  `;
  badge.querySelector(".hs-dot").style.cssText = `
    width:6px;height:6px;border-radius:50%;
    background:${c.dot};flex-shrink:0;
  `;

  // Click badge to open full report in popup
  badge.addEventListener("click", (e) => {
    e.stopPropagation();
    chrome.runtime.sendMessage({
      type: "SHOW_DETAIL",
      data: { text: el.innerText, result },
    });
  });

  // Wrap parent to allow positioning
  const wrapper = el.parentElement || el;
  wrapper.style.position = "relative";
  el.insertAdjacentElement("afterend", badge);
}

// ── Desktop notification for Dangerous threats ─────────────────────────────────
function sendNotification(text, result) {
  chrome.runtime.sendMessage({
    type: "DANGEROUS_DETECTED",
    data: {
      text: text.substring(0, 100),
      score: result.severity_score,
      flags: result.flags,
    },
  });
}

// ── Polling scan loop ──────────────────────────────────────────────────────────
function scanAll() {
  const elements = getMessageElements();
  elements.forEach(analyzeElement);
}

// Run on load and on DOM changes (new messages arriving)
scanAll();
setInterval(scanAll, SCAN_INTERVAL_MS);

// MutationObserver for real-time new message detection
const observer = new MutationObserver(() => scanAll());
observer.observe(document.body, { childList: true, subtree: true });


// ── Local fallback analysis (no backend needed) ────────────────────────────────
const THREATS = ["kill","hurt","find you","know where you live","watch out",
  "regret","come after","destroy you","make you pay","track you","hunt you",
  "harm","stab","shoot","attack","end you","dead","beat you"];
const ABUSE   = ["stupid","worthless","idiot","moron","ugly","disgusting",
  "pathetic","loser","trash","garbage","nobody wants you","hate you"];
const HARASS  = ["always watching","following","won't leave you alone",
  "never escape","stalk","obsessed"];
const MANIP   = ["no one cares about you","you're nothing without me",
  "nobody else would","i own you"];

function localAnalysis(text) {
  const lower = text.toLowerCase();
  let score = 0; const flags = [];
  const th = THREATS.filter(w => lower.includes(w));
  const ab = ABUSE.filter(w => lower.includes(w));
  const ha = HARASS.filter(w => lower.includes(w));
  const ma = MANIP.filter(w => lower.includes(w));
  score += th.length*30 + ab.length*15 + ha.length*25 + ma.length*12;
  if (th.length) flags.push("Threatening language");
  if (ab.length) flags.push("Abusive language");
  if (ha.length) flags.push("Harassment pattern");
  if (ma.length) flags.push("Manipulation tactic");
  score = Math.min(score, 100);
  const category = score >= 60 ? "Dangerous" : score >= 20 ? "Suspicious" : "Safe";
  const alerts = {
    Safe: "No threat detected.",
    Suspicious: "⚠️ Potentially harmful content detected.",
    Dangerous: "⛔ Serious threat indicators detected."
  };
  return { category, severity_score: score, alert: alerts[category], flags };
}
