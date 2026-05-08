; Auto-generated. Do not edit!


(cl:in-package excavator_msgs-msg)


;//! \htmlinclude ObstacleInfo.msg.html

(cl:defclass <ObstacleInfo> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (obstacle_id
    :reader obstacle_id
    :initarg :obstacle_id
    :type cl:string
    :initform "")
   (obstacle_type
    :reader obstacle_type
    :initarg :obstacle_type
    :type cl:string
    :initform "")
   (distance
    :reader distance
    :initarg :distance
    :type cl:float
    :initform 0.0)
   (relative_velocity
    :reader relative_velocity
    :initarg :relative_velocity
    :type cl:float
    :initform 0.0)
   (ttc
    :reader ttc
    :initarg :ttc
    :type cl:float
    :initform 0.0)
   (risk_score
    :reader risk_score
    :initarg :risk_score
    :type cl:float
    :initform 0.0)
   (risk_level
    :reader risk_level
    :initarg :risk_level
    :type cl:fixnum
    :initform 0)
   (pose
    :reader pose
    :initarg :pose
    :type geometry_msgs-msg:PoseStamped
    :initform (cl:make-instance 'geometry_msgs-msg:PoseStamped))
   (velocity_vec
    :reader velocity_vec
    :initarg :velocity_vec
    :type geometry_msgs-msg:Vector3
    :initform (cl:make-instance 'geometry_msgs-msg:Vector3)))
)

(cl:defclass ObstacleInfo (<ObstacleInfo>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ObstacleInfo>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ObstacleInfo)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name excavator_msgs-msg:<ObstacleInfo> is deprecated: use excavator_msgs-msg:ObstacleInfo instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:header-val is deprecated.  Use excavator_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'obstacle_id-val :lambda-list '(m))
(cl:defmethod obstacle_id-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:obstacle_id-val is deprecated.  Use excavator_msgs-msg:obstacle_id instead.")
  (obstacle_id m))

(cl:ensure-generic-function 'obstacle_type-val :lambda-list '(m))
(cl:defmethod obstacle_type-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:obstacle_type-val is deprecated.  Use excavator_msgs-msg:obstacle_type instead.")
  (obstacle_type m))

(cl:ensure-generic-function 'distance-val :lambda-list '(m))
(cl:defmethod distance-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:distance-val is deprecated.  Use excavator_msgs-msg:distance instead.")
  (distance m))

(cl:ensure-generic-function 'relative_velocity-val :lambda-list '(m))
(cl:defmethod relative_velocity-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:relative_velocity-val is deprecated.  Use excavator_msgs-msg:relative_velocity instead.")
  (relative_velocity m))

(cl:ensure-generic-function 'ttc-val :lambda-list '(m))
(cl:defmethod ttc-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:ttc-val is deprecated.  Use excavator_msgs-msg:ttc instead.")
  (ttc m))

(cl:ensure-generic-function 'risk_score-val :lambda-list '(m))
(cl:defmethod risk_score-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:risk_score-val is deprecated.  Use excavator_msgs-msg:risk_score instead.")
  (risk_score m))

(cl:ensure-generic-function 'risk_level-val :lambda-list '(m))
(cl:defmethod risk_level-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:risk_level-val is deprecated.  Use excavator_msgs-msg:risk_level instead.")
  (risk_level m))

(cl:ensure-generic-function 'pose-val :lambda-list '(m))
(cl:defmethod pose-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:pose-val is deprecated.  Use excavator_msgs-msg:pose instead.")
  (pose m))

(cl:ensure-generic-function 'velocity_vec-val :lambda-list '(m))
(cl:defmethod velocity_vec-val ((m <ObstacleInfo>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:velocity_vec-val is deprecated.  Use excavator_msgs-msg:velocity_vec instead.")
  (velocity_vec m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ObstacleInfo>) ostream)
  "Serializes a message object of type '<ObstacleInfo>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'obstacle_id))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'obstacle_id))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'obstacle_type))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'obstacle_type))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'distance))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'relative_velocity))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'ttc))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'risk_score))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'risk_level)) ostream)
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'pose) ostream)
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'velocity_vec) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ObstacleInfo>) istream)
  "Deserializes a message object of type '<ObstacleInfo>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'obstacle_id) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'obstacle_id) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'obstacle_type) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'obstacle_type) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'distance) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'relative_velocity) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'ttc) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'risk_score) (roslisp-utils:decode-single-float-bits bits)))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'risk_level)) (cl:read-byte istream))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'pose) istream)
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'velocity_vec) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ObstacleInfo>)))
  "Returns string type for a message object of type '<ObstacleInfo>"
  "excavator_msgs/ObstacleInfo")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ObstacleInfo)))
  "Returns string type for a message object of type 'ObstacleInfo"
  "excavator_msgs/ObstacleInfo")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ObstacleInfo>)))
  "Returns md5sum for a message object of type '<ObstacleInfo>"
  "fd4d72f9487b4c603a524a69bbad426f")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ObstacleInfo)))
  "Returns md5sum for a message object of type 'ObstacleInfo"
  "fd4d72f9487b4c603a524a69bbad426f")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ObstacleInfo>)))
  "Returns full string definition for message of type '<ObstacleInfo>"
  (cl:format cl:nil "std_msgs/Header header~%string obstacle_id~%string obstacle_type~%float32 distance~%float32 relative_velocity~%float32 ttc~%float32 risk_score~%uint8 risk_level~%geometry_msgs/PoseStamped pose~%geometry_msgs/Vector3 velocity_vec~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/PoseStamped~%# A Pose with reference coordinate frame and timestamp~%Header header~%Pose pose~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ObstacleInfo)))
  "Returns full string definition for message of type 'ObstacleInfo"
  (cl:format cl:nil "std_msgs/Header header~%string obstacle_id~%string obstacle_type~%float32 distance~%float32 relative_velocity~%float32 ttc~%float32 risk_score~%uint8 risk_level~%geometry_msgs/PoseStamped pose~%geometry_msgs/Vector3 velocity_vec~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%================================================================================~%MSG: geometry_msgs/PoseStamped~%# A Pose with reference coordinate frame and timestamp~%Header header~%Pose pose~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%================================================================================~%MSG: geometry_msgs/Vector3~%# This represents a vector in free space. ~%# It is only meant to represent a direction. Therefore, it does not~%# make sense to apply a translation to it (e.g., when applying a ~%# generic rigid transformation to a Vector3, tf2 will only apply the~%# rotation). If you want your data to be translatable too, use the~%# geometry_msgs/Point message instead.~%~%float64 x~%float64 y~%float64 z~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ObstacleInfo>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4 (cl:length (cl:slot-value msg 'obstacle_id))
     4 (cl:length (cl:slot-value msg 'obstacle_type))
     4
     4
     4
     4
     1
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'pose))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'velocity_vec))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ObstacleInfo>))
  "Converts a ROS message object to a list"
  (cl:list 'ObstacleInfo
    (cl:cons ':header (header msg))
    (cl:cons ':obstacle_id (obstacle_id msg))
    (cl:cons ':obstacle_type (obstacle_type msg))
    (cl:cons ':distance (distance msg))
    (cl:cons ':relative_velocity (relative_velocity msg))
    (cl:cons ':ttc (ttc msg))
    (cl:cons ':risk_score (risk_score msg))
    (cl:cons ':risk_level (risk_level msg))
    (cl:cons ':pose (pose msg))
    (cl:cons ':velocity_vec (velocity_vec msg))
))
