/**
 * DLAS Main Application Controller
 * Manages view routing, header rendering, language toggling, and toast alerts.
 */

function showToastMessage(message, type = "info") {
  let toastContainer = document.getElementById("toastContainer");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toastContainer";
    toastContainer.className = "toast-container";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-body">
      <span>${message}</span>
    </div>
  `;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast-fadeout");
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}
window.showToastMessage = showToastMessage;

function renderAppLayout() {
  const appRoot = document.getElementById("appRoot");
  const state = window.dlasStore.getState();
  const lang = state.language;
  const user = state.currentUser;
  const isAuth = !!state.authToken;

  if (!isAuth) {
    appRoot.innerHTML = `
      <div id="loginViewContainer"></div>
      <div id="modalContainer" style="display: none;"></div>
    `;
    window.renderLoginView(document.getElementById("loginViewContainer"), lang);
    return;
  }

  appRoot.innerHTML = `
    <div class="app-layout">
      <!-- Top Primary Government Header -->
      <header class="app-header">
        <div class="header-left">
          <div class="header-emblem">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke="#047857"/>
              <path d="m9 12 2 2 4-4" stroke="#047857"/>
              <circle cx="12" cy="12" r="3" fill="#b45309"/>
            </svg>
          </div>
          <div class="header-title-block">
            <h1 class="header-title">${window.t("app_title")}</h1>
            <span class="header-sub text-xs">${window.t("tagline")}</span>
          </div>
        </div>

        <div class="header-right">
          <!-- Realtime WebSocket Live Status Indicator -->
          <div class="ws-indicator-pill" id="wsIndicatorPill" title="WebSocket Live Stream Status">
            <span class="live-dot" id="wsDot"></span>
            <span class="ws-text" id="wsText">Live</span>
          </div>

          <!-- Prominent Bangladesh Standard Language Toggle (EN | বাংলা) -->
          <div class="lang-switch-box" id="langSwitchBox">
            <button type="button" class="lang-btn ${lang === 'bn' ? 'lang-btn-active' : ''}" id="btnLangBn">বাংলা</button>
            <span class="lang-sep">|</span>
            <button type="button" class="lang-btn ${lang === 'en' ? 'lang-btn-active' : ''}" id="btnLangEn">EN</button>
          </div>

          <!-- Notification Bell -->
          <button type="button" class="btn-icon-header" id="btnHeaderNotifs" title="Notifications">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span class="notification-count-badge" id="headerNotifBadge" style="${state.unreadCount > 0 ? '' : 'display: none;'}">
              ${window.formatNumber(state.unreadCount, lang)}
            </span>
          </button>

          <!-- User Profile & Sign Out -->
          <div class="user-profile-menu">
            <div class="user-avatar-circle">
              ${user.full_name ? user.full_name.charAt(0).toUpperCase() : "O"}
            </div>
            <div class="user-info-text">
              <span class="user-name">${user.full_name || "Official"}</span>
              <span class="user-role">${user.role === 'dlao_officer' ? window.t('role_dlao') : user.role}</span>
            </div>
            <button id="btnHeaderLogout" class="btn btn-outline-danger btn-xs" title="Logout">
              ${window.t("nav_logout")}
            </button>
          </div>
        </div>
      </header>

      <!-- Sub-Navigation Bar -->
      <nav class="sub-nav">
        <div class="nav-links-wrap">
          <button class="nav-item ${state.activeView === 'dashboard' ? 'nav-item-active' : ''}" data-view="dashboard">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect width="7" height="9" x="3" y="3" rx="1"/>
              <rect width="7" height="5" x="14" y="3" rx="1"/>
              <rect width="7" height="9" x="14" y="12" rx="1"/>
              <rect width="7" height="5" x="3" y="16" rx="1"/>
            </svg>
            ${window.t("nav_dashboard")}
          </button>

          <button class="nav-item ${state.activeView === 'queue' ? 'nav-item-active' : ''}" data-view="queue">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            ${window.t("nav_queue")}
          </button>

          <button class="nav-item ${state.activeView === 'lawyers' ? 'nav-item-active' : ''}" data-view="lawyers">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            ${window.t("nav_lawyer_queue")}
          </button>

          <button class="nav-item ${state.activeView === 'audit' ? 'nav-item-active' : ''}" data-view="audit">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>
            </svg>
            ${window.t("nav_audit")}
          </button>

          <button class="nav-item ${state.activeView === 'health' ? 'nav-item-active' : ''}" data-view="health">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            ${window.t("nav_health")}
          </button>

          <button class="nav-item ${state.activeView === 'notifications' ? 'nav-item-active' : ''}" data-view="notifications">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            ${window.t("nav_notifications")}
          </button>

          <button class="nav-item ${state.activeView === 'settings' ? 'nav-item-active' : ''}" data-view="settings">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            ${window.t("nav_settings")}
          </button>
        </div>
      </nav>

      <!-- Main Dynamic Content Container -->
      <main class="main-container" id="mainContent"></main>

      <!-- Modal Container -->
      <div id="modalContainer" style="display: none;"></div>
    </div>
  `;

  // Attach Top Header Listeners
  document.getElementById("btnLangBn").addEventListener("click", () => {
    window.dlasStore.setLanguage("bn");
  });

  document.getElementById("btnLangEn").addEventListener("click", () => {
    window.dlasStore.setLanguage("en");
  });

  document.getElementById("btnHeaderNotifs").addEventListener("click", () => {
    window.dlasStore.setView("notifications");
  });

  document.getElementById("btnHeaderLogout").addEventListener("click", () => {
    window.dlasRealtime.disconnect();
    window.dlasStore.logout();
  });

  // Attach Navigation Listeners
  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetView = btn.dataset.view;
      window.dlasStore.setView(targetView);
    });
  });

  // Render current view
  renderCurrentView();
  updateWsStatusIndicator(window.dlasStore.getState().wsStatus);
}

function renderCurrentView() {
  const mainContent = document.getElementById("mainContent");
  if (!mainContent) return;

  const state = window.dlasStore.getState();
  const view = state.activeView;
  const lang = state.language;

  // Highlight active nav button
  document.querySelectorAll(".nav-item").forEach((btn) => {
    if (btn.dataset.view === view) {
      btn.classList.add("nav-item-active");
    } else {
      btn.classList.remove("nav-item-active");
    }
  });

  switch (view) {
    case "dashboard":
      window.renderDashboardView(mainContent, lang);
      break;
    case "queue":
      window.renderCaseQueueView(mainContent, lang);
      break;
    case "detail":
      window.renderCaseDetailView(mainContent, lang);
      break;
    case "lawyers":
      window.renderLawyerQueueView(mainContent, lang);
      break;
    case "audit":
      window.renderAuditLogsView(mainContent, lang);
      break;
    case "health":
      window.renderHealthView(mainContent, lang);
      break;
    case "notifications":
      window.renderNotificationsView(mainContent, lang);
      break;
    case "settings":
      window.renderSettingsView(mainContent, lang);
      break;
    case "login":
      renderAppLayout();
      break;
    default:
      window.renderDashboardView(mainContent, lang);
      break;
  }
}

function updateWsStatusIndicator(status) {
  const dot = document.getElementById("wsDot");
  const text = document.getElementById("wsText");
  if (!dot || !text) return;

  const lang = window.dlasStore.getState().language;

  if (status === "connected") {
    dot.className = "live-dot dot-connected";
    text.textContent = lang === "bn" ? "লাইভ" : "Live";
  } else if (status === "reconnecting") {
    dot.className = "live-dot dot-reconnecting";
    text.textContent = lang === "bn" ? "পুনঃসংযোগ..." : "Reconnecting...";
  } else {
    dot.className = "live-dot dot-disconnected";
    text.textContent = lang === "bn" ? "বিচ্ছিন্ন" : "Offline";
  }
}

// Subscribe to state changes for seamless reactive updates
window.dlasStore.subscribe((event, data, state) => {
  if (event === "language") {
    // Re-render whole layout to translate navigation and active view instantly without reload
    renderAppLayout();
  } else if (event === "view" || event === "auth") {
    renderAppLayout();
  } else if (event === "case_updated" || event === "metrics") {
    // If on dashboard or queue, update view
    if (state.activeView === "dashboard" || state.activeView === "queue") {
      renderCurrentView();
    }
  } else if (event === "ws_status") {
    updateWsStatusIndicator(data);
  } else if (event === "notifications" || event === "notification_added") {
    const badge = document.getElementById("headerNotifBadge");
    if (badge) {
      if (state.unreadCount > 0) {
        badge.style.display = "inline-flex";
        badge.textContent = window.formatNumber(state.unreadCount, state.language);
      } else {
        badge.style.display = "none";
      }
    }
  }
});

// App Bootstrap on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  document.documentElement.lang = window.dlasStore.getState().language;
  renderAppLayout();

  // If authenticated, load initial dataset from authoritative backend
  if (window.dlasStore.getState().authToken) {
    try {
      const casesRes = await window.dlasApi.listCases();
      window.dlasStore.setCases(casesRes.items, casesRes.total, casesRes.page);

      const notifs = await window.dlasApi.listNotifications();
      window.dlasStore.setNotifications(notifs);

      // Connect WebSocket
      window.dlasRealtime.connect();
    } catch (err) {
      console.warn("Initial data load note:", err);
    }
  }
});
