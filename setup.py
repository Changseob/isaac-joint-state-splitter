from setuptools import setup

package_name = 'joint_state_splitter'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', ['config/example_config.yml']),
        ('share/' + package_name + '/launch', ['launch/joint_state_splitter.launch.py']),
    ],
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='todo',
    maintainer_email='todo@todo.com',
    description='Splits a JointState message into multiple topics based on joint names',
    license='MIT',
    entry_points={
        'console_scripts': [
            'splitter = joint_state_splitter.joint_state_splitter:main',
        ],
    },
)
