#!/usr/bin/env python
# coding: utf-8

# In[1]:


import mess
import match_prepare as match
import matplotlib.pyplot as plt
import numpy as np
import imutils
import glob
import cv2
import copy
import pickle


# #### horizontal projection

# In[2]:


def horizontal_projection(image_h):
    image = image_h.copy()
    image[image < 127] = 1
    image[image >= 127] = 0
    h_projection = np.sum(image, axis=1)

    return h_projection


def detect_horizontal_line(h_projection, pixel_limit_ste, pixel_limit_ets):
    # Detect line horizontal
    up_flag = 0
    down_flag = 0
    # pixel_limit = 5
    start_to_end = 0
    end_to_start = pixel_limit_ets + 1
    start_point = []
    for x in range(len(h_projection)):
        if h_projection[x] > 0 and up_flag == 1:
            start_to_end += 1

        if h_projection[x] == 0 and up_flag == 1:
            # print(start_to_end)
            start_point.append(x)
            # print(start_point)
            if start_to_end < pixel_limit_ste:
                del(start_point[len(start_point) - 1])
                # print('delete ste')
                down_flag = 0
                up_flag = 1
            else:
                down_flag = 1
                up_flag = 0
                start_to_end = 0

        if h_projection[x] == 0 and down_flag == 1:
            end_to_start += 1

        if h_projection[x] > 0 and up_flag == 0:
            start_point.append(x)
            # print(start_point)
            if end_to_start < pixel_limit_ets:
                del(start_point[len(start_point)-1])
                del(start_point[len(start_point)-1])
            up_flag = 1
            down_flag = 0
            end_to_start = 0

    if len(start_point) % 2 != 0:
        if h_projection[len(h_projection) - 1] > 0:
            start_point.append(len(h_projection) - 1)

    return start_point


# #### used by image processing stage

# In[3]:


def get_ul_coordinat(coordinat, height, ht_overide=0):
    if ht_overide > 0:
        height_tanwin = ht_overide
    else:
        height_tanwin = coordinat[3] - coordinat[1]
    # upper
    if coordinat[1]-height_tanwin > 0:
        upper = [coordinat[0], coordinat[1]-height_tanwin,
                 coordinat[2], coordinat[3]-height_tanwin]
    else:
        upper = [coordinat[0], 0,
                 coordinat[2], coordinat[3]-height_tanwin]
    # lower
    if coordinat[3]+height_tanwin < height:
        lower = [coordinat[0], coordinat[1]+height_tanwin,
                 coordinat[2], coordinat[3]+height_tanwin]
    else:
        lower = [coordinat[0], coordinat[1]+height_tanwin,
                 coordinat[2], height-1]

    return upper, lower


def upper_or_lower(bw_img, upper, lower):
    upper_count = 0
    for x in range(upper[0], upper[2]):
        for y in range(upper[1], upper[3]):
            if bw_img[y, x] < 1:
                upper_count += 1

    lower_count = 0
    for x in range(lower[0], lower[2]):
        for y in range(lower[1], lower[3]):
            if bw_img[y, x] < 1:
                lower_count += 1

    return upper_count, lower_count


def get_lr_coordinat(coordinat, width):
    width_tanwin = coordinat[2] - coordinat[0]
    if coordinat[0] - width_tanwin > 0:
        left = [coordinat[0]-width_tanwin, coordinat[1],
                coordinat[2]-width_tanwin, coordinat[3]]
    else:
        left = [0, coordinat[1],
                coordinat[2]-width_tanwin, coordinat[3]]
    if coordinat[2] + width_tanwin < width:
        right = [coordinat[0]+width_tanwin, coordinat[1],
                 coordinat[2]+width_tanwin, coordinat[3]]
    else:
        right = [coordinat[0]+width_tanwin, coordinat[1],
                 width-1, coordinat[3]]

    return left, right


def black_pixel_count(bw_img, lower):
    lower_count = 0
    for x in range(lower[0], lower[2]):
        for y in range(lower[1], lower[3]):
            if bw_img[y, x] < 1:
                lower_count += 1

    return lower_count


def get_marker_name(key):
    part = key.split('_')
    name = []
    for x in range(len(part)):
        if x == 0:
            continue
        if x == len(part) - 1:
            name.append(part[x])
        else:
            name.append(part[x] + '_')
    name = ''.join(name)

    return name


def region_tanwin(coordinat, image, font_list, view=True):
    saved_tanwin_height = coordinat[3] - coordinat[1]
    font_object = font_list[0]
    h, w, = image.shape

    marker_only_count = black_pixel_count(image, coordinat)

    con_pack = font_object.eight_connectivity(image.copy(), coordinat,
                                              left=False, right=False)
    image_process = image.copy()
    image_process[:] = 255
    for region in con_pack:
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
    # cv2.destroyAllWindows()
    font_object.horizontal_projection(image_process)
    h_image = font_object.detect_horizontal_line(image.copy(), 0, 0)
    start_point_h = font_object.start_point_h
    font_object.vertical_projection(image_process)
    h_image = font_object.detect_vertical_line(image.copy(), 0)
    start_point_v = font_object.start_point_v

    coordinat_candidate = [start_point_v[0], start_point_h[0],
                           start_point_v[1], start_point_h[1]]
    cc_count = black_pixel_count(image, coordinat_candidate)

    if cc_count < 2 * marker_only_count:
        coordinat = coordinat_candidate

    cv2.rectangle(image_process, (coordinat[0], coordinat[1]),
                  (coordinat[2], coordinat[3]), (0, 255, 0), 2)
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

    upper, lower = get_ul_coordinat(coordinat, h)
    print(upper)
    print(lower)
    upper_count, lower_count = upper_or_lower(image, upper, lower)

    if upper_count < lower_count:
        cv2.rectangle(image_process, (lower[0], lower[1]),
                      (lower[2], lower[3]), (100, 150, 0), 2)
        region = lower
    elif upper_count > lower_count:
        cv2.rectangle(image_process, (upper[0], upper[1]),
                      (upper[2], upper[3]), (100, 150, 0), 2)
        region = upper
    else:
        print('enlarge')
        while(upper_count == lower_count):
            upper, _ = get_ul_coordinat(upper, h)
            _, lower = get_ul_coordinat(lower, h)
            upper_count, lower_count = upper_or_lower(image, upper, lower)
            if upper_count < lower_count:
                cv2.rectangle(image_process, (lower[0], lower[1]),
                              (lower[2], lower[3]), (100, 150, 0), 2)
                region = lower
            elif upper_count > lower_count:
                cv2.rectangle(image_process, (upper[0], upper[1]),
                              (upper[2], upper[3]), (100, 150, 0), 2)
                region = upper
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

    return region


