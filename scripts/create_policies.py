#!/usr/bin/env python
"""
Create 20 hospital policies and household test cases for BillBack evaluation.
This script generates:
1. 20 HospitalPolicy JSON files in data/policies/
2. 10 HouseholdFacts JSON files in data/households/
3. A policy manifest JSON mapping policy_id -> hospital info
4. An answer key JSON with expected eligibility status for each (policy, household) pair
"""

import json
import sys
from decimal import Decimal
from pathlib import Path
from datetime import date

# Add project root to path for billback import
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# 20 Hospital Policies
# ============================================================

POLICIES = [
    {
        "policy_id": "HOSP-001",
        "hospital_name": "General Medical Center",
        "facility_names": ["General Medical Center Main", "GMC West Campus"],
        "state": "CA",
        "source_url": "https://example.com/gmc-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "California resident", "required": True, "verified_value": "CA", "evidence_ref": "Sec 2.1"},
                    {"name": "asset_test", "description": "Assets under $50,000", "required": True, "verified_value": "50000", "evidence_ref": "Sec 2.2"}
                ],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "75% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "75",
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "California resident", "required": True, "verified_value": "CA", "evidence_ref": "Sec 3.1"}
                ],
                "scope": {},
                "evidence_ref": "Page 4, Section 3",
                "priority": 1
            },
            {
                "tier_id": "discount-400",
                "name": "50% Discount - 400% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "400",
                "inclusivity": "inclusive",
                "discount_percent": "50",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 4, Section 4",
                "priority": 2
            }
        ]
    },
    {
        "policy_id": "HOSP-002",
        "hospital_name": "Metro Health System",
        "facility_names": ["Metro Health Hospital", "Metro Urgent Care"],
        "state": "NY",
        "source_url": "https://example.com/metro-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-300",
                "name": "Free Care - 300% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "NY state resident", "required": True, "verified_value": "NY", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-400",
                "name": "60% Discount - 400% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "400",
                "inclusivity": "exclusive",
                "discount_percent": "60",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-003",
        "hospital_name": "Sunshine State Hospital",
        "facility_names": ["Sunshine State Hospital"],
        "state": "FL",
        "source_url": "https://example.com/sunshine-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-table",
                "name": "Free Care - Income Table",
                "type": "free",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "FL resident", "required": True, "verified_value": "FL", "evidence_ref": "Sec 1"}
                ],
                "scope": {"income_table": {"1": "25000", "2": "34000", "3": "43000", "4": "52000", "5": "61000", "6": "70000"}},
                "evidence_ref": "Page 3, Table 1",
                "priority": 0
            },
            {
                "tier_id": "discount-table",
                "name": "Sliding Scale Discount",
                "type": "discounted",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": "100 - (income / threshold * 50)",
                "conditions": [],
                "scope": {"income_table": {"1": "50000", "2": "68000", "3": "86000", "4": "104000", "5": "122000", "6": "140000"}},
                "evidence_ref": "Page 4, Table 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-004",
        "hospital_name": "Lone Star Medical Center",
        "facility_names": ["Lone Star Medical Center", "LSMC North"],
        "state": "TX",
        "source_url": "https://example.com/lonestar-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Charity Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "exclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "TX resident", "required": True, "verified_value": "TX", "evidence_ref": "Sec 4.1"},
                    {"name": "insurance", "description": "Uninsured or underinsured", "required": True, "verified_value": "uninsured", "evidence_ref": "Sec 4.2"}
                ],
                "scope": {},
                "evidence_ref": "Page 5, Section 4",
                "priority": 0
            },
            {
                "tier_id": "discount-250",
                "name": "80% Discount - 250% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "250",
                "inclusivity": "inclusive",
                "discount_percent": "80",
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "TX resident", "required": True, "verified_value": "TX", "evidence_ref": "Sec 5.1"}
                ],
                "scope": {},
                "evidence_ref": "Page 6, Section 5",
                "priority": 1
            },
            {
                "tier_id": "discount-350",
                "name": "40% Discount - 350% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "350",
                "inclusivity": "inclusive",
                "discount_percent": "40",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 6, Section 6",
                "priority": 2
            }
        ]
    },
    {
        "policy_id": "HOSP-005",
        "hospital_name": "Mountain View Regional",
        "facility_names": ["Mountain View Regional Hospital"],
        "state": "CO",
        "source_url": "https://example.com/mtnview-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-250",
                "name": "Free Care - 250% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "250",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "CO resident", "required": True, "verified_value": "CO", "evidence_ref": "Sec 2"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 2",
                "priority": 0
            }
        ]
    },
    {
        "policy_id": "HOSP-006",
        "hospital_name": "Pacific Northwest Health",
        "facility_names": ["PNH Medical Center", "PNH Clinic"],
        "state": "WA",
        "source_url": "https://example.com/pnh-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "WA resident", "required": True, "verified_value": "WA", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "70% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "70",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-007",
        "hospital_name": "New England Medical Center",
        "facility_names": ["NE Medical Center", "NE Health Partners"],
        "state": "MA",
        "source_url": "https://example.com/ne-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-300",
                "name": "Free Care - 300% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "MA resident", "required": True, "verified_value": "MA", "evidence_ref": "Sec 1"},
                    {"name": "asset_test", "description": "Assets under $25,000", "required": True, "verified_value": "25000", "evidence_ref": "Sec 2"}
                ],
                "scope": {},
                "evidence_ref": "Page 3, Section 1-2",
                "priority": 0
            },
            {
                "tier_id": "discount-400",
                "name": "50% Discount - 400% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "400",
                "inclusivity": "inclusive",
                "discount_percent": "50",
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "MA resident", "required": True, "verified_value": "MA", "evidence_ref": "Sec 3"}
                ],
                "scope": {},
                "evidence_ref": "Page 4, Section 3",
                "priority": 1
            },
            {
                "tier_id": "discount-500",
                "name": "25% Discount - 500% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "500",
                "inclusivity": "exclusive",
                "discount_percent": "25",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 4, Section 4",
                "priority": 2
            }
        ]
    },
    {
        "policy_id": "HOSP-008",
        "hospital_name": "Great Lakes Hospital",
        "facility_names": ["Great Lakes Hospital", "GLH East", "GLH West"],
        "state": "IL",
        "source_url": "https://example.com/glh-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-table",
                "name": "Free Care - Income Table",
                "type": "free",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "IL resident", "required": True, "verified_value": "IL", "evidence_ref": "Sec 2"}
                ],
                "scope": {"income_table": {"1": "28000", "2": "38000", "3": "48000", "4": "58000", "5": "68000"}},
                "evidence_ref": "Page 3, Table 1",
                "priority": 0
            }
        ]
    },
    {
        "policy_id": "HOSP-009",
        "hospital_name": "Alaska Regional Hospital",
        "facility_names": ["Alaska Regional Hospital"],
        "state": "AK",
        "source_url": "https://example.com/ak-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "alaska",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL (Alaska)",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "AK resident", "required": True, "verified_value": "AK", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "60% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "60",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-010",
        "hospital_name": "Aloha Medical Center",
        "facility_names": ["Aloha Medical Center", "AMC Maui"],
        "state": "HI",
        "source_url": "https://example.com/aloha-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "hawaii",
        "tiers": [
            {
                "tier_id": "free-250",
                "name": "Free Care - 250% FPL (Hawaii)",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "250",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "HI resident", "required": True, "verified_value": "HI", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            }
        ]
    },
    {
        "policy_id": "HOSP-011",
        "hospital_name": "Midwest Community Hospital",
        "facility_names": ["Midwest Community Hospital"],
        "state": "OH",
        "source_url": "https://example.com/midwest-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "OH resident", "required": True, "verified_value": "OH", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "75% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "75",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            },
            {
                "tier_id": "discount-400",
                "name": "50% Discount - 400% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "400",
                "inclusivity": "inclusive",
                "discount_percent": "50",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 3",
                "priority": 2
            }
        ]
    },
    {
        "policy_id": "HOSP-012",
        "hospital_name": "Southern Health Alliance",
        "facility_names": ["Southern Health Hospital", "SHA Clinic Network"],
        "state": "GA",
        "source_url": "https://example.com/southern-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-150",
                "name": "Free Care - 150% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "150",
                "inclusivity": "exclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "GA resident", "required": True, "verified_value": "GA", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-250",
                "name": "80% Discount - 250% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "250",
                "inclusivity": "inclusive",
                "discount_percent": "80",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-013",
        "hospital_name": "Desert Medical Center",
        "facility_names": ["Desert Medical Center", "DMC Phoenix"],
        "state": "AZ",
        "source_url": "https://example.com/desert-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-table",
                "name": "Free Care - Income Table",
                "type": "free",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "AZ resident", "required": True, "verified_value": "AZ", "evidence_ref": "Sec 1"}
                ],
                "scope": {"income_table": {"1": "26000", "2": "35000", "3": "44000", "4": "53000", "5": "62000", "6": "71000"}},
                "evidence_ref": "Page 3, Table 1",
                "priority": 0
            },
            {
                "tier_id": "discount-table",
                "name": "Sliding Scale Discount",
                "type": "discounted",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": "max(0, 100 - (income - threshold) / threshold * 25)",
                "conditions": [],
                "scope": {"income_table": {"1": "52000", "2": "70000", "3": "88000", "4": "106000", "5": "124000", "6": "142000"}},
                "evidence_ref": "Page 4, Table 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-014",
        "hospital_name": "Capital Region Medical",
        "facility_names": ["Capital Region Medical Center"],
        "state": "VA",
        "source_url": "https://example.com/capital-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "VA resident", "required": True, "verified_value": "VA", "evidence_ref": "Sec 1"},
                    {"name": "insurance", "description": "Uninsured", "required": True, "verified_value": "uninsured", "evidence_ref": "Sec 2"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1-2",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "70% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "70",
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "VA resident", "required": True, "verified_value": "VA", "evidence_ref": "Sec 3"}
                ],
                "scope": {},
                "evidence_ref": "Page 3, Section 3",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-015",
        "hospital_name": "North Star Hospital",
        "facility_names": ["North Star Hospital", "NSH Duluth"],
        "state": "MN",
        "source_url": "https://example.com/northstar-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-275",
                "name": "Free Care - 275% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "275",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "MN resident", "required": True, "verified_value": "MN", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-350",
                "name": "60% Discount - 350% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "350",
                "inclusivity": "inclusive",
                "discount_percent": "60",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-016",
        "hospital_name": "Bay State Health",
        "facility_names": ["Bay State Hospital", "BSH Cape Cod"],
        "state": "MA",
        "source_url": "https://example.com/baystate-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-300",
                "name": "Free Care - 300% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "MA resident", "required": True, "verified_value": "MA", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-400",
                "name": "50% Discount - 400% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "400",
                "inclusivity": "inclusive",
                "discount_percent": "50",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-017",
        "hospital_name": "Prairie Medical Center",
        "facility_names": ["Prairie Medical Center"],
        "state": "KS",
        "source_url": "https://example.com/prairie-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "exclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "KS resident", "required": True, "verified_value": "KS", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "75% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "75",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-018",
        "hospital_name": "Gulf Coast Medical",
        "facility_names": ["Gulf Coast Medical Center", "GCMC Mobile"],
        "state": "AL",
        "source_url": "https://example.com/gulf-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-table",
                "name": "Free Care - Income Table",
                "type": "free",
                "threshold_type": "fixed_income_table",
                "threshold_value": "1",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "AL resident", "required": True, "verified_value": "AL", "evidence_ref": "Sec 1"}
                ],
                "scope": {"income_table": {"1": "24000", "2": "32000", "3": "40000", "4": "48000", "5": "56000"}},
                "evidence_ref": "Page 3, Table 1",
                "priority": 0
            }
        ]
    },
    {
        "policy_id": "HOSP-019",
        "hospital_name": "Rocky Mountain Health",
        "facility_names": ["Rocky Mountain Hospital", "RMH Colorado Springs"],
        "state": "CO",
        "source_url": "https://example.com/rocky-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-200",
                "name": "Free Care - 200% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "200",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "CO resident", "required": True, "verified_value": "CO", "evidence_ref": "Sec 1"},
                    {"name": "asset_test", "description": "Assets under $30,000", "required": True, "verified_value": "30000", "evidence_ref": "Sec 2"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1-2",
                "priority": 0
            },
            {
                "tier_id": "discount-300",
                "name": "70% Discount - 300% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "300",
                "inclusivity": "inclusive",
                "discount_percent": "70",
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "CO resident", "required": True, "verified_value": "CO", "evidence_ref": "Sec 3"}
                ],
                "scope": {},
                "evidence_ref": "Page 3, Section 3",
                "priority": 1
            }
        ]
    },
    {
        "policy_id": "HOSP-020",
        "hospital_name": "Emerald City Hospital",
        "facility_names": ["Emerald City Hospital", "ECH Bellevue"],
        "state": "WA",
        "source_url": "https://example.com/emerald-policy.pdf",
        "retrieval_date": "2024-01-15",
        "effective_date": "2024-01-01",
        "version": "2024.1",
        "default_fpl_year": 2024,
        "default_region": "contiguous",
        "tiers": [
            {
                "tier_id": "free-250",
                "name": "Free Care - 250% FPL",
                "type": "free",
                "threshold_type": "fpl_percentage",
                "threshold_value": "250",
                "inclusivity": "inclusive",
                "discount_percent": None,
                "discount_formula": None,
                "conditions": [
                    {"name": "residency", "description": "WA resident", "required": True, "verified_value": "WA", "evidence_ref": "Sec 1"}
                ],
                "scope": {},
                "evidence_ref": "Page 2, Section 1",
                "priority": 0
            },
            {
                "tier_id": "discount-350",
                "name": "65% Discount - 350% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "350",
                "inclusivity": "inclusive",
                "discount_percent": "65",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 2",
                "priority": 1
            },
            {
                "tier_id": "discount-450",
                "name": "30% Discount - 450% FPL",
                "type": "discounted",
                "threshold_type": "fpl_percentage",
                "threshold_value": "450",
                "inclusivity": "exclusive",
                "discount_percent": "30",
                "discount_formula": None,
                "conditions": [],
                "scope": {},
                "evidence_ref": "Page 3, Section 3",
                "priority": 2
            }
        ]
    }
]

