#!/usr/bin/env python

"""
    Tested with: pcl = [(0.4,1,0),(0.36,0.6,0), (0.5,1,0), (0.61,0.7,0),(0.36,0.7,0),(0,0.4,0),(0.3,1.36,0)]
"""

import rospy
from sensor_msgs.msg import PointCloud2, PointField, point_cloud2 as pcl2
from wall_extractor import extract_walls
import config as cfg


def processPcl(pcl_msg, pose):
    h = pcl_msg.height
    w = pcl_msg.width

    rospy.loginfo("Dimesions of PL array: %s", (h,w))
    rospy.loginfo("Field: %s", pcl_msg.fields)

    roi = zip(range(w),[int(h/2)]*w)
    pcl = pcl2.read_points(pcl_msg, field_names=("x", "y", "z"), skip_nans=True, uvs=roi)
    pcl_global = toGlobalFrame(pcl, pose)
    new_walls = extractWalls(pcl_global)

    # new_map = cfg.MAP + [w for w in new_walls if w not in new_map] # add in navigation.py
    return new_wall


def toGlobalFrame(pcl, pose):
    pcl_global = []
    for (x,y,z) in pcl:
        X = pose[0] + x*cos(pose[2]) - y*sin(pose[2])
        Y = pose[1] + y*cos(pose[2]) + x*sin(pose[2])
        pcl_global.append((X,Y))
    return pcl_global


def extractWalls(pcl):
    candidates = []
    for (x,y,z) in pcl:
        err_norm_x = abs(x - round(x - .5) - .5) - cfg.WALL_THICKNESS/2
        err_norm_y = abs(y - round(y - .5) - .5) - cfg.WALL_THICKNESS/2
        
        # Check if could be a vertical wall
        if abs(err_norm_x) < cfg.TOL_NORMAL:
            spread_y = y - round(y)
            if abs(spread_y) < cfg.TOL_ALONG:
                x_wall = round(x - 0.5) + 0.5
                y_wall = round(y)
                candidates = addPoint(candidates, x_wall, y_wall)
    
        # Or a horizontal one
        elif abs(err_norm_y) < cfg.TOL_NORMAL:
            spread_x = x - round(x)
            if abs(spread_x) < cfg.TOL_ALONG:
                x_wall = round(x)
                y_wall = round(y - 0.5) + 0.5
                candidates = addPoint(candidates, x_wall, y_wall)

    new_walls = [(x,y) for (x,y,cnt) in candidates if (cnt >= cfg.TOL_NB_PTS)]
    return new_walls


def addPoint(candidates, x_wall, y_wall):
    already_detected = False
    for i in range(len(candidates)):
        if (x_wall, y_wall) == (candidates[i][0], candidates[i][1]):
            candidates[i][2] += 1 # increase number of corresponding points
            already_detected = True
            break
    if not already_detected:
        candidates.append([x_wall, y_wall, 1])
    return candidates


if __name__ == "__main__":
    rospy.init_node("map_updater", anonymous=True)
    rospy.Subscriber("/camera/depth/points_throttle", PointCloud2, process_pcl)
    try:
        rospy.spin()
    except rospy.ROSInterruptException:
        rospy.loginfo("Shutting down node: %s", rospy.get_name())