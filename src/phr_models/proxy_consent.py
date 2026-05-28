from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PrivacyMode(str, Enum):
    MODE_A_STRICT = "V"  # Very Restricted (Self + Doctor only)
    MODE_B_PRIVILEGED = "R"  # Restricted (Doctor-facing)
    MODE_C_SHARED = "N"  # Normal (Carer/Family shared)
    MODE_S_SANCTUARY = "S"  # Sanctuary Mode (Locked down completely)


class LegalBasis(str, Enum):
    EXPLICIT_CONSENT = "explicit-consent"
    GUARDIAN_AUTHORITY = "guardian-authority"
    MHA_NOMINATED = "mha-nominated"
    SAFETY_OVERRIDE = "safety-override"


class ProxyRelationship(str, Enum):
    PARENT = "PRN"
    DEPENDENT = "DEP"
    GUARDIAN = "GUARD"
    PARTNER = "PART"
    CARER = "CARE"


class RelatedPerson(BaseModel):
    """FHIR AU Core mapped RelatedPerson for proxy contexts."""

    id: str = Field(..., description="Unique ID for the proxy/related person")
    patient_id: str = Field(..., description="The primary subject of the record")
    relationship: ProxyRelationship = Field(
        ..., description="SNOMED/HL7 relationship code"
    )
    is_anonymous: bool = Field(
        False, description="True if the proxy must remain de-identified for safety"
    )
    description: Optional[str] = Field(
        None, description="Minimally identifying description of the proxy"
    )


class ProxyConsent(BaseModel):
    """FHIR Consent resource mapping bridging the Patient and the Proxy."""

    id: str
    patient_id: str
    proxy_id: str = Field(
        ..., description="References the RelatedPerson.id acting as the proxy"
    )
    legal_basis: LegalBasis
    privacy_mode: PrivacyMode = Field(default=PrivacyMode.MODE_A_STRICT)
    audit_silenced: bool = Field(
        False,
        description="If True, suppresses standard audit trails for safety-override reasons.",
    )
