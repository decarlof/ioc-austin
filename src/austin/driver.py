import logging
import time
from copy import deepcopy

import numpy as np

import socket

from urx import Robot, RobotException
import austin.robotiq_gripper as robotiq_gripper


# Set up logging
log = logging.getLogger(__name__)

# Input for parameters

# homej0 = [-23.18, -78.18, 137.67, -153.64, -88.58, 284.37] # unit: degree


class RobotDisconnected(ConnectionError):
    ...


class RobotDriver:
    robot_ip: str = ""
    robot_port: int = 0
    gripper_port: int = 0
    is_connected: bool = False
    gripper: robotiq_gripper.RobotiqGripper = None
    gripper_pos_opn: int
    gripper_vel: int
    gripper_for: int
    ur = None

    def __init__(self, robot_ip, robot_port, gripper_port, timeout):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.gripper_port = gripper_port
        # Create the robot's socket object
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        # Prepare the gripper connection
        self.gripper = robotiq_gripper.RobotiqGripper()
        self.connect()

    def connect(self):
        self.ur = Robot(self.robot_ip)
        # Create socket for dashboard commands
        self.sock.connect((self.robot_ip, self.robot_port))
        # Receive initial "Connected" Header
        self.sock.recv(1096)
        # Connect the gripper
        self.gripper.connect(self.robot_ip, self.gripper_port)
        self.is_connected = True

    def send_and_receive(self, command):
        try:
            self.sock.sendall((command + "\n").encode())
            return self.get_reply()
        except (
            ConnectionResetError,
            ConnectionAbortedError,
            BrokenPipeError,
            TimeoutError,
        ):
            msg = f"The connection was lost to the robot ({self.robot_ip}:{self.robot_port})."
            msg += " Please connect and try running again."
            log.warning(msg)
            raise RobotDisconnected(msg)

    def get_reply(self):
        """Read one line from the socket.

        Returns
        =======

        response
          text until new line

        """
        collected = b""
        while True:
            part = self.sock.recv(1)
            if part != b"\n":
                collected += part
            elif part == b"\n":
                break
        return collected.decode("utf-8")

    # Robot position-related functions
    def get_position(self) -> tuple:
        """Return the robots current position in lab coordinates.

        Returns
        =======
        pos
          A tuple of the form (x, y, z, rx, ry, rz) for the robot's
          current position.

        """
        pos = self.ur.getl(wait=False)
        return pos

    def get_joints(self) -> tuple:
        """Return the robots current joint positions.

        Returns
        =======
        joints
          A tuple of the form (i, j, k, l, m, n) for the robot's
          current joins.

        """
        pos = self.ur.getj(wait=False)
        return pos

    # Gripper functions
    def activate_gripper(self):
        """
        activate Hand-E gripper
        """
        if self.gripper.is_active():
            print("Gripper already active")
        else:
            print("Activating gripper...")
            self.gripper.activate()
            print("Opening gripper...")
            self.gripper.move_and_wait_for_pos(
                self.gripper_pos_opn, self.gripper_vel, self.gripper_frc
            )

    def gripper_act_status(self):
        """
        check gripper being actived or not
        """
        return self.gripper.is_active()

    def disconnect_gripper(self):
        """
        disconnect Hand-E gripper
        """
        return self.gripper.disconnect()

    def gripper_cls_position(self):
        """
        gripper minimum position
        """
        return self.gripper.get_closed_position()

    def gripper_opn_position(self):
        """
        gripper maximum position
        """
        return self.gripper.get_open_position()

    def gripper_cal(self):
        """
        calibrate gripper position
        """
        return self.gripper.auto_calibrate()

    def gripper_cur_position(self):
        """
        get gripper current postion
        """
        return self.gripper.get_current_position()

    def gripper_move(self, gripper_pos=30, gripper_vel=0.5, gripper_frc=0.2):
        """
        move gripper to a postion with speed and force in percentage
        """
        return self.gripper.move_and_wait_for_pos(gripper_pos, gripper_vel, gripper_frc)

    # transfer functions
    def get_joint_angles(self):
        """
        get current joint angles
        """
        return self.connect.getj()

    def movej(self, joints, acc, vel, wait=True):
        """
        Description: Moves the robot to the home location.
        """
        return self.ur.movej(joints, acc, vel, wait=True)

    def movel(self, pos, acc, vel, wait=True):
        """
        Description: Moves the robot to the home location.
        """
        return self.ur.movel(pos, acc, vel, wait=True)

    def pickj(
        self,
        pick_goal,
        acc,
        vel,
        gripper_pos_opn,
        gripper_pos_cls,
        gripper_vel,
        gripper_frc,
        wait=True,
    ):
        """Pick up from first goal position"""
        above_goal = deepcopy(pick_goal)
        above_goal[2] += 0.05

        print("Moving to above goal position")
        self.ur.movej(above_goal, acc, vel, wait=True)

        print("Opening gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_opn, gripper_vel, gripper_frc)

        print("Moving to goal position")
        self.ur.movej(pick_goal, acc, vel, wait=True)

        print("Closing gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_cls, gripper_vel, gripper_frc)

        print("Moving back to above goal position")
        self.ur.movej(above_goal, acc, vel, wait=True)

    def pickl(
        self,
        pick_goal,
        acc,
        vel,
        gripper_pos_opn,
        gripper_pos_cls,
        gripper_vel,
        gripper_frc,
        wait=True,
    ):
        """Pick up from first goal position"""
        above_goal = deepcopy(pick_goal)
        above_goal[2] += 0.001

        print("Moving to above goal position")
        self.ur.movel(above_goal, acc, vel, wait=True)

        print("Opening gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_opn, gripper_vel, gripper_frc)

        print("Moving to goal position")
        self.ur.movel(pick_goal, acc, vel, wait=True)

        print("Closing gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_cls, gripper_vel, gripper_frc)

        print("Moving back to above goal position")
        self.ur.movel(above_goal, acc, vel, wait=True)

    def placej(
        self,
        place_goal,
        acc,
        vel,
        gripper_pos_opn,
        gripper_pos_cls,
        gripper_vel,
        gripper_frc,
        wait=True,
    ):
        """Place down at second goal position"""
        above_goal = deepcopy(place_goal)
        above_goal[2] += 0.05

        print("Moving to above goal position")
        self.ur.movej(above_goal, acc, vel, wait=True)

        print("Moving to goal position")
        self.ur.movej(place_goal, acc, vel, wait=True)

        print("Opennig gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_opn, gripper_vel, gripper_frc)

        print("Moving back to above goal position")
        self.ur.movej(above_goal, acc, vel, wait=True)

    def placel(
        self,
        place_goal,
        acc,
        vel,
        gripper_pos_opn,
        gripper_pos_cls,
        gripper_vel,
        gripper_frc,
        wait=True,
    ):
        """Place down at second goal position"""
        above_goal = deepcopy(place_goal)
        above_goal[2] += 0.001

        print("Moving to above goal position")
        self.ur.movel(above_goal, acc, vel, wait=True)

        print("Moving to goal position")
        self.ur.movel(place_goal, acc, vel, wait=True)

        print("Opennig gripper")
        self.gripper.move_and_wait_for_pos(gripper_pos_opn, gripper_vel, gripper_frc)

        print("Moving back to above goal position")
        self.ur.movel(above_goal, acc, vel, wait=True)
