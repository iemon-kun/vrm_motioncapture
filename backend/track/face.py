"""
Face mesh tracking using MediaPipe FaceMesh.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional

class FaceMeshTracker:
    """
    A class to detect and track face landmarks in an image.
    """

    def __init__(self, static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initializes the MediaPipe FaceMesh model.
        """
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=refine_landmarks, # Required for iris tracking
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process(self, image_bgr: np.ndarray) -> Optional[any]:
        """
        Processes a BGR image to find face landmarks.

        Args:
            image_bgr (np.ndarray): The input image in BGR format.

        Returns:
            The first detected face's landmarks result, or None if not found.
        """
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.face_mesh.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.multi_face_landmarks:
            return results.multi_face_landmarks[0] # Return first face
        return None

    def close(self):
        """
        Releases the MediaPipe FaceMesh resources.
        """
        self.face_mesh.close()

if __name__ == '__main__':
    print("Testing FaceMeshTracker...")
    tracker = FaceMeshTracker()
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    print("Processing a dummy image...")

    face_landmarks = tracker.process(dummy_image)

    if face_landmarks:
        print(f"Detected face with {len(face_landmarks.landmark)} landmarks.")
    else:
        print("No face detected in the dummy image.")

    tracker.close()
    print("FaceMeshTracker test complete.")
