"""
The main processing pipeline that orchestrates all tracking and feature extraction.
"""
import time
from typing import Dict, Any

# Import all the components we've built
from backend.track.pose import PoseTracker
from backend.track.hands import HandTracker, calculate_finger_rotations
from backend.track.face import FaceMeshTracker
from backend.features.shrug import ShrugDetector
from backend.features.gaze import GazeStabilizer
from backend.osc.vmc_sender import VMCSender
from backend.svc.recorder import Recorder
from backend.svc.replay import Replayer
import cv2
import numpy as np
from backend.ps_receiver import ps_receiver_instance

# PerfectSyncReceiver is handled by the WebSocket endpoint, but the pipeline might need to access its data.

class ProcessingPipeline:
    """
    A class to manage the entire motion capture and sending pipeline.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes all components of the pipeline based on a configuration dictionary.
        """
        print("Initializing processing pipeline...")
        self.config = config

        # Trackers
        self.pose_tracker = PoseTracker()
        self.hand_tracker = HandTracker()
        self.face_tracker = FaceMeshTracker()

        # Feature Extractors
        self.shrug_detector = ShrugDetector()
        self.gaze_stabilizer = GazeStabilizer()

        # I/O and Senders
        self.vmc_sender = VMCSender(host=config.get("host", "127.0.0.1"), port=config.get("port", 39539))
        self.ps_receiver = ps_receiver_instance

        self.recorder: Recorder = None
        self.replayer: Replayer = None

        self.is_running = False
        self.is_paused = False
        self.in_replay_mode = False

        print("Processing pipeline initialized.")

    def run(self):
        """
        The main processing loop. Delegates to live or replay loops.
        """
        self.is_running = True
        print("Pipeline starting...")

        if self.in_replay_mode:
            self._run_replay()
        else:
            self._run_live()

        print("Pipeline run finished.")

    def _send_motion_data(self, motion_data: Dict[str, Any]):
        """Helper function to send motion data via VMC."""
        if not motion_data:
            return

        # Send root transform (static for now)
        self.vmc_sender.send_root_transform(pos=(0, 0, 0), rot=(0, 0, 0, 1))

        # Send bone transforms
        if "bones" in motion_data:
            for bone_name, rot_quat in motion_data["bones"].items():
                self.vmc_sender.send_bone_transform(
                    bone_name=bone_name, pos=(0.0, 0.0, 0.0), rot=tuple(rot_quat)
                )

        # Send blendshape values
        if "blendshapes" in motion_data:
            for blend_name, value in motion_data["blendshapes"].items():
                self.vmc_sender.send_blendshape_value(blend_name, float(value))
            self.vmc_sender.apply_blendshapes()

    def _run_replay(self):
        """Loop for replaying from a file."""
        if not self.replayer:
            print("Error: Replay mode is on but no replayer is initialized.")
            return

        self.replayer.start()
        while self.is_running and self.replayer.is_replaying:
            frame_start_time = time.time()

            motion_data = self.replayer.get_current_frame()
            if motion_data:
                self._send_motion_data(motion_data)

            # Frame rate is determined by the replay file's timestamps
            elapsed = time.time() - frame_start_time
            # Sleep for a short duration to prevent a busy-wait loop
            time.sleep(max(0, 0.001 - elapsed))

        self.stop_replay()

    def _run_live(self):
        """Loop for live tracking from a camera."""
        cap = cv2.VideoCapture(self.config.get("camera_index", 0))
        if not cap.isOpened():
            print(f"Error: Cannot open camera at index {self.config.get('camera_index', 0)}.")
            self.is_running = False
            return

        while self.is_running:
            frame_start_time = time.time()

            success, image = cap.read()
            if not success:
                continue

            pose_landmarks, hand_landmarks_list, handedness_list, face_landmarks = None, None, None, None
            features = self.config.get("features", {})

            # --- Tracking ---
            if features.get("pose", True):
                pose_landmarks = self.pose_tracker.process(image)
            if features.get("hands", True):
                hand_landmarks_list, handedness_list = self.hand_tracker.process(image)
            if features.get("face", True):
                face_landmarks = self.face_tracker.process(image)

            motion_data = {"blendshapes": {}, "bones": {}}

            # --- Feature Extraction ---
            if pose_landmarks and features.get("shrug", True):
                shrug = self.shrug_detector.detect(pose_landmarks)
                motion_data["blendshapes"]["shrug_left"] = shrug.get('left', 0.0)
                motion_data["blendshapes"]["shrug_right"] = shrug.get('right', 0.0)

            if face_landmarks and features.get("gaze", True):
                gaze = self.gaze_stabilizer.process(face_landmarks)
                motion_data["blendshapes"]["gaze_left_x"] = gaze.get('left', (0.0, 0.0))[0]
                motion_data["blendshapes"]["gaze_left_y"] = gaze.get('left', (0.0, 0.0))[1]

            if hand_landmarks_list and handedness_list: # This implicitly checks features["hands"]
                for i, hand_lm in enumerate(hand_landmarks_list):
                    side = handedness_list[i].classification[0].label
                    rots = calculate_finger_rotations(hand_lm)
                    for bone, rot in rots.items():
                        motion_data["bones"][f"{side}{bone}"] = rot.tolist()

            ps_data = self.ps_receiver.get_latest_blendshapes()
            motion_data["blendshapes"].update(ps_data)

            if self.recorder and self.recorder.is_recording:
                self.recorder.record_frame(motion_data)

            self._send_motion_data(motion_data)

            elapsed = time.time() - frame_start_time
            sleep_time = (1.0 / self.config.get("fps", 30)) - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        cap.release()
        self.pose_tracker.close()
        self.hand_tracker.close()
        self.face_tracker.close()
        print("Live tracking stopped and resources released.")


    def stop(self):
        """Stops the processing loop."""
        self.is_running = False
        print("Pipeline stopping...")

    # --- Control Methods for Recorder and Replayer ---

    def start_recording(self, filepath: str, fmt: str = "jsonl"):
        """Stops any current recording and starts a new one."""
        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()
        self.recorder = Recorder(filepath=filepath, fmt=fmt)
        self.recorder.start()

    def stop_recording(self):
        """Stops the current recording."""
        if self.recorder:
            self.recorder.stop()
            self.recorder = None

    def start_replay(self, filepath: str):
        """Starts replaying from a given file."""
        if self.in_replay_mode:
            self.stop_replay()

        self.replayer = Replayer(filepath=filepath)
        if self.replayer.load():
            self.in_replay_mode = True
            # The main loop will pick this up. If it's already running,
            # it might need a restart or a more complex state transition.
            # For now, we assume the mode is set before run() is called.
            print("Replay mode enabled. The pipeline will now play from file.")
        else:
            self.replayer = None
            print("Failed to load replay file.")

    def stop_replay(self):
        """Stops the current replay."""
        if self.replayer:
            self.replayer.stop()
        self.in_replay_mode = False
        self.replayer = None
        print("Replay mode disabled.")

    def update_config(self, new_config: Dict[str, Any]):
        """
        Updates the pipeline's configuration.
        Note: Some changes may require a pipeline restart to take effect.
        """
        self.config.update(new_config)
        # Re-initialize components that depend on the config, if possible
        self.vmc_sender = VMCSender(host=self.config.get("host"), port=self.config.get("port"))
        print(f"Pipeline config updated. New VMC target: {self.config.get('host')}:{self.config.get('port')}")


if __name__ == '__main__':
    print("Testing ProcessingPipeline initialization...")
    test_config = {
        "host": "localhost",
        "port": 12345,
        "camera_index": 0, # Assume a camera exists for a full test
        "fps": 30,
    }
    pipeline = ProcessingPipeline(config=test_config)
    assert pipeline.vmc_sender is not None
    assert pipeline.pose_tracker is not None
    assert pipeline.ps_receiver is not None

    print("Initialization test complete.")
    # To run the full pipeline, you would need a camera connected.
    # For example:
    # import threading
    # p_thread = threading.Thread(target=pipeline.run)
    # p_thread.start()
    # time.sleep(10)
    # pipeline.stop()
    # p_thread.join()
