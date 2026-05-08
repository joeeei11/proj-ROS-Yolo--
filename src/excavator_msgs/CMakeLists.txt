cmake_minimum_required(VERSION 3.0.2)
project(excavator_msgs)

find_package(catkin REQUIRED COMPONENTS
  std_msgs
  geometry_msgs
  sensor_msgs
  message_generation
)

add_message_files(FILES
  ObstacleInfo.msg
  ObstacleArray.msg
  RiskState.msg
  SystemState.msg
)

add_service_files(FILES
  SetMode.srv
  SpawnObstacle.srv
)

generate_messages(
  DEPENDENCIES std_msgs geometry_msgs
)

catkin_package(
  CATKIN_DEPENDS message_runtime std_msgs geometry_msgs
)
