"""
Gaze stabilization using One Euro Filter and Exponential Moving Average (EMA).
"""

import numpy as np
import time
from typing import Dict, Tuple

# --- One Euro Filter Implementation ---
# Based on the public domain C++ implementation by Gery Casiez
# and the Python implementation by Nicolas Roussel.

def _smoothing_factor(t_e, cutoff):
    r = 2 * np.pi * cutoff * t_e
    return r / (r + 1)

def _exponential_smoothing(a, x, x_prev):
    return a * x + (1 - a) * x_prev

class OneEuroFilter:
    """
    A low-pass filter that adapts its cutoff frequency based on signal velocity.
    """
    def __init__(self, freq=30, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def __call__(self, x, t=None):
        if t is None:
            t = time.time()

        if self.t_prev is None:
            self.t_prev = t
            self.x_prev = x
            self.dx_prev = np.zeros_like(x)
            return x

        t_e = t - self.t_prev
        if t_e <= 0: # Handle cases with non-increasing timestamps
            return self.x_prev

        # The filtered derivative of the signal.
        a_d = _smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = _exponential_smoothing(a_d, dx, self.dx_prev)

        # The filtered signal.
        cutoff = self.min_cutoff + self.beta * np.linalg.norm(dx_hat)
        a = _smoothing_factor(t_e, cutoff)
        x_hat = _exponential_smoothing(a, x, self.x_prev)

        # Memorize the previous values.
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat

# --- Gaze Stabilizer ---

class GazeStabilizer:
    """
    Applies a cascade of filters to stabilize gaze data from face landmarks.
    """
    def __init__(self, one_euro_beta: float = 0.05, ema_alpha: float = 0.3):
        self.left_filter = OneEuroFilter(beta=one_euro_beta)
        self.right_filter = OneEuroFilter(beta=one_euro_beta)

        self.ema_alpha = ema_alpha
        self.last_left_gaze = None
        self.last_right_gaze = None

        # Indices for iris landmarks in MediaPipe FaceMesh (478 landmarks)
        self.LEFT_IRIS_INDICES = list(range(473, 478))
        self.RIGHT_IRIS_INDICES = list(range(468, 473))

    def _apply_ema(self, current_value: np.ndarray, last_value: np.ndarray) -> np.ndarray:
        if last_value is None:
            return current_value
        return self.ema_alpha * current_value + (1 - self.ema_alpha) * last_value

    def process(self, face_landmarks: any) -> Dict[str, Tuple[float, float]]:
        """
        Processes face landmarks to produce a stabilized gaze vector.

        Args:
            face_landmarks: The landmark list from a MediaPipe FaceMesh result.

        Returns:
            A dictionary with stabilized gaze vectors for left and right eyes.
        """
        if not face_landmarks:
            return {"left": (0.0, 0.0), "right": (0.0, 0.0)}

        lm_points = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks.landmark])

        left_pupil_center = np.mean(lm_points[self.LEFT_IRIS_INDICES], axis=0)
        right_pupil_center = np.mean(lm_points[self.RIGHT_IRIS_INDICES], axis=0)

        filtered_left = self.left_filter(left_pupil_center)
        filtered_right = self.right_filter(right_pupil_center)

        ema_left = self._apply_ema(filtered_left, self.last_left_gaze)
        ema_right = self._apply_ema(filtered_right, self.last_right_gaze)

        self.last_left_gaze = ema_left
        self.last_right_gaze = ema_right

        # For now, we return the filtered (x, y) coordinates as a proxy for yaw/pitch.
        # A full implementation would calculate angles relative to eye corners.
        return {
            "left": (ema_left[0], ema_left[1]),
            "right": (ema_right[0], ema_right[1])
        }

if __name__ == '__main__':
    print("Testing GazeStabilizer...")

    # Mock MediaPipe FaceMesh object for testing
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x, self.y, self.z = x, y, z

    class MockFaceResult:
        def __init__(self, num_landmarks=478):
            self.landmark = [MockLandmark(np.random.rand(), np.random.rand(), np.random.rand()) for _ in range(num_landmarks)]

    stabilizer = GazeStabilizer()
    mock_landmarks = MockFaceResult()

    print("Processing a stream of noisy data...")
    # Simulate a stream of data points
    for i in range(100):
        # Add noise to the pupil center
        noise = (np.random.rand(3) - 0.5) * 0.1
        for idx in stabilizer.LEFT_IRIS_INDICES + stabilizer.RIGHT_IRIS_INDICES:
            mock_landmarks.landmark[idx].x += noise[0]
            mock_landmarks.landmark[idx].y += noise[1]

        gaze = stabilizer.process(mock_landmarks)
        time.sleep(0.01) # Simulate time passing
        if i % 20 == 0:
            print(f"  Frame {i}: Left Gaze={gaze['left'][0]:.3f}, {gaze['left'][1]:.3f}")

    print("GazeStabilizer test complete.")
