import pytest
from app.services.identity_provider import (
    MockIdentityProvider,
    FutureAuthorisedIdentityProvider,
    get_identity_provider,
    DISCLAIMER_NOTICE,
)
from app.services.ai_intake_mapper import (
    calculate_application_completeness,
    extract_entities_from_spoken_transcript,
)
from app.models.intake_application import ApplicationCompleteness, FieldProvenance
from app.models.case import LegalCategory


def test_mock_identity_provider_demo_records():
    """
    Verify MockIdentityProvider returns 10-20 fictional records with demo labels.
    """
    provider = MockIdentityProvider()
    records = provider.list_demo_records()
    assert 10 <= len(records) <= 20
    for r in records:
        assert r["is_demo_data"] is True
        assert r["disclaimer"] == DISCLAIMER_NOTICE
        assert "nid_number" in r
        assert "applicant_name" in r
        assert "phone_number" in r
        assert "monthly_income_bdt" in r


def test_mock_identity_provider_lookup_by_phone():
    """
    Simulates lookup: caller phone -> demo identity provider -> fictional NID -> applicant profile
    """
    provider = MockIdentityProvider()
    profile = provider.lookup_by_phone("+8801711000001")
    assert profile is not None
    assert profile["applicant_name"] == "Shahnaz Akter"
    assert profile["nid_number"] == "19922612345678901"
    assert profile["is_demo_data"] is True
    assert profile["provenance"] == FieldProvenance.MOCK_IDENTITY
    assert profile["present_district"] == "Dhaka"


def test_mock_identity_provider_unknown_phone():
    provider = MockIdentityProvider()
    profile = provider.lookup_by_phone("+8801999999999")
    assert profile is None


def test_future_authorised_provider_raises_not_implemented():
    """
    Strict security rule: Never fabricate or fake government integration.
    """
    provider = FutureAuthorisedIdentityProvider()
    with pytest.raises(NotImplementedError):
        provider.lookup_by_phone("+8801711000001")

    with pytest.raises(NotImplementedError):
        provider.lookup_by_nid("19922612345678901")


def test_ai_extraction_strict_null_preservation():
    """
    The AI must not invent missing fields.
    Missing information must remain null / unknown.
    """
    spoken_transcript = (
        "আমার নাম জামাল উদ্দিন। আমি ঢাকার মিরপুরে থাকি। "
        "আমার জমি জোর করে দখল করেছে রফিকুল ইসলাম। "
        "আমার মাসিক আয় ১২০০০ টাকা।"
    )
    extracted, provenances = extract_entities_from_spoken_transcript(
        transcript=spoken_transcript,
        caller_phone="+8801711999888"
    )

    # Stated fields are extracted
    assert extracted["phone_number"] == "+8801711999888"
    assert extracted["present_district"] == "Dhaka"
    assert extracted["legal_category"] == LegalCategory.LAND_PROPERTY
    assert extracted["monthly_income_bdt"] == 12000.0
    assert extracted["opposing_party_name"] == "রফিকুল ইসলাম"
    assert extracted["applicant_name"] == "জামাল উদ্দিন"

    # Provenance tags
    assert provenances["phone_number"]["source"] == FieldProvenance.CALLER_REPORTED
    assert provenances["legal_category"]["source"] == FieldProvenance.AI_EXTRACTED
    assert provenances["monthly_income_bdt"]["source"] == FieldProvenance.AI_EXTRACTED
    assert provenances["annual_income_bdt"]["source"] == FieldProvenance.SYSTEM_DERIVED

    # Unstated fields MUST remain absent / null (NO hallucination!)
    assert "nid_number" not in extracted
    assert "mother_name" not in extracted
    assert "education_level" not in extracted
    assert "spouse_name" not in extracted


def test_completeness_calculation_statuses():
    """
    Tests completeness evaluation:
    - COMPLETE
    - PARTIALLY_COMPLETE
    - MISSING_REQUIRED_INFORMATION
    """
    # 1. Missing mandatory field (missing monthly_income_bdt and opposing_party_name)
    sparse_data = {
        "applicant_name": "Rahim",
        "phone_number": "+8801711000000",
        "present_district": "Chittagong",
        "legal_category": "LAND_PROPERTY",
        "grievance_description": "Boundary dispute with neighbor",
    }
    status, score, missing, follow_ups = calculate_application_completeness(sparse_data)
    assert status == ApplicationCompleteness.MISSING_REQUIRED_INFORMATION
    assert "monthly_income_bdt" in missing
    assert "opposing_party_name" in missing
    assert len(follow_ups) > 0
    # Check bilingual question
    income_q = next((q for q in follow_ups if q["field"] == "monthly_income_bdt"), None)
    assert income_q is not None
    assert "আয়" in income_q["question_bn"]
    assert "income" in income_q["question_en"]

    # 2. All mandatory fields present, but missing some recommended fields
    partial_data = {
        "applicant_name": "Rahim",
        "phone_number": "+8801711000000",
        "present_district": "Chittagong",
        "monthly_income_bdt": 12000.0,
        "legal_category": "LAND_PROPERTY",
        "grievance_description": "Boundary dispute with neighbor",
        "opposing_party_name": "Karim Mia",
    }
    status, score, missing, follow_ups = calculate_application_completeness(partial_data)
    assert status == ApplicationCompleteness.PARTIALLY_COMPLETE
    assert len(missing) == 0

    # 3. Complete application with all mandatory and recommended fields
    full_data = {
        "applicant_name": "Rahim",
        "phone_number": "+8801711000000",
        "present_district": "Chittagong",
        "present_upazila": "Pahartali",
        "monthly_income_bdt": 12000.0,
        "legal_category": "LAND_PROPERTY",
        "grievance_description": "Boundary dispute with neighbor",
        "opposing_party_name": "Karim Mia",
        "opposing_party_address": "Saraipara, Pahartali",
        "nid_number": "5501234567",
        "incident_date": "2026-01-15",
        "relief_sought": "Legal notice and court partition suit",
        "occupation": "Day Laborer",
        "marital_status": "MARRIED",
    }
    status, score, missing, follow_ups = calculate_application_completeness(full_data)
    assert status == ApplicationCompleteness.COMPLETE
    assert score >= 90.0
    assert len(missing) == 0


