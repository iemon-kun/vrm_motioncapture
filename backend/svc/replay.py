"""
Handles replaying of recorded motion data.
"""

import json
import time
from typing import List, Dict, Any, Optional

class Replayer:
    """
    Manages the playback of a recorded motion data file.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.frames: List[Dict[str, Any]] = []
        self.is_replaying = False
        self._start_time: float = 0.0
        self._frame_index: int = 0
        self._initial_timestamp: float = 0.0

    def load(self) -> bool:
        """
        Loads all frames from the recording file into memory.
        Returns True on success, False on failure.
        """
        self.frames = []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    self.frames.append(json.loads(line))

            if self.frames:
                self._initial_timestamp = self.frames[0]["timestamp"]

            print(f"Loaded {len(self.frames)} frames from {self.filepath}")
            return True
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading replay file: {e}")
            return False

    def start(self):
        """Starts the replay session."""
        if not self.frames:
            print("Warning: No frames loaded. Cannot start replay.")
            return

        self.is_replaying = True
        self._start_time = time.time()
        self._frame_index = 0
        print("Replay started.")

    def stop(self):
        """Stops the replay session."""
        self.is_replaying = False
        print("Replay stopped.")

    def get_current_frame(self) -> Optional[Dict[str, Any]]:
        """
        Returns the motion data for the current frame if it's time to play it.
        Returns None otherwise.
        """
        if not self.is_replaying:
            return None

        if self._frame_index >= len(self.frames):
            print("Replay finished.")
            self.stop()
            return None

        elapsed_time = time.time() - self._start_time
        current_frame_info = self.frames[self._frame_index]
        target_elapsed_time = current_frame_info["timestamp"] - self._initial_timestamp

        if elapsed_time >= target_elapsed_time:
            frame_data = current_frame_info["motion_data"]
            self._frame_index += 1
            return frame_data

        return None

if __name__ == '__main__':
    import os
    from backend.svc.recorder import Recorder

    print("Testing Replayer...")
    output_dir = "test_recordings"
    output_file = os.path.join(output_dir, "replay_test.jsonl")

    # 1. Use Recorder to create a test file
    print("--- Creating test recording ---")
    recorder = Recorder(filepath=output_file)
    recorder.start()
    mock_data_1 = {"frame": 1}
    mock_data_2 = {"frame": 2}
    recorder.record_frame(mock_data_1)
    time.sleep(0.1) # Simulate time between frames
    recorder.record_frame(mock_data_2)
    recorder.stop()
    print("--- Test recording created ---")

    # 2. Test the Replayer
    replayer = Replayer(filepath=output_file)
    assert replayer.load()
    assert len(replayer.frames) == 2

    replayer.start()
    assert replayer.is_replaying

    # Frame 1 should be available immediately
    frame1 = replayer.get_current_frame()
    print(f"Got frame: {frame1}")
    assert frame1 is not None and frame1["frame"] == 1

    # Frame 2 should not be available yet
    frame2_early = replayer.get_current_frame()
    assert frame2_early is None

    # Wait until it's time for frame 2
    print("Waiting for next frame...")
    time.sleep(0.11) # Sleep a little extra to avoid timing flakiness
    frame2_late = replayer.get_current_frame()
    print(f"Got frame: {frame2_late}")
    assert frame2_late is not None and frame2_late["frame"] == 2

    # No more frames
    assert replayer.get_current_frame() is None
    assert not replayer.is_replaying # Should stop automatically

    # Clean up
    os.remove(output_file)
    os.rmdir(output_dir)
    print("Replayer test complete.")
