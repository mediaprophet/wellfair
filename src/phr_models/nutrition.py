from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from src.phr_models.proxy_consent import PrivacyMode

class IntakeType(str, Enum):
    FOOD_MEAL = "food-meal"
    FOOD_SNACK = "food-snack"
    FLUID_WATER = "fluid-water"
    FLUID_SUGARY = "fluid-sugary"
    FLUID_CAFFEINATED = "fluid-caffeinated"
    FLUID_ALCOHOL = "fluid-alcohol"

class FastingState(str, Enum):
    FASTING = "fasting"
    NON_FASTING = "non-fasting"
    UNKNOWN = "unknown"

class NutritionIntake(BaseModel):
    """FHIR NutritionIntake mapped for food, fluid, and socioeconomic tracking."""
    id: str
    patient_id: str
    timestamp: datetime
    intake_type: IntakeType
    description: str = Field(..., description="e.g. 1 glass of wine, bowl of cereal")
    
    # Optional metrics
    calories_kcals: Optional[float] = None
    fluid_volume_ml: Optional[float] = None
    
    # Context
    fasting_state: FastingState = Field(default=FastingState.UNKNOWN, description="Useful context for pathology")
    socioeconomic_flag: bool = Field(default=False, description="Flag for food insecurity / skipped meals due to financial stress")
    
    privacy_mode: PrivacyMode = Field(default=PrivacyMode.MODE_C_SHARED)
    
    # Links
    linked_location_id: Optional[str] = Field(None, description="Where did this occur?")
    linked_psych_obs_id: Optional[str] = Field(None, description="If linked to eating disorder/mood observation")
    recorded_by_proxy_id: Optional[str] = Field(None, description="If logged by carer/guardian")