def test_api_intake_demo_identities_and_lookup(client):
    """
    Test REST endpoint for demo identities listing and lookup.
    """
    # 1. List demo records
    list_res = client.get("/api/v1/intake/demo-identities")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["is_demo_data"] is True
    assert list_data["total"] >= 10

    # 2. Lookup existing demo phone
    demo_phone = list_data["records"][0]["phone_number"]
    lookup_res = client.post(f"/api/v1/intake/demo-lookup?phone_number={demo_phone}")
    assert lookup_res.status_code == 200
    profile = lookup_res.json()
    assert profile["is_demo_data"] is True
    assert "DEMO IDENTITY DATA" in profile["disclaimer"]

    # 3. Lookup unknown phone returns 404
    unknown_res = client.post("/api/v1/intake/demo-lookup?phone_number=%2B8801999999999")
    assert unknown_res.status_code == 404


def test_api_intake_ai_extraction_endpoint(client):
    """
    Test REST endpoint for AI-assisted intake extraction.
    """
    payload = {
        "raw_transcript": "আমার নাম ফাতেমা বেগম। সিলেটে থাকি। স্বামী খোরপোশ দেয় না। অপরপক্ষ জাহিরুল হক। মাসিক আয় ৮৫০০ টাকা।",
        "caller_phone": "+8801911000003"
    }
    res = client.post("/api/v1/intake/extract-ai", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["extracted_fields"]["legal_category"] == LegalCategory.FAMILY_MATRIMONIAL
    assert data["extracted_fields"]["present_district"] == "Sylhet"
    assert data["extracted_fields"]["monthly_income_bdt"] == 8500.0
    assert "field_provenances" in data
    assert data["completeness_status"] in [ApplicationCompleteness.COMPLETE, ApplicationCompleteness.PARTIALLY_COMPLETE]


def test_api_create_and_retrieve_intake_application(client, dlao_token, dlao_headers):
    """
    Test creating a structured DBLA intake application and querying it back.
    """
    app_payload = {
        "applicant_name": "Shahnaz Akter",
        "applicant_name_bn": "শাহনাজ আক্তার",
        "gender": "FEMALE",
        "phone_number": "+8801711000001",
        "nid_number": "19922612345678901",
        "nid_type": "LEGACY_17",
        "nid_verified": True,
        "occupation": "Garment Factory Inspector",
        "monthly_income_bdt": 12500.0,
        "present_district": "Dhaka",
        "present_upazila": "Mirpur",
        "opposing_party_name": "Karnaphuli Garments Management",
        "legal_category": "LABOUR_EMPLOYMENT",
        "case_title": "Unlawful RMG Termination & Unpaid Wages",
        "grievance_description": "Terminated without notice or 4 months unpaid severance wages.",
        "relief_sought": "Recovery of statutory unpaid wages and compensation under Labour Act 2006",
        "field_provenances": {
            "nid_number": {"source": FieldProvenance.MOCK_IDENTITY, "timestamp": "2026-09-10T10:00:00Z", "confidence": 1.0},
            "applicant_name": {"source": FieldProvenance.MOCK_IDENTITY, "timestamp": "2026-09-10T10:00:00Z", "confidence": 1.0},
            "grievance_description": {"source": FieldProvenance.CALLER_REPORTED, "timestamp": "2026-09-10T10:00:00Z", "confidence": 1.0},
        }
    }

    create_res = client.post("/api/v1/intake/applications", json=app_payload, headers=dlao_headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["id"] > 0
    assert created["case_id"] > 0
    assert created["tracking_id"].startswith("DLAS-")
    assert created["completeness_status"] in [ApplicationCompleteness.COMPLETE, ApplicationCompleteness.PARTIALLY_COMPLETE]

    # Query back
    get_res = client.get(f"/api/v1/intake/applications/{created['id']}", headers=dlao_headers)
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["applicant_name"] == "Shahnaz Akter"
    assert retrieved["field_provenances"]["nid_number"]["source"] == FieldProvenance.MOCK_IDENTITY
