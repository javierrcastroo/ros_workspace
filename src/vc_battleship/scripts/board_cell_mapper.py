#!/usr/bin/env python3
import string
import rospy
from geometry_msgs.msg import PoseArray, PoseStamped
from std_msgs.msg import String


def parse_cell_label(label, row_labels, cols):
    cleaned = label.strip().upper()
    if not cleaned:
        raise ValueError("Empty cell label")
    row_char = cleaned[0]
    if row_char not in row_labels:
        raise ValueError("Row '%s' not in supported labels %s" % (row_char, row_labels))
    try:
        col_index = int(cleaned[1:]) - 1
    except ValueError as exc:
        raise ValueError("Invalid column number in '%s'" % cleaned) from exc
    if col_index < 0 or col_index >= cols:
        raise ValueError("Column out of range in '%s' (expected 1-%d)" % (cleaned, cols))
    row_index = row_labels.index(row_char)
    return row_index, col_index


class BoardCellMapper:
    def __init__(self):
        self.rows = rospy.get_param("~rows", 10)
        self.cols = rospy.get_param("~cols", 10)
        default_rows = string.ascii_uppercase[: self.rows]
        raw_labels = rospy.get_param("~row_labels", list(default_rows))
        if isinstance(raw_labels, str):
            raw_labels = [item.strip().upper() for item in raw_labels.split(",") if item.strip()]
        self.row_labels = raw_labels
        if len(self.row_labels) < self.rows:
            rospy.logwarn(
                "Row label count (%d) is smaller than configured rows (%d); extra rows will repeat last label.",
                len(self.row_labels),
                self.rows,
            )

        self._last_layout = None
        self._layout_header = None

        self.target_pub = rospy.Publisher("~attack_target_pose", PoseStamped, queue_size=1)
        rospy.Subscriber("~board_layout", PoseArray, self._layout_cb, queue_size=1)
        rospy.Subscriber("~attack_cell", String, self._attack_cb, queue_size=10)

        rospy.loginfo(
            "board_cell_mapper ready with %d rows x %d cols (rows=%s)",
            self.rows,
            self.cols,
            ",".join(self.row_labels),
        )

    def _layout_cb(self, msg):
        expected_cells = self.rows * self.cols
        if len(msg.poses) != expected_cells:
            rospy.logwarn(
                "Received layout with %d cells, expected %d. Ignoring until sizes match.",
                len(msg.poses),
                expected_cells,
            )
            return
        self._last_layout = msg.poses
        self._layout_header = msg.header
        rospy.loginfo("Updated board layout with frame_id '%s'", msg.header.frame_id)

    def _attack_cb(self, msg):
        if self._last_layout is None:
            rospy.logwarn("No board layout received yet; cannot resolve attack %s", msg.data)
            return
        try:
            row_idx, col_idx = parse_cell_label(msg.data, self.row_labels, self.cols)
        except ValueError as exc:
            rospy.logwarn("Could not parse attack cell '%s': %s", msg.data, exc)
            return

        index = row_idx * self.cols + col_idx
        pose = self._last_layout[index]

        target = PoseStamped()
        target.header = self._layout_header
        target.pose = pose

        self.target_pub.publish(target)
        rospy.loginfo(
            "Published attack target for cell %s at index %d (row %d, col %d) in frame %s",
            msg.data,
            index,
            row_idx,
            col_idx,
            target.header.frame_id,
        )


def main():
    rospy.init_node("board_cell_mapper")
    BoardCellMapper()
    rospy.spin()


if __name__ == "__main__":
    main()
