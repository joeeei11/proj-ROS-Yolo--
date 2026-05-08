;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::SystemState)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'SystemState (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::SYSTEMSTATE")
  (make-package "EXCAVATOR_MSGS::SYSTEMSTATE"))

(in-package "ROS")
;;//! \htmlinclude SystemState.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(intern "*NORMAL*" (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(shadow '*NORMAL* (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(defconstant excavator_msgs::SystemState::*NORMAL* 0)
(intern "*CAUTION*" (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(shadow '*CAUTION* (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(defconstant excavator_msgs::SystemState::*CAUTION* 1)
(intern "*PAUSED*" (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(shadow '*PAUSED* (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(defconstant excavator_msgs::SystemState::*PAUSED* 2)
(intern "*EMERGENCY_STOP*" (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(shadow '*EMERGENCY_STOP* (find-package "EXCAVATOR_MSGS::SYSTEMSTATE"))
(defconstant excavator_msgs::SystemState::*EMERGENCY_STOP* 3)

(defun excavator_msgs::SystemState-to-symbol (const)
  (cond
        ((= const 0) 'excavator_msgs::SystemState::*NORMAL*)
        ((= const 1) 'excavator_msgs::SystemState::*CAUTION*)
        ((= const 2) 'excavator_msgs::SystemState::*PAUSED*)
        ((= const 3) 'excavator_msgs::SystemState::*EMERGENCY_STOP*)
        (t nil)))

(defclass excavator_msgs::SystemState
  :super ros::object
  :slots (_header _state _reason _state_duration ))

(defmethod excavator_msgs::SystemState
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:state __state) 0)
    ((:reason __reason) "")
    ((:state_duration __state_duration) 0.0)
    )
   (send-super :init)
   (setq _header __header)
   (setq _state (round __state))
   (setq _reason (string __reason))
   (setq _state_duration (float __state_duration))
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:state
   (&optional __state)
   (if __state (setq _state __state)) _state)
  (:reason
   (&optional __reason)
   (if __reason (setq _reason __reason)) _reason)
  (:state_duration
   (&optional __state_duration)
   (if __state_duration (setq _state_duration __state_duration)) _state_duration)
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; uint8 _state
    1
    ;; string _reason
    4 (length _reason)
    ;; float32 _state_duration
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; uint8 _state
       (write-byte _state s)
     ;; string _reason
       (write-long (length _reason) s) (princ _reason s)
     ;; float32 _state_duration
       (sys::poke _state_duration (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; uint8 _state
     (setq _state (sys::peek buf ptr- :char)) (incf ptr- 1)
   ;; string _reason
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _reason (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _state_duration
     (setq _state_duration (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(setf (get excavator_msgs::SystemState :md5sum-) "72a42d7c3c302c099e7dd37f30ca5c90")
(setf (get excavator_msgs::SystemState :datatype-) "excavator_msgs/SystemState")
(setf (get excavator_msgs::SystemState :definition-)
      "std_msgs/Header header
uint8 NORMAL=0
uint8 CAUTION=1
uint8 PAUSED=2
uint8 EMERGENCY_STOP=3
uint8 state
string reason
float32 state_duration

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



(provide :excavator_msgs/SystemState "72a42d7c3c302c099e7dd37f30ca5c90")


