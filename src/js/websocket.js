/**
 * DLAS Hardened Realtime WebSocket Client
 * 
 * Invariants & Architecture:
 * - Realtime events are strictly PRESENTATIONAL NOTIFICATIONS and NEVER the source of truth.
 * - Authenticated WebSocket handshake using JWT token.
 * - Heartbeat keepalive with watchdog drop-detection.
 * - Exponential backoff with random jitter for resilient reconnection.
 * - In-memory event deduplication (seenEventIds) and sequence ordering (seq / timestamp).
 * - Missed-event recovery via /api/v1/events/since and authoritative server state reconciliation.
 */

class HardenedRealtimeClient {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 30000;
    this.baseDelay = 1000;
    this.reconnectTimer = null;
    this.pingInterval = null;
    this.watchdogTimer = null;
    this.lastPongReceived = Date.now();
    this.isManualClose = false;

    // Sequence and event tracking for deduplication and ordering
    this.lastEventSeq = 0;
    this.lastEventTimestamp = null;
    this.seenEventIds = new Set();
    this.maxSeenCache = 1000;

    // Recovery flag to avoid concurrent reconciliations
    this.isRecovering = false;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isManualClose = false;
    const store = window.dlasStore;
    const authToken = store.getState().authToken;

    // Build authenticated URL
    let wsUrl = window.DLAS_CONFIG.getWsUrl();
    if (authToken) {
      const sep = wsUrl.includes("?") ? "&" : "?";
      wsUrl = `${wsUrl}${sep}token=${encodeURIComponent(authToken)}`;
    }

