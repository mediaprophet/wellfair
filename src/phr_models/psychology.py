"""Psychology domain models – therapy, formulation, attachment & Sub Rosa.

This module provides the Pydantic schemas for the Psychology section of
Episteme:WellFair, including the sensitive "Sub Rosa" confessional recording
system that allows clinically-relevant but socially-invisible data to remain
computationally active within the local vault.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.phr_models.proxy_consent import PrivacyMode


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TherapyModality(str, Enum):
    CBT = "Cognitive Behavioural Therapy"
    DBT = "Dialectical Behaviour Therapy"
    EMDR = "Eye Movement Desensitisation & Reprocessing"
    PSYCHODYNAMIC = "Psychodynamic Therapy"
    SCHEMA = "Schema Therapy"
    ACT = "Acceptance & Commitment Therapy"
    IFS = "Internal Family Systems"
    SOMATIC = "Somatic Experiencing"
    NARRATIVE = "Narrative Therapy"
    GROUP = "Group Therapy"
    OTHER = "Other / Mixed"


class AttachmentStyle(str, Enum):
    SECURE = "secure"
    ANXIOUS_PREOCCUPIED = "anxious-preoccupied"
    DISMISSIVE_AVOIDANT = "dismissive-avoidant"
    FEARFUL_AVOIDANT = "fearful-avoidant"
    DISORGANISED = "disorganised"


class SubRosaCategory(str, Enum):
    """Categories for clinically-relevant but socially-sensitive records."""
    SUBSTANCE_USE = "Substance Use"
    SEXUAL_HEALTH = "Sexual Health & Experiences"
    ENVIRONMENTAL_EXPOSURE = "Environmental Exposure"
    DOMESTIC_SITUATION = "Domestic Situation"
    PROFESSIONAL_CONFLICT = "Professional / NDA Conflict"
    LEGAL_ENTANGLEMENT = "Legal Entanglement"
    FINANCIAL_DURESS = "Financial Duress"
    DEVELOPMENTAL_TRAUMA = "Developmental Trauma"
    OTHER = "Other"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TherapySessionNote(BaseModel):
    """A single therapy session record."""
    id: str
    date: datetime = Field(default_factory=datetime.now)
    modality: TherapyModality = TherapyModality.CBT
    therapist_agent_id: Optional[str] = Field(
        None, description="DID or Agent Directory ID of the treating psychologist"
    )
    session_summary: str = ""
    homework: Optional[str] = None
    mood_pre: int = Field(5, ge=0, le=10, description="Mood score before session (0-10)")
    mood_post: int = Field(5, ge=0, le=10, description="Mood score after session (0-10)")
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT


class PsychologicalFormulation(BaseModel):
    """The '5 Ps' psychological formulation model."""
    id: str
    date_created: datetime = Field(default_factory=datetime.now)
    presenting_problems: List[str] = Field(default_factory=list)
    predisposing_factors: List[str] = Field(default_factory=list)
    precipitating_factors: List[str] = Field(default_factory=list)
    perpetuating_factors: List[str] = Field(default_factory=list)
    protective_factors: List[str] = Field(default_factory=list)
    formulation_narrative: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT


class AttachmentStyleRecord(BaseModel):
    """Self-assessed or clinician-assessed attachment style."""
    id: str
    date_assessed: date = Field(default_factory=date.today)
    style: AttachmentStyle = AttachmentStyle.SECURE
    confidence: str = "Medium"  # Low / Medium / High
    assessor: str = "Self"  # Self, Clinician Name, etc.
    notes: Optional[str] = None


class SubRosaRecord(BaseModel):
    """A clinically-relevant but socially-invisible sensitive record.

    These records live in the Veiled Graph and are computationally active
    (can trigger Semantic Tripwires) but are never surfaced to external
    agents without explicit user consent.
    """
    id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    category: SubRosaCategory
    narrative: str = Field(
        ..., description="The sensitive fact or observation (encrypted at rest)"
    )
    clinical_relevance: str = Field(
        "", description="Why this matters medically – drug interactions, contraindications, etc."
    )
    semantic_tags: List[str] = Field(
        default_factory=list,
        description="SNOMED/ICD codes or free-text tags for conditions this may affect"
    )
    tripwire_rules: List[str] = Field(
        default_factory=list,
        description="Query patterns that should trigger Semantic Tripwires"
    )
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_A_STRICT,
        description="Always Mode A (self + doctor) or Sanctuary-only"
    )
    hypothesis_flag: bool = Field(
        False, description="True if this is a suspicion rather than a confirmed fact"
    )
    provenance_hash: Optional[str] = Field(
        None, description="SHA-256 hash for DLT anchoring"
    )

    def compute_provenance_hash(self) -> str:
        """Generate a deterministic SHA-256 hash for immutable provenance."""
        payload = f"{self.id}|{self.category.value}|{self.narrative}|{self.timestamp.isoformat()}"
        h = hashlib.sha256(payload.encode()).hexdigest()
        self.provenance_hash = h
        return h
