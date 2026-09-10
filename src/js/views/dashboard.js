/**
 * DLAS Dashboard Overview View
 */
function renderDashboardView(container, lang) {
  const state = window.dlasStore.getState();
  const metrics = state.metrics;
  const user = state.currentUser || {};
  const cases = state.cases || [];

  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("nav_dashboard")}</h1>
        <p class="view-subtitle">
          ${user.full_name || "Official"} | 
          <span class="user-role-tag">${user.role === "dlao_officer" ? window.t("role_dlao") : user.role}</span>
          ${user.district ? `(${user.district})` : ""}
        </p>
      </div>
      <div class="view-actions">
        <button id="btnRefreshDashboard" class="btn btn-secondary btn-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 21h5v-5"/>
          </svg>
          ${lang === "bn" ? "রিফ্রেশ" : "Refresh"}
        </button>
        <button id="btnGoToQueue" class="btn btn-primary btn-sm">
          ${window.t("nav_queue")} →
        </button>
      </div>
    </div>

    <!-- Live KPI Metrics Cards -->
    <div class="kpi-grid">
      <div class="kpi-card kpi-total" id="kpiCardTotal">
        <div class="kpi-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">${window.t("kpi_total_cases")}</p>
          <h3 class="kpi-value">${window.formatNumber(metrics.total, lang)}</h3>
        </div>
      </div>

      <div class="kpi-card kpi-pending clickable-card" id="kpiCardPending">
        <div class="kpi-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">${window.t("kpi_pending_review")}</p>
          <h3 class="kpi-value highlight-warning">${window.formatNumber(metrics.pendingReview, lang)}</h3>
        </div>
      </div>

      <div class="kpi-card kpi-verified clickable-card" id="kpiCardVerified">
        <div class="kpi-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
          </svg>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">${window.t("kpi_verified")}</p>
          <h3 class="kpi-value highlight-success">${window.formatNumber(metrics.verified, lang)}</h3>
        </div>
      </div>

      <div class="kpi-card kpi-urgent clickable-card" id="kpiCardUrgent">
        <div class="kpi-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">${window.t("kpi_urgent")}</p>
          <h3 class="kpi-value highlight-danger">${window.formatNumber(metrics.urgent, lang)}</h3>
        </div>
      </div>

      <div class="kpi-card kpi-queue clickable-card" id="kpiCardLawyerQueue">
        <div class="kpi-icon-wrap">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <div class="kpi-body">
          <p class="kpi-label">${window.t("kpi_lawyer_queue")}</p>
          <h3 class="kpi-value highlight-primary">${window.formatNumber(metrics.lawyerQueue, lang)}</h3>
        </div>
      </div>
    </div>

    <!-- Quick Workflow Banner -->
    <div class="workflow-banner">
      <div class="banner-text">
        <h4>${window.t("quick_actions")}</h4>
        <p>
          ${lang === "bn" 
            ? "আইনগত সহায়তা প্রদান আইন ২০০০ এর অধীনে নাগরিকদের অধিকার সুরক্ষায় দ্রুত যাচাই ও আইনজীবী নিয়োগের ব্যবস্থা।" 
            : "Direct statutory workflow under Legal Aid Services Act 2000 for rapid merit review and counsel dispatch."}
        </p>
      </div>
      <div class="banner-buttons">
        <button id="btnQuickReview" class="btn btn-warning btn-sm">
          ${lang === "bn" ? "যাচাইকরণ কিউ খুলুন" : "Open Verification Queue"} (${window.formatNumber(metrics.pendingReview, lang)})
        </button>
        <button id="btnQuickDblaIntake" class="btn btn-emerald btn-sm">
          ${lang === "bn" ? "ডিবিএলএ আবেদন ও ডেমো প্রোভাইডার" : "DBLA Online Intake & Demo"} ↗
        </button>
        <button id="btnQuickLawyerDispatch" class="btn btn-primary btn-sm">
          ${lang === "bn" ? "আইনজীবী নিয়োগ তালিকা" : "Assign Panel Lawyers"} (${window.formatNumber(metrics.lawyerQueue, lang)})
        </button>
      </div>
    </div>

    <!-- Recent Authoritative Case Activity -->
    <div class="section-card">
      <div class="section-card-header">
        <div class="section-header-title">
          <h3>${window.t("kpi_latest_activity")}</h3>
          <span class="live-dot-wrap"><span class="pulse-dot"></span> Live Telemetry</span>
        </div>
        <button id="btnViewAllCases" class="btn btn-link btn-sm">
          ${lang === "bn" ? "সকল মামলা দেখুন" : "View All Matters"} →
        </button>
      </div>

      <div class="table-responsive">
        <table class="dlas-table">
          <thead>
            <tr>
              <th>${window.t("col_tracking_id")}</th>
              <th>${window.t("col_applicant")}</th>
              <th>${window.t("col_category")}</th>
              <th>${window.t("col_district")}</th>
              <th>${window.t("col_priority")}</th>
              <th>${window.t("col_status")}</th>
              <th>${window.t("col_action")}</th>
            </tr>
          </thead>
          <tbody>
            ${
              cases.length === 0
                ? `<tr><td colspan="7" class="text-center py-4">${window.t("no_cases_found")}</td></tr>`
                : cases.slice(0, 6).map((c) => `
                  <tr class="table-row-hover" data-id="${c.id}">
                    <td>
                      <span class="tracking-id-badge">${c.tracking_id}</span>
                    </td>
                    <td>
                      <div class="applicant-cell">
                        <strong>${c.applicant_name}</strong>
                        <span class="text-muted text-xs">${c.applicant_phone}</span>
                      </div>
                    </td>
                    <td>${window.getCategoryBadgeHtml(c.legal_category, lang)}</td>
                    <td>${c.district}${c.upazila ? `, ${c.upazila}` : ""}</td>
                    <td>${window.getPriorityBadgeHtml(c.priority, lang)}</td>
                    <td>${window.getStatusBadgeHtml(c.status, lang)}</td>
                    <td>
                      <button class="btn btn-secondary btn-xs btn-inspect-case" data-id="${c.id}">
                        ${window.t("btn_inspect")}
                      </button>
                    </td>
                  </tr>
                `).join("")
            }
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Attach event handlers
  container.querySelector("#btnRefreshDashboard").addEventListener("click", async () => {
    try {
      const res = await window.dlasApi.listCases();
      window.dlasStore.setCases(res.items, res.total, res.page);
    } catch (_) {}
  });

  container.querySelector("#btnGoToQueue").addEventListener("click", () => {
    window.dlasStore.setView("queue");
  });

  container.querySelector("#btnViewAllCases").addEventListener("click", () => {
    window.dlasStore.setView("queue");
  });

  // KPI card jumps
  container.querySelector("#kpiCardPending").addEventListener("click", () => {
    window.dlasStore.state.casesFilter.status = "PENDING_HUMAN_REVIEW";
    window.dlasStore.setView("queue");
  });

  container.querySelector("#btnQuickReview").addEventListener("click", () => {
    window.dlasStore.state.casesFilter.status = "PENDING_HUMAN_REVIEW";
    window.dlasStore.setView("queue");
  });

  container.querySelector("#kpiCardVerified").addEventListener("click", () => {
    window.dlasStore.state.casesFilter.status = "VERIFIED";
    window.dlasStore.setView("queue");
  });

  container.querySelector("#kpiCardUrgent").addEventListener("click", () => {
    window.dlasStore.state.casesFilter.priority = "HIGH";
    window.dlasStore.setView("queue");
  });

  container.querySelector("#kpiCardLawyerQueue").addEventListener("click", () => {
    window.dlasStore.setView("lawyers");
  });

  container.querySelector("#btnQuickLawyerDispatch").addEventListener("click", () => {
    window.dlasStore.setView("lawyers");
  });

  container.querySelector("#btnQuickDblaIntake")?.addEventListener("click", () => {
    window.dlasStore.setView("dbla_intake");
  });

  // Row inspections
  container.querySelectorAll(".btn-inspect-case").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const caseId = parseInt(btn.dataset.id, 10);
      window.dlasStore.setView("detail", caseId);
    });
  });

  container.querySelectorAll(".table-row-hover").forEach((row) => {
    row.addEventListener("click", () => {
      const caseId = parseInt(row.dataset.id, 10);
      window.dlasStore.setView("detail", caseId);
    });
  });
}

window.renderDashboardView = renderDashboardView;
