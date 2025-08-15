"""
Hand tracking using MediaPipe Hands.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List

# Define a type hint for MediaPipe's NormalizedLandmarkList
LandmarkList = type(mp.solutions.hands.Hands().process(np.zeros((1,1,3), dtype=np.uint8)).multi_hand_landmarks)

class HandTracker:
    """
    A class to detect and track hand landmarks in an image.
    """

    def __init__(self, static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initializes the MediaPipe Hands model.

        Args:
            static_image_mode (bool): Whether to treat the input images as a batch of static
                                      and unrelated images, or a video stream.
            max_num_hands (int): Maximum number of hands to detect.
            min_detection_confidence (float): Minimum confidence value ([0.0, 1.0]) for hand
                                             detection to be considered successful.
            min_tracking_confidence (float): Minimum confidence value ([0.0, 1.0]) for the
                                              hand landmarks to be considered tracked successfully.
        """
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands

    def process(self, image_bgr: np.ndarray) -> Optional[tuple]:
        """
        Processes a BGR image to find hand landmarks and handedness.

        Args:
            image_bgr (np.ndarray): The input image in BGR format.

        Returns:
            A tuple containing (multi_hand_landmarks, multi_handedness),
            or (None, None) if no hands are found.
        """
        # Convert the BGR image to RGB, flip the image horizontally for a later selfie-view
        # display, and process it with MediaPipe Hands.
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image_rgb.flags.writeable = False
        results = self.hands.process(image_rgb)
        image_rgb.flags.writeable = True

        if not results.multi_hand_landmarks:
            return None, None

        return results.multi_hand_landmarks, results.multi_handedness

    def close(self):
        """
        Releases the MediaPipe Hands resources.
        """
        self.hands.close()


if __name__ == '__main__':
    # Example usage:
    print("Initializing HandTracker...")
    tracker = HandTracker()

    # Create a dummy black image for testing purposes
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    print("Processing a dummy image...")

    hand_landmarks, handedness = tracker.process(dummy_image)

    if hand_landmarks:
        print(f"Detected {len(hand_landmarks)} hands.")
        for i, hand in enumerate(hand_landmarks):
            side = handedness[i].classification[0].label
            print(f"  Hand {i} ({side}) has {len(hand.landmark)} landmarks.")
    else:
        print("No hands detected in the dummy image.")

    tracker.close()
    print("HandTracker test complete.")


# --- VRM Bone Mapping and Rotation Calculation ---

from scipy.spatial.transform import Rotation as R
from mediapipe.python.solutions.hands import HandLandmark

# This maps VRM humanoid bone names to the MediaPipe landmark indices that define the bone's vector.
# The vector is calculated from the first landmark index to the second.
VRM_HAND_BONE_MAP = {
    'ThumbProximal': (HandLandmark.THUMB_CMC, HandLandmark.THUMB_MCP),
    'ThumbIntermediate': (HandLandmark.THUMB_MCP, HandLandmark.THUMB_IP),
    'ThumbDistal': (HandLandmark.THUMB_IP, HandLandmark.THUMB_TIP),
    'IndexProximal': (HandLandmark.INDEX_FINGER_MCP, HandLandmark.INDEX_FINGER_PIP),
    'IndexIntermediate': (HandLandmark.INDEX_FINGER_PIP, HandLandmark.INDEX_FINGER_DIP),
    'IndexDistal': (HandLandmark.INDEX_FINGER_DIP, HandLandmark.INDEX_FINGER_TIP),
    'MiddleProximal': (HandLandmark.MIDDLE_FINGER_MCP, HandLandmark.MIDDLE_FINGER_PIP),
    'MiddleIntermediate': (HandLandmark.MIDDLE_FINGER_PIP, HandLandmark.MIDDLE_FINGER_DIP),
    'MiddleDistal': (HandLandmark.MIDDLE_FINGER_DIP, HandLandmark.MIDDLE_FINGER_TIP),
    'RingProximal': (HandLandmark.RING_FINGER_MCP, HandLandmark.RING_FINGER_PIP),
    'RingIntermediate': (HandLandmark.RING_FINGER_PIP, HandLandmark.RING_FINGER_DIP),
    'RingDistal': (HandLandmark.RING_FINGER_DIP, HandLandmark.RING_FINGER_TIP),
    'LittleProximal': (HandLandmark.PINKY_MCP, HandLandmark.PINKY_PIP),
    'LittleIntermediate': (HandLandmark.PINKY_PIP, HandLandmark.PINKY_DIP),
    'LittleDistal': (HandLandmark.PINKY_DIP, HandLandmark.PINKY_TIP),
}

def get_handedness(multi_handedness, index) -> Optional[str]:
    """Extracts handedness ('left' or 'right') from MediaPipe results."""
    if not multi_handedness:
        return None
    for handedness_classification in multi_handedness:
        if handedness_classification.classification[0].index == index:
            return handedness_classification.classification[0].label.lower()
    return None


def calculate_finger_rotations(landmarks: LandmarkList) -> dict:
    """
    Calculates the rotation for each finger bone based on hand landmarks.

    Args:
        landmarks: A list of landmarks for a single hand from MediaPipe.

    Returns:
        A dictionary mapping VRM bone names to their calculated quaternion rotation (x, y, z, w).
        Note: This is a simplified implementation and assumes a reference pose.
              A full implementation would require the VRM's T-pose data.
    """
    rotations = {}
    lm_points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])

    for bone_name, (start_idx, end_idx) in VRM_HAND_BONE_MAP.items():
        p1 = lm_points[start_idx]
        p2 = lm_points[end_idx]

        bone_vec = p2 - p1

        # This is a highly simplified rotation logic.
        # It calculates rotation against a default "straight" pose (Y-axis up).
        # A robust solution needs to consider parent bone rotation and T-pose.
        ref_vec = np.array([0, 1, 0])

        # Normalize vectors before comparison
        bone_vec_norm = bone_vec / np.linalg.norm(bone_vec)

        try:
            # align_vectors returns a rotation that maps the first set of vectors to the second
            rotation, _ = R.align_vectors([ref_vec], [bone_vec_norm])
            # Storing as (x, y, z, w) quaternion
            rotations[bone_name] = rotation.as_quat()
        except Exception:
            # In case of issues (e.g., zero-length vector), use no rotation
            rotations[bone_name] = np.array([0, 0, 0, 1])

    return rotations
