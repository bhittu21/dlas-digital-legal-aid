/**
 * DLAS DBLA Online Intake View
 * Reference: National Legal Aid Services Organization (NLASO) Online Applications
 * Portal: https://db.nlaso.gov.bd/Pages/OnlineApplications.aspx
 *
 * Implements:
 * 1. Demo Identity Provider lookup (Caller phone -> Demo Provider -> Fictional NID -> DBLA fields)
 * 2. AI-assisted spoken grievance extraction (Gemini mapping -> Field Provenance)
 * 3. Realtime DBLA application completeness calculation
 * 4. Provenance tracking: CALLER_REPORTED, AI_EXTRACTED, MOCK_IDENTITY, HUMAN_VERIFIED, SYSTEM_DERIVED
 */

(function () {
  let demoRecords = [];
  let formData = {
    applicant_name: "",
    applicant_name_bn: "",
    gender: "FEMALE",
    date_of_birth: "",
    age: null,
    marital_status: "MARRIED",
    religion: "ISLAM",
    phone_number: "",
    alternate_phone: "",
    email: "",
    nid_number: "",
    nid_type: "LEGACY_17",
    nid_verified: false,
    occupation: "",
    monthly_income_bdt: null,
    annual_income_bdt: null,
    education_level: "PRIMARY",
    num_dependents: 0,
    dependents_description: "",
    father_name: "",
    father_name_bn: "",
    mother_name: "",
    mother_name_bn: "",
    spouse_name: "",
    spouse_name_bn: "",
    present_division: "Dhaka",
    present_district: "Dhaka",
    present_upazila: "Mirpur",
    present_union_ward: "",
    present_village_road: "",
    present_post_code: "",
    permanent_division: "Dhaka",
    permanent_district: "Dhaka",
    permanent_upazila: "Mirpur",
    permanent_union_ward: "",
    permanent_village_road: "",
    permanent_post_code: "",
    has_representative: false,
    representative_name: "",
    representative_relation: "",
    representative_phone: "",
    opposing_party_name: "",
    opposing_party_address: "",
    opposing_party_relation: "",
    opposing_party_phone: "",
    legal_category: "LAND_PROPERTY",
    legal_sub_category: "",
    case_title: "",
    grievance_description: "",
    grievance_description_bn: "",
    relief_sought: "",
    incident_date: "",
    previous_case_filed: false,
    previous_case_number: "",
    court_name: "",
    intake_channel: "ONLINE_DBLA_FORM",
    raw_spoken_transcript: "",
  };

  let fieldProvenances = {};
  let currentCompleteness = {
    status: "MISSING_REQUIRED_INFORMATION",
    score: 0,
    missing: [
      "applicant_name",
      "phone_number",
      "present_district",
      "monthly_income_bdt",
      "legal_category",
      "grievance_description",
      "opposing_party_name",
    ],
    followUps: [],
  };

  const SAMPLE_TRANSCRIPTS = [
    {
      title: "Land Grabbing Dispute (Bangla)",
      phone: "+8801711000004",
      text: "আমার নাম রহিম উদ্দিন। আমি রাজশাহীর পবায় বসবাস করি। আমার পৈতৃক তিন বিঘা জমি জোর করে দখল করেছে মোতালেব প্রামাণিক। আমার দিনমজুরির মাসিক আয় ৯৫০০ টাকা। জমি উদ্ধারে সরকারের জরুরি আইনি সাহায্য চাই।",
    },
    {
      title: "Family Maintenance / Dower (Bangla)",
      phone: "+8801911000003",
      text: "আমার নাম ফাতেমা বেগম। আমি সিলেটে থাকি। স্বামী খোরপোশ ও দেনমোহর দেয় না। অপরপক্ষ জাহিরুল হক। আমার মাসিক আয় ৮৫০০ টাকা। আমি সন্তানের ভরণপোষণ ও দেনমোহর আদায় করতে চাই।",
    },
    {
      title: "RMG Termination & Unpaid Wages (Bangla)",
      phone: "+8801711000001",
      text: "আমার নাম শাহনাজ আক্তার। ঢাকার মিরপুরে পোশাক কারখানায় চাকরি করতাম। কর্ণফুলী গার্মেন্টস হঠাৎ চাকরি থেকে বের করে দিয়েছে ৪ মাসের বকেয়া বেতন ছাড়া। মাসিক বেতন ১২৫০০ টাকা। শ্রম আইনে পাওনা টাকা ও ক্ষতিপূরণ চাই।",
    },
  ];

  function getProvenanceBadge(field) {
    const prov = fieldProvenances[field];
    if (!prov) return "";
    const src = prov.source;
    let badgeClass = "badge-provenance-sys";
    let label = src;
    if (src === "MOCK_IDENTITY") {
      badgeClass = "badge-provenance-mock";
      label = window.t ? window.t("prov_mock") : "MOCK_IDENTITY";
    } else if (src === "AI_EXTRACTED") {
      badgeClass = "badge-provenance-ai";
      label = window.t ? window.t("prov_ai") : "AI_EXTRACTED";
    } else if (src === "CALLER_REPORTED") {
      badgeClass = "badge-provenance-caller";
      label = window.t ? window.t("prov_caller") : "CALLER_REPORTED";
    } else if (src === "HUMAN_VERIFIED") {
      badgeClass = "badge-provenance-human";
      label = window.t ? window.t("prov_human") : "HUMAN_VERIFIED";
    }
    return `<span class="provenance-pill ${badgeClass}" title="Source: ${src} | ${prov.notes || ''}">• ${label}</span>`;
  }

  function recalculateCompleteness() {
    const mandatoryFields = [
      "applicant_name",
      "phone_number",
      "present_district",
      "monthly_income_bdt",
      "legal_category",
      "grievance_description",
      "opposing_party_name",
    ];

    const recommendedFields = [
      "nid_number",
      "present_upazila",
      "incident_date",
      "relief_sought",
      "opposing_party_address",
      "occupation",
      "marital_status",
    ];

    const missingMandatory = [];
    for (const f of mandatoryFields) {
      const val = formData[f];
      if (val === null || val === undefined || String(val).trim() === "" || (typeof val === "number" && val < 0)) {
        missingMandatory.append ? missingMandatory.append(f) : missingMandatory.push(f);
      }
    }

    const missingRec = [];
    for (const f of recommendedFields) {
      const val = formData[f];
      if (val === null || val === undefined || String(val).trim() === "") {
        missingRec.push(f);
      }
    }

    const mEarned = (mandatoryFields.length - missingMandatory.length) * 10.0;
    const rEarned = (recommendedFields.length - missingRec.length) * (30.0 / recommendedFields.length);
    const score = Math.round(mEarned + rEarned);

    let status = "MISSING_REQUIRED_INFORMATION";
    if (missingMandatory.length === 0 && score >= 88) {
      status = "COMPLETE";
    } else if (missingMandatory.length === 0) {
      status = "PARTIALLY_COMPLETE";
    }

    currentCompleteness = {
      status,
      score,
      missing: missingMandatory,
      missingRecommended: missingRec,
    };

    updateCompletenessUI();
  }

  function updateCompletenessUI() {
    const meter = document.getElementById("dblaCompletenessMeter");
    if (!meter) return;

    let badgeClass = "badge-status-danger";
    let statusText = "MISSING REQUIRED INFORMATION";
    if (currentCompleteness.status === "COMPLETE") {
      badgeClass = "badge-status-success";
      statusText = "COMPLETE (READY FOR SUBMISSION)";
    } else if (currentCompleteness.status === "PARTIALLY_COMPLETE") {
      badgeClass = "badge-status-warning";
      statusText = "PARTIALLY COMPLETE";
    }

    meter.innerHTML = `
      <div class="completeness-header">
        <div class="completeness-title-row">
          <span class="font-bold text-sm">Application Statutory Completeness:</span>
          <span class="badge ${badgeClass} text-xs font-mono">${statusText}</span>
        </div>
        <div class="score-display">
          <span class="score-num font-bold text-lg text-emerald-700">${currentCompleteness.score}%</span>
        </div>
      </div>
      <div class="completeness-progress-bar">
        <div class="completeness-fill" style="width: ${Math.min(100, Math.max(5, currentCompleteness.score))}%; background-color: ${currentCompleteness.status === 'COMPLETE' ? '#059669' : currentCompleteness.status === 'PARTIALLY_COMPLETE' ? '#d97706' : '#dc2626'};"></div>
      </div>
      ${
        currentCompleteness.missing.length > 0
          ? `<div class="missing-fields-warning text-xs text-rose-700 mt-2">
               <strong>Missing Statutory Fields:</strong> ${currentCompleteness.missing.join(", ")}
             </div>`
          : `<div class="text-xs text-emerald-700 mt-2 font-medium">✓ All mandatory fields under Legal Aid Services Act 2000 satisfied.</div>`
      }
    `;
  }

  async function loadDemoIdentities() {
    try {
      const res = await window.dlasApi.listDemoIdentities();
      if (res && res.records) {
        demoRecords = res.records;
        const select = document.getElementById("demoPhoneSelect");
        if (select) {
          select.innerHTML = `<option value="">-- Select Fictional Demo Citizen Profile --</option>` +
            demoRecords.map(r => `
              <option value="${r.phone_number}">
                ${r.applicant_name} (${r.applicant_name_bn}) | ${r.phone_number} | ${r.occupation} (${r.present_district})
              </option>
            `).join("");
        }
      }
    } catch (err) {
      console.warn("Could not load demo identities:", err);
    }
  }

  async function handleDemoLookup(phoneNumber) {
    if (!phoneNumber) {
      window.showToastMessage("Please select a fictional citizen telephone number first.", "warning");
      return;
    }

    try {
      const profile = await window.dlasApi.lookupDemoIdentity(phoneNumber);
      if (!profile) return;

      // Populate DBLA fields
      formData.phone_number = profile.phone_number;
      formData.applicant_name = profile.applicant_name;
      formData.applicant_name_bn = profile.applicant_name_bn;
      formData.gender = profile.gender || "FEMALE";
      formData.date_of_birth = profile.date_of_birth;
      formData.father_name = profile.father_name || "";
      formData.father_name_bn = profile.father_name_bn || "";
      formData.mother_name = profile.mother_name || "";
      formData.mother_name_bn = profile.mother_name_bn || "";
      formData.present_division = profile.present_division || "Dhaka";
      formData.present_district = profile.present_district || "Dhaka";
      formData.present_upazila = profile.present_upazila || "";
      formData.occupation = profile.occupation || "";
      formData.monthly_income_bdt = profile.monthly_income_bdt;
      formData.annual_income_bdt = profile.monthly_income_bdt ? profile.monthly_income_bdt * 12 : null;
      formData.education_level = profile.education_level || "PRIMARY";
      formData.nid_number = profile.nid_number;
      formData.nid_type = profile.nid_type || "LEGACY_17";
      formData.nid_verified = true;

      // Track provenance
      const now = new Date().toISOString();
      const mockFields = [
        "phone_number", "applicant_name", "applicant_name_bn", "gender", "date_of_birth",
        "father_name", "father_name_bn", "mother_name", "mother_name_bn",
        "present_division", "present_district", "present_upazila",
        "occupation", "monthly_income_bdt", "education_level", "nid_number", "nid_type"
      ];
      mockFields.forEach(f => {
        fieldProvenances[f] = {
          source: "MOCK_IDENTITY",
          timestamp: now,
          confidence: 1.0,
          notes: "Derived from MockIdentityProvider synthetic Bangladesh registry record"
        };
      });

      fieldProvenances["annual_income_bdt"] = {
        source: "SYSTEM_DERIVED",
        timestamp: now,
        confidence: 1.0,
        notes: "Calculated as monthly_income_bdt * 12"
      };

      // Show banner & sync form
      syncFormFieldsFromState();
      recalculateCompleteness();
      window.showToastMessage(`Demo identity profile loaded for ${profile.applicant_name} (Fictional NID: ${profile.nid_number})`, "success");
    } catch (err) {
      window.showToastMessage("Lookup failed: " + (err.message || "Unknown error"), "danger");
    }
  }

  async function handleAiExtraction() {
    const transcript = (document.getElementById("spokenTranscriptInput")?.value || "").trim();
    if (!transcript) {
      window.showToastMessage("Please enter or select a spoken conversational transcript.", "warning");
      return;
    }

    const callerPhone = formData.phone_number || document.getElementById("demoPhoneSelect")?.value || null;
    const btn = document.getElementById("btnRunAiExtraction");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Processing transcript with Gemini AI...`;
    }

    try {
      const res = await window.dlasApi.extractAiIntake(transcript, callerPhone);
      if (res && res.extracted_fields) {
        const fields = res.extracted_fields;
        Object.keys(fields).forEach(k => {
          if (fields[k] !== null && fields[k] !== undefined) {
            formData[k] = fields[k];
          }
        });

        if (res.field_provenances) {
          Object.assign(fieldProvenances, res.field_provenances);
        }

        formData.raw_spoken_transcript = transcript;
        fieldProvenances["raw_spoken_transcript"] = {
          source: "CALLER_REPORTED",
          timestamp: new Date().toISOString(),
          confidence: 1.0,
          notes: "Raw conversational grievance statement"
        };

        syncFormFieldsFromState();
        recalculateCompleteness();
        window.showToastMessage("AI extraction complete: Legal grievance, party, and district mapped.", "success");
      }
    } catch (err) {
      window.showToastMessage("AI Extraction Error: " + (err.message || "Request failed"), "danger");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `Run Gemini Structured Extraction`;
      }
    }
  }

  function syncFormFieldsFromState() {
    const bindMap = {
      "dbla_applicant_name": "applicant_name",
      "dbla_applicant_name_bn": "applicant_name_bn",
      "dbla_phone": "phone_number",
      "dbla_alternate_phone": "alternate_phone",
      "dbla_email": "email",
      "dbla_nid": "nid_number",
      "dbla_nid_type": "nid_type",
      "dbla_occupation": "occupation",
      "dbla_income": "monthly_income_bdt",
      "dbla_gender": "gender",
      "dbla_dob": "date_of_birth",
      "dbla_education": "education_level",
      "dbla_father_name": "father_name",
      "dbla_mother_name": "mother_name",
      "dbla_spouse_name": "spouse_name",
      "dbla_present_district": "present_district",
      "dbla_present_upazila": "present_upazila",
      "dbla_legal_category": "legal_category",
      "dbla_case_title": "case_title",
      "dbla_grievance": "grievance_description",
      "dbla_opposing_party": "opposing_party_name",
      "dbla_relief": "relief_sought",
    };

    Object.entries(bindMap).forEach(([domId, prop]) => {
      const el = document.getElementById(domId);
      if (el) {
        if (formData[prop] !== null && formData[prop] !== undefined) {
          el.value = formData[prop];
        }
      }
    });

    // Re-render provenance badges next to fields
    document.querySelectorAll("[data-prov-for]").forEach(span => {
      const field = span.getAttribute("data-prov-for");
      span.innerHTML = getProvenanceBadge(field);
    });
  }

  function syncStateFromForm() {
    const bindMap = {
      "dbla_applicant_name": "applicant_name",
      "dbla_applicant_name_bn": "applicant_name_bn",
      "dbla_phone": "phone_number",
      "dbla_alternate_phone": "alternate_phone",
      "dbla_email": "email",
      "dbla_nid": "nid_number",
      "dbla_nid_type": "nid_type",
      "dbla_occupation": "occupation",
      "dbla_income": "monthly_income_bdt",
      "dbla_gender": "gender",
      "dbla_dob": "date_of_birth",
      "dbla_education": "education_level",
      "dbla_father_name": "father_name",
      "dbla_mother_name": "mother_name",
      "dbla_spouse_name": "spouse_name",
      "dbla_present_district": "present_district",
      "dbla_present_upazila": "present_upazila",
      "dbla_legal_category": "legal_category",
      "dbla_case_title": "case_title",
      "dbla_grievance": "grievance_description",
      "dbla_opposing_party": "opposing_party_name",
      "dbla_relief": "relief_sought",
    };

    Object.entries(bindMap).forEach(([domId, prop]) => {
      const el = document.getElementById(domId);
      if (el) {
        if (prop === "monthly_income_bdt") {
          formData[prop] = el.value ? parseFloat(el.value) : null;
          formData.annual_income_bdt = formData[prop] ? formData[prop] * 12 : null;
        } else {
          formData[prop] = el.value;
        }
      }
    });
  }

  async function handleCreateApplication() {
    syncStateFromForm();
    recalculateCompleteness();

    if (currentCompleteness.missing.length > 0) {
      window.showToastMessage(
        `Cannot submit application: Missing mandatory fields: ${currentCompleteness.missing.join(", ")}`,
        "danger"
      );
      return;
    }

    if (!formData.case_title) {
      formData.case_title = `${formData.legal_category.replace('_', ' ')} - ${formData.applicant_name}`;
    }

    const payload = {
      ...formData,
      field_provenances: fieldProvenances,
    };

    const submitBtn = document.getElementById("btnSubmitDblaApp");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Submitting Application to Authoritative DB...`;
    }

    try {
      const created = await window.dlasApi.createIntakeApplication(payload);
      window.showToastMessage(
        `Application successfully registered! Tracking ID: ${created.tracking_id} (Case #${created.case_id})`,
        "success"
      );

      // Navigate to newly created case
      setTimeout(() => {
        window.dlasStore.setState({ activeView: "queue" });
        if (window.renderAppLayout) window.renderAppLayout();
      }, 1200);
    } catch (err) {
      window.showToastMessage("Submission Failed: " + (err.message || "Server rejected request"), "danger");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = window.t ? window.t("dbla_btn_submit_app") : "Create Authoritative Case & Register Application";
      }
    }
  }

  function renderDblaIntakeView(container, lang = "en") {
    container.innerHTML = `
      <div class="view-content intake-view-container">
        <!-- Top Title & Government Portal Header -->
        <div class="view-header-row mb-4">
          <div>
            <h2 class="view-title text-2xl font-bold text-slate-900">
              ${window.t("dbla_intake_title")}
            </h2>
            <p class="view-subtitle text-sm text-slate-600">
              ${window.t("dbla_intake_subtitle")} | 
              <a href="https://db.nlaso.gov.bd/Pages/OnlineApplications.aspx" target="_blank" rel="noopener noreferrer" class="text-emerald-700 underline font-medium">
                NLASO DBLA Reference Portal ↗
              </a>
            </p>
          </div>
        </div>

        <!-- Statutory Compliance & Privacy Disclaimer Banner -->
        <div class="statutory-disclaimer-card mb-6">
          <div class="disclaimer-icon">⚠️</div>
          <div class="disclaimer-body">
            <h4 class="font-bold text-amber-900 text-sm mb-1">
              DEMO IDENTITY DATA — FOR HACKATHON EVALUATION ONLY
            </h4>
            <p class="text-xs text-amber-800 leading-relaxed">
              ${window.t("dbla_demo_warning")}
            </p>
            <div class="text-xs text-amber-950 font-semibold mt-1">
              • Direct SIM-to-NID derivation is strictly prohibited by law.
              • No external government databases are fabricated.
              • All synthetic applicant records are clearly isolated.
            </div>
          </div>
        </div>

        <div class="intake-grid-layout">
          <!-- Left Column: Simulation Tools (Demo Lookup + AI Extraction) -->
          <div class="intake-tools-column">
            <!-- 1. Demo Identity Provider Card -->
            <div class="card p-4 mb-4 border-l-4 border-l-purple-600 bg-white shadow-sm">
              <div class="flex items-center justify-between mb-2">
                <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full bg-purple-600 inline-block"></span>
                  ${window.t("dbla_demo_lookup_title")}
                </h3>
                <span class="badge badge-provenance-mock text-xs font-mono">IDENTITY_PROVIDER=mock</span>
              </div>
              <p class="text-xs text-slate-600 mb-3">
                Simulates incoming caller recognition flow using 12 pre-configured fictional citizen profiles.
              </p>

              <div class="form-group mb-3">
                <label class="form-label text-xs font-semibold text-slate-700">
                  ${window.t("dbla_demo_select_label")}
                </label>
                <select id="demoPhoneSelect" class="form-control text-xs">
                  <option value="">Loading fictional records...</option>
                </select>
              </div>

              <div class="demo-flow-diagram text-xs bg-slate-50 p-2.5 rounded border border-slate-200 mb-3 font-mono text-slate-700 leading-normal">
                caller phone → demo provider → fictional NID → DBLA fields [MOCK_IDENTITY]
              </div>

              <button type="button" id="btnRunDemoLookup" class="btn btn-sm btn-purple w-full">
                ${window.t("dbla_btn_lookup")}
              </button>
            </div>

            <!-- 2. AI Spoken Grievance Intake Card -->
            <div class="card p-4 mb-4 border-l-4 border-l-cyan-600 bg-white shadow-sm">
              <div class="flex items-center justify-between mb-2">
                <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full bg-cyan-600 inline-block"></span>
                  ${window.t("dbla_ai_intake_title")}
                </h3>
                <span class="badge badge-provenance-ai text-xs font-mono">Gemini Structured</span>
              </div>
              <p class="text-xs text-slate-600 mb-2">
                ${window.t("dbla_ai_intake_desc")}
              </p>

              <!-- Sample transcript pills -->
              <div class="mb-2">
                <span class="text-xs font-semibold text-slate-500 block mb-1">Pre-load Spoken Sample:</span>
                <div class="sample-chips-row flex flex-wrap gap-1">
                  ${SAMPLE_TRANSCRIPTS.map((s, idx) => `
                    <button type="button" class="btn btn-xs btn-outline-secondary btn-sample-chip" data-sample-idx="${idx}">
                      ${s.title}
                    </button>
                  `).join("")}
                </div>
              </div>

              <div class="form-group mb-3">
                <textarea id="spokenTranscriptInput" class="form-control text-xs" rows="4" placeholder="Enter raw spoken statement in Bengali or English..."></textarea>
              </div>

              <button type="button" id="btnRunAiExtraction" class="btn btn-sm btn-cyan w-full">
                ${window.t("dbla_btn_extract")}
              </button>
            </div>

            <!-- 3. Realtime Completeness Gauge -->
            <div class="card p-4 mb-4 bg-white shadow-sm border border-slate-200" id="dblaCompletenessMeter">
              <!-- Rendered dynamically -->
            </div>
          </div>

          <!-- Right Column: Full DBLA Structured Application Form -->
          <div class="intake-form-column">
            <div class="card p-5 bg-white shadow-sm border border-slate-200">
              <div class="dbla-form-header flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
                <div>
                  <h3 class="font-bold text-base text-slate-900">National Legal Aid Services Application Form</h3>
                  <span class="text-xs text-slate-500">Government of Bangladesh • Law and Justice Division</span>
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" id="btnSubmitDblaApp" class="btn btn-sm btn-success font-semibold px-4">
                    ${window.t("dbla_btn_submit_app")}
                  </button>
                </div>
              </div>

              <form id="dblaApplicationForm" onsubmit="return false;">
                <!-- Section 1: Applicant Particulars -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    1. Applicant Particulars / আবেদনকারীর তথ্য
                  </h4>
                  <div class="grid grid-cols-2 gap-3 mb-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Full Legal Name (English) <span class="text-rose-600">*</span>
                        <span data-prov-for="applicant_name"></span>
                      </label>
                      <input type="text" id="dbla_applicant_name" class="form-control text-xs" required placeholder="e.g. Shahnaz Akter" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        নাম (বাংলায়)
                        <span data-prov-for="applicant_name_bn"></span>
                      </label>
                      <input type="text" id="dbla_applicant_name_bn" class="form-control text-xs" placeholder="যেমন: শাহনাজ আক্তার" />
                    </div>
                  </div>

                  <div class="grid grid-cols-3 gap-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Gender / লিঙ্গ</label>
                      <select id="dbla_gender" class="form-control text-xs">
                        <option value="FEMALE">Female / নারী</option>
                        <option value="MALE">Male / পুরুষ</option>
                        <option value="THIRD_GENDER">Third Gender / হিজড়া</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Date of Birth / জন্মতারিখ</label>
                      <input type="date" id="dbla_dob" class="form-control text-xs" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Education / শিক্ষাগত যোগ্যতা</label>
                      <select id="dbla_education" class="form-control text-xs">
                        <option value="NONE">Illiterate / নিরক্ষর</option>
                        <option value="PRIMARY" selected>Primary / প্রাথমিক</option>
                        <option value="SECONDARY">Secondary / মাধ্যমিক</option>
                        <option value="HIGHER_SECONDARY">HSC / উচ্চ মাধ্যমিক</option>
                        <option value="GRADUATE">Graduate / স্নাতক</option>
                      </select>
                    </div>
                  </div>
                </div>

                <!-- Section 2: Contact & Identification -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    2. Contact & Identity / যোগাযোগ ও পরিচয়পত্র
                  </h4>
                  <div class="grid grid-cols-3 gap-3 mb-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Primary Mobile Phone <span class="text-rose-600">*</span>
                        <span data-prov-for="phone_number"></span>
                      </label>
                      <input type="text" id="dbla_phone" class="form-control text-xs font-mono" required placeholder="+88017XXXXXXXX" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Alternate Contact No.</label>
                      <input type="text" id="dbla_alternate_phone" class="form-control text-xs font-mono" placeholder="Optional" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Email Address</label>
                      <input type="email" id="dbla_email" class="form-control text-xs" placeholder="Optional" />
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        National ID (NID) Number
                        <span data-prov-for="nid_number"></span>
                      </label>
                      <input type="text" id="dbla_nid" class="form-control text-xs font-mono" placeholder="10 or 17 digits" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">NID Card Type</label>
                      <select id="dbla_nid_type" class="form-control text-xs font-mono">
                        <option value="SMART_10">SMART_10 (Smart NID)</option>
                        <option value="LEGACY_17" selected>LEGACY_17 (17-digit with Year)</option>
                        <option value="LEGACY_13">LEGACY_13 (13-digit legacy)</option>
                      </select>
                    </div>
                  </div>
                </div>

                <!-- Section 3: Socio-Economic Profile -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    3. Socio-Economic Eligibility / আর্থ-সামাজিক যোগ্যতা
                  </h4>
                  <div class="grid grid-cols-2 gap-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Occupation / পেশা
                        <span data-prov-for="occupation"></span>
                      </label>
                      <input type="text" id="dbla_occupation" class="form-control text-xs" placeholder="e.g. Garment Worker, Day Laborer" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Monthly Income (BDT) <span class="text-rose-600">*</span>
                        <span data-prov-for="monthly_income_bdt"></span>
                      </label>
                      <input type="number" id="dbla_income" class="form-control text-xs font-mono" required placeholder="e.g. 12000" />
                      <span class="text-2xs text-slate-500">Eligibility threshold under Legal Aid Services Act 2000</span>
                    </div>
                  </div>
                </div>

                <!-- Section 4: Family Details -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    4. Family Information / পিতা, মাতা ও স্ত্রীর তথ্য
                  </h4>
                  <div class="grid grid-cols-3 gap-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Father's Name / পিতার নাম</label>
                      <input type="text" id="dbla_father_name" class="form-control text-xs" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Mother's Name / মাতার নাম</label>
                      <input type="text" id="dbla_mother_name" class="form-control text-xs" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Spouse's Name / স্বামী বা স্ত্রীর নাম</label>
                      <input type="text" id="dbla_spouse_name" class="form-control text-xs" />
                    </div>
                  </div>
                </div>

                <!-- Section 5: Address -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    5. Present Address / বর্তমান ঠিকানা
                  </h4>
                  <div class="grid grid-cols-2 gap-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        District / জেলা <span class="text-rose-600">*</span>
                        <span data-prov-for="present_district"></span>
                      </label>
                      <input type="text" id="dbla_present_district" class="form-control text-xs" required placeholder="e.g. Dhaka, Chittagong, Sylhet" />
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Upazila / Police Station / উপজেলা বা থানা
                        <span data-prov-for="present_upazila"></span>
                      </label>
                      <input type="text" id="dbla_present_upazila" class="form-control text-xs" placeholder="e.g. Mirpur, Pahartali" />
                    </div>
                  </div>
                </div>

                <!-- Section 6: Opposing Party / Respondent -->
                <div class="form-section mb-5">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    6. Opposing Party / বিবাদী বা অপরপক্ষের বিবরণ
                  </h4>
                  <div class="form-group">
                    <label class="form-label text-xs font-semibold">
                      Opposing Party Full Name <span class="text-rose-600">*</span>
                      <span data-prov-for="opposing_party_name"></span>
                    </label>
                    <input type="text" id="dbla_opposing_party" class="form-control text-xs" required placeholder="Name of person or organization" />
                  </div>
                </div>

                <!-- Section 7: Legal Problem & Grievance -->
                <div class="form-section mb-4">
                  <h4 class="form-section-heading text-xs font-bold uppercase tracking-wider text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded mb-3">
                    7. Legal Grievance & Relief / অভিযোগ ও প্রত্যাশিত প্রতিকার
                  </h4>
                  <div class="grid grid-cols-2 gap-3 mb-3">
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">
                        Legal Category / মামলার ধরন <span class="text-rose-600">*</span>
                        <span data-prov-for="legal_category"></span>
                      </label>
                      <select id="dbla_legal_category" class="form-control text-xs font-semibold">
                        <option value="LAND_PROPERTY">Land & Property / ভূমি ও সম্পত্তি বিরোধ</option>
                        <option value="FAMILY_MATRIMONIAL">Family & Matrimonial / পারিবারিক ও দেনমোহর</option>
                        <option value="LABOUR_EMPLOYMENT">Labour & Employment / শ্রম আইন ও বকেয়া বেতন</option>
                        <option value="DOMESTIC_VIOLENCE_DOWRY">Domestic Violence & Dowry / পারিবারিক সহিংসতা ও যৌতুক</option>
                        <option value="CRIMINAL_DEFENSE_BAIL">Criminal Defense & Bail / ফৌজদারি জামিন</option>
                        <option value="CIVIL_GENERAL">Civil & Money Recovery / দেওয়ানি ও অর্থ বিরোধ</option>
                      </select>
                    </div>
                    <div class="form-group">
                      <label class="form-label text-xs font-semibold">Case Title / শিরোনাম</label>
                      <input type="text" id="dbla_case_title" class="form-control text-xs" placeholder="e.g. Land Partition Suit" />
                    </div>
                  </div>

                  <div class="form-group mb-3">
                    <label class="form-label text-xs font-semibold">
                      Grievance Description / সমস্যার বিস্তারিত বিবরণ <span class="text-rose-600">*</span>
                      <span data-prov-for="grievance_description"></span>
                    </label>
                    <textarea id="dbla_grievance" class="form-control text-xs" rows="3" required placeholder="State facts, dates, and actions taken..."></textarea>
                  </div>

                  <div class="form-group">
                    <label class="form-label text-xs font-semibold">Relief Sought / প্রত্যাশিত প্রতিকার</label>
                    <input type="text" id="dbla_relief" class="form-control text-xs" placeholder="e.g. Mediation notice, partition suit, recovery of wages" />
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    `;

    // Load initial demo identity list
    loadDemoIdentities();
    recalculateCompleteness();

    // Event listeners
    document.getElementById("btnRunDemoLookup")?.addEventListener("click", () => {
      const ph = document.getElementById("demoPhoneSelect")?.value;
      handleDemoLookup(ph);
    });

    document.getElementById("demoPhoneSelect")?.addEventListener("change", (e) => {
      if (e.target.value) {
        handleDemoLookup(e.target.value);
      }
    });

    document.getElementById("btnRunAiExtraction")?.addEventListener("click", () => {
      handleAiExtraction();
    });

    document.querySelectorAll(".btn-sample-chip").forEach(btn => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.currentTarget.getAttribute("data-sample-idx"), 10);
        const sample = SAMPLE_TRANSCRIPTS[idx];
        if (sample) {
          const txt = document.getElementById("spokenTranscriptInput");
          if (txt) txt.value = sample.text;
          const phSel = document.getElementById("demoPhoneSelect");
          if (phSel && sample.phone) {
            phSel.value = sample.phone;
          }
        }
      });
    });

    document.getElementById("btnSubmitDblaApp")?.addEventListener("click", () => {
      handleCreateApplication();
    });

    // Realtime completeness recalculation on input changes
    document.querySelectorAll("#dblaApplicationForm input, #dblaApplicationForm select, #dblaApplicationForm textarea").forEach(input => {
      input.addEventListener("input", () => {
        syncStateFromForm();
        recalculateCompleteness();
      });
      input.addEventListener("change", () => {
        syncStateFromForm();
        recalculateCompleteness();
      });
    });
  }

  window.renderDblaIntakeView = renderDblaIntakeView;
})();
