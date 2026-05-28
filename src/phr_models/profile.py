# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""
Patient Profile, Demographics & Epistemic Medical Intake — Pydantic models.

Defines schemas for personal demographics, genetic ancestry, pronouns,
disability accessibility supports, and allergies/pre-existing conditions
coupled with evidence linkages and verification audit fields.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class EpistemicStatus(str, Enum):
    CLINICALLY_VERIFIED = "clinically-verified"
    SELF_REPORTED_UNVERIFIED = "self-reported-unverified"
    SUSPECTED_ONSET = "suspected-onset"
    DISPUTED_MISDIAGNOSIS = "disputed-misdiagnosis"

class PatientProfile(BaseModel):
    id: str
    full_name: str
    date_of_birth: date
    biological_sex: str = Field(..., description="e.g., Male, Female, Intersex")
    pronouns: str = Field(..., description="e.g., He/Him, She/Her, They/Them, or custom pronouns")
    gender_identity: Optional[str] = None
    ancestry_lineage: str = Field(..., description="Genetic ancestral background, e.g., Anglo-Celtic, East Asian, Indigenous Australian")
    primary_language: str = Field(..., description="e.g., English, Mandarin, Spanish")
    medicare_number: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class DisabilitySupport(BaseModel):
    id: str
    support_name: str = Field(..., description="e.g., Visual Impairment Braille Aids, Wheelchair Mobility Support")
    description: str
    accessibility_requirements: List[str] = Field(default_factory=list, description="e.g., Ramp Access, Screen Reader support")
    has_ndis_funding: bool = False
    registered_provider: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class AllergyConditionNode(BaseModel):
    id: str
    name: str = Field(..., description="e.g., Penicillin Allergy, Type 1 Diabetes")
    category: str = Field(..., description="e.g., Food Allergy, Drug Allergy, Chronic Illness, Cardiovascular")
    epistemic_status: EpistemicStatus = EpistemicStatus.SELF_REPORTED_UNVERIFIED
    dispute_rationale: Optional[str] = Field(None, description="Explanation if marked as disputed, misdiagnosed, or unconfirmed")
    date_onset: Optional[date] = None
    linked_evidence_uris: List[str] = Field(default_factory=list, description="URIs or IDs of reports, tests, or clinical documents supporting/refuting this claim")
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT


class DwellingType(str, Enum):
    FIXED_HOUSE = "fixed-house"
    COUCH_SURFING = "couch-surfing"
    ROUGH_SLEEPING = "rough-sleeping"
    MOBILE_HOME_VAN = "mobile-home-van"
    CAMPING_TENT = "camping-tent"
    OTHER = "other"


class SleepSecurityLevel(str, Enum):
    SECURE_CAMPGROUND = "secure-campground"
    PUBLIC_PARKING_MEDIUM_RISK = "public-parking-medium-risk"
    UNPROTECTED_ROUGH_CAMPING_HIGH_RISK = "unprotected-rough-camping-high-risk"


class SocialFoundationsRecord(BaseModel):
    id: str
    dwelling_type: DwellingType
    homelessness_or_insecure_sleep: bool = False
    sleep_insecurity_reason: Optional[str] = Field(None, description="e.g. poverty, family separation, travel, etc.")
    threat_of_violence: bool = False
    actual_violence_experienced: bool = False
    environmental_hazards: List[str] = Field(default_factory=list, description="e.g. black mould, dampness, insecure lock, lack of heating/cooling")
    is_home_distinct_from_dwelling: bool = False
    is_trapped_at_location: bool = False
    trapped_reason: Optional[str] = Field(None, description="e.g. financial factors, domestic situations, unable to leave")
    deeply_unhappy_or_threatened: bool = False
    subjective_safety_score: int = Field(..., description="Subjective feeling of safety from 1 to 10")
    feels_unsafe_due_to_own_behaviors: bool = False
    own_behaviors_detail: Optional[str] = Field(None, description="Explanation if feeling unsafe is related to own health/behaviors/clinical episodes")
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT


class WalkaboutProfile(BaseModel):
    id: str
    shelter_type: str = Field(..., description="e.g. Van, Caravan, Tent, Swag, None")
    sleep_security_level: SleepSecurityLevel
    has_water: bool = False
    has_food_storage: bool = False
    has_hygiene_facilities: bool = False
    has_power: bool = False
    transit_frequency: str = Field(..., description="e.g. Daily, Weekly, Nomadic, Seasonal")
    transit_details: Optional[str] = None
    notes: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT
