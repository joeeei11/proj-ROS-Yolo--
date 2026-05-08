;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::RiskState)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'RiskState (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::RISKSTATE")
  (make-package "EXCAVATOR_MSGS::RISKSTATE"))

(in-package "ROS")
;;//! \htmlinclude RiskState.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(intern "*LEVEL_LOW*" (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(shadow '*LEVEL_LOW* (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(defconstant excavator_msgs::RiskState::*LEVEL_LOW* 0)
(intern "*LEVEL_MEDIUM*" (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(shadow '*LEVEL_MEDIUM* (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(defconstant excavator_msgs::RiskState::*LEVEL_MEDIUM* 1)
(intern "*LEVEL_HIGH*" (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(shadow '*LEVEL_HIGH* (find-package "EXCAVATOR_MSGS::RISKSTATE"))
(defconstant excavator_msgs::RiskState::*LEVEL_HIGH* 2)

(defun excavator_msgs::RiskState-to-symbol (const)
  (cond
        ((= const 0) 'excavator_msgs::RiskState::*LEVEL_LOW*)
        ((= const 1) 'excavator_msgs::RiskState::*LEVEL_MEDIUM*)
        ((= const 2) 'excavator_msgs::RiskState::*LEVEL_HIGH*)
        (t nil)))

(defclass excavator_msgs::RiskState
  :super ros::object
  :slots (_header _current_level _min_distance _min_ttc _primary_threat_id ))

(defmethod excavator_msgs::RiskState
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:current_level __current_level) 0)
    ((:min_distance __min_distance) 0.0)
    ((:min_ttc __min_ttc) 0.0)
    ((:primary_threat_id __primary_threat_id) "")
    )
   (send-super :init)
   (setq _header __header)
   (setq _current_level (round __current_level))
   (setq _min_distance (float __min_distance))
   (setq _min_ttc (float __min_ttc))
   (setq _primary_threat_id (string __primary_threat_id))
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:current_level
   (&optional __current_level)
   (if __current_level (setq _current_level __current_level)) _current_level)
  (:min_distance
   (&optional __min_distance)
   (if __min_distance (setq _min_distance __min_distance)) _min_distance)
  (:min_ttc
   (&optional __min_ttc)
   (if __min_ttc (setq _min_ttc __min_ttc)) _min_ttc)
  (:primary_threat_id
   (&optional __primary_threat_id)
   (if __primary_threat_id (setq _primary_threat_id __primary_threat_id)) _primary_threat_id)
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; uint8 _current_level
    1
    ;; float32 _min_distance
    4
    ;; float32 _min_ttc
    4
    ;; string _primary_threat_id
    4 (length _primary_threat_id)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; uint8 _current_level
       (write-byte _current_level s)
     ;; float32 _min_distance
       (sys::poke _min_distance (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; float32 _min_ttc
       (sys::poke _min_ttc (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; string _primary_threat_id
       (write-long (length _primary_threat_id) s) (princ _primary_threat_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; uint8 _current_level
     (setq _current_level (sys::peek buf ptr- :char)) (incf ptr- 1)
   ;; float32 _min_distance
     (setq _min_distance (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; float32 _min_ttc
     (setq _min_ttc (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; string _primary_threat_id
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _primary_threat_id (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(setf (get excavator_msgs::RiskState :md5sum-) "56281077a6d41cbba414fc9ed69c92af")
(setf (get excavator_msgs::RiskState :datatype-) "excavator_msgs/RiskState")
(setf (get excavator_msgs::RiskState :definition-)
      "std_msgs/Header header
uint8 LEVEL_LOW=0
uint8 LEVEL_MEDIUM=1
uint8 LEVEL_HIGH=2
uint8 current_level
float32 min_distance
float32 min_ttc
string primary_threat_id

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

")



(provide :excavator_msgs/RiskState "56281077a6d41cbba414fc9ed69c92af")