# ============================================================
# 10 Household Test Cases
# ============================================================

HOUSEHOLDS = [
    {
        "household_id": "HH-001",
        "description": "Single person, low income, qualifies for free care at most hospitals",
        "household_size": 1,
        "annual_income_usd": "18000",
        "residency_state": "CA",
        "residency_county": "Los Angeles",
        "assets_usd": "5000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "emergency",
        "patient_age": 35,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-002",
        "description": "Couple, moderate income, near 200% FPL boundary",
        "household_size": 2,
        "annual_income_usd": "40000",
        "residency_state": "NY",
        "residency_county": "Kings",
        "assets_usd": "15000",
        "insurance_status": "underinsured",
        "facility_name": None,
        "service_type": "inpatient",
        "patient_age": 42,
        "patient_citizenship": "legal_resident"
    },
    {
        "household_id": "HH-003",
        "description": "Family of 4, income above free tier but qualifies for discount",
        "household_size": 4,
        "annual_income_usd": "65000",
        "residency_state": "TX",
        "residency_county": "Harris",
        "assets_usd": "25000",
        "insurance_status": "insured",
        "facility_name": None,
        "service_type": "outpatient",
        "patient_age": 38,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-004",
        "description": "Large family (6), high income, likely not eligible",
        "household_size": 6,
        "annual_income_usd": "120000",
        "residency_state": "FL",
        "residency_county": "Miami-Dade",
        "assets_usd": "50000",
        "insurance_status": "insured",
        "facility_name": None,
        "service_type": "elective",
        "patient_age": 45,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-005",
        "description": "Single person, exactly at 200% FPL for household of 2 (testing inclusive)",
        "household_size": 2,
        "annual_income_usd": "40880",
        "residency_state": "WA",
        "residency_county": "King",
        "assets_usd": "10000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "emergency",
        "patient_age": 29,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-006",
        "description": "Couple, just over 200% FPL, under 300% (tests tier progression)",
        "household_size": 2,
        "annual_income_usd": "45000",
        "residency_state": "CO",
        "residency_county": "Denver",
        "assets_usd": "20000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "inpatient",
        "patient_age": 31,
        "patient_citizenship": "legal_resident"
    },
    {
        "household_id": "HH-007",
        "description": "Family of 3, missing residency info (tests needs_more_info)",
        "household_size": 3,
        "annual_income_usd": "35000",
        "residency_state": None,
        "residency_county": None,
        "assets_usd": "8000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "emergency",
        "patient_age": 34,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-008",
        "description": "Single person in Alaska, tests AK FPL region",
        "household_size": 1,
        "annual_income_usd": "30000",
        "residency_state": "AK",
        "residency_county": "Anchorage",
        "assets_usd": "5000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "emergency",
        "patient_age": 27,
        "patient_citizenship": "citizen"
    },
    {
        "household_id": "HH-009",
        "description": "Couple in Hawaii, tests HI FPL region",
        "household_size": 2,
        "annual_income_usd": "45000",
        "residency_state": "HI",
        "residency_county": "Honolulu",
        "assets_usd": "15000",
        "insurance_status": "underinsured",
        "facility_name": None,
        "service_type": "outpatient",
        "patient_age": 39,
        "patient_citizenship": "legal_resident"
    },
    {
        "household_id": "HH-010",
        "description": "Family of 5 with assets over limit (tests asset test failure)",
        "household_size": 5,
        "annual_income_usd": "40000",
        "residency_state": "MA",
        "residency_county": "Suffolk",
        "assets_usd": "60000",
        "insurance_status": "uninsured",
        "facility_name": None,
        "service_type": "emergency",
        "patient_age": 41,
        "patient_citizenship": "citizen"
    }
]

