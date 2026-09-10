---
name: legal-aid-intake
description: Guidelines for Bangladesh legal aid intake, eligibility criteria, mock NID identity adapter, legal dispute classification, and human verification gates.
---

# Legal Aid Intake & Eligibility Engine

## 1. Legal Framework: Legal Aid Services Act 2000
The Digital Legal Aid System serves eligible citizens under the National Legal Aid Services Act (আইনগত সহায়তা প্রদান আইন, ২০০০) administered by the National Legal Aid Services Organization (NLASO) and District Legal Aid Committees (DLAC):
- **Eligible Beneficiaries**:
  - Economically disadvantaged citizens (monthly household income below national/gazetted threshold, typically BDT 15,000–20,000/month or destitute criteria).
  - Destitute women, widows, and victims of domestic violence under Domestic Violence (Prevention and Protection) Act 2010.
  - Victims of violence against women and children under Nari O Shishu Nirjaton Daman Ain 2000 (নারী ও শিশু নির্যাতন দমন আইন, ২০০০).
  - Insolvent garment and informal sector workers seeking unpaid wages under Bangladesh Labour Act 2006.
  - Under-trial prisoners unable to engage defense counsel.
  - Disabled or incapacitated persons.

## 2. Mock / Demo Identity Adapter (NID Verification)
> **CRITICAL RULE**: Do NOT invent fictional government API endpoints or claim live integration with the Bangladesh Election Commission / Porichoy NID server.

DLAS implements an explicit **`MockNIDAdapter`**:
- **Format Validation**:
  - 10-digit Smart NID (`^[0-9]{10}$`)
  - 17-digit Legacy NID (`^[0-9]{17}$` or 13-digit prepended with 4-digit birth year)
- **Demo Mode Behavior**:
  - Simulates name, father/mother's name, date of birth, and district based on seedable test records or deterministic checksums.
  - Always marks verification metadata with `verification_mode: "DEMO_SIMULATED"` and `disclaimer: "Simulated for demonstration; no actual government database connection."`

## 3. Legal Classification Categories
Every intake record must be classified into one of the standardized Bangladesh legal domains:
1. `FAMILY_MATRIMONIAL`: Maintenance (খোরপোশ), Dower (দেনমোহর), Child Custody (অভিভাবকত্ব), Divorce registration.
2. `LAND_PROPERTY`: Land demarcation, partition suits (বাটোয়ারা মামলা), illegal dispossession (বেদখল), tenancy disputes.
3. `DOMESTIC_VIOLENCE_DOWRY`: Domestic violence protection orders, Dowry Prohibition Act 2018 violations.
4. `LABOUR_EMPLOYMENT`: Unpaid wages, wrongful dismissal, maternity benefits for RMG workers.
5. `CRIMINAL_DEFENSE_BAIL`: Indigent defense, bail applications for under-trial prisoners.
6. `CIVIL_GENERAL`: Money suits, breach of contract, succession certificates.

## 4. Intake Pipeline & AI Assistant Constraints
- **Multi-channel Ingestion**: Web portal form, Twilio IVR voice recording/transcript, SMS, or direct office counter entry.
- **AI Processing (Gemini)**:
  - Extracts key entities: Claimant Name, Phone, District/Upazila, Income Bracket, Narrative Summary, Identified Legal Domain.
  - Prepares bilingual summary (Bangla and English).
  - Computes an advisory preliminary urgency score (`LOW`, `MEDIUM`, `HIGH`, `EMERGENCY`).
- **Inviolable Gate**: Case state upon AI completion is **ALWAYS `PENDING_HUMAN_REVIEW`**.
- **Human Gate**: Only a human District Legal Aid Officer (DLAO) or authorized legal officer may inspect the evidence, review applicant income declarations, and click `Verify Case` to transition to `VERIFIED` and `PANEL_LAWYER_QUEUE`.
