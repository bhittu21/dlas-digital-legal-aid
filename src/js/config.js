/**
 * DLAS Frontend Configuration
 * Manages API and WebSocket endpoint resolution.
 */
const DLAS_CONFIG = {
  // Default to local FastAPI backend when running locally
  getApiBaseUrl() {
    const custom = localStorage.getItem("dlas_custom_api_url");
    if (custom) return custom;
    if (window.location.port === "8000" || window.location.port === "3000") {
      return `http://${window.location.hostname}:8000/api/v1`;
    }
    // Fallback for Vercel deployment with relative or configured domain
    return window.location.origin.includes("vercel.app") 
      ? "https://dlas-digital-legal-aid.onrender.com/api/v1"
      : `http://${window.location.hostname}:8000/api/v1`;
  },

  getWsUrl() {
    const custom = localStorage.getItem("dlas_custom_ws_url");
    if (custom) return custom;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    if (window.location.port === "8000" || window.location.port === "3000") {
      return `${protocol}//${window.location.hostname}:8000/ws`;
    }
    return window.location.origin.includes("vercel.app")
      ? "wss://dlas-digital-legal-aid.onrender.com/ws"
      : `${protocol}//${window.location.hostname}:8000/ws`;
  }
};

window.DLAS_CONFIG = DLAS_CONFIG;
