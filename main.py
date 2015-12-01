import cv2
import time
import os
import threading

import droneutil as du
import imgutil as iu
import alprutil as au

drone = du.get_drone()
alpr = au.get_alpr()


def manual_flight():
    du.manual_control(drone)

def detect_lp(folder_name=None):
    if folder_name is None:
        folder_name = 'lp'

    img_path = du.save_img(drone, folder_name)
    plates = au.detect_plates(alpr, img_path)
    if plates is not None:
        au.print_plates(plates)

def surveillance():
    du.manual_control(drone, func=detect_lp)


surveillance()