import cv2
import numpy as np
from typing import List, Dict
from .pose_detector import PoseDetector
from .measurement_engine import MeasurementEngine
from .models import MeasurementResponse, MeasurementValue


class ImageProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
    
    def process_images(self, image_files: List[bytes], image_names: List[str], height_cm: float) -> MeasurementResponse:
        all_measurements = []
        used_images = []
        warnings = []
        
        measurement_engine = MeasurementEngine(height_cm)
        
        for img_bytes, img_name in zip(image_files, image_names):
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                warnings.append(f"Failed to decode image: {img_name}")
                continue
            
            landmarks, pose_confidence = self.pose_detector.detect_landmarks(image)
            
            if landmarks is None or pose_confidence < 0.3:
                warnings.append(f"Poor pose detection in {img_name} (confidence: {pose_confidence:.2f})")
                continue
            
            scale, scale_confidence = measurement_engine.compute_scale_factor(landmarks)
            
            if scale is None or scale_confidence < 0.3:
                warnings.append(f"Could not calibrate scale for {img_name}")
                continue
            
            measurements = measurement_engine.estimate_measurements(landmarks, scale, image)
            
            if measurements:
                all_measurements.append(measurements)
                used_images.append(img_name)
        
        if not all_measurements:
            warnings.append("No valid measurements could be extracted from any image")
            return MeasurementResponse(
                height_cm=height_cm,
                measurements={},
                used_images=[],
                warnings=warnings
            )
        
        combined_measurements = self._combine_measurements(all_measurements)
        
        return MeasurementResponse(
            height_cm=height_cm,
            measurements=combined_measurements,
            used_images=used_images,
            warnings=warnings
        )
    
    def _combine_measurements(self, all_measurements: List[Dict]) -> Dict[str, MeasurementValue]:
        measurement_keys = set()
        for m in all_measurements:
            measurement_keys.update(m.keys())
        
        combined = {}
        
        for key in measurement_keys:
            values = []
            confidences = []
            
            for m in all_measurements:
                if key in m:
                    values.append(m[key]['value'])
                    confidences.append(m[key]['confidence'])
            
            if values:
                weights = np.array(confidences)
                weights = weights / weights.sum() if weights.sum() > 0 else np.ones_like(weights) / len(weights)
                
                avg_value = np.average(values, weights=weights)
                avg_confidence = np.mean(confidences)
                
                combined[key] = MeasurementValue(
                    value=round(float(avg_value), 1),
                    confidence=round(float(avg_confidence), 2)
                )
        
        return combined
