---
name: testing-and-release
description: Testing standards, state machine verification, CI test suites, Render deployment configuration, and Vercel release checklists.
---

# Testing & Release Engineering

## 1. Test Suite Invariants
Before merging or deploying any backend code, the automated test suite must execute and pass 100%:
- **State Machine Exhaustive Coverage**: Every valid transition (`NEW -> AI_INTAKE -> PENDING_HUMAN_REVIEW -> VERIFIED -> PANEL_LAWYER_QUEUE -> LAWYER_REVIEW`, plus `NEEDS_INFORMATION` and `REJECTED`) must have dedicated test assertions.
- **Negative Gate Testing**: Must explicitly assert that:
  1. Automated AI roles receive `403 Forbidden` if attempting to verify or assign cases.
  2. Citizens receive `403 Forbidden` if attempting to access case review queues or assign advocates.
  3. Direct state skips (e.g., `NEW -> PANEL_LAWYER_QUEUE`) are rejected with `400 Bad Request` or `422 Unprocessable Entity`.
- **Audit Log Verification**: Every state mutation, priority change, or note addition must verify that an immutable `AuditLog` row was created in the database transaction.

## 2. Test Execution Command
```bash
# Run pytest with coverage across all backend test modules
pytest tests/ -v --tb=short
```

## 3. Render Deployment Specification (Backend)
- **Runtime**: Python 3.12+ (or 3.14 compatible)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/api/v1/health` (Must return HTTP 200 with database status `healthy`)
- **Environment Variables Required on Render**:
  - `DATABASE_URL` (Internal PostgreSQL connection string)
  - `SECRET_KEY` (Strong 256-bit secret)
  - `GEMINI_API_KEY`
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `CORS_ORIGINS` (Comma-separated Vercel production and preview URLs)

## 4. Vercel Deployment Specification (Frontend)
- **Framework**: Next.js / Vite React
- **Build Command**: `npm run build`
- **Output Directory**: `.next` or `dist`
- **Public Environment Variables on Vercel**:
  - `NEXT_PUBLIC_API_BASE_URL` (Render backend URL, e.g. `https://dlas-backend.onrender.com`)
  - `NEXT_PUBLIC_WS_BASE_URL` (WebSocket URL, e.g. `wss://dlas-backend.onrender.com/ws`)
- **Security Check**: Verify that neither `GEMINI_API_KEY` nor `TWILIO_AUTH_TOKEN` is present in Vercel environment variables.
