cmake_minimum_required(VERSION 3.0.2)
project(vc_battleship)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  moveit_ros_planning_interface
  tf
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/board_cell_mapper.py
  scripts/attack_motion_executor.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
