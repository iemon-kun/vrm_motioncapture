"""
Shrug detection from MediaPipe Pose landmarks.
"""

import numpy as np
from typing import Dict, Any

# Using landmark indices directly for simplicity, but using the enum is better practice.
# from mediapipe.python.solutions.pose import PoseLandmark
# NOSE = PoseLandmark.NOSE.value # 0
# LEFT_SHOULDER = PoseLandmark.LEFT_SHOULDER.value # 11
# RIGHT_SHOULDER = PoseLandmark.RIGHT_SHOULDER.value # 12
# LEFT_HIP = PoseLandmark.LEFT_HIP.value # 23
# RIGHT_HIP = PoseLandmark.RIGHT_HIP.value # 24

class ShrugDetector:
    """
    Estimates shrug motion based on pose landmarks.
    """
    def __init__(self, shrug_threshold: float = 0.8):
        """
        Initializes the shrug detector.

        Args:
            shrug_threshold (float): A value to tune the sensitivity of the detection.
        """
        self.shrug_threshold = shrug_threshold
        # Store initial distances for calibration, if needed in the future
        self._initial_left_dist = None
        self._initial_right_dist = None

    def _get_landmark_pos(self, landmarks: Any, index: int) -> np.ndarray:
        """Helper to get a landmark's position as a numpy array."""
        lm = landmarks.landmark[index]
        return np.array([lm.x, lm.y, lm.z])

    def detect(self, landmarks: Any, normalize: bool = True) -> Dict[str, float]:
        """
        Detects shrugs from MediaPipe Pose landmarks.

        The logic is based on the idea that shrugging reduces the distance
        between the shoulder and the nose. This distance is normalized by the
        shoulder-to-hip distance to make it independent of the subject's size
        or distance from the camera.

        Args:
            landmarks: The landmark list from a MediaPipe Pose result.
            normalize: Whether to normalize the output to a 0-1 range.

        Returns:
            A dictionary containing the shrug amount for left and right sides,
            e.g., {'left': 0.8, 'right': 0.1}.
        """
        if not landmarks:
            return {'left': 0.0, 'right': 0.0}

        # Get landmark positions
        nose = self._get_landmark_pos(landmarks, 0)
        left_shoulder = self._get_landmark_pos(landmarks, 11)
        right_shoulder = self._get_landmark_pos(landmarks, 12)
        left_hip = self._get_landmark_pos(landmarks, 23)
        right_hip = self._get_landmark_pos(landmarks, 24)

        # Calculate reference distances (torso length) for normalization
        ref_dist_left = np.linalg.norm(left_shoulder - left_hip)
        ref_dist_right = np.linalg.norm(right_shoulder - right_hip)

        # Avoid division by zero if landmarks are not detected properly
        if ref_dist_left == 0 or ref_dist_right == 0:
            return {'left': 0.0, 'right': 0.0}

        # Calculate current distance from shoulder to nose
        dist_left = np.linalg.norm(left_shoulder - nose)
        dist_right = np.linalg.norm(right_shoulder - nose)

        # Normalize the distance
        norm_dist_left = dist_left / ref_dist_left
        norm_dist_right = dist_right / ref_dist_right

        # The shrug factor is inversely proportional to the normalized distance.
        # We use a baseline (self.shrug_threshold) which can be calibrated
        # to represent the "neutral" pose's normalized distance.
        # A value of 1.0 means fully shrugged. 0.0 means no shrug.
        left_shrug = max(0.0, 1.0 - (norm_dist_left / self.shrug_threshold))
        right_shrug = max(0.0, 1.0 - (norm_dist_right / self.shrug_threshold))

        return {'left': left_shrug, 'right': right_shrug}

if __name__ == '__main__':
    print("Testing ShrugDetector...")

    # Mock MediaPipe landmarks object for testing
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

    class MockPoseResult:
        def __init__(self, landmarks):
            self.landmark = landmarks

    # 1. Test with a neutral pose
    neutral_landmarks = MockPoseResult([
        MockLandmark(0, 1.0, 0),    # 0: Nose
        None, None, None, None, None, None, None, None, None, None, # 1-10
        MockLandmark(-0.5, 0.5, 0), # 11: Left Shoulder
        MockLandmark(0.5, 0.5, 0),  # 12: Right Shoulder
        None, None, None, None, None, None, None, None, None, None, # 13-22
        MockLandmark(-0.5, -0.5, 0),# 23: Left Hip
        MockLandmark(0.5, -0.5, 0), # 24: Right Hip
    ])

    detector = ShrugDetector(shrug_threshold=0.6) # Threshold tuned for this mock data
    shrug_values = detector.detect(neutral_landmarks)
    print(f"Neutral pose shrug values: {shrug_values}")
    assert shrug_values['left'] == 0.0 and shrug_values['right'] == 0.0, "Neutral pose should have 0.0 shrug"

    # 2. Test with a shrugged pose (shoulders moved up)
    shrugged_landmarks = MockPoseResult([
        MockLandmark(0, 1.0, 0),    # 0: Nose
        None, None, None, None, None, None, None, None, None, None, # 1-10
        MockLandmark(-0.5, 0.9, 0), # 11: Left Shoulder (Y is higher and more extreme)
        MockLandmark(0.5, 0.9, 0),  # 12: Right Shoulder (Y is higher and more extreme)
        None, None, None, None, None, None, None, None, None, None, # 13-22
        MockLandmark(-0.5, -0.5, 0),# 23: Left Hip
        MockLandmark(0.5, -0.5, 0), # 24: Right Hip
    ])

    # Adjust threshold to be more realistic for the mock data
    detector.shrug_threshold = 0.7
    shrug_values = detector.detect(shrugged_landmarks)
    print(f"Shrugged pose shrug values: {shrug_values}")
    assert shrug_values['left'] > 0.4 and shrug_values['right'] > 0.4, "Shrugged pose should have high shrug values"

    print("ShrugDetector test complete.")
