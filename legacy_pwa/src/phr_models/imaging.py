from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


class ImagingModality(str, Enum):
    MRI = "MRI"
    CT = "CT"
    PET = "PET"
    ULTRASOUND = "Ultrasound"
    XRAY = "X-Ray"


class ImagingSeries(BaseModel):
    """Represents a specific volumetric series or slice sequence within a study."""

    id: str
    series_description: str = Field(..., description="e.g. T1 Axial, FLAIR")
    modality: ImagingModality
    slice_thickness_mm: Optional[float] = None
    number_of_slices: int
    dicom_archive_uri: str = Field(..., description="Secure URI to the raw DICOM slices")


class MedicalImagingStudy(BaseModel):
    """FHIR ImagingStudy representing the full volumetric medical scan."""

    id: str
    patient_id: str
    date_recorded: datetime
    study_description: str = Field(..., description="e.g. MRI Brain without contrast")
    modality: ImagingModality
    series: List[ImagingSeries] = Field(default_factory=list)

    # Volumetric imaging is highly sensitive and identifiable. Defaults to Sanctuary Mode.
    # Use the string value "S" to avoid Enum lookup failures during Pyodide/Stlite import.
    privacy_mode: str = Field(default="S", description="S = Sanctuary Mode (fully locked)")
    recorded_by_proxy_id: Optional[str] = Field(
        None, description="If imported by carer"
    )
