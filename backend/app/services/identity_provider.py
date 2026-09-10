from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from app.config import settings

logger = logging.getLogger("dlas.identity")

# Strict Compliance Notice:
# DO NOT claim that a real public API can derive a person's NID from an arbitrary phone number.
# DO NOT fabricate government integration.
# This entire feature is explicitly labeled as DEMO IDENTITY DATA for hackathon demonstration.

DISCLAIMER_NOTICE = (
    "DEMO IDENTITY DATA - NOT A REAL GOVERNMENT REGISTRY INTEGRATION. "
    "Created strictly for hackathon demonstration. In production, phone numbers do not directly "
    "expose citizen NID or civil registry records without explicit biometric, OTP, or statutory citizen authorization."
)


class IdentityProvider(ABC):
    """
    Abstract identity provider interface for citizen legal-aid eligibility lookups.
    """

    @abstractmethod
    def lookup_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Lookup citizen profile by caller phone number (DEMO ONLY)."""
        pass

    @abstractmethod
    def lookup_by_nid(self, nid: str) -> Optional[Dict[str, Any]]:
        """Lookup citizen profile by National ID (DEMO ONLY)."""
        pass

    @abstractmethod
    def list_demo_records(self) -> List[Dict[str, Any]]:
        """List available demo identity profiles for testing."""
        pass


class MockIdentityProvider(IdentityProvider):
    """
    Mock Identity Provider containing 15 fictional Bangladesh demo identity records.
    Provides structured DBLA application fields for telephone intake simulation.
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = [
            {
                "phone_number": "+8801711000001",
                "applicant_name": "Shahnaz Akter",
                "applicant_name_bn": "শাহনাজ আক্তার",
                "nid_number": "19922612345678901",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1992-05-14",
                "age": 34,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "SECONDARY",
                "occupation": "Garment Factory Quality Inspector",
                "occupation_bn": "পোশাক কারখানা পরিদর্শক",
                "employer_name": "Karnaphuli Garments Ltd",
                "designation": "Quality Inspector",
                "monthly_income_bdt": 12500.0,
                "annual_income_bdt": 150000.0,
                "income_source": "Monthly Wage",
                "is_below_poverty_line": True,
                "father_name": "Late Abdul Jalil",
                "father_name_bn": "মৃত আব্দুল জলিল",
                "mother_name": "Razia Begum",
                "mother_name_bn": "রাজিয়া বেগম",
                "spouse_name": "Md. Rafiqul Islam",
                "spouse_name_bn": "মো. রফিকুল ইসলাম",
                "spouse_occupation": "Transport Worker",
                "total_dependents": 2,
                "minor_children_count": 2,
                "elderly_dependents_count": 0,
                "present_division": "Dhaka",
                "present_district": "Dhaka",
                "present_upazila": "Mirpur",
                "present_union_ward": "Ward 11",
                "present_village_road": "Section 11, Block C, Line 4",
                "present_post_code": "1216",
                "permanent_division": "Barishal",
                "permanent_district": "Patuakhali",
                "permanent_upazila": "Galachipa",
                "permanent_union_ward": "Dakua Union",
                "permanent_village_road": "Village Chotobaliatali",
                "permanent_post_code": "8640",
                "is_permanent_same_as_present": False,
            },
            {
                "phone_number": "+8801811000002",
                "applicant_name": "Md. Rafiqul Islam",
                "applicant_name_bn": "মো. রফিকুল ইসলাম",
                "nid_number": "5501234567",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1988-11-20",
                "age": 38,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Day Laborer / Transport Worker",
                "occupation_bn": "দিনমজুর / পরিবহন শ্রমিক",
                "employer_name": "Local Transport Cooperative",
                "designation": "Driver Helper",
                "monthly_income_bdt": 14000.0,
                "annual_income_bdt": 168000.0,
                "income_source": "Daily Labor",
                "is_below_poverty_line": True,
                "father_name": "Md. Nurul Huda",
                "father_name_bn": "মো. নুরুল হুদা",
                "mother_name": "Amena Khatun",
                "mother_name_bn": "আমেনা খাতুন",
                "spouse_name": "Halima Begum",
                "spouse_name_bn": "হালিমা বেগম",
                "spouse_occupation": "Homemaker",
                "total_dependents": 4,
                "minor_children_count": 3,
                "elderly_dependents_count": 1,
                "present_division": "Chittagong",
                "present_district": "Chittagong",
                "present_upazila": "Pahartali",
                "present_union_ward": "Ward 13",
                "present_village_road": "Saraipara Railway Colony",
                "present_post_code": "4202",
                "permanent_division": "Chittagong",
                "permanent_district": "Comilla",
                "permanent_upazila": "Chauddagram",
                "permanent_union_ward": "Batisha Union",
                "permanent_village_road": "Village Parikot",
                "permanent_post_code": "3550",
                "is_permanent_same_as_present": False,
            },
            {
                "phone_number": "+8801911000003",
                "applicant_name": "Fatema Begum",
                "applicant_name_bn": "ফাতেমা বেগম",
                "nid_number": "19958212345678902",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1995-03-08",
                "age": 31,
                "marital_status": "SEPARATED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Domestic Worker",
                "occupation_bn": "গৃহকর্মী",
                "employer_name": "Informal Domestic Work",
                "designation": "Helper",
                "monthly_income_bdt": 8500.0,
                "annual_income_bdt": 102000.0,
                "income_source": "Domestic Help Wages",
                "is_below_poverty_line": True,
                "father_name": "Kalam Mia",
                "father_name_bn": "কালাম মিয়া",
                "mother_name": "Sufia Begum",
                "mother_name_bn": "সুফিয়া বেগম",
                "spouse_name": "Jahirul Haque",
                "spouse_name_bn": "জহিরুল হক",
                "spouse_occupation": "Unemployed",
                "total_dependents": 2,
                "minor_children_count": 2,
                "elderly_dependents_count": 0,
                "present_division": "Sylhet",
                "present_district": "Sylhet",
                "present_upazila": "Sylhet Sadar",
                "present_union_ward": "Ward 5",
                "present_village_road": "Ambarkhana Colony",
                "present_post_code": "3100",
                "permanent_division": "Sylhet",
                "permanent_district": "Sunamganj",
                "permanent_upazila": "Chhatak",
                "permanent_union_ward": "Gobindaganj Union",
                "permanent_village_road": "Village Harinagar",
                "permanent_post_code": "3080",
                "is_permanent_same_as_present": False,
            },
            {
                "phone_number": "+8801711000004",
                "applicant_name": "Anowar Hossain",
                "applicant_name_bn": "আনোয়ার হোসেন",
                "nid_number": "6701234568",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1978-08-12",
                "age": 48,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Tenant Farmer / Sharecropper",
                "occupation_bn": "বর্গা কৃষক",
                "employer_name": "Self-employed Agriculture",
                "designation": "Cultivator",
                "monthly_income_bdt": 11000.0,
                "annual_income_bdt": 132000.0,
                "income_source": "Crop Harvesting",
                "is_below_poverty_line": True,
                "father_name": "Late Mokbul Hossain",
                "father_name_bn": "মৃত মকবুল হোসেন",
                "mother_name": "Zubeda Bibi",
                "mother_name_bn": "জুবেদা বিবি",
                "spouse_name": "Rokeya Begum",
                "spouse_name_bn": "রোকেয়া বেগম",
                "spouse_occupation": "Homemaker",
                "total_dependents": 3,
                "minor_children_count": 1,
                "elderly_dependents_count": 1,
                "present_division": "Rangpur",
                "present_district": "Kurigram",
                "present_upazila": "Chilmari",
                "present_union_ward": "Chilmari Union",
                "present_village_road": "Mondolpara Char",
                "present_post_code": "5630",
                "permanent_division": "Rangpur",
                "permanent_district": "Kurigram",
                "permanent_upazila": "Chilmari",
                "permanent_union_ward": "Chilmari Union",
                "permanent_village_road": "Mondolpara Char",
                "permanent_post_code": "5630",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801611000005",
                "applicant_name": "Rupa Rani Das",
                "applicant_name_bn": "রূপা রানী দাস",
                "nid_number": "19984112345678903",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1998-12-05",
                "age": 28,
                "marital_status": "MARRIED",
                "religion": "HINDUISM",
                "education_level": "SECONDARY",
                "occupation": "Handicrafts & Sewing Worker",
                "occupation_bn": "হস্তশিল্প ও দর্জি কর্মী",
                "employer_name": "Village Cottage Artisan Group",
                "designation": "Seamstress",
                "monthly_income_bdt": 9500.0,
                "annual_income_bdt": 114000.0,
                "income_source": "Tailoring Piece Rate",
                "is_below_poverty_line": True,
                "father_name": "Bikash Chandra Das",
                "father_name_bn": "বিকাশ চন্দ্র দাস",
                "mother_name": "Gita Rani Das",
                "mother_name_bn": "গীতা রানী দাস",
                "spouse_name": "Subrata Das",
                "spouse_name_bn": "সুব্রত দাস",
                "spouse_occupation": "Carpenter",
                "total_dependents": 1,
                "minor_children_count": 1,
                "elderly_dependents_count": 0,
                "present_division": "Khulna",
                "present_district": "Satkhira",
                "present_upazila": "Shyamnagar",
                "present_union_ward": "Bhurulia Union",
                "present_village_road": "Village Nakipur",
                "present_post_code": "9450",
                "permanent_division": "Khulna",
                "permanent_district": "Satkhira",
                "permanent_upazila": "Shyamnagar",
                "permanent_union_ward": "Bhurulia Union",
                "permanent_village_road": "Village Nakipur",
                "permanent_post_code": "9450",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801711000006",
                "applicant_name": "Khairul Bashar",
                "applicant_name_bn": "খায়রুল বাশার",
                "nid_number": "7801234569",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1983-04-18",
                "age": 43,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Tea Garden Plucker / Plantation Labor",
                "occupation_bn": "চা শ্রমিক",
                "employer_name": "Sreemangal Tea Estate",
                "designation": "Plucker",
                "monthly_income_bdt": 7800.0,
                "annual_income_bdt": 93600.0,
                "income_source": "Estate Wages",
                "is_below_poverty_line": True,
                "father_name": "Late Ramzan Ali",
                "father_name_bn": "মৃত রমজান আলী",
                "mother_name": "Khodeja Begum",
                "mother_name_bn": "খদেজা বেগম",
                "spouse_name": "Rabeya Khatun",
                "spouse_name_bn": "রাবেয়া খাতুন",
                "spouse_occupation": "Tea Worker",
                "total_dependents": 3,
                "minor_children_count": 2,
                "elderly_dependents_count": 1,
                "present_division": "Sylhet",
                "present_district": "Moulvibazar",
                "present_upazila": "Sreemangal",
                "present_union_ward": "Kalighat Union",
                "present_village_road": "Kalighat Tea Division Line 2",
                "present_post_code": "3210",
                "permanent_division": "Sylhet",
                "permanent_district": "Moulvibazar",
                "permanent_upazila": "Sreemangal",
                "permanent_union_ward": "Kalighat Union",
                "permanent_village_road": "Kalighat Tea Division Line 2",
                "permanent_post_code": "3210",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801811000007",
                "applicant_name": "Nasreen Sultana",
                "applicant_name_bn": "নাসরীন সুলতানা",
                "nid_number": "19941912345678904",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1994-07-22",
                "age": 32,
                "marital_status": "DIVORCED",
                "religion": "ISLAM",
                "education_level": "HIGHER_SECONDARY",
                "occupation": "Community Health Volunteer",
                "occupation_bn": "স্বাস্থ্যকর্মী",
                "employer_name": "Local NGO Healthcare Project",
                "designation": "Field Health Worker",
                "monthly_income_bdt": 11500.0,
                "annual_income_bdt": 138000.0,
                "income_source": "Health Honorarium",
                "is_below_poverty_line": True,
                "father_name": "Sirajul Islam",
                "father_name_bn": "সিরাজুল ইসলাম",
                "mother_name": "Momena Begum",
                "mother_name_bn": "মোমেনা বেগম",
                "spouse_name": None,
                "spouse_name_bn": None,
                "spouse_occupation": None,
                "total_dependents": 1,
                "minor_children_count": 1,
                "elderly_dependents_count": 0,
                "present_division": "Rajshahi",
                "present_district": "Bogra",
                "present_upazila": "Sariakandi",
                "present_union_ward": "Chaluabari Union",
                "present_village_road": "Village Manikdair",
                "present_post_code": "5850",
                "permanent_division": "Rajshahi",
                "permanent_district": "Bogra",
                "permanent_upazila": "Sariakandi",
                "permanent_union_ward": "Chaluabari Union",
                "permanent_village_road": "Village Manikdair",
                "permanent_post_code": "5850",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801711000008",
                "applicant_name": "Jashim Uddin",
                "applicant_name_bn": "জসিম উদ্দিন",
                "nid_number": "8901234570",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1975-01-15",
                "age": 51,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "ILLITERATE",
                "occupation": "Fisherman / Net Mender",
                "occupation_bn": "জেলে",
                "employer_name": "Coastal Fishing Crew",
                "designation": "Boat Hand",
                "monthly_income_bdt": 10500.0,
                "annual_income_bdt": 126000.0,
                "income_source": "Fish Catch Share",
                "is_below_poverty_line": True,
                "father_name": "Late Moniruzzaman",
                "father_name_bn": "মৃত মনিরুজ্জামান",
                "mother_name": "Khuki Begum",
                "mother_name_bn": "খুকি বেগম",
                "spouse_name": "Kulsum Bibi",
                "spouse_name_bn": "কুলসুম বিবি",
                "spouse_occupation": "Homemaker",
                "total_dependents": 4,
                "minor_children_count": 2,
                "elderly_dependents_count": 1,
                "present_division": "Chittagong",
                "present_district": "Cox's Bazar",
                "present_upazila": "Teknaf",
                "present_union_ward": "Sabrang Union",
                "present_village_road": "Village Shah Porir Dwip",
                "present_post_code": "4760",
                "permanent_division": "Chittagong",
                "permanent_district": "Cox's Bazar",
                "permanent_upazila": "Teknaf",
                "permanent_union_ward": "Sabrang Union",
                "permanent_village_road": "Village Shah Porir Dwip",
                "permanent_post_code": "4760",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801911000009",
                "applicant_name": "Morium Begum",
                "applicant_name_bn": "মরিয়ম বেগম",
                "nid_number": "19896712345678905",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1989-09-30",
                "age": 37,
                "marital_status": "WIDOWED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Poultry & Livestock Attendant",
                "occupation_bn": "হাঁস-মুরগি খামার কর্মী",
                "employer_name": "Community Micro-farm",
                "designation": "Caretaker",
                "monthly_income_bdt": 9000.0,
                "annual_income_bdt": 108000.0,
                "income_source": "Livestock Tending",
                "is_below_poverty_line": True,
                "father_name": "Late Habibur Rahman",
                "father_name_bn": "মৃত হাবিবুর রহমান",
                "mother_name": "Feroza Begum",
                "mother_name_bn": "ফিরোজা বেগম",
                "spouse_name": "Late Tofazzal Hossain",
                "spouse_name_bn": "মৃত তোফাজ্জল হোসেন",
                "spouse_occupation": "Deceased",
                "total_dependents": 2,
                "minor_children_count": 2,
                "elderly_dependents_count": 0,
                "present_division": "Mymensingh",
                "present_district": "Netrokona",
                "present_upazila": "Khaliajuri",
                "present_union_ward": "Mendipur Union",
                "present_village_road": "Village Jagannathpur (Haor)",
                "present_post_code": "2460",
                "permanent_division": "Mymensingh",
                "permanent_district": "Netrokona",
                "permanent_upazila": "Khaliajuri",
                "permanent_union_ward": "Mendipur Union",
                "permanent_village_road": "Village Jagannathpur (Haor)",
                "permanent_post_code": "2460",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801511000010",
                "applicant_name": "Babul Chandra Roy",
                "applicant_name_bn": "বাবুল চন্দ্র রায়",
                "nid_number": "9001234571",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1991-06-19",
                "age": 35,
                "marital_status": "MARRIED",
                "religion": "HINDUISM",
                "education_level": "SECONDARY",
                "occupation": "Potter / Clay Artisan",
                "occupation_bn": "মৃৎশিল্পী / কুমার",
                "employer_name": "Palpara Pottery Cooperative",
                "designation": "Artisan",
                "monthly_income_bdt": 11800.0,
                "annual_income_bdt": 141600.0,
                "income_source": "Pottery Sales",
                "is_below_poverty_line": True,
                "father_name": "Subal Chandra Roy",
                "father_name_bn": "সুবল চন্দ্র রায়",
                "mother_name": "Radharani Roy",
                "mother_name_bn": "রাধারানী রায়",
                "spouse_name": "Maya Rani Roy",
                "spouse_name_bn": "মায়া রানী রায়",
                "spouse_occupation": "Artisan Helper",
                "total_dependents": 3,
                "minor_children_count": 1,
                "elderly_dependents_count": 2,
                "present_division": "Rajshahi",
                "present_district": "Naogaon",
                "present_upazila": "Patnitala",
                "present_union_ward": "Patichara Union",
                "present_village_road": "Village Palpara",
                "present_post_code": "6540",
                "permanent_division": "Rajshahi",
                "permanent_district": "Naogaon",
                "permanent_upazila": "Patnitala",
                "permanent_union_ward": "Patichara Union",
                "permanent_village_road": "Village Palpara",
                "permanent_post_code": "6540",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801711000011",
                "applicant_name": "Aklima Khatun",
                "applicant_name_bn": "আক্লিমা খাতুন",
                "nid_number": "19973212345678906",
                "nid_type": "LEGACY_17",
                "gender": "FEMALE",
                "date_of_birth": "1997-10-10",
                "age": 29,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Tea Stall Helper / Cook",
                "occupation_bn": "সহকারী বাবুর্চি",
                "employer_name": "Roadside Canteen",
                "designation": "Kitchen Hand",
                "monthly_income_bdt": 8000.0,
                "annual_income_bdt": 96000.0,
                "income_source": "Daily Wage",
                "is_below_poverty_line": True,
                "father_name": "Late Idris Ali",
                "father_name_bn": "মৃত ইদ্রিস আলী",
                "mother_name": "Salma Begum",
                "mother_name_bn": "সালমা বেগম",
                "spouse_name": "Dulal Mia",
                "spouse_name_bn": "দুলাল মিয়া",
                "spouse_occupation": "Van Puller",
                "total_dependents": 2,
                "minor_children_count": 2,
                "elderly_dependents_count": 0,
                "present_division": "Khulna",
                "present_district": "Jessore",
                "present_upazila": "Jhikargachha",
                "present_union_ward": "Panisara Union",
                "present_village_road": "Village Godkhali Flower Market Road",
                "present_post_code": "7420",
                "permanent_division": "Khulna",
                "permanent_district": "Jessore",
                "permanent_upazila": "Jhikargachha",
                "permanent_union_ward": "Panisara Union",
                "permanent_village_road": "Village Godkhali Flower Market Road",
                "permanent_post_code": "7420",
                "is_permanent_same_as_present": True,
            },
            {
                "phone_number": "+8801811000012",
                "applicant_name": "Solaiman Hawlader",
                "applicant_name_bn": "সোলায়মান হাওলাদার",
                "nid_number": "1201234572",
                "nid_type": "SMART_10",
                "gender": "MALE",
                "date_of_birth": "1980-02-28",
                "age": 46,
                "marital_status": "MARRIED",
                "religion": "ISLAM",
                "education_level": "PRIMARY",
                "occupation": "Salt Field Laborer",
                "occupation_bn": "লবণ মাঠ শ্রমিক",
                "employer_name": "Cox's Bazar Salt Growers Collective",
                "designation": "Field Worker",
                "monthly_income_bdt": 12000.0,
                "annual_income_bdt": 144000.0,
                "income_source": "Salt Pan Wages",
                "is_below_poverty_line": True,
                "father_name": "Late Yunus Hawlader",
                "father_name_bn": "মৃত ইউনুস হাওলাদার",
                "mother_name": "Ayesha Khatun",
                "mother_name_bn": "আয়েশা খাতুন",
                "spouse_name": "Nurjahan Begum",
                "spouse_name_bn": "নুরজাহান বেগম",
                "spouse_occupation": "Homemaker",
                "total_dependents": 3,
                "minor_children_count": 2,
                "elderly_dependents_count": 1,
                "present_division": "Chittagong",
                "present_district": "Cox's Bazar",
                "present_upazila": "Chakaria",
                "present_union_ward": "Demoshia Union",
                "present_village_road": "Village Rampura Salt Field",
                "present_post_code": "4740",
                "permanent_division": "Barishal",
                "permanent_district": "Bhola",
                "permanent_upazila": "Char Fasson",
                "permanent_union_ward": "Char Manika Union",
                "permanent_village_road": "Village Dokkhin Aicha",
                "permanent_post_code": "8340",
                "is_permanent_same_as_present": False,
            }
        ]

    def lookup_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        clean_phone = phone.strip().replace(" ", "").replace("-", "")
        for record in self.records:
            rec_phone = record["phone_number"].replace(" ", "").replace("-", "")
            if rec_phone == clean_phone or rec_phone.endswith(clean_phone[-10:]):
                result = dict(record)
                result["is_demo_data"] = True
                result["disclaimer"] = DISCLAIMER_NOTICE
                result["provenance"] = "MOCK_IDENTITY"
                return result
        return None

    def lookup_by_nid(self, nid: str) -> Optional[Dict[str, Any]]:
        clean_nid = nid.strip().replace(" ", "").replace("-", "")
        for record in self.records:
            if record["nid_number"] == clean_nid:
                result = dict(record)
                result["is_demo_data"] = True
                result["disclaimer"] = DISCLAIMER_NOTICE
                result["provenance"] = "MOCK_IDENTITY"
                return result
        return None

    def list_demo_records(self) -> List[Dict[str, Any]]:
        results = []
        for r in self.records:
            rec = dict(r)
            rec["is_demo_data"] = True
            rec["disclaimer"] = DISCLAIMER_NOTICE
            results.append(rec)
        return results


