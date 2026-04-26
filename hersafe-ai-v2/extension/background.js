/**
 * background.js — HerSafe AI Service Worker
 * Handles notifications and message passing from content script.
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log("HerSafe AI extension installed.");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  // ── Dangerous threat desktop notification ──────────────────────────────────
  if (message.type === "DANGEROUS_DETECTED") {
    const { text, score, flags } = message.data;
    chrome.notifications.create({
      type:     "basic",
      iconUrl:  "icons/icon48.png",
      title:    "⛔ HerSafe AI: Dangerous Message Detected",
      message:  `Severity: ${score}% | ${flags.slice(0,2).join(", ")}\n"${text.substring(0,80)}..."`,
      priority: 2,
    });
  }

  // ── Open detail view in popup ──────────────────────────────────────────────
  if (message.type === "SHOW_DETAIL") {
    // Store result so popup can read it
    chrome.storage.local.set({ lastDetail: message.data });
    // Open popup (focuses existing if already open)
    chrome.action.openPopup?.();
  }

  return true;
});
