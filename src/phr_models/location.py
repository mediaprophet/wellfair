from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode


class SemanticCategory(str, Enum):
    HOME = "home"
    WORK = "work"
    MEDICAL_FACILITY = "medical-facility"
    TRAVEL = "travel"
    OTHER = "other"


class GeoEvent(BaseModel):
    """Custom high-volume time-series geospatial event."""

    id: str
    patient_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    category: SemanticCategory = Field(default=SemanticCategory.OTHER)

    privacy_mode: PrivacyMode = Field(
        default=PrivacyMode.MODE_C_SHARED,
        description="Locations default to lower sensitivity unless tagged",
    )
    linked_symptom_id: Optional[str] = Field(
        None,
        description="Link to PsychiatryObservation to correlate environment with mood/symptoms",
    )