class FutureAuthorisedIdentityProvider(IdentityProvider):
    """
    Stub for future production statutory government registry integration.
    Strict safety posture: Never fabricates or fakes live government APIs.
    """

    def lookup_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "Authorised Government NID / Porichoy Gateway requires statutory clearance, "
            "production cryptographic credentials, and gazetted citizen consent protocols. "
            "Never fabricated in DLAS."
        )

    def lookup_by_nid(self, nid: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "Authorised Government NID / Porichoy Gateway requires statutory clearance, "
            "production cryptographic credentials, and gazetted citizen consent protocols. "
            "Never fabricated in DLAS."
        )

    def list_demo_records(self) -> List[Dict[str, Any]]:
        return []


def get_identity_provider() -> IdentityProvider:
    """
    Factory returning configured IdentityProvider implementation.
    Defaults to MockIdentityProvider for hackathon demonstration.
    """
    provider_mode = getattr(settings, "IDENTITY_PROVIDER", "mock").lower()
    if provider_mode == "mock":
        return MockIdentityProvider()
    elif provider_mode in ["authorised", "government", "production"]:
        return FutureAuthorisedIdentityProvider()
    else:
        logger.warning(f"Unknown IDENTITY_PROVIDER mode '{provider_mode}'. Falling back to MockIdentityProvider.")
        return MockIdentityProvider()
