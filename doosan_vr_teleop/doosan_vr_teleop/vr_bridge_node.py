#!/usr/bin/env python3
"""
vr_bridge_node.py
=================
Core teleoperation bridge for the Doosan M1509.

Converts incoming VR controller pose (geometry_msgs/PoseStamped published by
the Unity Meta Quest 2 app) into a MoveIt Servo TwistStamped command.

Topic interface
---------------
  Subscriptions:
    /vr/right/pose     geometry_msgs/PoseStamped    delta pose from Unity
    /vr/right/inputs   doosan_teleop_msgs/VRControllerInput  buttons

  Publications:
    /servo_node/delta_twist_cmds  geometry_msgs/TwistStamped  to MoveIt Servo
    /teleop/status                doosan_teleop_msgs/TeleopStatus

Parameters
----------
  linear_gain      (float, default 1.5)    scale translation delta → m/s
  angular_gain     (float, default 1.2)    scale rotation delta    → rad/s
  publish_rate     (float, default 30.0)   Hz
  base_frame       (str,   default 'base_link')
  max_linear_vel   (float, default 0.15)   m/s hard clamp
  max_angular_vel  (float, default 0.8)    rad/s hard clamp
  deadband_linear  (float, default 0.002)  m  — ignore below this
  deadband_angular (float, default 0.005)  rad — ignore below this
  vr_timeout       (float, default 0.5)    s  — mark disconnected after this
"""

import math
import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import PoseStamped, TwistStamped
from std_msgs.msg import Header

from doosan_teleop_msgs.msg import VRControllerInput, TeleopStatus


def _quat_to_rotvec(qx, qy, qz, qw):
    """Quaternion → axis-angle rotation vector (rad)."""
    qw = max(-1.0, min(1.0, qw))
    angle = 2.0 * math.acos(abs(qw))
    s = math.sqrt(max(0.0, 1.0 - qw * qw))
    if s < 1e-6:
        return 0.0, 0.0, 0.0
    if qw < 0.0:
        qx, qy, qz = -qx, -qy, -qz
    return qx / s * angle, qy / s * angle, qz / s * angle


