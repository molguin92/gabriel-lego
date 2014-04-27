#!/usr/bin/env python
#
# Cloudlet Infrastructure for Mobile Computing
#   - Task Assistance
#
#   Author: Zhuo Chen <zhuoc@cs.cmu.edu>
#
#   Copyright (C) 2011-2013 Carnegie Mellon University
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import os
import sys
import cv2
import time
import struct
import traceback
import numpy as np
if os.path.isdir("../../../"):
    sys.path.insert(0, "../../../")

from gabriel.proxy.common import LOG

LOG_TAG = "LEGO: "

def raw2cv_image(raw_data):
    img_array = np.asarray(bytearray(raw_data), dtype=np.int8)
    cv_image = cv2.imdecode(img_array, -1)
    return cv_image

def display_image(display_name, img, wait_time = 500):
    img_display = cv2.resize(img, (640, 360))
    #img_display = img
    cv2.imshow(display_name, img_display)
    cv2.waitKey(wait_time)

def set_value(img, pts, value):
    '''
    set the points (@pts) in the image (@img) to value (@value)
    @img is the input image array, can be single/multi channel
    @pts are n * 2 arrays where n is the number of points
    '''
    if pts.ndim == 3:
        pts.resize(len(pts), 2)
    is_multichannel = img.ndim > 2
    i = pts[:, 1]
    j = pts[:, 0]
    if is_multichannel:
        img[i, j, :] = value
    else:
        img[i, j] = value

def ind2sub(size, idx):
    return (idx / size[1], idx % size[1])

