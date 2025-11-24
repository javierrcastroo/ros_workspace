#!/usr/bin/env python3
import copy
import math
import sys

import moveit_commander
import rospy
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from tf.transformations import quaternion_from_euler


class AttackMotionExecutor:
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        self.group_name = rospy.get_param("~move_group", "manipulator")
        self.approach_offset = rospy.get_param("~approach_offset", 0.10)
        self.orientation_rpy = rospy.get_param("~orientation_rpy", [math.pi, 0.0, 0.0])
        self.execute_approach = rospy.get_param("~execute_approach", True)

        self.group = moveit_commander.MoveGroupCommander(self.group_name)
        rospy.loginfo("Using MoveIt group '%s' with reference frame '%s'", self.group_name, self.group.get_pose_reference_frame())

        self.status_pub = rospy.Publisher("~status", String, queue_size=1)
        rospy.Subscriber("~attack_target_pose", PoseStamped, self._target_cb, queue_size=1)

    def _target_cb(self, msg):
        target_pose = PoseStamped()
        target_pose.header = msg.header
        target_pose.pose = msg.pose

        quat = quaternion_from_euler(*self.orientation_rpy)
        target_pose.pose.orientation.x = quat[0]
        target_pose.pose.orientation.y = quat[1]
        target_pose.pose.orientation.z = quat[2]
        target_pose.pose.orientation.w = quat[3]

        if self.execute_approach:
            approach_pose = copy.deepcopy(target_pose)
            approach_pose.pose.position.z += self.approach_offset
            rospy.loginfo("Moving to approach pose above %s by %.3f m", msg.header.frame_id, self.approach_offset)
            if not self._execute_pose(approach_pose):
                self._publish_status("failed_approach")
                return

        rospy.loginfo(
            "Moving to attack target at (%.3f, %.3f, %.3f) in frame %s",
            target_pose.pose.position.x,
            target_pose.pose.position.y,
            target_pose.pose.position.z,
            target_pose.header.frame_id,
        )
        if self._execute_pose(target_pose):
            self._publish_status("succeeded")
        else:
            self._publish_status("failed_target")

    def _execute_pose(self, pose_stamped):
        self.group.set_pose_reference_frame(pose_stamped.header.frame_id)
        self.group.set_pose_target(pose_stamped)
        success = self.group.go(wait=True)
        self.group.stop()
        self.group.clear_pose_targets()
        if not success:
            rospy.logwarn("Motion planning/execution failed for target in frame %s", pose_stamped.header.frame_id)
        return success

    def _publish_status(self, status):
        self.status_pub.publish(String(data=status))
        rospy.loginfo("Attack motion status: %s", status)


def main():
    rospy.init_node("attack_motion_executor")
    AttackMotionExecutor()
    rospy.spin()


if __name__ == "__main__":
    main()
