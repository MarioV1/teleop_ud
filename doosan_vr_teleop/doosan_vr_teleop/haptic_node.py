#!/usr/bin/env python3
"""
haptic_node.py
==============
Monitors MoveIt Servo status and publishes haptic feedback commands
to the Unity VR app via /vr/right/haptic.

Topic interface
---------------
  Subscriptions:
    /servo_node/status      std_msgs/Int8         MoveIt Servo status
    /teleop/status          doosan_teleop_msgs/TeleopStatus

  Publications:
    /vr/right/haptic        doosan_teleop_msgs/VRHapticFeedback

Haptic patterns
---------------
  Status 2 (near singularity)   → slow warning pulse  80 Hz / 0.4 amp
  Status 3 (singularity halt)   → hard alert pulse    120 Hz / 0.9 amp
  Status 4 (near collision)     → medium pulse         60 Hz / 0.6 amp
  Status 5 (collision halt)     → hard alert pulse    120 Hz / 0.9 amp
  Status 6 (joint bound)        → soft pulse           40 Hz / 0.5 amp
  Status 1 (cleared/OK)         → gentle confirmation  20 Hz / 0.2 amp
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Int8
from doosan_teleop_msgs.msg import VRHapticFeedback, TeleopStatus


# Haptic pattern: (frequency_hz, amplitude_0_1, duration_s)
HAPTIC_PATTERNS = {
    1: (20.0,  0.2, 0.05),   # OK / cleared
    2: (80.0,  0.4, 0.15),   # near singularity
    3: (120.0, 0.9, 0.3),    # singularity halt
    4: (60.0,  0.6, 0.2),    # near collision
    5: (120.0, 0.9, 0.3),    # collision halt
    6: (40.0,  0.5, 0.15),   # joint bound
}


class HapticNode(Node):

    def __init__(self):
        super().__init__('haptic_node')

        self._prev_status = 1  # start at NO_WARNING

        best_effort = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Subscriptions
        self.create_subscription(
            Int8,
            '/servo_node/status',
            self._servo_status_cb,
            best_effort,
        )

        # Publisher
        self._haptic_pub = self.create_publisher(
            VRHapticFeedback,
            '/vr/right/haptic',
            10,
        )

        self.get_logger().info(
            'haptic_node ready\n'
            '  sub  /servo_node/status\n'
            '  pub  /vr/right/haptic'
        )

    def _servo_status_cb(self, msg: Int8):
        status = int(msg.data)
        if status == self._prev_status:
            return

        status_names = {
            0: 'INVALID', 1: 'OK', 2: 'NEAR_SINGULARITY',
            3: 'SINGULARITY_HALT', 4: 'NEAR_COLLISION',
            5: 'COLLISION_HALT', 6: 'JOINT_BOUND',
        }
        self.get_logger().info(
            f'Servo status: {status_names.get(status, f"UNKNOWN({status})")}'
        )

        if status in HAPTIC_PATTERNS:
            freq, amp, dur = HAPTIC_PATTERNS[status]
            self._send_haptic(freq, amp, dur)

        self._prev_status = status

    def _send_haptic(self, frequency: float, amplitude: float, duration: float):
        msg = VRHapticFeedback()
        msg.frequency = float(frequency)
        msg.amplitude = float(amplitude)
        msg.duration  = float(duration)
        self._haptic_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = HapticNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