def raw_baseline(image_b, font_object):
    #     image_b = bw_image[oneline_coordinat[0]:oneline_coordinat[1], :]
    font_object.horizontal_projection(image_b)
    font_object.base_line(image_b)
    oneline_baseline = []
    oneline_baseline.append(font_object.base_start)
    oneline_baseline.append(font_object.base_end)
    if oneline_baseline[1] < oneline_baseline[0]:
        temp = oneline_baseline[0]
        oneline_baseline[0] = oneline_baseline[1]
        oneline_baseline[1] = temp
    oneline_image = font_object.one_line_image
    # cv2.imshow('line', oneline_image)
    # print('>')

    return oneline_baseline


# #### eight_conn_by_seed_tanwin

# In[6]:


def eight_conn_by_seed_tanwin(coordinat, img, font_list, view=True):
    saved_tanwin_height = coordinat[3] - coordinat[1]
    font_object = font_list[0]
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     coordinat = [ 98, 625, 109, 640]
    # mid_seed = coordinat[1] + int((coordinat[3]-coordinat[1])/2)
    # seed = [0, mid_seed, w, mid_seed+1]
    # Otsu threshold
    # ret_img, image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY
    #                                 + cv2.THRESH_OTSU)
    # Simple threshold
    # ret_img, image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    # Adaptive threshold value is the mean of neighbourhood area
    # image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
    #                               cv2.THRESH_BINARY, 11, 2)

    # Adaptive threshold value is the weighted sum of neighbourhood
    # values where weights are a gaussian window
    image = cv2.adaptiveThreshold(gray, 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)

    marker_only_count = black_pixel_count(image, coordinat)

    con_pack = font_object.eight_connectivity(image.copy(), coordinat,
                                              left=False, right=False)
    image_process = image.copy()
    image_process[:] = 255
    for region in con_pack:
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
    # cv2.destroyAllWindows()
    font_object.horizontal_projection(image_process)
    h_image = font_object.detect_horizontal_line(image.copy(), 0, 0)
    start_point_h = font_object.start_point_h
    font_object.vertical_projection(image_process)
    h_image = font_object.detect_vertical_line(image.copy(), 0)
    start_point_v = font_object.start_point_v

    coordinat_candidate = [start_point_v[0], start_point_h[0],
                           start_point_v[1], start_point_h[1]]
    cc_count = black_pixel_count(image, coordinat_candidate)

    if cc_count < 2 * marker_only_count:
        coordinat = coordinat_candidate

    cv2.rectangle(image_process, (coordinat[0], coordinat[1]),
                  (coordinat[2], coordinat[3]), (0, 255, 0), 2)
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

    upper, lower = get_ul_coordinat(coordinat, h)
    print(upper)
    print(lower)
    upper_count, lower_count = upper_or_lower(image, upper, lower)

    if upper_count < lower_count:
        print('lower')
        left, right = get_lr_coordinat(lower, w)
        con_pack = font_object.eight_connectivity(image.copy(), lower,
                                                  left=False, right=False)
        for region in con_pack:
            for val in con_pack[region]:
                image_process[val] = 0
        cv2.rectangle(image_process, (lower[0], lower[1]),
                      (lower[2], lower[3]), (100, 150, 0), 2)
    elif upper_count > lower_count:
        print('upper')
        left, right = get_lr_coordinat(upper, w)
        con_pack = font_object.eight_connectivity(image.copy(), upper,
                                                  left=False, right=False)
        for region in con_pack:
            for val in con_pack[region]:
                image_process[val] = 0
        cv2.rectangle(image_process, (upper[0], upper[1]),
                      (upper[2], upper[3]), (100, 150, 0), 2)
    else:
        print('enlarge')
        while(upper_count == lower_count):
            upper, _ = get_ul_coordinat(upper, h)
            _, lower = get_ul_coordinat(lower, h)
            upper_count, lower_count = upper_or_lower(image, upper, lower)
            if upper_count < lower_count:
                left, right = get_lr_coordinat(lower, w)
                con_pack = font_object.eight_connectivity(image.copy(), lower,
                                                          left=False, right=False)
                for region in con_pack:
                    for val in con_pack[region]:
                        image_process[val] = 0
                cv2.rectangle(image_process, (lower[0], lower[1]),
                              (lower[2], lower[3]), (100, 150, 0), 2)
            elif upper_count > lower_count:
                left, right = get_lr_coordinat(upper, w)
                con_pack = font_object.eight_connectivity(image.copy(), upper,
                                                          left=False, right=False)
                for region in con_pack:
                    for val in con_pack[region]:
                        image_process[val] = 0
                cv2.rectangle(image_process, (upper[0], upper[1]),
                              (upper[2], upper[3]), (100, 150, 0), 2)

    left_count, _ = upper_or_lower(image, left, right)
    while(left_count < 2):
        left, _ = get_lr_coordinat(left, w)
        left_count, _ = upper_or_lower(image, left, right)
        if left[0] < 1:
            break
    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), left,
                                              left=False, right=False)
    max_left_region = 0
    for region in con_pack:
        #         print(con_pack[region])
        #         print(region)
        if len(con_pack[region]) > max_left_region:
            max_left_region = len(con_pack[region])
            print(max_left_region)
        for val in con_pack[region]:
            #             print(region)
            #             print(val)
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
    # cv2.destroyAllWindows()

    image_process_after_left = image.copy()
    image_process_after_left[:] = 255
    for region in con_pack:
        for val in con_pack[region]:
            image_process_after_left[val] = 0
    font_object.horizontal_projection(image_process_after_left)
    h_image_al = font_object.detect_horizontal_line(image.copy(), 0, 0)
    start_point_h_al = font_object.start_point_h
    coordinat_al = [0, start_point_h_al[0], w, start_point_h_al[1]]

    cv2.rectangle(image_process_after_left, (coordinat_al[0], coordinat_al[1]),
                  (coordinat_al[2], coordinat_al[3]), (0, 255, 0), 2)
    if view:
        cv2.imshow('d_al', image_process_after_left)
        cv2.waitKey(0)

    left = [left[0], start_point_h_al[0], left[2], start_point_h_al[1]]
    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)

    upper, lower = get_ul_coordinat(left, h, saved_tanwin_height)
#     cv2.rectangle(image_process, (lower[0], lower[1]),
#                           (lower[2], lower[3]), (100, 150,0), 2)
#     cv2.rectangle(image_process, (upper[0], upper[1]),
#                           (upper[2], upper[3]), (100, 150,0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), upper,
                                              left=False, right=False)
#     max_left_region = 30
    for region in con_pack:
        if len(con_pack[region]) > max_left_region:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    con_pack = font_object.eight_connectivity(image.copy(), lower,
                                              left=False, right=False)
    for region in con_pack:
        if len(con_pack[region]) > max_left_region:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

