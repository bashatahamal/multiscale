# import argparse
import matplotlib.pyplot as plt
import numpy as np
import imutils
import glob
import cv2
import copy

# Argument parser
# ap = argparse.ArgumentParser()
# ap.add_argument(
#     "-t", "--template", required=True, help="Path to template image")
# ap.add_argument(
#     "-i", "--images", required=True, help="Path to matched images")
# ap.add_argument(
#     "-v", "--visualize", help="Flag indicating to visualize each iteration")
# args = vars(ap.parse_args())


class Marker:
    def __init__(self, **kwargs):
        self._Data = kwargs

    def get_template_location(self):
        return self._Data["template_loc"]
    # def get_image_location(self):
    #     return self._Data["image_loc"]

    def get_template_thresh(self):
        return self._Data["template_thresh"]

    def get_nms_thresh(self):
        return self._Data["nms_thresh"]

    def get_image(self):
        return self._Data["image"]

    def non_max_suppression_slow(self, boxes, overlapThresh):
        # if there are no boxes, return an empty list
        if len(boxes) == 0:
            return []

        # initialize the list of picked indexes
        pick = []

        # grab the coordinates of the bounding boxes
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]

        # compute the area of the bounding boxes and sort the bounding
        # boxes by the bottom-right y-coordinate of the bounding box
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)

        # keep looping while some indexes still remain in the indexes
        # list
        while len(idxs) > 0:
            # grab the last index in the indexes list, add the index
            # value to the list of picked indexes, then initialize
            # the suppression list (i.e. indexes that will be deleted)
            # using the last index
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            suppress = [last]

            # loop over all indexes in the indexes list
            for pos in range(0, last):
                # grab the current index
                j = idxs[pos]

                # find the largest (x, y) coordinates for the start of
                # the bounding box and the smallest (x, y) coordinates
                # for the end of the bounding box
                xx1 = max(x1[i], x1[j])
                yy1 = max(y1[i], y1[j])
                xx2 = min(x2[i], x2[j])
                yy2 = min(y2[i], y2[j])

                # compute the width and height of the bounding box
                w = max(0, xx2 - xx1 + 1)
                h = max(0, yy2 - yy1 + 1)

                # compute the ratio of overlap between the computed
                # bounding box and the bounding box in the area list
                overlap = float(w * h) / area[j]

                # if there is sufficient overlap, suppress the
                # current bounding box
                if overlap > overlapThresh:
                    suppress.append(pos)

            # delete all indexes from the index list that are in the
            # suppression list
            idxs = np.delete(idxs, suppress)

        # return only the bounding boxes that were picked
        return boxes[pick]

    def match_template(self, visualize=False, numstep=100):
        # Get template
        # print('.')
        template = cv2.imread(self.get_template_location())
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        # Canny edge
        # template = cv2.Canny(template, 50, 200)
        # Otsu threshold
        # ret_temp, template = cv2.threshold(template, 0, 255,
        #                                    cv2.THRESH_BINARY
        #                                    + cv2.THRESH_OTSU)
        # Simple threshold
        # ret_temp, template = cv2.threshold(template, 127, 255,
        #                                    cv2.THRESH_BINARY)
        # Adaptive threshold value is the mean of neighbourhood area
        # template = cv2.adaptiveThreshold(template, 255,
        #                                  cv2.ADAPTIVE_THRESH_MEAN_C,
        #                                  cv2.THRESH_BINARY,
        #                                  11, 2)
        # Adaptive threshold value is the weighted sum of neighbourhood values
        # where weights are a gaussian window
        template = cv2.adaptiveThreshold(template, 255,
                                         cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY,
                                         11, 2)
        # cv2.imshow("Template", template)
        (tH, tW) = template.shape[:2]

        # Get image
        # image = cv2.imread(self.get_image_location())
        # print(self.get_image_location())
        # self.image=image
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('gray', gray)
        image = self.get_image()
        # boundingBoxes = np.ones((1,4), dtype=int)
        boundingBoxes = []
        max_value_list = []
        # print(numstep)
        # Loop over scaled image (start stop numstep) from the back
        for scale in np.linspace(0.2, 2.0, numstep)[::-1]:
            resized = imutils.resize(image, width=int(image.shape[1] * scale))
            r = image.shape[1] / float(resized.shape[1])
            # If resized image smaller than template, then break the loop
            if resized.shape[0] < tH or resized.shape[1] < tW:
                break

            # Preprocessing resized image and then apply template matching
            # Cannyedge
            # edged = cv2.Canny(resized, 50, 200)
            # Otsu threshold
            # ret_img, resized = cv2.threshold(resized, 0, 255,
            #                                  cv2.THRESH_BINARY
            #                                  + cv2.THRESH_OTSU)
            # Simple threshold
            # ret_img, resized = cv2.threshold(resized, 127, 255,
            #                                  cv2.THRESH_BINARY)
            # Adaptive threshold value is the mean of neighbourhood area
            # resized = cv2.adaptiveThreshold(resized, 255,
            #                                 cv2.ADAPTIVE_THRESH_MEAN_C,
            #                                 cv2.THRESH_BINARY, 11, 2)
            # Adaptive threshold value is the weighted sum of neighbourhood
            # values where weights are a gaussian window
            resized = cv2.adaptiveThreshold(resized, 255,
                                            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 11, 2)
            result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
            (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
            if visualize:
                # clone = np.dstack([edged, edged, edged])
                clone = np.dstack([resized, resized, resized])
                print(self.get_template_location())
                print(maxVal)
                cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
                              (maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
                cv2.imshow("Visualizing", clone)
                cv2.waitKey(0)

            if maxVal > self.get_template_thresh():
                (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
                (endX, endY) = (int((maxLoc[0] + tW) * r),
                                int((maxLoc[1] + tH) * r))
                temp = [startX, startY, endX, endY]
                # boundingBoxes = np.append(boundingBoxes, [temp], axis=0)
                # max_value_list = np.append(max_value_list, [maxVal], axis=0)
                boundingBoxes.append(temp)
                max_value_list.append(maxVal)
                # print("Max val = {} location {}".format(maxVal, temp))

        # If detected on this scale size
        # if len(boundingBoxes) > 1:
        #     boundingBoxes = np.delete(boundingBoxes, 0, axis=0)
            # print("{} {}".format(len(pick), self.get_template_location()))
            # print(pick)
            # for (startX, startY, endX, endY) in pick:
            #     cv2.rectangle(image, (startX, startY),(endX, endY),
            #     (0, 255, 0), 2)
        boundingBoxes = np.array(boundingBoxes)
        pick = self.non_max_suppression_slow(boundingBoxes,
                                             self.get_nms_thresh())

        if len(max_value_list) > 1:
            max_local_value = max(max_value_list)
        if len(max_value_list) == 1:
            max_local_value = max_value_list
        if max_value_list == []:
            pick = 0
            max_local_value = 0
        # cv2.imshow('IMAGE MATCH ()',image)
        return pick, max_local_value


class FontWrapper(Marker):
    def __init__(self, nms_thresh=0.3, visualize=False, **kwargs):
        # print("INIT!")
        self._Data = kwargs
        self.nms_thresh = nms_thresh
        self.visualize = visualize

        self.image_location = self._Data["image_loc"]
        self.marker_location = self._Data["loc_list"]
        self.marker_thresh = self._Data["thresh_list"]
        self.image = self._Data["image"]

        for data in self._Data:
            if data == 'numstep':
                self.numstep = self._Data["numstep"]
            else:
                self.numstep = 0
            # self.key = self._Data[data]
            # print(type(self.data))
        # print(self.key)

        self.pocket = {}
        # super().__init__()
        colour_tanwin = [
            (255, 0, 255), (0, 0, 255), (128, 0, 128),
            (0, 0, 128)
        ]
        colour_nun = [
            (255, 0, 0), (128, 0, 0), (255, 99, 71),
            (220, 20, 60), (139, 0, 0)
        ]
        colour_mim = [
            (154, 205, 50), (107, 142, 35), (85, 107, 47),
            (0, 128, 0), (34, 139, 34)
        ]
        t = 0
        m = 0
        n = 0
        self.temp_colour = self.get_marker_thresh().copy()
        for key in self.get_marker_thresh().keys():
            # print(key)
            x = key.split('_')
            if x[0] == 'tanwin':
                self.temp_colour[key] = colour_tanwin[t]
                if t+1 > len(colour_tanwin) - 1:
                    t = 0
                else:
                    t += 1
            if x[0] == 'nun':
                self.temp_colour[key] = colour_nun[n]
                if n+1 > len(colour_nun) - 1:
                    n = 0
                else:
                    n += 1
            if x[0] == 'mim':
                self.temp_colour[key] = colour_mim[m]
                if m+1 > len(colour_mim) - 1:
                    m = 0
                else:
                    m += 1
        # print(self.temp_colour)
        # tanwin = 0
        # nun    = 0
        # mim    = 0
        # for key in self.get_marker_thresh().keys():
        #     x = key.split('_')
        #     if x[0] == 'tanwin':
        #         tanwin+=1
        #     if x[0] == 'nun':
        #         nun+=1
        #     if x[0] == 'mim':
        #         mim+=1
        # print('Tanwin {} nun {} mim {}'.format(tanwin, nun, mim))
        # self.pick_colour  =[]
        # reserved_tanwin = tanwin
        # reserved_nun    = nun
        # reserved_mim    = mim
        # for x in range(len(self.get_marker_thresh())):
        #     if reserved_tanwin <= len(colour_tanwin):
        #         if tanwin > 0:
        #             self.pick_colour.append(colour_tanwin[tanwin-1])
        #             tanwin-=1
        #             # print(tanwin)
        #     else :
        #         if tanwin > 0:
        #             self.pick_colour.append(colour_tanwin[0])
        #             tanwin-=1
        #     if reserved_nun <= len(colour_nun):
        #         if tanwin <= 0 and nun > 0:
        #             self.pick_colour.append(colour_nun[nun-1])
        #             nun-=1
        #     else:
        #         if tanwin <= 0 and nun > 0:
        #             self.pick_colour.append(colour_nun[0])
        #             nun-=1
        #     if reserved_mim <= len(colour_mim):
        #         if nun <= 0 and mim > 0:
        #             self.pick_colour.append(colour_mim[mim-1])
        #             mim-=1
        #     else:
        #         if nun <= 0 and mim > 0:
        #             self.pick_colour.append(colour_mim[0])
        #             mim-=1
        # print(self.pick_colour)

    def get_marker_thresh(self):
        return self.marker_thresh

    def get_marker_location(self):
        return self.marker_location

    # def get_image_location(self):
    #     return self.image_location

    # def get_original_image(self):
    #     original_image = cv2.imread(self.get_image_location())
    #     return original_image

    def get_object_result(self):
        return self.pocket

    def get_image(self):
        return self.image

    def get_object_name(self):
        return self.get_marker_location()[0].split('/')[2]

    def display_marker_result(self, input_image):
        # rectangle_image = self.get_original_image()
        rectangle_image = input_image.copy()
        found = False
        for key in self.get_marker_thresh().keys():
            if isinstance(self.get_object_result()['box_' + key],
                          type(np.array([]))):
                for (startX, startY, endX, endY) in \
                        self.get_object_result()['box_' + key]:
                    cv2.rectangle(rectangle_image, (startX, startY),
                                  (endX, endY), self.temp_colour[key], 2)
                # print(self.pick_colour[x])
                found = True
        if found:
            print('<<<<<<<< View Result >>>>>>>>')
            cv2.imshow("Detected Image_" + self.get_object_name(),
                       rectangle_image)
        else:
            cv2.imshow("Original Image", rectangle_image)
            print('not found')
        print('>')
        cv2.waitKey(0)
        # cv2.destroyWindow("Detected Image_" + self.get_object_name())

    def run(self, view=False, numstep=100):
        # Tanwin
        # print(self.get_marker_thresh())
        print('run() Marker Font')

        # gray = cv2.cvtColor(self.get_original_image(), cv2.COLOR_BGR2GRAY)
        if self.numstep == 0:
            numstep = numstep
        else:
            numstep = self.numstep
        print("numstep = ", numstep)
        pocketData = {}
        for x in range(len(self.get_marker_thresh())):
            # print(len(template_thresh))
            # print(list(template_thresh.values())[x])
            super().__init__(image=self.get_image,
                             template_thresh=list(
                                 self.get_marker_thresh().values())[x],
                             template_loc=self.get_marker_location()[x],
                             nms_thresh=self.nms_thresh)
            (pocketData[x], pocketData[x+len(self.get_marker_thresh())]) \
                = super().match_template(visualize=self.visualize,
                                         numstep=numstep)
            # print(type(pocketData[x]))

        for x in range(len(self.get_marker_thresh())):
            temp = list(self.get_marker_thresh().keys())[x]
            # box = 'box_'+ temp
            self.get_object_result()[temp] = pocketData[
                x+len(self.get_marker_thresh())]
            self.get_object_result()['box_' + temp] = pocketData[x]

        if view:
            self.display_marker_result()

        # return pocket


def font(imagePath, image):
    # LPMQ_Font
    # print("LPMQ")
    loc_list_LPMQ = sorted(glob.glob('./marker/LPMQ/*.png'))
    font_LPMQ = FontWrapper(thresh_list={'tanwin_1': 0.7, 'tanwin_2': 0.7,
                                         'nun_stand': 0.53, 'nun_beg_1': 0.7,
                                         'nun_beg_2': 0.7, 'nun_mid': 0.7,
                                         'nun_end': 0.7, 'mim_stand': 0.7,
                                         'mim_beg': 0.8, 'mim_mid': 0.7,
                                         'mim_end_1': 0.7, 'mim_end_2': 0.7},
                            loc_list=loc_list_LPMQ, image_loc=imagePath,
                            image=image, visualize=False, nms_thresh=0.3,
                            numstep=30)
    # AlQalam_Font
    # print("AlQalam")
    loc_list_AlQalam = sorted(glob.glob('./marker/AlQalam/*.png'))
    font_AlQalam = FontWrapper(thresh_list={'tanwin_1': 0.7, 'tanwin_2': 0.56,
                                            'nun_stand': 0.8, 'nun_beg': 0.7,
                                            'nun_mid': 0.7, 'nun_end': 0.7,
                                            'mim_stand': 0.7, 'mim_beg': 0.7,
                                            'mim_mid': 0.7, 'mim_end': 0.7},
                               loc_list=loc_list_AlQalam, image_loc=imagePath,
                               image=image, visualize=False, nms_thresh=0.3)
    # meQuran_Font
    # print("meQuran")
    loc_list_meQuran = sorted(glob.glob('./marker/meQuran/*.png'))
    font_meQuran = FontWrapper(thresh_list={'tanwin_1': 0.7, 'tanwin_2': 0.65,
                                            'nun_stand': 0.7, 'nun_beg_1': 0.7,
                                            'nun_beg_2': 0.7, 'nun_mid': 0.7,
                                            'nun_end': 0.7, 'mim_stand': 0.7,
                                            'mim_beg': 0.7, 'mim_mid': 0.7,
                                            'mim_end_1': 0.7, 'mim_end_2': 0.68},
                               loc_list=loc_list_meQuran, image_loc=imagePath,
                               image=image, visualize=False, nms_thresh=0.3)
    # PDMS_Font
    # print("PDMS")
    loc_list_PDMS = sorted(glob.glob('./marker/PDMS/*.png'))
    font_PDMS = FontWrapper(thresh_list={'tanwin_1': 0.7, 'tanwin_2': 0.7,
                                         'nun_stand': 0.7, 'nun_beg': 0.65,
                                         'nun_mid': 0.7, 'nun_end': 0.7,
                                         'mim_stand': 0.7, 'mim_beg': 0.7,
                                         'mim_mid': 0.7, 'mim_end': 0.65},
                            loc_list=loc_list_PDMS, image_loc=imagePath,
                            image=image, visualize=False, nms_thresh=0.3)

    list_object_font = [font_LPMQ, font_AlQalam, font_meQuran, font_PDMS]

    return list_object_font


class ImageProcessing():
    def __init__(self, **kwargs):
        # print('init')
        self._Data = kwargs
        self.original_image = self._Data['original_image']
        self.height, self.width, _ = self.original_image.shape
        # Instance variable list
        # self.v_projection = 0
        # self.h_projection = 0
        # self.start_point_h = []
        # self.start_point_v = []
        # self.base_start = 0
        # self.base_end = 0
        # self.bag_of_h_crop
        # self.bag_of_v_crop

    def vertical_projection(self, image_v):
        image = image_v.copy()
        # cv2.imshow('doing v_projection', image)
        # print(len(image))
        image[image < 127] = 1
        image[image >= 127] = 0
        self.v_projection = np.sum(image, axis=0)

        return self.v_projection

    def horizontal_projection(self, image_h):
        image = image_h.copy()
        # cv2.imshow('h', image)
        image[image < 127] = 1
        image[image >= 127] = 0
        self.h_projection = np.sum(image, axis=1)

        return self.h_projection

    def detect_horizontal_line(self):
        # Detect line horizontal
        h_projection = self.h_projection
        up_flag = 0
        down_flag = 0
        pixel_limit = 5
        start_to_end = 0
        end_to_start = 0
        start_point = []
        for x in range(len(h_projection)):
            if h_projection[x] == 0 and up_flag == 1:
                start_point.append(x)
                down_flag = 1
                up_flag = 0

            if up_flag == 1:
                start_to_end += 1
            else:
                start_to_end = 0

            if down_flag == 1:
                end_to_start += 1
                # print(end_to_start)
            else:
                end_to_start = 0

            if h_projection[x] > 0 and up_flag == 0:
                # if count>=pixel_limit
                start_point.append(x)
                if down_flag == 1 and end_to_start < pixel_limit:
                    del(start_point[len(start_point)-1])
                    del(start_point[len(start_point)-1])
                    # print('delete')
                # print(count)
                up_flag = 1
                down_flag = 0
        self.start_point_h = start_point

        # Even is begining of line and Odd is end of line
        for x in range(len(start_point)):
            # cv2.line(original_image, (0, start_point[x]), (len(v_projection),
            #          start_point[x]), (0, 0, 255), 2)
            # print(x)
            if x % 2 == 0:     # Start_point
                cv2.line(self.original_image, (0, start_point[x]),
                         (self.width, start_point[x]), (0, 0, 255), 2)
                # print(x)
            else:         # End_point
                cv2.line(self.original_image, (0, start_point[x]),
                         (self.width, start_point[x]), (255, 0, 0), 2)
        # cv2.imshow('line', self.original_image)
        # cv2.waitKey(0)

    def base_line(self, one_line_image):
        h_projection = self.h_projection
        # print(h_projection)
        # original_image = one_line_image
        self.one_line_image = one_line_image
        # print(h_projection)
        diff = [0]
        for x in range(len(h_projection)):
            if x > 0:
                temp_diff = abs(int(h_projection[x]) - int(h_projection[x-1]))
                diff.append(temp_diff)

        temp = 0
        for x in range(len(diff)):
            if diff[x] > temp:
                temp = diff[x]
                self.base_end = x

        temp = 0
        for x in range(len(diff)):
            if x == self.base_end:
                continue
            if diff[x] > temp:
                temp = diff[x]
                self.base_start = x
        # self.base_start = base_start
        # self.base_end = base_end
        cv2.line(self.one_line_image, (0, self.base_start),
                 (self.width, self.base_start), (0, 255, 0), 2)
        cv2.line(self.one_line_image, (0, self.base_end),
                 (self.width, self.base_end), (0, 255, 0), 2)

    def detect_vertical_line(self, v_projection, image):
        # Detect line vertical
        # v_projection = self.v_projection
        # print(v_projection)
        original_image = image.copy()
        up_flag = 0
        down_flag = 0
        pixel_limit_v = 8
        start_to_end_v = 0
        start_point_v = []
        for x in range(len(v_projection)):
            if v_projection[x] > 0 and up_flag == 0:
                start_point_v.append(x)
                up_flag = 1
                down_flag = 0

            if v_projection[x] > 0 and down_flag == 0:
                start_to_end_v += 1

            if v_projection[x] == 0 and up_flag == 1:
                start_point_v.append(x)
                # print(start_to_end_v)
                if start_to_end_v < pixel_limit_v:
                    del(start_point_v[len(start_point_v) - 1])
                    del(start_point_v[len(start_point_v) - 1])
                    # print(start_to_end_v)
                    print('delete')
                start_to_end_v = 0
                up_flag = 0
                down_flag = 1

        self.start_point_v = start_point_v
        # print(start_point_v)
        # Even is begining of line and Odd is end of line
        for x in range(len(start_point_v)):
            if x % 2 == 0:
                cv2.line(original_image, (start_point_v[x], 0),
                         (start_point_v[x], self.height), (0, 0, 0), 2)
            else:
                cv2.line(original_image, (start_point_v[x], 0),
                         (start_point_v[x], self.height), (0, 0, 0), 2)

        cv2.imshow('line', original_image)
        print('>')
        cv2.waitKey(0)
        # print(start_point_v)

    def crop_image(self, input_image, h_point=False, v_point=False):
        if h_point:
            start_point = h_point
            # if input_image!=False:
            original_image = input_image
            # cv2.imshow('crop', original_image)
            print('>')
            cv2.waitKey(0)
            # else:
            #     original_image = self.original_image
            # print(start_point)
            bag_of_h_crop = {}
            for x in range(len(start_point)):
                if x + 2 > len(start_point):
                    # print('x')
                    continue
                if x % 2 == 0:
                    bag_of_h_crop[x] = original_image[
                                        start_point[x]:start_point[x+1], :]
            # print(bag_of_h_crop)
            for image in bag_of_h_crop:
                cv2.imshow('bag_h'+str(image), bag_of_h_crop[image])
                print('>')
                cv2.waitKey(0)
                cv2.destroyWindow('bag_h'+str(image))
            self.bag_of_h_crop = bag_of_h_crop

        if v_point:
            start_point_v = v_point
            # if input_image!=False:
            original_image = input_image
            # else:
            #     original_image = self.original_image
            bag_of_v_crop = {}
            count = 0
            for image in bag_of_h_crop:
                # print(image)
                # y = int(image/2)
                for x in range(len(start_point_v)):
                    # print('inside loop')
                    # print(image)
                    count += 1
                    if x % 2 == 0:
                        x1 = start_point[image]
                        x2 = start_point[image+1]
                        y1 = start_point_v[x]
                        y2 = start_point_v[x+1]
                        bag_of_v_crop[count] = original_image[x1:x2, y1:y2]
                    # print(x1,'_', x2,'_', y1,'_', y2)

            for image in bag_of_v_crop:
                cv2.imshow('Crop Result', bag_of_v_crop[image])
                print('>')
                cv2.waitKey(0)
                # cv2.destroyAllWindows()
            self.bag_of_v_crop = bag_of_v_crop

    def eight_conectivity(self, image, visualize=True):
        # image = cv2.bitwise_not(image)
        height, width = image.shape
        # print('eight conectivity')
        # cv2.imshow('eight', image)
        # cv2.waitKey(0)
        # print(image)
        print('height= {}, width= {}'. format(height, width))
        # print(len(image))
        self.conn_pack = {}
        reg = 1
        connected = True
        count = 0
        # self.conn_pack['region_' + str(reg)] = set()
        region = {}
        # for x in range(width):
        #     for y in range(height):
        #         if region != {}:
        #             for x in region:
        #                 if (x,y) == x:
        #                     continue 
        #         x_y = []
        #         flag = False
        #         while(True):
        #             if x_y != []:
        #                 for c in range(count):
        #                     x_loop = c
        #                     y_l = x_y[0][0]
        #                     x_l = x_y[0][1]
        #                     print('y= {}'.format(y))
        #                     cv2.waitKey(0)

        #                     # Left
        #                     if x_l - 1 > 0:
        #                         if y_l + 1 < height:
        #                             if image[y_l + 1, x_l - 1] == 0:
        #                                 x_y.append((y_l + 1, x_l - 1))

        #                     if image[y_l, x_l - 1] == 0:
        #                         x_y.append((y_l, x_l - 1))
        #                     if y_l - 1 > 0:
        #                         if image[y_l - 1, x_l - 1] == 0:
        #                             x_y.append((y_l - 1, x_l - 1))
        #                     # Middle
        #                     if y_l + 1 < height:
        #                         if image[y_l + 1, x_l] == 0:
        #                             x_y.append((y_l + 1, x_l))
        #                 # print('m2')
        #                 if y - 1 > 0:
        #                     if image[y - 1, x] == 0:
        #                         x_y.append((y - 1, x))
        #                         count += 1
        #                         # print('m3')
        #                 # Right
        #                 if x + 1 < width:
        #                     if y + 1 < height:
        #                         if image[y + 1, x + 1] == 0:
        #                             x_y.append((y + 1, x + 1))
        #                             count += 1
        #                             # print('r1')
        #                     if image[y, x + 1] == 0:
        #                         x_y.append((y, x + 1))
        #                         count += 1
        #                         # print('r2')
        #                     if y - 1 > 0:
        #                         if image[y - 1, x + 1] == 0:
        #                             x_y.append((y - 1, x + 1))
        #                             count += 1
        #                             # print('r3')
                            
        #                 if count == 0:
        #                     break
        #             if image[y, x] == 0 and flag is False:
        #                 # Left
        #                 if x - 1 > 0:
        #                     if y + 1 < height:
        #                         if image[y + 1, x - 1] == 0:
        #                             x_y.append((y + 1, x - 1))
        #                             count += 1
        #                             # print('l1')

        #                     if image[y, x - 1] == 0:
        #                         x_y.append((y, x - 1))
        #                         count += 1
        #                         # print('l2')
        #                     if y - 1 > 0:
        #                         if image[y - 1, x - 1] == 0:
        #                             x_y.append((y - 1, x - 1))
        #                             count += 1
        #                             # print('l3')
        #                 # Middle
        #                 if y + 1 < height:
        #                     if image[y + 1, x] == 0:
        #                         x_y.append((y + 1, x))
        #                         count += 1
        #                     # print('m1')
        #                 x_y.append((y, x))
        #                 count += 1
        #                 # print('m2')
        #                 if y - 1 > 0:
        #                     if image[y - 1, x] == 0:
        #                         x_y.append((y - 1, x))
        #                         count += 1
        #                         # print('m3')
        #                 # Right
        #                 if x + 1 < width:
        #                     if y + 1 < height:
        #                         if image[y + 1, x + 1] == 0:
        #                             x_y.append((y + 1, x + 1))
        #                             count += 1
        #                             # print('r1')
        #                     if image[y, x + 1] == 0:
        #                         x_y.append((y, x + 1))
        #                         count += 1
        #                         # print('r2')
        #                     if y - 1 > 0:
        #                         if image[y - 1, x + 1] == 0:
        #                             x_y.append((y - 1, x + 1))
        #                             count += 1
        #                             # print('r3')
        #                 flag = True
        #                 print('x_y= {}'.format(x_y))
        #                 print('region= {}'.format(reg))
        #                 # cv2.waitKey(0)
        #             else:
        #                 break
        #         if x_y != []:
        #             region+=1
        #         print(region_1)


        for x in range(width):
            for y in range(height):
                if image[y, x] == 0:
                    count += 1
                    # self.conn_pack['region_' + reg].add((x,y))
                    x_y = []
                    # Left
                    if x - 1 > 0:
                        if y + 1 < height:
                            if image[y + 1, x - 1] == 0:
                                x_y.append((y + 1, x - 1))
                                # print('l1')
                        if image[y, x - 1] == 0:
                            x_y.append((y, x - 1))
                            # print('l2')
                        if y - 1 > 0:
                            if image[y - 1, x - 1] == 0:
                                x_y.append((y - 1, x - 1))
                                # print('l3')
                    # Middle
                    if y + 1 < height:
                        if image[y + 1, x] == 0:
                            x_y.append((y + 1, x))
                        # print('m1')
                    x_y.append((y, x))
                    # print('m2')
                    if y - 1 > 0:
                        if image[y - 1, x] == 0:
                            x_y.append((y - 1, x))
                            # print('m3')
                    # Right
                    if x + 1 < width:
                        if y + 1 < height:
                            if image[y + 1, x + 1] == 0:
                                x_y.append((y + 1, x + 1))
                                # print('r1')
                        if image[y, x + 1] == 0:
                            x_y.append((y, x + 1))
                            # print('r2')
                        if y - 1 > 0:
                            if image[y - 1, x + 1] == 0:
                                x_y.append((y - 1, x + 1))
                                # print('r3')
                    
                    # print('x_y= {}'.format(x_y))
                    # print('region= {}'.format(reg))

                    if self.conn_pack == {}:
                        self.conn_pack['region_' + str(reg)] = set()
                        for x1_join in x_y: 
                            self.conn_pack['region_' + str(reg)].add(x1_join)
                        # print('inisialitation')
                    connected =False
                    if self.conn_pack != {}:
                        for x_list in x_y:
                            if connected:
                                break
                            for r in range(reg):
                                r += 1
                                if connected:
                                    break
                                for val in self.conn_pack['region_' + str(r)]:
                                    # if connected:
                                    #     break
                                    # for val_list in val:
                                    if x_list == val:
                                        # print('xlist= {}, val={}'.format(x_list,val))
                                        # cv2.waitKey(0)
                                        for x_join in x_y: 
                                            self.conn_pack['region_' + str(r)]\
                                                .add(x_join)
                                        connected = True
                                        break
                        if connected is False:
                            reg += 1
                            self.conn_pack['region_' + str(reg)] = set()
                            for x2_join in x_y: 
                                self.conn_pack['region_' + str(reg)].add(x2_join)
                    #     # print('is not empty')
                    #     # print(reg)
                    #     for r in range(reg):
                    #         print(r)
                    #         for val in self.conn_pack['region_' + str(r+1)]:
                    #             print('try conectivity')
                    #             print(val)
                                # for x in range(len(x_y)):
                                #     if x_y[x] == 100:#val.any():
                                #         self.conn_pack['region_' + str(reg+1)].append(x_y)
                                #     else:
                                #         new_reg = reg+1
                                #         # print('plusing reg')
                                #         # self.conn_pack['region_' + str(reg)] == []
                                #         self.conn_pack['region_' + str(new_reg)] = x_y

                    # reg = new_reg
        self.conn_pack_sort = copy.deepcopy(self.conn_pack)
        same_reg =[]
        for j in self.conn_pack:
            for k in self.conn_pack:
                # print(self.conn_pack)
                # print(self.conn_pack[k])
                # cv2.waitKey(0)
                connected = False
                if j == k:
                    continue      
                for q in self.conn_pack[j]:
                    if connected:
                        break
                    for w in self.conn_pack[k]:
                        # print('q={} ,w={}'.format(q,w))
                        # cv2.waitKey(0)

                        # Left
                        x = q[1]
                        y = q[0]
                        if x - 1 > 0:
                            if y + 1 < height:
                                if (y + 1, x - 1) == w:
                                    if k in self.conn_pack_sort \
                                            and j in self.conn_pack_sort :
                                        # print(k)
                                        # cv2.waitKey(0)
                                        for val in self.conn_pack_sort[k]:
                                            self.conn_pack_sort[j].add(val)
                                        del(self.conn_pack_sort[k])
                                    # print(j +'=' + k)
                                    # same_reg.append((j, k))
                                    connected = True
                                    break
                                    # print('l1')
                            if (y, x - 1) == w:
                                if k in self.conn_pack_sort\
                                        and j in self.conn_pack_sort :
                                    for val in self.conn_pack_sort[k]:
                                        self.conn_pack_sort[j].add(val)
                                    del(self.conn_pack_sort[k])
                                # print(j +'=' + k)
                                # same_reg.append((j, k))
                                connected = True
                                break
                            if y - 1 > 0:
                                if (y - 1, x - 1) == w:
                                    if k in self.conn_pack_sort\
                                            and j in self.conn_pack_sort :
                                        for val in self.conn_pack_sort[k]:
                                            self.conn_pack_sort[j].add(val)
                                        del(self.conn_pack_sort[k])
                                    # print(j +'=' + k)
                                    # same_reg.append((j, k))
                                    connected = True
                                    break
                                    # print('l3')
                        # Middle
                        if y + 1 < height:
                            if (y + 1, x) == w:
                                if k in self.conn_pack_sort\
                                        and j in self.conn_pack_sort:
                                    # print(k)
                                    # cv2.waitKey(0)
                                    for val in self.conn_pack_sort[k]:
                                        # print(j)
                                        # cv2.waitKey(0)
                                        self.conn_pack_sort[j].add(val)
                                    del(self.conn_pack_sort[k])
                                # print(j +'=' + k)
                                # same_reg.append((j, k))
                                connected = True
                                break
                            # print('m1')
                        if y - 1 > 0:
                            if (y - 1, x) == w:
                                if k in self.conn_pack_sort\
                                        and j in self.conn_pack_sort:
                                    for val in self.conn_pack_sort[k]:
                                        self.conn_pack_sort[j].add(val)
                                    del(self.conn_pack_sort[k])
                                # print(j +'=' + k)
                                # same_reg.append((j, k))
                                connected = True
                                break

                        # Right
                        if x + 1 < width:
                            if y + 1 < height:
                                if (y + 1, x + 1) == w:
                                    if k in self.conn_pack_sort\
                                            and j in self.conn_pack_sort:
                                        for val in self.conn_pack_sort[k]:
                                            self.conn_pack_sort[j].add(val)
                                        del(self.conn_pack_sort[k])
                                    # print(j +'=' + k)
                                    # same_reg.append((j, k))
                                    connected = True
                                    break
                            if (y, x + 1) == w:
                                if k in self.conn_pack_sort\
                                        and j in self.conn_pack_sort:
                                    for val in self.conn_pack_sort[k]:
                                        self.conn_pack_sort[j].add(val)
                                    del(self.conn_pack_sort[k])
                                # print(j +'=' + k)
                                # same_reg.append((j, k))
                                connected = True
                                break
                            if y - 1 > 0:
                                if (y - 1, x + 1) == w:
                                    if k in self.conn_pack_sort\
                                            and j in self.conn_pack_sort:
                                        for val in self.conn_pack_sort[k]:
                                            self.conn_pack_sort[j].add(val)
                                        del(self.conn_pack_sort[k])
                                    # print(j +'=' + k)
                                    # same_reg.append((j, k))
                                    connected = True
                                    break
                        

                        
        # print(same_reg)
        # cv2.waitKey(0)
        # for lr in same_reg:
        #     for val in self.conn_pack[lr[1]]:
        #         self.conn_pack[lr[0]].add(val)
                
        #     # print(lr[0])
        #     # cv2.waitKey(0)
        # save = []
        # for reg_1 in same_reg:
        #     for x in range(len(same_reg)):
        #         if reg_1 == (same_reg[x][1], same_reg[x][0]):
        #             save.append(x)
        #             break
                    

        # print(same_reg)
        # print(len(same_reg))
        # print(save)
        # cv2.waitKey(0)
        # for val in self.conn_pack_sort[k]:
        #     self.conn_pack_sort[j].add(val)
        # del(self.conn_pack_sort[k])
        

def main():
    # for imagePath in sorted(glob.glob(args["images"] + "/*.png")):

    for imagePath in sorted(glob.glob("temp" + "/*.png")):
        print('________________Next File_________________')
        original_image = cv2.imread(imagePath)
        gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        # template = cv2.Canny(gray, 50, 200)
        # Otsu threshold
        # ret_img, image1 = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY
        #                                + cv2.THRESH_OTSU)
        # Simple threshold
        # ret_img, image2 = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
        # Adaptive threshold value is the mean of neighbourhood area
        # image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        #                               cv2.THRESH_BINARY, 11, 2)
        # Adaptive threshold value is the weighted sum of neighbourhood
        # values where weights are a gaussian window
        image = cv2.adaptiveThreshold(gray, 255,
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY, 11, 2)

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

        # # Font_Processing
        # font_list = font(imagePath=imagePath, image=gray)

        # max_font_value = 0
        # font_type = 0
        # numstep = 20
        # for font_object in font_list:
        #     font_object.run(numstep=numstep)
        #     for value in font_object.get_object_result().values():
        #         # print(value)
        #         if type(value) == float:
        #             if value > max_font_value:
        #                 max_font_value = value
        #                 font_type = font_object

        # if isinstance(font_type, type(font_list[0])):
        #     font_type.display_marker_result()
        # else:
        #     print('Not a valuable result found check the numstep!')

        # pixel_gray = image
        # pixel_gray = cv2.cvtColor(pixel_value, cv2.COLOR_BGR2GRAY)
        # v_projection = vertical_projection(pixel_gray.copy())
        # h_projection = horizontal_projection(pixel_gray.copy())
        # plt.subplot(212), plt.imshow(pixel_gray)
        # plt.subplot(221), plt.plot(np.arange(0, len(v_projection), 1), v_projection)
        # plt.subplot(222), plt.plot(np.arange(0, len(h_projection), 1), h_projection)
        # # plt.xlim([0,256])
        # # plt.show()
        # cv2.waitKey(0)
        # cv2.imshow('h_before', image)

        input_image = ImageProcessing(original_image=original_image.copy())
        input_image.horizontal_projection(image.copy())  # adaptive binaryimage
        input_image.detect_horizontal_line()  # got self.start_point_h
        cv2.imshow('from main', input_image.original_image)
        input_image.crop_image(h_point=input_image.start_point_h,
                               input_image=original_image.copy())  # crop ori

        marker_height_list = []
        font_list = font(imagePath=imagePath, image=gray)
        for font_object in font_list:
            for location in font_object.get_marker_location():
                temp = cv2.imread(location)
                h, _, _ = temp.shape
                marker_height_list.append(h)

        # Block font processing
        for image in input_image.bag_of_h_crop:
            # Get original cropped one line binary image
            temp_image_ori = input_image.bag_of_h_crop[image]
            h, _, _ = temp_image_ori.shape
            # Scaled image by height ratio
            scaled_one_line_img_size = 1.3 * max(marker_height_list)
            if h > scaled_one_line_img_size:
                scale = scaled_one_line_img_size / h
                temp_image_ori = imutils.resize(temp_image_ori,
                                                height=int(h * scale))
            else:
                scale = 1
            if scale != 1:
                print('Scalling image to ' + str(scale))

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
            cv2.imshow('Base start =' + str(input_image.base_start)
                       + ' end =' + str(input_image.base_end),
                       input_image.one_line_image)
            print('>')
            cv2.waitKey(0)
            cv2.destroyWindow('Base start =' + str(input_image.base_start)
                              + ' end =' + str(input_image.base_end))

            # Font_Processing
            font_list = font(imagePath=imagePath, image=gray)
            max_font_value = 0
            font_type = 0
            numstep = 20
            # Looking for font type by the greatest value
            for font_object in font_list:
                font_object.run(numstep=numstep)
                for value in font_object.get_object_result().values():
                    # print(value)
                    if type(value) == float:
                        if value > max_font_value:
                            max_font_value = value
                            font_type = font_object

            if isinstance(font_type, type(font_list[0])):
                object_result = font_type.get_object_result()
                # font_type.display_marker_result(input_image=temp_image_ori)
            else:
                object_result = False
                print('Not a valuable result found check the numstep!')
                # cv2.waitKey(0)

            # for key in font_type.get_marker_thresh().keys():
            v_projection = input_image.vertical_projection(temp_image)
            input_image.detect_vertical_line(v_projection, temp_image.copy())
            # print(input_image.start_point_v)
            # Crop next word marker wether it's inside or beside 
            crop_words = {}
            if object_result:
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
                            x = (temp_x)[arr][0]
                            print('ordinat ' + data + '={}'.format(x))
                            marker_width = (temp_x[arr][2]) - x
                            space_limit = 2 * marker_width
                            v_point = input_image.start_point_v
                            # print(v_point)
                            print('marker {}'.format(space_limit))
                            for v in range(len(v_point)):
                                # print(v)
                                if v % 2 > 0:
                                    # print(v)
                                    if x < v_point[v]:
                                        space = (x - v_point[v-1])
                                        print('space {}'.format(space))
                                        # Marker position in v_point
                                        if space >= space_limit:
                                            # crop_words[data + '_' + str(arr)]
                                            #     = (v_point[v-1], v_point[v])
                                            print('add inside' + data)
                                            crop_words['final_inside_' + name
                                                       + '_' + str(arr)] \
                                                = (v_point[v-1], v_point[v])
                                            crop_words['ordinat_' + name
                                                       + '_' + str(arr)] \
                                                = temp_x[arr]
                                            break
                                        elif v > 1:
                                            crop_words['next_' + name
                                                       + '_' + str(arr)] \
                                                = (v_point[v-3], v_point[v-2])
                                            print('add next ' + data)
                                            crop_words['word_' + name
                                                       + '_' + str(arr)] \
                                                = (v_point[v-1], v_point[v])
                                            crop_words['ordinat_' + name
                                                       + '_' + str(arr)] \
                                                = temp_x[arr]
                                            break
                                        else:
                                            break
            print(crop_words)
            print(v_point)
            if object_result:
                # object_result = font_type.get_object_result()
                font_type.display_marker_result(input_image=temp_image_ori)
            else:
                print('Not a valuable result found check the numstep!')
                print('>')
                cv2.waitKey(0)

            # Check v_projection words
            # If there is a hanging marker
            crop_words_final = crop_words.copy()
            for key in crop_words:
                name = key.split('_')
                # print('key {}'.format(key))
                if name[0] == 'next':
                    next_ = crop_words[key]
                    join = []
                    for x in range(len(name)):
                        if x == 0:
                            continue
                        if x == len(name) - 1:
                            join.append(name[x])
                            # print(name[x])
                        else:
                            join.append(name[x] + '_')
                            # print(name[x])
                    join = ''.join(join)
                    # print('join {}'.format(join))
                    # print('nrxt {}'.format(next_))
                if name[0] == 'word':
                    word_ = crop_words[key]
                    next_image = temp_image.copy()[:, next_[0]:next_[1]]
                    next_v_proj = input_image.vertical_projection(next_image)
                    # plt.subplot(121), plt.imshow(next_image)
                    # plt.subplot(122), plt.plot(np.arange(0, len(next_v_proj), 1), next_v_proj)
                    # plt.show()
                    word_image = temp_image.copy()[:, word_[0]:word_[1]]
                    word_v_proj = input_image.vertical_projection(word_image)
                    # plt.subplot(121), plt.imshow(word_image)
                    # plt.subplot(122), plt.plot(np.arange(0, len(word_v_proj), 1), word_v_proj)
                    # plt.show()
                    next_h_proj = input_image.horizontal_projection(next_image)
                    input_image.base_line(next_image.copy())
                    # cv2.imshow('Base start =' + str(input_image.base_start)
                    #            + ' end =' + str(input_image.base_end),
                    #            input_image.one_line_image)
                    # print('>')
                    # cv2.waitKey(0)
                    word_h_proj = input_image.horizontal_projection(word_image)
                    input_image.base_line(word_image.copy())
                    # cv2.imshow('Base start =' + str(input_image.base_start)
                    #            + ' end =' + str(input_image.base_end),
                    #            input_image.one_line_image)
                    # print('>')
                    # cv2.waitKey(0)
                    # print(input_image.base_start)
                    # print(input_image.base_end)
                    # print(len(next_h_proj))
                    # print(next_h_proj)
                    # Get crop word index
                    for x in range(len(v_point)):
                        if x % 2 == 0:
                            if v_point[x] == next_[0]:
                                w_index = x
                                break
                    # print(w_index)
                    base_check = next_h_proj[oneline_baseline[0]:
                                             oneline_baseline[1]]
                    if np.all(base_check == 0):
                        if w_index >= 2:
                            crop_words_final['final_beside_' + join]\
                                    = (v_point[w_index - 2],
                                       v_point[w_index - 1])
                            print('final beside origin')
                    else:
                        crop_words_final['final_beside_' + join]\
                                = (v_point[w_index], v_point[w_index + 1])
                        # print('final beside')

            print(crop_words_final)
            for key in crop_words_final:
                name = key.split('_')
                if name[0] == 'final':
                    x_value = crop_words_final[key]
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

                    if name[1] == 'beside':
                        final_img = temp_image.copy()[:, x_value[0]:x_value[1]]
                        # cv2.imshow('beside', final_img)
                        # temp_img = final_img.copy()
                        # ccc = input_image.vertical_projection(final_img)
                        # sum1=0
                        # for x in ccc:
                        #     sum1 += x
                        # print(sum1)
                        final_img = cv2.bitwise_not(final_img)
                        cv2.imshow('inverse', final_img)
                        kernel = np.ones((2,2), np.uint8)
                        dilation = cv2.dilate(final_img.copy(),kernel,iterations = 1)
                        # kernel = np.ones((2,2), np.uint8)
                        # erosion = cv2.erode(final_img.copy(),kernel,iterations = 1)
                        # opening = cv2.morphologyEx(final_img.copy(), cv2.MORPH_OPEN, kernel)
                        # closing = cv2.morphologyEx(final_img.copy(), cv2.MORPH_CLOSE, kernel)
                        final_img = cv2.bitwise_not(dilation)
                        cv2.imshow('morph', final_img)
                        print('morph')
                        cv2.waitKey(0)
                        # cv2.imshow('dilation', dilation)
                        # print('dilation')
                        # cv2.waitKey(0)
                        # cv2.imshow('opening', opening)
                        # print('opening')
                        # cv2.waitKey(0)
                        # cv2.imshow('closing', closing)
                        # print('closing')
                        # cv2.waitKey(0)
                        input_image.eight_conectivity(image=final_img)
                        print('back to main')
                        # print(input_image.conn_pack_sort)
                        # print(input_image.conn_pack['region_7'])
                        print('ori={}, sort={}'.format(
                            len(input_image.conn_pack),len(input_image.conn_pack_sort)))
                        print('>')
                        cv2.waitKey(0)
                        final_img[:] = 255
                        cv2.imshow('white', final_img)
                        cv2.waitKey(0)
                        for region in input_image.conn_pack_sort:
                            value = list(input_image.conn_pack_sort[region])
                            # print(value)
                            for x in value:
                                final_img[x] = 0
                            cv2.imshow('region', final_img)
                            cv2.waitKey(0)
                        # height, width = final_img.shape
                        # h_project = input_image.horizontal_projection(final_img)
                        # input_image.base_line(final_img.copy())
                        # v_project = input_image.vertical_projection(final_img)
                        # cv2.line(temp_img, (0, oneline_baseline[0]),
                        #          (width, oneline_baseline[0]), (0, 0, 0), 2)
                        # cv2.line(temp_img, (0, oneline_baseline[1]),
                        #          (width, oneline_baseline[1]), (0, 0, 0), 2)
                        # cv2.imshow('word', input_image.one_line_image)
                        # cv2.imshow('one line', temp_img)
                        # cv2.waitKey(0)
                        # v_project_1 = input_image.vertical_projection(temp_img)
                        # plt.figure(1)
                        # plt.subplot(211), plt.imshow(final_img)
                        # plt.subplot(212), plt.plot(np.arange(0, len(v_project), 1),v_project)
                        # plt.figure(2)
                        # plt.subplot(211), plt.imshow(temp_img)
                        # plt.subplot(212), plt.plot(np.arange(0, len(v_project_1), 1),v_project_1)
                        # plt.show()
                    # if name[1] == 'inside':



        # input_image.base_line()
        # input_image.detect_vertical_line()

        # cv2.imshow('from main', input_image.original_image)

    #     # Detect line horizontal
    #     up_flag = 0
    #     down_flag = 0
    #     pixel_limit = 4
    #     start_to_end = 0
    #     end_to_start = 0
    #     start_point = []
    #     for x in range(len(h_projection)):
    #         if h_projection[x] == 0 and up_flag == 1:
    #             start_point.append(x)
    #             down_flag = 1
    #             up_flag = 0

    #         if up_flag == 1:
    #             start_to_end += 1
    #         else:
    #             start_to_end = 0

    #         if down_flag == 1:
    #             end_to_start += 1
    #             # print(end_to_start)
    #         else:
    #             end_to_start = 0

    #         if h_projection[x] > 0 and up_flag == 0:
    #             # if count>=pixel_limit
    #             start_point.append(x)
    #             if down_flag == 1 and end_to_start < pixel_limit:
    #                 del(start_point[len(start_point)-1])
    #                 del(start_point[len(start_point)-1])
    #                 # print('delete')
    #             # print(count)
    #             up_flag = 1
    #             down_flag = 0

    #     # Even is begining of line and Odd is end of line
    #     for x in range(len(start_point)):
    #         # cv2.line(original_image, (0, start_point[x]), (len(v_projection),
    #         #          start_point[x]), (0, 0, 255), 2)
    #         # print(x)
    #         if x % 2 == 0:     # Start_point
    #             cv2.line(original_image, (0, start_point[x]), 
    #                      (len(v_projection), start_point[x]), (0, 0, 255), 2)
    #             # print(x)
    #         else:         # End_point
    #             cv2.line(original_image, (0, start_point[x]),
    #                      (len(v_projection), start_point[x]), (255, 0, 0), 2)
    #             # print(x)
    #             # print('end')

    #     diff = [0]
    #     for x in range(len(h_projection)):
    #         if x > 0:
    #             temp_diff = abs(int(h_projection[x]) - int(h_projection[x-1]))
    #             diff.append(temp_diff)

    #     base_start = 0
    #     base_end = 0
    #     temp = 0
    #     for x in range(len(diff)):
    #         if diff[x] > temp:
    #             temp = diff[x]
    #             base_end = x

    #     temp = 0 
    #     for x in range(len(diff)):
    #         if x == base_end:
    #             continue
    #         if diff[x] > temp:
    #             temp = diff[x]
    #             base_start = x

    #     cv2.line(original_image, (0, base_start), (len(v_projection),
    #              base_start), (0, 255, 0), 2)
    #     cv2.line(original_image, (0, base_end), (len(v_projection),
    #              base_end), (0, 255, 0), 2)

    
    #     # Detect line vertical
    #     up_flag = 0
    #     down_flag = 0
    #     pixel_limit_v = 4
    #     start_to_end_v = 0
    #     end_to_start_v = 0
    #     start_point_v = []
    #     for x in range(len(v_projection)):
    #         if v_projection[x] > 0 and up_flag == 0:
    #             start_point_v.append(x)
    #             up_flag = 1
    #             down_flag = 0

    #         if v_projection[x] == 0 and up_flag == 1:
    #             start_point_v.append(x)
    #             down_flag = 1
    #             up_flag = 0

    #         if up_flag == 1:
    #             start_to_end_v += 1
    #         else:
    #             start_to_end_v = 0

    #         if down_flag == 1:
    #             end_to_start_v += 1
    #         else:
    #             end_to_start_v = 0


    #     # Even is begining of line and Odd is end of line
    #     for x in range(len(start_point_v)):
    #         if x % 2 == 0:
    #             cv2.line(original_image, (start_point_v[x], 0),
    #                      (start_point_v[x], len(h_projection)), (0, 0, 255), 2)
    #         else:
    #             cv2.line(original_image, (start_point_v[x], 0), 
    #                      (start_point_v[x], len(h_projection)), (255, 0, 0), 2)

    #     cv2.imshow('line', original_image)
    #     cv2.waitKey(0)

    #     print(start_point)
    #     bag_of_h_crop = {}
    #     for x in range(len(start_point)):
    #         if x + 2 > len(start_point):
    #             print('x')
    #             continue
    #         if x % 2 == 0:
    #             bag_of_h_crop[x] = original_image[
    #                                start_point[x]:start_point[x+1], :]
    #     # print(bag_of_h_crop)
    #     for image in bag_of_h_crop:
    #         cv2.imshow('bag_h', bag_of_h_crop[image])
    #         cv2.waitKey(0)
    #         # cv2.destroyAllWindows()

    #     bag_of_v_crop = {}
    #     count = 0
    #     for image in bag_of_h_crop:
    #         # print(image)
    #         #y = int(image/2)
    #         for x in range(len(start_point_v)):
    #             #print('inside loop')
    #             print(image)
    #             count += 1
    #             if x % 2 == 0:
    #                 x1 = start_point[image]
    #                 x2 = start_point[image+1]
    #                 y1 = start_point_v[x]
    #                 y2 = start_point_v[x+1]
    #                 bag_of_v_crop[count] = original_image[x1:x2, y1:y2]
    #             # print(x1,'_', x2,'_', y1,'_', y2)

    #     for image in bag_of_v_crop:
    #         cv2.imshow('Crop Result', bag_of_v_crop[image])
    #         cv2.waitKey(0)
    #         # cv2.destroyAllWindows()
        # cv2.waitKey(0)
    cv2.destroyAllWindows()

# cv2.imshow('crop', view)
# cv2.waitKey(0)
# cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
# exec(main())
