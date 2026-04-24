# VRControllerInput.msg
# Published by the Unity VR app on /vr/right/inputs and /vr/left/inputs
# Carries the full state of one Meta Quest 2 controller

bool button_lower          # Lower trigger button (pause / anchor-reset)
bool button_upper          # Upper face button (A on right, X on left)
float32 trigger_index      # Index trigger pressure  (0.0 - 1.0)
float32 trigger_middle     # Middle trigger pressure (0.0 - 1.0)
float32 thumbstick_x       # Horizontal thumbstick  (-1.0 - 1.0)
float32 thumbstick_y       # Vertical thumbstick    (-1.0 - 1.0)
