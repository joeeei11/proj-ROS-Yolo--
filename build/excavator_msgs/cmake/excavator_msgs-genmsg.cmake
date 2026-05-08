# generated from genmsg/cmake/pkg-genmsg.cmake.em

message(STATUS "excavator_msgs: 4 messages, 2 services")

set(MSG_I_FLAGS "-Iexcavator_msgs:/home/excavator/excavator_ws/src/excavator_msgs/msg;-Istd_msgs:/opt/ros/noetic/share/std_msgs/cmake/../msg;-Igeometry_msgs:/opt/ros/noetic/share/geometry_msgs/cmake/../msg")

# Find all generators
find_package(gencpp REQUIRED)
find_package(geneus REQUIRED)
find_package(genlisp REQUIRED)
find_package(gennodejs REQUIRED)
find_package(genpy REQUIRED)

add_custom_target(excavator_msgs_generate_messages ALL)

# verify that message/service dependencies have not changed since configure



get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" "geometry_msgs/PoseStamped:geometry_msgs/Quaternion:geometry_msgs/Vector3:std_msgs/Header:geometry_msgs/Pose:geometry_msgs/Point"
)

get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" "geometry_msgs/PoseStamped:geometry_msgs/Quaternion:excavator_msgs/ObstacleInfo:geometry_msgs/Vector3:std_msgs/Header:geometry_msgs/Pose:geometry_msgs/Point"
)

get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" "std_msgs/Header"
)

get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" "std_msgs/Header"
)

get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" ""
)

get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_custom_target(_excavator_msgs_generate_messages_check_deps_${_filename}
  COMMAND ${CATKIN_ENV} ${PYTHON_EXECUTABLE} ${GENMSG_CHECK_DEPS_SCRIPT} "excavator_msgs" "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" "geometry_msgs/Pose:geometry_msgs/Point:geometry_msgs/Quaternion"
)

#
#  langs = gencpp;geneus;genlisp;gennodejs;genpy
#

### Section generating for lang: gencpp
### Generating Messages
_generate_msg_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)

### Generating Services
_generate_srv_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)
_generate_srv_cpp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
)

### Generating Module File
_generate_module_cpp(excavator_msgs
  ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
  "${ALL_GEN_OUTPUT_FILES_cpp}"
)

add_custom_target(excavator_msgs_generate_messages_cpp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_cpp}
)
add_dependencies(excavator_msgs_generate_messages excavator_msgs_generate_messages_cpp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_cpp _excavator_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(excavator_msgs_gencpp)
add_dependencies(excavator_msgs_gencpp excavator_msgs_generate_messages_cpp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS excavator_msgs_generate_messages_cpp)

### Section generating for lang: geneus
### Generating Messages
_generate_msg_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)
_generate_msg_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)
_generate_msg_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)
_generate_msg_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)

### Generating Services
_generate_srv_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)
_generate_srv_eus(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
)

### Generating Module File
_generate_module_eus(excavator_msgs
  ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
  "${ALL_GEN_OUTPUT_FILES_eus}"
)

add_custom_target(excavator_msgs_generate_messages_eus
  DEPENDS ${ALL_GEN_OUTPUT_FILES_eus}
)
add_dependencies(excavator_msgs_generate_messages excavator_msgs_generate_messages_eus)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_eus _excavator_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(excavator_msgs_geneus)
add_dependencies(excavator_msgs_geneus excavator_msgs_generate_messages_eus)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS excavator_msgs_generate_messages_eus)

### Section generating for lang: genlisp
### Generating Messages
_generate_msg_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)
_generate_msg_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)

### Generating Services
_generate_srv_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)
_generate_srv_lisp(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
)

### Generating Module File
_generate_module_lisp(excavator_msgs
  ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
  "${ALL_GEN_OUTPUT_FILES_lisp}"
)

add_custom_target(excavator_msgs_generate_messages_lisp
  DEPENDS ${ALL_GEN_OUTPUT_FILES_lisp}
)
add_dependencies(excavator_msgs_generate_messages excavator_msgs_generate_messages_lisp)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_lisp _excavator_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(excavator_msgs_genlisp)
add_dependencies(excavator_msgs_genlisp excavator_msgs_generate_messages_lisp)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS excavator_msgs_generate_messages_lisp)

### Section generating for lang: gennodejs
### Generating Messages
_generate_msg_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)
_generate_msg_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)
_generate_msg_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)
_generate_msg_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)

### Generating Services
_generate_srv_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)
_generate_srv_nodejs(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
)

### Generating Module File
_generate_module_nodejs(excavator_msgs
  ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
  "${ALL_GEN_OUTPUT_FILES_nodejs}"
)

