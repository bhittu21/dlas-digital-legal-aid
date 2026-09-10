/**
 * DLAS Realtime WebSocket Client
 * Manages live connection, heartbeat keepalive, reconnect backoff, and event dispatch.
 */
class RealtimeClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 30000;
    this.reconnectTimer = null;
    this.pingInterval = null;
    this.isManualClose = false;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isManualClose = false;
    const wsUrl = window.DLAS_CONFIG.getWsUrl();
    window.dlasStore.setWsStatus("connecting");

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        window.dlasStore.setWsStatus("connected");
        this.startHeartbeat();

        // On successful reconnection, synchronize state via REST
        this.synchronizeState();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleEvent(data);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      this.ws.onclose = () => {
        this.stopHeartbeat();
        if (!this.isManualClose) {
          window.dlasStore.setWsStatus("reconnecting");
          this.scheduleReconnect();
        } else {
          window.dlasStore.setWsStatus("disconnected");
        }
      };

      this.ws.onerror = (err) => {
        console.warn("WebSocket stream notice:", err);
        // onclose will trigger next step
      };
    } catch (err) {
      console.error("WebSocket connection initiation error:", err);
      window.dlasStore.setWsStatus("disconnected");
      this.scheduleReconnect();
    }
  }

  disconnect() {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    window.dlasStore.setWsStatus("disconnected");
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 25000);
  }

  stopHeartbeat() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectAttempts += 1;
    // Exponential backoff with jitter: 1s, 2s, 4s, 8s, up to 30s
    const delay = Math.min(1000 * Math.pow(1.8, this.reconnectAttempts), this.maxReconnectDelay);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  handleEvent(envelope) {
    if (envelope.type === "pong") return;

    const { event, payload, actor, timestamp } = envelope;
    const store = window.dlasStore;
    const currentLang = store.getState().language;

    console.log(`[DLAS Realtime] Event: ${event}`, payload);

    switch (event) {
      case "CASE_CREATED":
        if (payload.case_id) {
          // Fetch full entity or construct lightweight representation
          window.dlasApi.getCaseDetail(payload.case_id)
            .then((fullCase) => {
              store.updateSingleCase(fullCase);
              this.showToast(
                currentLang === "bn"
                  ? `নতুন আবেদন জমা পড়েছে (${fullCase.tracking_id})`
                  : `New intake received (${fullCase.tracking_id})`,
                "info"
              );
            })
            .catch(() => {});
        }
        break;

      case "CASE_STATUS_CHANGED":
      case "CASE_PRIORITY_CHANGED":
      case "LAWYER_ASSIGNED":
      case "CASE_UPDATED":
      case "CASE_ARCHIVED":
        if (payload.case_id) {
          window.dlasApi.getCaseDetail(payload.case_id)
            .then((fullCase) => {
              store.updateSingleCase(fullCase);
              const tKey = `status_${fullCase.status}`;
              const statusName = window.TRANSLATIONS[currentLang][tKey] || fullCase.status;
              this.showToast(
                currentLang === "bn"
                  ? `${fullCase.tracking_id}: অবস্থা পরিবর্তিত হয়েছে → ${statusName}`
                  : `${fullCase.tracking_id}: Status updated → ${statusName}`,
                "success"
              );
            })
            .catch(() => {});
        }
        break;

      case "NOTIFICATION_DISPATCHED":
        store.addNotification(payload);
        this.showToast(payload.title, "warning");
        break;

      default:
        break;
    }
  }

  async synchronizeState() {
    try {
      const state = window.dlasStore.getState();
      if (!state.authToken) return;

      const casesRes = await window.dlasApi.listCases(state.casesFilter);
      window.dlasStore.setCases(casesRes.items, casesRes.total, casesRes.page);

      const notifs = await window.dlasApi.listNotifications();
      window.dlasStore.setNotifications(notifs);
    } catch (err) {
      console.warn("Realtime reconvergence sync error:", err);
    }
  }

  showToast(message, type = "info") {
    if (window.showToastMessage) {
      window.showToastMessage(message, type);
    }
  }
}

window.dlasRealtime = new RealtimeClient();
