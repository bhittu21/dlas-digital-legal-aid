/**
 * DLAS UI & Accessibility Utilities
 */

function t(key) {
  const lang = window.dlasStore ? window.dlasStore.getState().language : "bn";
  const dict = window.TRANSLATIONS[lang] || window.TRANSLATIONS.en;
  return dict[key] || window.TRANSLATIONS.en[key] || key;
}

function formatDate(dateStr, lang) {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;

  const day = d.getDate();
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");

  const enMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const bnMonths = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"];

  if (lang === "bn") {
    return `${window.toBanglaDigits(day)} ${bnMonths[d.getMonth()]} ${window.toBanglaDigits(year)}, ${window.toBanglaDigits(hours)}:${window.toBanglaDigits(minutes)}`;
  }
  return `${day} ${enMonths[d.getMonth()]} ${year}, ${hours}:${minutes}`;
}

function getStatusBadgeHtml(status, lang) {
  const tKey = `status_${status}`;
  const label = window.TRANSLATIONS[lang][tKey] || status;

  const statusClassMap = {
    NEW: "badge-new",
    AI_INTAKE: "badge-ai",
    PENDING_HUMAN_REVIEW: "badge-pending",
    VERIFIED: "badge-verified",
    PANEL_LAWYER_QUEUE: "badge-queue",
    LAWYER_REVIEW: "badge-lawyer",
    NEEDS_INFORMATION: "badge-info-needed",
    REJECTED: "badge-rejected",
    ARCHIVED: "badge-archived",
  };

  const badgeClass = statusClassMap[status] || "badge-default";
  return `<span class="badge ${badgeClass}"><span class="badge-dot"></span>${label}</span>`;
}

function getPriorityBadgeHtml(priority, lang) {
  const tKey = `prio_${priority}`;
  const label = window.TRANSLATIONS[lang][tKey] || priority;

  const prioClassMap = {
    LOW: "prio-low",
    MEDIUM: "prio-medium",
    HIGH: "prio-high",
    EMERGENCY: "prio-emergency",
  };

  const prioClass = prioClassMap[priority] || "prio-medium";
  return `<span class="prio-tag ${prioClass}">${label}</span>`;
}

function getCategoryBadgeHtml(cat, lang) {
  const tKey = `cat_${cat}`;
  const label = window.TRANSLATIONS[lang][tKey] || cat;
  return `<span class="cat-pill">${label}</span>`;
}

/**
 * Text-to-Speech synthesis for low-literacy or audio assistance
 */
function speakText(text) {
  if (!window.speechSynthesis) {
    alert("Speech synthesis is not supported on this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const lang = window.dlasStore.getState().language;
  utterance.lang = lang === "bn" ? "bn-BD" : "en-US";
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

/**
 * Web Audio API gentle chime for urgent updates
 */
function playEmergencyChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.35);
  } catch (_) {}
}

window.t = t;
window.formatDate = formatDate;
window.getStatusBadgeHtml = getStatusBadgeHtml;
window.getPriorityBadgeHtml = getPriorityBadgeHtml;
window.getCategoryBadgeHtml = getCategoryBadgeHtml;
window.speakText = speakText;
window.playEmergencyChime = playEmergencyChime;
