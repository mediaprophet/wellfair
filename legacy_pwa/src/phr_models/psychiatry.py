from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


class ObservationContext(str, Enum):
    SELF_REPORTED = "self-reported"
    CARER_OBSERVED = "carer-observed"
    CLINICIAN_OBSERVED = "clinician-observed"


class DataQualityTag(str, Enum):
    EXACT = "exact"
    ESTIMATE = "estimate"


class PsychiatryObservation(BaseModel):
    """FHIR Observation mapped for trauma-informed psych tracking."""

    id: str
    patient_id: str
    date_recorded: datetime
    context: ObservationContext
    quality_tag: DataQualityTag = Field(default=DataQualityTag.ESTIMATE)

    # Links to ProxyConsent engine
    recorded_by_proxy_id: Optional[str] = Field(
        None, description="If carer-observed, links to RelatedPerson ID"
    )
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_A_STRICT,
        description="Defaults to strict for mental health",
    )

    symptom_code: str = Field(
        ..., description="SNOMED CT code for the observed symptom/mood"
    )
    notes: Optional[str] = Field(
        None, description="Free text therapy notes or carer observations"
    )

    linked_medication_id: Optional[str] = Field(
        None, description="Link to psychotropic MedicationStatement"
    )
