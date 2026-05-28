from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class TrustLevel(str, Enum):
    VERIFIED_CLINICAL = "verified-clinical"
    VERIFIED_DEVICE = "verified-device"
    UNVERIFIED_SELF = "unverified-self"
    UNVERIFIED_THIRD_PARTY = "unverified-third-party"
    OUT_OF_SCOPE = "out-of-scope"
    CONFLICTING = "conflicting"

class AuthorType(str, Enum):
    SELF = "self"
    CLINICIAN_GP = "clinician-gp"
    CLINICIAN_SPECIALIST = "clinician-specialist"
    PATHOLOGY_LAB = "pathology-lab"
    CARER = "carer"
    DEVICE_SENSOR = "device-sensor"

class InformationSource(BaseModel):
    """Represents the origin of a document or claim."""
    id: str
    author_type: AuthorType
    author_name: str
    organization: Optional[str] = None
    credentials: Optional[str] = Field(None, description="e.g. AHPRA number, NATA accreditation")
    date_recorded: datetime

class ClinicalClaim(BaseModel):
    """An atomic assertion extracted from a document."""
    id: str
    source_document_id: str
    subject_id: str = Field(default="patient-self")
    domain: str = Field(..., description="e.g. Pathology, Psychiatry, Medication")
    claim_text: str = Field(..., description="The raw assertion text or key-value")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Structured parsed data")
    
    # Claim Evaluation
    trust_level: TrustLevel = Field(default=TrustLevel.UNVERIFIED_SELF)
    evaluation_notes: Optional[str] = Field(None, description="Why this trust level was assigned")
    
    privacy_mode: PrivacyMode = Field(default=PrivacyMode.MODE_B_PRIVILEGED)

class ContentPackage(BaseModel):
    """A container for a processed document and its resulting structured claims."""
    id: str
    original_file_name: str
    upload_date: datetime
    source: InformationSource
    raw_extracted_text: str
    claims: List[ClinicalClaim] = Field(default_factory=list)
    status: str = Field(default="Draft", description="Draft, Approved, Rejected")
    
    def evaluate_claims(self):
        """Basic semantic evaluation based on author scope."""
        for claim in self.claims:
            if self.source.author_type == AuthorType.PATHOLOGY_LAB and claim.domain == "Pathology":
                claim.trust_level = TrustLevel.VERIFIED_CLINICAL
                claim.evaluation_notes = "In-scope assertion by accredited laboratory."
            elif self.source.author_type == AuthorType.SELF and claim.domain == "Pathology":
                claim.trust_level = TrustLevel.UNVERIFIED_SELF
                claim.evaluation_notes = "Self-reported lab result. Requires formal verification."
            elif self.source.author_type == AuthorType.CLINICIAN_GP and claim.domain == "Psychiatry":
                claim.trust_level = TrustLevel.VERIFIED_CLINICAL
                claim.evaluation_notes = "GP observation. May require specialist for formal diagnosis."
            else:
                claim.trust_level = TrustLevel.UNVERIFIED_SELF
