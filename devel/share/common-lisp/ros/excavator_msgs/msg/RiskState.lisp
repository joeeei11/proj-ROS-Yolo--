; Auto-generated. Do not edit!


(cl:in-package excavator_msgs-msg)


;//! \htmlinclude RiskState.msg.html

(cl:defclass <RiskState> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (current_level
    :reader current_level
    :initarg :current_level
    :type cl:fixnum
    :initform 0)
   (min_distance
    :reader min_distance
    :initarg :min_distance
    :type cl:float
    :initform 0.0)
   (min_ttc
    :reader min_ttc
    :initarg :min_ttc
    :type cl:float
    :initform 0.0)
   (primary_threat_id
    :reader primary_threat_id
    :initarg :primary_threat_id
    :type cl:string
    :initform ""))
)

(cl:defclass RiskState (<RiskState>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <RiskState>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'RiskState)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name excavator_msgs-msg:<RiskState> is deprecated: use excavator_msgs-msg:RiskState instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <RiskState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:header-val is deprecated.  Use excavator_msgs-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'current_level-val :lambda-list '(m))
(cl:defmethod current_level-val ((m <RiskState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:current_level-val is deprecated.  Use excavator_msgs-msg:current_level instead.")
  (current_level m))

(cl:ensure-generic-function 'min_distance-val :lambda-list '(m))
(cl:defmethod min_distance-val ((m <RiskState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:min_distance-val is deprecated.  Use excavator_msgs-msg:min_distance instead.")
  (min_distance m))

(cl:ensure-generic-function 'min_ttc-val :lambda-list '(m))
(cl:defmethod min_ttc-val ((m <RiskState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:min_ttc-val is deprecated.  Use excavator_msgs-msg:min_ttc instead.")
  (min_ttc m))

(cl:ensure-generic-function 'primary_threat_id-val :lambda-list '(m))
(cl:defmethod primary_threat_id-val ((m <RiskState>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader excavator_msgs-msg:primary_threat_id-val is deprecated.  Use excavator_msgs-msg:primary_threat_id instead.")
  (primary_threat_id m))
(cl:defmethod roslisp-msg-protocol:symbol-codes ((msg-type (cl:eql '<RiskState>)))
    "Constants for message type '<RiskState>"
  '((:LEVEL_LOW . 0)
    (:LEVEL_MEDIUM . 1)
    (:LEVEL_HIGH . 2))
)
(cl:defmethod roslisp-msg-protocol:symbol-codes ((msg-type (cl:eql 'RiskState)))
    "Constants for message type 'RiskState"
  '((:LEVEL_LOW . 0)
    (:LEVEL_MEDIUM . 1)
    (:LEVEL_HIGH . 2))
)
(cl:defmethod roslisp-msg-protocol:serialize ((msg <RiskState>) ostream)
  "Serializes a message object of type '<RiskState>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'current_level)) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'min_distance))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'min_ttc))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'primary_threat_id))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'primary_threat_id))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <RiskState>) istream)
  "Deserializes a message object of type '<RiskState>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'current_level)) (cl:read-byte istream))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'min_distance) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'min_ttc) (roslisp-utils:decode-single-float-bits bits)))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'primary_threat_id) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'primary_threat_id) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<RiskState>)))
  "Returns string type for a message object of type '<RiskState>"
  "excavator_msgs/RiskState")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'RiskState)))
  "Returns string type for a message object of type 'RiskState"
  "excavator_msgs/RiskState")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<RiskState>)))
  "Returns md5sum for a message object of type '<RiskState>"
  "56281077a6d41cbba414fc9ed69c92af")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'RiskState)))
  "Returns md5sum for a message object of type 'RiskState"
  "56281077a6d41cbba414fc9ed69c92af")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<RiskState>)))
  "Returns full string definition for message of type '<RiskState>"
  (cl:format cl:nil "std_msgs/Header header~%uint8 LEVEL_LOW=0~%uint8 LEVEL_MEDIUM=1~%uint8 LEVEL_HIGH=2~%uint8 current_level~%float32 min_distance~%float32 min_ttc~%string primary_threat_id~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'RiskState)))
  "Returns full string definition for message of type 'RiskState"
  (cl:format cl:nil "std_msgs/Header header~%uint8 LEVEL_LOW=0~%uint8 LEVEL_MEDIUM=1~%uint8 LEVEL_HIGH=2~%uint8 current_level~%float32 min_distance~%float32 min_ttc~%string primary_threat_id~%~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <RiskState>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     1
     4
     4
     4 (cl:length (cl:slot-value msg 'primary_threat_id))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <RiskState>))
  "Converts a ROS message object to a list"
  (cl:list 'RiskState
    (cl:cons ':header (header msg))
    (cl:cons ':current_level (current_level msg))
    (cl:cons ':min_distance (min_distance msg))
    (cl:cons ':min_ttc (min_ttc msg))
    (cl:cons ':primary_threat_id (primary_threat_id msg))
))
