from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, Field

from src.utils import ROOT

class PsychiatricAssessmentBase(BaseModel):
    """Base model for a psychiatric questionnaire assessment.

    Attributes
    ----------
    id: str
        Unique identifier for the assessment record.
    name: str
        Human‑readable name of the questionnaire (e.g., "BDI‑II").
    date_taken: date
        Date the assessment was performed.
    pdf_uri: Optional[str]
        Absolute file URI where the original PDF is stored.
    scores: Dict[str, Optional[float]]
        Mapping of questionnaire item identifiers to numeric scores (or None if not filled).
    """

    id: str = Field(..., description="Unique identifier for the assessment")
    name: str = Field(..., description="Name of the questionnaire")
    date_taken: date = Field(default_factory=date.today, description="Date of assessment")
    pdf_uri: Optional[str] = Field(None, description="Path/URI to the stored PDF file")
    scores: Dict[str, Optional[float]] = Field(default_factory=dict, description="Item scores")
    rdf_status: str = Field("pending", description="RDF generation status")

    class Config:
        # Allow population by field name for future extensions
        validate_by_name = True

# Example concrete subclasses – can be expanded later
class BDI2Assessment(PsychiatricAssessmentBase):
    name: str = "BDI‑II"
    # BDI‑II has 21 items labelled "Q1" … "Q21"
    scores: Dict[str, Optional[int]] = Field(default_factory=lambda: {f"Q{i}": None for i in range(1, 22)})

class AQ10Assessment(PsychiatricAssessmentBase):
    name: str = "AQ‑10"
    scores: Dict[str, Optional[int]] = Field(default_factory=lambda: {f"Q{i}": None for i in range(1, 11)})

class DASS21Assessment(PsychiatricAssessmentBase):
    name: str = "DASS‑21"
    scores: Dict[str, Optional[int]] = Field(default_factory=lambda: {f"Q{i}": None for i in range(1, 22)})

class K10Assessment(PsychiatricAssessmentBase):
    name: str = "K10"
    scores: Dict[str, Optional[int]] = Field(default_factory=lambda: {f"Q{i}": None for i in range(1, 11)})
