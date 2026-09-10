# DLAS Judge & Evaluator Demonstration Checklist

This checklist provides a structured, verifiable walkthrough for evaluating the **Digital Legal Aid System (DLAS)** across all 10 core scenarios (A through J), security boundaries, and bilingual capabilities.

---

## Pre-Loaded Demo Credentials

| Role | Email | Password | Primary Mission |
| :--- | :--- | :--- | :--- |
| **DLAO Officer (Dhaka)** | `dlao.dhaka@dlas.gov.bd` | `DlaoPass2026!` | Human Verification Gate, Priority Escalation, Panel Dispatch |
| **DLAO Officer (Chittagong)** | `dlao.ctg@dlas.gov.bd` | `DlaoPass2026!` | Multi-District Case Review & Regional Triage |
| **Panel Lawyer (Land)** | `lawyer.nazmul@dlas.gov.bd` | `LawyerPass2026!` | Advocate Intake Queue, Case Review, Realtime Notifications |
| **Panel Lawyer (Family)** | `lawyer.farhana@dlas.gov.bd` | `LawyerPass2026!` | Domestic Violence & Maintenance Legal Aid Defense |
| **Citizen Applicant** | `applicant.shahnaz@gmail.com` | `CitizenPass2026!` | Personal Case Status Tracking & Document Submission |

---

## Scenario-by-Scenario Evaluation Script

### 🏛️ Scenario A: Judicial Verification & Advocate Dispatch
1. **Login**: Sign in as `dlao.dhaka@dlas.gov.bd`.
2. **Review Seeded Cases**: Dashboard loads 20 seeded Bangladesh legal aid cases (`DLAS-2026-0001` through `DLAS-2026-0020`).
3. **Open Case**: Click on any case with status `PENDING_HUMAN_REVIEW` (e.g., `DLAS-2026-0016`).
4. **Execute Verification**: Click **"যাচাই করুন / Verify Eligibility"**. Enter statutory notes (e.g., *"Merits and income threshold verified under Legal Aid Act 2000"*).
5. **Verify State Transition**:
   - Case moves authoritatively to `PANEL_LAWYER_QUEUE`.
   - Audit Log immediately records `CASE_VERIFIED` with timestamp and officer name.
   - An idempotent notification is dispatched to panel advocate `lawyer.nazmul@dlas.gov.bd`.

---

### 🎙️ Scenario B & F: Bangla Voice Helpline (Incremental Persistence & Safety Triage)
1. **Navigate to Voice Helpline**: Click **"ভয়েস হেল্পলাইন (টেলিফোনি) / Voice Helpline"** in the top navigation.
2. **Initiate Inbound Call**: Click **"ইনবাউন্ড কল সিমুলেশন শুরু (১৬৪৩০)"**.
3. **Question Q0 (Consent)**:
   - System speaks statutory greeting in natural Bangladesh Bangla:
     *"জাতীয় আইনগত সহায়তা হেল্পলাইনে স্বাগতম... নিজের সমস্যাটি সম্পর্কে কথা বলতে সম্মত?"*
   - Click **"Send Safe Sample Answer"** or speak into the microphone: *"হ্যাঁ, আমি কথা বলতে সম্মত।"*
   - Observe **Immediate Persistence**: The answer appears in the feed with `PERSISTED IMMEDIATELY IN DB` badge.
4. **Question Q1 (Grievance Narrative)**:
   - System asks: *"আপনার সমস্যাটি সংক্ষেপে বলবেন?"*
   - Send grievance answer. Legal category is automatically identified.
5. **Question Q2 (Immediate Danger & Abuser Proximity)**:
   - System asks: *"আপনি কি এই মুহূর্তে নিরাপদে আছেন? আপনার স্বামী বা যিনি আপনাকে হুমকি দিচ্ছেন, তিনি কি এখন আপনার কাছে আছেন?"*
   - Click **"⚠ Send High-Risk/Danger Sample"**:
     *"আমি একদম নিরাপদ নই, সে এখন দা নিয়ে আমার সামনে ঘরে বসে আছে এবং মারধর করছে!"*
   - **Triage Result**: System immediately triggers `CURRENT_VIOLENCE_OR_THREAT`, `ABUSER_PRESENT`, and `IMMEDIATE_DANGER` flags. Suggested priority jumps to `EMERGENCY`.
