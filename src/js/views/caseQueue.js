/**
 * DLAS Live Case Queue View
 */
function renderCaseQueueView(container, lang) {
  const state = window.dlasStore.getState();
  const filter = state.casesFilter;
  const cases = state.cases || [];
  const total = state.casesTotal || 0;
  const page = state.casesPage || 1;
  const totalPages = Math.ceil(total / 25) || 1;

  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("nav_queue")}</h1>
        <p class="view-subtitle">
          ${lang === "bn" ? "মোট মামলা:" : "Total matters found:"} 
          <strong>${window.formatNumber(total, lang)}</strong>
        </p>
      </div>
      <div class="view-actions">
        <button id="btnResetFilters" class="btn btn-secondary btn-sm">
          ${lang === "bn" ? "ফিল্টার রিসেট" : "Reset Filters"}
        </button>
      </div>
    </div>

    <!-- Search & Multi-Filter Bar -->
    <div class="filter-card">
      <div class="filter-grid">
        <div class="filter-item filter-search">
          <input 
            type="text" 
            id="searchInput" 
            class="form-control" 
            placeholder="${window.t("search_placeholder")}" 
            value="${filter.search || ""}"
          />
        </div>

        <div class="filter-item">
          <select id="statusFilter" class="form-control">
            <option value="">${window.t("all_statuses")}</option>
            <option value="NEW" ${filter.status === "NEW" ? "selected" : ""}>${window.t("status_NEW")}</option>
            <option value="AI_INTAKE" ${filter.status === "AI_INTAKE" ? "selected" : ""}>${window.t("status_AI_INTAKE")}</option>
            <option value="PENDING_HUMAN_REVIEW" ${filter.status === "PENDING_HUMAN_REVIEW" ? "selected" : ""}>${window.t("status_PENDING_HUMAN_REVIEW")}</option>
            <option value="VERIFIED" ${filter.status === "VERIFIED" ? "selected" : ""}>${window.t("status_VERIFIED")}</option>
            <option value="PANEL_LAWYER_QUEUE" ${filter.status === "PANEL_LAWYER_QUEUE" ? "selected" : ""}>${window.t("status_PANEL_LAWYER_QUEUE")}</option>
            <option value="LAWYER_REVIEW" ${filter.status === "LAWYER_REVIEW" ? "selected" : ""}>${window.t("status_LAWYER_REVIEW")}</option>
            <option value="NEEDS_INFORMATION" ${filter.status === "NEEDS_INFORMATION" ? "selected" : ""}>${window.t("status_NEEDS_INFORMATION")}</option>
            <option value="REJECTED" ${filter.status === "REJECTED" ? "selected" : ""}>${window.t("status_REJECTED")}</option>
          </select>
        </div>

        <div class="filter-item">
          <select id="priorityFilter" class="form-control">
            <option value="">${window.t("all_priorities")}</option>
            <option value="LOW" ${filter.priority === "LOW" ? "selected" : ""}>${window.t("prio_LOW")}</option>
            <option value="MEDIUM" ${filter.priority === "MEDIUM" ? "selected" : ""}>${window.t("prio_MEDIUM")}</option>
            <option value="HIGH" ${filter.priority === "HIGH" ? "selected" : ""}>${window.t("prio_HIGH")}</option>
            <option value="EMERGENCY" ${filter.priority === "EMERGENCY" ? "selected" : ""}>${window.t("prio_EMERGENCY")}</option>
          </select>
        </div>

        <div class="filter-item">
          <select id="categoryFilter" class="form-control">
            <option value="">${window.t("all_categories")}</option>
            <option value="FAMILY_MATRIMONIAL" ${filter.category === "FAMILY_MATRIMONIAL" ? "selected" : ""}>${window.t("cat_FAMILY_MATRIMONIAL")}</option>
            <option value="LAND_PROPERTY" ${filter.category === "LAND_PROPERTY" ? "selected" : ""}>${window.t("cat_LAND_PROPERTY")}</option>
            <option value="DOMESTIC_VIOLENCE_DOWRY" ${filter.category === "DOMESTIC_VIOLENCE_DOWRY" ? "selected" : ""}>${window.t("cat_DOMESTIC_VIOLENCE_DOWRY")}</option>
            <option value="LABOUR_EMPLOYMENT" ${filter.category === "LABOUR_EMPLOYMENT" ? "selected" : ""}>${window.t("cat_LABOUR_EMPLOYMENT")}</option>
            <option value="CRIMINAL_DEFENSE_BAIL" ${filter.category === "CRIMINAL_DEFENSE_BAIL" ? "selected" : ""}>${window.t("cat_CRIMINAL_DEFENSE_BAIL")}</option>
            <option value="CIVIL_GENERAL" ${filter.category === "CIVIL_GENERAL" ? "selected" : ""}>${window.t("cat_CIVIL_GENERAL")}</option>
          </select>
        </div>

        <div class="filter-item">
          <button id="btnApplyFilter" class="btn btn-primary btn-block">
            ${lang === "bn" ? "অনুসন্ধান" : "Search"}
          </button>
        </div>
      </div>
    </div>

    <!-- Case Table -->
    <div class="section-card">
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
                ? `<tr><td colspan="7" class="text-center py-5 text-muted">${window.t("no_cases_found")}</td></tr>`
                : cases.map((c) => `
                  <tr class="table-row-hover" data-id="${c.id}">
                    <td>
                      <span class="tracking-id-badge">${c.tracking_id}</span>
                    </td>
                    <td>
                      <div class="applicant-cell">
                        <strong>${c.applicant_name}</strong>
                        <span class="text-muted text-xs">${c.applicant_phone}</span>
                        ${c.applicant_income_bdt ? `<span class="income-tag">${window.formatCurrency(c.applicant_income_bdt, lang)}</span>` : ""}
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

      <!-- Pagination -->
      <div class="pagination-bar">
        <span class="pagination-info">
          ${lang === "bn" ? `পৃষ্ঠা ${window.formatNumber(page, lang)} / ${window.formatNumber(totalPages, lang)}` : `Page ${page} of ${totalPages}`}
        </span>
        <div class="pagination-controls">
          <button id="btnPrevPage" class="btn btn-secondary btn-xs" ${page <= 1 ? "disabled" : ""}>
            ← ${lang === "bn" ? "পূর্ববর্তী" : "Previous"}
          </button>
          <button id="btnNextPage" class="btn btn-secondary btn-xs" ${page >= totalPages ? "disabled" : ""}>
            ${lang === "bn" ? "পরবর্তী" : "Next"} →
          </button>
        </div>
      </div>
    </div>
  `;

  // Attach search & filter handlers
  const executeQuery = async (newPage = 1) => {
    const searchVal = container.querySelector("#searchInput").value.trim();
    const statusVal = container.querySelector("#statusFilter").value;
    const priorityVal = container.querySelector("#priorityFilter").value;
    const categoryVal = container.querySelector("#categoryFilter").value;

    state.casesFilter = {
      search: searchVal,
      status: statusVal,
      priority: priorityVal,
      category: categoryVal,
      district: "",
    };

    try {
      const res = await window.dlasApi.listCases({
        ...state.casesFilter,
        page: newPage,
      });
      window.dlasStore.setCases(res.items, res.total, newPage);
    } catch (err) {
      alert(err.message || "Failed to query cases");
    }
  };

  container.querySelector("#btnApplyFilter").addEventListener("click", () => executeQuery(1));

  container.querySelector("#searchInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") executeQuery(1);
  });

  container.querySelector("#statusFilter").addEventListener("change", () => executeQuery(1));
  container.querySelector("#priorityFilter").addEventListener("change", () => executeQuery(1));
  container.querySelector("#categoryFilter").addEventListener("change", () => executeQuery(1));

  container.querySelector("#btnResetFilters").addEventListener("click", () => {
    container.querySelector("#searchInput").value = "";
    container.querySelector("#statusFilter").value = "";
    container.querySelector("#priorityFilter").value = "";
    container.querySelector("#categoryFilter").value = "";
    executeQuery(1);
  });

  container.querySelector("#btnPrevPage").addEventListener("click", () => {
    if (page > 1) executeQuery(page - 1);
  });

  container.querySelector("#btnNextPage").addEventListener("click", () => {
    if (page < totalPages) executeQuery(page + 1);
  });

  // Row inspection
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

window.renderCaseQueueView = renderCaseQueueView;