############################
#     left_count_mod = black_pixel_count(image, left)
    left_count_mod = 100
    left, _ = get_lr_coordinat(left, w)
    left_count = black_pixel_count(image, left)
    while(left_count < 2):
        left, _ = get_lr_coordinat(left, w)
        left_count = black_pixel_count(image, left)
        if left[0] < 1:
            break
    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), left,
                                              left=False, right=False)
    for region in con_pack:
        if len(con_pack[region]) > 2 * left_count_mod:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

    left, _ = get_lr_coordinat(left, w)
    left_count = black_pixel_count(image, left)
    while(left_count < 2):
        left, _ = get_lr_coordinat(left, w)
        left_count = black_pixel_count(image, left)
        if left[0] < 1:
            break
    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), left,
                                              left=False, right=False)
    for region in con_pack:
        if len(con_pack[region]) > 2 * left_count_mod:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
##########################

    con_pack = font_object.eight_connectivity(image.copy(), right,
                                              left=False, right=False)
    for region in con_pack:
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
#     cv2.destroyAllWindows()

    font_object.horizontal_projection(image_process)
    al_height = start_point_h_al[1]-start_point_h_al[0]
    print('al_height:', al_height)
    h_image = font_object.detect_horizontal_line(image.copy(), al_height, 5)
    start_point_h = font_object.start_point_h
    if view:
        cv2.imshow('line', h_image)
        cv2.waitKey(0)
#     cv2.destroyAllWindows()

    return start_point_h, image_process


# #### eight_conn_by_seed

# In[7]:


def eight_conn_by_seed(coordinat, img, font_list, view=True):
    saved_starting_height = coordinat[3] - coordinat[1]
    font_object = font_list[0]
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     coordinat = [ 98, 625, 109, 640]
    # mid_seed = coordinat[1] + int((coordinat[3]-coordinat[1])/2)
    # seed = [0, mid_seed, w, mid_seed+1]
    # Otsu threshold
    # ret_img, image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY
    #                                 + cv2.THRESH_OTSU)
    # Simple threshold
    # ret_img, image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    # Adaptive threshold value is the mean of neighbourhood area
    # image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
    #                               cv2.THRESH_BINARY, 11, 2)

    # Adaptive threshold value is the weighted sum of neighbourhood
    # values where weights are a gaussian window
    image = cv2.adaptiveThreshold(gray, 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 11, 2)

    marker_only_count = black_pixel_count(image, coordinat)

    con_pack = font_object.eight_connectivity(image.copy(), coordinat,
                                              left=False, right=False)
    max_y_start = 0
    min_y_start = 10000
    for region in con_pack:
        for val in con_pack[region]:
            if val[0] > max_y_start:
                max_y_start = val[0]
            if val[0] < min_y_start:
                min_y_start = val[0]

    starting_height = coordinat[3] - coordinat[1]
    sch_a = max_y_start - coordinat[1]
    sch_b = coordinat[3] - min_y_start

    if sch_a > sch_b:
        starting_conpack_height = sch_a
    else:
        starting_conpack_height = sch_b

    image_process = image.copy()
    image_process[:] = 255
    if starting_conpack_height < 2 * starting_height:
        for region in con_pack:
            for val in con_pack[region]:
                image_process[val] = 0
        if view:
            cv2.imshow('d', image_process)
            cv2.waitKey(0)
    # cv2.destroyAllWindows()
        font_object.horizontal_projection(image_process)
        h_image = font_object.detect_horizontal_line(
            image.copy(), starting_height, 0)
        start_point_h = font_object.start_point_h
        font_object.vertical_projection(image_process)
        h_image = font_object.detect_vertical_line(image.copy(), 0)
        start_point_v = font_object.start_point_v

        coordinat_candidate = [start_point_v[0], start_point_h[0],
                               start_point_v[1], start_point_h[1]]
        cc_count = black_pixel_count(image, coordinat_candidate)

        if cc_count < 2 * marker_only_count:
            print('replace coordinat')
            coordinat = coordinat_candidate

    cv2.rectangle(image_process, (coordinat[0], coordinat[1]),
                  (coordinat[2], coordinat[3]), (0, 255, 0), 2)
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

    coordinat, right = get_lr_coordinat(coordinat, w)

    left_count = black_pixel_count(image, coordinat)
    print('leftcount:', left_count)
    while(left_count < 2):
        coordinat, _ = get_lr_coordinat(coordinat, w)
        left_count = black_pixel_count(image, coordinat)
        print('leftcount:', left_count)
    left = coordinat

    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), left,
                                              left=False, right=False)
    max_left_region = 0
    for region in con_pack:
        if len(con_pack[region]) > max_left_region:
            max_left_region = len(con_pack[region])
#             print(max_left_region)
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)
    # cv2.destroyAllWindows()

    image_process_after_left = image.copy()
    image_process_after_left[:] = 255
    for region in con_pack:
        for val in con_pack[region]:
            image_process_after_left[val] = 0
    font_object.horizontal_projection(image_process_after_left)
    h_image_al = font_object.detect_horizontal_line(image.copy(), 0, 0)
    start_point_h_al = font_object.start_point_h
    coordinat_al = [0, start_point_h_al[0], w, start_point_h_al[1]]

    cv2.rectangle(image_process_after_left, (coordinat_al[0], coordinat_al[1]),
                  (coordinat_al[2], coordinat_al[3]), (0, 255, 0), 2)
    if view:
        cv2.imshow('d_al', image_process_after_left)
        cv2.waitKey(0)

    left = [left[0], start_point_h_al[0], left[2], start_point_h_al[1]]
    cv2.rectangle(image_process, (left[0], left[1]),
                  (left[2], left[3]), (100, 150, 0), 2)

    upper, lower = get_ul_coordinat(left, h, saved_starting_height)
#     cv2.rectangle(image_process, (lower[0], lower[1]),
#                           (lower[2], lower[3]), (100, 150,0), 2)
#     cv2.rectangle(image_process, (upper[0], upper[1]),
#                           (upper[2], upper[3]), (100, 150,0), 2)
    con_pack = font_object.eight_connectivity(image.copy(), upper,
                                              left=False, right=False)
    max_left_region = 20
    for region in con_pack:
        if len(con_pack[region]) > max_left_region:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    con_pack = font_object.eight_connectivity(image.copy(), lower,
                                              left=False, right=False)
    for region in con_pack:
        if len(con_pack[region]) > max_left_region:
            continue
        for val in con_pack[region]:
            image_process[val] = 0
    if view:
        cv2.imshow('d', image_process)
        cv2.waitKey(0)

#     con_pack = font_object.eight_connectivity(image.copy(), right,
#                                               left=False, right=False)
#     for region in con_pack:
#         for val in con_pack[region]:
#             image_process[val] = 0
#     cv2.imshow('d', image_process)
#     cv2.waitKey(0)
#     cv2.destroyAllWindows()

####

    font_object.horizontal_projection(image_process)
    al_height = start_point_h_al[1]-start_point_h_al[0]
    print('al_height:', al_height)
    h_image = font_object.detect_horizontal_line(image.copy(), al_height, 5)
    start_point_h = font_object.start_point_h
    if view:
        cv2.imshow('line', h_image)
        cv2.waitKey(0)
#     cv2.destroyAllWindows()

    return start_point_h, image_process


# #### image_processing_blok

# In[8]:


