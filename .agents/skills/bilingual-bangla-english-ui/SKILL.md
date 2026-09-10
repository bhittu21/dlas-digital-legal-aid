---
name: bilingual-bangla-english-ui
description: Design principles, typography, localization dictionary, numeral conversions, and accessibility guidelines for bilingual Bangla/English UI.
---

# Bilingual Bangla/English UI & Accessibility

## 1. Bilingual Philosophy & Core Standards
Digital Legal Aid in Bangladesh must be accessible to ordinary citizens from all 64 districts, including rural and semi-literate individuals, while remaining precise for judicial officers and advocates:
- **Primary Public Language**: Bangla (বাংলা) is the default citizen-facing interface language.
- **Secondary Administrative Language**: English is instantly toggleable for legal reporting, audit export, and technical administration.
- **Zero Raw Enums**: Never show raw machine constants like `PENDING_HUMAN_REVIEW` or `CIVIL_GENERAL` to users. Always render translated, human-friendly terms.

## 2. Typography & Font Stacks
To prevent broken glyphs (যুক্তাক্ষর) and awkward kerning:
```css
/* Bangla-optimized Font Stack */
font-family: "Hind Siliguri", "Noto Sans Bengali", "Kalpurush", sans-serif;

/* Primary UI Font Stack (Bilingual) */
font-family: "Inter", "Hind Siliguri", system-ui, -apple-system, sans-serif;
```
- Line-height for Bangla text must be set at least **1.5 to 1.6** (Bangla ascenders and matras like ি, ী, ু, ূ require extra vertical breathing room compared to Latin characters).

## 3. Standard Legal Aid Localization Dictionary
| Concept / Key | English | Bangla (বাংলা) | Contextual Note |
| :--- | :--- | :--- | :--- |
| `app_title` | Digital Legal Aid System | ডিজিটাল লিগ্যাল এইড সিস্টেম | Official title |
| `status_new` | New Ingestion | নতুন আবেদন | Newly registered |
| `status_ai_intake` | AI Intake In Progress | এআই তথ্য গ্রহণ চলছে | Parsing voice/form |
| `status_pending_review` | Pending Verification | কর্মকর্তা যাচাইকরণ অপেক্ষমাণ | DLAO review queue |
| `status_verified` | Verified & Approved | যাচাইকৃত ও অনুমোদিত | Legal eligibility met |
| `status_needs_info` | Additional Info Needed | অতিরিক্ত তথ্য প্রয়োজন | Returned to applicant |
| `status_panel_queue` | Panel Lawyer Queue | প্যানেল আইনজীবী অপেক্ষমাণ তালিকা | Ready for assignment |
| `status_lawyer_review` | Under Legal Review | আইনজীবী পর্যালোচনাধীন | Advocate engaged |
| `status_rejected` | Application Rejected | আবেদন বাতিল | Ineligible / no cause |
| `role_dlao` | District Legal Aid Officer | জেলা লিগ্যাল এইড অফিসার (ডিএলএও) | Authorized verifier |
| `role_lawyer` | Panel Advocate | প্যানেল আইনজীবী | Appointed attorney |
| `currency_symbol` | BDT | ৳ (টাকা) | Bangladesh Taka |

## 4. Numeral Systems & Date Formats
- Provide bidirectional conversion utilities:
  - English digits: `0 1 2 3 4 5 6 7 8 9`
  - Bangla numerals: `০ ১ ২ ৩ ৪ ৫ ৬ ৭ ৮ ৯`
- Format dates according to Bangladesh local standard (DD/MM/YYYY or DD Month YYYY in Bangla, e.g., `১০ সেপ্টেম্বর ২০২৬`).
- Phone numbers must normalize to Bangladesh E.164 (`+8801XXXXXXXXX`) or local format (`01XXXXXXXXX`).

## 5. Low-Literacy & Rural Accessibility
- **Voice Assistance Trigger**: Provide prominent speaker/listen buttons (`শুনুন` / "Listen") for case status and instructions.
- **Visual Status Stepper**: Display a high-contrast visual timeline with easily recognizable icons (Document -> Search -> Shield -> Lawyer -> Gavel).
- **Mobile First**: Minimum touch target size 44x44px. Full responsiveness on low-end Android mobile devices with 3G/4G connections.
