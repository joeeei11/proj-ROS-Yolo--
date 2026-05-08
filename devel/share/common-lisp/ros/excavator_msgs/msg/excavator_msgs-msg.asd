
(cl:in-package :asdf)

(defsystem "excavator_msgs-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :geometry_msgs-msg
               :std_msgs-msg
)
  :components ((:file "_package")
    (:file "ObstacleArray" :depends-on ("_package_ObstacleArray"))
    (:file "_package_ObstacleArray" :depends-on ("_package"))
    (:file "ObstacleInfo" :depends-on ("_package_ObstacleInfo"))
    (:file "_package_ObstacleInfo" :depends-on ("_package"))
    (:file "RiskState" :depends-on ("_package_RiskState"))
    (:file "_package_RiskState" :depends-on ("_package"))
    (:file "SystemState" :depends-on ("_package_SystemState"))
    (:file "_package_SystemState" :depends-on ("_package"))
  ))