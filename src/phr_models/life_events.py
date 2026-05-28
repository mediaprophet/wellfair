# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Socioeconomic Wellbeing & Life Events — Pydantic models.

Captures major life transitions (job loss, divorce, homelessness, etc.)
as pivotal nodes that intersect financial, legal, professional, housing,
and relational domains.  Every record integrates with the PrivacyMode
consent engine and supports cross-linking to psychiatric observations,
proxy relationships, and supporting documents.

Reference: instructions/social_biostatistics
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class LifeEventCategory(str, Enum):
    """Taxonomy of major life events (Section 3, social_biostatistics)."""
    JOB_LOSS = "job-loss"
    DIVORCE_SEPARATION = "divorce-separation"
    BANKRUPTCY = "bankruptcy"
    HOMELESSNESS = "homelessness"
    HEALTH_CRISIS = "health-crisis"
    INCARCERATION = "incarceration"
    MIGRATION = "migration"
    NATURAL_DISASTER = "natural-disaster"
    BEREAVEMENT = "bereavement"
    DOMESTIC_VIOLENCE = "domestic-violence"
    DISABILITY_ONSET = "disability-onset"
    EDUCATION_TRANSITION = "education-transition"
    RETIREMENT = "retirement"
    OTHER = "other"


class WellbeingDimension(str, Enum):
    """OECD Well-being Framework aligned impact dimensions (Section 2)."""
    INCOME_WEALTH = "income-wealth"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    HEALTH_PHYSICAL = "health-physical"
    HEALTH_MENTAL = "health-mental"
    EDUCATION_SKILLS = "education-skills"
    SOCIAL_CONNECTIONS = "social-connections"
    WORK_LIFE_BALANCE = "work-life-balance"
    CIVIC_ENGAGEMENT = "civic-engagement"
    SAFETY = "safety"
    SUBJECTIVE_WELLBEING = "subjective-wellbeing"
    RIGHTS_LEGAL = "rights-legal"


class SeverityLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentCategory(str, Enum):
    """Categories for supporting documents (Section 4)."""
    LEGAL = "legal"
    PROFESSIONAL = "professional"
    FINANCIAL = "financial"
    HOUSING = "housing"
    RELATIONAL = "relational"
    GOVERNMENT = "government"
    MEDICAL = "medical"


class RecoveryStatus(str, Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    STABLE = "stable"
    RESOLVED = "resolved"


class MaslowLayer(str, Enum):
    """Optional Maslow's hierarchy tagging for multi-model vault views."""
    PHYSIOLOGICAL = "physiological"
    SAFETY = "safety"
    BELONGING = "belonging"
    ESTEEM = "esteem"
    SELF_ACTUALISATION = "self-actualisation"


class DataQualityTag(str, Enum):
    EXACT = "exact"
    ESTIMATE = "estimate"
    SELF_REPORT = "self-report"
    PROFESSIONAL_VERIFIED = "professional-verified"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class SupportingDocument(BaseModel):
    """Lightweight metadata reference to an encrypted document.

    The vault stores a URI to the encrypted original; full document
    parsing (PDF extraction of court orders, etc.) is a future iteration.
    """

    id: str
    title: str = Field(..., description="Human-readable document title")
    category: DocumentCategory
    document_uri: str = Field(
        ..., description="Secure URI to the encrypted stored document"
    )
    date_issued: Optional[datetime] = None
    jurisdiction: Optional[str] = Field(
        None,
        description="e.g. 'AU-NSW', 'AU-FED', 'AU-QLD' or ISO 3166-2 code",
    )
    description: Optional[str] = None
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_A_STRICT,
        description="Legal documents default to strict privacy",
    )


class WellbeingImpact(BaseModel):
    """Assessment of how a life event impacts a specific wellbeing dimension."""

    dimension: WellbeingDimension
    severity: SeverityLevel
    description: Optional[str] = Field(
        None, description="Narrative describing the impact"
    )
    date_assessed: Optional[datetime] = None


class RecoveryIndicator(BaseModel):
    """A milestone or support action in the recovery pathway post-event."""

    id: str
    description: str = Field(
        ..., description="e.g. 'Register with Centrelink', 'Attend retraining'"
    )
    status: RecoveryStatus = Field(default=RecoveryStatus.NOT_STARTED)
    target_date: Optional[date] = None
    completed_date: Optional[date] = None
    linked_service: Optional[str] = Field(
        None,
        description="Service or organisation supporting this milestone",
    )


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

class LifeEvent(BaseModel):
    """Core life event record for the Personal Welfare Informatics Vault.

    Maps to the taxonomy in Section 3 of social_biostatistics.
    Integrates with ProxyConsent (privacy_mode, proxy recording),
    PsychiatryObservation (cross-linked symptoms), and the
    SupportingDocument registry.
    """

    id: str
    patient_id: str
    event_category: LifeEventCategory
    title: str = Field(..., description="Short human-readable event title")
    description: Optional[str] = Field(
        None, description="Narrative context about the event"
    )

    # Temporal
    trigger_date: datetime = Field(
        ..., description="When the event started or was triggered"
    )
    end_date: Optional[datetime] = Field(
        None, description="None for ongoing events"
    )

    severity: SeverityLevel = Field(default=SeverityLevel.MODERATE)

    # Privacy & proxy
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_A_STRICT,
        description="Life events default to strict — many involve trauma",
    )
    recorded_by_proxy_id: Optional[str] = Field(
        None, description="If logged by a carer, links to RelatedPerson ID"
    )
    involved_parties: List[str] = Field(
        default_factory=list,
        description="RelatedPerson IDs of people involved in the event",
    )

    # Impact & recovery
    wellbeing_impacts: List[WellbeingImpact] = Field(default_factory=list)
    supporting_documents: List[SupportingDocument] = Field(default_factory=list)
    recovery_indicators: List[RecoveryIndicator] = Field(default_factory=list)

    # Cross-references
    linked_psych_observation_ids: List[str] = Field(
        default_factory=list,
        description="Links to PsychiatryObservation IDs triggered by this event",
    )
    linked_medication_ids: List[str] = Field(
        default_factory=list,
        description="Links to MedicationAdministration IDs related to this event",
    )

    # Multi-model vault support
    maslow_layer: Optional[MaslowLayer] = Field(
        None,
        description="Optional Maslow's hierarchy layer for needs-based vault views",
    )

    data_quality_tag: DataQualityTag = Field(default=DataQualityTag.SELF_REPORT)
    notes: Optional[str] = Field(
        None, description="Free-text notes or journal entries about the event"
    )
