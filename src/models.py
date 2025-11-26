from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class MeasurementValue(BaseModel):
    value: float
    confidence: float


class MeasurementResponse(BaseModel):
    height_cm: float
    measurements: Dict[str, MeasurementValue]
    used_images: List[str]
    warnings: List[str] = Field(default_factory=list)


class MeasurementRequest(BaseModel):
    height_cm: Optional[float] = None
    height_inches: Optional[float] = None
    gender: Optional[str] = None
    age: Optional[int] = None
