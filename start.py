#!/usr/bin/env python3

import sys
import io
import os

import time
from time import sleep

import numpy
import matplotlib
from PIL import Image
from PyQt5.QtCore import *
import PyQt5.QtCore
from PyQt5.QtGui import *

from PyQt5.QtWidgets import *

from pyqt import FreakingQtImageViewer
import scipy.misc

from skimage import color
from skimage import transform as tf
#from skimage import data
from skimage.feature import canny
from skimage.transform import hough_ellipse
from skimage.draw import ellipse_perimeter

from skimage.transform import hough_circle
from skimage.feature import peak_local_max
from skimage.draw import circle_perimeter
from skimage.util import img_as_ubyte

import scipy.misc

import picamera
import picamera.array

from cv import circle_detection, rgb2gray
from _thread import start_new_thread


class DraughtsGameWindow(QWidget):

	def __init__(self):
		super().__init__()
		self.corners = []
		self.CELLS_PER_ROW = 8
		self.BLACK_COLOR = QColor(0,0,0,255)
		self.WHITE_COLOR = QColor(255,255,255,255)
		self.BLUE_COLOR = QColor(0,0,255,255)
		self.RED_COLOR = QColor(255,0,0,255)
		self.GREEN_COLOR = QColor(0,255,0,255)
		self.DEFAULT_PEN = QPen(self.BLUE_COLOR)
		self.DEFAULT_PEN.setWidth(20)
		self.PIX_PADDING = 25
		self.BORDER_RADIUS = 10

		self.rg_bg = (2, 3)

		self.initUI()
		
	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Escape: 
			self.close()
		elif event.key() == Qt.Key_C:
			start_new_thread(self.calibrate, (0, 0,))
		elif event.key() == Qt.Key_V:

			self.vbox.setContentsMargins(self.upper_left[0] + 10,self.PIX_PADDING + 10,240,112)
			self.pixmap = QPixmap("checkers_randlos.jpg")
			self.pixmap = self.pixmap.scaledToWidth( self.upper_right[0]-self.upper_left[0] )
			'''
			self.painter.drawEllipse(self.upper_left[0]-10,self.upper_left[1]-10,20,20)
			self.painter = QPainter(self.pixmap)
			self.DEFAULT_PEN.setColor(self.WHITE_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.upper_right[0]-10,self.upper_right[1]-10,20,20)
			self.DEFAULT_PEN.setColor(self.RED_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.lower_right[0]-10,self.lower_right[1]-10,20,20)
			self.DEFAULT_PEN.setColor(self.GREEN_COLOR)
			self.painter.setPen(self.DEFAULT_PEN)
			self.painter.drawEllipse(self.lower_left[0]-10,self.lower_left[1]-10,20,20)
			'''
			
			self.lbl.setPixmap(self.pixmap)
			self.lbl.repaint()

		elif event.key() == Qt.Key_S:

			##############################################
			# find 
			# 
			# 
			##############################################

			start_new_thread(self.findTiles, (0, 0,))

		elif event.key() == Qt.Key_P:

			##############################################
			# shoot with defined white balance mode
			# 
			# capture image with defined self.rg_bg and show
			##############################################

			camera = picamera.PiCamera()

			# test manual white balance
			camera.awb_mode = 'off'
			camera.awb_gains = self.rg_bg
			# end

			with picamera.array.PiRGBArray(camera) as stream:
				camera.capture(stream, format='rgb')
				im = Image.fromarray(stream.array)
				im.save('./preview.png')				
				camera.close()
				os.system('xdg-open ./preview.png')

		elif event.key() == Qt.Key_T:

			##############################################
			# test white balance modi 
			# 
			# iterate through various combinations of wb
			##############################################

			camera = picamera.PiCamera()
			camera.awb_mode = 'off'

			rg_bg = (2, 3)

			for rg in range(0,20):
				for bg in range(0,20):

					rg_x=rg/10
					bg_x=bg/10

					camera.awb_gains = (rg_x,bg_x)
					with picamera.array.PiRGBArray(camera) as stream:
						camera.capture(stream, format='rgb')
						im = Image.fromarray(stream.array)
						im.save('./preview_'+str(rg_x)+'_'+str(bg_x)+'.png')				

			camera.close()

			self.vbox.setContentsMargins(self.upper_left[0] + 10,self.PIX_PADDING + 10,240,112)
			self.pixmap = QPixmap("checkers_randlos.jpg")
			self.pixmap = self.pixmap.scaledToWidth( self.upper_right[0]-self.upper_left[0] )			
			self.lbl.setPixmap(self.pixmap)
			self.lbl.repaint()


	def initUI(self):
		
		self.WIDTH, self.HEIGHT, self.CELL_SIZE = screen_rect.width(), screen_rect.height(), screen_rect.width() / self.CELLS_PER_ROW
		self.pixmap = QPixmap(self.WIDTH-20,self.HEIGHT-20)
		
		self.upper_left = (self.PIX_PADDING + self.WIDTH / 2 - self.pixmap.height() / 2, self.PIX_PADDING)
		self.upper_right = (- self.PIX_PADDING + self.WIDTH / 2 + self.pixmap.height() / 2, self.PIX_PADDING + 0)
		self.lower_right = (-self.PIX_PADDING + self.WIDTH / 2 + self.pixmap.height() / 2, -self.PIX_PADDING + self.pixmap.height())
		self.lower_left = (self.PIX_PADDING + self.WIDTH / 2 - self.pixmap.height() / 2, -self.PIX_PADDING + self.pixmap.height())
		
		self.DRAW_SIZE = self.upper_right[0] - self.upper_left[0]
		print(self.DRAW_SIZE)
		
		self.painter = QPainter(self.pixmap)
		self.painter.setPen(self.DEFAULT_PEN)

		self.painter.fillRect(0, 0,self.WIDTH, self.HEIGHT, self.BLACK_COLOR)
		self.painter.drawEllipse(self.upper_left[0]-10,self.upper_left[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.WHITE_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.upper_right[0]-10,self.upper_right[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.RED_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.lower_right[0]-10,self.lower_right[1]-10,20,20)
		self.DEFAULT_PEN.setColor(self.GREEN_COLOR)
		self.painter.setPen(self.DEFAULT_PEN)
		self.painter.drawEllipse(self.lower_left[0]-10,self.lower_left[1]-10,20,20)
		
		self.vbox = QVBoxLayout(self)
		self.lbl = QLabel(self)
		self.lbl.setPixmap(self.pixmap)
		self.vbox.addWidget(self.lbl)
		
		self.setStyleSheet("background-color:black;")
		
		self.setLayout(self.vbox)
		self.vbox.setAlignment(Qt.AlignHCenter)
		self.showFullScreen()
		self.setWindowTitle('DraughtsCV')
		self.show()
		
	def calibrate(self, ignore1, ignore2): # pythonmaster
		camera = picamera.PiCamera()

		# test manual white balance
		#camera.awb_mode = 'off'
		#camera.awb_gains = self.rg_bg
		# end
		
		self.calibrationPoints = -1
		#while True:
		with picamera.array.PiRGBArray(camera) as stream:
			camera.capture(stream, format='rgb')
			img = stream.array
			camera.close()

			img, coords = circle_detection(img, 20, 25)
			im = Image.fromarray(img)
			im.save('./tmp.png')
				
			
			self.calibrationPoints = self.checkCoords(img, coords)
			if isinstance(self.calibrationPoints, (numpy.ndarray, numpy.generic) ):
				src = numpy.array((
					(0, 0), #upper left
					(0, 800), #lower left
					(800, 800), #lright
					(800, 0) #uright
				))
			
				transformer = tf.ProjectiveTransform()
				transformer.estimate(src, self.calibrationPoints)
				transformed_image = tf.warp(im, transformer, output_shape = (800,800))
				
				#print("Transformed Image: ",transformed_image)
				
				scipy.misc.imsave('./transformed.png', transformed_image)
				#break
			else: print('ups')
		print(self.corners)


	def checkCoords(self, img, coords):
		self.upper_left_coords = []
		self.lower_left_coords = []
		self.lower_right_coords = []
		self.upper_right_coords = []

		"""
		# debug -->
		# for debug: draw all circles as shapes to image
		# 1. new image
		debug_img = numpy.zeros((1024, 1280, 3), dtype=numpy.uint8)
		# debug -->
		"""

		for index, coord in enumerate(coords):
			#print(img[coord[0], coord[1]]," - ", )

			pixel = img[coord[0], coord[1]]
			sum = 0
			sum += pixel[0]
			sum += pixel[1]
			sum += pixel[2]
			'''if sum > 300:
				print()
				#print("delete ", coord, ' with ', pixel)
			else:'''

			"""
			# debug -->
			# paramters: y, x, radius; returns x, y
			cx, cy = circle_perimeter(coord[0], coord[1], 23, method='bresenham', shape=(1024,1280))
			debug_img[cx, cy] = (pixel[0], pixel[1], pixel[2])
			# <-- debug end
			"""


			print("pixel: ", pixel, "@ y:",coord[0],', x:',coord[1])
			if pixel[0] > 150 and pixel[1] > 150 and pixel[2] > 150:
				self.upper_right_coords.append(coord)
			elif pixel[0] > 110:
				self.lower_right_coords.append(coord)
			elif pixel[1] > 110:
				self.lower_left_coords.append(coord)
			elif pixel[2] > 110:
				self.upper_left_coords.append(coord)
		
		"""
		# debug -->
		scipy.misc.imsave('./circles_detected_debug.png', debug_img)
		# <-- debug end
		"""

		#final_red = (int(numpy.sum(self.lower_right_coords[0])/len(self.lower_right_coords)),int(numpy.sum(self.lower_right_coords[1])/len(self.lower_right_coords[])))	#(sum(self.lower_right_coords[0]), sum(self.lower_right_coords[1]))
		final_white = numpy.average(self.upper_right_coords, axis=0)
		final_red = numpy.average(self.lower_right_coords, axis=0)
		final_green = numpy.average(self.lower_left_coords, axis=0)
		final_blue = numpy.average(self.upper_left_coords, axis=0)
		
		self.lbl.setPixmap(self.pixmap)
		if len(self.upper_right_coords) == 0 or len(self.upper_left_coords) == 0 or len(self.lower_left_coords) == 0 or len(self.lower_right_coords) == 0 :
			print('less than 4 corners for calibration detected, returning -1')
			return -1
		
		final_white = (int(final_white[1]),int(final_white[0]))
		final_red = (int(final_red[1]),int(final_red[0]))
		final_green = (int(final_green[1]),int(final_green[0]))
		final_blue = (int(final_blue[1]),int(final_blue[0]))
		
		print('avg blue ',final_blue)
		print('avg green',final_green)
		print('avg red ',final_red)
		print('avg white ',final_white)
		
		return numpy.array((final_blue, final_green, final_red, final_white))



	# 
	# Detect draughts tiles (german: Spielstein) at the field
	#
	def findTiles(self, ignore1, ignore2): # pythonmaster

		if isinstance(self.calibrationPoints, (numpy.ndarray, numpy.generic) ):

			camera = picamera.PiCamera()

			# test manual white balance
			#camera.awb_mode = 'off'
			#camera.awb_gains = self.rg_bg
			# end

			with picamera.array.PiRGBArray(camera) as stream:
				camera.capture(stream, format='rgb')
				img = stream.array
				camera.close()

				src = numpy.array((
					(0, 0), #upper left
					(0, 800), #lower left
					(800, 800), #lright
					(800, 0) #uright
				))
				
				transformer = tf.ProjectiveTransform()
				transformer.estimate(src, self.calibrationPoints)
				board_image = tf.warp(img, transformer, output_shape = (800,800))

				scipy.misc.imsave('./board.png', board_image)
			
			print('board image captured')

		else:
			print('calibrationPoints not yet set')

if __name__ == '__main__':

	app = QApplication(sys.argv)

	screen_rect = app.desktop().screenGeometry()
	viewer = DraughtsGameWindow() # init ui
	sys.exit(app.exec_())