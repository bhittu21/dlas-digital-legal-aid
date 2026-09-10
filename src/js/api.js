/**
 * DLAS Authoritative REST API Client
 * Interfaces strictly with the FastAPI backend.
 */
class ApiClient {
  constructor() {
    this.baseUrl = window.DLAS_CONFIG.getApiBaseUrl();
  }

  getHeaders(customHeaders = {}) {
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...customHeaders,
    };
    const token = window.dlasStore.getState().authToken;
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.headers),
    };

    try {
      const res = await fetch(url, config);

      if (res.status === 401) {
        // Token expired or invalid
        window.dlasStore.logout();
        throw new Error("Session expired. Please sign in again.");
      }

      if (!res.ok) {
        let errMessage = `HTTP error ${res.status}`;
        try {
          const errJson = await res.json();
          errMessage = errJson.detail || errMessage;
        } catch (_) {}
        throw new Error(errMessage);
      }

      return await res.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // Health Diagnostics
  async getHealth() {
    return this.request("/health");
  }

  // Authentication
  async login(email, password) {
    return this.request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this.request("/auth/me");
  }

  // Cases
  async listCases(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append("status", params.status);
    if (params.priority) query.append("priority", params.priority);
    if (params.category) query.append("legal_category", params.category);
    if (params.district) query.append("district", params.district);
    if (params.search) query.append("search", params.search);
    if (params.page) query.append("page", params.page);
    if (params.size) query.append("size", params.size || 25);

    const qs = query.toString();
    return this.request(`/cases${qs ? `?${qs}` : ""}`);
  }

  async getCaseDetail(caseId) {
    return this.request(`/cases/${caseId}`);
  }

  async createCase(caseData) {
    return this.request("/cases", {
      method: "POST",
      body: JSON.stringify(caseData),
    });
  }

  async updateCase(caseId, updateData) {
    return this.request(`/cases/${caseId}`, {
      method: "PATCH",
      body: JSON.stringify(updateData),
    });
  }

  // Human DLAO Verification Gate & Actions
  async verifyCase(caseId, { notes, priority, routeToPanelQueue = true }) {
    return this.request(`/cases/${caseId}/verify`, {
      method: "POST",
      body: JSON.stringify({
        notes,
        priority: priority || null,
        route_to_panel_queue: routeToPanelQueue,
      }),
    });
  }

  async requestCaseInfo(caseId, infoNeeded) {
    return this.request(`/cases/${caseId}/request-info`, {
      method: "POST",
      body: JSON.stringify({ info_needed: infoNeeded }),
    });
  }

  async rejectCase(caseId, reason) {
    return this.request(`/cases/${caseId}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  }

  async updateCasePriority(caseId, priority, reason) {
    return this.request(`/cases/${caseId}/priority`, {
      method: "POST",
      body: JSON.stringify({ priority, reason }),
    });
  }

  async assignPanelLawyer(caseId, lawyerId, notes = "") {
    return this.request(`/cases/${caseId}/assign`, {
      method: "POST",
      body: JSON.stringify({ lawyer_id: lawyerId, notes }),
    });
  }

  async archiveCase(caseId, reason) {
    return this.request(`/cases/${caseId}/archive`, {
      method: "POST",
      body: JSON.stringify({ authorization: true, reason }),
    });
  }

  // Case-specific audit log
  async getCaseAuditLogs(caseId) {
    return this.request(`/cases/${caseId}/audit-logs`);
  }

  // Panel Lawyers Directory
  async listPanelLawyers(district = "") {
    const qs = district ? `?district=${encodeURIComponent(district)}` : "";
    return this.request(`/lawyers${qs}`);
  }

  // Notifications
  async listNotifications() {
    return this.request("/notifications");
  }

  async markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: "PATCH",
    });
  }

  // System-wide Audit Log
  async listSystemAuditLogs(caseId = null, limit = 50) {
    const query = new URLSearchParams();
    if (caseId) query.append("case_id", caseId);
    query.append("limit", limit);
    return this.request(`/audit-logs?${query.toString()}`);
  }

  // Mock NID Verification
  async verifyMockNID(nidNumber, dateOfBirth, name = "") {
    return this.request("/mock-nid/verify", {
      method: "POST",
      body: JSON.stringify({
        nid_number: nidNumber,
        date_of_birth: dateOfBirth,
        name: name || null,
      }),
    });
  }

  // Missed-event Recovery Endpoint
  async getEventsSince(sinceSeq = 0) {
    return this.request(`/events/since?since_seq=${encodeURIComponent(sinceSeq)}`);
  }

  // DBLA Intake & Demo Identity Provider Endpoints
  async listDemoIdentities() {
    return this.request("/intake/demo-identities");
  }

  async lookupDemoIdentity(phoneNumber) {
    return this.request(`/intake/demo-lookup?phone_number=${encodeURIComponent(phoneNumber)}`, {
      method: "POST",
    });
  }

  async extractAiIntake(rawTranscript, callerPhone = null, existingAppId = null) {
    return this.request("/intake/extract-ai", {
      method: "POST",
      body: JSON.stringify({
        raw_transcript: rawTranscript,
        caller_phone: callerPhone,
        existing_application_id: existingAppId,
      }),
    });
  }

  async createIntakeApplication(applicationData) {
    return this.request("/intake/applications", {
      method: "POST",
      body: JSON.stringify(applicationData),
    });
  }

  async getIntakeApplication(applicationId) {
    return this.request(`/intake/applications/${applicationId}`);
  }

  // Voice Helpline Simulation Endpoints (Zero Twilio Cost in Browser Test Mode)
  async startVoiceSimulation(callerPhone = "+8801711000001", applicantName = "", district = "Dhaka") {
    return this.request("/voice/simulate/start", {
      method: "POST",
      body: JSON.stringify({
        caller_phone: callerPhone,
        applicant_name: applicantName || null,
        district: district || "Dhaka",
      }),
    });
  }

  async submitVoiceStep(sessionId, questionId, spokenAnswer, source = "BROWSER_SIMULATED", confidence = 1.0) {
    return this.request("/voice/simulate/step", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        spoken_answer: spokenAnswer,
        source: source,
        confidence: confidence,
      }),
    });
  }

  async getVoiceSession(sessionId) {
    return this.request(`/voice/simulate/session/${encodeURIComponent(sessionId)}`);
  }
}

window.dlasApi = new ApiClient();
