import sys

import yaml
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
from sensor_msgs.msg import JointState


class JointStateSplitter(Node):
    def __init__(self, config_path: str):
        super().__init__('joint_state_splitter')

        config = self._load_config(config_path)

        subscribe_topic = config['subscribe_topic']
        publish_topics = config['publish_topics']

        # Build a mapping: joint_name -> list of (publisher, index_in_that_topic)
        # and per-publisher joint name lists for building outgoing messages.
        self._pub_infos: list[dict] = []
        for entry in publish_topics:
            topic_name = entry['topic_name']
            joint_names = list(entry['joint_names'])
            pub = self.create_publisher(JointState, topic_name, 10)
            self._pub_infos.append({
                'publisher': pub,
                'joint_names': joint_names,
            })
            self.get_logger().info(
                f"Will publish to '{topic_name}' with joints: {joint_names}"
            )

        # Subscribe with a SensorDataQoS-compatible profile (best effort, volatile)
        # so it works with typical robot publishers. Also keep default reliable
        # profile as fallback — we subscribe with SYSTEM_DEFAULT to let DDS negotiate.
        self._subscription = self.create_subscription(
            JointState,
            subscribe_topic,
            self._on_joint_state,
            10,
        )
        self.get_logger().info(
            f"Subscribed to '{subscribe_topic}'"
        )

    # ------------------------------------------------------------------
    def _load_config(self, path: str) -> dict:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        # Validate minimal structure
        if 'subscribe_topic' not in config:
            raise ValueError("Config must contain 'subscribe_topic'")
        if 'publish_topics' not in config or not config['publish_topics']:
            raise ValueError("Config must contain a non-empty 'publish_topics' list")
        for i, entry in enumerate(config['publish_topics']):
            if 'topic_name' not in entry:
                raise ValueError(f"publish_topics[{i}] must contain 'topic_name'")
            if 'joint_names' not in entry or not entry['joint_names']:
                raise ValueError(
                    f"publish_topics[{i}] must contain a non-empty 'joint_names' list"
                )
        return config

    # ------------------------------------------------------------------
    def _on_joint_state(self, msg: JointState):
        # Build an index once per incoming message for fast lookups
        name_to_idx: dict[str, int] = {
            name: idx for idx, name in enumerate(msg.name)
        }

        for info in self._pub_infos:
            out_msg = JointState()
            out_msg.header = msg.header  # preserve stamp & frame_id

            indices = []
            names = []
            for jn in info['joint_names']:
                if jn in name_to_idx:
                    indices.append(name_to_idx[jn])
                    names.append(jn)
                else:
                    self.get_logger().warn(
                        f"Joint '{jn}' not found in incoming JointState, skipping",
                        throttle_duration_sec=5.0,
                    )

            out_msg.name = names

            if msg.position:
                out_msg.position = [msg.position[i] for i in indices]
            if msg.velocity:
                out_msg.velocity = [msg.velocity[i] for i in indices]
            if msg.effort:
                out_msg.effort = [msg.effort[i] for i in indices]

            info['publisher'].publish(out_msg)


def main(args=None):
    rclpy.init(args=args)

    # The config file path is passed as a ROS parameter or CLI argument.
    # Usage: ros2 run isaac_joint_state_splitter joint_state_splitter --ros-args -p config_file:=/path/to/config.yml
    #    or: ros2 run isaac_joint_state_splitter joint_state_splitter /path/to/config.yml

    node_tmp = Node('_joint_state_splitter_bootstrap')
    node_tmp.declare_parameter('config_file', '')
    config_file = node_tmp.get_parameter('config_file').get_parameter_value().string_value
    node_tmp.destroy_node()

    if not config_file:
        # Fallback: look at sys.argv for a plain positional argument
        non_ros_args = rclpy.utilities.remove_ros_args(sys.argv)
        if len(non_ros_args) >= 2:
            config_file = non_ros_args[1]
        else:
            print(
                "Usage:\n"
                "  ros2 run isaac_joint_state_splitter joint_state_splitter "
                "--ros-args -p config_file:=/path/to/config.yml\n"
                "  or\n"
                "  ros2 run isaac_joint_state_splitter joint_state_splitter "
                "/path/to/config.yml",
                file=sys.stderr,
            )
            sys.exit(1)

    node = JointStateSplitter(config_file)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
