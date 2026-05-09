#include "excavator_planner/rrt_star_planner.h"

#include <algorithm>
#include <limits>
#include <ctime>

namespace excavator_planner {

// ─────────────────────────────────────────────────────────────────────────────
// RRTStar – algorithm implementation
// ─────────────────────────────────────────────────────────────────────────────

RRTStar::RRTStar(const Params& p)
    : params_(p),
      rng_(static_cast<unsigned>(std::time(nullptr))),
      uni_x_(p.x_min, p.x_max),
      uni_y_(p.y_min, p.y_max),
      uni01_(0.0, 1.0)
{}

void RRTStar::setObstacles(const std::vector<CircleObs>& obs) {
    obstacles_ = obs;
}

std::vector<Point2D> RRTStar::plan(const Point2D& start, const Point2D& goal) {
    nodes_.clear();
    nodes_.reserve(params_.max_iterations + 1);

    RRTNode root;
    root.x_ = start.x; root.y_ = start.y;
    root.parent_ = -1; root.cost_ = 0.0;
    nodes_.push_back(root);

    int goal_idx = -1;
    double best_goal_cost = std::numeric_limits<double>::infinity();

    auto deadline = std::chrono::steady_clock::now()
                  + std::chrono::duration<double>(params_.timeout_sec);

    for (int iter = 0; iter < params_.max_iterations; ++iter) {
        if (std::chrono::steady_clock::now() > deadline) {
            ROS_WARN("RRTStar: timeout after %d iterations", iter);
            break;
        }

        Point2D q_rand = sample(goal);
        int near_idx   = nearest(q_rand);
        Point2D q_new  = steer({nodes_[near_idx].x_, nodes_[near_idx].y_}, q_rand);

        if (!collisionFree({nodes_[near_idx].x_, nodes_[near_idx].y_}, q_new))
            continue;

        std::vector<int> near_ids = nearNodes(q_new);

        // Choose best parent from near nodes
        int best_parent = near_idx;
        double best_cost = nodes_[near_idx].cost_
                         + dist({nodes_[near_idx].x_, nodes_[near_idx].y_}, q_new);
        for (int nid : near_ids) {
            double c = nodes_[nid].cost_
                     + dist({nodes_[nid].x_, nodes_[nid].y_}, q_new);
            if (c < best_cost &&
                collisionFree({nodes_[nid].x_, nodes_[nid].y_}, q_new)) {
                best_cost   = c;
                best_parent = nid;
            }
        }

        RRTNode new_node;
        new_node.x_      = q_new.x;
        new_node.y_      = q_new.y;
        new_node.parent_ = best_parent;
        new_node.cost_   = best_cost;
        nodes_.push_back(new_node);
        int new_idx = static_cast<int>(nodes_.size()) - 1;

        rewire(new_idx, near_ids);

        // Check if goal reached
        double d_goal = dist(q_new, goal);
        if (d_goal <= params_.goal_radius && best_cost < best_goal_cost) {
            best_goal_cost = best_cost;
            goal_idx = new_idx;
        }
    }

    if (goal_idx < 0) {
        ROS_WARN("RRTStar: no path found to goal (%.2f, %.2f)", goal.x, goal.y);
        return {};
    }

    std::vector<Point2D> raw = extractPath(goal_idx);
    return smoothPath(raw, 10);
}

// ── Core primitives ───────────────────────────────────────────────────────────

Point2D RRTStar::sample(const Point2D& goal) {
    // 10% goal bias
    if (uni01_(rng_) < 0.10)
        return goal;
    return {uni_x_(rng_), uni_y_(rng_)};
}

int RRTStar::nearest(const Point2D& q) const {
    int best = 0;
    double best_d = std::numeric_limits<double>::infinity();
    for (int i = 0; i < static_cast<int>(nodes_.size()); ++i) {
        double d = dist(q, {nodes_[i].x_, nodes_[i].y_});
        if (d < best_d) { best_d = d; best = i; }
    }
    return best;
}

Point2D RRTStar::steer(const Point2D& from, const Point2D& to) const {
    double d = dist(from, to);
    if (d <= params_.step_size) return to;
    double ratio = params_.step_size / d;
    return {from.x + ratio * (to.x - from.x),
            from.y + ratio * (to.y - from.y)};
}

bool RRTStar::collisionFree(const Point2D& a, const Point2D& b) const {
    return segmentFree(a, b);
}

std::vector<int> RRTStar::nearNodes(const Point2D& q) const {
    std::vector<int> result;
    double r = params_.rewire_radius;
    for (int i = 0; i < static_cast<int>(nodes_.size()); ++i) {
        if (dist(q, {nodes_[i].x_, nodes_[i].y_}) <= r)
            result.push_back(i);
    }
    return result;
}

void RRTStar::rewire(int new_idx, const std::vector<int>& near_ids) {
    const RRTNode& nn = nodes_[new_idx];
    Point2D np{nn.x_, nn.y_};
    for (int nid : near_ids) {
        double new_cost = nn.cost_ + dist(np, {nodes_[nid].x_, nodes_[nid].y_});
        if (new_cost < nodes_[nid].cost_ &&
            collisionFree(np, {nodes_[nid].x_, nodes_[nid].y_})) {
            nodes_[nid].parent_ = new_idx;
            nodes_[nid].cost_   = new_cost;
        }
    }
}

std::vector<Point2D> RRTStar::extractPath(int node_idx) const {
    std::vector<Point2D> path;
    int idx = node_idx;
    while (idx >= 0) {
        path.push_back({nodes_[idx].x_, nodes_[idx].y_});
        idx = nodes_[idx].parent_;
    }
    std::reverse(path.begin(), path.end());
    return path;
}

bool RRTStar::pointFree(const Point2D& p) const {
    for (const auto& obs : obstacles_) {
        double d = std::hypot(p.x - obs.cx, p.y - obs.cy);
        if (d < obs.radius + params_.obstacle_margin)
            return false;
    }
    return true;
}

bool RRTStar::segmentFree(const Point2D& a, const Point2D& b) const {
    // Sample 20 points along segment and check each
    const int steps = 20;
    for (int i = 0; i <= steps; ++i) {
        double t = static_cast<double>(i) / steps;
        Point2D p{a.x + t * (b.x - a.x), a.y + t * (b.y - a.y)};
        if (!pointFree(p)) return false;
    }
    return true;
}

// ── Quintic polynomial path smoothing ────────────────────────────────────────

std::vector<Point2D> RRTStar::smoothPath(const std::vector<Point2D>& raw,
                                          int samples_per_seg) {
    if (raw.size() < 2) return raw;

    // Compute tangent vectors at each waypoint (average of adjacent segment dirs)
    const int n = static_cast<int>(raw.size());
    std::vector<Point2D> tangents(n, {0.0, 0.0});
    for (int i = 1; i < n - 1; ++i) {
        tangents[i].x = 0.5 * (raw[i+1].x - raw[i-1].x);
        tangents[i].y = 0.5 * (raw[i+1].y - raw[i-1].y);
    }
    // Endpoint tangents: forward / backward difference
    tangents[0].x = raw[1].x - raw[0].x;
    tangents[0].y = raw[1].y - raw[0].y;
    tangents[n-1].x = raw[n-1].x - raw[n-2].x;
    tangents[n-1].y = raw[n-1].y - raw[n-2].y;

    std::vector<Point2D> smooth;
    smooth.reserve((n - 1) * samples_per_seg + 1);

    for (int i = 0; i < n - 1; ++i) {
        const Point2D& p0 = raw[i];
        const Point2D& p1 = raw[i+1];
        const Point2D& t0 = tangents[i];
        const Point2D& t1 = tangents[i+1];

        // Quintic Hermite: P(tau) coefficients for x and y
        // Boundary conditions: P(0)=p0, P(1)=p1, P'(0)=t0, P'(1)=t1, P''(0)=P''(1)=0
        // Solving the 6-coefficient system gives:
        //   a0 = p0,  a1 = t0
        //   a2 = 0  (zero second derivative at start)
        //   a3 = 10(p1-p0) - 6t0 - 4t1
        //   a4 = -15(p1-p0) + 8t0 + 7t1      (fixed from zero-accel constraint)
        //   a5 = 6(p1-p0) - 3t0 - 3t1        (simplified to match quintic behavior)
        // Note: Using simplified formulation matching the velocity profile polynomial.
        double dx = p1.x - p0.x, dy = p1.y - p0.y;
        double a3x = 10*dx - 6*t0.x - 4*t1.x;
        double a4x = -15*dx + 8*t0.x + 7*t1.x;
        double a5x = 6*dx - 3*t0.x - 3*t1.x;
        double a3y = 10*dy - 6*t0.y - 4*t1.y;
        double a4y = -15*dy + 8*t0.y + 7*t1.y;
        double a5y = 6*dy - 3*t0.y - 3*t1.y;

        int end = (i == n - 2) ? samples_per_seg : samples_per_seg - 1;
        for (int s = 0; s <= end; ++s) {
            double tau = static_cast<double>(s) / samples_per_seg;
            double tau2 = tau*tau, tau3 = tau2*tau, tau4 = tau3*tau, tau5 = tau4*tau;
            Point2D pt;
            pt.x = p0.x + t0.x*tau + a3x*tau3 + a4x*tau4 + a5x*tau5;
            pt.y = p0.y + t0.y*tau + a3y*tau3 + a4y*tau4 + a5y*tau5;
            smooth.push_back(pt);
        }
    }
    return smooth;
}

// ─────────────────────────────────────────────────────────────────────────────
// RRTStarPlannerNode – ROS wrapper
// ─────────────────────────────────────────────────────────────────────────────

RRTStarPlannerNode::RRTStarPlannerNode() : nh_("~") {
    // Load planner params
    nh_.param("step_size",       params_.step_size,       0.5);
    nh_.param("max_iterations",  params_.max_iterations,  5000);
    nh_.param("goal_radius",     params_.goal_radius,     0.3);
    nh_.param("rewire_radius",   params_.rewire_radius,   2.0);
    nh_.param("obstacle_margin", params_.obstacle_margin, 0.5);
    nh_.param("planning_timeout",params_.timeout_sec,     5.0);

    nh_.param("nominal_speed",   nominal_speed_,   1.0);
    nh_.param("lookahead_dist",  lookahead_dist_,  2.0);
    nh_.param("fixed_frame",     fixed_frame_,     std::string("odom"));
    nh_.param("planning_period", planning_period_, 2.0);
    nh_.param("following_period",following_period_,0.1);

    double gx, gy;
    nh_.param("goal_x", gx, 10.0);
    nh_.param("goal_y", gy, 0.0);
    goal_ = {gx, gy};

    current_pos_ = {0.0, 0.0};

    obs_sub_ = nh_.subscribe("/excavator/assessed_obstacles", 10,
                              &RRTStarPlannerNode::obstacleCb, this);
    odom_sub_ = nh_.subscribe("/odom", 10,
                               &RRTStarPlannerNode::odomCb, this);
    path_pub_    = nh_.advertise<nav_msgs::Path>("/planned_path", 10, true);
    cmd_vel_pub_ = nh_.advertise<geometry_msgs::Twist>("/excavator/planned_cmd_vel", 10);

    planning_timer_  = nh_.createTimer(ros::Duration(planning_period_),
                                        &RRTStarPlannerNode::planningTimerCb, this);
    following_timer_ = nh_.createTimer(ros::Duration(following_period_),
                                        &RRTStarPlannerNode::followingTimerCb, this);

    ROS_INFO("RRTStarPlannerNode initialized. Goal: (%.2f, %.2f)", gx, gy);
}

void RRTStarPlannerNode::obstacleCb(
    const excavator_msgs::ObstacleArray::ConstPtr& msg)
{
    obstacles_.clear();
    for (const auto& obs : msg->obstacles) {
        if (obs.world_x == 0.0f && obs.world_y == 0.0f && obs.world_z == 0.0f)
            continue;  // 无有效世界坐标，跳过
        CircleObs co;
        co.cx     = static_cast<double>(obs.world_x);
        co.cy     = static_cast<double>(obs.world_y);
        co.radius = 1.0;  // 固定 1m 安全圆，足够覆盖行人/车辆
        obstacles_.push_back(co);
    }
}

void RRTStarPlannerNode::planningTimerCb(const ros::TimerEvent&) {
    RRTStar planner(params_);
    planner.setObstacles(obstacles_);

    auto path = planner.plan(current_pos_, goal_);
    if (path.empty()) return;

    current_path_ = path;
    path_idx_     = 0;

    // Publish nav_msgs/Path for RViz
    nav_msgs::Path path_msg;
    path_msg.header.stamp    = ros::Time::now();
    path_msg.header.frame_id = fixed_frame_;
    path_msg.poses.reserve(path.size());
    for (const auto& pt : path) {
        geometry_msgs::PoseStamped ps;
        ps.header = path_msg.header;
        ps.pose.position.x = pt.x;
        ps.pose.position.y = pt.y;
        ps.pose.position.z = 0.0;
        ps.pose.orientation.w = 1.0;
        path_msg.poses.push_back(ps);
    }
    path_pub_.publish(path_msg);
    ROS_INFO("RRTStar: new path with %zu waypoints published",
             path_msg.poses.size());
}

void RRTStarPlannerNode::odomCb(const nav_msgs::Odometry::ConstPtr& msg) {
    current_pos_.x = msg->pose.pose.position.x;
    current_pos_.y = msg->pose.pose.position.y;
    const auto& q  = msg->pose.pose.orientation;
    double siny    = 2.0 * (q.w * q.z + q.x * q.y);
    double cosy    = 1.0 - 2.0 * (q.y * q.y + q.z * q.z);
    current_yaw_   = std::atan2(siny, cosy);
    odom_received_ = true;
}

void RRTStarPlannerNode::followingTimerCb(const ros::TimerEvent&) {
    if (!odom_received_ || current_path_.empty()) return;

    // Check goal reached first
    double d_goal = std::hypot(current_pos_.x - goal_.x, current_pos_.y - goal_.y);
    if (d_goal < params_.goal_radius) {
        ROS_INFO("RRTStar: goal reached! (dist=%.3f)", d_goal);
        current_path_.clear();
        cmd_vel_pub_.publish(geometry_msgs::Twist());  // 零速通知 FSM 停止前进
        return;
    }

    // Find look-ahead point on path
    while (path_idx_ + 1 < current_path_.size()) {
        double d = std::hypot(current_path_[path_idx_].x - current_pos_.x,
                              current_path_[path_idx_].y - current_pos_.y);
        if (d > lookahead_dist_) break;
        ++path_idx_;
    }

    const Point2D& target = current_path_[path_idx_];

    // Pure pursuit: steer toward look-ahead point
    double dx = target.x - current_pos_.x;
    double dy = target.y - current_pos_.y;
    double angle_to_target = std::atan2(dy, dx);
    double angle_error     = angle_to_target - current_yaw_;
    // Normalize to [-pi, pi]
    while (angle_error >  M_PI) angle_error -= 2.0 * M_PI;
    while (angle_error < -M_PI) angle_error += 2.0 * M_PI;

    geometry_msgs::Twist cmd;
    cmd.linear.x  = nominal_speed_;
    cmd.angular.z = std::max(-1.0, std::min(1.0, 2.0 * angle_error));
    cmd_vel_pub_.publish(cmd);
}

void RRTStarPlannerNode::spin() {
    ros::AsyncSpinner spinner(2);
    spinner.start();
    ros::waitForShutdown();
}

} // namespace excavator_planner

int main(int argc, char** argv) {
    ros::init(argc, argv, "rrt_star_planner");
    excavator_planner::RRTStarPlannerNode node;
    node.spin();
    return 0;
}
