/**
 * DLAS Panel Lawyer Queue & Directory View
 */
async function renderLawyerQueueView(container, lang) {
  const state = window.dlasStore.getState();
  const user = state.currentUser || {};
  const isDLAO = user.role === "dlao_officer" || user.role === "admin";

  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("nav_lawyer_queue")}</h1>
        <p class="view-subtitle">
          ${lang === "bn" 
            ? "যাচাইকৃত মামলার তালিকা এবং প্যানেল আইনজীবীদের মামলা বণ্টন ও কার্যভার ব্যবস্থাপনা।" 
            : "Verified matters awaiting counsel appointment and panel lawyer workload management."}
        </p>
      </div>
      <div class="view-actions">
        <button id="btnRefreshLawyerQueue" class="btn btn-secondary btn-sm">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
            <path d="M3 3v5h5"/>
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
            <path d="M16 21h5v-5"/>
          </svg>
          ${lang === "bn" ? "রিফ্রেশ" : "Refresh"}
        </button>
      </div>
    </div>

    <div class="dual-pane-grid">
      <!-- Waiting Cases in PANEL_LAWYER_QUEUE -->
      <div class="pane-column">
        <div class="section-card">
          <div class="section-card-header">
            <h4>
              ${lang === "bn" ? "আইনজীবী অপেক্ষমাণ মামলাসমূহ" : "Matters Awaiting Panel Advocate"}
            </h4>
            <span class="badge badge-queue" id="badgeQueueCount">...</span>
          </div>

          <div class="table-responsive">
            <table class="dlas-table table-sm" id="tableQueueCases">
              <thead>
                <tr>
                  <th>${window.t("col_tracking_id")}</th>
                  <th>${window.t("col_applicant")}</th>
                  <th>${window.t("col_category")}</th>
                  <th>${window.t("col_priority")}</th>
                  <th>${window.t("col_action")}</th>
                </tr>
              </thead>
              <tbody id="queueCasesTbody">
                <tr><td colspan="5" class="text-center py-4 text-muted">${lang === "bn" ? "লোড হচ্ছে..." : "Loading queue..."}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Panel Lawyers Directory & Workload -->
      <div class="pane-column">
        <div class="section-card">
          <div class="section-card-header">
            <h4>
              ${lang === "bn" ? "তালিকাভুক্ত প্যানেল আইনজীবী ও বর্তমান কার্যভার" : "Panel Advocate Workload Directory"}
            </h4>
          </div>

          <div class="lawyers-grid" id="lawyersGridContainer">
            <div class="py-4 text-center text-muted">${lang === "bn" ? "আইনজীবীদের তথ্য লোড হচ্ছে..." : "Loading advocate directory..."}</div>
          </div>
        </div>
      </div>
    </div>
  `;

  const refreshData = async () => {
    try {
      // 1. Fetch cases in PANEL_LAWYER_QUEUE
      const queueCasesRes = await window.dlasApi.listCases({
        status: "PANEL_LAWYER_QUEUE",
        size: 50,
      });

      // 2. Fetch panel lawyers
      const lawyers = await window.dlasApi.listPanelLawyers();
      window.dlasStore.setLawyers(lawyers);

      // Render queue table
      const tbody = container.querySelector("#queueCasesTbody");
      const badgeCount = container.querySelector("#badgeQueueCount");
      badgeCount.textContent = window.formatNumber(queueCasesRes.items.length, lang);

      if (queueCasesRes.items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">${lang === "bn" ? "এই মুহূর্তে কোনো মামলা আইনজীবী অপেক্ষমাণ নেই।" : "No verified matters currently awaiting assignment."}</td></tr>`;
      } else {
        tbody.innerHTML = queueCasesRes.items.map((c) => `
          <tr class="table-row-hover" data-id="${c.id}">
            <td><span class="tracking-id-badge">${c.tracking_id}</span></td>
            <td>
              <strong>${c.applicant_name}</strong>
              <div class="text-xs text-muted">${c.district}</div>
            </td>
            <td>${window.getCategoryBadgeHtml(c.legal_category, lang)}</td>
            <td>${window.getPriorityBadgeHtml(c.priority, lang)}</td>
            <td>
              <div class="action-btn-group">
                <button class="btn btn-secondary btn-xs btn-inspect-queue" data-id="${c.id}">
                  ${window.t("btn_inspect")}
                </button>
                ${
                  isDLAO
                    ? `<button class="btn btn-primary btn-xs btn-assign-queue" data-id="${c.id}">
                        ${lang === "bn" ? "নিয়োগ" : "Assign"}
                      </button>`
                    : ""
                }
              </div>
            </td>
          </tr>
        `).join("");

        tbody.querySelectorAll(".btn-inspect-queue").forEach((btn) => {
          btn.addEventListener("click", (e) => {
            e.stopPropagation();
            window.dlasStore.setView("detail", parseInt(btn.dataset.id, 10));
          });
        });

        tbody.querySelectorAll(".btn-assign-queue").forEach((btn) => {
          btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const caseId = parseInt(btn.dataset.id, 10);
            const targetCase = queueCasesRes.items.find((c) => c.id === caseId);
            if (targetCase) window.openAssignModal(targetCase);
          });
        });
      }

      // Render lawyers grid
      const lawyersContainer = container.querySelector("#lawyersGridContainer");
      if (lawyers.length === 0) {
        lawyersContainer.innerHTML = `<div class="text-center py-4 text-muted">${lang === "bn" ? "কোনো আইনজীবী নিবন্ধিত নেই।" : "No advocates listed."}</div>`;
      } else {
        lawyersContainer.innerHTML = lawyers.map((l) => `
          <div class="lawyer-card">
            <div class="lawyer-avatar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="lawyer-info">
              <h5>${l.full_name}</h5>
              <p class="text-xs text-muted"><strong>${l.specialization || "General Civil & Family"}</strong> | ${l.district || "National"}</p>
              <div class="lawyer-workload-badge">
                ${lang === "bn" ? "চলমান মামলা:" : "Active Matters:"} <strong>${window.formatNumber(l.active_cases_count, lang)}</strong>
              </div>
            </div>
          </div>
        `).join("");
      }

    } catch (err) {
      console.error("Error refreshing lawyer queue:", err);
    }
  };

  await refreshData();

  container.querySelector("#btnRefreshLawyerQueue").addEventListener("click", refreshData);
}

window.renderLawyerQueueView = renderLawyerQueueView;
