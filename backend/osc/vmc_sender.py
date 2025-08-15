"""
VMC (Virtual Motion Capture) Protocol Sender using python-osc.

This module provides a class to send motion capture data over the network
using the VMC protocol specification.
"""

from pythonosc import udp_client
from typing import List, Tuple

class VMCSender:
    """
    A class to send data following the VMC protocol via OSC.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 39539):
        """
        Initializes the OSC client to send VMC messages.

        Args:
            host (str): The target host IP address.
            port (int): The target host port. VMC standard port is 39539.
        """
        self.client = udp_client.SimpleUDPClient(host, port)
        print(f"VMC sender initialized for {host}:{port}")

    def send_root_transform(
        self,
        pos: Tuple[float, float, float],
        rot: Tuple[float, float, float, float]
    ):
        """
        Sends the root bone's transform.
        /VMC/Ext/Root/Pos (string)"root" (float)p.x (float)p.y (float)p.z (float)q.x (float)q.y (float)q.z (float)q.w

        Args:
            pos (Tuple[float, float, float]): A tuple (x, y, z) for position.
            rot (Tuple[float, float, float, float]): A tuple (x, y, z, w) for quaternion rotation.
        """
        address = "/VMC/Ext/Root/Pos"
        args = ["root", *pos, *rot]
        self.client.send_message(address, args)

    def send_bone_transform(
        self,
        bone_name: str,
        pos: Tuple[float, float, float],
        rot: Tuple[float, float, float, float]
    ):
        """
        Sends a single bone's transform.
        /VMC/Ext/Bone/Pos (string){name} (float)p.x (float)p.y (float)p.z (float)q.x (float)q.y (float)q.z (float)q.w

        Args:
            bone_name (str): The name of the bone.
            pos (Tuple[float, float, float]): A tuple (x, y, z) for position.
            rot (Tuple[float, float, float, float]): A tuple (x, y, z, w) for quaternion rotation.
        """
        address = "/VMC/Ext/Bone/Pos"
        args = [bone_name, *pos, *rot]
        self.client.send_message(address, args)

    def send_blendshape_value(self, blend_name: str, value: float):
        """
        Sends a single blend shape value.
        /VMC/Ext/Blend/Val (string){name} (float){value}

        Args:
            blend_name (str): The name of the blend shape.
            value (float): The value of the blend shape (0.0 to 1.0).
        """
        address = "/VMC/Ext/Blend/Val"
        args = [blend_name, value]
        self.client.send_message(address, args)

    def apply_blendshapes(self):
        """
        Signals the end of blend shape value transmission for the current frame.
        /VMC/Ext/Blend/Apply
        """
        address = "/VMC/Ext/Blend/Apply"
        self.client.send_message(address, [])

    def send_bundle(self, messages: List[Tuple[str, list]]):
        """
        Sends a bundle of OSC messages. This is more efficient for sending
        multiple updates at once.
        Note: SimpleUDPClient does not support bundles directly.
              For high-performance scenarios, a more advanced client might be needed.
              For now, we send messages individually.
        """
        for address, args in messages:
            self.client.send_message(address, args)


if __name__ == '__main__':
    # Example usage and test for the VMCSender class.
    # This will not actually send data unless a VMC receiver is listening on localhost:39539.
    print("Testing VMCSender...")
    sender = VMCSender(host="127.0.0.1", port=39539)

    # 1. Send root transform
    print("Sending root transform...")
    sender.send_root_transform(pos=(0, 0, 0), rot=(0, 0, 0, 1))

    # 2. Send a bone transform (e.g., Head)
    print("Sending head bone transform...")
    sender.send_bone_transform(
        bone_name="Head",
        pos=(0, 1.5, 0),
        rot=(0, 0, 0, 1)
    )

    # 3. Send blend shape values
    print("Sending blend shape values...")
    sender.send_blendshape_value(blend_name="Blink_L", value=0.9)
    sender.send_blendshape_value(blend_name="Blink_R", value=0.85)
    sender.apply_blendshapes()

    print("VMCSender test complete.")
