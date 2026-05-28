from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


class AdherenceStatus(str, Enum):
    TAKEN = "completed"
    MISSED = "not-done"
    STOPPED = "stopped"
    ON_HOLD = "on-hold"
    UNKNOWN = "unknown"


class DataQualityTag(str, Enum):
    EXACT = "exact"
    ESTIMATE = "estimate"
    DEVICE_IMPORTED = "device-imported"
    SELF_REPORT = "self-report"


class SubstanceCategory(str, Enum):
    PRESCRIBED = "prescribed"
    OVER_THE_COUNTER = "over-the-counter"
    SUPPLEMENT = "supplement"
    LEGAL_RECREATIONAL = "legal-recreational"  # e.g., Alcohol, Nicotine, Caffeine
    ILLICIT = "illicit"


class MedicationAdministration(BaseModel):
    """FHIR MedicationAdministration mapped for adherence tracking, including broader substances."""

    id: str
    patient_id: str
    medication_name: str
    category: SubstanceCategory = Field(default=SubstanceCategory.PRESCRIBED)
    status: AdherenceStatus = Field(..., description="Adherence status")
    effective_time: datetime = Field(
        ..., description="When the dose was taken or missed"
    )
    quality_tag: DataQualityTag = Field(default=DataQualityTag.EXACT)
    privacy_mode: PrivacyMode = Field(default=PrivacyMode.MODE_B_PRIVILEGED, description="Illicit substances should default to Mode A")

    # Proxy support
    recorded_by_proxy_id: Optional[str] = Field(
        None, description="If carer-logged, links to RelatedPerson ID"
    )
    notes: Optional[str] = Field(
        None, description="Reason for missing/stopping or general notes"
    )
