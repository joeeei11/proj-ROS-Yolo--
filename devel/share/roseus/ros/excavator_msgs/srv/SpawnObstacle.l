;; Auto-generated. Do not edit!


(when (boundp 'excavator_msgs::SpawnObstacle)
  (if (not (find-package "EXCAVATOR_MSGS"))
    (make-package "EXCAVATOR_MSGS"))
  (shadow 'SpawnObstacle (find-package "EXCAVATOR_MSGS")))
(unless (find-package "EXCAVATOR_MSGS::SPAWNOBSTACLE")
  (make-package "EXCAVATOR_MSGS::SPAWNOBSTACLE"))
(unless (find-package "EXCAVATOR_MSGS::SPAWNOBSTACLEREQUEST")
  (make-package "EXCAVATOR_MSGS::SPAWNOBSTACLEREQUEST"))
(unless (find-package "EXCAVATOR_MSGS::SPAWNOBSTACLERESPONSE")
  (make-package "EXCAVATOR_MSGS::SPAWNOBSTACLERESPONSE"))

(in-package "ROS")

(if (not (find-package "GEOMETRY_MSGS"))
  (ros::roseus-add-msgs "geometry_msgs"))




(defclass excavator_msgs::SpawnObstacleRequest
  :super ros::object
  :slots (_obstacle_type _pose ))

(defmethod excavator_msgs::SpawnObstacleRequest
  (:init
   (&key
    ((:obstacle_type __obstacle_type) "")
    ((:pose __pose) (instance geometry_msgs::Pose :init))
    )
   (send-super :init)
   (setq _obstacle_type (string __obstacle_type))
   (setq _pose __pose)
   self)
  (:obstacle_type
   (&optional __obstacle_type)
   (if __obstacle_type (setq _obstacle_type __obstacle_type)) _obstacle_type)
  (:pose
   (&rest __pose)
   (if (keywordp (car __pose))
       (send* _pose __pose)
     (progn
       (if __pose (setq _pose (car __pose)))
       _pose)))
  (:serialization-length
   ()
   (+
    ;; string _obstacle_type
    4 (length _obstacle_type)
    ;; geometry_msgs/Pose _pose
    (send _pose :serialization-length)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _obstacle_type
       (write-long (length _obstacle_type) s) (princ _obstacle_type s)
     ;; geometry_msgs/Pose _pose
       (send _pose :serialize s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _obstacle_type
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _obstacle_type (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; geometry_msgs/Pose _pose
     (send _pose :deserialize buf ptr-) (incf ptr- (send _pose :serialization-length))
   ;;
   self)
  )

(defclass excavator_msgs::SpawnObstacleResponse
  :super ros::object
  :slots (_success _obstacle_id ))

(defmethod excavator_msgs::SpawnObstacleResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:obstacle_id __obstacle_id) "")
    )
   (send-super :init)
   (setq _success __success)
   (setq _obstacle_id (string __obstacle_id))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:obstacle_id
   (&optional __obstacle_id)
   (if __obstacle_id (setq _obstacle_id __obstacle_id)) _obstacle_id)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _obstacle_id
    4 (length _obstacle_id)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _obstacle_id
       (write-long (length _obstacle_id) s) (princ _obstacle_id s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _obstacle_id
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _obstacle_id (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass excavator_msgs::SpawnObstacle
  :super ros::object
  :slots ())

(setf (get excavator_msgs::SpawnObstacle :md5sum-) "65854cfe8780150fdff4825667aa09ca")
(setf (get excavator_msgs::SpawnObstacle :datatype-) "excavator_msgs/SpawnObstacle")
(setf (get excavator_msgs::SpawnObstacle :request) excavator_msgs::SpawnObstacleRequest)
(setf (get excavator_msgs::SpawnObstacle :response) excavator_msgs::SpawnObstacleResponse)

(defmethod excavator_msgs::SpawnObstacleRequest
  (:response () (instance excavator_msgs::SpawnObstacleResponse :init)))

(setf (get excavator_msgs::SpawnObstacleRequest :md5sum-) "65854cfe8780150fdff4825667aa09ca")
(setf (get excavator_msgs::SpawnObstacleRequest :datatype-) "excavator_msgs/SpawnObstacleRequest")
(setf (get excavator_msgs::SpawnObstacleRequest :definition-)
      "string obstacle_type
geometry_msgs/Pose pose

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
---
bool success
string obstacle_id

")

(setf (get excavator_msgs::SpawnObstacleResponse :md5sum-) "65854cfe8780150fdff4825667aa09ca")
(setf (get excavator_msgs::SpawnObstacleResponse :datatype-) "excavator_msgs/SpawnObstacleResponse")
(setf (get excavator_msgs::SpawnObstacleResponse :definition-)
      "string obstacle_type
geometry_msgs/Pose pose

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
---
bool success
string obstacle_id

")



(provide :excavator_msgs/SpawnObstacle "65854cfe8780150fdff4825667aa09ca")


