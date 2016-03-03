import cv2
import numpy as np
import time


# basic marker generation parameters
x = 20 				# scaling parameter (pixels)
w_img = 500			# image width (pixels)
h_img = 500			# image height (pixels)
char = "T"			# alphanumeric character

# marker rotation parameters
rotx = 0			# x-axis image rotation angle (degrees)
roty = 0			# y-axis image rotation angle (degrees)
rotz = 0			# z-axis image rotation angle (degrees)
f = 1 				# focal length of viewpoint (?)

# marker motion blur parameters
blur_mag = 0		# motion blur magnitude
blur_angle = 0		# motion blur angle


# create a 3D rotated marker as per the iMeche UAS specifications
def create_marker():
	print "x: %d pixels" % x
	print "image width: %d pixels" % w_img
	print "image height: %d pixels" % h_img  

	# create main image
	center = (w_img/2, h_img/2)
	img = np.zeros((h_img, w_img, 3), dtype="uint8")
	img[:,:,:] = (0,100,0)

	# add white border
	delta = (3 * x / 16)
	x_border = center[0] - (8 * x)
	y_border = center[1] - (8 * x)
	w_border = 16 * x
	h_border = 16 * x
	img[(y_border - delta) : (y_border + h_border + delta), 
		(x_border - delta) : (x_border + w_border + delta), 
		:] = (255,255,255)
	img[(y_border + delta) : (y_border + h_border - delta), 
		(x_border + delta) : (x_border + w_border - delta), 
		:] = (0,100,0)

	# add red square
	w_sq = 4 * x
	h_sq = w_sq
	x_sq = center[0] - (w_sq / 2)
	y_sq = center[1] - (h_sq / 2)
	img[y_sq:y_sq+h_sq, x_sq:x_sq+w_sq, :] = (0,0,255)

	# add alphanumeric character
	(w_char, h_char), _ = cv2.getTextSize(char, cv2.FONT_HERSHEY_DUPLEX, (w_sq*h_sq)/2000, thickness=2)
	x_char = center[0] - (w_char / 2)
	y_char = center[1] + (h_char / 2)
	cv2.putText(img, char, (x_char, y_char), 
				fontFace=cv2.FONT_HERSHEY_DUPLEX, 
				fontScale=(w_sq * h_sq) / 2000, 
				color=(255,255,255), 
				thickness=2)
	return img


# generate multiple rotations of the marker image
def rotate_marker(img):
	global rotx, roty, rotz
	h, w, d = img.shape
	# convert angles from degrees to radians
	rotx = rotx * np.pi / 180.0
	roty = roty * np.pi / 180.0
	rotz = rotz * np.pi / 180.0
	# calculate cosines and sines of rotation angles
	cx = np.cos(rotx)
	sx = np.sin(rotx)
	cy = np.cos(roty)
	sy = np.sin(roty)
	cz = np.cos(rotz)
	sz = np.sin(rotz)
	# create rotation matrix
	roto = [
		[cz * cy, cz * sy * sx - sz * cx],
		[sz * cy, sz * sy * sx + cz * cx],
		[-sy, cy * sx]
	]
	# create rotation point
	pt = [
		[-w/2, -h/2],
		[w/2, -h/2],
		[w/2, h/2],
		[-w/2, h/2]	
	]
	# create output points
	ptt = np.float32([[0, 0], [0, 0], [0, 0], [0, 0]])
	# calculate output points based on rotation rotation matrix and rotation point
	for i in range(4):
		pz = pt[i][0] * roto[2][0] + pt[i][1] * roto[2][1]
		ptt[i][0] = w / 2 + (pt[i][0] * roto[0][0] + pt[i][1] * roto[0][1]) * f * h / (f * h + pz)
		ptt[i][1] = h / 2 + (pt[i][0] * roto[1][0] + pt[i][1] * roto[1][1]) * f * h / (f * h + pz)
	# input points for perspective transform
	in_pt = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
	# output points for perspective transform
	out_pt = np.float32(ptt)
	# generate perspective transformation matrix
	transform = cv2.getPerspectiveTransform(in_pt, out_pt)
	# apply and return perspective transformed image
	return cv2.warpPerspective(img, transform, (w,h), flags=cv2.INTER_CUBIC)


# add motion blur ot marker image
def blur_marker(img):
	if blur_mag == 0:
		return img
	# create linear motion blur kernel
	kernel = np.zeros((blur_mag,blur_mag), dtype="float32")
	kernel[blur_mag / 2, :] = np.ones(blur_mag)
	# normalize motion blur kernel
	kernel /= blur_mag
	# generate rotation matrix for motion blur kernel based on specified motion blur angle
	M = cv2.getRotationMatrix2D((blur_mag / 2, blur_mag / 2), blur_angle, 1)
	# generate rotated motion blur kernel
	kernel = cv2.warpAffine(kernel, M, kernel.shape, flags=cv2.INTER_CUBIC)
	# apply motion blur kernel and return motion blurred image
	img = cv2.filter2D(img, -1, kernel)
	return img


def main():
	print "[ draw marker ]"	

	# generate marker image
	marker_img = create_marker()
	
	# generate rotated marker image
	rot_img = rotate_marker(marker_img)

	# add motion blur to amrker image
	blur_img = blur_marker(rot_img)

	# generate current timestamp
	current_time = time.localtime(time.time())
	timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", current_time)

	# add current timestamp to image filename
	marker_filename = "marker_%s.png" % timestamp
	
	# show image
	print "press the 's' key to save image (%s)" % marker_filename
	print "press any other key to skip saving"
	cv2.imshow(marker_filename, blur_img)	
	if cv2.waitKey(0) == ord('s'):
		# save the generated marker image if 's' key is pressed
		if cv2.imwrite("marker_%s.png" % timestamp, blur_img):
			print "image was saved"
		else:
			print "image could not be saved"


if __name__ == "__main__":
	main()