import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Tuple, Optional


class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def detect_landmarks(self, image: np.ndarray) -> Tuple[Optional[Dict], float]:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)
        
        if not results.pose_landmarks:
            return None, 0.0
        
        height, width = image.shape[:2]
        landmarks = {}
        confidences = []
        
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            landmarks[idx] = {
                'x': landmark.x * width,
                'y': landmark.y * height,
                'z': landmark.z,
                'visibility': landmark.visibility
            }
            confidences.append(landmark.visibility)
        
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return landmarks, float(avg_confidence)
    
    def get_keypoint_names(self) -> Dict[int, str]:
        return {
            0: 'nose',
            11: 'left_shoulder',
            12: 'right_shoulder',
            23: 'left_hip',
            24: 'right_hip',
            13: 'left_elbow',
            14: 'right_elbow',
            15: 'left_wrist',
            16: 'right_wrist',
            25: 'left_knee',
            26: 'right_knee',
            27: 'left_ankle',
            28: 'right_ankle',
            7: 'left_ear',
            8: 'right_ear'
        }
    
    def __del__(self):
        self.pose.close()
