/**
 * DLAS System-wide Audit Log View
 */
async function renderAuditLogsView(container, lang) {
  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("audit_title")}</h1>
        <p class="view-subtitle">${window.t("audit_subtitle")}</p>
      </div>
      <div class="view-actions">
        <button id="btnRefreshAudit" class="btn btn-secondary btn-sm">
          ${lang === "bn" ? "রিফ্রেশ" : "Refresh"}
        </button>
      </div>
    </div>

    <div class="section-card">
      <div class="table-responsive">
        <table class="dlas-table">
          <thead>
            <tr>
              <th>${window.t("col_timestamp")}</th>
              <th>${window.t("col_actor")}</th>
              <th>${window.t("col_case")}</th>
              <th>${window.t("col_event")}</th>
              <th>${window.t("col_transition")}</th>
              <th>${window.t("col_notes")}</th>
            </tr>
          </thead>
          <tbody id="auditTableBody">
            <tr><td colspan="6" class="text-center py-5 text-muted">${lang === "bn" ? "নিরীক্ষা লগ লোড হচ্ছে..." : "Loading audit log trail..."}</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  `;

  const refreshAudit = async () => {
    try {
      const logs = await window.dlasApi.listSystemAuditLogs(null, 50);
      const tbody = container.querySelector("#auditTableBody");

      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-5 text-muted">${lang === "bn" ? "কোনো অডিট রেকর্ড পাওয়া যায়নি।" : "No audit entries recorded."}</td></tr>`;
        return;
      }

      tbody.innerHTML = logs.map((log) => `
        <tr>
          <td class="text-xs text-muted">${window.formatDate(log.timestamp, lang)}</td>
          <td>
            <strong>${log.actor_name}</strong>
            <div class="text-xs text-muted">${log.actor_role} ${log.ip_address ? `• ${log.ip_address}` : ""}</div>
          </td>
          <td>
            ${
              log.case_id
                ? `<button class="btn btn-link btn-xs btn-inspect-audit-case" data-id="${log.case_id}">Case #${log.case_id}</button>`
                : "—"
            }
          </td>
          <td><span class="badge badge-default">${log.action}</span></td>
          <td class="text-xs">
            ${log.previous_state ? `<span class="text-muted">${log.previous_state}</span> → ` : ""}
            <strong>${log.new_state || "—"}</strong>
          </td>
          <td class="text-xs">${log.notes || "—"}</td>
        </tr>
      `).join("");

      tbody.querySelectorAll(".btn-inspect-audit-case").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const caseId = parseInt(btn.dataset.id, 10);
          window.dlasStore.setView("detail", caseId);
        });
      });
    } catch (err) {
      console.error("Error loading audit logs:", err);
    }
  };

  await refreshAudit();
  container.querySelector("#btnRefreshAudit").addEventListener("click", refreshAudit);
}

window.renderAuditLogsView = renderAuditLogsView;
