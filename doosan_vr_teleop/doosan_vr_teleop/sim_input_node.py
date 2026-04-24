#!/usr/bin/env python3
"""
sim_input_node.py
=================
Desktop simulator — publishes fake VR controller data on the correct
doosan_vr_teleop topic names so you can test the full ROS2 pipeline
without wearing the headset or running the Unity app.

Usage
-----
  ros2 run doosan_vr_teleop sim_input --ros-args -p mode:=translate_x
  ros2 run doosan_vr_teleop sim_input --ros-args -p mode:=rotate_z
  ros2 run doosan_vr_teleop sim_input --ros-args -p mode:=idle
  ros2 run doosan_vr_teleop sim_input --ros-args -p mode:=button_lower

Modes: idle | translate_x | translate_y | translate_z | rotate_z | rotate_y | button_lower
"""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from doosan_teleop_msgs.msg import VRControllerInput


_MODES = {
    'idle':        (0.00, 0.00, 0.00, 0.0,  0.0,  0.00),
    'translate_x': (0.01, 0.00, 0.00, 0.0,  0.0,  0.00),
    'translate_y': (0.00, 0.01, 0.00, 0.0,  0.0,  0.00),
    'translate_z': (0.00, 0.00, 0.01, 0.0,  0.0,  0.00),
    'rotate_z':    (0.00, 0.00, 0.00, 0.0,  0.0,  0.05),
    'rotate_y':    (0.00, 0.00, 0.00, 0.0,  0.05, 0.00),
    'button_lower':(0.00, 0.00, 0.00, 0.0,  0.0,  0.00),
}


class SimInputNode(Node):

    def __init__(self):
        super().__init__('sim_input')
        self.declare_parameter('mode', 'idle')
        self.declare_parameter('rate', 30.0)

        mode = self.get_parameter('mode').value
        rate = self.get_parameter('rate').value
        self._press_lower = (mode == 'button_lower')

        if mode not in _MODES:
            self.get_logger().warn(
                f"Unknown mode '{mode}', using 'idle'. "
                f"Valid: {list(_MODES.keys())}"
            )
            mode = 'idle'

        tx, ty, tz, rx, ry, rz = _MODES[mode]
        self._tx, self._ty, self._tz = tx, ty, tz
        self._rx, self._ry, self._rz = rx, ry, rz

        # Publish on the new custom topic names
        self._pose_pub  = self.create_publisher(PoseStamped,      '/vr/right/pose',   10)
        self._input_pub = self.create_publisher(VRControllerInput, '/vr/right/inputs', 10)

        self.create_timer(1.0 / rate, self._timer_cb)
        self.get_logger().info(
            f'sim_input: mode={mode} at {rate:.0f} Hz\n'
            f'  pub /vr/right/pose  /vr/right/inputs'
        )

    def _timer_cb(self):
        now = self.get_clock().now().to_msg()

        # PoseStamped
        pose = PoseStamped()
        pose.header.stamp    = now
        pose.header.frame_id = 'world'
        pose.pose.position.x = self._tx
        pose.pose.position.y = self._ty
        pose.pose.position.z = self._tz

        angle = math.sqrt(self._rx**2 + self._ry**2 + self._rz**2)
        if angle > 1e-6:
            s = math.sin(angle / 2.0) / angle
            pose.pose.orientation.x = self._rx * s
            pose.pose.orientation.y = self._ry * s
            pose.pose.orientation.z = self._rz * s
            pose.pose.orientation.w = math.cos(angle / 2.0)
        else:
            pose.pose.orientation.w = 1.0

        self._pose_pub.publish(pose)

        # VRControllerInput
        inp = VRControllerInput()
        inp.button_lower   = self._press_lower
        inp.button_upper   = False
        inp.trigger_index  = 0.0
        inp.trigger_middle = 0.0
        inp.thumbstick_x   = 0.0
        inp.thumbstick_y   = 0.0
        self._input_pub.publish(inp)


def main(args=None):
    rclpy.init(args=args)
    node = SimInputNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
