import cv2
import numpy as np

def match_template(temp_path, src_path, gray=True, edge=True):
    template = cv2.imread(temp_path)
    srcimg = cv2.imread(src_path)
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
    for scale in np.linspace(0.1, 2.5, 20):
        # resized dimensions
        rw = int(scale * srcimg.shape[1])
        rh = int(scale * srcimg.shape[0])

        # If template is bigger than source
        if rw < tw or rh < th:
            continue

        resized = cv2.resize(srcimg, (rw, rh), 
            interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if found is None or max_val > found[0]:
            found = (max_val, max_loc, scale)

    # matching region dimensions & locations
    mrw, mrh = int(tw / found[2]), int(th / found[2])
    mrloc = (int(found[1][0] / found[2]), 
        int(found[1][1] / found[2]))

    cv2.rectangle(src_copy, mrloc, (mrloc[0]+mrw, mrloc[1]+mrh),
        (0, 0, 0), 2)
    # cv2.imshow('ImageWindow', src_copy)
    # cv2.waitKey(1500)

    return found[0]