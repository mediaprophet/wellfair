from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode, LegalBasis

class ActorType(str, Enum):
    ORGANIZATION = "organization"
    PRACTITIONER = "practitioner"
    DELEGATE = "delegate"
    SYNTHETIC_AGENT = "synthetic_agent"

class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    SELF_CLAIMED = "self_claimed"

class Actor(BaseModel):
    """Represents an organization, practitioner, delegate, or synthetic agent."""
    id: str
    actor_type: ActorType
    name: str
    organization: Optional[str] = None
    qualifications: List[str] = Field(default_factory=list, description="Degrees, credentials, registrations, certifications")
    roles: List[str] = Field(default_factory=list, description="Roles they perform in the welfare ecosystem")
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    did_uri: Optional[str] = Field(None, description="Decentralized Identifier (DID) URI")

class DelegationRule(BaseModel):
    """Granular access policy linking an Actor to patient records and claims."""
    id: str
    patient_id: str
    actor_id: str
    granted_roles: List[str] = Field(default_factory=list, description="e.g. read_pathology, verify_claims")
    legal_basis: LegalBasis
    privacy_mode_limit: PrivacyMode = Field(default=PrivacyMode.MODE_B_PRIVILEGED, description="The maximum privacy mode clearance")
    allowed_record_types: List[str] = Field(default_factory=list, description="Whitelist of model names (e.g. PathologyObservation)")
    restricted_records: List[str] = Field(default_factory=list, description="Blacklist of model names")
    linked_case_ids: List[str] = Field(default_factory=list, description="Scope limited to these case files")
    is_active: bool = Field(default=True)

def evaluate_access(actor: Actor, rule: DelegationRule, record: Any) -> tuple[bool, list[str]]:
    """
    Evaluates whether an Actor can access a specific record under a DelegationRule.
    Returns (access_granted: bool, evaluation_log: list[str]).
    """
    log = []
    log.append(f"Starting access evaluation for Actor '{actor.name}' ({actor.actor_type.value})")
    
    if not rule.is_active:
        log.append("DENIED: Delegation rule is inactive.")
        return False, log
    log.append("OK: Delegation rule is active.")
    
    # Check Actor binding
    if rule.actor_id != actor.id:
        log.append(f"DENIED: Rule is bound to actor ID '{rule.actor_id}', but evaluator received ID '{actor.id}'.")
        return False, log
        
    # Get record privacy mode
    record_privacy = getattr(record, "privacy_mode", None)
    if record_privacy is not None:
        log.append(f"Check: Record has privacy mode '{record_privacy.name}' ({record_privacy.value})")
        log.append(f"Check: Actor clearance limit is '{rule.privacy_mode_limit.name}' ({rule.privacy_mode_limit.value})")
        
        # Privacy modes: A is highest (Strict), B is Privileged, C is normal (Shared)
        # MODE_A_STRICT = "V"
        # MODE_B_PRIVILEGED = "R"
        # MODE_C_SHARED = "N"
        # Hierarchy: A requires A clearance. B requires A or B clearance. C requires A, B, or C clearance.
        clearance_hierarchy = {
            PrivacyMode.MODE_A_STRICT: 3,
            PrivacyMode.MODE_B_PRIVILEGED: 2,
            PrivacyMode.MODE_C_SHARED: 1
        }
        
        rec_val = clearance_hierarchy.get(record_privacy, 1)
        actor_val = clearance_hierarchy.get(rule.privacy_mode_limit, 1)
        
        if actor_val < rec_val:
            log.append(f"DENIED: Actor clearance level ({rule.privacy_mode_limit.name}) is insufficient for record level ({record_privacy.name}).")
            return False, log
        log.append("OK: Privacy mode clearance verified.")
    else:
        log.append("Note: Record does not declare an explicit privacy_mode (access allowed by default).")
        
    # Check record type whitelist / blacklist
    record_class_name = record.__class__.__name__
    log.append(f"Check: Record model class is '{record_class_name}'")
    
    if rule.restricted_records:
        if record_class_name in rule.restricted_records:
            log.append(f"DENIED: Record class '{record_class_name}' is blacklisted in rule.restricted_records.")
            return False, log
            
    if rule.allowed_record_types:
        if record_class_name not in rule.allowed_record_types:
            log.append(f"DENIED: Record class '{record_class_name}' is not in rule.allowed_record_types whitelist.")
            return False, log
        log.append(f"OK: Record class '{record_class_name}' is whitelisted.")
        
    log.append(f"GRANTED: All policies evaluated successfully. Access allowed for '{actor.name}'.")
    return True, log
