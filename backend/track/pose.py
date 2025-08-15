"""
Pose tracking using MediaPipe Pose.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional

class PoseTracker:
    """
    A class to detect and track human pose landmarks in an image.
    """

    def __init__(self, static_image_mode=False, model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initializes the MediaPipe Pose model.
        """
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process(self, image_bgr: np.ndarray) -> Optional[any]:
        """
        Processes a BGR image to find pose landmarks.

        Args:
            image_bgr (np.ndarray): The input image in BGR format.

        Returns:
            The pose landmarks result from MediaPipe, or None if not found.
        """
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.pose.process(image_rgb)
        image_rgb.flags.writeable = True

        return results.pose_landmarks

    def close(self):
        """
        Releases the MediaPipe Pose resources.
        """
        self.pose.close()

if __name__ == '__main__':
    print("Testing PoseTracker...")
    tracker = PoseTracker()
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    print("Processing a dummy image...")

    pose_landmarks = tracker.process(dummy_image)

    if pose_landmarks:
        print(f"Detected pose with {len(pose_landmarks.landmark)} landmarks.")
    else:
        print("No pose detected in the dummy image.")

    tracker.close()
    print("PoseTracker test complete.")
