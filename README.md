# 🤖 Doosan VR Teleop

Meta Quest 2 VR teleoperation for the **Doosan M1509** robot arm using
**ROS2 Humble**, and **Unity 6**.

---

## 📡 Topic reference

| Topic | Type | Direction | Description |
|-------|------|-----------|-------------|
| `/vr/right/pose` | `geometry_msgs/PoseStamped` | Unity → ROS | Right controller delta pose |
| `/vr/right/inputs` | `doosan_teleop_msgs/VRControllerInput` | Unity → ROS | Buttons, triggers, thumbstick |
| `/vr/right/haptic` | `doosan_teleop_msgs/VRHapticFeedback` | ROS → Unity | Controller vibration command |
| `/teleop/status` | `doosan_teleop_msgs/TeleopStatus` | ROS → Unity | System health status |
| `/joint_states` | `sensor_msgs/JointState` | ROS → Unity | Robot joint positions |
| `/servo_node/delta_twist_cmds` | `geometry_msgs/TwistStamped` | Bridge → Servo | Cartesian velocity command |
| `/dsr_moveit_controller/joint_trajectory` | `trajectory_msgs/JointTrajectory` | Servo → JTC | Joint commands |

---

## 📦 Dependencies

### ROS2 packages
- ROS2 Humble
- MoveIt2
- `moveit_servo`
- `ros_tcp_endpoint` — [Unity Technologies](https://github.com/Unity-Technologies/ROS-TCP-Endpoint)
- `doosan-robot2` — Doosan robot description, controllers, MoveIt config

### Unity (Windows PC — build only)
- Unity 6 with Android Build Support
- ROS-TCP-Connector
- URDF Importer
- XR Interaction Toolkit
- Meta OpenXR plugin

---

## ⚙️ Installation

### 1. Install system dependencies
```bash
sudo apt-get install -y \
    ros-humble-moveit-servo \
    ros-humble-moveit-ros-move-group \
    ros-humble-moveit-configs-utils
```

### 2. Install ROS-TCP-Endpoint
```bash
cd ~/ros2_ws/src
git clone -b main-ros2 https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git ros_tcp_endpoint
cd ~/ros2_ws && colcon build --packages-select ros_tcp_endpoint
```

### 3. Clone this repository
```bash
cd ~/ros2_ws/src
git clone https://github.com/MarioV1/teleop_ud.git
cd doosan-vr-teleop
```

### 4. Build
```bash
cd ~/ros2_ws
colcon build --packages-select doosan_teleop_msgs
colcon build --packages-select doosan_vr_teleop
source install/setup.bash
```

### 5. Verify
```bash
ros2 pkg list | grep doosan
ros2 interface show doosan_teleop_msgs/msg/VRControllerInput
```

---

## 🚀 Usage

### Pipeline test — no robot, no headset
```bash
# Terminal 1
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0

# Terminal 2
ros2 launch doosan_vr_teleop teleop_sim_test.launch.py

# Terminal 3 — verify output
ros2 topic echo /servo_node/delta_twist_cmds
ros2 topic echo /teleop/status
```

### Real robot
```bash
# Step 1 — home the robot first
ros2 launch dsr_bringup2 dsr_bringup2_rviz.launch.py \
  mode:=real host:=192.168.137.100 model:=m1509
ros2 service call /motion/move_home dsr_msgs2/srv/MoveHome {}
# Ctrl-C after homing

# Step 2 — launch teleop
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0
ros2 launch doosan_vr_teleop teleop.launch.py \
  mode:=real \
  host:=192.168.137.100 \
  ros_ip:=$(hostname -I | awk '{print $1}')
```

### 🎛️ Launch arguments
| Argument | Default | Description |
|----------|---------|-------------|
| `mode` | `virtual` | `virtual` or `real` |
| `host` | `192.168.137.100` | Robot controller IP |
| `ros_ip` | `0.0.0.0` | Ubuntu PC WiFi IP |
| `lin_gain` | `1.5` | Controller linear gain |
| `ang_gain` | `1.2` | Controller angular gain |
| `vel_scale` | `0.25` | MoveIt Servo velocity scale (0–1) |

---

## 🕹️ Controller buttons

| Button | Action |
|--------|--------|
| Lower trigger (first press) | Pause + anchor reset |
| Lower trigger (second press) | Resume |

---

## ⚡ Speed tuning

Three parameters control robot speed:

```bash
# Conservative start
ros2 launch doosan_vr_teleop teleop.launch.py vel_scale:=0.1 lin_gain:=1.0

# Default
ros2 launch doosan_vr_teleop teleop.launch.py vel_scale:=0.25 lin_gain:=1.5

# Practical working speed
ros2 launch doosan_vr_teleop teleop.launch.py vel_scale:=0.5 lin_gain:=1.5
```

---

## 🔧 Hardware

- **Robot:** Doosan M1509, 6-DOF, payload 5 kg, reach 900 mm
- **Headset:** Meta Quest 2
- **PC:** Ubuntu 22.04, ROS2 Humble
- **Controller firmware:** v2.12+ required for MoveIt2 compatibility

---

## 📄 License

Apache 2.0