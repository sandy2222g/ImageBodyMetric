from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class MeasurementValue(BaseModel):
    value: float
    confidence: float
    method: Optional[str] = None


class ImageQuality(BaseModel):
    overall_score: float
    resolution_score: float
    brightness_score: float
    contrast_score: float
    sharpness_score: float
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class ImageAnalysis(BaseModel):
    name: str
    quality: Dict[str, Any]
    view_type: str
    pose_confidence: float
    used: bool


class MeasurementResponse(BaseModel):
    height_cm: float
    measurements: Dict[str, MeasurementValue]
    used_images: List[str]
    warnings: List[str] = Field(default_factory=list)


class EnhancedMeasurementResponse(BaseModel):
    height_cm: float
    measurements: Dict[str, MeasurementValue]
    used_images: List[str]
    warnings: List[str] = Field(default_factory=list)
    image_analyses: List[ImageAnalysis] = Field(default_factory=list)
    multi_view_fusion: bool = False
    accuracy_rating: float = 0.0


class MeasurementRequest(BaseModel):
    height_cm: Optional[float] = None
    height_inches: Optional[float] = None
    gender: Optional[str] = None
    age: Optional[int] = None
