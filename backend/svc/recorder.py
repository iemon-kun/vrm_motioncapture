"""
Handles recording of motion data to a file.
"""

import json
import time
import os
from typing import Dict, Any, IO, Optional

class Recorder:
    """
    Manages the recording of motion data frames to a file.
    """
    def __init__(self, filepath: str, fmt: str = "jsonl"):
        if fmt not in ["jsonl"]:
            raise ValueError("Unsupported format. Currently only 'jsonl' is supported.")

        self.filepath = filepath
        self.format = fmt
        self.is_recording = False
        self._file_handle: Optional[IO[Any]] = None

    def start(self):
        """Opens the file and starts the recording session."""
        if self.is_recording:
            print("Warning: Already recording.")
            return

        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self._file_handle = open(self.filepath, 'w', encoding='utf-8')
            self.is_recording = True
            print(f"Recording started, writing to {self.filepath}")
        except IOError as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False

    def stop(self):
        """Closes the file and stops the recording session."""
        if not self.is_recording:
            return

        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

        self.is_recording = False
        print(f"Recording stopped for {self.filepath}")

    def record_frame(self, motion_data: Dict[str, Any]):
        """
        Writes a single frame of motion data to the file.

        Args:
            motion_data (Dict[str, Any]): A dictionary containing the motion
                                          data for the current frame.
        """
        if not self.is_recording or not self._file_handle:
            return

        record = {
            "timestamp": time.time(),
            "motion_data": motion_data
        }

        if self.format == "jsonl":
            try:
                self._file_handle.write(json.dumps(record) + '\n')
            except TypeError as e:
                print(f"Error serializing motion data to JSON: {e}")
            except IOError as e:
                print(f"Error writing to file: {e}")
                self.stop()

    def __del__(self):
        # Ensure file is closed if the object is destroyed unexpectedly.
        if self.is_recording:
            self.stop()

if __name__ == '__main__':
    print("Testing Recorder...")
    output_dir = "test_recordings"
    output_file = os.path.join(output_dir, "test.jsonl")

    # 1. Create and start a recorder
    recorder = Recorder(filepath=output_file)
    recorder.start()
    assert recorder.is_recording
    assert os.path.exists(output_dir)

    # 2. Record some dummy frames
    mock_motion_data = {
        "blendshapes": {"mouthSmile_L": 0.8},
        "bones": {"Head": [0, 0, 0, 1]} # simplified
    }
    recorder.record_frame(mock_motion_data)
    time.sleep(0.01)
    recorder.record_frame(mock_motion_data)

    # 3. Stop the recorder
    recorder.stop()
    assert not recorder.is_recording

    # 4. Verify the file content
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
        first_record = json.loads(lines[0])
        assert "timestamp" in first_record
        assert first_record["motion_data"]["blendshapes"]["mouthSmile_L"] == 0.8
    print("File content verified.")

    # Clean up the test file and dir
    os.remove(output_file)
    os.rmdir(output_dir)
    print("Recorder test complete.")
