#!/usr/bin/env python

import rospy
import Tkinter as tki
from Tkinter import Toplevel, Scale
import threading
import os
import time
import platform
from geometry_msgs.msg import Twist, PoseStamped, Point, Pose
from std_msgs.msg import Empty, Bool, Int32, Float32
from flock_msgs.msg import Flip, FlightData
import signal
import math
from tf.transformations import euler_from_quaternion, quaternion_from_euler
PACKAGE = "orb_slam2_ros"
import roslib;roslib.load_manifest(PACKAGE)
import dynamic_reconfigure.client



class TelloUI(object):
    """Wrapper class to enable the GUI."""

    def __init__(self, root):

        rospy.init_node('tello_ui', anonymous=False)

        # rospy.Subscriber('/command_pos', Point, self.command_pos_callback)

        signal.signal(signal.SIGINT, self.onClose)
        signal.signal(signal.SIGTERM, self.onClose)

        try: 
            self.id                = rospy.get_param('~ID')
        except KeyError:
            self.id = 0
        self.publish_prefix = "tello{}/".format(self.id)


        self.point_command_pos = Point(0.0, 0.0, 1.0)
        self.point_command_pos_yaw = 0.0
        self.command_pos = Pose()
        self.rotated_pos = Point()
        self.slam_pos = Point()
        self.twist_manual_control = Twist()
        self.real_world_pos = Point()
        self.delta_pos = Point()
        self.orientation_degree = Point()

        self.allow_slam_control = False

        self.current_mux = 0
        # initialize the root window and image panel
        self.root = root

        self.panel = None
       # self.panel_for_pose_handle_show = None

        # self.client = dynamic_reconfigure.client.Client("orb_slam2_mono")
       

        # create buttons

        self.column = 0
        self.row = 0
        self.frame_column = 0
        self.frame_row = 0

        self.angle_delta_x = 0
        self.angle_delta_y = 0
        self.angle_delta_z = 0
        self.angle = 12.0
        self.angle_radian = self.angle / 180.0 * math.pi

        self.real_world_scale = 3.9636
        self.altitude = 0

        self.init_command_pos_frame_flag = False
        self.init_real_world_frame_flag = False
        self.init_slam_pose_frame_flag = False
        self.init_delta_frame_flag = False
        self.init_speed_frame_flag = False
        self.init_info_frame_flag = False
        self.init_manual_control_frame_flag = False
        self.init_angle_calc_frame_flag = False
        self.init_rotated_frame_flag = False



        self.init_command_pos_frame()

        self.init_real_world_frame()

        self.init_rotated_frame()
        # self.init_slam_pose_frame()

        self.init_delta_frame()

        self.init_speed_frame()

        self.init_info_frame()

        self.init_manual_control_frame()

        # self.init_angle_calc_frame()

        self.init_kd_kp_frame()

        self.update_command_pos_to_gui()





        self.row += 1
        self.column = 0


        # set a callback to handle when the window is closed
        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        self.kd = Pose()
        self.kp = Pose()

        rospy.Subscriber('/orb_slam2_mono/pose', PoseStamped, self.slam_callback)
        rospy.Subscriber(self.publish_prefix+'delta_pos', Point, self.delta_pos_callback)
        rospy.Subscriber(self.publish_prefix+'cmd_vel', Twist, self.speed_callback)
        rospy.Subscriber(self.publish_prefix+'flight_data', FlightData, self.flightdata_callback)
        rospy.Subscriber(self.publish_prefix+'allow_slam_control', Bool, self.allow_slam_control_callback)
        rospy.Subscriber(self.publish_prefix+'real_world_scale', Float32, self.real_world_scale_callback)
        rospy.Subscriber(self.publish_prefix+'real_world_pos', PoseStamped, self.real_world_pos_callback) 
        rospy.Subscriber(self.publish_prefix+'rotated_pos', Point, self.rotated_pos_callback)
        rospy.Subscriber(self.publish_prefix+'command_pos', Pose, self.command_pos_callback)
        rospy.Subscriber(self.publish_prefix+'orientation', Point, self.orientation_callback)

        self.command_pos_publisher = rospy.Publisher(self.publish_prefix+'command_pos', Pose, queue_size = 1)
        self.pub_takeoff = rospy.Publisher(self.publish_prefix+'takeoff', Empty, queue_size=1)
        self.pub_land = rospy.Publisher(self.publish_prefix+'land', Empty, queue_size=1)
        self.pub_allow_slam_control = rospy.Publisher(self.publish_prefix+'allow_slam_control', Bool, queue_size=1)
        self.cmd_val_publisher = rospy.Publisher(self.publish_prefix+'cmd_vel', Twist, queue_size = 1)
        self.calibrate_real_world_scale_publisher = rospy.Publisher(self.publish_prefix+'calibrate_real_world_scale', Empty, queue_size = 1)
        self.scan_room_publisher = rospy.Publisher(self.publish_prefix+'scan_room', Bool, queue_size = 1)
        self.kd_publisher = rospy.Publisher(self.publish_prefix+'kd', Pose, queue_size = 1)
        self.kp_publisher = rospy.Publisher(self.publish_prefix+'kp', Pose, queue_size = 1)
        self.kp_publisher = rospy.Publisher(self.publish_prefix+'kp', Pose, queue_size = 1)
        self.pub_mux =  rospy.Publisher('tello_mux', Int32, queue_size = 1)
        

        self.publish_command()




    def nothing(self):
        rospy.loginfo("nothing")
        return


    def init_command_pos_frame(self):
        self.init_command_pos_frame_flag = True
        self.frame_command = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_command.grid(row=self.row, column=self.column)

        self.title_label_command_pos = tki.Label(self.frame_command, text="Command Position[Meters]", font=("Helvetica", 13))
        self.title_label_command_pos.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.command_label_x = tki.Label(self.frame_command, text="X[m]")
        self.command_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.command_label_y = tki.Label(self.frame_command, text="Y[m]")
        self.command_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.command_label_z = tki.Label(self.frame_command, text="Z[m]")
        self.command_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.command_label_yaw = tki.Label(self.frame_command, text="Yaw[Degree]")
        self.command_label_yaw.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.command_strigvar_x = tki.StringVar()
        self.command_entry_x = tki.Entry(self.frame_command, width=15, textvariable=self.command_strigvar_x)
        self.command_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.command_entry_x.delete(0, tki.END)
        self.command_entry_x.insert(0, "0.0")

        self.frame_column += 1

        self.command_strigvar_y = tki.StringVar()
        self.command_entry_y = tki.Entry(self.frame_command, width=15, textvariable=self.command_strigvar_y)
        self.command_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.command_entry_y.delete(0, tki.END)
        self.command_entry_y.insert(0, "0.0")

        self.frame_column += 1

        self.command_strigvar_z = tki.StringVar()
        self.command_entry_z = tki.Entry(self.frame_command, width=15, textvariable=self.command_strigvar_z)
        self.command_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.command_entry_z.delete(0, tki.END)
        self.command_entry_z.insert(0, "1.0")

        self.frame_column += 1

        self.command_strigvar_yaw = tki.StringVar()
        self.command_entry_yaw = tki.Entry(self.frame_command, width=15, textvariable=self.command_strigvar_yaw)
        self.command_entry_yaw.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.command_entry_yaw.delete(0, tki.END)
        self.command_entry_yaw.insert(0, "0.0")

        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.btn_takeoff = tki.Button(self.frame_command, text="Takeoff!", command=self.takeoff)
        self.btn_takeoff.grid(row=self.frame_row, column=0, padx=10, pady=5)

        self.btn_publish_command = tki.Button(self.frame_command, text="Publish Command!", command=self.publish_command)
        self.btn_publish_command.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.btn_land = tki.Button(self.frame_command, text="Land!", command=self.land)
        self.btn_land.grid(row=self.frame_row, column=2, padx=10, pady=5)

        self.btn_land = tki.Button(self.frame_command, text="Reset Map!", command=self.reset_map_callback)
        self.btn_land.grid(row=self.frame_row, column=3, padx=10, pady=5)

        self.frame_row += 1

        self.btn_scan_room = tki.Button(self.frame_command, text="Scan Room Right!", command=self.scan_room_right_callback)
        self.btn_scan_room.grid(row=self.frame_row, column=0, padx=10, pady=5)

        self.btn_scan_room = tki.Button(self.frame_command, text="Scan Room Left!", command=self.scan_room_left_callback)
        self.btn_scan_room.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.btn_stay_in_place = tki.Button(self.frame_command, text="Stay In Place!", command=self.stay_in_place)
        self.btn_stay_in_place.grid(row=self.frame_row, column=2, padx=10, pady=5)

        self.btn_calibrate_z = tki.Button(self.frame_command, text="Calibrate Z!", command=self.calibrate_z_callback)
        self.btn_calibrate_z.grid(row=self.frame_row, column=3, padx=10, pady=5)

        self.row += 1
        self.column = 0

    def init_slam_pose_frame(self):
        self.init_slam_pose_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_pose = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_pose.grid(row=self.row, column=self.column)

        self.title_label_pose = tki.Label(self.frame_pose, text="Slam Pose", font=("Helvetica", 13))
        self.title_label_pose.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.slam_pose_label_x = tki.Label(self.frame_pose, text="X")
        self.slam_pose_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.slam_pose_label_y = tki.Label(self.frame_pose, text="Y")
        self.slam_pose_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.slam_pose_label_z = tki.Label(self.frame_pose, text="Z")
        self.slam_pose_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.slam_pose_strigvar_x = tki.StringVar()
        self.slam_pose_entry_x = tki.Entry(self.frame_pose, width=15, textvariable=self.slam_pose_strigvar_x)
        self.slam_pose_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.slam_pose_entry_x.delete(0, tki.END)
        self.slam_pose_entry_x.insert(0, "0.0")

        self.frame_column += 1

        self.slam_pose_strigvar_y = tki.StringVar()
        self.slam_pose_entry_y = tki.Entry(self.frame_pose, width=15, textvariable=self.slam_pose_strigvar_y)
        self.slam_pose_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.slam_pose_entry_y.delete(0, tki.END)
        self.slam_pose_entry_y.insert(0, "0.0")

        self.frame_column += 1

        self.slam_pose_strigvar_z = tki.StringVar()
        self.slam_pose_entry_z = tki.Entry(self.frame_pose, width=15, textvariable=self.slam_pose_strigvar_z)
        self.slam_pose_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.slam_pose_entry_z.delete(0, tki.END)
        self.slam_pose_entry_z.insert(0, "0.0")


        self.frame_column += 1
        self.row += 1
        self.column = 0

    def init_delta_frame(self):
        self.init_delta_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_delta = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_delta.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_delta

        self.title_label_dela = tki.Label(self.current_frame, text="Delta Between Command and Real World [Meters]", font=("Helvetica", 13))
        self.title_label_dela.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.delta_label_x = tki.Label(self.current_frame, text="X")
        self.delta_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.delta_label_y = tki.Label(self.current_frame, text="Y")
        self.delta_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.delta_label_z = tki.Label(self.current_frame, text="Z")
        self.delta_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.delta_strigvar_x = tki.StringVar()
        self.delta_entry_x = tki.Entry(self.current_frame, width=15, textvariable=self.delta_strigvar_x)
        self.delta_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.delta_entry_x.delete(0, tki.END)
        self.delta_entry_x.insert(0, "0.0")

        self.frame_column += 1

        self.delta_strigvar_y = tki.StringVar()
        self.delta_entry_y = tki.Entry(self.current_frame, width=15, textvariable=self.delta_strigvar_y)
        self.delta_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.delta_entry_y.delete(0, tki.END)
        self.delta_entry_y.insert(0, "0.0")

        self.frame_column += 1

        self.delta_strigvar_z = tki.StringVar()
        self.delta_entry_z = tki.Entry(self.current_frame, width=15, textvariable=self.delta_strigvar_z)
        self.delta_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.delta_entry_z.delete(0, tki.END)
        self.delta_entry_z.insert(0, "0.0")

        self.frame_column += 1
        self.row += 1
        self.column = 0
    
    def init_speed_frame(self):
        self.init_speed_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_speed = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_speed.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_speed

        self.title_label_speed = tki.Label(self.current_frame, text="Speed", font=("Helvetica", 13))
        self.title_label_speed.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.speed_label_pitch = tki.Label(self.current_frame, text="Pitch")
        self.speed_label_pitch.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.speed_label_roll = tki.Label(self.current_frame, text="Roll")
        self.speed_label_roll.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.speed_label_throttle = tki.Label(self.current_frame, text="Throttle")
        self.speed_label_throttle.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.speed_label_yaw = tki.Label(self.current_frame, text="Yaw")
        self.speed_label_yaw.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1


        self.frame_row += 1
        self.frame_column = 0

        self.speed_strigvar_pitch = tki.StringVar()
        self.speed_entry_pitch = tki.Entry(self.current_frame, width=15, textvariable=self.speed_strigvar_pitch)
        self.speed_entry_pitch.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.speed_entry_pitch.delete(0, tki.END)
        self.speed_entry_pitch.insert(0, "0.0")

        self.frame_column += 1

        self.speed_strigvar_roll = tki.StringVar()
        self.speed_entry_roll = tki.Entry(self.current_frame, width=15, textvariable=self.speed_strigvar_roll)
        self.speed_entry_roll.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.speed_entry_roll.delete(0, tki.END)
        self.speed_entry_roll.insert(0, "0.0")

        self.frame_column += 1

        self.speed_strigvar_throttle = tki.StringVar()
        self.speed_entry_throttle = tki.Entry(self.current_frame, width=15, textvariable=self.speed_strigvar_throttle)
        self.speed_entry_throttle.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.speed_entry_throttle.delete(0, tki.END)
        self.speed_entry_throttle.insert(0, "0.0")

        self.frame_column += 1

        self.speed_strigvar_yaw = tki.StringVar()
        self.speed_entry_yaw = tki.Entry(self.current_frame, width=15, textvariable=self.speed_strigvar_yaw)
        self.speed_entry_yaw.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.speed_entry_yaw.delete(0, tki.END)
        self.speed_entry_yaw.insert(0, "0.0")

        self.row += 1
        self.column = 0

    def init_info_frame(self):
        self.init_info_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_etc = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_etc.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_etc


        self.altitude_label = tki.Label(self.current_frame, text="Altitude")
        self.altitude_label.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1

        self.battery_label = tki.Label(self.current_frame, text="Battery %")
        self.battery_label.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1

        self.flight_time_remaining_label = tki.Label(self.current_frame, text="flight time remaining")
        self.flight_time_remaining_label.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1

        self.allow_slam_control_btn = tki.Button(self.current_frame, text="Toggle Slam Control!",  command=self.allow_slam_control_btn_callback)
        self.allow_slam_control_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)


        self.frame_row += 1
        self.frame_column = 0

        self.altitude_strigvar = tki.StringVar()
        self.altitude_entry = tki.Entry(self.current_frame, width=15, textvariable=self.altitude_strigvar)
        self.altitude_entry.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.altitude_entry.delete(0, tki.END)
        self.altitude_entry.insert(0, "0.0")

        self.frame_column += 1

        self.battery_strigvar = tki.StringVar()
        self.battery_entry = tki.Entry(self.current_frame, width=15, textvariable=self.battery_strigvar)
        self.battery_entry.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.battery_entry.delete(0, tki.END)
        self.battery_entry.insert(0, "0.0")

        self.frame_column += 1

        self.flight_time_remaining_strigvar = tki.StringVar()
        self.flight_time_remaining_entry = tki.Entry(self.current_frame, width=15, textvariable=self.flight_time_remaining_strigvar)
        self.flight_time_remaining_entry.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.flight_time_remaining_entry.delete(0, tki.END)
        self.flight_time_remaining_entry.insert(0, "0.0")

        self.frame_column += 1

        self.allow_slam_control_strigvar = tki.StringVar()
        self.allow_slam_control_entry = tki.Entry(self.current_frame, width=15, textvariable=self.allow_slam_control_strigvar)
        self.allow_slam_control_entry.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.allow_slam_control_entry.delete(0, tki.END)
        self.allow_slam_control_entry.insert(0, "{}".format(self.allow_slam_control))

        self.row += 1
        self.column = 0

    def init_manual_control_frame(self):
        self.init_manual_control_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_manual_control = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_manual_control.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_manual_control

        self.title_label_manual_control = tki.Label(self.current_frame, text="Manual Control", font=("Helvetica", 13))
        self.title_label_manual_control.grid(row=self.frame_row, column=2, padx=10, pady=5)

        self.frame_row += 1

        self.manual_control_label_pitch = tki.Label(self.current_frame, text="Pitch")
        self.manual_control_label_pitch.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.manual_control_label_roll = tki.Label(self.current_frame, text="Roll")
        self.manual_control_label_roll.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.manual_control_label_throttle = tki.Label(self.current_frame, text="Throttle")
        self.manual_control_label_throttle.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.manual_control_label_yaw = tki.Label(self.current_frame, text="Yaw")
        self.manual_control_label_yaw.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.manual_control_set_btn = tki.Button(self.current_frame, text="Manual Control Set!",  command=self.manual_control_set_callback)
        self.manual_control_set_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1


        self.frame_row += 1
        self.frame_column = 0

        self.manual_control_strigvar_pitch = tki.StringVar()
        self.manual_control_entry_pitch = tki.Entry(self.current_frame, width=15, textvariable=self.manual_control_strigvar_pitch)
        self.manual_control_entry_pitch.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.manual_control_entry_pitch.delete(0, tki.END)
        self.manual_control_entry_pitch.insert(0, "0.0")

        self.frame_column += 1

        self.manual_control_strigvar_roll = tki.StringVar()
        self.manual_control_entry_roll = tki.Entry(self.current_frame, width=15, textvariable=self.manual_control_strigvar_roll)
        self.manual_control_entry_roll.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.manual_control_entry_roll.delete(0, tki.END)
        self.manual_control_entry_roll.insert(0, "0.0")

        self.frame_column += 1

        self.manual_control_strigvar_throttle = tki.StringVar()
        self.manual_control_entry_throttle = tki.Entry(self.current_frame, width=15, textvariable=self.manual_control_strigvar_throttle)
        self.manual_control_entry_throttle.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.manual_control_entry_throttle.delete(0, tki.END)
        self.manual_control_entry_throttle.insert(0, "0.0")

        self.frame_column += 1

        self.manual_control_strigvar_yaw = tki.StringVar()
        self.manual_control_entry_yaw = tki.Entry(self.current_frame, width=15, textvariable=self.manual_control_strigvar_yaw)
        self.manual_control_entry_yaw.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.manual_control_entry_yaw.delete(0, tki.END)
        self.manual_control_entry_yaw.insert(0, "0.0")

        self.frame_column += 1

        self.manual_control_clear_btn = tki.Button(self.current_frame, text="Manual Control Clear!",  command=self.manual_control_clear_callback)
        self.manual_control_clear_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1

        self.row += 1
        self.column = 0

    def init_angle_calc_frame(self):
        self.init_angle_calc_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_angle_calc = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_angle_calc.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_angle_calc

        self.title_label_angle_calc = tki.Label(self.current_frame, text="Angel Calc", font=("Helvetica", 13))
        self.title_label_angle_calc.grid(row=self.frame_row, column=2, padx=10, pady=5)

        self.frame_row += 1

        self.angle_calc_label_x_moved = tki.Label(self.current_frame, text="X Moved")
        self.angle_calc_label_x_moved.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.angle_calc_label_y_moved = tki.Label(self.current_frame, text="Y Moved")
        self.angle_calc_label_y_moved.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.angle_calc_label_z_moved = tki.Label(self.current_frame, text="Z Moved")
        self.angle_calc_label_z_moved.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.angle_calc_label_angle = tki.Label(self.current_frame, text="Angle")
        self.angle_calc_label_angle.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.angle_calc_set_btn = tki.Button(self.current_frame, text="Calculate Angle!",  command=self.angle_calc_set_callback)
        self.angle_calc_set_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1


        self.frame_row += 1
        self.frame_column = 0

        self.angle_calc_strigvar_x_moved = tki.StringVar()
        self.angle_calc_entry_x_moved = tki.Entry(self.current_frame, width=15, textvariable=self.angle_calc_strigvar_x_moved)
        self.angle_calc_entry_x_moved.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.angle_calc_entry_x_moved.delete(0, tki.END)
        self.angle_calc_entry_x_moved.insert(0, "0.0")

        self.frame_column += 1

        self.angle_calc_strigvar_y_moved = tki.StringVar()
        self.angle_calc_entry_y_moved = tki.Entry(self.current_frame, width=15, textvariable=self.angle_calc_strigvar_y_moved)
        self.angle_calc_entry_y_moved.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.angle_calc_entry_y_moved.delete(0, tki.END)
        self.angle_calc_entry_y_moved.insert(0, "0.0")

        self.frame_column += 1

        self.angle_calc_strigvar_z_moved = tki.StringVar()
        self.angle_calc_entry_z_moved = tki.Entry(self.current_frame, width=15, textvariable=self.angle_calc_strigvar_z_moved)
        self.angle_calc_entry_z_moved.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.angle_calc_entry_z_moved.delete(0, tki.END)
        self.angle_calc_entry_z_moved.insert(0, "0.0")

        self.frame_column += 1

        self.angle_calc_strigvar_angle = tki.StringVar()
        self.angle_calc_entry_angle = tki.Entry(self.current_frame, width=15, textvariable=self.angle_calc_strigvar_angle)
        self.angle_calc_entry_angle.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.angle_calc_entry_angle.delete(0, tki.END)
        self.angle_calc_entry_angle.insert(0, "0.0")
        self.angle_calc_strigvar_angle.set('%.4f'%(self.angle))  

        self.frame_column += 1

        self.angle_calc_clear_btn = tki.Button(self.current_frame, text="Clear Angle!",  command=self.angle_calc_clear_callback)
        self.angle_calc_clear_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)

        self.frame_column += 1

        self.row += 1
        self.column = 0
    
    def init_rotated_frame(self):
        self.init_rotated_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_rotated = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_rotated.grid(row=self.row, column=self.column)

        self.title_label_rotated = tki.Label(self.frame_rotated, text="Rotated SLAM Coordinates", font=("Helvetica", 13))
        self.title_label_rotated.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.rotated_label_x = tki.Label(self.frame_rotated, text="X")
        self.rotated_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.rotated_label_y = tki.Label(self.frame_rotated, text="Y")
        self.rotated_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.rotated_label_z = tki.Label(self.frame_rotated, text="Z")
        self.rotated_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.rotated_label_orientation = tki.Label(self.frame_rotated, text="Orientation")
        self.rotated_label_orientation.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.rotated_strigvar_x = tki.StringVar()
        self.rotated_entry_x = tki.Entry(self.frame_rotated, width=15, textvariable=self.rotated_strigvar_x)
        self.rotated_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.rotated_entry_x.delete(0, tki.END)
        self.rotated_entry_x.insert(0, "0.0")

        self.frame_column += 1

        self.rotated_strigvar_y = tki.StringVar()
        self.rotated_entry_y = tki.Entry(self.frame_rotated, width=15, textvariable=self.rotated_strigvar_y)
        self.rotated_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.rotated_entry_y.delete(0, tki.END)
        self.rotated_entry_y.insert(0, "0.0")

        self.frame_column += 1

        self.rotated_strigvar_z = tki.StringVar()
        self.rotated_entry_z = tki.Entry(self.frame_rotated, width=15, textvariable=self.rotated_strigvar_z)
        self.rotated_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.rotated_entry_z.delete(0, tki.END)
        self.rotated_entry_z.insert(0, "0.0")

        self.frame_column += 1

        self.rotated_strigvar_orientation = tki.StringVar()
        self.rotated_entry_orientation = tki.Entry(self.frame_rotated, width=15, textvariable=self.rotated_strigvar_orientation)
        self.rotated_entry_orientation.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.rotated_entry_orientation.delete(0, tki.END)
        self.rotated_entry_orientation.insert(0, "0.0")

        self.frame_column += 1

        self.row += 1
        self.column = 0

    def init_real_world_frame(self):
        self.init_real_world_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_real_world = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_real_world.grid(row=self.row, column=self.column)

        self.title_label_real_world = tki.Label(self.frame_real_world, text="Real World Position[Meters]", font=("Helvetica", 13))
        self.title_label_real_world.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.btn_change_mux_toggle = tki.Button(self.frame_real_world, text="Change Mux!", command=self.change_mux)
        self.btn_change_mux_toggle.grid(row=self.frame_row, column=3, padx=10, pady=5)

        self.frame_row += 1

        self.real_world_label_x = tki.Label(self.frame_real_world, text="X")
        self.real_world_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.real_world_label_y = tki.Label(self.frame_real_world, text="Y")
        self.real_world_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.real_world_label_z = tki.Label(self.frame_real_world, text="Z")
        self.real_world_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.real_world_label_scale = tki.Label(self.frame_real_world, text="Altitude Scale")
        self.real_world_label_scale.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.frame_row += 1
        self.frame_column = 0

        self.real_world_strigvar_x = tki.StringVar()
        self.real_world_entry_x = tki.Entry(self.frame_real_world, width=15, textvariable=self.real_world_strigvar_x)
        self.real_world_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.real_world_entry_x.delete(0, tki.END)
        self.real_world_entry_x.insert(0, "0.0")

        self.frame_column += 1

        self.real_world_strigvar_y = tki.StringVar()
        self.real_world_entry_y = tki.Entry(self.frame_real_world, width=15, textvariable=self.real_world_strigvar_y)
        self.real_world_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.real_world_entry_y.delete(0, tki.END)
        self.real_world_entry_y.insert(0, "0.0")

        self.frame_column += 1

        self.real_world_strigvar_z = tki.StringVar()
        self.real_world_entry_z = tki.Entry(self.frame_real_world, width=15, textvariable=self.real_world_strigvar_z)
        self.real_world_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.real_world_entry_z.delete(0, tki.END)
        self.real_world_entry_z.insert(0, "0.0")

        self.frame_column += 1

        self.real_world_strigvar_scale = tki.StringVar()
        self.real_world_entry_scale = tki.Entry(self.frame_real_world, width=15, textvariable=self.real_world_strigvar_scale)
        self.real_world_entry_scale.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.real_world_entry_scale.delete(0, tki.END)
        self.real_world_entry_scale.insert(0, "0.0")

        self.frame_column += 1

        self.row += 1
        self.column = 0
    
    def init_kd_kp_frame(self):
        self.init_kd_kp_frame_flag = True
        self.frame_column = 0
        self.frame_row = 0

        self.frame_kd_kp = tki.Frame(self.root, relief=tki.SUNKEN)
        self.frame_kd_kp.grid(row=self.row, column=self.column)

        self.current_frame = self.frame_kd_kp


        self.title_label_kd = tki.Label(self.current_frame, text="Kd", font=("Helvetica", 13))
        self.title_label_kd.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.kp_kd_btn = tki.Button(self.current_frame, text="Publish Kd/Kp!",  command=self.kd_kp_callback)
        self.kp_kd_btn.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)


        self.frame_row += 1

        self.kd_label_x = tki.Label(self.current_frame, text="X")
        self.kd_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kd_label_y = tki.Label(self.current_frame, text="Y")
        self.kd_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kd_label_z = tki.Label(self.current_frame, text="Z")
        self.kd_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kd_label_yaw = tki.Label(self.current_frame, text="Yaw")
        self.kd_label_yaw.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1


        self.frame_row += 1
        self.frame_column = 0

        self.kd_strigvar_x = tki.StringVar()
        self.kd_entry_x = tki.Entry(self.current_frame, width=15, textvariable=self.kd_strigvar_x)
        self.kd_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kd_entry_x.delete(0, tki.END)
        self.kd_entry_x.insert(0, "1.0")

        self.frame_column += 1

        self.kd_strigvar_y = tki.StringVar()
        self.kd_entry_y = tki.Entry(self.current_frame, width=15, textvariable=self.kd_strigvar_y)
        self.kd_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kd_entry_y.delete(0, tki.END)
        self.kd_entry_y.insert(0, "1.0")

        self.frame_column += 1

        self.kd_strigvar_z = tki.StringVar()
        self.kd_entry_z = tki.Entry(self.current_frame, width=15, textvariable=self.kd_strigvar_z)
        self.kd_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kd_entry_z.delete(0, tki.END)
        self.kd_entry_z.insert(0, "1.5")

        self.frame_column += 1

        self.kd_strigvar_yaw = tki.StringVar()
        self.kd_entry_yaw = tki.Entry(self.current_frame, width=15, textvariable=self.kd_strigvar_yaw)
        self.kd_entry_yaw.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kd_entry_yaw.delete(0, tki.END)
        self.kd_entry_yaw.insert(0, "0.001")

        self.frame_column = 0
        self.frame_row += 1

        self.title_label_kp = tki.Label(self.current_frame, text="Kp", font=("Helvetica", 13))
        self.title_label_kp.grid(row=self.frame_row, column=1, padx=10, pady=5)

        self.frame_row += 1

        self.kp_label_x = tki.Label(self.current_frame, text="X")
        self.kp_label_x.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kp_label_y = tki.Label(self.current_frame, text="Y")
        self.kp_label_y.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kp_label_z = tki.Label(self.current_frame, text="Z")
        self.kp_label_z.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1

        self.kp_label_yaw = tki.Label(self.current_frame, text="Yaw")
        self.kp_label_yaw.grid(row=self.frame_row, column=self.frame_column, padx=10, pady=5)
        self.frame_column += 1


        self.frame_row += 1
        self.frame_column = 0

        self.kp_strigvar_x = tki.StringVar()
        self.kp_entry_x = tki.Entry(self.current_frame, width=15, textvariable=self.kp_strigvar_x)
        self.kp_entry_x.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kp_entry_x.delete(0, tki.END)
        self.kp_entry_x.insert(0, "0.6")

        self.frame_column += 1

        self.kp_strigvar_y = tki.StringVar()
        self.kp_entry_y = tki.Entry(self.current_frame, width=15, textvariable=self.kp_strigvar_y)
        self.kp_entry_y.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kp_entry_y.delete(0, tki.END)
        self.kp_entry_y.insert(0, "0.6")

        self.frame_column += 1

        self.kp_strigvar_z = tki.StringVar()
        self.kp_entry_z = tki.Entry(self.current_frame, width=15, textvariable=self.kp_strigvar_z)
        self.kp_entry_z.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kp_entry_z.delete(0, tki.END)
        self.kp_entry_z.insert(0, "1.5")

        self.frame_column += 1

        self.kp_strigvar_yaw = tki.StringVar()
        self.kp_entry_yaw = tki.Entry(self.current_frame, width=15, textvariable=self.kp_strigvar_yaw)
        self.kp_entry_yaw.grid(row=self.frame_row, column=self.frame_column, padx=5, pady=5)
        self.kp_entry_yaw.delete(0, tki.END)
        self.kp_entry_yaw.insert(0, "0.03")

        self.row += 1
        self.column = 0

    

    def calibrate_z_callback(self):
        self.calibrate_real_world_scale_publisher.publish()

    def scan_room_left_callback(self):
        rospy.loginfo('pressed Scan Room Left!')
        self.scan_room_publisher.publish(True)

    def scan_room_right_callback(self):
        rospy.loginfo('pressed Scan Room Right!')
        self.scan_room_publisher.publish(False)

    def allow_slam_control_btn_callback(self):
        self.pub_allow_slam_control.publish(not self.allow_slam_control)

    def real_world_scale_callback(self, msg):
        self.real_world_scale = float(msg.data)
        if self.init_real_world_frame_flag:
            self.real_world_strigvar_scale.set('%.4f'%(self.real_world_scale)) 

    def real_world_pos_callback(self, msg):
        self.real_world_pos = msg.pose.position
        if self.init_real_world_frame_flag:
            self.real_world_strigvar_x.set('%.4f'%(self.real_world_pos.x))
            self.real_world_strigvar_y.set('%.4f'%(self.real_world_pos.y))
            self.real_world_strigvar_z.set('%.4f'%(self.real_world_pos.z))

    def flightdata_callback(self, flight_data):
        self.altitude = flight_data.altitude
        if self.init_info_frame_flag:
            self.altitude_strigvar.set('%.4f'%(self.altitude))
            self.battery_strigvar.set('%.2f'%(flight_data.battery_percent))
            self.flight_time_remaining_strigvar.set('%.2f'%(flight_data.estimated_flight_time_remaining))
        # try:
            # if self.altitude > 0.2:
                # self.real_world_scale = self.altitude / self.rotated_pos.z
        # except ZeroDivisionError:
            # self.real_world_scale = 1
        # self.real_world_strigvar_scale.set('%.4f'%(self.real_world_scale))  

    def allow_slam_control_callback(self, msg):
        self.allow_slam_control = (msg.data == 1)
        if self.init_speed_frame_flag:
            self.allow_slam_control_strigvar.set(self.allow_slam_control)

    def angle_calc_clear_callback(self):
        self.angle_delta_x = float(self.slam_pose_strigvar_x.get())
        self.angle_delta_y = float(self.slam_pose_strigvar_y.get())
        self.angle_delta_z = float(self.slam_pose_strigvar_z.get())


    def kd_kp_callback(self):
        self.kd.position.x = float(self.kd_strigvar_x.get())
        self.kd.position.y = float(self.kd_strigvar_y.get())
        self.kd.position.z = float(self.kd_strigvar_z.get())
        self.kd.orientation.z = float(self.kd_strigvar_yaw.get())

        self.kp.position.x = float(self.kp_strigvar_x.get())
        self.kp.position.y = float(self.kp_strigvar_y.get())
        self.kp.position.z = float(self.kp_strigvar_z.get())
        self.kp.orientation.z = float(self.kp_strigvar_yaw.get())

        self.kd_publisher.publish(self.kd)
        self.kp_publisher.publish(self.kp)



    def angle_calc_set_callback(self):
        x = float(self.angle_calc_strigvar_x_moved.get())
        z = float(self.angle_calc_strigvar_z_moved.get())
        tan_angle = z/x
        self.angle_radian = math.atan(tan_angle)
        self.angle = self.angle_radian*180/math.pi
        self.angle_calc_strigvar_angle.set('%.4f'%(self.angle))  
        print("x={} z={} z/x={} angle={}".format(x, z, tan_angle, self.angle))

    def orientation_callback(self, orientation_point):
        self.orientation_degree = orientation_point
        if self.init_rotated_frame_flag:
            self.rotated_strigvar_orientation.set('%.4f'%(self.orientation_degree.z))

    def delta_pos_callback(self, delta_pos):
        self.delta_pos = delta_pos
        if self.init_delta_frame_flag:
            self.delta_strigvar_x.set('%.4f'%(self.delta_pos.x))
            self.delta_strigvar_y.set('%.4f'%(self.delta_pos.y))
            self.delta_strigvar_z.set('%.4f'%(self.delta_pos.z))

    def rotated_pos_callback(self, rotated_pos):
        self.rotated_pos = rotated_pos
        if self.init_rotated_frame_flag:
            self.rotated_strigvar_x.set('%.4f'%(self.rotated_pos.x))
            self.rotated_strigvar_y.set('%.4f'%(self.rotated_pos.y))
            self.rotated_strigvar_z.set('%.4f'%(self.rotated_pos.z))

    def point_copy(self, p):
        return Point(p.x, p.y, p.z)

    def quatenrion_point_to_euler_degree(self, slam_quaternion):
        rad = self.quatenrion_point_to_euler(slam_quaternion)
        return Point(self.rad_to_deg(rad.x), self.rad_to_deg(rad.y), self.rad_to_deg(rad.z))

    def quatenrion_point_to_euler(self, orientation_point):
        return self.quaternion_to_orientation(orientation_point.x, orientation_point.y, orientation_point.z, orientation_point.w)

    def euler_point_deg_to_rad(self, point_deg):
        return Point(self.deg_to_rad(point_deg.x), self.deg_to_rad(point_deg.y), self.deg_to_rad(point_deg.z))


    def euler_point_deg_to_quatenrion(self, euler_point_deg):
        return self.euler_point_to_quatenrion(self.euler_point_deg_to_rad(euler_point_deg))

    def euler_point_to_quatenrion(self, euler_point):
        return self.orientation_to_quaternion(euler_point.x, euler_point.y, euler_point.z)

    def quaternion_to_orientation(self, x, y, z, w):
        euler_list = euler_from_quaternion([x, y, z, w])
        euler = Point()
        euler.x = euler_list[0]
        euler.y = euler_list[1]
        euler.z = euler_list[2]
        return euler

    def orientation_to_quaternion(self, pitch, roll, yaw):
        quaternion_list = quaternion_from_euler(pitch, roll, yaw)
        quaternion = Quaternion()
        quaternion.x = quaternion_list[0]
        quaternion.y = quaternion_list[1]
        quaternion.z = quaternion_list[2]
        quaternion.w = quaternion_list[3]
        # rospy.loginfo("quaternion={}".format(quaternion))
        return quaternion

    def command_pos_callback(self, command_pos):
        self.point_command_pos = self.point_copy(command_pos.position)
        orientation_deg = self.quatenrion_point_to_euler_degree(command_pos.orientation)
        self.point_command_pos_yaw =  orientation_deg.z
        # rospy.loginfo("self.point_command_pos_yaw = {} {} {}".format(self.point_command_pos_yaw, command_pos.orientation, orientation_deg))
        self.update_command_pos_to_gui()  

    def slam_callback(self, slam_msg):
        self.slam_pos = slam_msg.pose.position
        if self.init_slam_pose_frame_flag:
            self.slam_pose_strigvar_x.set('%.4f'%(self.slam_pos.x))
            self.slam_pose_strigvar_y.set('%.4f'%(self.slam_pos.y))
            self.slam_pose_strigvar_z.set('%.4f'%(self.slam_pos.z))    

        if self.init_angle_calc_frame_flag:
            self.angle_calc_strigvar_x_moved.set('%.4f'%(self.slam_pos.x - self.angle_delta_x))
            self.angle_calc_strigvar_y_moved.set('%.4f'%(self.slam_pos.y - self.angle_delta_y))
            self.angle_calc_strigvar_z_moved.set('%.4f'%(self.slam_pos.z - self.angle_delta_z))  

    def update_command_pos_from_gui(self):
        if self.init_command_pos_frame_flag:
            self.point_command_pos.x = float(self.command_strigvar_x.get())
            self.point_command_pos.y = float(self.command_strigvar_y.get())
            self.point_command_pos.z = float(self.command_strigvar_z.get())
            self.point_command_pos_yaw = float(self.command_strigvar_yaw.get())
        self.command_pos.position = self.point_command_pos
        yaw_rad = self.deg_to_rad(self.point_command_pos_yaw)
        orientation = quaternion_from_euler(0, 0, yaw_rad)
        self.command_pos.orientation.x = orientation[0]
        self.command_pos.orientation.y = orientation[1]
        self.command_pos.orientation.z = orientation[2]
        self.command_pos.orientation.w = orientation[3]


    def rad_to_deg(self, rad):
        return rad / math.pi * 180.0

    def deg_to_rad(self, deg):
        return deg * math.pi / 180.0

    def update_command_pos_to_gui(self):
        if self.init_command_pos_frame_flag:
            self.command_strigvar_x.set('%.4f'%(self.point_command_pos.x))
            self.command_strigvar_y.set('%.4f'%(self.point_command_pos.y))
            self.command_strigvar_z.set('%.4f'%(self.point_command_pos.z))
            self.command_strigvar_yaw.set('%.4f'%(self.point_command_pos_yaw))

    def publish_command(self):
        self.update_command_pos_from_gui()
        self.command_pos_publisher.publish(self.command_pos)
        time.sleep(0.2)
        self.command_pos_publisher.publish(self.command_pos)
        time.sleep(0.2)
        self.command_pos_publisher.publish(self.command_pos)

    def stay_in_place(self):
        self.point_command_pos.x = self.real_world_pos.x
        self.point_command_pos.y = self.real_world_pos.y
        self.point_command_pos.z = self.real_world_pos.z
        self.point_command_pos_yaw = self.orientation_degree.z
        self.update_command_pos_to_gui()
        self.publish_command()

    def speed_callback(self, twist_msg):
        if self.init_speed_frame_flag:
            self.speed_strigvar_pitch.set('%.4f'%(twist_msg.linear.x))
            self.speed_strigvar_roll.set('%.4f'%(-twist_msg.linear.y))
            self.speed_strigvar_throttle.set('%.4f'%(twist_msg.linear.z))
            self.speed_strigvar_yaw.set('%.4f'%(-twist_msg.angular.z))

    def manual_control_set_callback(self):
        try:
            self.twist_manual_control.linear.x = float(self.manual_control_strigvar_pitch.get())
            self.twist_manual_control.linear.y = -float(self.manual_control_strigvar_roll.get())
            self.twist_manual_control.linear.z = float(self.manual_control_strigvar_throttle.get())
            self.twist_manual_control.angular.z = -float(self.manual_control_strigvar_yaw.get())
        except ValueError:
            self.twist_manual_control = Twist()
        self.cmd_val_publisher.publish(self.twist_manual_control)

    def manual_control_clear_callback(self):
        self.twist_manual_control.linear.x = 0
        self.twist_manual_control.linear.y = 0
        self.twist_manual_control.linear.z = 0
        self.twist_manual_control.angular.z = 0
        self.cmd_val_publisher.publish(self.twist_manual_control)

    def reset_map_callback(self):
        self.client.update_configuration({"reset_map": True})


    def takeoff(self):
        self.pub_takeoff.publish()


    def change_mux(self):
        self.current_mux = 1-self.current_mux
        self.pub_mux.publish(self.current_mux)

    def land(self):
        self.pub_land.publish()


    def onClose(self, *args):
        """
        set the stop event, cleanup the camera, and allow the rest of
        
        the quit process to continue
        """
        print("[INFO] closing...")
        # self.stopEvent.set()
        self.root.quit()
        self.root.destroy()
        # rospy.signal_shutdown('Exited UI')

if __name__ == '__main__':
    root = tki.Tk()
    my_gui = TelloUI(root)
    root.mainloop()