def write_json(path: Path, data: dict):
    """Write JSON with Decimal serialization."""
    def decimal_serializer(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=decimal_serializer)

def create_policy_manifest():
    """Create manifest mapping policy_id to hospital info."""
    manifest = {
        "generated_date": str(date.today()),
        "total_policies": len(POLICIES),
        "policies": [
            {
                "policy_id": p["policy_id"],
                "hospital_name": p["hospital_name"],
                "state": p["state"],
                "facility_count": len(p["facility_names"]),
                "tier_count": len(p["tiers"]),
                "default_fpl_year": p["default_fpl_year"],
                "default_region": p["default_region"]
            }
            for p in POLICIES
        ]
    }
    return manifest

def create_household_manifest():
    """Create manifest for household test cases."""
    manifest = {
        "generated_date": str(date.today()),
        "total_households": len(HOUSEHOLDS),
        "households": [
            {
                "household_id": h["household_id"],
                "description": h["description"],
                "household_size": h["household_size"],
                "annual_income_usd": h["annual_income_usd"],
                "residency_state": h["residency_state"]
            }
            for h in HOUSEHOLDS
        ]
    }
    return manifest

def evaluate_all_combinations():
    """Evaluate all policy-household combinations to create answer key."""
    from billback.eligibility import (
        EligibilityEngine,
        HospitalPolicy,
        AssistanceTier,
        PolicyCondition,
        HouseholdFacts,
        ThresholdType,
        Inclusivity,
        EligibilityStatus,
        create_synthetic_resolver
    )
    from decimal import Decimal

    resolver = create_synthetic_resolver(2024)
    engine = EligibilityEngine(resolver)

    # Convert policy dicts to objects
    policy_objects = {}
    for p in POLICIES:
        tiers = []
        for t in p["tiers"]:
            conditions = []
            for c in t["conditions"]:
                conditions.append(PolicyCondition(
                    name=c["name"],
                    description=c["description"],
                    required=c["required"],
                    verified_value=c["verified_value"],
                    evidence_ref=c.get("evidence_ref")
                ))
            tiers.append(AssistanceTier(
                tier_id=t["tier_id"],
                name=t["name"],
                type=t["type"],
                threshold_type=ThresholdType(t["threshold_type"]),
                threshold_value=Decimal(t["threshold_value"]),
                inclusivity=Inclusivity(t["inclusivity"]),
                discount_percent=Decimal(t["discount_percent"]) if t["discount_percent"] else None,
                discount_formula=t["discount_formula"],
                conditions=conditions,
                scope=t["scope"],
                evidence_ref=t["evidence_ref"],
                priority=t["priority"]
            ))

        policy_objects[p["policy_id"]] = HospitalPolicy(
            policy_id=p["policy_id"],
            hospital_name=p["hospital_name"],
            facility_names=p["facility_names"],
            state=p["state"],
            source_url=p["source_url"],
            retrieval_date=p["retrieval_date"],
            effective_date=p["effective_date"],
            version=p["version"],
            tiers=tiers,
            default_fpl_year=p["default_fpl_year"],
            default_region=p["default_region"]
        )

    # Convert household dicts to objects
    household_objects = {}
    for h in HOUSEHOLDS:
        household_objects[h["household_id"]] = HouseholdFacts(
            household_size=h["household_size"],
            annual_income_usd=Decimal(h["annual_income_usd"]),
            residency_state=h["residency_state"],
            residency_county=h["residency_county"],
            assets_usd=Decimal(h["assets_usd"]) if h["assets_usd"] else None,
            insurance_status=h["insurance_status"],
            facility_name=h["facility_name"],
            service_type=h["service_type"],
            patient_age=h["patient_age"],
            patient_citizenship=h["patient_citizenship"]
        )

    # Evaluate all combinations
    answer_key = {
        "generated_date": str(date.today()),
        "total_combinations": len(POLICIES) * len(HOUSEHOLDS),
        "results": {}
    }

    for p in POLICIES:
        policy_id = p["policy_id"]
        answer_key["results"][policy_id] = {}

        for h in HOUSEHOLDS:
            household_id = h["household_id"]
            try:
                result = engine.evaluate(policy_objects[policy_id], household_objects[household_id])
                answer_key["results"][policy_id][household_id] = {
                    "status": result.status.value,
                    "matching_tier": result.matching_tier.tier_id if result.matching_tier else None,
                    "matching_tier_name": result.matching_tier.name if result.matching_tier else None,
                    "matching_tier_type": result.matching_tier.type if result.matching_tier else None,
                    "discount_percent": str(result.matching_tier.discount_percent) if result.matching_tier and result.matching_tier.discount_percent else None,
                    "explanation": result.explanation,
                    "missing_facts": result.missing_facts,
                    "unresolved_rules": result.unresolved_rules
                }
            except Exception as e:
                answer_key["results"][policy_id][household_id] = {
                    "status": "error",
                    "error": str(e)
                }

    return answer_key

def main():
    data_dir = Path("data")
    policies_dir = data_dir / "policies"
    households_dir = data_dir / "households"

    policies_dir.mkdir(parents=True, exist_ok=True)
    households_dir.mkdir(parents=True, exist_ok=True)

    # Write individual policy files
    for p in POLICIES:
        write_json(policies_dir / f"{p['policy_id']}.json", p)

    # Write individual household files
    for h in HOUSEHOLDS:
        write_json(households_dir / f"{h['household_id']}.json", h)

    # Write manifests
    write_json(data_dir / "policy_manifest.json", create_policy_manifest())
    write_json(data_dir / "household_manifest.json", create_household_manifest())

    # Write answer key
    print("Evaluating all policy-household combinations...")
    answer_key = evaluate_all_combinations()
    write_json(data_dir / "answer_key.json", answer_key)

    print(f"Created {len(POLICIES)} policy files in {policies_dir}")
    print(f"Created {len(HOUSEHOLDS)} household files in {households_dir}")
    print(f"Created policy_manifest.json, household_manifest.json, answer_key.json in {data_dir}")
    print(f"Total combinations evaluated: {answer_key['total_combinations']}")

if __name__ == "__main__":
    main()