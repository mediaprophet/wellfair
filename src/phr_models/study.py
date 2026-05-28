# Copyright (C) 2025-2026 Timothy Charles Holborn <timothy.holborn@gmail.com>
# SPDX-License-Identifier: CC-BY-NC-ND-4.0

"""
Study & Clinical Research Vault — Pydantic models.

Defines schemas for structured diagnostic forms, auto-population metadata,
research paper parsing, comorbidity/symptom classification, and cryptographically
signed study packages for cooperative care.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class FormQuestion(BaseModel):
    id: str
    text: str
    options: List[str] = Field(default_factory=list, description="e.g., ['None of the time', 'A little', 'Some', 'Most', 'All of the time']")
    score_weights: List[int] = Field(default_factory=list, description="Mapping options to numeric scores, e.g., [1, 2, 3, 4, 5]")

class DiagnosticForm(BaseModel):
    id: str
    title: str = Field(..., description="e.g., Kessler K10 Distress Scale")
    questions: List[FormQuestion] = Field(default_factory=list)
    answers: Dict[str, str] = Field(default_factory=dict, description="Question ID to selected option string")
    score: int = Field(0, description="Total aggregated form score")
    autofill_source: Optional[str] = Field(None, description="e.g., 'Parsed chat transcript', 'Manual'")
    date_filled: datetime
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class ClinicalInsight(BaseModel):
    category: str = Field(..., description="e.g., Comorbidity, Cause, Symptom, Evolution")
    title: str
    description: str
    confidence_score: float = Field(..., description="0.0 to 1.0 extraction confidence")

class ResearchPaper(BaseModel):
    id: str
    title: str = Field(..., description="e.g., Diagnostic Indicators of Chronic Fatigue Syndromes")
    authors: str
    publication_date: date
    doi: Optional[str] = None
    extracted_insights: List[ClinicalInsight] = Field(default_factory=list)
    established_hypotheses: List[str] = Field(default_factory=list, description="Hypotheses formulated by the user/system based on this paper")
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT

class SharedStudyPackage(BaseModel):
    id: str
    recipient_did: str = Field(..., description="DID of recipient, e.g., did:web:laverty.com.au:labs")
    shared_form_ids: List[str] = Field(default_factory=list)
    shared_paper_ids: List[str] = Field(default_factory=list)
    signature: str = Field(..., description="Cryptographic signature of the user validating the package")
    date_shared: datetime
    privacy_mode: PrivacyMode = PrivacyMode.MODE_A_STRICT
