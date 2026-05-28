from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


class DiagnosticReportStatus(str, Enum):
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"


class PathologyObservation(BaseModel):
    """FHIR Observation mapped for individual lab results."""

    id: str
    test_name: str = Field(..., description="e.g. Blood Glucose")
    value: float
    unit: str
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_B_PRIVILEGED,
        description="Can be set to Mode A for sensitive tests",
    )


class DiagnosticReport(BaseModel):
    """FHIR DiagnosticReport representing the full pathology PDF."""

    id: str
    patient_id: str
    date_issued: datetime
    status: DiagnosticReportStatus = Field(default=DiagnosticReportStatus.PRELIMINARY)
    pdf_attachment_uri: str = Field(
        ..., description="Secure URI to the encrypted original PDF"
    )
    observations: List[PathologyObservation] = Field(default_factory=list)

    privacy_mode: PrivacyMode = Field(default=PrivacyMode.MODE_B_PRIVILEGED)
    recorded_by_proxy_id: Optional[str] = Field(
        None, description="If imported by carer"
    )
