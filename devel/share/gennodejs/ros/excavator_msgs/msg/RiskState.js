// Auto-generated. Do not edit!

// (in-package excavator_msgs.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class RiskState {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.current_level = null;
      this.min_distance = null;
      this.min_ttc = null;
      this.primary_threat_id = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('current_level')) {
        this.current_level = initObj.current_level
      }
      else {
        this.current_level = 0;
      }
      if (initObj.hasOwnProperty('min_distance')) {
        this.min_distance = initObj.min_distance
      }
      else {
        this.min_distance = 0.0;
      }
      if (initObj.hasOwnProperty('min_ttc')) {
        this.min_ttc = initObj.min_ttc
      }
      else {
        this.min_ttc = 0.0;
      }
      if (initObj.hasOwnProperty('primary_threat_id')) {
        this.primary_threat_id = initObj.primary_threat_id
      }
      else {
        this.primary_threat_id = '';
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type RiskState
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [current_level]
    bufferOffset = _serializer.uint8(obj.current_level, buffer, bufferOffset);
    // Serialize message field [min_distance]
    bufferOffset = _serializer.float32(obj.min_distance, buffer, bufferOffset);
    // Serialize message field [min_ttc]
    bufferOffset = _serializer.float32(obj.min_ttc, buffer, bufferOffset);
    // Serialize message field [primary_threat_id]
    bufferOffset = _serializer.string(obj.primary_threat_id, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type RiskState
    let len;
    let data = new RiskState(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [current_level]
    data.current_level = _deserializer.uint8(buffer, bufferOffset);
    // Deserialize message field [min_distance]
    data.min_distance = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [min_ttc]
    data.min_ttc = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [primary_threat_id]
    data.primary_threat_id = _deserializer.string(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    length += _getByteLength(object.primary_threat_id);
    return length + 13;
  }

  static datatype() {
    // Returns string type for a message object
    return 'excavator_msgs/RiskState';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '56281077a6d41cbba414fc9ed69c92af';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    std_msgs/Header header
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new RiskState(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.current_level !== undefined) {
      resolved.current_level = msg.current_level;
    }
    else {
      resolved.current_level = 0
    }

    if (msg.min_distance !== undefined) {
      resolved.min_distance = msg.min_distance;
    }
    else {
      resolved.min_distance = 0.0
    }

    if (msg.min_ttc !== undefined) {
      resolved.min_ttc = msg.min_ttc;
    }
    else {
      resolved.min_ttc = 0.0
    }

    if (msg.primary_threat_id !== undefined) {
      resolved.primary_threat_id = msg.primary_threat_id;
    }
    else {
      resolved.primary_threat_id = ''
    }

    return resolved;
    }
};

// Constants for message
RiskState.Constants = {
  LEVEL_LOW: 0,
  LEVEL_MEDIUM: 1,
  LEVEL_HIGH: 2,
}

module.exports = RiskState;
