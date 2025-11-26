import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from .pose_detector import PoseDetector
from .enhanced_measurement import EnhancedMeasurementEngine
from .image_analyzer import ImageAnalyzer
from .models import MeasurementResponse, MeasurementValue, EnhancedMeasurementResponse, ImageAnalysis


class ImageProcessor:
    def __init__(self):
        self.pose_detector = PoseDetector()
        self.image_analyzer = ImageAnalyzer()
    
    def process_images(
        self, 
        image_files: List[bytes], 
        image_names: List[str], 
        height_cm: float,
        gender: Optional[str] = None
    ) -> MeasurementResponse:
        all_measurements = []
        used_images = []
        warnings = []
        
        measurement_engine = EnhancedMeasurementEngine(height_cm, gender)
        
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
            
            view_type = self.image_analyzer.detect_view_type(landmarks)
            measurements = measurement_engine.estimate_measurements_single_view(
                landmarks, scale, view_type
            )
            
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
    
    def process_images_enhanced(
        self,
        image_files: List[bytes],
        image_names: List[str],
        height_cm: float,
        gender: Optional[str] = None
    ) -> EnhancedMeasurementResponse:
        """
        Enhanced processing with image quality analysis, view detection,
        and multi-view fusion for improved accuracy.
        """
        processed_images = []
        front_data = None
        side_data = None
        all_measurements = []
        used_images = []
        warnings = []
        
        measurement_engine = EnhancedMeasurementEngine(height_cm, gender)
        
        for img_bytes, img_name in zip(image_files, image_names):
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                warnings.append(f"Failed to decode image: {img_name}")
                continue
            
            quality = self.image_analyzer.analyze_image_quality(image)
            
            if quality['issues']:
                warnings.extend([f"{img_name}: {issue}" for issue in quality['issues']])
            
            landmarks, pose_confidence = self.pose_detector.detect_landmarks(image)
            
            if landmarks is None or pose_confidence < 0.3:
                processed_images.append({
                    'name': img_name,
                    'quality': quality,
                    'view_type': 'unknown',
                    'pose_confidence': pose_confidence,
                    'used': False
                })
                warnings.append(f"Poor pose detection in {img_name}")
                continue
            
            view_type = self.image_analyzer.detect_view_type(landmarks)
            
            scale, scale_confidence = measurement_engine.compute_scale_factor(landmarks)
            
            if scale is None or scale_confidence < 0.3:
                processed_images.append({
                    'name': img_name,
                    'quality': quality,
                    'view_type': view_type,
                    'pose_confidence': pose_confidence,
                    'used': False
                })
                warnings.append(f"Could not calibrate scale for {img_name}")
                continue
            
            processed_images.append({
                'name': img_name,
                'quality': quality,
                'view_type': view_type,
                'pose_confidence': pose_confidence,
                'used': True
            })
            
            if view_type == "front" and front_data is None:
                front_data = (landmarks, scale)
            elif view_type in ["side", "left_side", "right_side"] and side_data is None:
                side_data = (landmarks, scale)
            
            measurements = measurement_engine.estimate_measurements_single_view(
                landmarks, scale, view_type
            )
            
            if measurements:
                all_measurements.append(measurements)
                used_images.append(img_name)
        
        if front_data and side_data:
            multi_view_measurements = measurement_engine.estimate_measurements_multi_view(
                front_data[0], side_data[0], front_data[1], side_data[1]
            )
            if multi_view_measurements:
                all_measurements.append(multi_view_measurements)
                warnings.append("Multi-view fusion applied for improved accuracy")
        
        if not all_measurements:
            warnings.append("No valid measurements could be extracted from any image")
            return EnhancedMeasurementResponse(
                height_cm=height_cm,
                measurements={},
                used_images=[],
                warnings=warnings,
                image_analyses=[
                    ImageAnalysis(**img) for img in processed_images
                ],
                multi_view_fusion=front_data is not None and side_data is not None,
                accuracy_rating=0.0
            )
        
        combined_measurements = self._combine_measurements(all_measurements)
        
        accuracy_rating = self._calculate_accuracy_rating(
            combined_measurements, 
            processed_images,
            front_data is not None and side_data is not None
        )
        
        return EnhancedMeasurementResponse(
            height_cm=height_cm,
            measurements=combined_measurements,
            used_images=used_images,
            warnings=warnings,
            image_analyses=[
                ImageAnalysis(**img) for img in processed_images
            ],
            multi_view_fusion=front_data is not None and side_data is not None,
            accuracy_rating=accuracy_rating
        )
    
    def _calculate_accuracy_rating(
        self,
        measurements: Dict[str, MeasurementValue],
        processed_images: List[Dict],
        has_multi_view: bool
    ) -> float:
        """Calculate overall accuracy rating based on various factors."""
        if not measurements:
            return 0.0
        
        avg_confidence = np.mean([m.confidence for m in measurements.values()])
        
        quality_scores = [
            img['quality']['overall_score'] 
            for img in processed_images 
            if img['used']
        ]
        avg_quality = np.mean(quality_scores) if quality_scores else 0.5
        
        multi_view_bonus = 0.15 if has_multi_view else 0
        
        num_images = len([img for img in processed_images if img['used']])
        coverage_bonus = min(0.1, num_images * 0.03)
        
        rating = (avg_confidence * 0.5 + avg_quality * 0.3 + 0.2) + multi_view_bonus + coverage_bonus
        
        return round(min(rating, 1.0), 2)
    
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
