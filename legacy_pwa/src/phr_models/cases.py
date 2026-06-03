# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# https://www.linkedin.com/in/ubiquitous/
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Case Management & Claims — Pydantic models.

Enables users to manage "case files" tracking hypotheses, claims, routine checks,
or interval tests. Integrates with My Health Record/Solid pod architecture for
evidence collection, data-linking (Samsung Health), and proxy-consent controls.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class CaseCategory(str, Enum):
    SUSPECTED_CONDITION = "suspected-condition"
    ROUTINE_CHECK = "routine-check"
    INTERVAL_TEST = "interval-test"
    OTHER = "other"

class CaseStatus(str, Enum):
    SUSPECTED = "suspected"
    INVESTIGATING = "investigating"
    ACTIVE = "active"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"

class CaseTask(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed_date: Optional[date] = None
    is_completed: bool = False

class CaseFile(BaseModel):
    id: str
    patient_id: str
    title: str
    category: CaseCategory
    status: CaseStatus = CaseStatus.SUSPECTED
    hypothesis_or_claim: str = Field(..., description="The core claim, hypothesis, or reason for the case file")
    date_created: datetime
    date_updated: datetime
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT
    
    # Links & Metadata
    supporting_documents: List[str] = Field(default_factory=list, description="Linked SupportingDocument IDs")
    linked_psych_observations: List[str] = Field(default_factory=list, description="Linked PsychiatryObservation IDs")
    linked_datatypes: List[str] = Field(default_factory=list, description="Linked Samsung Health data types (e.g. com.samsung.shealth.sleep)")
    
    tasks: List[CaseTask] = Field(default_factory=list)
    notes: Optional[str] = None