class VRBridgeNode(Node):

    def __init__(self):
        super().__init__('vr_bridge')

        # ── Parameters ────────────────────────────────────────────────
        self.declare_parameter('linear_gain',      1.5)
        self.declare_parameter('angular_gain',     1.2)
        self.declare_parameter('publish_rate',     30.0)
        self.declare_parameter('base_frame',       'base_link')
        self.declare_parameter('max_linear_vel',   0.15)
        self.declare_parameter('max_angular_vel',  0.8)
        self.declare_parameter('deadband_linear',  0.002)
        self.declare_parameter('deadband_angular', 0.005)
        self.declare_parameter('vr_timeout',       0.5)

        self._lin_gain    = self.get_parameter('linear_gain').value
        self._ang_gain    = self.get_parameter('angular_gain').value
        self._base_frame  = self.get_parameter('base_frame').value
        self._max_lin     = self.get_parameter('max_linear_vel').value
        self._max_ang     = self.get_parameter('max_angular_vel').value
        self._db_lin      = self.get_parameter('deadband_linear').value
        self._db_ang      = self.get_parameter('deadband_angular').value
        self._vr_timeout  = self.get_parameter('vr_timeout').value

        # ── State ─────────────────────────────────────────────────────
        self._paused           = False
        self._last_pose        = None
        self._last_pose_time   = 0.0
        self._prev_lower_btn   = False
        self._servo_status     = 1  # NO_WARNING

        # ── QoS ───────────────────────────────────────────────────────
        best_effort = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ── Subscriptions ─────────────────────────────────────────────
        self.create_subscription(
            PoseStamped,
            '/vr/right/pose',
            self._pose_cb,
            best_effort,
        )
        self.create_subscription(
            VRControllerInput,
            '/vr/right/inputs',
            self._inputs_cb,
            best_effort,
        )

        # ── Publishers ────────────────────────────────────────────────
        self._twist_pub = self.create_publisher(
            TwistStamped,
            '/servo_node/delta_twist_cmds',
            10,
        )
        self._status_pub = self.create_publisher(
            TeleopStatus,
            '/teleop/status',
            10,
        )

        # ── Timer ─────────────────────────────────────────────────────
        rate = self.get_parameter('publish_rate').value
        self.create_timer(1.0 / rate, self._timer_cb)

        self.get_logger().info(
            f'vr_bridge ready\n'
            f'  sub  /vr/right/pose  /vr/right/inputs\n'
            f'  pub  /servo_node/delta_twist_cmds  /teleop/status\n'
            f'  frame={self._base_frame}  '
            f'lin_gain={self._lin_gain}  ang_gain={self._ang_gain}'
        )

    # ── Callbacks ──────────────────────────────────────────────────────

    def _pose_cb(self, msg: PoseStamped):
        self._last_pose      = msg
        self._last_pose_time = time.time()

    def _inputs_cb(self, msg: VRControllerInput):
        lower = bool(msg.button_lower)
        # Rising edge → toggle pause / anchor-reset
        if lower and not self._prev_lower_btn:
            self._paused = not self._paused
            if self._paused:
                self._publish_zero()
                self.get_logger().info('Teleop PAUSED — anchor reset')
            else:
                self.get_logger().info('Teleop RESUMED')
        self._prev_lower_btn = lower

    def _timer_cb(self):
        vr_connected = (time.time() - self._last_pose_time) < self._vr_timeout
        active       = vr_connected and not self._paused

        # Publish motion only when active
        if active and self._last_pose is not None:
            self._publish_twist(self._last_pose)

        # Always publish status
        self._publish_status(vr_connected, active)

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _clamp(v, limit):
        return max(-limit, min(limit, v))

    @staticmethod
    def _deadband(v, thr):
        return 0.0 if abs(v) < thr else v

    def _publish_twist(self, pose: PoseStamped):
        p = pose.pose.position
        q = pose.pose.orientation

        lx = self._clamp(self._deadband(p.x * self._lin_gain, self._db_lin), self._max_lin)
        ly = self._clamp(self._deadband(p.y * self._lin_gain, self._db_lin), self._max_lin)
        lz = self._clamp(self._deadband(p.z * self._lin_gain, self._db_lin), self._max_lin)

        rx, ry, rz = _quat_to_rotvec(q.x, q.y, q.z, q.w)
        ax = self._clamp(self._deadband(rx * self._ang_gain, self._db_ang), self._max_ang)
        ay = self._clamp(self._deadband(ry * self._ang_gain, self._db_ang), self._max_ang)
        az = self._clamp(self._deadband(rz * self._ang_gain, self._db_ang), self._max_ang)

        msg = TwistStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._base_frame
        msg.twist.linear.x  = lx
        msg.twist.linear.y  = ly
        msg.twist.linear.z  = lz
        msg.twist.angular.x = ax
        msg.twist.angular.y = ay
        msg.twist.angular.z = az
        self._twist_pub.publish(msg)

    def _publish_zero(self):
        msg = TwistStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._base_frame
        self._twist_pub.publish(msg)

    def _publish_status(self, vr_connected: bool, active: bool):
        status_names = {
            0: 'INVALID', 1: 'OK', 2: 'NEAR_SINGULARITY',
            3: 'SINGULARITY_HALT', 4: 'NEAR_COLLISION',
            5: 'COLLISION_HALT', 6: 'JOINT_BOUND',
        }
        msg = TeleopStatus()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = self._base_frame
        msg.vr_connected    = vr_connected
        msg.teleop_active   = active
        msg.servo_ready     = True
        msg.servo_status    = self._servo_status
        msg.status_message  = (
            f'VR={"ON" if vr_connected else "OFF"} '
            f'TELEOP={"ACTIVE" if active else ("PAUSED" if self._paused else "WAITING")} '
            f'SERVO={status_names.get(self._servo_status, "?")}'
        )
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = VRBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
