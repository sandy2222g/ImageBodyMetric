import numpy as np
from typing import Dict, List, Tuple, Optional
import cv2


class MeasurementEngine:
    def __init__(self, height_cm: float):
        self.height_cm = height_cm
        self.scale_factor = None
        
    def calculate_distance(self, point1: Dict, point2: Dict) -> float:
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        return np.sqrt(dx**2 + dy**2)
    
    def compute_scale_factor(self, landmarks: Dict) -> Tuple[Optional[float], float]:
        if not landmarks or 0 not in landmarks:
            return None, 0.0
        
        nose = landmarks[0]
        left_ankle = landmarks.get(27)
        right_ankle = landmarks.get(28)
        
        if not left_ankle or not right_ankle:
            return None, 0.0
        
        ankle_y = (left_ankle['y'] + right_ankle['y']) / 2
        pixel_height = abs(ankle_y - nose['y'])
        
        if pixel_height < 10:
            return None, 0.0
        
        scale = self.height_cm / pixel_height
        
        confidence = min(
            nose.get('visibility', 0),
            left_ankle.get('visibility', 0),
            right_ankle.get('visibility', 0)
        )
        
        return scale, float(confidence)
    
    def estimate_measurements(self, landmarks: Dict, scale: float, image: np.ndarray) -> Dict:
        measurements = {}
        
        chest = self._estimate_chest(landmarks, scale)
        if chest:
            measurements['chest_cm'] = chest
        
        waist = self._estimate_waist(landmarks, scale)
        if waist:
            measurements['waist_cm'] = waist
        
        hips = self._estimate_hips(landmarks, scale)
        if hips:
            measurements['hips_cm'] = hips
        
        inseam = self._estimate_inseam(landmarks, scale)
        if inseam:
            measurements['inseam_cm'] = inseam
        
        left_arm = self._estimate_arm_length(landmarks, scale, 'left')
        if left_arm:
            measurements['left_arm_cm'] = left_arm
        
        right_arm = self._estimate_arm_length(landmarks, scale, 'right')
        if right_arm:
            measurements['right_arm_cm'] = right_arm
        
        return measurements
    
    def _estimate_chest(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        
        if not left_shoulder or not right_shoulder:
            return None
        
        width_px = self.calculate_distance(left_shoulder, right_shoulder)
        width_cm = width_px * scale
        
        circumference_cm = width_cm * 3.2
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2)
        }
    
    def _estimate_waist(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        waist_left_x = left_shoulder['x']
        waist_right_x = right_shoulder['x']
        waist_y = (left_shoulder['y'] + left_hip['y']) / 2
        
        waist_left = {'x': waist_left_x, 'y': waist_y}
        waist_right = {'x': waist_right_x, 'y': waist_y}
        
        width_px = self.calculate_distance(waist_left, waist_right)
        width_cm = width_px * scale
        
        circumference_cm = width_cm * 2.8
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0),
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2)
        }
    
    def _estimate_hips(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not left_hip or not right_hip:
            return None
        
        width_px = self.calculate_distance(left_hip, right_hip)
        width_cm = width_px * scale
        
        circumference_cm = width_cm * 3.3
        
        confidence = min(
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2)
        }
    
    def _estimate_inseam(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        left_ankle = landmarks.get(27)
        right_ankle = landmarks.get(28)
        
        if not all([left_hip, right_hip, left_ankle, right_ankle]):
            return None
        
        hip_center_y = (left_hip['y'] + right_hip['y']) / 2
        ankle_center_y = (left_ankle['y'] + right_ankle['y']) / 2
        
        inseam_px = abs(ankle_center_y - hip_center_y)
        inseam_cm = inseam_px * scale
        
        confidence = min(
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0),
            left_ankle.get('visibility', 0),
            right_ankle.get('visibility', 0)
        )
        
        return {
            'value': round(inseam_cm, 1),
            'confidence': round(confidence, 2)
        }
    
    def _estimate_arm_length(self, landmarks: Dict, scale: float, side: str) -> Optional[Dict]:
        if side == 'left':
            shoulder = landmarks.get(11)
            elbow = landmarks.get(13)
            wrist = landmarks.get(15)
        else:
            shoulder = landmarks.get(12)
            elbow = landmarks.get(14)
            wrist = landmarks.get(16)
        
        if not all([shoulder, elbow, wrist]):
            return None
        
        upper_arm_px = self.calculate_distance(shoulder, elbow)
        forearm_px = self.calculate_distance(elbow, wrist)
        
        arm_length_px = upper_arm_px + forearm_px
        arm_length_cm = arm_length_px * scale
        
        confidence = min(
            shoulder.get('visibility', 0),
            elbow.get('visibility', 0),
            wrist.get('visibility', 0)
        )
        
        return {
            'value': round(arm_length_cm, 1),
            'confidence': round(confidence, 2)
        }