    store.setWsStatus("reconnecting");

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = async () => {
        console.log("[DLAS Realtime] Connected to live WebSocket stream");
        this.reconnectAttempts = 0;
        this.lastPongReceived = Date.now();
        store.setWsStatus("connected");

        this.startHeartbeat();

        // On successful (re)connection:
        // 1. Recover any missed events
        // 2. Fetch current authoritative server state
        // 3. Reconcile differences
        // 4. Continue realtime updates
        await this.handleReconnectionReconciliation();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "pong") {
            this.lastPongReceived = Date.now();
            if (data.latest_seq && data.latest_seq > this.lastEventSeq) {
              // Server has emitted events we might not have received
              if (this.lastEventSeq > 0 && data.latest_seq > this.lastEventSeq + 1) {
                this.recoverMissedEvents(this.lastEventSeq);
              }
            }
            return;
          }
          this.handleIncomingEnvelope(data);
        } catch (err) {
          console.error("[DLAS Realtime] Failed to parse message:", err);
        }
      };

      this.ws.onclose = (event) => {
        this.stopHeartbeat();
        console.warn(`[DLAS Realtime] WebSocket closed (code: ${event.code})`);

        if (!this.isManualClose) {
          store.setWsStatus("reconnecting");
          this.scheduleReconnect();
        } else {
          store.setWsStatus("disconnected");
        }
      };

      this.ws.onerror = (err) => {
        console.warn("[DLAS Realtime] WebSocket stream error:", err);
      };
    } catch (err) {
      console.error("[DLAS Realtime] WebSocket connection exception:", err);
      store.setWsStatus("disconnected");
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
    this.lastPongReceived = Date.now();

    // Send ping every 15 seconds
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);

    // Watchdog timer: If no message or pong received within 30s, force reconnect
    this.watchdogTimer = setInterval(() => {
      if (Date.now() - this.lastPongReceived > 30000) {
        console.warn("[DLAS Realtime] Heartbeat watchdog timed out. Force closing stalled socket.");
        if (this.ws) {
          this.ws.close();
        }
      }
    }, 5000);
  }

  stopHeartbeat() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.watchdogTimer) {
      clearInterval(this.watchdogTimer);
      this.watchdogTimer = null;
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectAttempts += 1;

    // Exponential backoff with random jitter (prevents thundering herd):
    // 1s, 2s, 4s, 8s, up to max 30s + jitter
    const backoff = Math.min(this.baseDelay * Math.pow(1.6, this.reconnectAttempts), this.maxReconnectDelay);
    const jitter = Math.floor(Math.random() * 500);
    const delay = backoff + jitter;

    console.log(`[DLAS Realtime] Scheduling reconnect in ${delay}ms (attempt #${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  handleIncomingEnvelope(envelope) {
    if (!envelope || !envelope.event) return;

    const { event_id, seq, event, payload, timestamp } = envelope;

    // Duplicate-event protection
    if (event_id) {
      if (this.seenEventIds.has(event_id)) {
        console.log(`[DLAS Realtime] Duplicate event dropped: ${event_id}`);
        return;
      }
      this.seenEventIds.add(event_id);
      if (this.seenEventIds.size > this.maxSeenCache) {
        // Prune older entries
        const iterator = this.seenEventIds.values();
        this.seenEventIds.delete(iterator.next().value);
      }
    }

    // Sequence ordering check
    if (seq !== undefined && seq !== null) {
      if (this.lastEventSeq > 0) {
        if (seq <= this.lastEventSeq) {
          console.warn(`[DLAS Realtime] Out-of-order event dropped (seq ${seq} <= last ${this.lastEventSeq})`);
          return;
        }
        if (seq > this.lastEventSeq + 1) {
          console.warn(`[DLAS Realtime] Sequence gap detected (expected ${this.lastEventSeq + 1}, got ${seq}). Triggering recovery.`);
          this.recoverMissedEvents(this.lastEventSeq);
        }
      }
      this.lastEventSeq = seq;
    }

    if (timestamp) {
      this.lastEventTimestamp = timestamp;
    }

    this.processEvent(envelope);
  }

  /**
   * Process event to update UI presentation state.
   * CRITICAL INVARIANT: The event is an informative notification.
   * The backend REST API remains the authoritative source of truth.
   */
  processEvent(envelope) {
    const { event, payload } = envelope;
    const store = window.dlasStore;
    const currentLang = store.getState().language;

    console.log(`[DLAS Realtime] Processing validated event [${event}]:`, payload);

    switch (event) {
      case "CASE_CREATED":
        if (payload.case_id) {
          // Authoritative fetch of newly created case record
          window.dlasApi.getCaseDetail(payload.case_id)
            .then((authoritativeCase) => {
              store.updateSingleCase(authoritativeCase);
              this.showToast(
                currentLang === "bn"
                  ? `নতুন মামলা নিবন্ধিত হয়েছে: ${authoritativeCase.tracking_id}`
                  : `New legal aid matter registered: ${authoritativeCase.tracking_id}`,
                "info"
              );
            })
            .catch(() => this.synchronizeState());
        }
        break;

      case "CASE_UPDATED":
      case "CASE_STATUS_CHANGED":
      case "CASE_VERIFIED":
      case "CASE_RETURNED":
      case "CASE_PRIORITY_CHANGED":
      case "CASE_ASSIGNED":
      case "CASE_ARCHIVED":
        if (payload.case_id) {
          // Authoritative fetch of updated case entity
          window.dlasApi.getCaseDetail(payload.case_id)
            .then((authoritativeCase) => {
              store.updateSingleCase(authoritativeCase);

              const tKey = `status_${authoritativeCase.status}`;
              const statusLabel = window.TRANSLATIONS[currentLang][tKey] || authoritativeCase.status;

              let toastMsg = "";
              if (event === "CASE_VERIFIED") {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: কর্মকর্তা কর্তৃক যাচাইকৃত ও অনুমোদিত`
                  : `${authoritativeCase.tracking_id}: Verified & routed to Lawyer Queue`;
              } else if (event === "CASE_RETURNED") {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: অতিরিক্ত তথ্য তলব করা হয়েছে`
                  : `${authoritativeCase.tracking_id}: Returned for additional documents`;
              } else if (event === "CASE_PRIORITY_CHANGED") {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: অগ্রাধিকার পরিবর্তন → ${authoritativeCase.priority}`
                  : `${authoritativeCase.tracking_id}: Priority changed → ${authoritativeCase.priority}`;
              } else if (event === "CASE_ASSIGNED") {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: প্যানেল আইনজীবী নিযুক্ত করা হয়েছে`
                  : `${authoritativeCase.tracking_id}: Assigned to Panel Advocate`;
              } else if (event === "CASE_ARCHIVED") {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: নথিভুক্ত ও সংরক্ষিত করা হয়েছে`
                  : `${authoritativeCase.tracking_id}: Matter archived`;
              } else {
                toastMsg = currentLang === "bn"
                  ? `${authoritativeCase.tracking_id}: অবস্থা পরিবর্তিত হয়েছে → ${statusLabel}`
                  : `${authoritativeCase.tracking_id}: Status updated → ${statusLabel}`;
              }

              this.showToast(toastMsg, event === "CASE_RETURNED" ? "warning" : "success");
            })
            .catch(() => this.synchronizeState());
        }
        break;

      case "LAWYER_NOTIFICATION_CREATED":
      case "NOTIFICATION_DISPATCHED":
        // Fetch latest authoritative notifications from server
        window.dlasApi.listNotifications()
          .then((notifs) => {
            store.setNotifications(notifs);
            if (payload.title) {
              this.showToast(payload.title, "warning");
            }
          })
          .catch(() => {});
        break;

      default:
        break;
    }
  }

  /**
   * Missed-event recovery protocol:
   * Requests missed events from server circular buffer.
   * If server buffer has overflowed (reset_required), performs full authoritative state sync.
   */
  async recoverMissedEvents(sinceSeq) {
    if (this.isRecovering) return;
    this.isRecovering = true;

    try {
      console.log(`[DLAS Realtime] Recovering missed events since seq: ${sinceSeq}`);
      const res = await window.dlasApi.getEventsSince(sinceSeq);

      if (res.reset_required) {
        console.warn("[DLAS Realtime] Event buffer overflowed on server. Triggering authoritative refresh.");
        await this.synchronizeState();
      } else if (res.events && res.events.length > 0) {
        console.log(`[DLAS Realtime] Replaying ${res.events.length} missed events in sequence`);
        for (const evt of res.events) {
          this.handleIncomingEnvelope(evt);
        }
      }

      if (res.latest_seq) {
        this.lastEventSeq = Math.max(this.lastEventSeq, res.latest_seq);
      }
    } catch (err) {
      console.warn("[DLAS Realtime] Missed event recovery failed, falling back to full state sync:", err);
      await this.synchronizeState();
    } finally {
      this.isRecovering = false;
    }
  }

  /**
   * Reconnection Protocol:
   * 1. Reconnect WebSocket
   * 2. Fetch current server state
   * 3. Reconcile differences
   * 4. Continue realtime updates
   */
  async handleReconnectionReconciliation() {
    if (this.lastEventSeq > 0) {
      await this.recoverMissedEvents(this.lastEventSeq);
    }
    await this.synchronizeState();
  }

  /**
   * Authoritative server state fetch and reconciliation.
   */
  async synchronizeState() {
    try {
      const store = window.dlasStore;
      const state = store.getState();
      if (!state.authToken) return;

      console.log("[DLAS Realtime] Reconciling authoritative state with backend database...");

      // 1. Fetch case list according to active user filter
      const casesRes = await window.dlasApi.listCases(state.casesFilter);
      store.setCases(casesRes.items, casesRes.total, casesRes.page);

      // 2. Fetch notifications
      const notifs = await window.dlasApi.listNotifications();
      store.setNotifications(notifs);

      // 3. If currently viewing a specific case detail, refresh it authoritatively
      if (state.activeView === "detail" && state.selectedCaseId) {
        const refreshedCase = await window.dlasApi.getCaseDetail(state.selectedCaseId);
        store.setSelectedCase(refreshedCase);
      }

      console.log("[DLAS Realtime] Authoritative state reconciliation complete.");
    } catch (err) {
      console.warn("[DLAS Realtime] Authoritative state reconciliation warning:", err);
    }
  }

  showToast(message, type = "info") {
    if (window.showToastMessage) {
      window.showToastMessage(message, type);
    }
  }
}

window.dlasRealtime = new HardenedRealtimeClient();