add_custom_target(excavator_msgs_generate_messages_nodejs
  DEPENDS ${ALL_GEN_OUTPUT_FILES_nodejs}
)
add_dependencies(excavator_msgs_generate_messages excavator_msgs_generate_messages_nodejs)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_nodejs _excavator_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(excavator_msgs_gennodejs)
add_dependencies(excavator_msgs_gennodejs excavator_msgs_generate_messages_nodejs)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS excavator_msgs_generate_messages_nodejs)

### Section generating for lang: genpy
### Generating Messages
_generate_msg_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)
_generate_msg_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/PoseStamped.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg;/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Vector3.msg;/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)
_generate_msg_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)
_generate_msg_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/std_msgs/cmake/../msg/Header.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)

### Generating Services
_generate_srv_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv"
  "${MSG_I_FLAGS}"
  ""
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)
_generate_srv_py(excavator_msgs
  "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv"
  "${MSG_I_FLAGS}"
  "/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Pose.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Point.msg;/opt/ros/noetic/share/geometry_msgs/cmake/../msg/Quaternion.msg"
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
)

### Generating Module File
_generate_module_py(excavator_msgs
  ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
  "${ALL_GEN_OUTPUT_FILES_py}"
)

add_custom_target(excavator_msgs_generate_messages_py
  DEPENDS ${ALL_GEN_OUTPUT_FILES_py}
)
add_dependencies(excavator_msgs_generate_messages excavator_msgs_generate_messages_py)

# add dependencies to all check dependencies targets
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleInfo.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/ObstacleArray.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/RiskState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/msg/SystemState.msg" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SetMode.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})
get_filename_component(_filename "/home/excavator/excavator_ws/src/excavator_msgs/srv/SpawnObstacle.srv" NAME_WE)
add_dependencies(excavator_msgs_generate_messages_py _excavator_msgs_generate_messages_check_deps_${_filename})

# target for backward compatibility
add_custom_target(excavator_msgs_genpy)
add_dependencies(excavator_msgs_genpy excavator_msgs_generate_messages_py)

# register target for catkin_package(EXPORTED_TARGETS)
list(APPEND ${PROJECT_NAME}_EXPORTED_TARGETS excavator_msgs_generate_messages_py)



if(gencpp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gencpp_INSTALL_DIR}/excavator_msgs
    DESTINATION ${gencpp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_cpp)
  add_dependencies(excavator_msgs_generate_messages_cpp std_msgs_generate_messages_cpp)
endif()
if(TARGET geometry_msgs_generate_messages_cpp)
  add_dependencies(excavator_msgs_generate_messages_cpp geometry_msgs_generate_messages_cpp)
endif()

if(geneus_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${geneus_INSTALL_DIR}/excavator_msgs
    DESTINATION ${geneus_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_eus)
  add_dependencies(excavator_msgs_generate_messages_eus std_msgs_generate_messages_eus)
endif()
if(TARGET geometry_msgs_generate_messages_eus)
  add_dependencies(excavator_msgs_generate_messages_eus geometry_msgs_generate_messages_eus)
endif()

if(genlisp_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genlisp_INSTALL_DIR}/excavator_msgs
    DESTINATION ${genlisp_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_lisp)
  add_dependencies(excavator_msgs_generate_messages_lisp std_msgs_generate_messages_lisp)
endif()
if(TARGET geometry_msgs_generate_messages_lisp)
  add_dependencies(excavator_msgs_generate_messages_lisp geometry_msgs_generate_messages_lisp)
endif()

if(gennodejs_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs)
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${gennodejs_INSTALL_DIR}/excavator_msgs
    DESTINATION ${gennodejs_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_nodejs)
  add_dependencies(excavator_msgs_generate_messages_nodejs std_msgs_generate_messages_nodejs)
endif()
if(TARGET geometry_msgs_generate_messages_nodejs)
  add_dependencies(excavator_msgs_generate_messages_nodejs geometry_msgs_generate_messages_nodejs)
endif()

if(genpy_INSTALL_DIR AND EXISTS ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs)
  install(CODE "execute_process(COMMAND \"/usr/bin/python3\" -m compileall \"${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs\")")
  # install generated code
  install(
    DIRECTORY ${CATKIN_DEVEL_PREFIX}/${genpy_INSTALL_DIR}/excavator_msgs
    DESTINATION ${genpy_INSTALL_DIR}
  )
endif()
if(TARGET std_msgs_generate_messages_py)
  add_dependencies(excavator_msgs_generate_messages_py std_msgs_generate_messages_py)
endif()
if(TARGET geometry_msgs_generate_messages_py)
  add_dependencies(excavator_msgs_generate_messages_py geometry_msgs_generate_messages_py)
endif()
