import ps_drone
import cv2
import os

import imgutil
import alprutil
import time


def print_battery(drone):
    drone.printBlue('Battery: ' + str(drone.getBattery()[0]) + 
                    '% ' + str(drone.getBattery()[1]))

def save_img(drone, folder_name):
    VIC = drone.VideoImageCount
    cv2img = drone.VideoImage

    root_path = '/home/guyu/py/ps_drone/camera_img/'
    if not os.path.isdir(root_path + folder_name):
        os.makedirs(root_path + folder_name)

    img_path = '%s%s/drone_%d.jpg' % (root_path, folder_name, VIC)

    cv2.imwrite(img_path, cv2img)
    # drone.printGreen('Picture stored in %s' % img_path)
    return img_path    

def get_drone(defaultSpeed=0.1, videoOn=True):
    drone = ps_drone.Drone()
    drone.startup()
    drone.reset()

    # getBattery() returns (batValue percent), batStatus(OK or empty))
    while drone.getBattery()[0] == -1:
        time.sleep(0.1)
    # Give the drone some time to fully awake
    time.sleep(0.5)

    # "demo", "vision detect" and "chksum" packages of Navdata
    # are available 15 times per second
    drone.useDemoMode(True)
    # Recalibrate sensors
    drone.trim()
    drone.setSpeed(defaultSpeed)
    print_battery(drone)

    if videoOn:
        # Need to switch drone to multi-configuration mode before using video
        drone.setConfigAllID()
        # Use lower resolution
        drone.sdVideo()
        # Use front camera
        drone.frontCam()
        # Activate the drone's video function
        drone.printYellow('Loading Video Function...')
        drone.startVideo()

        VIC = drone.VideoImageCount
        while VIC == drone.VideoImageCount:
            time.sleep(0.5)

        drone.printGreen('Video Function Loaded')

    return drone

def do(func, duration):
    if func is None:
        time.sleep(duration)
        return

    t = time.time()
    while time.time() - t < duration:
        func()
        time.sleep(0.01)

def current_time_str():
    def two_digit(digits):
        if len(digits) == 1:
            return '0' + digits
        return digits

    t = time.gmtime()
    timestr = ''
    for i in range(6):
        s = two_digit(str(t[i]))
        if i < 2:
            s += '-'
        elif i == 2:
            s += ' '
        elif i < 5:
            s += ':'

        timestr += s

    return timestr

control_message = \
"""

---CONTROL MANUAL---
SPACE:  LAND/TAKE OFF
B:      STOP MOVEMENT
W:      MOVE FOWARD
S:      MOVE BACKWARD
A:      MOVE LEFT
D:      MOVE RIGHT
Q:      TURN LEFT
E:      TURN RIGHT
P:      TAKE PICTURE
U:      MOVE UP
I:      MOVE DOWN
N:      TERMINATE CONTROL
H:      SHOW MANUAL

"""

controls_dict = {
    ' ': 'Taking off/Landing...',
    'b': 'Stopping movement...',
    'w': 'Moving forward...',
    's': 'Moving backward...',
    'a': 'Movin left...',
    'd': 'Moving right...',
    'q': 'Turning left...',
    'e': 'Turning right...',
    'p': 'Taking a picture...',
    'u': 'Moving up...',
    'i': 'Moving down...',
    'n': 'Terminating control...',
    'h': control_message
}

def manual_control(drone, defaultSpeed=0.05, interval=2, func=None):
    stop = False
    session_time = current_time_str()
    drone.printBlue(control_message)

    while not stop:
        key = drone.getKey()

        # Check if key is valid
        if key in controls_dict:
            drone.printBlue(controls_dict[key])
        elif key != '':
            drone.printRed('"%s" is an invalid command.' % key)
            time.sleep(0.1)
            continue

        # ***CONTROL COMMANDS***

        # Press space to toggle landing / taking off
        if key == ' ':
            is_landed = drone.NavData['demo'][0][2]
            is_flying = drone.NavData['demo'][0][3]
            if is_landed and not is_flying:
                drone.takeoff()
                time.sleep(4)
            else:
                drone.land()
                time.sleep(4)

        # WASD controls
        elif key == 'w':
            drone.moveForward()
            do(func, interval)
            drone.hover()
        elif key == 's':
            drone.moveBackward()
            do(func, interval)
            drone.hover()
        elif key == 'a':
            drone.moveLeft()
            do(func, interval)
            drone.hover()
        elif key == 'd':
            drone.moveRight()
            do(func, interval)
            drone.hover()

        # QE for turning
        elif key == 'q':
            drone.turnAngle(-30, defaultSpeed, 1)
            do(func, max(2, interval))
            drone.hover()
        elif key == 'e':
            drone.turnAngle(30, defaultSpeed, 1)
            do(func, max(2, interval))
            drone.hover()

        # UI for moving up/down
        elif key == 'u':
            drone.moveUp()
            do(func, interval)
            drone.hover()
        elif key == 'i':
            drone.moveDown()
            do(func, interval)
            drone.hover()

        # L to take picture
        elif key == 'p':
            img_path = save_img(drone)
            drone.printGreen('Picture stored in %s' % img_path)

        # B to stop movement
        elif key == 'b':
            drone.hover()
            time.sleep(1)

        # N to terminate control
        elif key == 'n':
            drone.land()
            stop = True

        if key != '':
            drone.printGreen('Command Successful.')

        time.sleep(0.1)



#### Code for chasing an object
#### Doesn't work now, needs major revision
def look_around(drone, threshold, pattern_path, turn_speed=0.1):
    for i in range(24):
        drone.turnAngle(15, turn_speed, 0.1)
    time.sleep(4)
    t = time.time()
    while time.time() - t < 4:
        path = save_pic(drone, folder_name='pattern_detect')
        confidence = imgutil.match_template(pattern_path, path)
        if confidence > threshold:
            drone.stop()
            return True
    return False

def find_pattern(drone, threshold, pattern_path, downs, ups, interval):
    for d in range(downs):
        drone.moveDown()
        time.sleep(interval)
        drone.stop()
        found = look_around(drone, threshold, pattern_path)

        if found:
            return True

    for u in range(ups):
        drone.moveUp()
        time.sleep(interval)
        drone.stop()
        found = look_around(drone, threshold, pattern_path)

        if found:
            return True

    return False


def chase(drone, threshold, pattern_path):
    drone.takeoff()
    time.sleep(5)
    found = find_pattern(drone, threshold, pattern_path, 3, 6, 0.2)
    if not found:
        drone.land()
    else:
        while found:
            drone.moveForward()
            time.sleep(0.5)
            drone.stop()
            found = find_pattern(drone, threshold, pattern_path, 3, 6, 0.5)

    drone.land()