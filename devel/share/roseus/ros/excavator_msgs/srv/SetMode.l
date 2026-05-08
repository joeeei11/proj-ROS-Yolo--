;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::SetMode)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'SetMode (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::SETMODE")
  (make-package "EXCAVATOR_MSGS::SETMODE"))
(unless (find-package "EXCAVATOR_MSGS::SETMODEREQUEST")
  (make-package "EXCAVATOR_MSGS::SETMODEREQUEST"))
(unless (find-package "EXCAVATOR_MSGS::SETMODERESPONSE")
  (make-package "EXCAVATOR_MSGS::SETMODERESPONSE"))

(in-package "ROS")





(defclass excavator_msgs::SetModeRequest
  :super ros::object
  :slots (_mode ))

(defmethod excavator_msgs::SetModeRequest
  (:init
   (&key
    ((:mode __mode) "")
    )
   (send-super :init)
   (setq _mode (string __mode))
   self)
  (:mode
   (&optional __mode)
   (if __mode (setq _mode __mode)) _mode)
  (:serialization-length
   ()
   (+
    ;; string _mode
    4 (length _mode)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _mode
       (write-long (length _mode) s) (princ _mode s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _mode
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _mode (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass excavator_msgs::SetModeResponse
  :super ros::object
  :slots (_success _message ))

(defmethod excavator_msgs::SetModeResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:message __message) "")
    )
   (send-super :init)
   (setq _success __success)
   (setq _message (string __message))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:message
   (&optional __message)
   (if __message (setq _message __message)) _message)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _message
    4 (length _message)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _message
       (write-long (length _message) s) (princ _message s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass excavator_msgs::SetMode
  :super ros::object
  :slots ())

(setf (get excavator_msgs::SetMode :md5sum-) "1393b8f659688f5f0d86f35948597ef1")
(setf (get excavator_msgs::SetMode :datatype-) "excavator_msgs/SetMode")
(setf (get excavator_msgs::SetMode :request) excavator_msgs::SetModeRequest)
(setf (get excavator_msgs::SetMode :response) excavator_msgs::SetModeResponse)

(defmethod excavator_msgs::SetModeRequest
  (:response () (instance excavator_msgs::SetModeResponse :init)))

(setf (get excavator_msgs::SetModeRequest :md5sum-) "1393b8f659688f5f0d86f35948597ef1")
(setf (get excavator_msgs::SetModeRequest :datatype-) "excavator_msgs/SetModeRequest")
(setf (get excavator_msgs::SetModeRequest :definition-)
      "string mode
---
bool success
string message

")

(setf (get excavator_msgs::SetModeResponse :md5sum-) "1393b8f659688f5f0d86f35948597ef1")
(setf (get excavator_msgs::SetModeResponse :datatype-) "excavator_msgs/SetModeResponse")
(setf (get excavator_msgs::SetModeResponse :definition-)
      "string mode
---
bool success
string message

")



(provide :excavator_msgs/SetMode "1393b8f659688f5f0d86f35948597ef1")


