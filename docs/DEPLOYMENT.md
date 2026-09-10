# DLAS Deployment Guide — Production Release

This guide outlines the production deployment procedure for the **Digital Legal Aid System (DLAS)** following the authoritative backend architecture split between **Render** (FastAPI Backend + PostgreSQL) and **Vercel** (Bilingual Single-Page Interface).

---

## Architecture Overview

```mermaid
graph TD
    CitizenPhone[Caller Phone / Web Browser] -->|16430 / +17372508034| Twilio[Twilio Voice Gateway]
    Twilio -->|HTTP POST TwiML / WebSocket| RenderBackend[Render: FastAPI Backend & State Machine]
    RenderBackend -->|Authoritative Transactions| RenderPostgres[(PostgreSQL Database)]
    RenderBackend -->|Realtime WebSockets| VercelFrontend[Vercel: Bilingual Dashboard & Queue]
    VercelFrontend -->|REST API Requests| RenderBackend
    RenderBackend -->|Safety & Categorization| GeminiAI[Google Gemini 2.0 Flash]
```

---

## 1. Backend Deployment (Render)

### A. Environment Configuration
Create a Web Service on [Render](https://render.com) pointing to this repository with **Root Directory**: `backend`.

- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### B. Required Environment Variables on Render
Configure these in the Render Dashboard under **Environment**:

| Variable Name | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Environment mode | `production` |
| `HOST` | Bind host | `0.0.0.0` |
| `PORT` | Dynamic port set by host | `8000` |
| `CORS_ORIGINS` | Allowed frontend domains | `https://dlas-legal-aid.vercel.app,http://localhost:3000` |
| `SECRET_KEY` | Cryptographic JWT signing key | *(Generate a 64-char random hex string)* |
| `ALGORITHM` | JWT hashing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session validity duration | `1440` (24 hours) |
| `DATABASE_URL` | Render PostgreSQL internal connection URL | `postgresql://user:pass@dpg-xxxx.render.com/dlas_db` |
| `GEMINI_API_KEY` | Google Gemini API Key (Backend only) | `AIzaSy...` |
| `GEMINI_MODEL` | Gemini Model Identifier | `gemini-2.0-flash` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `...` |
| `TWILIO_PHONE_NUMBER` | National legal aid helpline number | `+17372508034` |
| `TWILIO_VOICE_LANGUAGE` | Default speech language | `bn-BD` |
| `IDENTITY_PROVIDER` | Legal Aid Identity Adapter Mode | `mock` *(demo mode; zero synthetic gov claims)* |

> [!IMPORTANT]
> Render provides PostgreSQL connection strings starting with `postgres://`. The DLAS config automatically normalizes this to `postgresql://` for SQLAlchemy 2.0 compatibility.

---

## 2. Frontend Deployment (Vercel)

### A. Project Settings
Create a Project on [Vercel](https://vercel.com) connecting the repository root.

- **Framework Preset**: `Other`
- **Root Directory**: `./` (Uses `vercel.json` rewrite routing `/src/$1`)
- **Output Directory**: `src`

### B. Frontend Environment Variables
In the Vercel Dashboard, configure:

```ini
NEXT_PUBLIC_API_BASE_URL=https://<your-render-backend-url>.onrender.com
NEXT_PUBLIC_WS_BASE_URL=wss://<your-render-backend-url>.onrender.com/ws
```

> [!CAUTION]
> NEVER place `TWILIO_AUTH_TOKEN`, `GEMINI_API_KEY`, or database credentials in Vercel environment variables or frontend code. The frontend interacts strictly through authenticated DLAS API endpoints.

---

## 3. Twilio Telephony & Webhook Configuration

Configure the active Twilio phone number (`+17372508034` or Bangladeshi virtual trunk) in the [Twilio Console](https://console.twilio.com):

1. **Voice Configuration**:
   - **A Call Comes In**: `Webhook`
   - **URL**: `https://<your-render-backend-url>.onrender.com/api/v1/voice/twilio/incoming`
   - **HTTP Method**: `HTTP POST`
2. **Status Callback**:
   - **URL**: `https://<your-render-backend-url>.onrender.com/api/v1/voice/twilio/status`
   - **HTTP Method**: `HTTP POST`
   - **Events**: `completed`, `busy`, `no-answer`, `failed`
3. **Realtime Media Streams (Optional Bidirectional Streaming)**:
   - **Stream WebSocket URL**: `wss://<your-render-backend-url>.onrender.com/api/v1/voice/twilio/media-stream`

---

## 4. Post-Deployment Verification Checklist

1. [ ] **Health Endpoint**: `GET https://<render-url>/api/v1/health` returns `{"status": "healthy", "database": "connected"}`.
2. [ ] **Database Seeding**: The authoritative database automatically seeds initial DLAO officers and 20 demo cases on first boot.
3. [ ] **WebSocket Stream**: Open dashboard on Vercel and verify the `LIVE` pill displays green.
4. [ ] **Bilingual Switch**: Toggle between `বাংলা` and `EN` — verify zero reload and instant translation.
5. [ ] **Simulated Voice Test**: Open the **Voice Helpline** tab and complete a test turn to confirm immediate persistence without incurring Twilio billing.
