/**
 * DLAS Human Verification & Judicial Action Modals
 */

function closeActiveModal() {
  const modalContainer = document.getElementById("modalContainer");
  if (modalContainer) {
    modalContainer.innerHTML = "";
    modalContainer.style.display = "none";
  }
}

function openModal(htmlContent) {
  let modalContainer = document.getElementById("modalContainer");
  if (!modalContainer) {
    modalContainer = document.createElement("div");
    modalContainer.id = "modalContainer";
    document.body.appendChild(modalContainer);
  }

  modalContainer.innerHTML = `
    <div class="modal-backdrop" id="modalBackdrop">
      <div class="modal-dialog">
        <button class="modal-close-btn" id="modalCloseBtn">&times;</button>
        ${htmlContent}
      </div>
    </div>
  `;
  modalContainer.style.display = "block";

  modalContainer.querySelector("#modalCloseBtn").addEventListener("click", closeActiveModal);
  modalContainer.querySelector("#modalBackdrop").addEventListener("click", (e) => {
    if (e.target.id === "modalBackdrop") closeActiveModal();
  });
}

function openVerifyModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  const content = `
    <div class="modal-header">
      <h3>${window.t("modal_verify_title")}</h3>
      <p class="modal-sub text-muted">${window.t("modal_verify_desc")}</p>
    </div>
    <form id="verifyForm" class="modal-form">
      <div class="form-group">
        <label>${window.t("notes_label")} <span class="required">*</span></label>
        <textarea 
          id="verifyNotes" 
          class="form-control" 
          rows="4" 
          required 
          placeholder="${window.t("notes_placeholder")}"
        >Statutory economic insolvency and prima facie merit verified under Legal Aid Services Act 2000.</textarea>
      </div>

      <div class="form-group">
        <label>${window.t("filter_priority")}</label>
        <select id="verifyPriority" class="form-control">
          <option value="LOW" ${caseItem.priority === "LOW" ? "selected" : ""}>${window.t("prio_LOW")}</option>
          <option value="MEDIUM" ${caseItem.priority === "MEDIUM" ? "selected" : ""}>${window.t("prio_MEDIUM")}</option>
          <option value="HIGH" ${caseItem.priority === "HIGH" ? "selected" : ""}>${window.t("prio_HIGH")}</option>
          <option value="EMERGENCY" ${caseItem.priority === "EMERGENCY" ? "selected" : ""}>${window.t("prio_EMERGENCY")}</option>
        </select>
      </div>

      <div class="form-group checkbox-group">
        <label>
          <input type="checkbox" id="verifyRouteQueue" checked />
          ${window.t("route_to_queue_checkbox")}
        </label>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-success" id="btnSubmitVerify">${window.t("btn_submit")}</button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("verifyForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const notes = document.getElementById("verifyNotes").value.trim();
    const priority = document.getElementById("verifyPriority").value;
    const routeToPanelQueue = document.getElementById("verifyRouteQueue").checked;
    const submitBtn = document.getElementById("btnSubmitVerify");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.verifyCase(caseItem.id, {
        notes,
        priority,
        routeToPanelQueue,
      });
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("detail", caseItem.id);
    } catch (err) {
      alert(err.message || "Verification failed");
      submitBtn.disabled = false;
    }
  });
}

function openRequestInfoModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  const content = `
    <div class="modal-header">
      <h3>${window.t("modal_request_info_title")}</h3>
      <p class="modal-sub text-muted">${window.t("request_info_desc")}</p>
    </div>
    <form id="requestInfoForm" class="modal-form">
      <div class="form-group">
        <label>${window.t("info_needed_label")} <span class="required">*</span></label>
        <textarea 
          id="infoNeededText" 
          class="form-control" 
          rows="4" 
          required 
          placeholder="e.g. Please provide Union Parishad land tenancy receipt, medical injury certificate, or pay slips."
        ></textarea>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-warning" id="btnSubmitRequestInfo">${window.t("btn_submit")}</button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("requestInfoForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const infoNeeded = document.getElementById("infoNeededText").value.trim();
    const submitBtn = document.getElementById("btnSubmitRequestInfo");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.requestCaseInfo(caseItem.id, infoNeeded);
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("detail", caseItem.id);
    } catch (err) {
      alert(err.message || "Operation failed");
      submitBtn.disabled = false;
    }
  });
}

function openRejectModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  const content = `
    <div class="modal-header">
      <h3 class="text-danger">${window.t("modal_reject_title")}</h3>
      <p class="modal-sub text-muted">
        ${lang === "bn" ? "আইনগত সহায়তা প্রাপ্তির অযোগ্যতার কারণ সুস্পষ্টভাবে লিপিবদ্ধ করুন।" : "Specify statutory grounds why applicant is ineligible for state legal aid."}
      </p>
    </div>
    <form id="rejectForm" class="modal-form">
      <div class="form-group">
        <label>${window.t("reject_reason_label")} <span class="required">*</span></label>
        <textarea 
          id="rejectReasonText" 
          class="form-control" 
          rows="4" 
          required 
          placeholder="e.g. Applicant monthly income exceeds gazetted ceiling under Legal Aid Act 2000, or dispute lacks prima facie legal basis."
        ></textarea>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-danger" id="btnSubmitReject">${window.t("btn_submit")}</button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("rejectForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const reason = document.getElementById("rejectReasonText").value.trim();
    const submitBtn = document.getElementById("btnSubmitReject");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.rejectCase(caseItem.id, reason);
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("detail", caseItem.id);
    } catch (err) {
      alert(err.message || "Rejection failed");
      submitBtn.disabled = false;
    }
  });
}

function openPriorityModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  const content = `
    <div class="modal-header">
      <h3>${window.t("btn_change_priority")}</h3>
    </div>
    <form id="priorityForm" class="modal-form">
      <div class="form-group">
        <label>${window.t("filter_priority")} <span class="required">*</span></label>
        <select id="selectPriority" class="form-control">
          <option value="LOW" ${caseItem.priority === "LOW" ? "selected" : ""}>${window.t("prio_LOW")}</option>
          <option value="MEDIUM" ${caseItem.priority === "MEDIUM" ? "selected" : ""}>${window.t("prio_MEDIUM")}</option>
          <option value="HIGH" ${caseItem.priority === "HIGH" ? "selected" : ""}>${window.t("prio_HIGH")}</option>
          <option value="EMERGENCY" ${caseItem.priority === "EMERGENCY" ? "selected" : ""}>${window.t("prio_EMERGENCY")}</option>
        </select>
      </div>

      <div class="form-group">
        <label>${lang === "bn" ? "পরিবর্তনের কারণ" : "Reason for Urgency Adjustment"} <span class="required">*</span></label>
        <input type="text" id="priorityReason" class="form-control" required placeholder="e.g. Imminent eviction risk or urgent court date" />
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-primary" id="btnSubmitPriority">${window.t("btn_submit")}</button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("priorityForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const priority = document.getElementById("selectPriority").value;
    const reason = document.getElementById("priorityReason").value.trim();
    const submitBtn = document.getElementById("btnSubmitPriority");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.updateCasePriority(caseItem.id, priority, reason);
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("detail", caseItem.id);
    } catch (err) {
      alert(err.message || "Priority adjustment failed");
      submitBtn.disabled = false;
    }
  });
}

async function openAssignModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  let lawyers = [];
  try {
    lawyers = await window.dlasApi.listPanelLawyers(caseItem.district || "");
    if (lawyers.length === 0) {
      lawyers = await window.dlasApi.listPanelLawyers(); // fallback all districts
    }
  } catch (_) {}

  const content = `
    <div class="modal-header">
      <h3>${window.t("modal_assign_title")}</h3>
      <p class="modal-sub text-muted">${caseItem.tracking_id} - ${caseItem.title}</p>
    </div>
    <form id="assignForm" class="modal-form">
      <div class="form-group">
        <label>${window.t("select_lawyer_label")} <span class="required">*</span></label>
        <select id="selectLawyer" class="form-control" required>
          ${
            lawyers.length === 0
              ? `<option value="">${lang === "bn" ? "কোনো আইনজীবী পাওয়া যায়নি" : "No panel lawyers available"}</option>`
              : lawyers.map((l) => `
                <option value="${l.id}">
                  ${l.full_name} (${l.specialization || "General"}) - ${l.district || "All"} | ${window.t("lawyer_workload")}: ${l.active_cases_count}
                </option>
              `).join("")
          }
        </select>
      </div>

      <div class="form-group">
        <label>${lang === "bn" ? "নিয়োগ নির্দেশনা বা নোট" : "Appointment Directives & Notes"}</label>
        <textarea id="assignNotes" class="form-control" rows="3" placeholder="e.g. Please file urgent injunction and contact applicant within 48 hours."></textarea>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-primary" id="btnSubmitAssign" ${lawyers.length === 0 ? "disabled" : ""}>
          ${window.t("btn_submit")}
        </button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("assignForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const lawyerId = parseInt(document.getElementById("selectLawyer").value, 10);
    const notes = document.getElementById("assignNotes").value.trim();
    const submitBtn = document.getElementById("btnSubmitAssign");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.assignPanelLawyer(caseItem.id, lawyerId, notes);
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("detail", caseItem.id);
    } catch (err) {
      alert(err.message || "Assignment failed");
      submitBtn.disabled = false;
    }
  });
}

function openArchiveModal(caseItem) {
  const lang = window.dlasStore.getState().language;
  const content = `
    <div class="modal-header">
      <h3 class="text-danger">${window.t("modal_archive_title")}</h3>
      <p class="modal-sub text-muted">${caseItem.tracking_id} - ${caseItem.title}</p>
    </div>
    <form id="archiveForm" class="modal-form">
      <div class="form-group checkbox-group">
        <label>
          <input type="checkbox" id="archiveConfirm" required />
          <strong>${window.t("archive_confirm_label")}</strong>
        </label>
      </div>

      <div class="form-group">
        <label>${window.t("archive_reason_label")} <span class="required">*</span></label>
        <input type="text" id="archiveReason" class="form-control" required placeholder="e.g. Matter formally resolved via mediation or court disposal" />
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" onclick="window.closeActiveModal()">${window.t("btn_cancel")}</button>
        <button type="submit" class="btn btn-danger" id="btnSubmitArchive">${window.t("btn_submit")}</button>
      </div>
    </form>
  `;

  openModal(content);

  document.getElementById("archiveForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const reason = document.getElementById("archiveReason").value.trim();
    const submitBtn = document.getElementById("btnSubmitArchive");
    submitBtn.disabled = true;

    try {
      const updatedCase = await window.dlasApi.archiveCase(caseItem.id, reason);
      window.dlasStore.updateSingleCase(updatedCase);
      closeActiveModal();
      window.showToastMessage(window.t("toast_success"), "success");
      window.dlasStore.setView("queue");
    } catch (err) {
      alert(err.message || "Archival failed");
      submitBtn.disabled = false;
    }
  });
}

window.closeActiveModal = closeActiveModal;
window.openVerifyModal = openVerifyModal;
window.openRequestInfoModal = openRequestInfoModal;
window.openRejectModal = openRejectModal;
window.openPriorityModal = openPriorityModal;
window.openAssignModal = openAssignModal;
window.openArchiveModal = openArchiveModal;
