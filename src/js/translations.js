/**
 * DLAS Bilingual Localization Dictionary (Bangla & English)
 * Complete interface translations for Bangladesh Digital Legal Aid.
 */
const TRANSLATIONS = {
  en: {
    // Branding & Header
    gov_title: "Government of the People's Republic of Bangladesh",
    app_title: "Digital Legal Aid System",
    app_acronym: "DLAS",
    tagline: "National Legal Aid Services Authority (NLASO)",
    lang_switch: "বাংলা",

    // Navigation
    nav_dashboard: "Dashboard Overview",
    nav_queue: "Live Case Queue",
    nav_lawyer_queue: "Panel Lawyer Queue",
    nav_audit: "Audit Trail",
    nav_health: "System Diagnostics",
    nav_notifications: "Notifications",
    nav_settings: "Settings & Language",
    nav_logout: "Sign Out",

    // Authentication
    login_title: "Officer & Advocate Sign In",
    login_subtitle: "Access the authoritative judicial legal-aid dashboard",
    email_label: "Official Email Address",
    password_label: "Password",
    sign_in_btn: "Sign In to DLAS",
    quick_login_hint: "Demo Quick Sign-In Options:",
    role_dlao_dhaka: "Mahmudur Rahman (DLAO Dhaka)",
    role_dlao_ctg: "Fatema Zohra (DLAO Chittagong)",
    role_lawyer_nazmul: "Adv. Nazmul Huda (Land Specialist)",
    role_citizen: "Shahnaz Akter (Citizen Applicant)",
    login_error: "Authentication failed. Please verify credentials.",

    // Dashboard Metrics
    kpi_total_cases: "Total Registered Cases",
    kpi_pending_review: "Pending DLAO Verification",
    kpi_verified: "Verified & Approved",
    kpi_urgent: "Emergency & Urgent Matters",
    kpi_lawyer_queue: "Ready for Advocate Dispatch",
    kpi_latest_activity: "Authoritative Transaction Feed",
    quick_actions: "Expedited Workflows",
    btn_new_intake: "Register Walk-in Intake",

    // Case Statuses
    status_NEW: "New Intake",
    status_AI_INTAKE: "AI Intake Parsing",
    status_PENDING_HUMAN_REVIEW: "Pending Human Review",
    status_VERIFIED: "Verified & Approved",
    status_PANEL_LAWYER_QUEUE: "Panel Lawyer Queue",
    status_LAWYER_REVIEW: "Under Legal Review",
    status_NEEDS_INFORMATION: "Information Needed",
    status_REJECTED: "Application Rejected",
    status_ARCHIVED: "Archived",

    // Urgency Priorities
    prio_LOW: "Low",
    prio_MEDIUM: "Medium",
    prio_HIGH: "High",
    prio_EMERGENCY: "Emergency",

    // Legal Categories
    cat_FAMILY_MATRIMONIAL: "Family & Matrimonial",
    cat_LAND_PROPERTY: "Land & Property Disputes",
    cat_DOMESTIC_VIOLENCE_DOWRY: "Domestic Violence & Dowry",
    cat_LABOUR_EMPLOYMENT: "Labour & Employment",
    cat_CRIMINAL_DEFENSE_BAIL: "Criminal Defense & Bail",
    cat_CIVIL_GENERAL: "Civil & General Claims",

    // Case Queue View
    search_placeholder: "Search by Tracking ID, applicant name, phone, or NID...",
    filter_status: "Filter Status",
    filter_priority: "Filter Urgency",
    filter_category: "Filter Legal Domain",
    all_statuses: "All Statuses",
    all_priorities: "All Priorities",
    all_categories: "All Categories",
    col_tracking_id: "Tracking ID",
    col_applicant: "Applicant & Contact",
    col_category: "Dispute Domain",
    col_district: "Jurisdiction",
    col_priority: "Urgency",
    col_status: "Lifecycle State",
    col_action: "Actions",
    btn_inspect: "Inspect Matter",
    no_cases_found: "No legal aid matters match the current filter criteria.",

    // Case Detail View
    back_to_queue: "Back to Live Queue",
    case_overview: "Matter Overview",
    applicant_details: "Applicant Profile & Eligibility",
    full_name: "Full Name",
    phone_number: "Phone Number",
    nid_number: "National ID (NID)",
    nid_verified_badge: "Simulated NID Verified",
    nid_unverified_badge: "NID Verification Pending",
    monthly_income: "Self-Reported Household Income",
    jurisdiction: "District & Upazila",
    intake_channel: "Ingestion Channel",
    case_narrative: "Grievance Narrative",
    ai_advisory_box: "Google Gemini 2.0 AI Intake Assessment (Advisory)",
    ai_summary_label: "Extracted Legal Summary",
    ai_urgency_label: "Assessed Urgency Score",
    ai_disclaimer: "Advisory AI output only. Automated verification or assignment is prohibited.",
    judicial_notes: "DLAO Judicial Review Assessment",
    assigned_counsel: "Appointed Panel Advocate",
    no_counsel_yet: "No advocate appointed yet. Matter is in panel queue.",
    lifecycle_timeline: "Procedural Milestone Timeline",

    // Actions & Verification Panel
    btn_verify: "Verify & Route to Lawyer Queue",
    btn_request_info: "Request Additional Information",
    btn_reject: "Reject Application",
    btn_change_priority: "Adjust Urgency Priority",
    btn_assign_lawyer: "Appoint Panel Advocate",
    btn_archive_matter: "Archive Resolved Matter",
    btn_listen: "Audio Readout",

    // Modals
    modal_verify_title: "Human DLAO Verification Gate",
    modal_verify_desc: "Confirm statutory eligibility under Legal Aid Services Act 2000. This will advance the case to the Panel Lawyer Queue.",
    notes_label: "Judicial Verification Findings & Order",
    notes_placeholder: "Enter official review findings, eligibility criteria met, and directives...",
    route_to_queue_checkbox: "Immediately place in active Panel Lawyer Queue",
    modal_request_info_title: "Request Additional Documentation",
    request_info_desc: "Inform applicant of missing documents (e.g. Khatian copies, pay slips, medical certificates).",
    info_needed_label: "Specific Information or Documents Required",
    modal_reject_title: "Statutory Rejection of Legal Aid",
    reject_reason_label: "Statutory Grounds for Rejection",
    modal_assign_title: "Assign Panel Advocate",
    select_lawyer_label: "Select Verified Panel Advocate",
    lawyer_workload: "Active Case Load",
    modal_archive_title: "Authorized Case Archival",
    archive_confirm_label: "I confirm explicit human judicial authorization to archive this record.",
    archive_reason_label: "Archival Justification",
    btn_cancel: "Cancel",
    btn_submit: "Submit Order",

    // Notifications View
    notifications_title: "Official Notifications & Alerts",
    no_notifications: "You are all caught up. No unread notifications.",
    btn_mark_read: "Mark Read",

    // Audit Log View
    audit_title: "Authoritative Transaction Audit Trail",
    audit_subtitle: "Immutable append-only record of all case state transitions and orders",
    col_timestamp: "UTC Timestamp",
    col_actor: "Authoritative Actor",
    col_case: "Case Ref",
    col_event: "Action / Event",
    col_transition: "State Mutation",
    col_notes: "Order / Justification",

    // Diagnostics / Health
    health_title: "System Diagnostics & Telemetry",
    backend_status: "FastAPI Backend Service",
    db_status: "Authoritative Persistent Database",
    ws_status: "Realtime WebSocket Hub",
    ws_connected: "Connected & Receiving Live Telemetry",
    ws_reconnecting: "Reconnecting to Realtime Stream...",
    ws_disconnected: "Disconnected (Using Fallback Polling)",
    btn_recheck_health: "Refresh Diagnostics",

    // Settings
    settings_title: "System Settings & Preferences",
    interface_lang: "Default Interface Language",
    active_profile: "Active User Profile",
    sound_alerts: "Audible Notification Chimes on Emergency Events",
    api_endpoint_config: "Backend API Endpoint Override",

    // Toast Messages
    toast_success: "Action completed successfully.",
    toast_error: "Operation failed. Please try again.",
    toast_ws_update: "Realtime event received from backend.",
    currency_bdt: "BDT"
  },

  bn: {
    // Branding & Header
    gov_title: "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার",
    app_title: "ডিজিটাল লিগ্যাল এইড সিস্টেম",
    app_acronym: "ডিএলএএস",
    tagline: "জাতীয় আইনগত সহায়তা প্রদান সংস্থা (এনএলএএসও)",
    lang_switch: "English",

    // Navigation
    nav_dashboard: "ড্যাশবোর্ড পর্যালোচনা",
    nav_queue: "লাইভ মামলা সারি",
    nav_lawyer_queue: "প্যানেল আইনজীবী কিউ",
    nav_audit: "অডিট ও নিরীক্ষা লগ",
    nav_health: "সিস্টেম ডায়াগনস্টিকস",
    nav_notifications: "বিজ্ঞপ্তিসমূহ",
    nav_settings: "সেটিংস ও ভাষা",
    nav_logout: "লগআউট",

    // Authentication
    login_title: "কর্মকর্তা ও আইনজীবী প্রবেশদ্বার",
    login_subtitle: "সরকারি আইনগত সহায়তা ব্যবস্থাপনা ড্যাশবোর্ডে প্রবেশ করুন",
    email_label: "দাপ্তরিক ইমেইল ঠিকানা",
    password_label: "পাসওয়ার্ড",
    sign_in_btn: "প্রবেশ করুন",
    quick_login_hint: "ডেমো টেস্ট অ্যাকাউন্টসমূহ:",
    role_dlao_dhaka: "মাহমুদুর রহমান (ডিএলএও ঢাকা)",
    role_dlao_ctg: "ফাতেমা জোহরা (ডিএলএও চট্টগ্রাম)",
    role_lawyer_nazmul: "অ্যাডভোকেট নাজমুল হুদা (ভূমি বিশেষজ্ঞ)",
    role_citizen: "শাহনাজ আক্তার (নাগরিক আবেদনকারী)",
    login_error: "প্রবেশ ব্যর্থ হয়েছে। সঠিক তথ্য প্রদান করুন।",

    // Dashboard Metrics
    kpi_total_cases: "মোট নিবন্ধিত মামলা",
    kpi_pending_review: "কর্মকর্তা যাচাইকরণ অপেক্ষমাণ",
    kpi_verified: "যাচাইকৃত ও অনুমোদিত",
    kpi_urgent: "জরুরি ও অতীব জরুরি মামলা",
    kpi_lawyer_queue: "আইনজীবী নিয়োগের জন্য প্রস্তুত",
    kpi_latest_activity: "সাম্প্রতিক প্রাতিষ্ঠানিক কার্যক্রম",
    quick_actions: "দ্রুত সেবাসমূহ",
    btn_new_intake: "নতুন সরাসরি আবেদন গ্রহণ",

    // Case Statuses
    status_NEW: "নতুন আবেদন",
    status_AI_INTAKE: "এআই তথ্য গ্রহণ চলছে",
    status_PENDING_HUMAN_REVIEW: "কর্মকর্তা যাচাইকরণ অপেক্ষমাণ",
    status_VERIFIED: "যাচাইকৃত ও অনুমোদিত",
    status_PANEL_LAWYER_QUEUE: "প্যানেল আইনজীবী অপেক্ষমাণ তালিকা",
    status_LAWYER_REVIEW: "আইনজীবী পর্যালোচনাধীন",
    status_NEEDS_INFORMATION: "অতিরিক্ত তথ্য তলব",
    status_REJECTED: "আবেদন বাতিল",
    status_ARCHIVED: "আর্কাইভকৃত",

    // Urgency Priorities
    prio_LOW: "সাধারণ",
    prio_MEDIUM: "মাঝারি",
    prio_HIGH: "জরুরি",
    prio_EMERGENCY: "অতীব জরুরি",

    // Legal Categories
    cat_FAMILY_MATRIMONIAL: "পারিবারিক ও দেনমোহর",
    cat_LAND_PROPERTY: "ভূমি ও সম্পত্তি সংক্রান্ত বিরোধ",
    cat_DOMESTIC_VIOLENCE_DOWRY: "পারিবারিক সহিংসতা ও যৌতুক",
    cat_LABOUR_EMPLOYMENT: "শ্রম ও কর্মসংস্থান",
    cat_CRIMINAL_DEFENSE_BAIL: "ফৌজদারি ও জামিন সহায়তা",
    cat_CIVIL_GENERAL: "দেওয়ানি ও অন্যান্য দাবি",

    // Case Queue View
    search_placeholder: "ট্র্যাকিং আইডি, আবেদনকারীর নাম, মোবাইল বা এনআইডি দিয়ে খুঁজুন...",
    filter_status: "মামলার অবস্থা",
    filter_priority: "অগ্রাধিকার স্তর",
    filter_category: "আইনি ক্ষেত্র",
    all_statuses: "সকল অবস্থা",
    all_priorities: "সকল অগ্রাধিকার",
    all_categories: "সকল আইনি ক্ষেত্র",
    col_tracking_id: "ট্র্যাকিং নম্বর",
    col_applicant: "আবেদনকারী ও যোগাযোগ",
    col_category: "বিরোধের ধরন",
    col_district: "আওতাধীন জেলা",
    col_priority: "অগ্রাধিকার",
    col_status: "বর্তমান অবস্থা",
    col_action: "কার্যক্রম",
    btn_inspect: "বিস্তারিত দেখুন",
    no_cases_found: "বর্তমান ফিল্টারে কোনো মামলা পাওয়া যায়নি।",

    // Case Detail View
    back_to_queue: "পূর্ববর্তী সারিতে ফিরে যান",
    case_overview: "মামলার পূর্ণ বিবরণ",
    applicant_details: "আবেদনকারীর পরিচিতি ও তথ্য",
    full_name: "পূর্ণ নাম",
    phone_number: "মোবাইল নম্বর",
    nid_number: "জাতীয় পরিচয়পত্র নম্বর",
    nid_verified_badge: "এনআইডি যাচাইকৃত (সিমুলেটেড)",
    nid_unverified_badge: "এনআইডি যাচাই বাকি",
    monthly_income: "ঘোষিত মাসিক পারিবারিক আয়",
    jurisdiction: "জেলা ও উপজেলা",
    intake_channel: "আবেদনের মাধ্যম",
    case_narrative: "অভিযোগের বিস্তারিত বিবরণ",
    ai_advisory_box: "গুগল জেমিনি ২.০ এআই বিশ্লেষণ (পরামর্শমূলক)",
    ai_summary_label: "এআই কর্তৃক নিষ্কাশিত সারাংশ",
    ai_urgency_label: "স্বয়ংক্রিয় জরুরি মানদণ্ড",
    ai_disclaimer: "এআই মতামত শুধুমাত্র পরামর্শমূলক। স্বয়ংক্রিয়ভাবে অনুমোদন বা নিয়োগ নিষিদ্ধ।",
    judicial_notes: "ডিএলএও কর্মকর্তার আইনগত যাচাই ও মন্তব্য",
    assigned_counsel: "নিয়োগপ্রাপ্ত প্যানেল আইনজীবী",
    no_counsel_yet: "এখনও আইনজীবী নিযুক্ত হননি। মামলাটি অপেক্ষমাণ কিউতে আছে।",
    lifecycle_timeline: "মামলা অগ্রগতির ধাপসমূহ",

    // Actions & Verification Panel
    btn_verify: "যাচাই ও আইনজীবী কিউতে প্রেরণ",
    btn_request_info: "অতিরিক্ত তথ্য তলব করুন",
    btn_reject: "আবেদন বাতিল করুন",
    btn_change_priority: "অগ্রাধিকার পরিবর্তন",
    btn_assign_lawyer: "প্যানেল আইনজীবী নিয়োগ করুন",
    btn_archive_matter: "মামলা সমাপ্ত ও আর্কাইভ",
    btn_listen: "শুনুন (অডিও)",

    // Modals
    modal_verify_title: "ডিএলএও কর্মকর্তা যাচাইকরণ গেট",
    modal_verify_desc: "আইনগত সহায়তা প্রদান আইন ২০০০ অনুযায়ী আবেদনকারীর আইনি অধিকার ও অর্থনৈতিক অসচ্ছলতা যাচাই নিশ্চিত করুন।",
    notes_label: "কর্মকর্তার পর্যবেক্ষণ ও আদেশ",
    notes_placeholder: "যাচাইকরণের বিস্তারিত ফলাফল ও সিদ্ধান্ত লিপিবদ্ধ করুন...",
    route_to_queue_checkbox: "সরাসরি প্যানেল আইনজীবী কিউতে প্রেরণ করুন",
    modal_request_info_title: "অতিরিক্ত নথি বা তথ্য তলব",
    request_info_desc: "প্রয়োজনীয় প্রমাণপত্র বা তথ্যের বিবরণ আবেদনকারীকে জানান।",
    info_needed_label: "প্রয়োজনীয় তথ্যের তালিকা",
    modal_reject_title: "আইনগত সহায়তা আবেদন প্রত্যাখ্যান",
    reject_reason_label: "বাতিলের আইনি কারণ",
    modal_assign_title: "প্যানেল আইনজীবী নিয়োগ",
    select_lawyer_label: "তালিকাভুক্ত প্যানেল আইনজীবী নির্বাচন করুন",
    lawyer_workload: "চলমান মামলার সংখ্যা",
    modal_archive_title: "অনুমোদিত মামলা সংরক্ষণ/আর্কাইভ",
    archive_confirm_label: "আমি এই মামলাটি আর্কাইভ করার দাপ্তরিক অনুমোদন প্রদান করছি।",
    archive_reason_label: "আর্কাইভের কারণ",
    btn_cancel: "বাতিল",
    btn_submit: "আদেশ কার্যকর করুন",

    // Notifications View
    notifications_title: "দাপ্তরিক নোটিশ ও সতর্কবার্তাসমূহ",
    no_notifications: "কোনো অপঠিত বিজ্ঞপ্তি নেই।",
    btn_mark_read: "পঠিত হিসেবে চিহ্নিত করুন",

    // Audit Log View
    audit_title: "প্রাতিষ্ঠানিক নিরীক্ষা ও ট্রানজ্যাকশন লগ",
    audit_subtitle: "মামলার প্রতিটি অবস্থার পরিবর্তন ও আদেশের অপরিবর্তনীয় ডিজিটাল রেকর্ড",
    col_timestamp: "সময় (ইউটিসি)",
    col_actor: "দায়িত্বপ্রাপ্ত কর্মকর্তা",
    col_case: "মামলা নং",
    col_event: "পদক্ষেপ / কার্যক্রম",
    col_transition: "অবস্থার পরিবর্তন",
    col_notes: "আদেশ ও মন্তব্য",

    // Diagnostics / Health
    health_title: "সিস্টেম ডায়াগনস্টিকস ও টেলিমেট্রি",
    backend_status: "ফাস্টএপিআই ব্যাকএন্ড সেবা",
    db_status: "স্থায়ী প্রাতিষ্ঠানিক ডাটাবেজ",
    ws_status: "রিয়েলটাইম ওয়েবসকেট হাব",
    ws_connected: "সংযুক্ত ও লাইভ তথ্য সম্প্রচার চালু",
    ws_reconnecting: "লাইভ সার্ভারে পুনরায় সংযোগ স্থাপন চলছে...",
    ws_disconnected: "বিচ্ছিন্ন (ব্যাকআপ মোডে চালু)",
    btn_recheck_health: "পুনরায় পরীক্ষা করুন",

    // Settings
    settings_title: "সিস্টেম সেটিংস ও পছন্দসমূহ",
    interface_lang: "ডিফল্ট ইন্টারফেস ভাষা",
    active_profile: "বর্তমান ব্যবহারকারীর তথ্য",
    sound_alerts: "জরুরি মামলার ক্ষেত্রে শব্দভিত্তিক সতর্কতা",
    api_endpoint_config: "ব্যাকএন্ড এপিআই সার্ভার ঠিকানা",

    // Toast Messages
    toast_success: "কার্যক্রম সফলভাবে সম্পন্ন হয়েছে।",
    toast_error: "অনুরোধটি সম্পন্ন করা যায়নি। পুনরায় চেষ্টা করুন।",
    toast_ws_update: "লাইভ ডাটাবেজ আপডেট গৃহীত হয়েছে।",
    currency_bdt: "৳ (টাকা)"
  }
};

/**
 * Numeral conversion helper (e.g. 15 -> ১৫ in Bangla)
 */
function toBanglaDigits(num) {
  if (num === null || num === undefined) return "";
  const banglaDigits = ["০", "১", "২", "৩", "৪", "৫", "৬", "৭", "৮", "৯"];
  return String(num).replace(/\d/g, (d) => banglaDigits[d]);
}

/**
 * Numeral translation based on active language
 */
function formatNumber(num, lang) {
  if (num === null || num === undefined) return "0";
  return lang === "bn" ? toBanglaDigits(num) : String(num);
}

/**
 * Currency formatter
 */
function formatCurrency(amount, lang) {
  if (amount === null || amount === undefined) return "—";
  const numStr = Math.round(amount).toLocaleString();
  return lang === "bn" ? `${toBanglaDigits(numStr)} ৳` : `BDT ${numStr}`;
}

window.TRANSLATIONS = TRANSLATIONS;
window.toBanglaDigits = toBanglaDigits;
window.formatNumber = formatNumber;
window.formatCurrency = formatCurrency;
