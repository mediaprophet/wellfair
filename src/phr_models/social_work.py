# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""
Social Work & Assistance — Pydantic models.

Defines schemas to support individuals requiring social work assistance
(housing, food, etc.), and government/social security documentation.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class AssistanceCategory(str, Enum):
    HOUSING = "housing"
    FOOD = "food"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    TRANSPORT = "transport"
    OTHER = "other"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class AssistanceStatus(str, Enum):
    IDENTIFIED = "identified"
    REFERRAL_SENT = "referral-sent"
    PROGRAM_ACTIVE = "program-active"
    RESOLVED = "resolved"

class AssistanceNeed(BaseModel):
    id: str
    category: AssistanceCategory
    urgency: UrgencyLevel
    description: str
    date_logged: datetime
    status: AssistanceStatus = AssistanceStatus.IDENTIFIED
    provider_name: Optional[str] = Field(None, description="e.g., Salvation Army, Department of Housing")
    notes: Optional[str] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class SocialSecurityStatus(str, Enum):
    APPLIED = "applied"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    ACTIVE = "active"

class PaymentFrequency(str, Enum):
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"
    ONE_OFF = "one-off"

class SocialSecurityRecord(BaseModel):
    id: str
    agency_name: str = Field(..., description="e.g., Centrelink, SSA")
    payment_type: str = Field(..., description="e.g., JobSeeker, Disability Support Pension")
    status: SocialSecurityStatus = SocialSecurityStatus.ACTIVE
    amount: float
    frequency: PaymentFrequency
    start_date: date
    end_date: Optional[date] = None
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class GovernmentLetter(BaseModel):
    id: str
    title: str = Field(..., description="e.g., Benefit Review Notice")
    sender_agency: str = Field(..., description="e.g., Centrelink, Department of Housing")
    date_received: date
    summary: str
    action_required: Optional[str] = None
    action_due_date: Optional[date] = None
    document_uri: Optional[str] = Field(None, description="Secure URI to the stored letter PDF")
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT
