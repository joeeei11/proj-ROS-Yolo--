
(cl:in-package :asdf)

(defsystem "excavator_msgs-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
)
  :components ((:file "_package")
    (:file "SetMode" :depends-on ("_package_SetMode"))
    (:file "_package_SetMode" :depends-on ("_package"))
    (:file "SpawnObstacle" :depends-on ("_package_SpawnObstacle"))
    (:file "_package_SpawnObstacle" :depends-on ("_package"))
  ))