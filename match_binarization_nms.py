from pyimagesearch.nms import non_max_suppression_slow
import numpy as np
import argparse
import imutils
import glob
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-t", "--template", required=True, help="Path to template image")
ap.add_argument("-i", "--images", required=True,
	help="Path to images where template will be matched")
ap.add_argument("-v", "--visualize",
	help="Flag indicating whether or not to visualize each iteration")
args = vars(ap.parse_args())

# load the image image, convert it to grayscale, and detect edges
template = cv2.imread(args["template"])
template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
#template = cv2.Canny(template, 50, 200)

#Otsu threshold
#ret_temp,template = cv2.threshold(template,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

#Simple threshold
#ret_temp, template = cv2.threshold(template,127,255,cv2.THRESH_BINARY)

#Adaptive threshold value is the mean of neighbourhood area
#template = cv2.adaptiveThreshold(template,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)

#Adaptive threshold value is the weighted sum of neighbourhood values where weights are a gaussian window
template = cv2.adaptiveThreshold(template,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)

cv2.imshow("template", template)
(tH, tW) = template.shape[:2]
#cv2.imshow("Template", template)

def NormalizeData(data):
	return (data - np.min(data)) / (np.max(data) - np.min(data))



# loop over the images to find the template in
for imagePath in glob.glob(args["images"] + "/*.png"):
	# load the image, convert it to grayscale, and initialize the
	# bookkeeping variable to keep track of the matched region
	image = cv2.imread(imagePath)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	found = None

	boundingBoxes=np.ones((1,4), dtype=int)
	# loop over the scales of the image (start stop numstep) from the back
	for scale in np.linspace(0.2, 2.0, 40)[::-1]:
		# resize the image according to the scale, and keep track
		# of the ratio of the resizing
		resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
		r = gray.shape[1] / float(resized.shape[1])

		# if the resized image is smaller than the template, then break
		# from the loop
		if resized.shape[0] < tH or resized.shape[1] < tW:
			break
		
		# detect edges in the resized, grayscale image and apply template
		# matching to find the template in the image
		#edged = cv2.Canny(resized, 50, 200)

		#Otsu threshold
		#ret_img,resized = cv2.threshold(resized,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

		#Simple threshold
		#ret_img, resized = cv2.threshold(resized,127,255,cv2.THRESH_BINARY)

		#Adaptive threshold value is the mean of neighbourhood area
		#resized = cv2.adaptiveThreshold(resized,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)

		#Adaptive threshold value is the weighted sum of neighbourhood values where weights are a gaussian window
		resized = cv2.adaptiveThreshold(resized,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)


		#cv2.imshow("edged",resized)
		result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
		#result = NormalizeData(result)
		(_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
		#print(maxVal)
		# check to see if the iteration should be visualized
		if args.get("visualize", False):
			# draw a bounding box around the detected region
			clone = np.dstack([edged, edged, edged])
			cv2.rectangle(clone, (maxLoc[0], maxLoc[1]),
				(maxLoc[0] + tW, maxLoc[1] + tH), (0, 0, 255), 2)
			cv2.imshow("Visualize", clone)
			cv2.waitKey(0)

		threshold = 0.7
		# loc = np.where(result >= threshold)
		# (startX, startY) = (int(loc[0] * r), int(loc[1] * r))
		# (endX, endY) = (int((loc[0] + tW) * r), int((loc[1] + tH) * r))
		# for pt in zip(*loc[::-1]):
		# 	cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
		# 	#cv2.rectangle(image, pt, (pt[0] + tW , pt[1] + tH), (0, 0, 255), 2)
		
		temp=[]
		if maxVal > threshold:
			found = (maxVal, maxLoc, r)
			(_, maxLoc, r) = found
			(startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
			(endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
			# cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
			temp = [startX, startY, endX, endY]
			boundingBoxes = np.append(boundingBoxes, [temp], axis=0)
			
			print(maxVal)

	# unpack the bookkeeping varaible and compute the (x, y) coordinates
	# of the bounding box based on the resized ratio
	# (_, maxLoc, r) = found
	# (startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
	# (endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))
	
	#if detected 
	if len(boundingBoxes) > 1 :
		boundingBoxes = np.delete(boundingBoxes, 0, axis = 0)
		pick = non_max_suppression_slow(boundingBoxes, 0.3)
		print (len(pick))
		print (pick)
		# print (boundingBoxes)
		for (startX, startY, endX, endY) in pick:
			cv2.rectangle(image, (startX, startY), (endX, endY), (0, 255, 0), 2)
	
	# cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
	cv2.imshow("Image", image)
	cv2.waitKey(0)

cv2.destroyAllWindows()