def normal_image_processing_blok(imagePath, object_result):
    original_image = cv2.imread(imagePath)
    gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    # template = cv2.Canny(gray, 50, 200)
    # Otsu threshold
    ret_img, image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY
                                   + cv2.THRESH_OTSU)
    # Simple threshold
    # ret_img, image2 = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
    # Adaptive threshold value is the mean of neighbourhood area
    # image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
    #                               cv2.THRESH_BINARY, 11, 2)

    # Adaptive threshold value is the weighted sum of neighbourhood
    # values where weights are a gaussian window
#     image = cv2.adaptiveThreshold(gray, 255,
#                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                   cv2.THRESH_BINARY, 11, 2)

    # cv2.imshow('otsu', image1)
    # cv2.imshow('simple', image2)
    # cv2.imshow('adapt mean', image3)
    # cv2.imshow('adapt gaussian', image)
    # cv2.waitKey(0)
    # image = cv2.bitwise_not(image)
    # kernel = np.ones((1,1), np.uint8)
    # dilation = cv2.dilate(final_img.copy(),kernel,iterations = 1)
    # kernel = np.ones((2,2), np.uint8)
    # image = cv2.erode(image,kernel,iterations = 1)
    # image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    # image = cv2.bitwise_not(image)
    # closing = cv2.morphologyEx(final_img.copy(), cv2.MORPH_CLOSE, kernel)
    # cv2.imshow('morph', image)
    # print('morph')
    # cv2.waitKey(0)

    input_image = match.ImageProcessing(original_image=original_image.copy())
    input_image.horizontal_projection(image.copy())  # adaptive binaryimage
    horizontal_image = input_image.detect_horizontal_line(
        image=original_image.copy(),
        pixel_limit_ste=5,  # Start to end
        pixel_limit_ets=5   # End to start
    )  # Got self.start_point_h
    # cv2.imshow('from main', input_image.original_image)
    bag_h_original = input_image.start_point_h
    input_image.crop_image(h_point=input_image.start_point_h,
                           input_image=original_image.copy())  # crop ori

#     marker_height_list = []
#     font_list = mess.font(imagePath=imagePath, image=gray)
#     for font_object in font_list:
#         for location in font_object.get_marker_location():
#             temp = cv2.imread(location)
#             h, _, _ = temp.shape
#             marker_height_list.append(h)
#     print(marker_height_list)
    # Block font processing
    count = 0
    save_state = {}
    imagelist_bag_of_h_with_baseline = []
    imagelist_image_final_body = []
    imagelist_image_final_marker = []
    imagelist_perchar_marker = []
    imagelist_final_word_img = []
    imagelist_final_segmented_char = []
    for image in input_image.bag_of_h_crop:
        # Get original cropped one line binary image
        temp_image_ori = input_image.bag_of_h_crop[image]
        h, _, _ = temp_image_ori.shape
        # Scaled image by height ratio
#         scaled_one_line_img_size = 1.3 * max(marker_height_list)
#         if h > scaled_one_line_img_size:
#             scale = scaled_one_line_img_size / h
#             temp_image_ori = imutils.resize(temp_image_ori,
#                                             height=int(h * scale))
#         else:
#             scale = 1
#         if scale != 1:
#             print('Scalling image to ' + str(scale))
#         scale = 0.9285714285714286
#         temp_image_ori = imutils.resize(temp_image_ori,
#                                             height=int(h * scale))
        scale = 1
        gray = cv2.cvtColor(temp_image_ori, cv2.COLOR_BGR2GRAY)
        temp_image = cv2.adaptiveThreshold(gray, 255,
                                           cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY, 11, 2)
        # temp_image = temp_image_ori
        # Calculate base line processing from self.h_projection
        input_image.horizontal_projection(temp_image.copy())
        input_image.base_line(one_line_image=temp_image_ori)
        oneline_baseline = []
        oneline_baseline.append(input_image.base_start)
        oneline_baseline.append(input_image.base_end)
        if oneline_baseline[1] < oneline_baseline[0]:
            temp = oneline_baseline[0]
            oneline_baseline[0] = oneline_baseline[1]
            oneline_baseline[1] = temp
        imagelist_bag_of_h_with_baseline.append(input_image.one_line_image)
#         cv2.imshow('Base start =' + str(input_image.base_start)
#                    + ' end =' + str(input_image.base_end),
#                    input_image.one_line_image)
#         print('>')
#         cv2.waitKey(0)
#         cv2.destroyWindow('Base start =' + str(input_image.base_start)
#                           + ' end =' + str(input_image.base_end))

        # Font_Processing
#         font_list = font(imagePath=imagePath, image=gray)
#         max_font_value = 0
#         font_type = 0
#         numstep = 20
        # Looking for font type by the greatest value
#         for font_object in font_list:
#             font_object.run(numstep=numstep)
#             for value in font_object.get_object_result().values():
#                 # print(value)
#                 if type(value) == float:
#                     if value > max_font_value:
#                         max_font_value = value
#                         font_type = font_object
        not_empty = False
        for data in object_result:
            if isinstance(object_result[data], type(np.array([]))):
                not_empty = True
                break

        if not_empty:
            print('into eight connectivity')
            input_image.eight_connectivity(
                temp_image.copy(), oneline_baseline
            )
            conn_pack_sorted = copy.deepcopy(
                input_image.conn_pack_sorted
            )
            conn_pack_minus_body = copy.deepcopy(
                input_image.conn_pack_minus_body
            )
            imagelist_image_final_body.append(input_image.image_final_sorted)
            imagelist_image_final_marker.append(input_image.image_final_marker)
            # font_type.display_marker_result(input_image=temp_image_ori)
        else:
            object_result = False
            print('Not a valuable result found check the numstep!')
            continue
            # cv2.waitKey(0)

        # Crop next word marker wether it's inside or beside
        crop_words = {}
        if object_result:
            # Grouping marker by its v_projection
            input_image.grouping_marker()
            group_marker_by_wall = copy.deepcopy(
                input_image.group_marker_by_wall
            )
#             print('bw:', group_marker_by_wall)
#             print('bw1:', conn_pack_sorted)
#             print('bw2:', conn_pack_minus_body)
#             print(object_result)
#             cv2.waitKey(0)
            for data in object_result:
                if isinstance(object_result[data], type(np.array([]))):
                    temp_x = object_result[data]
                    part = data.split('_')
                    name = []
                    for x in range(len(part)):
                        if x == 0:
                            continue
                        if x == len(part) - 1:
                            name.append(part[x])
                        else:
                            name.append(part[x] + '_')
                    name = ''.join(name)
                    # crop_words['ordinat_' + name]=temp_x
                    for arr in range(len(temp_x)):
                        y1 = (temp_x)[arr][1]
                        y2 = (temp_x)[arr][3]
                        if bag_h_original[image] <= y1 <= bag_h_original[image+1]:
                            #                             print('pass')
                            print('processing:', name)
                            pass
                        else:
                            #                             print('continue')
                            continue
                        x2 = (temp_x)[arr][2]  # x2 is on the right
                        x1 = (temp_x)[arr][0]  # x1 is on the left
                        width_x = x2-x1
                        mid_x = x1 + round((x2 - x1)/2)  # x in the middle
