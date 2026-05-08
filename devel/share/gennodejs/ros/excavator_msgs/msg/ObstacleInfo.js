// Auto-generated. Do not edit!

// (in-package excavator_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let geometry_msgs = _finder('geometry_msgs');
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class ObstacleInfo {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.obstacle_id = null;
      this.obstacle_type = null;
      this.distance = null;
      this.relative_velocity = null;
      this.ttc = null;
      this.risk_score = null;
      this.risk_level = null;
      this.pose = null;
      this.velocity_vec = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('obstacle_id')) {
        this.obstacle_id = initObj.obstacle_id
      }
      else {
        this.obstacle_id = '';
      }
      if (initObj.hasOwnProperty('obstacle_type')) {
        this.obstacle_type = initObj.obstacle_type
      }
      else {
        this.obstacle_type = '';
      }
      if (initObj.hasOwnProperty('distance')) {
        this.distance = initObj.distance
      }
      else {
        this.distance = 0.0;
      }
      if (initObj.hasOwnProperty('relative_velocity')) {
        this.relative_velocity = initObj.relative_velocity
      }
      else {
        this.relative_velocity = 0.0;
      }
      if (initObj.hasOwnProperty('ttc')) {
        this.ttc = initObj.ttc
      }
      else {
        this.ttc = 0.0;
      }
      if (initObj.hasOwnProperty('risk_score')) {
        this.risk_score = initObj.risk_score
      }
      else {
        this.risk_score = 0.0;
      }
      if (initObj.hasOwnProperty('risk_level')) {
        this.risk_level = initObj.risk_level
      }
      else {
        this.risk_level = 0;
      }
      if (initObj.hasOwnProperty('pose')) {
        this.pose = initObj.pose
      }
      else {
        this.pose = new geometry_msgs.msg.PoseStamped();
      }
      if (initObj.hasOwnProperty('velocity_vec')) {
        this.velocity_vec = initObj.velocity_vec
      }
      else {
        this.velocity_vec = new geometry_msgs.msg.Vector3();
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ObstacleInfo
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [obstacle_id]
    bufferOffset = _serializer.string(obj.obstacle_id, buffer, bufferOffset);
    // Serialize message field [obstacle_type]
    bufferOffset = _serializer.string(obj.obstacle_type, buffer, bufferOffset);
    // Serialize message field [distance]
    bufferOffset = _serializer.float32(obj.distance, buffer, bufferOffset);
    // Serialize message field [relative_velocity]
    bufferOffset = _serializer.float32(obj.relative_velocity, buffer, bufferOffset);
    // Serialize message field [ttc]
    bufferOffset = _serializer.float32(obj.ttc, buffer, bufferOffset);
    // Serialize message field [risk_score]
    bufferOffset = _serializer.float32(obj.risk_score, buffer, bufferOffset);
    // Serialize message field [risk_level]
    bufferOffset = _serializer.uint8(obj.risk_level, buffer, bufferOffset);
    // Serialize message field [pose]
    bufferOffset = geometry_msgs.msg.PoseStamped.serialize(obj.pose, buffer, bufferOffset);
    // Serialize message field [velocity_vec]
    bufferOffset = geometry_msgs.msg.Vector3.serialize(obj.velocity_vec, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ObstacleInfo
    let len;
    let data = new ObstacleInfo(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [obstacle_id]
    data.obstacle_id = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [obstacle_type]
    data.obstacle_type = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [distance]
    data.distance = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [relative_velocity]
    data.relative_velocity = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [ttc]
    data.ttc = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [risk_score]
    data.risk_score = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [risk_level]
    data.risk_level = _deserializer.uint8(buffer, bufferOffset);
    // Deserialize message field [pose]
    data.pose = geometry_msgs.msg.PoseStamped.deserialize(buffer, bufferOffset);
    // Deserialize message field [velocity_vec]
    data.velocity_vec = geometry_msgs.msg.Vector3.deserialize(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    length += _getByteLength(object.obstacle_id);
    length += _getByteLength(object.obstacle_type);
    length += geometry_msgs.msg.PoseStamped.getMessageSize(object.pose);
    return length + 49;
  }

  static datatype() {
    // Returns string type for a message object
    return 'excavator_msgs/ObstacleInfo';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'fd4d72f9487b4c603a524a69bbad426f';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    std_msgs/Header header
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
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ObstacleInfo(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.obstacle_id !== undefined) {
      resolved.obstacle_id = msg.obstacle_id;
    }
    else {
      resolved.obstacle_id = ''
    }

    if (msg.obstacle_type !== undefined) {
      resolved.obstacle_type = msg.obstacle_type;
    }
    else {
      resolved.obstacle_type = ''
    }

    if (msg.distance !== undefined) {
      resolved.distance = msg.distance;
    }
    else {
      resolved.distance = 0.0
    }

    if (msg.relative_velocity !== undefined) {
      resolved.relative_velocity = msg.relative_velocity;
    }
    else {
      resolved.relative_velocity = 0.0
    }

    if (msg.ttc !== undefined) {
      resolved.ttc = msg.ttc;
    }
    else {
      resolved.ttc = 0.0
    }

    if (msg.risk_score !== undefined) {
      resolved.risk_score = msg.risk_score;
    }
    else {
      resolved.risk_score = 0.0
    }

    if (msg.risk_level !== undefined) {
      resolved.risk_level = msg.risk_level;
    }
    else {
      resolved.risk_level = 0
    }

    if (msg.pose !== undefined) {
      resolved.pose = geometry_msgs.msg.PoseStamped.Resolve(msg.pose)
    }
    else {
      resolved.pose = new geometry_msgs.msg.PoseStamped()
    }

    if (msg.velocity_vec !== undefined) {
      resolved.velocity_vec = geometry_msgs.msg.Vector3.Resolve(msg.velocity_vec)
    }
    else {
      resolved.velocity_vec = new geometry_msgs.msg.Vector3()
    }

    return resolved;
    }
};

module.exports = ObstacleInfo;