def euc_dist(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    return np.linalg.norm(p1 - p2)

def angle_dist(a1, a2, angle_range = 180):
    a1, a2 = min(a1, a2), max(a1, a2)
    dist1 = a2 - a1
    dist2 = a1 + angle_range - a2
    return min(dist1, dist2)

def is_roughly_convex(cnt, threshold = 0.7):
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    cnt_area = cv2.contourArea(cnt)
    return (float(cnt_area) / hull_area > threshold)

def is_line_seg_close(line1, line2):
    pt1_1 = np.array(line1[0 : 2])
    pt1_2 = np.array(line1[2 : 4])
    pt2_1 = np.array(line2[0 : 2])
    pt2_2 = np.array(line2[2 : 4])
    l1 = euc_dist(pt1_1, pt1_2)
    l2 = euc_dist(pt2_1, pt2_2)
    v1 = pt1_2 - pt1_1
    v2 = pt2_1 - pt1_1
    v3 = pt2_2 - pt1_1
    area1 = np.absolute(np.cross(v1, v2))
    area2 = np.absolute(np.cross(v1, v3))
    if max(area1, area2) < l1 * l2 / 3:
        return True
    else:
        return False

def line_interset(a, b):
    x1 = a[0]; y1 = a[1]; x2 = a[2]; y2 = a[3]
    x3 = b[0]; y3 = b[1]; x4 = b[2]; y4 = b[3]
    d = ((float)(x1-x2) * (y3-y4)) - ((y1-y2) * (x3-x4))
    if d:
        x = ((x1*y2 - y1*x2) * (x3-x4) - (x1-x2) * (x3*y4 - y3*x4)) / d;
        y = ((x1*y2 - y1*x2) * (y3-y4) - (y1-y2) * (x3*y4 - y3*x4)) / d;
    else:
        x, y = (-1, -1)
    return (x, y)

def get_corner_pts(bw):
    lines = cv2.HoughLinesP(bw, 1, np.pi/180, 50, minLineLength = 100, maxLineGap = 100)
    lines = lines[0]
    new_lines = list()
    for line in lines:
        flag = True
        for new_line in new_lines:
            if is_line_seg_close(line, new_line):
                flag = False
                break
        if flag:
            new_lines.append(list(line))

    mean_p = lines.mean(axis = 0)
    mean_p = (np.mean([mean_p[0], mean_p[2]]), np.mean([mean_p[1], mean_p[3]]))
    corners = list()
    for idx1, line1 in enumerate(new_lines):
        for idx2, line2 in enumerate(new_lines):
            if idx1 >= idx2:
                continue
            inter_p = line_interset(line1, line2)
            dist = euc_dist(inter_p, mean_p)
            if dist < 500:
                corners.append(inter_p)

    dtype = [('x', float), ('y', float)]
    corners = np.array(corners, dtype = dtype)
    corners = np.sort(corners, order = 'y')
    if corners[0][0] < corners[1][0]:
        ul = corners[0]; ur = corners[1]
    else:
        ul = corners[1]; ur = corners[0]
    if corners[2][0] < corners[3][0]:
        bl = corners[2]; br = corners[3]
    else:
        bl = corners[3]; br = corners[2]

    corners = np.float32([list(ul), list(ur), list(bl), list(br)])
    return corners

def get_rotation(bw):
    lines = cv2.HoughLinesP(bw, 1, np.pi/180, 10, minLineLength = 15, maxLineGap = 10)
    lines = lines[0]
    degrees = np.zeros(len(lines))
    for line_idx, line in enumerate(lines):
        x_diff = line[0] - line[2]
        y_diff = line[1] - line[3]
        if x_diff == 0:
            degree = np.pi / 2 # TODO
        else:
            degree = np.arctan(y_diff / x_diff)
        degrees[line_idx] = degree * 180 / np.pi
        if degrees[line_idx] <= 0: # get an angle in (0, 90]
            degrees[line_idx] += 90

    # now use RANSAC like algorithm to get the consensus
    max_vote = 0
    consensus_degree = None
    for degree in degrees:
        n_vote = 0
        for degree_cmp in degrees:
            if angle_dist(degree, degree_cmp) < 5:
                n_vote += 1
        if n_vote > max_vote:
            max_vote = n_vote
            consensus_degree = degree

    # TODO: average within the 5 degree range
    return consensus_degree


##################### Below are only for the Lego task #########################
def locate_lego(img, display_list):
    black_min = np.array([0, 0, 0], np.uint8)
    black_max = np.array([100, 100, 100], np.uint8)
    mask_black = cv2.inRange(img, black_min, black_max)

    ## 1. find black dots (somewhat black, and small)
    ## 2. find area where black dots density is high
    mask_black_copy = mask_black.copy() # need a copy because cv2.findContours may change the image
    contours, hierarchy = cv2.findContours(mask_black_copy, mode = cv2.RETR_CCOMP, method = cv2.CHAIN_APPROX_NONE )
    counts = np.zeros((9, 16)) # count black dots in each 80 * 80 block
    for cnt_idx, cnt in enumerate(contours):
        if len(cnt) > 20 or (hierarchy[0, cnt_idx, 3] != -1):
            continue
        max_p = cnt.max(axis = 0)
        min_p = cnt.min(axis = 0)
        diff_p = max_p - min_p
        if diff_p.max() > 5:
            continue
        mean_p = cnt.mean(axis = 0)[0]
        counts[int(mean_p[1] / 80), int(mean_p[0] / 80)] += 1

    ## find a point that we are confident is in the board
    max_idx = counts.argmax()
    i, j = ind2sub((9, 16), max_idx)
    if counts[i, j] < 50:
        rtn_msg = {'status' : 'fail', 'message' : 'Too little black dots'}
        return (rtn_msg, None, None)
    in_board_p = (i * 80 + 40, j * 80 + 40)

    ## locate the board by finding the contour that is likely to be of the board
    min_dist = 10000
    closest_cnt = None
    for cnt_idx, cnt in enumerate(contours):
        if hierarchy[0, cnt_idx, 3] == -1:
            continue
        max_p = cnt.max(axis = 0)
        min_p = cnt.min(axis = 0)
        #print "max: %s, min: %s" % (max_p, min_p)
        diff_p = max_p - min_p
        if diff_p.min() > 100:
            mean_p = cnt.mean(axis = 0)[0]
            mean_p = mean_p[::-1]
            dist = euc_dist(mean_p, in_board_p)
            if dist < min_dist:
                min_dist = dist
                closest_cnt = cnt

    if min_dist > 250 or not is_roughly_convex(closest_cnt):
        rtn_msg = {'status' : 'fail', 'message' : 'Cannot locate board border'}
        return (rtn_msg, None, None)
    hull = cv2.convexHull(closest_cnt)
    mask_board = np.zeros(mask_black.shape, dtype=np.uint8)
    cv2.drawContours(mask_board, [hull], 0, 255, -1)
    img_board = np.zeros(img.shape, dtype=np.uint8)
    img_board = cv2.bitwise_and(img, img, dst = img_board, mask = mask_board)
    if 'board' in display_list:
        display_image('board', img_board)
    
    ## some properties of the board
    board_area = cv2.contourArea(hull)
    M = cv2.moments(hull)
    board_center = (int(M['m01']/M['m00']), int(M['m10']/M['m00']))
    board_perimeter = cv2.arcLength(hull, True)
    #print (board_area, board_center, board_perimeter)

    ## find the perspective correction matrix
    board_border = np.zeros(mask_black.shape, dtype=np.uint8)
    cv2.drawContours(board_border, [hull], 0, 255, 1)
    corners = get_corner_pts(board_border)
    target_points = np.float32([[0, 0], [270, 0], [0, 155], [270, 155]])
    perspective_mtx = cv2.getPerspectiveTransform(corners, target_points)

    ## locate lego
    bw_board = cv2.cvtColor(img_board, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(bw_board, 100, 200) # TODO: check thresholds...
    kernel = np.ones((6,6),np.int8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations = 1)
    kernel = np.ones((3,3),np.int8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel, iterations = 1)
    # TODO: add some safety here...
    edges = cv2.bitwise_not(edges, mask = mask_board)

    contours, hierarchy = cv2.findContours(edges, mode = cv2.RETR_CCOMP, method = cv2.CHAIN_APPROX_NONE )
    max_area = 0
    lego_cnt = None
    for cnt_idx, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < board_area / 300.0:
            continue
        if hierarchy[0, cnt_idx, 3] != -1 or not is_roughly_convex(cnt):
            continue
        mean_p = cnt.mean(axis = 0)[0]
        mean_p = mean_p[::-1]
        if euc_dist(mean_p, board_center) > board_perimeter / 10.0:
            continue
        cnt_area = cv2.contourArea(cnt)
        if cnt_area > max_area:
            max_area = cnt_area
            lego_cnt = cnt

    if lego_cnt is None:
        rtn_msg = {'status' : 'fail', 'message' : 'Cannot find Lego on the board'}
        return (rtn_msg, None, None)

    mask_lego = np.zeros(mask_board.shape, dtype=np.uint8)
    cv2.drawContours(mask_lego, [lego_cnt], 0, 255, -1)
    kernel = np.uint8([[0, 0, 0], [0, 1, 0], [0, 1, 0]])
    mask_lego = cv2.erode(mask_lego, kernel, iterations = 3)
    img_lego = np.zeros(img.shape, dtype=np.uint8)
    img_lego = cv2.bitwise_and(img, img, dst = img_lego, mask = mask_lego) # this is weird, if not providing an input image, the output will be with random backgrounds... how is dst initialized?

    if 'board_corrected' in display_list:
        img_board_corrected = cv2.warpPerspective(img_board, perspective_mtx, (270, 155))
        display_image('board_corrected', img_board_corrected)
    if 'lego' in display_list:
        display_image('lego', img_lego)

    rtn_msg = {'status' : 'success'}
    return (rtn_msg, img_lego, perspective_mtx)

def correct_orientation(img_lego, perspective_mtx, display_list):
    ## correct perspective
    img_perspective = cv2.warpPerspective(img_lego, perspective_mtx, (270, 155))
    if 'lego_perspective' in display_list:
        display_image('lego_perspective', img_perspective)

    ## correct rotation
    bw_perspective = cv2.cvtColor(img_perspective, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(bw_perspective, 100, 200)
    if 'lego_edge' in display_list:
        display_image('lego_edge', edges)
    
    rotation_degree = get_rotation(edges)
    #print rotation_degree
    img_shape = img_perspective.shape
    M = cv2.getRotationMatrix2D((img_shape[1]/2, img_shape[0]/2), rotation_degree, scale = 1)
    img_correct = cv2.warpAffine(img_perspective, M, (img_shape[1], img_shape[0]))
    if 'lego_correct' in display_list:
        display_image('lego_correct', img_correct)

    return (None, None)