#                         print('ordinat ' + data + '={}'.format(x))
                        # marker_width = (temp_x[arr][2]) - x
                        wall_count = -1
                        for wall in group_marker_by_wall:
                            wall_count += 1
                            if wall[0] <= mid_x <= wall[1]:
                                break
#                         cv2.waitKey(0)
                        wall = group_marker_by_wall.keys()
                        wall = list(wall)
                        ####
                        # print(group_marker_by_wall, wall_count)
                        ####
                        found_in_wall = False
                        for region in group_marker_by_wall[
                                wall[wall_count]]:
                            if found_in_wall:
                                break
                            region_yx = conn_pack_minus_body[
                                region]
                            for y_x in region_yx:
                                if y_x[1] < x1 - width_x:
                                    print('add inside wall')
                                    crop_words['final_inside_' + name
                                               + '_' + str(arr)] \
                                        = wall[wall_count]
                                    crop_words['ordinat_' + name
                                               + '_' + str(arr)] \
                                        = temp_x[arr]
                                    found_in_wall = True
                                    break
                        if not found_in_wall:
                            if wall_count > 0:
                                next_wall = wall[wall_count - 1]
                                found_next_wall = False
                                if group_marker_by_wall[next_wall] != []:
                                    print('add next wall')
                                    crop_words['final_beside_'
                                               + name + '_' + str(arr)] \
                                        = next_wall
                                    crop_words['ordinat_' + name
                                               + '_' + str(arr)] \
                                        = temp_x[arr]
                                    found_next_wall = True
                                if not found_next_wall and wall_count > 1:
                                    beside_next_wall = wall[wall_count - 2]
                                    if group_marker_by_wall[
                                            beside_next_wall] != []:
                                        print('add beside next wall')
                                        crop_words['final_beside_'
                                                   + name + '_'
                                                   + str(arr)] \
                                            = beside_next_wall
                                        crop_words['ordinat_' + name
                                                   + '_' + str(arr)] \
                                            = temp_x[arr]

#             font_type.display_marker_result(input_image=temp_image_ori)

        # Looking for final segmented character
        # print(crop_words_final)
        # for key in crop_words_final:
        
        print('CROP WORDS = ', crop_words)
        for key in crop_words:
            name = key.split('_')
            if name[0] == 'final':
                save_state[count] = []
                count += 1
                # x_value = crop_words_final[key]
                x_value = crop_words[key]
                # print(x_value)
                join = []
                for x in range(len(name)):
                    if x == 0:
                        continue
                    if x == 1:
                        continue
                    if x == len(name) - 1:
                        join.append(name[x])
                        # print(name[x])
                    else:
                        join.append(name[x] + '_')
                        # print(name[x])
                join = ''.join(join)
                save_state[count-1].append(join)
                print('join = {}'.format(join))

                # List available for final segmented char
                final_segmented_char = temp_image.copy()
                final_segmented_char[:] = 255
                if name[1] == 'beside':
                    # final_img = temp_image.copy()[:, x_value[0]:x_value[1]]
                    final_img = input_image.image_join.copy()[
                        :, x_value[0]:x_value[1]]
                    w_height, w_width = final_img.shape
#                     cv2.imshow('beside', final_img)
                    final_segmented_char, pass_x1 = input_image.find_final_processed_char(
                        x_value, oneline_baseline
                    )
                    if final_segmented_char == 'continue':
                        print(
                            '>> from main to continue next word candidate'
                        )
                        continue
                    else:
                        save_state[count-1].append(scale)
                        save_state[count-1].append(bag_h_original[image])
                        save_state[count-1].append(
                            crop_words['ordinat_' + join]
                        )
                        save_state[count-1].append(final_segmented_char)
                        save_state[count-1].append(pass_x1)

                if name[1] == 'inside':
                    x1_ordinat = crop_words['ordinat_' + join][0]
                    # x1_ordinat = crop_words_final['ordinat_' + join][0]
                    # Cut before the detected char marker
#                     print('x1_ordinat = {}'.format(x1_ordinat))
#                     cv2.waitKey(0)
                    # final_img = temp_image.copy()[:, x_value[0]:x1_ordinat]
                    final_img = input_image.image_join.copy()[
                        :, x_value[0]:x1_ordinat]
                    w_height, w_width = final_img.shape
#                     cv2.imshow('inside', final_img)
                    final_wall = (x_value[0], x1_ordinat)
                    final_segmented_char, pass_x1 = input_image.find_final_processed_char(
                        final_wall, oneline_baseline
                    )
                    if final_segmented_char == 'continue':
                        print(
                            '>> from main to continue next word candidate'
                        )
                        continue
                    else:
                        save_state[count-1].append(scale)
                        save_state[count-1].append(bag_h_original[image])
                        save_state[count-1].append(
                            crop_words['ordinat_' + join]
                        )
                        save_state[count-1].append(final_segmented_char)
                        save_state[count-1].append(pass_x1)
                
                imagelist_perchar_marker.append(input_image.imagelist_perchar_marker)
                # print('_________________________________', imagelist_perchar_marker)
                imagelist_final_word_img.append(final_img)
                # print('sd', imagelist_final_word_img)
                imagelist_final_segmented_char.append(final_segmented_char)
                # print('l', imagelist_final_segmented_char)

    return save_state, imagelist_perchar_marker, imagelist_final_word_img, imagelist_final_segmented_char,\
        imagelist_bag_of_h_with_baseline, imagelist_image_final_body, imagelist_image_final_marker,\
            horizontal_image


# ## Image Processing Stage

# In[9]:


def most_frequent(List):
    return max(set(List), key=List.count)


# In[21]:


# imagePath = './temp/v1.jpg'
# img = cv2.imread(imagePath)
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
def font_list(imagePath, image, setting, markerPath):
    font_list, loc_path = mess.font(imagePath=imagePath, image=image,
                          setting=setting, markerPath=markerPath)

    return font_list, loc_path

# In[22]:


