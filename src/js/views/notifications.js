/**
 * DLAS Notifications View
 */
async function renderNotificationsView(container, lang) {
  container.innerHTML = `
    <div class="view-header">
      <div>
        <h1 class="view-title">${window.t("notifications_title")}</h1>
        <p class="view-subtitle">${lang === "bn" ? "সকল মামলা সংক্রান্ত সাম্প্রতিক বিজ্ঞপ্তি ও সতর্কতা।" : "Real-time procedural alerts, appointments, and judicial notifications."}</p>
      </div>
      <div class="view-actions">
        <button id="btnRefreshNotifs" class="btn btn-secondary btn-sm">
          ${lang === "bn" ? "রিফ্রেশ" : "Refresh"}
        </button>
      </div>
    </div>

    <div class="section-card">
      <div id="notificationsListContainer" class="notifications-feed">
        <div class="py-5 text-center text-muted">Loading notifications...</div>
      </div>
    </div>
  `;

  const refreshNotifs = async () => {
    try {
      const notifs = await window.dlasApi.listNotifications();
      window.dlasStore.setNotifications(notifs);

      const listContainer = container.querySelector("#notificationsListContainer");
      if (notifs.length === 0) {
        listContainer.innerHTML = `<div class="py-5 text-center text-muted">${window.t("no_notifications")}</div>`;
        return;
      }

      listContainer.innerHTML = notifs.map((n) => {
        const title = (lang === "bn" && n.title_bn) ? n.title_bn : n.title;
        const msg = (lang === "bn" && n.message_bn) ? n.message_bn : n.message;
        return `
          <div class="notification-item ${n.is_read ? 'notif-read' : 'notif-unread'}" data-id="${n.id}">
            <div class="notif-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
            </div>
            <div class="notif-content">
              <div class="notif-top">
                <h5 class="notif-title">${title}</h5>
                <span class="notif-time text-xs text-muted">${window.formatDate(n.created_at, lang)}</span>
              </div>
              <p class="notif-message">${msg}</p>
              <div class="notif-actions mt-2">
                ${
                  n.case_id
                    ? `<button class="btn btn-link btn-xs btn-inspect-notif-case" data-case-id="${n.case_id}">
                        ${lang === "bn" ? "মামলা দেখুন" : "View Case"} →
                      </button>`
                    : ""
                }
                ${
                  !n.is_read
                    ? `<button class="btn btn-outline-secondary btn-xs btn-mark-notif-read" data-id="${n.id}">
                        ${window.t("btn_mark_read")}
                      </button>`
                    : ""
                }
              </div>
            </div>
          </div>
        `;
      }).join("");

      listContainer.querySelectorAll(".btn-mark-notif-read").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          e.stopPropagation();
          const notifId = parseInt(btn.dataset.id, 10);
          try {
            await window.dlasApi.markNotificationRead(notifId);
            const found = notifs.find((n) => n.id === notifId);
            if (found) found.is_read = true;
            window.dlasStore.setNotifications([...notifs]);
            refreshNotifs();
          } catch (_) {}
        });
      });

      listContainer.querySelectorAll(".btn-inspect-notif-case").forEach((btn) => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const caseId = parseInt(btn.dataset.caseId, 10);
          window.dlasStore.setView("detail", caseId);
        });
      });
    } catch (err) {
      console.error("Error loading notifications:", err);
    }
  };

  await refreshNotifs();
  container.querySelector("#btnRefreshNotifs").addEventListener("click", refreshNotifs);
}

window.renderNotificationsView = renderNotificationsView;