6. **Question Q3 (Child Risk & Callback Protocol)**:
   - Send: *"আমার ছোট সন্তান ঝুঁকিতে আছে, দুপুরে যোগাযোগ করবেন।"*
   - System extracts child vulnerability flag (`CHILD_AT_RISK`) and registers safe callback time (`Afternoon`).
7. **Call Termination**:
   - Status transitions to `PENDING_HUMAN_REVIEW` with `URGENT_REVIEW` escalation.
   - Click **"Open Case in Review Panel"** to inspect the aggregated narrative and safety badges.

---

### ⚡ Scenario C: Priority Elevation & Multi-Session Sync
1. Open two browser sessions side-by-side:
   - **Window 1**: Judge DLAO logged in.
   - **Window 2**: Observer or Panel Lawyer logged in.
2. In Window 1, open a case and change priority from `MEDIUM` to `EMERGENCY`.
3. Observe Window 2: Without page reload, the priority badge instantly shifts to `EMERGENCY` via WebSocket event `CASE_UPDATED`.
4. Refresh Window 2: The updated priority remains persistent in the authoritative database.

---

### 📋 Scenario D: Return for Missing Information
1. As DLAO, open a case in `PENDING_HUMAN_REVIEW`.
2. Select **"তথ্য প্রয়োজন / Request Information"**.
3. Submit required document note (e.g., *"Missing certified land deed"*).
4. Verify:
   - Status changes to `NEEDS_INFORMATION`.
   - **Zero lawyer notifications are dispatched** (lawyer queue is NOT prematurely polluted).

---

### 🛡️ Scenario E: Single Notification Idempotency
1. Complete human verification on a case.
2. Check notifications under `lawyer.nazmul@dlas.gov.bd`.
3. Verify exactly **one** assignment notification is recorded.
4. Refresh the page 5 times — verify no duplicate notifications are created.

---

### 💾 Scenario G: Durability Across Backend Restarts
1. Create or verify a case.
2. Restart the backend service (`uvicorn` reload or process restart).
3. Query the cases and audit logs.
4. All seeded cases, newly created records, audit trails, and notifications remain fully intact.

---

### 🔌 Scenario H: WebSocket Disconnect & Reconnect Resilience
1. Open the **System Diagnostics** tab.
2. Disconnect your network or trigger WebSocket closure.
3. Observe the top pill: Displays **"Reconnecting..."** with backoff timer.
4. Reconnect network: System fetches missed events via `/api/v1/events/since`, reconciles state, and resumes live stream without duplicate alerts.

---

### 🚫 Scenario I & J: Security & Role Boundaries (Hostile Testing)
1. **AI Autonomous Overreach Prevention**:
   - Automated AI accounts cannot call `/api/v1/cases/{id}/verify`, `/reject`, or `/archive`. The backend returns `403 Forbidden`.
   - Judicial decisions require a human DLAO officer token.
2. **Panel Lawyer Modification Block**:
   - Panel lawyers attempting to verify cases receive `403 Forbidden`.
3. **Unauthenticated Access**:
   - Calling `/api/v1/cases` without a Bearer token returns `401 Unauthorized`.
4. **Zero Client Secret Exposure**:
   - Inspect all frontend assets in DevTools: No `TWILIO_AUTH_TOKEN`, `GEMINI_API_KEY`, or database credentials exist on the client side.

---

### 🌐 Bilingual Experience (Bangladesh Standard EN ↔ বাংলা)
1. Click **"বাংলা"** or **"EN"** on the header toggle.
2. The entire interface changes language instantly:
   - Navigation links
   - Table column headers
   - Status and priority pills
   - Form inputs and placeholders
   - Modal action buttons
3. **Zero page reload occurs**. The user's active view, filter selection, and current case remain preserved.
