---
name: security-and-secrets
description: Security posture, secret isolation, role-based access control, environment variable safety, and audit standards for DLAS.
---

# Security & Secrets Management

## 1. Zero-Trust Secrets Isolation
- **Client Separation Rule**: No Gemini API keys, Twilio Auth Tokens, Database credentials, or JWT signing secrets may EVER exist in frontend code, git commits, or browser bundles.
- **Frontend Variables**: Only variables prefixed with `NEXT_PUBLIC_` (pointing to public endpoints like API URL or WebSocket URL) are allowed on the client.
- **Backend Isolation**: All sensitive operations (AI parsing, SMS/Call dispatch, database transactions, password verification) execute solely within the FastAPI backend environment.

## 2. Environment Variables & Git Hygiene
- **Never Commit Secrets**: `.env` and all `.env*.local` variants are strictly blacklisted in `.gitignore`.
- **Never Print Secrets**: Agents, terminal logs, and system error responses must NEVER output secret values or raw environment contents.
- **Inspection Protocol**: When verifying environment variable configuration, check key presence or use masked indicators (e.g., `GEMINI_API_KEY is configured (length: 39)`), never printing the value.
- **Template Standard**: `.env.example` contains only variable names, descriptive comments, and non-sensitive defaults.

## 3. Authentication & Role-Based Access Control (RBAC)
Every backend endpoint must enforce strict role verification using JWT bearer tokens:
| Role | Capabilities | Restrictions |
| :--- | :--- | :--- |
| **`dlao_officer`** (District Legal Aid Officer) | Verify cases, assign panel lawyers, reject/request info, view audit logs, trigger archiving | Authoritative administrative role |
| **`panel_lawyer`** | View assigned cases, submit case status updates, add legal notes | Cannot verify or assign other lawyers |
| **`applicant`** (Citizen) | Submit intake, view self case status, provide requested information | Cannot view internal notes or other applicants' cases |
| **`system_ai`** (Gemini/Twilio Service) | Create initial intake record, enrich intake summary | **FORBIDDEN** from verifying, assigning, rejecting, or deleting |

## 4. Audit Logging & Non-Repudiation
Every state change, priority adjustment, lawyer assignment, and document attachment must generate an immutable audit log record:
- `timestamp`: UTC ISO timestamp
- `actor_id`: User ID or system service identifier
- `actor_role`: `dlao_officer`, `panel_lawyer`, or `system`
- `case_id`: UUID/Integer foreign key
- `action`: Specific action code (e.g., `CASE_VERIFIED`, `PRIORITY_CHANGED`)
- `previous_state` & `new_state`: Enforced schema state snapshot
- `notes`: Justification or human verification comment
- `ip_address`: Client IP address

## 5. Defense Against Vulnerabilities
- **SQL Injection**: Strictly forbidden from writing raw SQL strings with interpolation; use SQLAlchemy ORM or parameterized Core statements.
- **Cross-Site Scripting (XSS)**: Sanitize citizen-submitted text fields on input and render as plain text or properly sanitized markdown.
- **Mass Assignment**: Pydantic schemas must strictly define allowed fields for intake vs update endpoints.
