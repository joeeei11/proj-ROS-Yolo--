;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::ObstacleInfo)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'ObstacleInfo (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::OBSTACLEINFO")
  (make-package "EXCAVATOR_MSGS::OBSTACLEINFO"))

(in-package "ROS")
;;//! \htmlinclude ObstacleInfo.msg.html
(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass excavator_msgs::ObstacleInfo
  :super ros::object
  :slots (_header _obstacle_id _obstacle_type _distance _relative_velocity _ttc _risk_score _risk_level _pose _velocity_vec ))

(defmethod excavator_msgs::ObstacleInfo
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:obstacle_id __obstacle_id) "")
    ((:obstacle_type __obstacle_type) "")
    ((:distance __distance) 0.0)
    ((:relative_velocity __relative_velocity) 0.0)
    ((:ttc __ttc) 0.0)
    ((:risk_score __risk_score) 0.0)
    ((:risk_level __risk_level) 0)
    ((:pose __pose) (instance geometry_msgs::PoseStamped :init))
    ((:velocity_vec __velocity_vec) (instance geometry_msgs::Vector3 :init))
    )
   (send-super :init)
   (setq _header __header)
   (setq _obstacle_id (string __obstacle_id))
   (setq _obstacle_type (string __obstacle_type))
   (setq _distance (float __distance))
   (setq _relative_velocity (float __relative_velocity))
   (setq _ttc (float __ttc))
   (setq _risk_score (float __risk_score))
   (setq _risk_level (round __risk_level))
   (setq _pose __pose)
   (setq _velocity_vec __velocity_vec)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:obstacle_id
   (&optional __obstacle_id)
   (if __obstacle_id (setq _obstacle_id __obstacle_id)) _obstacle_id)
  (:obstacle_type
   (&optional __obstacle_type)
   (if __obstacle_type (setq _obstacle_type __obstacle_type)) _obstacle_type)
  (:distance
   (&optional __distance)
   (if __distance (setq _distance __distance)) _distance)
  (:relative_velocity
   (&optional __relative_velocity)
   (if __relative_velocity (setq _relative_velocity __relative_velocity)) _relative_velocity)
  (:ttc
   (&optional __ttc)
   (if __ttc (setq _ttc __ttc)) _ttc)
  (:risk_score
   (&optional __risk_score)
   (if __risk_score (setq _risk_score __risk_score)) _risk_score)
  (:risk_level
   (&optional __risk_level)
   (if __risk_level (setq _risk_level __risk_level)) _risk_level)
  (:pose
   (&rest __pose)
   (if (keywordp (car __pose))
       (send* _pose __pose)
     (progn
       (if __pose (setq _pose (car __pose)))
       _pose)))
  (:velocity_vec
   (&rest __velocity_vec)
   (if (keywordp (car __velocity_vec))
       (send* _velocity_vec __velocity_vec)
     (progn
       (if __velocity_vec (setq _velocity_vec (car __velocity_vec)))
       _velocity_vec)))
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; string _obstacle_id
    4 (length _obstacle_id)
    ;; string _obstacle_type
    4 (length _obstacle_type)
    ;; float32 _distance
    4
    ;; float32 _relative_velocity
    4
    ;; float32 _ttc
    4
    ;; float32 _risk_score
    4
    ;; uint8 _risk_level
    1
    ;; geometry_msgs/PoseStamped _pose
    (send _pose :serialization-length)
    ;; geometry_msgs/Vector3 _velocity_vec
    (send _velocity_vec :serialization-length)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; string _obstacle_id
       (write-long (length _obstacle_id) s) (princ _obstacle_id s)
     ;; string _obstacle_type
       (write-long (length _obstacle_type) s) (princ _obstacle_type s)
     ;; float32 _distance
       (sys::poke _distance (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _relative_velocity
       (sys::poke _relative_velocity (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _ttc
       (sys::poke _ttc (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _risk_score
       (sys::poke _risk_score (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; uint8 _risk_level
       (write-byte _risk_level s)
     ;; geometry_msgs/PoseStamped _pose
       (send _pose :serialize s)
     ;; geometry_msgs/Vector3 _velocity_vec
       (send _velocity_vec :serialize s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; string _obstacle_id
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _obstacle_id (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _obstacle_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _obstacle_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _distance
     (setq _distance (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _relative_velocity
     (setq _relative_velocity (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _ttc
     (setq _ttc (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _risk_score
     (setq _risk_score (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; uint8 _risk_level
     (setq _risk_level (sys::peek buf ptr- :char)) (incf ptr- 1)
   ;; geometry_msgs/PoseStamped _pose
     (send _pose :deserialize buf ptr-) (incf ptr- (send _pose :serialization-length))
   ;; geometry_msgs/Vector3 _velocity_vec
     (send _velocity_vec :deserialize buf ptr-) (incf ptr- (send _velocity_vec :serialization-length))
   ;;
   self)
  )

(setf (get excavator_msgs::ObstacleInfo :md5sum-) "fd4d72f9487b4c603a524a69bbad426f")
(setf (get excavator_msgs::ObstacleInfo :datatype-) "excavator_msgs/ObstacleInfo")
(setf (get excavator_msgs::ObstacleInfo :definition-)
      "std_msgs/Header header
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



(provide :excavator_msgs/ObstacleInfo "fd4d72f9487b4c603a524a69bbad426f")


