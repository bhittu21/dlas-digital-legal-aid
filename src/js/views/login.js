/**
 * DLAS Login View
 */
function renderLoginView(container, lang) {
  container.innerHTML = `
    <div class="login-wrapper">
      <div class="login-card">
        <div class="login-header">
          <div class="emblem-container">
            <div class="gov-seal">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                <circle cx="12" cy="12" r="10" stroke="#065f46" stroke-width="2"/>
                <path d="m9 12 2 2 4-4" stroke="#065f46" stroke-width="2"/>
                <path d="M12 6v2M12 16v2M6 12h2M16 12h2" stroke="#b45309"/>
              </svg>
            </div>
          </div>
          <p class="gov-sup">${window.t("gov_title")}</p>
          <h2 class="app-heading">${window.t("app_title")}</h2>
          <p class="login-sub">${window.t("login_subtitle")}</p>
        </div>

        <form id="loginForm" class="login-form">
          <div id="loginError" class="alert alert-danger" style="display: none;"></div>

          <div class="form-group">
            <label for="loginEmail">${window.t("email_label")}</label>
            <input 
              type="email" 
              id="loginEmail" 
              class="form-control" 
              required 
              placeholder="e.g. dlao.dhaka@dlas.gov.bd"
              value="dlao.dhaka@dlas.gov.bd"
            />
          </div>

          <div class="form-group">
            <label for="loginPassword">${window.t("password_label")}</label>
            <input 
              type="password" 
              id="loginPassword" 
              class="form-control" 
              required 
              placeholder="••••••••••••"
              value="DlaoPass2026!"
            />
          </div>

          <button type="submit" id="btnSignInSubmit" class="btn btn-primary btn-block">
            <span class="btn-spinner" style="display: none;"></span>
            ${window.t("sign_in_btn")}
          </button>
        </form>

        <div class="quick-login-section">
          <p class="quick-title">${window.t("quick_login_hint")}</p>
          <div class="quick-pills">
            <button type="button" class="quick-btn" data-email="officer@dlas.gov.bd" data-pass="officer123">
              <span class="role-badge badge-dlao">DLAO</span> Officer (officer123)
            </button>
            <button type="button" class="quick-btn" data-email="dlao.dhaka@dlas.gov.bd" data-pass="DlaoPass2026!">
              <span class="role-badge badge-dlao">DLAO</span> ${window.t("role_dlao_dhaka")}
            </button>
            <button type="button" class="quick-btn" data-email="lawyer@dlas.gov.bd" data-pass="lawyer123">
              <span class="role-badge badge-advocate">ADV</span> Lawyer (lawyer123)
            </button>
            <button type="button" class="quick-btn" data-email="lawyer.nazmul@dlas.gov.bd" data-pass="LawyerPass2026!">
              <span class="role-badge badge-advocate">ADV</span> ${window.t("role_lawyer_nazmul")}
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Attach event listeners
  const form = document.getElementById("loginForm");
  const errorDiv = document.getElementById("loginError");
  const submitBtn = document.getElementById("btnSignInSubmit");
  const spinner = submitBtn.querySelector(".btn-spinner");

  // Quick buttons
  container.querySelectorAll(".quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.getElementById("loginEmail").value = btn.dataset.email;
      document.getElementById("loginPassword").value = btn.dataset.pass;
    });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorDiv.style.display = "none";
    submitBtn.disabled = true;
    spinner.style.display = "inline-block";

    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
      const authData = await window.dlasApi.login(email, password);
      window.dlasStore.setAuth(authData.access_token, {
        id: authData.user_id,
        email: authData.email,
        full_name: authData.full_name,
        role: authData.role,
        district: authData.district,
      });

      // Connect WebSocket upon login
      window.dlasRealtime.connect();

      // Immediately fetch initial authoritative datasets
      try {
        const casesRes = await window.dlasApi.listCases();
        if (casesRes && casesRes.items) {
          window.dlasStore.setCases(casesRes.items, casesRes.total, casesRes.page);
        }
        const notifs = await window.dlasApi.listNotifications();
        if (notifs) {
          window.dlasStore.setNotifications(notifs);
        }
      } catch (fetchErr) {
        console.warn("Post-login data fetch warning:", fetchErr);
      }
    } catch (err) {
      let errorMsg = err.message || window.t("login_error");
      const lower = errorMsg.toLowerCase();
      if (lower.includes("failed to fetch") || lower.includes("networkerror") || lower.includes("cors")) {
        errorMsg = lang === "bn"
          ? "ক্লাউড সার্ভারের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি। রেন্ডার ক্লাউড ব্যাকএন্ড চালু হতে ২০-৩০ সেকেন্ড সময় লাগতে পারে, অনুগ্রহ করে পুনরায় চেষ্টা করুন।"
          : "Could not connect to the cloud backend. Render instances may take 20-30 seconds to wake up from cold standby. Please wait a moment and retry.";
      }
      errorDiv.textContent = errorMsg;
      errorDiv.style.display = "block";
    } finally {
      submitBtn.disabled = false;
      spinner.style.display = "none";
    }
  });
}

window.renderLoginView = renderLoginView;
