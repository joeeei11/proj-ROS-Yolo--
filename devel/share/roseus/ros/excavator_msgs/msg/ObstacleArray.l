;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::ObstacleArray)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'ObstacleArray (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::OBSTACLEARRAY")
  (make-package "EXCAVATOR_MSGS::OBSTACLEARRAY"))

(in-package "ROS")
;;//! \htmlinclude ObstacleArray.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass excavator_msgs::ObstacleArray
  :super ros::object
  :slots (_header _obstacles _dominant_risk_level ))

(defmethod excavator_msgs::ObstacleArray
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:obstacles __obstacles) ())
    ((:dominant_risk_level __dominant_risk_level) 0)
    )
   (send-super :init)
   (setq _header __header)
   (setq _obstacles __obstacles)
   (setq _dominant_risk_level (round __dominant_risk_level))
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:obstacles
   (&rest __obstacles)
   (if (keywordp (car __obstacles))
       (send* _obstacles __obstacles)
     (progn
       (if __obstacles (setq _obstacles (car __obstacles)))
       _obstacles)))
  (:dominant_risk_level
   (&optional __dominant_risk_level)
   (if __dominant_risk_level (setq _dominant_risk_level __dominant_risk_level)) _dominant_risk_level)
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; excavator_msgs/ObstacleInfo[] _obstacles
    (apply #'+ (send-all _obstacles :serialization-length)) 4
    ;; uint8 _dominant_risk_level
    1
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; excavator_msgs/ObstacleInfo[] _obstacles
     (write-long (length _obstacles) s)
     (dolist (elem _obstacles)
       (send elem :serialize s)
       )
     ;; uint8 _dominant_risk_level
       (write-byte _dominant_risk_level s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; excavator_msgs/ObstacleInfo[] _obstacles
   (let (n)
     (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4)
     (setq _obstacles (let (r) (dotimes (i n) (push (instance excavator_msgs::ObstacleInfo :init) r)) r))
     (dolist (elem- _obstacles)
     (send elem- :deserialize buf ptr-) (incf ptr- (send elem- :serialization-length))
     ))
   ;; uint8 _dominant_risk_level
     (setq _dominant_risk_level (sys::peek buf ptr- :char)) (incf ptr- 1)
   ;;
   self)
  )

(setf (get excavator_msgs::ObstacleArray :md5sum-) "47b96ec652e3bd0352f9dd3764857936")
(setf (get excavator_msgs::ObstacleArray :datatype-) "excavator_msgs/ObstacleArray")
(setf (get excavator_msgs::ObstacleArray :definition-)
      "std_msgs/Header header
excavator_msgs/ObstacleInfo[] obstacles
uint8 dominant_risk_level

================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
string frame_id

================================================================================
MSG: excavator_msgs/ObstacleInfo
std_msgs/Header header
string obstacle_id
string obstacle_type
float32 distance
float32 relative_velocity
float32 ttc
float32 risk_score
uint8 risk_level
geometry_msgs/PoseStamped pose
geometry_msgs/Vector3 velocity_vec

================================================================================
MSG: geometry_msgs/PoseStamped
# A Pose with reference coordinate frame and timestamp
Header header
Pose pose

================================================================================
MSG: geometry_msgs/Pose
# A representation of pose in free space, composed of position and orientation. 
Point position
Quaternion orientation

================================================================================
MSG: geometry_msgs/Point
# This contains the position of a point in free space
float64 x
float64 y
float64 z

================================================================================
MSG: geometry_msgs/Quaternion
# This represents an orientation in free space in quaternion form.

float64 x
float64 y
float64 z
float64 w

================================================================================
MSG: geometry_msgs/Vector3
# This represents a vector in free space. 
# It is only meant to represent a direction. Therefore, it does not
# make sense to apply a translation to it (e.g., when applying a 
# generic rigid transformation to a Vector3, tf2 will only apply the
# rotation). If you want your data to be translatable too, use the
# geometry_msgs/Point message instead.

float64 x
float64 y
float64 z
")



(provide :excavator_msgs/ObstacleArray "47b96ec652e3bd0352f9dd3764857936")


