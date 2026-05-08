cmake_minimum_required(VERSION 3.0.2)
project(excavator_planner)

add_compile_options(-std=c++17)

find_package(catkin REQUIRED COMPONENTS
  excavator_msgs
  geometry_msgs
  nav_msgs
  roscpp
  std_msgs
)

catkin_package(
  INCLUDE_DIRS include
  CATKIN_DEPENDS excavator_msgs geometry_msgs nav_msgs roscpp std_msgs
)

include_directories(
  include
  ${catkin_INCLUDE_DIRS}
)

add_executable(rrt_star_planner
  src/rrt_star_planner.cpp
)

add_dependencies(rrt_star_planner
  ${${PROJECT_NAME}_EXPORTED_TARGETS}
  ${catkin_EXPORTED_TARGETS}
)

target_link_libraries(rrt_star_planner
  ${catkin_LIBRARIES}
)