def big_blok(temp_object, imagePath, font_object, model, font_list):
    # Get the most marker
    count = -1
    temp_marker_count = {}
    for obj in temp_object:
        count += 1
        marker_count = 0
        for value in obj.values():
            if type(value) == type(np.array([])):
                marker_count += len(value)
        temp_marker_count[count] = marker_count

    max_count = 0
    max_id = 0
    for x in temp_marker_count:
        if temp_marker_count[x] > max_count:
            max_count = temp_marker_count[x]
            max_id = x

    # In[23]:
    # Get the horizontal line image by using eight connectivity
    img = cv2.imread(imagePath)
    list_start_point_h = []
    imagelist_horizontal_line_by_eight_conn = []
    continue_flag = False
    for key in temp_object[max_id].keys():
        if type(temp_object[max_id][key]) == type(np.array([])):
            split = key.split('_')
            name = get_marker_name(key)
            if split[1] == 'tanwin':
                print(name)
                for c in temp_object[max_id][key]:
                    start_point_h, image_process = eight_conn_by_seed_tanwin(
                        c, img, font_list, False)
                    imagelist_horizontal_line_by_eight_conn.append(image_process)
                    list_start_point_h.append(start_point_h)
                    print(list_start_point_h)
            else:
                print(name)
                for c in temp_object[max_id][key]:
                    start_point_h, image_process = eight_conn_by_seed(
                        c, img, font_list, False)
                    imagelist_horizontal_line_by_eight_conn.append(image_process)
                    list_start_point_h.append(start_point_h)
                    print(list_start_point_h)

    # In[24]:

    img = cv2.imread(imagePath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_copy = gray.copy()
    height, width = gray_copy.shape
    normal_processing = []
    for y_y in list_start_point_h:
        image_vo = gray[y_y[0]:y_y[1], :]
        image_v = image_vo.copy()
        font_object.vertical_projection(image_v)
        font_object.detect_vertical_line(image_v.copy(), 10)
        start_point_v = font_object.start_point_v
        print(start_point_v)
    #     for x in range(len(start_point_v)):
    #         if x % 2 == 0:
    #             cv2.line(image_v, (start_point_v[x], 0),
    #                      (start_point_v[x], height), (0, 0, 0), 2)
    #         else:
    #             cv2.line(image_v, (start_point_v[x], 0),
    #                      (start_point_v[x], height), (100, 100, 100), 2)
    #     cv2.imshow('line', image_v)
    #     print('>')
    #     cv2.waitKey(0)

        if len(start_point_v) > 5:
            # Go to the normal match
            normal_processing.append(True)
        else:
            # Just crop the next char by ratio
            normal_processing.append(False)
            print(len(start_point_v), 'is not enough')
    cv2.destroyAllWindows()

    # In[25]:

    normal_processing = most_frequent(normal_processing)
    print(normal_processing)

    # In[26]:

    img = cv2.imread(imagePath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bw_image = cv2.adaptiveThreshold(gray, 255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    height, width = gray.shape

    kernel = np.ones((3, 3), np.uint8)

    temp_gray_copy = []
    temp_image_process = []
    temp_sub_image = []
    temp_check_image = []
    temp_final_img = []
    save_state = {}
    normal_processing_result = []
    crop_ratio_processing_result = []
    if normal_processing:
        #     pass
        save_state, imagelist_perchar_marker, imagelist_final_word_img, imagelist_final_segmented_char,\
         imagelist_bag_of_h_with_baseline, imagelist_image_final_body, imagelist_image_final_marker,\
             horizontal_image = normal_image_processing_blok(imagePath, temp_object[max_id])
        # print('comeon', save_state)
        # print('f', imagelist_perchar_marker)
        # print('ddd', imagelist_final_word_img)
        # print('normal__', imagelist_final_segmented_char)
        normal_processing_result = [imagelist_perchar_marker,
                                    imagelist_final_word_img,
                                    imagelist_final_segmented_char, 
                                    imagelist_bag_of_h_with_baseline, 
                                    imagelist_image_final_body, 
                                    imagelist_image_final_marker,
                                    horizontal_image]
    else:
        arr_count = -1
        for key in temp_object[max_id].keys():
            gray_copy = gray.copy()
            bw = bw_image.copy()
            if type(temp_object[max_id][key]) == type(np.array([])):
                split = key.split('_')
                name = get_marker_name(key)
                if split[1] == 'tanwin':
                    print(name)
                    for c in temp_object[max_id][key]:
                        y1_c = c[1]
                        arr_count += 1
                        oneline_coordinat = list_start_point_h[arr_count]
                        oneline_bw_image = bw_image[oneline_coordinat[0]:
                                                    oneline_coordinat[1], :]
                        cv2.rectangle(gray_copy,
                                      (0, oneline_coordinat[0]),
                                      (width, oneline_coordinat[1]),
                                      (0, 255, 0), 2)
                        cv2.rectangle(gray_copy,
                                      (c[0], c[1]),
                                      (c[2], c[3]),
                                      (0, 255, 0), 2)
                        # cv2.imshow('check', gray_copy)
                        # cv2.waitKey(0)
                        c = region_tanwin(c, bw_image, font_list, False)
                        next_c, _ = get_lr_coordinat(c, width)
                        next_c_count = black_pixel_count(bw_image, next_c)
                        while(next_c_count < 2):
                            next_c, _ = get_lr_coordinat(next_c, width)
                            next_c_count = black_pixel_count(bw_image, next_c)
                            if next_c[0] < 1:
                                break
                        if next_c[1] > y1_c:
                            mod_c, _ = get_ul_coordinat(next_c, height)
                            next_c = [next_c[0], mod_c[1],
                                      next_c[2], next_c[3]]
                        else:
                            _, mod_c = get_ul_coordinat(next_c, height)
                            next_c = [next_c[0], next_c[1],
                                      next_c[2], mod_c[3]]
                        cv2.rectangle(gray_copy,
                                      (next_c[0], next_c[1]),
                                      (next_c[2], next_c[3]),
                                      (200, 150, 0), 2)
                        temp_height = c[3] - c[1]
                        crop_by = int(1/4 * temp_height)
                        crop_image = bw[next_c[1]+crop_by:next_c[3]  # -crop_by
                                        , next_c[0]:next_c[2]]
                        one_base = raw_baseline(crop_image.copy(), font_object)
                        cv2.rectangle(gray_copy,
                                      (0, c[1] + one_base[0]),
                                      (width, c[1] + one_base[1]),
                                      (1000, 150, 0), 2)
    #                     crop_image = cv2.morphologyEx(crop_image,
    #                                                   cv2.MORPH_OPEN, kernel)
    #                     crop_image = cv2.erode(crop_image,kernel,iterations = 1)
                        # cv2.imshow('ff', crop_image)
                        # cv2.waitKey(0)
                        h_crop, w_crop = crop_image.shape
                        base = [0, one_base[0],
                                w_crop-1, one_base[1]]
                        con_pack = font_object.eight_connectivity(crop_image, base,
                                                                  left=False, right=False)
                        image_process = crop_image.copy()
                        image_process[:] = 255
                        for region in con_pack:
                            for val in con_pack[region]:
                                image_process[val] = 0
                        # cv2.imshow('d', image_process)
                        # cv2.waitKey(0)
                        sub_image = cv2.subtract(image_process, crop_image)
                        sub_image = cv2.bitwise_not(sub_image)
    #                     final_c = [int(1/2*w_next), 0, w_crop, h_crop]
                        final_c = [0, 0, w_crop, h_crop]
                        check_img = sub_image[final_c[1]:final_c[3],
                                              final_c[0]:final_c[2]]
                        final_img = image_process[final_c[1]:final_c[3],
                                                  final_c[0]:final_c[2]]
                        dot = font_object.dot_checker(check_img)
                        if dot:
                            final_img = cv2.bitwise_and(check_img, final_img)
                            # final_img = cv2.add(check_img, final_img)
                        # cv2.imshow('final', final_img)
                        # cv2.waitKey(0)

                        save_state[arr_count] = []
                        save_state[arr_count].append(name)
                        save_state[arr_count].append(1)  # scale
                        save_state[arr_count].append(0)  # y_origin
                        save_state[arr_count].append(c)  # marker_coordinat
                        save_state[arr_count].append(final_img)
                        save_state[arr_count].append(next_c[0])

                        temp_gray_copy.append(gray_copy)
                        temp_image_process.append(image_process)
                        temp_sub_image.append(sub_image)
                        temp_check_image.append(check_img)
                        temp_final_img.append(final_img)

    #                     raw_baseline(oneline_coordinat, bw_image)
    #                     temp_height = c[3] - c[1]
    #                     crop_by = int(1/4 * temp_height)
    #                     crop_image = bw_image[c[1]+crop_by:c[3]#-crop_by
    #                                           , c[0]:c[2]]
    #                     one_base = raw_baseline(crop_image)
    #                     cv2.rectangle(gray_copy,
    #                                   (0, c[1] + one_base[0]),
    #                                   (width, c[1] + one_base[1]),
    #                                   (1000, 150,0), 2)

    #                     base = [0, one_base[0],
    #                             width, one_base[1]]
    #                     con_pack = font_object.eight_connectivity(oneline_bw_image, base,
    #                                               left=False, right=False)
    #                     image_process = oneline_bw_image.copy()
    #                     image_process[:] = 255
    #                     for region in con_pack:
    #                         for val in con_pack[region]:
    #                             image_process[val] = 0
    #                     cv2.imshow('d', image_process)
    #                     cv2.waitKey(0)

    #                     font_object.modified_eight_connectivity(oneline_bw_image, one_base)
    #                     font_object.grouping_marker()

    #                     cv2.imshow('image final marker', font_object.image_final_marker)
    #                     cv2.imshow('image final body', font_object.image_final_sorted)
    #                     cv2.waitKey(0)
                else:
                    print(name)
                    for c in temp_object[max_id][key]:
                        arr_count += 1
                        oneline_coordinat = list_start_point_h[arr_count]
                        oneline_bw_image = bw_image[oneline_coordinat[0]:
                                                    oneline_coordinat[1], :]
                        cv2.rectangle(gray_copy,
                                      (0, oneline_coordinat[0]),
                                      (width, oneline_coordinat[1]),
                                      (0, 255, 0), 2)
                        cv2.rectangle(gray_copy,
                                      (c[0], c[1]),
                                      (c[2], c[3]),
                                      (0, 255, 0), 2)
                        # cv2.imshow('check', gray_copy)
                        # cv2.waitKey(0)
                        next_c, _ = get_lr_coordinat(c, width)
                        next_c_count = black_pixel_count(bw_image, next_c)
                        while(next_c_count < 2):
                            next_c, _ = get_lr_coordinat(next_c, width)
                            next_c_count = black_pixel_count(bw_image, next_c)
                            if next_c[0] < 1:
                                break
                        mod_c, _ = get_lr_coordinat(next_c, width)
                        w_next = mod_c[2] - mod_c[0]
                        next_c = [next_c[0] - int(1/2*w_next), next_c[1],
                                  next_c[2], next_c[3]]
                        cv2.rectangle(gray_copy,
                                      (next_c[0], next_c[1]),
                                      (next_c[2], next_c[3]),
                                      (200, 150, 0), 2)
                        temp_height = c[3] - c[1]
                        crop_by = int(1/4 * temp_height)
                        crop_image = bw[next_c[1]+crop_by:next_c[3]  # -crop_by
                                        , next_c[0]:next_c[2]]
                        one_base = raw_baseline(crop_image.copy(), font_object)
                        cv2.rectangle(gray_copy,
                                      (0, c[1] + one_base[0]),
                                      (width, c[1] + one_base[1]),
                                      (1000, 150, 0), 2)
    #                     crop_image = cv2.morphologyEx(crop_image,
    #                                                   cv2.MORPH_OPEN, kernel)
    #                     crop_image = cv2.erode(crop_image,kernel,iterations = 1)
                        # cv2.imshow('ff', crop_image)
                        # cv2.waitKey(0)
                        h_crop, w_crop = crop_image.shape
                        base = [0, one_base[0],
                                w_crop-1, one_base[1]]
                        con_pack = font_object.eight_connectivity(crop_image, base,
                                                                  left=False, right=False)
                        image_process = crop_image.copy()
                        image_process[:] = 255
                        for region in con_pack:
                            for val in con_pack[region]:
                                image_process[val] = 0
                        # cv2.imshow('d', image_process)
                        # cv2.waitKey(0)
                        sub_image = cv2.subtract(image_process, crop_image)
                        sub_image = cv2.bitwise_not(sub_image)
                        final_c = [int(1/2*w_next), 0, w_crop, h_crop]
                        check_img = sub_image[final_c[1]:final_c[3],
                                              final_c[0]:final_c[2]]
                        final_img = image_process[final_c[1]:final_c[3],
                                                  final_c[0]:final_c[2]]
                        dot = font_object.dot_checker(check_img)
                        if dot:
                            print('dot')
                            final_img = cv2.bitwise_and(final_img, check_img)
                            # final_img = cv2.add(final_img, check_img)
                        # cv2.imshow('final', final_img)
                        # cv2.waitKey(0)

                        save_state[arr_count] = []
                        save_state[arr_count].append(name)
                        save_state[arr_count].append(1)  # scale
                        save_state[arr_count].append(0)  # y_origin
                        save_state[arr_count].append(c)  # marker_coordinat
                        save_state[arr_count].append(final_img)
                        save_state[arr_count].append(
                            next_c[0] + int(1/2*w_next))
                
                        temp_gray_copy.append(gray_copy)
                        temp_image_process.append(image_process)
                        temp_sub_image.append(sub_image)
                        temp_check_image.append(check_img)
                        temp_final_img.append(final_img)

        # temp_image_process = eight conn result on baseline
        # check image = sub_image cutted
        crop_ratio_processing_result = [temp_gray_copy,
                                        temp_image_process,
                                        temp_sub_image,
                                        temp_check_image,
                                        temp_final_img]
    #                     raw_baseline(oneline_coordinat, bw_image)
    #                     temp_height = c[3] - c[1]
    #                     crop_by = int(1/4 * temp_height)
    #                     crop_image = bw_image[c[1]+crop_by:c[3]#-crop_by
    #                                           , c[0]:c[2]]
    #                     one_base = raw_baseline(crop_image)
    #                     cv2.rectangle(gray_copy,
    #                                   (0, c[1] + one_base[0]),
    #                                   (width, c[1] + one_base[1]),
    #                                   (1000, 150,0), 2)

    #                     base = [0, one_base[0],
    #                             width, one_base[1]]
    #                     con_pack = font_object.eight_connectivity(oneline_bw_image, base,
    #                                               left=False, right=False)
    #                     image_process = oneline_bw_image.copy()
    #                     image_process[:] = 255
    #                     for region in con_pack:
    #                         for val in con_pack[region]:
    #                             image_process[val] = 0
    #                     cv2.imshow('d', image_process)
    #                     cv2.waitKey(0)

    #                     font_object.modified_eight_connectivity(oneline_bw_image, one_base)
    #                     font_object.grouping_marker()

    #                     cv2.imshow('image final marker', font_object.image_final_marker)
    #                     cv2.imshow('image final body', font_object.image_final_sorted)
    #                     cv2.waitKey(0)

    #             cv2.imshow('check', gray_copy)
    #             cv2.waitKey(0)
    # print(save_state)
    # cv2.destroyAllWindows()

    # ## Final Recognition Stage
    # In[18]:

    iqlab = [1]
    idgham_bigunnah = [23, 24, 25, 27]
    idgham_bilagunnah = [9, 22]
    idzhar_halqi = [0, 26, 17, 18, 5, 6]
    ikhfa_hakiki = [2, 3, 4, 7, 8, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21]
    ikhfa_syafawi = [1]
    idgham_mimi = [23]
    idzhar_syafawi = [23, 1]  # NOT
    font_text = cv2.FONT_HERSHEY_PLAIN
    WHITE = (255, 0, 0)
    GREEN = (0, 255, 0)

    # In[27]:

    original_image = cv2.imread(imagePath)
    # save_state = image_processing_blok(imagePath)
    #     print(save_state)
    # Final segmented char recognition
    char_recog = []
    for x in save_state:
        if len(save_state[x]) < 2:
            continue
        # cv2.imshow('save state image', save_state[x][4])
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        start_point = detect_horizontal_line(
            horizontal_projection(save_state[x][4]), 0, 50)
    #     print(x)
        print(start_point)
        cut_image = save_state[x][4][start_point[0]:start_point[1], :]
    #     cv2.imshow('r', cut_image)
    #     cv2.waitKey(0)
    #     cv2.destroyAllWindows()
        # DD
        image_32_dd = cv2.resize(cut_image, (32, 32))
        # DK
    #         square_img = concat_image(cut_image)
    #         image_32_dk = cv2.resize(square_img, (32, 32))
    #         plt.figure(x)
    #         plt.imshow(image_32_dd, cmap='gray')
    #         char_recog.append(image_32_dk)
        char_recog.append(image_32_dd)

    if len(save_state) > 0:
        char_recog = np.array(char_recog)
        char_recog = char_recog.reshape(-1, 32, 32, 1).astype(np.float32)/255

        y_pred = model.predict(char_recog)
        y_pred = np.argmax(y_pred, axis=1)

    count = -1
    for x in save_state:
        if len(save_state[x]) < 2:
            continue
        count += 1
        h, w = save_state[x][4].shape
        marker = save_state[x][0].split('_')
        if isinstance(save_state[x][3], type([])):
            marker_coordinat = np.array(save_state[x][3])
        elif isinstance(save_state[x][3], type(np.array([]))):
            marker_coordinat = save_state[x][3]
        char_box = marker_coordinat / save_state[x][1]
    #         final_box = [
    #             int(char_box[0]) - int(w / save_state[x][1]),
    #             int(char_box[1]) + save_state[x][2], int(char_box[2]),
    #             int(char_box[3]) + save_state[x][2] + int(char_box[3]) - int(char_box[1])
    #         ]
    #     final_box = [
    #         int(save_state[x][5] / save_state[x][1]),
    #         save_state[x][2], int(char_box[2]),
    #         int(char_box[3]) + save_state[x][2]
    #     ]
        final_box = [
            int(save_state[x][5] / save_state[x][1]),
            int(char_box[1]),
            int(char_box[2]), int(char_box[3])
        ]
        found = False
        if marker[0] == 'nun' or marker[0] == 'tanwin':
            if y_pred[count] == iqlab[0]:
                cv2.rectangle(original_image, (final_box[0], final_box[1]),
                              (final_box[2], final_box[3]), GREEN, 2)
                cv2.putText(original_image, 'iqlab',
                            (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                print('iqlab')
                continue
            for c in idgham_bilagunnah:
                if y_pred[count] == c:
                    print('idgham bilagunnah')
                    cv2.rectangle(original_image, (final_box[0], final_box[1]),
                                  (final_box[2], final_box[3]), GREEN, 2)
                    cv2.putText(original_image, 'idgham bilagunnah',
                                (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                    found = True
                    break
            if found:
                continue
            for c in idgham_bigunnah:
                if y_pred[count] == c:
                    print('idgham bigunnah')
                    cv2.rectangle(original_image, (final_box[0], final_box[1]),
                                  (final_box[2], final_box[3]), GREEN, 2)
                    cv2.putText(original_image, 'idgham bigunnah',
                                (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                    found = True
                    break
            if found:
                continue
            for c in idzhar_halqi:
                if y_pred[count] == c:
                    print('idzhar halqi')
                    cv2.rectangle(original_image, (final_box[0], final_box[1]),
                                  (final_box[2], final_box[3]), GREEN, 2)
                    cv2.putText(original_image, 'idzhar halqi',
                                (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                    found = True
                    break
            if found:
                continue
            for c in ikhfa_hakiki:
                if y_pred[count] == c:
                    print('ikhfa hakiki')
                    cv2.rectangle(original_image, (final_box[0], final_box[1]),
                                  (final_box[2], final_box[3]), GREEN, 2)
                    cv2.putText(original_image, 'ikhfa hakiki',
                                (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                    found = True
                    break
            if found:
                continue

        elif marker[0] == 'mim':
            if y_pred[count] == ikhfa_syafawi[0]:
                print('ikfha syafawi')
                cv2.rectangle(original_image, (final_box[0], final_box[1]),
                              (final_box[2], final_box[3]), GREEN, 2)
                cv2.putText(original_image, 'ikhfa syafawi',
                            (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                continue
            elif y_pred[count] == idgham_mimi[0]:
                print('idgham mimi')
                cv2.rectangle(original_image, (final_box[0], final_box[1]),
                              (final_box[2], final_box[3]), GREEN, 2)
                cv2.putText(original_image, 'idgham mimi',
                            (final_box[0], final_box[3] + 5), font_text, 1, WHITE)
                continue
            else:
                print('idzhar syafawi')
                cv2.rectangle(original_image, (final_box[0], final_box[1]),
                              (final_box[2], final_box[3]), GREEN, 2)
                cv2.putText(original_image, 'idzhar syafawi',
                            (final_box[0], final_box[3] + 5), font_text, 1, WHITE)

    # cv2.imshow('Final Result', original_image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    final_image_result = original_image


    return final_image_result, normal_processing_result, crop_ratio_processing_result, imagelist_horizontal_line_by_eight_conn


# ### DONE
