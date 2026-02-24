import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('joint_state_splitter')
    default_config = os.path.join(pkg_share, 'config', 'example_config.yml')

    config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value=default_config,
        description='Path to the YAML config file for joint state splitting',
    )

    splitter_node = Node(
        package='joint_state_splitter',
        executable='splitter',
        name='joint_state_splitter',
        parameters=[{'config_file': LaunchConfiguration('config_file')}],
        output='screen',
    )

    return LaunchDescription([
        config_file_arg,
        splitter_node,
    ])
