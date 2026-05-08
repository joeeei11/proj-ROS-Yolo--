#pragma once

#include <vector>
#include <cmath>
#include <random>
#include <chrono>
#include <string>

#include <ros/ros.h>
#include <geometry_msgs/Twist.h>
#include <nav_msgs/Path.h>
#include <excavator_msgs/ObstacleArray.h>

namespace excavator_planner {

struct Point2D {
    double x{0.0};
    double y{0.0};
};

struct CircleObs {
    double cx, cy, radius;
};

struct RRTNode {
    double x_;
    double y_;
    int    parent_;
    double cost_;
};

// ── Pure RRT* algorithm (no ROS) ─────────────────────────────────────────────

class RRTStar {
public:
    struct Params {
        double step_size{0.5};
        int    max_iterations{5000};
        double goal_radius{0.3};
        double rewire_radius{2.0};
        double obstacle_margin{0.5};
        double timeout_sec{5.0};
        double x_min{-25.0}, x_max{25.0};
        double y_min{-25.0}, y_max{25.0};
    };

    explicit RRTStar(const Params& p);
    void setObstacles(const std::vector<CircleObs>& obs);

    // Returns smoothed path; empty vector on failure/timeout.
    std::vector<Point2D> plan(const Point2D& start, const Point2D& goal);

    // Quintic polynomial interpolation between consecutive waypoints.
    static std::vector<Point2D> smoothPath(const std::vector<Point2D>& raw,
                                            int samples_per_seg = 10);

private:
    Point2D sample(const Point2D& goal);
    int     nearest(const Point2D& q) const;
    Point2D steer(const Point2D& from, const Point2D& to) const;
    bool    collisionFree(const Point2D& a, const Point2D& b) const;
    std::vector<int> nearNodes(const Point2D& q) const;
    void    rewire(int new_idx, const std::vector<int>& near_ids);
    std::vector<Point2D> extractPath(int node_idx) const;

    inline double dist(const Point2D& a, const Point2D& b) const {
        return std::hypot(a.x - b.x, a.y - b.y);
    }
    bool pointFree(const Point2D& p) const;
    bool segmentFree(const Point2D& a, const Point2D& b) const;

    Params params_;
    std::vector<RRTNode>  nodes_;
    std::vector<CircleObs> obstacles_;
    std::mt19937 rng_;
    std::uniform_real_distribution<double> uni_x_, uni_y_, uni01_;
};

// ── ROS node wrapper ──────────────────────────────────────────────────────────

class RRTStarPlannerNode {
public:
    RRTStarPlannerNode();
    void spin();

private:
    void obstacleCb(const excavator_msgs::ObstacleArray::ConstPtr& msg);
    void planningTimerCb(const ros::TimerEvent&);
    void followingTimerCb(const ros::TimerEvent&);

    ros::NodeHandle nh_;
    ros::Subscriber obs_sub_;
    ros::Publisher  path_pub_;
    ros::Publisher  cmd_vel_pub_;
    ros::Timer      planning_timer_;
    ros::Timer      following_timer_;

    RRTStar::Params params_;
    std::vector<CircleObs>   obstacles_;
    std::vector<Point2D>     current_path_;
    size_t path_idx_{0};

    // Robot pose (dead-reckoned from cmd_vel in simulation)
    Point2D current_pos_;
    double  current_yaw_{0.0};

    Point2D     goal_;
    double      nominal_speed_;
    double      lookahead_dist_;
    std::string fixed_frame_;
    double      planning_period_;
    double      following_period_;
};

} // namespace excavator_planner
