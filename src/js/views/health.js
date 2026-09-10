/**
 * DLAS System Diagnostics & Telemetry View
 */
async function renderHealthView(container, lang) {
  const wsStatus = window.dlasStore.getState().wsStatus;

  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("health_title")}</h1>
        <p class="view-subtitle">${lang === "bn" ? "সার্ভার, ডাটাবেজ এবং ওয়েবসকেট সংযোগের লাইভ স্ট্যাটাস মনিটর।" : "Real-time service telemetry, database integrity, and WebSocket connection monitor."}</p>
      </div>
      <div class="view-actions">
        <button id="btnRefreshHealth" class="btn btn-primary btn-sm">
          ${window.t("btn_recheck_health")}
        </button>
      </div>
    </div>

    <div class="health-grid">
      <!-- Backend FastAPI Diagnostic Card -->
      <div class="health-card" id="cardBackendHealth">
        <div class="health-card-header">
          <div class="health-indicator-circle circle-pending" id="circleBackend"></div>
          <h4>${window.t("backend_status")}</h4>
        </div>
        <div class="health-card-body" id="bodyBackendHealth">
          <p class="text-muted">${lang === "bn" ? "পরীক্ষা করা হচ্ছে..." : "Pinging service..."}</p>
        </div>
      </div>

      <!-- Authoritative Persistent Database Card -->
      <div class="health-card" id="cardDbHealth">
        <div class="health-card-header">
          <div class="health-indicator-circle circle-pending" id="circleDb"></div>
          <h4>${window.t("db_status")}</h4>
        </div>
        <div class="health-card-body" id="bodyDbHealth">
          <p class="text-muted">${lang === "bn" ? "পরীক্ষা করা হচ্ছে..." : "Checking ACID connection..."}</p>
        </div>
      </div>

      <!-- Realtime WebSocket Stream Card -->
      <div class="health-card" id="cardWsHealth">
        <div class="health-card-header">
          <div class="health-indicator-circle ${wsStatus === 'connected' ? 'circle-success' : 'circle-warning'}" id="circleWs"></div>
          <h4>${window.t("ws_status")}</h4>
        </div>
        <div class="health-card-body">
          <p class="health-status-text">
            ${
              wsStatus === "connected"
                ? window.t("ws_connected")
                : wsStatus === "reconnecting"
                ? window.t("ws_reconnecting")
                : window.t("ws_disconnected")
            }
          </p>
          <div class="text-xs text-muted mt-2">
            <strong>Endpoint:</strong> <code>${window.DLAS_CONFIG.getWsUrl()}</code>
          </div>
        </div>
      </div>
    </div>

    <!-- Diagnostic Details & Benchmarking -->
    <div class="section-card mt-4">
      <h4 class="section-card-title">${lang === "bn" ? "সিস্টেম টেলিমেট্রি স্পেসিফিকেশন" : "System Telemetry Metrics"}</h4>
      <div class="profile-item">
        <span class="profile-label">API Gateway Latency:</span>
        <span class="profile-value" id="valApiLatency">—</span>
      </div>
      <div class="profile-item">
        <span class="profile-label">Authoritative Engine:</span>
        <span class="profile-value">FastAPI + SQLAlchemy Core</span>
      </div>
      <div class="profile-item">
        <span class="profile-label">AI Intake Engine:</span>
        <span class="profile-value">Google Gemini 2.0 Flash (Backend Isolated)</span>
      </div>
      <div class="profile-item">
        <span class="profile-label">Telephony Gateway:</span>
        <span class="profile-value">Twilio Voice Webhook (Bangla bn-BD Neural)</span>
      </div>
      <div class="profile-item">
        <span class="profile-label">Human Verification Gate:</span>
        <span class="profile-value"><strong class="highlight-success">Active & Enforced (HTTP 403 AI Lock)</strong></span>
      </div>
    </div>
  `;

  const runHealthCheck = async () => {
    const t0 = performance.now();
    try {
      const data = await window.dlasApi.getHealth();
      const latency = Math.round(performance.now() - t0);

      container.querySelector("#valApiLatency").textContent = `${latency} ms`;

      // Update backend card
      const circleBackend = container.querySelector("#circleBackend");
      circleBackend.className = "health-indicator-circle circle-success";
      container.querySelector("#bodyBackendHealth").innerHTML = `
        <p class="health-status-text highlight-success">Operating Normally (200 OK)</p>
        <div class="text-xs text-muted mt-1">Environment: <code>${data.environment}</code></div>
        <div class="text-xs text-muted">Latency: ${latency} ms</div>
      `;

      // Update DB card
      const circleDb = container.querySelector("#circleDb");
      if (data.database === "healthy") {
        circleDb.className = "health-indicator-circle circle-success";
        container.querySelector("#bodyDbHealth").innerHTML = `
          <p class="health-status-text highlight-success">ACID Store Healthy</p>
          <div class="text-xs text-muted mt-1">Status: Persistent SQL Transaction Engine Active</div>
        `;
      } else {
        circleDb.className = "health-indicator-circle circle-danger";
        container.querySelector("#bodyDbHealth").innerHTML = `
          <p class="health-status-text highlight-danger">Degraded</p>
          <div class="text-xs text-muted">${data.database}</div>
        `;
      }
    } catch (err) {
      const circleBackend = container.querySelector("#circleBackend");
      circleBackend.className = "health-indicator-circle circle-danger";
      container.querySelector("#bodyBackendHealth").innerHTML = `
        <p class="health-status-text highlight-danger">Connection Failed</p>
        <div class="text-xs text-muted">${err.message}</div>
      `;
    }
  };

  await runHealthCheck();
  container.querySelector("#btnRefreshHealth").addEventListener("click", runHealthCheck);
}

window.renderHealthView = renderHealthView;
