import cv2
import numpy as np
from typing import Dict, Tuple, List


class ImageAnalyzer:
    """
    Analyzes image quality and provides guidance for better measurements.
    """
    
    def analyze_image_quality(self, image: np.ndarray) -> Dict:
        """
        Analyze image quality factors that affect measurement accuracy.
        """
        height, width = image.shape[:2]
        
        resolution_score = self._check_resolution(width, height)
        brightness_score, brightness_issue = self._check_brightness(image)
        contrast_score = self._check_contrast(image)
        blur_score = self._check_blur(image)
        
        overall_score = (resolution_score + brightness_score + contrast_score + blur_score) / 4
        
        issues = []
        suggestions = []
        
        if resolution_score < 0.5:
            issues.append("Low resolution image")
            suggestions.append("Use a higher resolution camera or move closer")
        
        if brightness_issue == "dark":
            issues.append("Image too dark")
            suggestions.append("Increase lighting or use flash")
        elif brightness_issue == "bright":
            issues.append("Image overexposed")
            suggestions.append("Reduce lighting or avoid direct sunlight")
        
        if contrast_score < 0.4:
            issues.append("Low contrast")
            suggestions.append("Wear clothing that contrasts with background")
        
        if blur_score < 0.4:
            issues.append("Image appears blurry")
            suggestions.append("Hold camera steady or use a tripod")
        
        return {
            'overall_score': round(overall_score, 2),
            'resolution_score': round(resolution_score, 2),
            'brightness_score': round(brightness_score, 2),
            'contrast_score': round(contrast_score, 2),
            'sharpness_score': round(blur_score, 2),
            'issues': issues,
            'suggestions': suggestions
        }
    
    def _check_resolution(self, width: int, height: int) -> float:
        min_dimension = min(width, height)
        if min_dimension >= 1080:
            return 1.0
        elif min_dimension >= 720:
            return 0.8
        elif min_dimension >= 480:
            return 0.6
        elif min_dimension >= 320:
            return 0.4
        else:
            return 0.2
    
    def _check_brightness(self, image: np.ndarray) -> Tuple[float, str]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 50:
            return 0.3, "dark"
        elif mean_brightness < 80:
            return 0.6, "slightly_dark"
        elif mean_brightness > 220:
            return 0.3, "bright"
        elif mean_brightness > 200:
            return 0.6, "slightly_bright"
        else:
            return 1.0, "good"
    
    def _check_contrast(self, image: np.ndarray) -> float:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray)
        
        if std_dev >= 60:
            return 1.0
        elif std_dev >= 40:
            return 0.7
        elif std_dev >= 25:
            return 0.5
        else:
            return 0.3
    
    def _check_blur(self, image: np.ndarray) -> float:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if laplacian_var >= 500:
            return 1.0
        elif laplacian_var >= 200:
            return 0.8
        elif laplacian_var >= 100:
            return 0.6
        elif laplacian_var >= 50:
            return 0.4
        else:
            return 0.2
    
    def detect_view_type(self, landmarks: Dict) -> str:
        """
        Detect if the image is a front, side, or back view based on landmarks.
        """
        if not landmarks:
            return "unknown"
        
        left_shoulder = landmarks.get(11)
        right_shoulder = landmarks.get(12)
        nose = landmarks.get(0)
        left_hip = landmarks.get(23)
        right_hip = landmarks.get(24)
        
        if not all([left_shoulder, right_shoulder]):
            return "unknown"
        
        shoulder_width = abs(left_shoulder['x'] - right_shoulder['x'])
        
        if left_hip and right_hip:
            hip_width = abs(left_hip['x'] - right_hip['x'])
        else:
            hip_width = shoulder_width
        
        avg_width = (shoulder_width + hip_width) / 2
        
        left_vis = left_shoulder.get('visibility', 0)
        right_vis = right_shoulder.get('visibility', 0)
        
        if nose and nose.get('visibility', 0) > 0.5:
            if abs(left_vis - right_vis) < 0.3:
                return "front"
            elif left_vis > right_vis + 0.2:
                return "left_side"
            else:
                return "right_side"
        else:
            if abs(left_vis - right_vis) < 0.3:
                return "back"
            else:
                return "side"
        
        return "front"
