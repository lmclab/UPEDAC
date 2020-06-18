#! python3

import cv2
import sys
import numpy as np

import color_harmonization
import util
import importlib
importlib.reload(color_harmonization)
importlib.reload(util)

def getColorHarm(fname):
	color_image = cv2.imread(image_filename, cv2.IMREAD_COLOR)

	height = color_image.shape[0]
	width  = color_image.shape[1]

	HSV_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
	best_harmomic_scheme = color_harmonization.B(HSV_image)
	#print("Harmonic Scheme Type  : ", best_harmomic_scheme.m)
	#print("Harmonic Scheme Alpha : ", best_harmomic_scheme.alpha)
	return best_harmomic_scheme.m

##HueTemplates = ["i","V","L","mirror_L","I","T","Y","X" ]
if __name__ == '__main__':

	image_filename = sys.argv[1]

	ch = getColorHarm(image_filename)

	print("Harmonic Scheme Type  : ", ch)