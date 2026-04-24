from setuptools import setup
import os
from glob import glob

package_name = 'doosan_vr_teleop'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('doosan_vr_teleop/config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='VR teleoperation stack for Doosan M1509 via Meta Quest 2 and Unity',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'vr_bridge       = doosan_vr_teleop.vr_bridge_node:main',
            'haptic          = doosan_vr_teleop.haptic_node:main',
            'servo_activator = doosan_vr_teleop.servo_activator_node:main',
            'sim_input       = doosan_vr_teleop.sim_input_node:main',
        ],
    },
)
