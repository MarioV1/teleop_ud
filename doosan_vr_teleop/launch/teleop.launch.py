"""
teleop.launch.py
================
Full VR teleoperation stack for the Doosan M1509.

Launch order
------------
  t=0s   Doosan M1509 + MoveIt2  (dsr_bringup2_moveit)
  t=0s   ROS-TCP-Endpoint        (Unity WiFi bridge, port 10000)
  t=15s  MoveIt Servo node
  t=17s  servo_activator         (calls /servo_node/start_servo)
  t=18s  vr_bridge               (VR pose → TwistStamped)
  t=18s  haptic_node             (Servo status → VR haptic feedback)

Arguments
---------
  host      Robot controller IP    (default: 192.168.137.100)
  port      Robot controller port  (default: 12345)
  mode      virtual | real         (default: virtual)
  ros_ip    PC IP for Unity app    (default: 0.0.0.0)
  ros_port  TCP port               (default: 10000)
  lin_gain  Linear velocity gain   (default: 1.5)
  ang_gain  Angular velocity gain  (default: 1.2)
  vel_scale Servo velocity scale   (default: 0.25)

Usage
-----
  # Virtual (safe desktop test):
  ros2 launch doosan_vr_teleop teleop.launch.py

  # Real robot:
  ros2 launch doosan_vr_teleop teleop.launch.py \\
    mode:=real host:=192.168.137.100 \\
    ros_ip:=$(hostname -I | awk '{print $1}')
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ── Arguments ──────────────────────────────────────────────────────
    args = [
        DeclareLaunchArgument('host',      default_value='192.168.137.100'),
        DeclareLaunchArgument('port',      default_value='12345'),
        DeclareLaunchArgument('mode',      default_value='virtual'),
        DeclareLaunchArgument('ros_ip',    default_value='0.0.0.0'),
        DeclareLaunchArgument('ros_port',  default_value='10000'),
        DeclareLaunchArgument('lin_gain',  default_value='1.5'),
        DeclareLaunchArgument('ang_gain',  default_value='1.2'),
        DeclareLaunchArgument('vel_scale', default_value='0.25'),
    ]

    # ── 1. Doosan M1509 + MoveIt2 ───────────────────────────────────────
    dsr_moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('dsr_bringup2'),
                'launch', 'dsr_bringup2_moveit.launch.py',
            ])
        ]),
        launch_arguments={
            'model': 'm1509',
            'mode':  LaunchConfiguration('mode'),
            'host':  LaunchConfiguration('host'),
            'port':  LaunchConfiguration('port'),
        }.items(),
    )

    # ── 2. ROS-TCP-Endpoint (Unity WiFi bridge) ─────────────────────────
    tcp_endpoint = Node(
        package='ros_tcp_endpoint',
        executable='default_server_endpoint',
        name='tcp_endpoint',
        output='screen',
        parameters=[{
            'ROS_IP':       LaunchConfiguration('ros_ip'),
            'ROS_TCP_PORT': LaunchConfiguration('ros_port'),
        }],
    )

    # ── 3. MoveIt Servo (delayed 15s) ───────────────────────────────────
    servo_params = os.path.join(
        get_package_share_directory('doosan_vr_teleop'),
        'config', 'servo_params.yaml',
    )
    srdf_path = os.path.join(
        get_package_share_directory('dsr_moveit_config_m1509'),
        'config', 'dsr.srdf',
    )
    with open(srdf_path) as f:
        srdf = f.read()

    urdf = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]), ' ',
        PathJoinSubstitution([
            FindPackageShare('dsr_description2'), 'xacro', 'm1509.urdf.xacro',
        ]),
        ' name:=', '', ' host:=', LaunchConfiguration('host'),
        ' port:=',  LaunchConfiguration('port'),
        ' mode:=',  LaunchConfiguration('mode'),
        ' model:=', 'm1509', ' update_rate:=', '100',
    ])

    servo_node = Node(
        package='moveit_servo',
        executable='servo_node',
        name='servo_node',
        output='screen',
        parameters=[
            servo_params,
            {'robot_description': urdf},
            {'robot_description_semantic': srdf},
            {'override_velocity_scaling_factor': LaunchConfiguration('vel_scale')},
        ],
    )

    # ── 4. Servo activator (delayed 17s) ────────────────────────────────
    servo_activator = Node(
        package='doosan_vr_teleop',
        executable='servo_activator',
        name='servo_activator',
        output='screen',
    )

    # ── 5. VR bridge + haptic (delayed 18s) ─────────────────────────────
    vr_bridge = Node(
        package='doosan_vr_teleop',
        executable='vr_bridge',
        name='vr_bridge',
        output='screen',
        parameters=[{
            'linear_gain':      LaunchConfiguration('lin_gain'),
            'angular_gain':     LaunchConfiguration('ang_gain'),
            'base_frame':       'base_link',
            'publish_rate':     30.0,
            'max_linear_vel':   0.15,
            'max_angular_vel':  0.8,
            'deadband_linear':  0.002,
            'deadband_angular': 0.005,
            'vr_timeout':       0.5,
        }],
    )

    haptic = Node(
        package='doosan_vr_teleop',
        executable='haptic',
        name='haptic_node',
        output='screen',
    )

    return LaunchDescription(args + [
        dsr_moveit,
        tcp_endpoint,
        TimerAction(period=15.0, actions=[servo_node]),
        TimerAction(period=17.0, actions=[servo_activator]),
        TimerAction(period=18.0, actions=[vr_bridge, haptic]),
    ])
