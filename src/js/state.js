/**
 * DLAS Reactive State Store
 * Centralizes application data, navigation, authentication, and live metrics.
 */
class StateStore {
  constructor() {
    this.state = {
      // Language: defaults to Bangla ('bn') or saved user preference
      language: localStorage.getItem("dlas_lang") || "bn",

      // Authentication
      authToken: localStorage.getItem("dlas_jwt_token") || null,
      currentUser: JSON.parse(localStorage.getItem("dlas_user") || "null"),

      // Navigation
      activeView: localStorage.getItem("dlas_jwt_token") ? "dashboard" : "login",
      selectedCaseId: null,

      // Data Collections
      cases: [],
      casesTotal: 0,
      casesPage: 1,
      casesFilter: {
        status: "",
        priority: "",
        category: "",
        district: "",
        search: "",
      },

      selectedCase: null,
      lawyers: [],
      auditLogs: [],
      notifications: [],
      unreadCount: 0,

      // High-level KPI metrics computed from live backend data
      metrics: {
        total: 0,
        pendingReview: 0,
        verified: 0,
        urgent: 0,
        lawyerQueue: 0,
      },

      // Telemetry & WebSocket
      wsStatus: "disconnected",
      backendHealth: null,
    };

    this.subscribers = new Set();
  }

  getState() {
    return this.state;
  }

  setLanguage(lang) {
    if (this.state.language === lang) return;
    this.state.language = lang;
    localStorage.setItem("dlas_lang", lang);
    document.documentElement.lang = lang;
    this.notify("language", lang);
  }

  setAuth(token, user) {
    this.state.authToken = token;
    this.state.currentUser = user;
    if (token) {
      localStorage.setItem("dlas_jwt_token", token);
      localStorage.setItem("dlas_user", JSON.stringify(user));
      this.setView("dashboard");
    } else {
      localStorage.removeItem("dlas_jwt_token");
      localStorage.removeItem("dlas_user");
      this.setView("login");
    }
    this.notify("auth", { token, user });
  }

  logout() {
    this.setAuth(null, null);
  }

  setView(viewName, caseId = null) {
    this.state.activeView = viewName;
    if (caseId !== null) {
      this.state.selectedCaseId = caseId;
    }
    this.notify("view", { viewName, caseId });
  }

  setCases(cases, total, page = 1) {
    this.state.cases = cases;
    this.state.casesTotal = total;
    this.state.casesPage = page;
    this.calculateMetrics();
    this.notify("cases", { cases, total, page });
  }

  updateSingleCase(updatedCase) {
    const idx = this.state.cases.findIndex((c) => c.id === updatedCase.id);
    if (idx >= 0) {
      this.state.cases[idx] = { ...this.state.cases[idx], ...updatedCase };
    } else {
      this.state.cases.unshift(updatedCase);
      this.state.casesTotal += 1;
    }

    if (this.state.selectedCase && this.state.selectedCase.id === updatedCase.id) {
      this.state.selectedCase = { ...this.state.selectedCase, ...updatedCase };
    }

    this.calculateMetrics();
    this.notify("case_updated", updatedCase);
  }

  setSelectedCase(caseItem) {
    this.state.selectedCase = caseItem;
    if (caseItem) {
      this.state.selectedCaseId = caseItem.id;
    }
    this.notify("selected_case", caseItem);
  }

  setLawyers(lawyers) {
    this.state.lawyers = lawyers;
    this.notify("lawyers", lawyers);
  }

  setAuditLogs(logs) {
    this.state.auditLogs = logs;
    this.notify("audit_logs", logs);
  }

  setNotifications(notifications) {
    this.state.notifications = notifications;
    this.state.unreadCount = notifications.filter((n) => !n.is_read).length;
    this.notify("notifications", notifications);
  }

  addNotification(notif) {
    this.state.notifications.unshift(notif);
    this.state.unreadCount += 1;
    this.notify("notification_added", notif);
  }

  setWsStatus(status) {
    this.state.wsStatus = status;
    this.notify("ws_status", status);
  }

  setBackendHealth(health) {
    this.state.backendHealth = health;
    this.notify("health", health);
  }

  calculateMetrics() {
    const list = this.state.cases;
    this.state.metrics = {
      total: this.state.casesTotal || list.length,
      pendingReview: list.filter((c) => c.status === "PENDING_HUMAN_REVIEW").length,
      verified: list.filter((c) => c.status === "VERIFIED").length,
      urgent: list.filter((c) => c.priority === "HIGH" || c.priority === "EMERGENCY").length,
      lawyerQueue: list.filter((c) => c.status === "PANEL_LAWYER_QUEUE").length,
    };
    this.notify("metrics", this.state.metrics);
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notify(event, data) {
    for (const callback of this.subscribers) {
      try {
        callback(event, data, this.state);
      } catch (err) {
        console.error("Subscriber notification error:", err);
      }
    }
  }
}

window.dlasStore = new StateStore();
