import numpy as np
from typing import Dict, List, Tuple, Optional
import math


class EnhancedMeasurementEngine:
    """
    Enhanced measurement engine with multi-view fusion and improved accuracy.
    
    Uses elliptical circumference calculation when both front and side views
    are available, and applies refined anthropometric multipliers based on
    body proportion research.
    """
    
    CHEST_FRONT_MULTIPLIER = 2.95
    CHEST_DEPTH_RATIO = 0.75
    WAIST_FRONT_MULTIPLIER = 2.55
    WAIST_DEPTH_RATIO = 0.70
    HIP_FRONT_MULTIPLIER = 2.85
    HIP_DEPTH_RATIO = 0.85
    HEAD_OFFSET_RATIO = 0.085
    
    def __init__(self, height_cm: float, gender: Optional[str] = None):
        self.height_cm = height_cm
        self.gender = gender
        self._apply_gender_adjustments()
    
    def _apply_gender_adjustments(self):
        """Apply gender-specific multiplier adjustments if provided."""
        if self.gender == 'female':
            self.CHEST_FRONT_MULTIPLIER = 3.05
            self.WAIST_FRONT_MULTIPLIER = 2.45
            self.HIP_FRONT_MULTIPLIER = 3.0
        elif self.gender == 'male':
            self.CHEST_FRONT_MULTIPLIER = 2.90
            self.WAIST_FRONT_MULTIPLIER = 2.60
            self.HIP_FRONT_MULTIPLIER = 2.75
    
    def calculate_distance(self, point1: Dict, point2: Dict) -> float:
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        return np.sqrt(dx**2 + dy**2)
    
    def ellipse_circumference(self, a: float, b: float) -> float:
        """
        Calculate ellipse circumference using Ramanujan's approximation.
        a = semi-major axis, b = semi-minor axis
        """
        h = ((a - b) ** 2) / ((a + b) ** 2)
        return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
    
    def compute_scale_factor(self, landmarks: Dict) -> Tuple[Optional[float], float]:
        """Compute pixel-to-cm scale using improved head offset calculation."""
        if not landmarks or 0 not in landmarks:
            return None, 0.0
        
        nose = landmarks[0]
        left_ear = landmarks.get(7)
        right_ear = landmarks.get(8)
        left_ankle = landmarks.get(27)
        right_ankle = landmarks.get(28)
        left_heel = landmarks.get(29)
        right_heel = landmarks.get(30)
        
        if not left_ankle or not right_ankle:
            return None, 0.0
        
        if left_heel and right_heel:
            foot_y = max(
                left_ankle['y'], right_ankle['y'],
                left_heel['y'], right_heel['y']
            )
        else:
            foot_y = max(left_ankle['y'], right_ankle['y'])
        
        if left_ear and right_ear:
            top_y = min(left_ear['y'], right_ear['y'], nose['y'])
            head_visible = True
        else:
            top_y = nose['y']
            head_visible = False
        
        pixel_height_visible = abs(foot_y - top_y)
        
        if pixel_height_visible < 10:
            return None, 0.0
        
        if head_visible:
            estimated_full_pixel_height = pixel_height_visible / (1 - self.HEAD_OFFSET_RATIO * 0.5)
        else:
            estimated_full_pixel_height = pixel_height_visible / (1 - self.HEAD_OFFSET_RATIO)
        
        scale = self.height_cm / estimated_full_pixel_height
        
        confidence_values = [
            nose.get('visibility', 0),
            left_ankle.get('visibility', 0),
            right_ankle.get('visibility', 0)
        ]
        if left_ear:
            confidence_values.append(left_ear.get('visibility', 0))
        if right_ear:
            confidence_values.append(right_ear.get('visibility', 0))
        
        confidence = min(confidence_values)
        
        return scale, float(confidence)
    
    def estimate_measurements_single_view(
        self, 
        landmarks: Dict, 
        scale: float, 
        view_type: str = "front"
    ) -> Dict:
        """Estimate measurements from a single view with improved accuracy."""
        measurements = {}
        
        chest = self._estimate_chest_single(landmarks, scale, view_type)
        if chest:
            measurements['chest_cm'] = chest
        
        waist = self._estimate_waist_single(landmarks, scale, view_type)
        if waist:
            measurements['waist_cm'] = waist
        
        hips = self._estimate_hips_single(landmarks, scale, view_type)
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
        
        shoulder = self._estimate_shoulder_width(landmarks, scale)
        if shoulder:
            measurements['shoulder_cm'] = shoulder
        
        torso = self._estimate_torso_length(landmarks, scale)
        if torso:
            measurements['torso_cm'] = torso
        
        return measurements
    
    def estimate_measurements_multi_view(
        self,
        front_landmarks: Optional[Dict],
        side_landmarks: Optional[Dict],
        front_scale: float,
        side_scale: Optional[float] = None
    ) -> Dict:
        """
        Estimate measurements using both front and side views for elliptical
        circumference calculation.
        """
        measurements = {}
        
        if side_scale is None:
            side_scale = front_scale
        
        if front_landmarks and side_landmarks:
            chest = self._estimate_chest_multi_view(
                front_landmarks, side_landmarks, front_scale, side_scale
            )
            if chest:
                measurements['chest_cm'] = chest
            
            waist = self._estimate_waist_multi_view(
                front_landmarks, side_landmarks, front_scale, side_scale
            )
            if waist:
                measurements['waist_cm'] = waist
            
            hips = self._estimate_hips_multi_view(
                front_landmarks, side_landmarks, front_scale, side_scale
            )
            if hips:
                measurements['hips_cm'] = hips
        elif front_landmarks:
            measurements.update(
                self.estimate_measurements_single_view(front_landmarks, front_scale, "front")
            )
        
        if front_landmarks:
            inseam = self._estimate_inseam(front_landmarks, front_scale)
            if inseam:
                measurements['inseam_cm'] = inseam
            
            left_arm = self._estimate_arm_length(front_landmarks, front_scale, 'left')
            if left_arm:
                measurements['left_arm_cm'] = left_arm
            
            right_arm = self._estimate_arm_length(front_landmarks, front_scale, 'right')
            if right_arm:
                measurements['right_arm_cm'] = right_arm
            
            shoulder = self._estimate_shoulder_width(front_landmarks, front_scale)
            if shoulder:
                measurements['shoulder_cm'] = shoulder
            
            torso = self._estimate_torso_length(front_landmarks, front_scale)
            if torso:
                measurements['torso_cm'] = torso
        
        return measurements
    
    def _estimate_chest_single(self, landmarks: Dict, scale: float, view_type: str) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        
        if not left_shoulder or not right_shoulder:
            return None
        
        width_px = self.calculate_distance(left_shoulder, right_shoulder)
        width_cm = width_px * scale
        
        if view_type in ["front", "back"]:
            estimated_depth = width_cm * self.CHEST_DEPTH_RATIO
            circumference_cm = self.ellipse_circumference(width_cm / 2, estimated_depth / 2)
        else:
            circumference_cm = width_cm * self.CHEST_FRONT_MULTIPLIER
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'single_view_ellipse'
        }
    
    def _estimate_chest_multi_view(
        self,
        front_landmarks: Dict,
        side_landmarks: Dict,
        front_scale: float,
        side_scale: float
    ) -> Optional[Dict]:
        left_shoulder_f = front_landmarks.get(11)
        right_shoulder_f = front_landmarks.get(12)
        
        if not left_shoulder_f or not right_shoulder_f:
            return None
        
        front_width_px = self.calculate_distance(left_shoulder_f, right_shoulder_f)
        front_width_cm = front_width_px * front_scale
        
        left_shoulder_s = side_landmarks.get(11)
        right_shoulder_s = side_landmarks.get(12)
        
        if left_shoulder_s and right_shoulder_s:
            side_depth_px = abs(left_shoulder_s['x'] - right_shoulder_s['x'])
            side_depth_cm = side_depth_px * side_scale
        else:
            side_depth_cm = front_width_cm * self.CHEST_DEPTH_RATIO
        
        circumference_cm = self.ellipse_circumference(front_width_cm / 2, side_depth_cm / 2)
        
        confidence = min(
            left_shoulder_f.get('visibility', 0),
            right_shoulder_f.get('visibility', 0)
        ) * 1.1
        confidence = min(confidence, 0.99)
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'multi_view_ellipse'
        }
    
    def _estimate_waist_single(self, landmarks: Dict, scale: float, view_type: str) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        waist_ratio = 0.45
        
        waist_left_x = left_shoulder['x'] + waist_ratio * (left_hip['x'] - left_shoulder['x'])
        waist_right_x = right_shoulder['x'] + waist_ratio * (right_hip['x'] - right_shoulder['x'])
        waist_y = left_shoulder['y'] + waist_ratio * (left_hip['y'] - left_shoulder['y'])
        
        waist_left = {'x': waist_left_x, 'y': waist_y}
        waist_right = {'x': waist_right_x, 'y': waist_y}
        
        width_px = self.calculate_distance(waist_left, waist_right)
        width_cm = width_px * scale
        
        if view_type in ["front", "back"]:
            estimated_depth = width_cm * self.WAIST_DEPTH_RATIO
            circumference_cm = self.ellipse_circumference(width_cm / 2, estimated_depth / 2)
        else:
            circumference_cm = width_cm * self.WAIST_FRONT_MULTIPLIER
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0),
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'single_view_ellipse'
        }
    
    def _estimate_waist_multi_view(
        self,
        front_landmarks: Dict,
        side_landmarks: Dict,
        front_scale: float,
        side_scale: float
    ) -> Optional[Dict]:
        left_shoulder_f = front_landmarks.get(11)
        right_shoulder_f = front_landmarks.get(12)
        left_hip_f = front_landmarks.get(23)
        right_hip_f = front_landmarks.get(24)
        
        if not all([left_shoulder_f, right_shoulder_f, left_hip_f, right_hip_f]):
            return None
        
        waist_ratio = 0.45
        waist_left_x = left_shoulder_f['x'] + waist_ratio * (left_hip_f['x'] - left_shoulder_f['x'])
        waist_right_x = right_shoulder_f['x'] + waist_ratio * (right_hip_f['x'] - right_shoulder_f['x'])
        
        front_width_cm = abs(waist_right_x - waist_left_x) * front_scale
        
        left_shoulder_s = side_landmarks.get(11)
        left_hip_s = side_landmarks.get(23)
        
        if left_shoulder_s and left_hip_s:
            waist_depth_s = abs(
                left_shoulder_s['x'] + waist_ratio * (left_hip_s['x'] - left_shoulder_s['x'])
            )
            side_depth_cm = waist_depth_s * side_scale * 0.5
        else:
            side_depth_cm = front_width_cm * self.WAIST_DEPTH_RATIO
        
        circumference_cm = self.ellipse_circumference(front_width_cm / 2, side_depth_cm / 2)
        
        confidence = min(
            left_shoulder_f.get('visibility', 0),
            right_shoulder_f.get('visibility', 0),
            left_hip_f.get('visibility', 0),
            right_hip_f.get('visibility', 0)
        ) * 1.1
        confidence = min(confidence, 0.99)
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'multi_view_ellipse'
        }
    
    def _estimate_hips_single(self, landmarks: Dict, scale: float, view_type: str) -> Optional[Dict]:
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not left_hip or not right_hip:
            return None
        
        width_px = self.calculate_distance(left_hip, right_hip)
        width_cm = width_px * scale
        
        if view_type in ["front", "back"]:
            estimated_depth = width_cm * self.HIP_DEPTH_RATIO
            circumference_cm = self.ellipse_circumference(width_cm / 2, estimated_depth / 2)
        else:
            circumference_cm = width_cm * self.HIP_FRONT_MULTIPLIER
        
        confidence = min(
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0)
        )
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'single_view_ellipse'
        }
    
    def _estimate_hips_multi_view(
        self,
        front_landmarks: Dict,
        side_landmarks: Dict,
        front_scale: float,
        side_scale: float
    ) -> Optional[Dict]:
        left_hip_f = front_landmarks.get(23)
        right_hip_f = front_landmarks.get(24)
        
        if not left_hip_f or not right_hip_f:
            return None
        
        front_width_px = self.calculate_distance(left_hip_f, right_hip_f)
        front_width_cm = front_width_px * front_scale
        
        left_hip_s = side_landmarks.get(23)
        right_hip_s = side_landmarks.get(24)
        
        if left_hip_s and right_hip_s:
            side_depth_px = abs(left_hip_s['x'] - right_hip_s['x'])
            side_depth_cm = side_depth_px * side_scale
        else:
            side_depth_cm = front_width_cm * self.HIP_DEPTH_RATIO
        
        circumference_cm = self.ellipse_circumference(front_width_cm / 2, side_depth_cm / 2)
        
        confidence = min(
            left_hip_f.get('visibility', 0),
            right_hip_f.get('visibility', 0)
        ) * 1.1
        confidence = min(confidence, 0.99)
        
        return {
            'value': round(circumference_cm, 1),
            'confidence': round(confidence, 2),
            'method': 'multi_view_ellipse'
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
    
    def _estimate_shoulder_width(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        
        if not left_shoulder or not right_shoulder:
            return None
        
        width_px = self.calculate_distance(left_shoulder, right_shoulder)
        width_cm = width_px * scale
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0)
        )
        
        return {
            'value': round(width_cm, 1),
            'confidence': round(confidence, 2)
        }
    
    def _estimate_torso_length(self, landmarks: Dict, scale: float) -> Optional[Dict]:
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
            return None
        
        shoulder_y = (left_shoulder['y'] + right_shoulder['y']) / 2
        hip_y = (left_hip['y'] + right_hip['y']) / 2
        
        torso_px = abs(hip_y - shoulder_y)
        torso_cm = torso_px * scale
        
        confidence = min(
            left_shoulder.get('visibility', 0),
            right_shoulder.get('visibility', 0),
            left_hip.get('visibility', 0),
            right_hip.get('visibility', 0)
        )
        
        return {
            'value': round(torso_cm, 1),
            'confidence': round(confidence, 2)
        }
