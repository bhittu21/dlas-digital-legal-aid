/**
 * DLAS Frontend Configuration
 * Manages API and WebSocket endpoint resolution.
 */
const DLAS_CONFIG = {
  // Resolves authoritative FastAPI backend base URL
  getApiBaseUrl() {
    const custom = localStorage.getItem("dlas_custom_api_url");
    if (custom) return custom.replace(/\/+$/, "");

    const hostname = window.location.hostname;

    // Local development (any port)
    if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "0.0.0.0") {
      return `http://${hostname}:8000/api/v1`;
    }

    // Hosted directly on Render backend container
    if (hostname.includes("onrender.com")) {
      return `${window.location.origin}/api/v1`;
    }

    // Vercel deployment, custom domain, or cloud hosting
    return "https://dlas-digital-legal-aid.onrender.com/api/v1";
  },

  // Resolves authoritative WebSocket URL
  getWsUrl() {
    const custom = localStorage.getItem("dlas_custom_ws_url");
    if (custom) return custom.replace(/\/+$/, "");

    const hostname = window.location.hostname;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

    // Local development (any port)
    if (hostname === "localhost" || hostname === "127.0.0.1" || hostname === "0.0.0.0") {
      return `${protocol}//${hostname}:8000/ws`;
    }

    // Hosted directly on Render backend container
    if (hostname.includes("onrender.com")) {
      return `${protocol}//${window.location.host}/ws`;
    }

    // Vercel deployment, custom domain, or cloud hosting
    return "wss://dlas-digital-legal-aid.onrender.com/ws";
  }
};

window.DLAS_CONFIG = DLAS_CONFIG;
