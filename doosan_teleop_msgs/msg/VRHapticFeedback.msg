# VRHapticFeedback.msg
# Subscribed by the Unity VR app on /vr/right/haptic and /vr/left/haptic
# Commands controller vibration

float32 frequency    # Vibration frequency in Hz
float32 amplitude    # Vibration amplitude  (0.0 - 1.0)
float32 duration     # Duration in seconds  (0.0 = single pulse)
