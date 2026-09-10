/**
 * DLAS Settings, Language & Identity Testing View
 */
function renderSettingsView(container, lang) {
  const state = window.dlasStore.getState();
  const user = state.currentUser || {};

  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("settings_title")}</h1>
        <p class="view-subtitle">${lang === "bn" ? "ভাষা পরিবর্তন, ব্যবহারকারী প্রোফাইল এবং ডেমো এনআইডি ভেরিফায়ার।" : "Language customization, official profile metadata, and simulated NID testing tool."}</p>
      </div>
    </div>

    <div class="settings-grid">
      <!-- Language Switcher Card -->
      <div class="section-card">
        <h4 class="section-card-title">${window.t("interface_lang")}</h4>
        <p class="text-sm text-muted mb-4">
          ${lang === "bn" 
            ? "বাংলাদেশ সরকারের জাতীয় পোর্টালের মতো তাৎক্ষণিক ভাষা পরিবর্তন। কোনো পেজ রিলোড ছাড়াই সম্পূর্ণ ইন্টারফেস বাংলায় রূপান্তরিত হবে।" 
            : "Government standard bilingual toggling. Instant client-side transformation without page reload or state loss."}
        </p>
        <div class="lang-toggle-container">
          <button id="btnSetLangBn" class="btn ${lang === 'bn' ? 'btn-primary' : 'btn-secondary'}">
            বাংলা (Bangla)
          </button>
          <button id="btnSetLangEn" class="btn ${lang === 'en' ? 'btn-primary' : 'btn-secondary'}">
            English (EN)
          </button>
        </div>
      </div>

      <!-- User Profile Card -->
      <div class="section-card">
        <h4 class="section-card-title">${window.t("active_profile")}</h4>
        <div class="profile-item">
          <span class="profile-label">${window.t("full_name")}</span>
          <span class="profile-value">${user.full_name || "Official"}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">${window.t("email_label")}</span>
          <span class="profile-value">${user.email || "—"}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">${lang === "bn" ? "ভূমিকা / পদবি" : "Role / Authorization"}</span>
          <span class="profile-value"><span class="role-badge badge-dlao">${user.role || "—"}</span></span>
        </div>
        <div class="profile-item">
          <span class="profile-label">${lang === "bn" ? "আওতাধীন জেলা" : "Jurisdiction"}</span>
          <span class="profile-value">${user.district || "National"}</span>
        </div>
      </div>
    </div>

    <!-- Demo Mock NID Identity Verification Tester -->
    <div class="section-card mt-4">
      <div class="section-card-header">
        <h4>${lang === "bn" ? "ডেমো জাতীয় পরিচয়পত্র (এনআইডি) যাচাইকরণ টুল" : "Simulated Bangladesh NID Identity Adapter"}</h4>
        <span class="badge badge-default">Demo Adapter</span>
      </div>
      <p class="text-xs text-muted mb-4">
        ${lang === "bn" 
          ? "সতর্কতা: এটি একটি পরীক্ষামূলক ডেমো অ্যাডাপ্টার। নির্বাচন কমিশন বা সরকারি কোনো সার্ভারের সাথে সরাসরি সংযোগ দাবি করা হয় না।" 
          : "Transparency: This is a simulated identity adapter conforming to Bangladesh NID format rules (10-digit Smart / 17-digit Legacy)."}
      </p>

      <form id="nidTestForm" class="nid-tester-form">
        <div class="filter-grid">
          <div class="filter-item">
            <label class="text-xs text-muted">NID Number (10 or 17 digits)</label>
            <input type="text" id="testNidNumber" class="form-control" placeholder="e.g. 19852691234567890 or 1234567890" value="19852691234567890" required />
          </div>
          <div class="filter-item">
            <label class="text-xs text-muted">Date of Birth (YYYY-MM-DD)</label>
            <input type="date" id="testNidDob" class="form-control" value="1985-11-20" required />
          </div>
          <div class="filter-item" style="align-self: flex-end;">
            <button type="submit" class="btn btn-primary btn-block" id="btnTestNidSubmit">
              ${lang === "bn" ? "এনআইডি যাচাই পরীক্ষা" : "Test Verification"}
            </button>
          </div>
        </div>
      </form>

      <div id="nidTestResultBox" class="mt-4" style="display: none;"></div>
    </div>
  `;

  // Language switch listeners
  container.querySelector("#btnSetLangBn").addEventListener("click", () => {
    window.dlasStore.setLanguage("bn");
  });

  container.querySelector("#btnSetLangEn").addEventListener("click", () => {
    window.dlasStore.setLanguage("en");
  });

  // NID form listener
  container.querySelector("#nidTestForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nid = container.querySelector("#testNidNumber").value.trim();
    const dob = container.querySelector("#testNidDob").value;
    const resultBox = container.querySelector("#nidTestResultBox");
    const submitBtn = container.querySelector("#btnTestNidSubmit");

    submitBtn.disabled = true;
    resultBox.style.display = "block";
    resultBox.innerHTML = `<p class="text-muted text-center py-2">Verifying via MockNIDAdapter...</p>`;

    try {
      const res = await window.dlasApi.verifyMockNID(nid, dob);
      if (res.is_valid) {
        resultBox.innerHTML = `
          <div class="alert alert-success">
            <h5>✓ NID Verification Successful (Simulated)</h5>
            <div class="profile-item mt-2">
              <span class="profile-label">Name (EN):</span>
              <span class="profile-value"><strong>${res.name_en || "—"}</strong></span>
            </div>
            <div class="profile-item">
              <span class="profile-label">Name (BN):</span>
              <span class="profile-value"><strong>${res.name_bn || "—"}</strong></span>
            </div>
            <div class="profile-item">
              <span class="profile-label">Father's Name:</span>
              <span class="profile-value">${res.father_name || "—"}</span>
            </div>
            <div class="profile-item">
              <span class="profile-label">District:</span>
              <span class="profile-value">${res.district || "—"}</span>
            </div>
            <p class="text-xs text-muted mt-3">${res.disclaimer}</p>
          </div>
        `;
      } else {
        resultBox.innerHTML = `
          <div class="alert alert-danger">
            <h5>✗ NID Verification Failed</h5>
            <p class="text-sm">${res.disclaimer}</p>
          </div>
        `;
      }
    } catch (err) {
      resultBox.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    } finally {
      submitBtn.disabled = false;
    }
  });
}

window.renderSettingsView = renderSettingsView;
