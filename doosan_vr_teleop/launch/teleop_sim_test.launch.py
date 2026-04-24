"""
teleop_sim_test.launch.py
=========================
Desktop pipeline test — no robot, no headset required.
Runs sim_input + vr_bridge and lets you verify the full
VR → Servo command chain in one terminal.

Usage:
  ros2 launch doosan_vr_teleop teleop_sim_test.launch.py
  ros2 launch doosan_vr_teleop teleop_sim_test.launch.py mode:=rotate_z

In another terminal:
  ros2 topic echo /servo_node/delta_twist_cmds
  ros2 topic echo /teleop/status
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        DeclareLaunchArgument(
            'mode', default_value='translate_x',
            description=(
                'idle | translate_x | translate_y | translate_z | '
                'rotate_z | rotate_y | button_lower'
            )
        ),
        DeclareLaunchArgument('lin_gain', default_value='1.5'),
        DeclareLaunchArgument('ang_gain', default_value='1.2'),

        # Publishes /vr/right/pose and /vr/right/inputs
        Node(
            package='doosan_vr_teleop',
            executable='sim_input',
            name='sim_input',
            output='screen',
            parameters=[{
                'mode': LaunchConfiguration('mode'),
                'rate': 30.0,
            }],
        ),

        # Converts PoseStamped → TwistStamped, publishes /teleop/status
        Node(
            package='doosan_vr_teleop',
            executable='vr_bridge',
            name='vr_bridge',
            output='screen',
            parameters=[{
                'linear_gain':  LaunchConfiguration('lin_gain'),
                'angular_gain': LaunchConfiguration('ang_gain'),
                'base_frame':   'base_link',
                'publish_rate': 30.0,
            }],
        ),
    ])
