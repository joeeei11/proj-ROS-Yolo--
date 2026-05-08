; Auto-generated. Do not edit!


(cl:in-package excavator_msgs-srv)


;//! \htmlinclude SpawnObstacle-request.msg.html

(cl:defclass <SpawnObstacle-request> (roslisp-msg-protocol:ros-message)
  ((obstacle_type
    :reader obstacle_type
    :initarg :obstacle_type
    :type cl:string
    :initform "")
   (pose
    :reader pose
    :initarg :pose
    :type geometry_msgs-msg:Pose
    :initform (cl:make-instance 'geometry_msgs-msg:Pose)))
)

(cl:defclass SpawnObstacle-request (<SpawnObstacle-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SpawnObstacle-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SpawnObstacle-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name excavator_msgs-srv:<SpawnObstacle-request> is deprecated: use excavator_msgs-srv:SpawnObstacle-request instead.")))

(cl:ensure-generic-function 'obstacle_type-val :lambda-list '(m))
(cl:defmethod obstacle_type-val ((m <SpawnObstacle-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-srv:obstacle_type-val is deprecated.  Use excavator_msgs-srv:obstacle_type instead.")
  (obstacle_type m))

(cl:ensure-generic-function 'pose-val :lambda-list '(m))
(cl:defmethod pose-val ((m <SpawnObstacle-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-srv:pose-val is deprecated.  Use excavator_msgs-srv:pose instead.")
  (pose m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SpawnObstacle-request>) ostream)
  "Serializes a message object of type '<SpawnObstacle-request>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'obstacle_type))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'obstacle_type))
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'pose) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SpawnObstacle-request>) istream)
  "Deserializes a message object of type '<SpawnObstacle-request>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'obstacle_type) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'obstacle_type) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'pose) istream)
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SpawnObstacle-request>)))
  "Returns string type for a service object of type '<SpawnObstacle-request>"
  "excavator_msgs/SpawnObstacleRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SpawnObstacle-request)))
  "Returns string type for a service object of type 'SpawnObstacle-request"
  "excavator_msgs/SpawnObstacleRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SpawnObstacle-request>)))
  "Returns md5sum for a message object of type '<SpawnObstacle-request>"
  "65854cfe8780150fdff4825667aa09ca")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SpawnObstacle-request)))
  "Returns md5sum for a message object of type 'SpawnObstacle-request"
  "65854cfe8780150fdff4825667aa09ca")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SpawnObstacle-request>)))
  "Returns full string definition for message of type '<SpawnObstacle-request>"
  (cl:format cl:nil "string obstacle_type~%geometry_msgs/Pose pose~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SpawnObstacle-request)))
  "Returns full string definition for message of type 'SpawnObstacle-request"
  (cl:format cl:nil "string obstacle_type~%geometry_msgs/Pose pose~%~%================================================================================~%MSG: geometry_msgs/Pose~%# A representation of pose in free space, composed of position and orientation. ~%Point position~%Quaternion orientation~%~%================================================================================~%MSG: geometry_msgs/Point~%# This contains the position of a point in free space~%float64 x~%float64 y~%float64 z~%~%================================================================================~%MSG: geometry_msgs/Quaternion~%# This represents an orientation in free space in quaternion form.~%~%float64 x~%float64 y~%float64 z~%float64 w~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SpawnObstacle-request>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'obstacle_type))
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'pose))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SpawnObstacle-request>))
  "Converts a ROS message object to a list"
  (cl:list 'SpawnObstacle-request
    (cl:cons ':obstacle_type (obstacle_type msg))
    (cl:cons ':pose (pose msg))
))
;//! \htmlinclude SpawnObstacle-response.msg.html

(cl:defclass <SpawnObstacle-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (obstacle_id
    :reader obstacle_id
    :initarg :obstacle_id
    :type cl:string
    :initform ""))
)

(cl:defclass SpawnObstacle-response (<SpawnObstacle-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SpawnObstacle-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SpawnObstacle-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name excavator_msgs-srv:<SpawnObstacle-response> is deprecated: use excavator_msgs-srv:SpawnObstacle-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <SpawnObstacle-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-srv:success-val is deprecated.  Use excavator_msgs-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'obstacle_id-val :lambda-list '(m))
(cl:defmethod obstacle_id-val ((m <SpawnObstacle-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-srv:obstacle_id-val is deprecated.  Use excavator_msgs-srv:obstacle_id instead.")
  (obstacle_id m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SpawnObstacle-response>) ostream)
  "Serializes a message object of type '<SpawnObstacle-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'obstacle_id))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'obstacle_id))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SpawnObstacle-response>) istream)
  "Deserializes a message object of type '<SpawnObstacle-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'obstacle_id) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'obstacle_id) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SpawnObstacle-response>)))
  "Returns string type for a service object of type '<SpawnObstacle-response>"
  "excavator_msgs/SpawnObstacleResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SpawnObstacle-response)))
  "Returns string type for a service object of type 'SpawnObstacle-response"
  "excavator_msgs/SpawnObstacleResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SpawnObstacle-response>)))
  "Returns md5sum for a message object of type '<SpawnObstacle-response>"
  "65854cfe8780150fdff4825667aa09ca")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SpawnObstacle-response)))
  "Returns md5sum for a message object of type 'SpawnObstacle-response"
  "65854cfe8780150fdff4825667aa09ca")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SpawnObstacle-response>)))
  "Returns full string definition for message of type '<SpawnObstacle-response>"
  (cl:format cl:nil "bool success~%string obstacle_id~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SpawnObstacle-response)))
  "Returns full string definition for message of type 'SpawnObstacle-response"
  (cl:format cl:nil "bool success~%string obstacle_id~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SpawnObstacle-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'obstacle_id))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SpawnObstacle-response>))
  "Converts a ROS message object to a list"
  (cl:list 'SpawnObstacle-response
    (cl:cons ':success (success msg))
    (cl:cons ':obstacle_id (obstacle_id msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'SpawnObstacle)))
  'SpawnObstacle-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'SpawnObstacle)))
  'SpawnObstacle-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SpawnObstacle)))
  "Returns string type for a service object of type '<SpawnObstacle>"
  "excavator_msgs/SpawnObstacle")