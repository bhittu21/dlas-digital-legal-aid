/**
 * DLAS Case Detail & Judicial Dossier View
 */
async function renderCaseDetailView(container, lang) {
  const state = window.dlasStore.getState();
  const caseId = state.selectedCaseId;
  const user = state.currentUser || {};
  const isDLAO = user.role === "dlao_officer" || user.role === "admin";

  container.innerHTML = `
    <div class="loading-state py-5 text-center">
      <div class="spinner"></div>
      <p class="mt-3 text-muted">${lang === "bn" ? "মামলার নথি লোড হচ্ছে..." : "Loading case dossier..."}</p>
    </div>
  `;

  try {
    const c = await window.dlasApi.getCaseDetail(caseId);
    window.dlasStore.setSelectedCase(c);
    const auditLogs = await window.dlasApi.getCaseAuditLogs(caseId);

    // Title selection: Use Bangla title if available and language is bn, otherwise English title
    const displayTitle = (lang === "bn" && c.title_bn) ? c.title_bn : c.title;
    const displayDesc = (lang === "bn" && c.description_bn) ? c.description_bn : c.description;

    container.innerHTML = `
      <div class="view-header">
        <div class="header-breadcrumbs">
          <button id="btnBackToQueue" class="btn btn-secondary btn-sm">
            ← ${window.t("back_to_queue")}
          </button>
          <span class="tracking-id-hero">${c.tracking_id}</span>
        </div>
        <div class="view-actions">
          <button id="btnListenAudio" class="btn btn-secondary btn-sm" title="Audio Readout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
            </svg>
            ${window.t("btn_listen")}
          </button>
        </div>
      </div>

      <!-- Main Header Card -->
      <div class="detail-hero-card">
        <div class="hero-top-row">
          <div class="hero-tags">
            ${window.getStatusBadgeHtml(c.status, lang)}
            ${window.getPriorityBadgeHtml(c.priority, lang)}
            ${window.getCategoryBadgeHtml(c.legal_category, lang)}
            <span class="intake-channel-pill">${c.intake_channel}</span>
          </div>
          <span class="text-muted text-xs">
            ${lang === "bn" ? "নিবন্ধন:" : "Registered:"} ${window.formatDate(c.created_at, lang)}
          </span>
        </div>
        <h2 class="case-main-title">${displayTitle}</h2>
        ${c.title_bn && lang === "en" ? `<p class="title-sub-bn text-muted">${c.title_bn}</p>` : ""}
      </div>

      <!-- Action Toolbar for DLAO Officers -->
      ${
        isDLAO && !c.archived
          ? `
            <div class="dlao-action-bar">
              <span class="dlao-action-label">${lang === "bn" ? "ডিএলএও দাপ্তরিক সিদ্ধান্ত:" : "DLAO Judicial Directives:"}</span>
              <div class="dlao-action-buttons">
                ${
                  c.status === "PENDING_HUMAN_REVIEW" || c.status === "NEEDS_INFORMATION" || c.status === "VERIFIED"
                    ? `<button id="btnActionVerify" class="btn btn-success btn-sm">${window.t("btn_verify")}</button>`
                    : ""
                }
                ${
                  c.status === "PENDING_HUMAN_REVIEW"
                    ? `<button id="btnActionRequestInfo" class="btn btn-warning btn-sm">${window.t("btn_request_info")}</button>`
                    : ""
                }
                ${
                  c.status === "PENDING_HUMAN_REVIEW" || c.status === "NEEDS_INFORMATION"
                    ? `<button id="btnActionReject" class="btn btn-danger btn-sm">${window.t("btn_reject")}</button>`
                    : ""
                }
                ${
                  c.status === "PANEL_LAWYER_QUEUE" || c.status === "VERIFIED"
                    ? `<button id="btnActionAssignLawyer" class="btn btn-primary btn-sm">${window.t("btn_assign_lawyer")}</button>`
                    : ""
                }
                <button id="btnActionChangePriority" class="btn btn-secondary btn-sm">${window.t("btn_change_priority")}</button>
                <button id="btnActionArchive" class="btn btn-outline-danger btn-sm">${window.t("btn_archive_matter")}</button>
              </div>
            </div>
          `
          : ""
      }

      <div class="detail-grid">
        <!-- Left Column: Dossier Content -->
        <div class="detail-main-col">
          <!-- Procedural Timeline Stepper -->
          <div class="section-card">
            <h4 class="section-card-title">${window.t("lifecycle_timeline")}</h4>
            <div class="timeline-stepper">
              <div class="step-item ${['NEW', 'AI_INTAKE', 'PENDING_HUMAN_REVIEW', 'VERIFIED', 'PANEL_LAWYER_QUEUE', 'LAWYER_REVIEW'].includes(c.status) ? 'step-done' : ''}">
                <div class="step-dot">1</div>
                <div class="step-label">${window.t("status_NEW")}</div>
              </div>
              <div class="step-line"></div>
              <div class="step-item ${['AI_INTAKE', 'PENDING_HUMAN_REVIEW', 'VERIFIED', 'PANEL_LAWYER_QUEUE', 'LAWYER_REVIEW'].includes(c.status) ? 'step-done' : ''}">
                <div class="step-dot">2</div>
                <div class="step-label">${window.t("status_AI_INTAKE")}</div>
              </div>
              <div class="step-line"></div>
              <div class="step-item ${['PENDING_HUMAN_REVIEW', 'VERIFIED', 'PANEL_LAWYER_QUEUE', 'LAWYER_REVIEW'].includes(c.status) ? 'step-done' : ''} ${c.status === 'PENDING_HUMAN_REVIEW' ? 'step-active' : ''}">
                <div class="step-dot">3</div>
                <div class="step-label">${window.t("status_PENDING_HUMAN_REVIEW")}</div>
              </div>
              <div class="step-line"></div>
              <div class="step-item ${['VERIFIED', 'PANEL_LAWYER_QUEUE', 'LAWYER_REVIEW'].includes(c.status) ? 'step-done' : ''} ${['VERIFIED', 'PANEL_LAWYER_QUEUE'].includes(c.status) ? 'step-active' : ''}">
                <div class="step-dot">4</div>
                <div class="step-label">${window.t("status_PANEL_LAWYER_QUEUE")}</div>
              </div>
              <div class="step-line"></div>
              <div class="step-item ${c.status === 'LAWYER_REVIEW' ? 'step-done step-active' : ''}">
                <div class="step-dot">5</div>
                <div class="step-label">${window.t("status_LAWYER_REVIEW")}</div>
              </div>
            </div>
          </div>

          <!-- Dispute Narrative -->
          <div class="section-card">
            <h4 class="section-card-title">${window.t("case_narrative")}</h4>
            <div class="narrative-box">
              <p class="narrative-text">${displayDesc}</p>
              ${c.description_bn && lang === "en" ? `<div class="sub-narrative text-muted"><small><strong>Bangla Record:</strong> ${c.description_bn}</small></div>` : ""}
            </div>
          </div>

          <!-- AI Intake Assessment (Gemini Advisory) -->
          <div class="section-card ai-assessment-card">
            <div class="ai-header">
              <div class="ai-title-wrap">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2">
                  <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
                <h4>${window.t("ai_advisory_box")}</h4>
              </div>
              <span class="ai-chip">Gemini 2.0 Flash</span>
            </div>

            <div class="ai-body">
              <div class="ai-metric-row">
                <span class="ai-metric-label">${window.t("ai_urgency_label")}:</span>
                <span class="ai-metric-val">${c.ai_urgency_score ? window.getPriorityBadgeHtml(c.ai_urgency_score, lang) : "—"}</span>
              </div>
              <p class="ai-summary-text">
                ${c.ai_summary || (lang === "bn" ? "এআই সারাংশ প্রক্রিয়া সম্পন্ন।" : "Automated intake entity extraction completed.")}
              </p>
              <div class="ai-disclaimer-box">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="12" y1="8" x2="12" y2="12"/>
                  <line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>${window.t("ai_disclaimer")}</span>
              </div>
            </div>
          </div>

          <!-- Judicial Verification Assessment -->
          <div class="section-card">
            <h4 class="section-card-title">${window.t("judicial_notes")}</h4>
            <div class="judicial-box">
              ${
                c.verification_notes
                  ? `<p class="judicial-text">${c.verification_notes}</p>`
                  : `<p class="text-muted italic">${lang === "bn" ? "এখনও কোনো বিচার বিভাগীয় যাচাইকরণ মন্তব্য লিপিবদ্ধ হয়নি।" : "No judicial verification notes recorded yet."}</p>`
              }
              ${
                c.verified_at
                  ? `<div class="verified-meta text-xs text-muted mt-2">
                      ${lang === "bn" ? "যাচাইকৃত:" : "Verified at:"} ${window.formatDate(c.verified_at, lang)}
                    </div>`
                  : ""
              }
            </div>
          </div>

          <!-- Immutable Transaction Audit Trail for this Case -->
          <div class="section-card">
            <h4 class="section-card-title">${window.t("audit_title")}</h4>
            <div class="table-responsive">
              <table class="dlas-table table-sm">
                <thead>
                  <tr>
                    <th>${window.t("col_timestamp")}</th>
                    <th>${window.t("col_actor")}</th>
                    <th>${window.t("col_event")}</th>
                    <th>${window.t("col_transition")}</th>
                    <th>${window.t("col_notes")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${
                    auditLogs.length === 0
                      ? `<tr><td colspan="5" class="text-center text-muted">${lang === "bn" ? "কোনো অডিট রেকর্ড নেই।" : "No audit entries recorded."}</td></tr>`
                      : auditLogs.map((log) => `
                        <tr>
                          <td class="text-xs text-muted">${window.formatDate(log.timestamp, lang)}</td>
                          <td><strong>${log.actor_name}</strong> <span class="text-xs text-muted">(${log.actor_role})</span></td>
                          <td><span class="badge badge-default">${log.action}</span></td>
                          <td class="text-xs">
                            ${log.previous_state ? `<span class="text-muted">${log.previous_state}</span> → ` : ""}
                            <strong>${log.new_state || "—"}</strong>
                          </td>
                          <td class="text-xs">${log.notes || "—"}</td>
                        </tr>
                      `).join("")
                  }
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Right Column: Applicant Profile & Advocate Assignment -->
        <div class="detail-sidebar-col">
          <!-- Applicant Profile Card -->
          <div class="sidebar-card">
            <h4 class="sidebar-card-title">${window.t("applicant_details")}</h4>
            <div class="applicant-profile-list">
              <div class="profile-item">
                <span class="profile-label">${window.t("full_name")}</span>
                <span class="profile-value">${c.applicant_name}</span>
              </div>
              <div class="profile-item">
                <span class="profile-label">${window.t("phone_number")}</span>
                <span class="profile-value">${c.applicant_phone}</span>
              </div>
              <div class="profile-item">
                <span class="profile-label">${window.t("nid_number")}</span>
                <div class="profile-value">
                  ${c.applicant_nid || "—"}
                  ${
                    c.applicant_nid_verified
                      ? `<span class="nid-badge nid-verified">${window.t("nid_verified_badge")}</span>`
                      : `<span class="nid-badge nid-pending">${window.t("nid_unverified_badge")}</span>`
                  }
                </div>
              </div>
              <div class="profile-item">
                <span class="profile-label">${window.t("monthly_income")}</span>
                <span class="profile-value highlight-income">${window.formatCurrency(c.applicant_income_bdt, lang)}</span>
              </div>
              <div class="profile-item">
                <span class="profile-label">${window.t("jurisdiction")}</span>
                <span class="profile-value">${c.district}${c.upazila ? `, ${c.upazila}` : ""}</span>
              </div>
              <div class="profile-item">
                <span class="profile-label">${window.t("intake_channel")}</span>
                <span class="profile-value">${c.intake_channel}</span>
              </div>
            </div>
          </div>

          <!-- Appointed Panel Advocate Card -->
          <div class="sidebar-card">
            <h4 class="sidebar-card-title">${window.t("assigned_counsel")}</h4>
            <div class="counsel-body">
              ${
                c.assigned_lawyer_id
                  ? `
                    <div class="counsel-info">
                      <div class="counsel-avatar">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                          <circle cx="12" cy="7" r="4"/>
                        </svg>
                      </div>
                      <div>
                        <h5>${lang === "bn" ? "অ্যাডভোকেট নিযুক্ত আছেন" : "Panel Advocate Engaged"}</h5>
                        <p class="text-xs text-muted">Lawyer ID: #${c.assigned_lawyer_id}</p>
                        ${c.assigned_at ? `<p class="text-xs text-muted">${lang === "bn" ? "নিয়োগের তারিখ:" : "Assigned at:"} ${window.formatDate(c.assigned_at, lang)}</p>` : ""}
                      </div>
                    </div>
                  `
                  : `
                    <p class="text-muted text-sm">${window.t("no_counsel_yet")}</p>
                    ${
                      isDLAO && (c.status === "PANEL_LAWYER_QUEUE" || c.status === "VERIFIED")
                        ? `<button id="btnSidebarAssign" class="btn btn-primary btn-block btn-sm mt-3">${window.t("btn_assign_lawyer")}</button>`
                        : ""
                    }
                  `
              }
            </div>
          </div>
        </div>
      </div>
    `;

    // Event Handlers
    container.querySelector("#btnBackToQueue").addEventListener("click", () => {
      window.dlasStore.setView("queue");
    });

    container.querySelector("#btnListenAudio").addEventListener("click", () => {
      const speech = `${displayTitle}. ${displayDesc}`;
      window.speakText(speech);
    });

    // Verification modals triggers
    const triggerVerify = () => window.openVerifyModal(c);
    const triggerRequestInfo = () => window.openRequestInfoModal(c);
    const triggerReject = () => window.openRejectModal(c);
    const triggerChangePriority = () => window.openPriorityModal(c);
    const triggerAssignLawyer = () => window.openAssignModal(c);
    const triggerArchive = () => window.openArchiveModal(c);

    if (container.querySelector("#btnActionVerify")) {
      container.querySelector("#btnActionVerify").addEventListener("click", triggerVerify);
    }
    if (container.querySelector("#btnActionRequestInfo")) {
      container.querySelector("#btnActionRequestInfo").addEventListener("click", triggerRequestInfo);
    }
    if (container.querySelector("#btnActionReject")) {
      container.querySelector("#btnActionReject").addEventListener("click", triggerReject);
    }
    if (container.querySelector("#btnActionChangePriority")) {
      container.querySelector("#btnActionChangePriority").addEventListener("click", triggerChangePriority);
    }
    if (container.querySelector("#btnActionAssignLawyer")) {
      container.querySelector("#btnActionAssignLawyer").addEventListener("click", triggerAssignLawyer);
    }
    if (container.querySelector("#btnSidebarAssign")) {
      container.querySelector("#btnSidebarAssign").addEventListener("click", triggerAssignLawyer);
    }
    if (container.querySelector("#btnActionArchive")) {
      container.querySelector("#btnActionArchive").addEventListener("click", triggerArchive);
    }

  } catch (err) {
    container.innerHTML = `
      <div class="alert alert-danger my-5">
        <h4>Error Loading Case</h4>
        <p>${err.message}</p>
        <button id="btnErrorBack" class="btn btn-secondary mt-3">← Back to Queue</button>
      </div>
    `;
    container.querySelector("#btnErrorBack").addEventListener("click", () => {
      window.dlasStore.setView("queue");
    });
  }
}

window.renderCaseDetailView = renderCaseDetailView;
