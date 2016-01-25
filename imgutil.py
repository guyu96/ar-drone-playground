import cv2
import numpy as np
import os
import time


def match_template(template, srcimg, gray=True, edge=True, debug=False):
    t = time.time()
    if debug:
        src_copy = srcimg.copy()

    if gray:
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        srcimg = cv2.cvtColor(srcimg, cv2.COLOR_BGR2GRAY)
    if edge:
        template = cv2.Canny(template, 50, 200)
        srcimg = cv2.Canny(srcimg, 50, 200)

    # Template and source dimensions
    tw, th = template.shape[1], template.shape[0]
    sw, sh = srcimg.shape[1], srcimg.shape[0]

    found = None
    for scale in np.linspace(0.3, 2.5, 10):
        # resized dimensions
        rw = int(scale * sw)
        rh = int(scale * sh)

        # If template is bigger than source
        if rw < tw or rh < th:
            continue

        resized = cv2.resize(srcimg, (rw, rh),
                             interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if found is None or max_val > found[0]:
            found = (max_val, max_loc, scale)

    # matching region dimensions & location
    mrw, mrh = int(tw / found[2]), int(th / found[2])
    mrx, mry = int(found[1][0] / found[2]), int(found[1][1] / found[2])

    if debug:
        cv2.rectangle(src_copy, (mrx, mry), (mrx+mrw, mry+mrh),
                      (0, 0, 0), 2)
        cv2.imshow('ImageWindow', src_copy)
        cv2.waitKey(0)

    print(time.time() - t)
    return {'confidence': found[0], 'region_dimension': (mrw, mrh),
            'region_location': (mrx, mry)}


def get_threshold_stats():
    root_path = '/home/guyu/py/ps_drone/img/pattern'

    img_types = os.listdir(root_path + '/sample')
    template = cv2.imread(root_path + '/pattern.png')

    confidence_dict = {}
    for img_type in img_types:
        confidence_sum = 0
        highest = 0
        lowest = 1000000000

        imgs = os.listdir(root_path + '/sample/' + img_type)
        for img in imgs:
            srcimg = cv2.imread(root_path + '/sample/' + img_type + '/' + img)
            confidence = match_template(template, srcimg)['confidence']

            confidence_sum += confidence
            if confidence > highest:
                highest = confidence
            if confidence < lowest:
                lowest = confidence

        confidence_dict[img_type] = (lowest, highest, confidence_sum/len(imgs))

    print(confidence_dict)


def get_range(srcimg):

    def callback(value):
        pass

    def setup_trackbars():
        cv2.namedWindow("Range Selector", 0)
        for val in 'HSV':
            cv2.createTrackbar("%s_MIN" % val, "Range Selector", 0, 255, callback)
            cv2.createTrackbar("%s_MAX" % val, "Range Selector", 255, 255, callback)

    def get_trackbar_values():
        values = []

        for val in 'HSV':
            v1 = cv2.getTrackbarPos("%s_MIN" % val, "Range Selector")
            v2 = cv2.getTrackbarPos("%s_MAX" % val, "Range Selector")
            values.append(v1)
            values.append(v2)

        return values

    hsv = cv2.cvtColor(srcimg, cv2.COLOR_BGR2HSV)
    setup_trackbars()
    while True:
        v1_min, v1_max, v2_min, v2_max, v3_min, v3_max = get_trackbar_values()
        minhsv = (v1_min, v2_min, v3_min)
        maxhsv = (v1_max, v2_max, v3_max)
        thresh = cv2.inRange(hsv, minhsv, maxhsv)

        cv2.imshow("Original", srcimg)
        cv2.imshow("Thresholded", thresh)
        pressed = cv2.waitKey(10)
        if pressed != -1:
            print(minhsv, maxhsv)
            return minhsv, maxhsv


def get_center(srcimg, minhsv, maxhsv, min_blob_radius=0, debug=False):
    srccopy = srcimg.copy()
    # Blur to remove noise
    blurred = cv2.GaussianBlur(srcimg, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, minhsv, maxhsv)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    if debug:
        cv2.imshow('Binary Image', mask)
        cv2.waitKey(0)

    contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None

    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        (x, y), radius = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M['m10'] / M['m00']),
                  int(M['m01'] / M['m00']))

        if radius > min_blob_radius:
            cv2.circle(srccopy, (int(x), int(y)), int(radius),
                       (0, 255, 255), 2)
            cv2.circle(srccopy, center, 4, (0, 0, 0), -1)

            if debug:
                print('radius: %d, center: %s' % (radius, str(center)))
                cv2.imshow('Color Blob Detected', srccopy)
                cv2.waitKey(0)

            return radius, center, srccopy

    return None


if __name__ == '__main__':
    img = cv2.imread('/home/guyu/py/ps_drone/img/pp_orange.jpg')
    minhsv, maxhsv = get_range(img)
    t = time.time()
    get_center(img, minhsv, maxhsv, 5, False)
    print(time.time() - t)
    print(minhsv, maxhsv)
