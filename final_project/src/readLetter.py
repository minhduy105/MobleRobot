#!/usr/bin/env python

from __future__ import print_function
import roslib
import sys
import rospy
import cv2
import rospy
import numpy as np
import pyocr
import message_filters
import pyocr.builders
from sensor_msgs.msg import Image
from std_msgs.msg import String
from PIL import Image as Img
from cv_bridge import CvBridge, CvBridgeError

class image_converter:

	def __init__(self):

		self.name_pub = rospy.Publisher("delivery_to",String,queue_size=10)
		self.bridge = CvBridge()
		#this is for start searching "name" when the user hit s, and stop when it finds the name
		self.start = False 
		#this is the directory of all the person in the office with their ID
		self.person ={"Duy": 01,
					"Alison": 02}
		#set up the character recognition tool
		self.tools = pyocr.get_available_tools()
		if len(self.tools) == 0:
			print("No OCR tool found")
			sys.exit(1)
		self.tool = self.tools[0]
		self.langs = self.tool.get_available_languages()
		self.lang = self.langs[0]
		print("Will use lang '%s'" % (self.lang))
		image_sub = rospy.Subscriber("/usb_cam/image_raw",Image,self.callbackImg)
		key_sub = rospy.Subscriber('keys', String,self.callbackStr)

	def getletter(self,img):
		txt = self.tool.image_to_string(
			img,
			lang=self.lang,
			builder=pyocr.builders.TextBuilder()
		)
		return txt

	def detectName(self,crop_img):
		if self.start:
			cv2_im = cv2.cvtColor(crop_img,cv2.COLOR_BGR2RGB)
			pil_im = Img.fromarray(cv2_im)
			txt = self.getletter(pil_im)
			#delete all space
			liststr = txt.split( )
			#delete all special character
			liststr = [''.join(e for e in x if e.isalnum()) if True else x for x in liststr ]
			i = 0
			
			#assume the first name will be in the first 4 letter (Deliver to:, etc)
			while i < len(liststr) or i < 4:
				if any(s.lower() == liststr[i].lower() for s in self.person):
					print ("find person: ",liststr[i]) 
					self.start = False
					rate = rospy.Rate(10)
					self.name_pub.publish(liststr[i])							
					break
				i = i + 1

	def callbackImg(self,image):
		try:
			cv_image = self.bridge.imgmsg_to_cv2(image, "bgr8")
		except CvBridgeError as e:
			print(e)

		crop_img = cv_image[80:320, 80:480] #crop image 
		#need to make sure the image in this window before hit "s"
		cv2.imshow("Image window", crop_img)
		cv2.waitKey(3)
		self.detectName(crop_img)

	def callbackStr(self,keys):
		word = keys.data
		if word == 's':
			self.start = True# start looking for the person
		else :
			print ("Hit s to start looking for name")

	
if __name__ == '__main__':
	rospy.init_node('read_name', anonymous=True)
	ic = image_converter()

	try:
		rospy.spin()
	except KeyboardInterrupt:
		print("Shutting down")
	cv2.destroyAllWindows()

