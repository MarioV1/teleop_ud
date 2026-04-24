# TeleopStatus.msg
# Published by doosan_vr_teleop on /teleop/status
# Gives the Unity app a single topic to monitor the full system state

std_msgs/Header header

bool vr_connected          # Unity app is publishing controller data
bool teleop_active         # Bridge is streaming commands to Servo
bool servo_ready           # MoveIt Servo has been activated
uint8 servo_status         # Raw MoveIt Servo status code (0-6)

# Servo status codes:
#   0 = INVALID
#   1 = NO_WARNING
#   2 = DECELERATE_SINGULARITY
#   3 = HALT_SINGULARITY
#   4 = DECELERATE_COLLISION
#   5 = HALT_COLLISION
#   6 = JOINT_BOUND

string status_message      # Human-readable status string
