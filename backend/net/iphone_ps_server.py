"""
Handles data received from Perfect Sync compatible applications like iFacialMocap.
"""

from typing import Dict, Optional

class PerfectSyncReceiver:
    """
    Parses and handles ARKit 52 blendshape data from a Perfect Sync source.
    This class itself is not a server, but a processor for data received
    by a server (e.g., a WebSocket endpoint).
    """

    # The 52 ARKit blendshape location names
    AR_KIT_52_BLENDSHAPES = [
        "browDown_L", "browDown_R", "browInnerUp", "browOuterUp_L", "browOuterUp_R",
        "cheekPuff", "cheekSquint_L", "cheekSquint_R", "eyeBlink_L", "eyeBlink_R",
        "eyeLookDown_L", "eyeLookDown_R", "eyeLookIn_L", "eyeLookIn_R", "eyeLookOut_L",
        "eyeLookOut_R", "eyeLookUp_L", "eyeLookUp_R", "eyeSquint_L", "eyeSquint_R",
        "eyeWide_L", "eyeWide_R", "jawForward", "jawLeft", "jawOpen", "jawRight",
        "mouthClose", "mouthDimple_L", "mouthDimple_R", "mouthFrown_L", "mouthFrown_R",
        "mouthFunnel", "mouthLeft", "mouthLowerDown_L", "mouthLowerDown_R", "mouthPress_L",
        "mouthPress_R", "mouthPucker", "mouthRight", "mouthRollLower", "mouthRollUpper",
        "mouthShrugLower", "mouthShrugUpper", "mouthSmile_L", "mouthSmile_R",
        "mouthStretch_L", "mouthStretch_R", "mouthUpperUp_L", "mouthUpperUp_R",
        "noseSneer_L", "noseSneer_R"
    ]

    def __init__(self):
        self.latest_blendshapes: Dict[str, float] = {name: 0.0 for name in self.AR_KIT_52_BLENDSHAPES}

    def parse_ifacialmocap_data(self, data: bytes) -> Optional[Dict[str, float]]:
        """
        Parses the data format sent by iFacialMocap.
        The format is typically a byte string containing key-value pairs,
        separated by '&' or '|'. E.g., "mouthSmile_L=0.5&jawOpen=0.2"

        Args:
            data (bytes): The raw byte data received from the socket.

        Returns:
            A dictionary of blendshape names to their float values, or None if parsing fails.
        """
        try:
            decoded_data = data.decode("utf-8")

            # Standardize separators by replacing '|' with '&'
            standardized_data = decoded_data.replace('|', '&')

            parsed_values = {}
            pairs = standardized_data.split('&')
            for pair in pairs:
                if '=' not in pair:
                    continue
                key, value_str = pair.split('=', 1)
                # The key might have a suffix like "_L" or "_R", which is what we want.
                # Sometimes apps send extra data we don't need, so we filter by our list.
                if key in self.AR_KIT_52_BLENDSHAPES:
                    parsed_values[key] = float(value_str)

            return parsed_values
        except (UnicodeDecodeError, ValueError) as e:
            print(f"Error parsing iFacialMocap data: {e}")
            return None

    def process_data(self, data: bytes):
        """
        Parses the data and updates the latest blendshape values.

        Args:
            data (bytes): The raw byte data from the socket.
        """
        parsed_data = self.parse_ifacialmocap_data(data)
        if parsed_data:
            self.latest_blendshapes.update(parsed_data)
            # In a real application, this would likely put the data into a thread-safe queue
            # to be consumed by the main motion processing loop.
            # For now, we just update the internal state.

    def get_latest_blendshapes(self) -> Dict[str, float]:
        """
        Returns the most recently received blendshape values.
        """
        return self.latest_blendshapes.copy()

if __name__ == '__main__':
    print("Testing PerfectSyncReceiver...")
    receiver = PerfectSyncReceiver()

    # 1. Test with valid data
    test_data = b"mouthSmile_L=0.88|jawOpen=0.42&eyeBlink_R=1.0"
    receiver.process_data(test_data)
    blendshapes = receiver.get_latest_blendshapes()

    print(f"Parsed values: mouthSmile_L={blendshapes['mouthSmile_L']}, jawOpen={blendshapes['jawOpen']}, eyeBlink_R={blendshapes['eyeBlink_R']}")
    assert blendshapes['mouthSmile_L'] == 0.88
    assert blendshapes['jawOpen'] == 0.42
    assert blendshapes['eyeBlink_R'] == 1.0
    # Check that others are still 0.0
    assert blendshapes['browInnerUp'] == 0.0

    # 2. Test with invalid data
    test_data_invalid = b"thisisnotvaliddata"
    receiver.process_data(test_data_invalid)
    # Should not raise an error, just print a message.

    print("PerfectSyncReceiver test complete.")
