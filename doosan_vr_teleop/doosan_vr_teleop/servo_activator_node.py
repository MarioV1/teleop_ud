#!/usr/bin/env python3
"""
servo_activator_node.py
=======================
One-shot node that calls /servo_node/start_servo after MoveIt Servo
starts up. Servo does not stream by default — this activates it.

Without this node you would need to run manually:
  ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class ServoActivatorNode(Node):

    def __init__(self):
        super().__init__('servo_activator')
        self._done = False
        # Check every 2 seconds until the service is available
        self.create_timer(2.0, self._try_activate)
        self.get_logger().info(
            'servo_activator: waiting for /servo_node/start_servo...'
        )

    def _try_activate(self):
        if self._done:
            return

        client = self.create_client(Trigger, '/servo_node/start_servo')
        if not client.service_is_ready():
            self.get_logger().info(
                'servo_activator: service not ready yet, retrying...'
            )
            return

        future = client.call_async(Trigger.Request())
        future.add_done_callback(self._on_response)

    def _on_response(self, future):
        try:
            result = future.result()
            if result.success:
                self.get_logger().info(
                    'MoveIt Servo ACTIVATED — teleoperation ready.'
                )
            else:
                self.get_logger().warn(
                    f'Servo activation returned: {result.message}'
                )
        except Exception as e:
            self.get_logger().error(f'Servo activation failed: {e}')
        self._done = True
        raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = ServoActivatorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
