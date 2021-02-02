import sys
import datetime
import os
from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from functools import partial

from ais_db import AIS_db
from calibration_db import Calibration_db
from common import file_time, sec_time
from gui_widgets import *

# Define colours for contacts and ais lines
colA = QtCore.Qt.red
colB = QtCore.Qt.magenta
colSuspect = QColor(255, 0, 127)
colVessel = QColor(255, 255, 0)
colMarineMammal = QColor(0, 255, 255)


class Program(QMainWindow):
	nextIm, currIm, prevIm = None, None, None
	dispImg = None
	imageIndex = 0
	imageList = []
	months = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "June",
			  7: "July", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"}

	contactWidg = None

	poi = []

	def __init__(self):
		super(Program, self).__init__()
		self.setWindowTitle('AIS Clicky tool')

		# mode list: '': None, "c": Calibrate
		self.mode = ''
		self.caliWidg = None
		self.reportWin = None
		self.AISRenderDistance = 150000
		self.AISTimeLimit = 60

		self.contactsFolder = ""
		self.caliFolder = ""

		self.contactsDB = Contact_db(self.contactsFolder)
		self.caliDB = Calibration_db(self.caliFolder, 5184, 3456)

		self.rbInWidth = 200
		self.rbExWidth = 240

		self.zoomed = False
		self.zoomOffsets = (0, 0)

		# Set primary layout to window
		self.mainLayout = QHBoxLayout()
		self.mainWidget = QWidget()
		self.mainWidget.setLayout(self.mainLayout)
		self.setCentralWidget(self.mainWidget)
		self.setGeometry(400, 250, 1000, 600)

		self.imWidget = QWidget()
		self.mainLayout.addWidget(self.imWidget)

		self.barWidget = QWidget()
		self.barWidget.setMaximumWidth(self.rbExWidth)
		self.barLayout = QVBoxLayout()
		self.barWidget.setLayout(self.barLayout)
		self.mainLayout.addWidget(self.barWidget)

		# Load a default image. Set a few things here to handle other logic if a list of images
		# hasn't yet been selected
		self.imLabel = QLabel(self.imWidget)
		self.imLabel.mousePressEvent = self.image_event
		self.currIm = QPixmap("sample.jpg")
		self.imLabel.setPixmap(self.currIm)
		self.imLabel.setAlignment(QtCore.Qt.AlignTop)
		self.imLabel.setAlignment(QtCore.Qt.AlignLeft)

		# Set up the right bar

		# Label for the image time
		self.dateLbl = QLabel("Date")
		self.dateLbl.setAlignment(QtCore.Qt.AlignCenter)
		self.timeLbl = QLabel("00:00:00")
		self.timeLbl.setAlignment(QtCore.Qt.AlignCenter)

		self.timeLayout = QHBoxLayout()
		self.timeLayout.addWidget(self.timeLbl)
		self.timeLayout.addWidget(self.dateLbl)
		self.barLayout.addLayout(self.timeLayout)

		# Set up AIS area
		self.aisScrollArea = QScrollArea()
		self.aisScrollArea.setWidgetResizable(True)
		self.aisScrollWidget = QWidget()
		self.aisScrollWidget.setFixedWidth(self.rbInWidth)
		self.aisScrollLayout = QVBoxLayout()

		self.aisScrollWidget.setLayout(self.aisScrollLayout)
		self.aisScrollArea.setWidget(self.aisScrollWidget)
		self.barLayout.addWidget(self.aisScrollArea)

		self.aisBox = AisWidget(self.link_ais, self.reload_display)
		self.aisScrollLayout.addWidget(self.aisBox)

		# Set up new contact area
		self.contactScrollArea = QScrollArea()
		self.contactScrollArea.setWidgetResizable(True)
		self.contactScrollWidget = QWidget()
		self.contactScrollWidget.setFixedWidth(self.rbInWidth)
		self.contactScrollLayout = QVBoxLayout()

		self.contactScrollWidget.setLayout(self.contactScrollLayout)
		self.contactScrollArea.setWidget(self.contactScrollWidget)
		self.barLayout.addWidget(self.contactScrollArea)

		# Label for summary counts
		self.countsLabel = QLabel("0 AIS, 0 non-AIS, 0 marine mammal")
		self.barLayout.addWidget(self.countsLabel)
		self.countsLabel.setAlignment(QtCore.Qt.AlignCenter)

		# Create control buttons, and connect to actions
		self.controlBtnLayout = QGridLayout()
		self.barLayout.addLayout(self.controlBtnLayout)

		self.nextBtn = QPushButton("Next")
		self.nextBtn.clicked.connect(self.next_img)
		self.controlBtnLayout.addWidget(self.nextBtn, 3, 2)

		self.prevBtn = QPushButton("Prev")
		self.prevBtn.clicked.connect(self.prev_img)
		self.controlBtnLayout.addWidget(self.prevBtn, 3, 1)

		self.gotoBtn = QPushButton("Go to image")
		self.gotoBtn.clicked.connect(self.goto_img)
		self.controlBtnLayout.addWidget(self.gotoBtn, 2, 2)

		self.gotoTimeBtn = QPushButton("Go to time")
		self.gotoTimeBtn.clicked.connect(self.goto_img_time)
		self.controlBtnLayout.addWidget(self.gotoTimeBtn, 1, 2)

		self.reloadBtn = QPushButton("Reload")
		self.reloadBtn.clicked.connect(self.reload_display)
		self.controlBtnLayout.addWidget(self.reloadBtn, 1, 1)

		# Label for image count (ex: 'image 203/550')
		self.imIndexLabel = QLabel("Image -/-")
		self.barLayout.addWidget(self.imIndexLabel)
		self.imIndexLabel.setAlignment(QtCore.Qt.AlignCenter)

		# Create "File" menu
		self.statusBar()
		self.mainMenu = self.menuBar()
		self.fileMenu = self.mainMenu.addMenu('&File')

		self.loadImgAction = QAction("&Load images", self)
		self.loadImgAction.setStatusTip('Load a new set of images')
		self.loadImgAction.triggered.connect(self.load_image_set)
		self.fileMenu.addAction(self.loadImgAction)

		# self.loadaisAction = QAction("&Load ais", self)
		# self.loadaisAction.setStatusTip("Load AIS data")
		# self.loadaisAction.triggered.connect(self.load_ais_set)
		# self.fileMenu.addAction(self.loadaisAction)

		self.viewDailySummaryAction = QAction("&Create daily report", self)
		self.viewDailySummaryAction.triggered.connect(self.create_daily_report)
		self.fileMenu.addAction(self.viewDailySummaryAction)

		self.viewMinuteSummaryAction = QAction("&Create minute report", self)
		self.viewMinuteSummaryAction.triggered.connect(self.create_minute_report)
		self.fileMenu.addAction(self.viewMinuteSummaryAction)

		self.saveContactsAction = QAction("&Save contacts", self)
		self.saveContactsAction.triggered.connect(self.save_contact_db)
		self.fileMenu.addAction(self.saveContactsAction)

		self.changeContactsDBAction = QAction("&Change contacts database", self)
		self.changeContactsDBAction.triggered.connect(self.change_contact_db_caller)
		self.fileMenu.addAction(self.changeContactsDBAction)

		self.calibrateModeAction = QAction("&Calibrate mode...", self)
		self.calibrateModeAction.triggered.connect(self.switch_calibrate_mode)
		self.fileMenu.addAction(self.calibrateModeAction)

		self.displayMenu = self.mainMenu.addMenu('&Display')

		self.AISDistanceAction = QAction("&Limit AIS display distance", self)
		self.AISDistanceAction.triggered.connect(self.AIS_toggle_distance_limit)
		self.displayMenu.addAction(self.AISDistanceAction)

		self.AISTimeAction = QAction("&Display time: +/- 1 minute", self)
		self.AISTimeAction.triggered.connect(self.AIS_toggle_time_limit)
		self.displayMenu.addAction(self.AISTimeAction)

		self.reportMenu = self.mainMenu.addMenu('&Generate Report')

		self.viewDailySummaryAction = QAction("&Create daily report", self)
		self.viewDailySummaryAction.triggered.connect(self.create_daily_report)
		self.reportMenu.addAction(self.viewDailySummaryAction)

		self.viewMinuteSummaryAction = QAction("&Create minute report", self)
		self.viewMinuteSummaryAction.triggered.connect(self.create_minute_report)
		self.reportMenu.addAction(self.viewMinuteSummaryAction)

		self.viewMinuteSummaryAction = QAction("&Create vessel report", self)
		self.viewMinuteSummaryAction.triggered.connect(self.create_vessel_report)
		self.reportMenu.addAction(self.viewMinuteSummaryAction)

		# Set up arrow key control
		self.setChildrenFocusPolicy(QtCore.Qt.NoFocus)


		self.show()

		# Get user to select the databases being used (can be changed later)
		self.change_contact_db_caller()

	# def init_georectifier(self, width=5184, height=3456):
	# 	self.geo = Georectifier(width, height, False)
	# 	self.geo.set_camera_pos(48.781065, -123.051861, 25)
	# 	self.geo.set_ref_point(48.732954, -123.029852, 2, 2190, 100)
	# 	self.geo.set_ref_point(48.732631, -123.040011, 2, 3806, 94)
	# 	self.geo.init()

	def setChildrenFocusPolicy(self, policy):
		def recursiveSetChildFocusPolicy(parentQWidget):
			for childQWidget in parentQWidget.findChildren(QWidget):
				childQWidget.setFocusPolicy(policy)
				recursiveSetChildFocusPolicy(childQWidget)

		recursiveSetChildFocusPolicy(self)

	# Occurs whenever a key is pressed
	def keyPressEvent(self, eventQKeyEvent):
		# print(eventQKeyEvent.key())
		keyNum = eventQKeyEvent.key()
		# Left click
		if keyNum == 16777234:
			self.prev_img()
		# Right click
		elif keyNum == 16777236:
			self.next_img()
		QWidget.keyPressEvent(self, eventQKeyEvent)

	# Move to and display the next image in sequence
	def next_img(self):
		if self.imageIndex < len(self.imageList) - 1:
			self.imageIndex += 1
			# Set display to next image
			self.prevIm = self.currIm
			self.currIm = self.nextIm
			self.reload_display(False)

			# Load new next image
			QtCore.QTimer.singleShot(100, self.load_next_img)

	# Move to and display the previous image in sequence
	def prev_img(self):
		if self.imageIndex > 0:
			self.imageIndex -= 1
			# Set display to the previous image
			self.nextIm = self.currIm
			self.currIm = self.prevIm
			self.reload_display(False)

			# Load new previous image (Delay allows for display to update first)
			QtCore.QTimer.singleShot(100, self.load_prev_img)

	# Lets the user select a specific image by index
	def goto_img(self, num=None):
		ok = True
		if type(num) == bool:
			num, ok = QInputDialog.getInt(self, "Jump to image", "Enter a number from 1 to " + str(len(self.imageList)), min=1, max=len(self.imageList))
			if num:
				num -= 1			# Index starting at 0 for program, 1 for user
		if ok:
			self.imageIndex = num
			self.load_curr_img()
			self.reload_display(False)
			QtCore.QTimer.singleShot(100, self.load_next_img)
			QtCore.QTimer.singleShot(100, self.load_prev_img)

	def goto_img_time(self):
		num, ok = QInputDialog.getInt(self, "Jump to time", "Enter a time in form: (day/day)hour/hour/minute/minute/second/second")
		if ok and num >= 10000 and num < 100000000:
			targetTime = file_time(self.imageList[self.imageIndex])[:]
			if num < 1000000:
				targetTime = [targetTime[0], targetTime[1], targetTime[2], num // 10000, num // 100 % 100, num % 100]
			else:
				targetTime = [targetTime[0], targetTime[1], num // 1000000, num // 10000 % 100, num // 100 % 100, num % 100]

			newIndex = self.imageIndex
			maxIndex = len(self.imageList) - 1

			# Will end on the image immediately before the time, or the first image if applicable
			# print("target time:")
			# print(targetTime)

			targSecTime = sec_time(targetTime)
			newSecTime = sec_time(file_time(self.imageList[newIndex]))
			while targSecTime > newSecTime and newIndex < maxIndex:
				newIndex += 1
				newSecTime = sec_time(file_time(self.imageList[newIndex]))
			while targSecTime < newSecTime and newIndex > 0:
				newIndex -= 1
				newSecTime = sec_time(file_time(self.imageList[newIndex]))

			# print("Selected time:")
			# print(file_time(self.imageList[newIndex]))
			self.imageIndex = newIndex
			self.load_curr_img()
			self.reload_display(False)
			QtCore.QTimer.singleShot(100, self.load_next_img)
			QtCore.QTimer.singleShot(100, self.load_prev_img)

	# Refreshes the display to the currIm (Current image), no zoom.
	def reload_display(self, refreshing=True):
		# Reset the image from the source image
		self.zoomed = False
		self.imLabel.setFixedSize(self.imWidget.width(), self.imWidget.height())
		self.dispImg = self.currIm.scaled(self.imLabel.width(), self.imLabel.height(), QtCore.Qt.KeepAspectRatio)

		# Update time label
		time = file_time(self.imageList[self.imageIndex])
		if time > [0, 0, 0, 0, 0, 0]:
			self.dateLbl.setText(self.months[time[1]] + " " + str(time[2]))
			self.timeLbl.setText(self.build_time_string(time))
		else:
			self.timeLbl.setText("-")

		timeObj = datetime.datetime(*time)
		# self.caliDB.update_geo(timeObj)		# unneeded because each caliDB method takes the time as a parameter

		# Reset click-able locations
		self.poi = []

		if self.mode == '':
			# Draw contacts on the image (also sets click-able locations
			self.draw_contacts()

			# Draw AIS lines on the image
			self.draw_ais()

		elif self.mode == 'c':
			# try:
			# 	self.caliWidg.deleteLater()
			# # If it's already been deleted (internally through a cancel or confirm), don't worry
			# except:
			# 	pass
			# timeObj = datetime.datetime(time[0], time[1], time[2], time[3], time[4], time[5])
			# self.caliWidg = CaliEditWidget(datetime, self.caliDB.add_calibration_set)
			# self.contactScrollLayout.addWidget(self.caliWidg)
			# presets = self.caliDB.get_calibration_set(timeObj)
			# if presets:
			# 	self.caliWidg.set_point(presets[0], presets[1])
			# 	self.caliWidg.set_point(presets[2], presets[3])
			#
			if not refreshing:
				self.create_reset_cali_widget()
			self.draw_cali_poi()

		# Update image number and image
		self.imLabel.setPixmap(self.dispImg)
		self.imIndexLabel.setText("Image " + str(self.imageIndex + 1) + "/" + str(len(self.imageList)))



		# Update contact tallies (form: "0 AIS, 0 non-AIS, 0 marine mammal")
		text = str(self.contactsDB.count_ais_contacts()) + " AIS, " \
			   + str(self.contactsDB.count_nonais_contacts()) + " non-AIS\n" \
			   + str(self.contactsDB.count_suspect_contacts()) + " suspect, " \
			   + str(self.contactsDB.count_misc_contacts()) + " marine mammal"
		self.countsLabel.setText(text)

	def draw_contacts(self):
		painter = QPainter()
		painter.begin(self.dispImg)
		non_ais_pen = QPen(colVessel, 2)
		ais_a_pen = QPen(colA, 2)
		ais_b_pen = QPen(colB, 2)
		non_vessel_pen = QPen(colMarineMammal, 2)
		suspect_pen = QPen(colSuspect, 2)
		currTime = file_time(self.imageList[self.imageIndex])
		for contact in self.contactsDB.get_contacts(currTime):

			# Create points for an "X" over the target point
			dist = 5
			# correct for image scaling
			xf = float(self.dispImg.width()) / self.currIm.width()
			yf = float(self.dispImg.height()) / self.currIm.height()
			p1 = (int(contact.x * xf - dist), int(contact.y * yf - dist))
			p2 = (int(contact.x * xf + dist), int(contact.y * yf + dist))
			p3 = (int(contact.x * xf + dist), int(contact.y * yf - dist))
			p4 = (int(contact.x * xf - dist), int(contact.y * yf + dist))

			# Choose colour based on contact details
			if contact.ais == 0:
				painter.setPen(non_ais_pen)
			elif contact.ais == 1:
				painter.setPen(suspect_pen)
			elif contact.ais == -1:
				painter.setPen(non_vessel_pen)
			elif contact.aisClass == "A":
				painter.setPen(ais_a_pen)
			elif contact.aisClass == "B":
				painter.setPen(ais_b_pen)
			# default to non-contact pen:
			else:
				painter.setPen(non_vessel_pen)

			painter.drawLine(p1[0], p1[1], p2[0], p2[1])
			painter.drawLine(p3[0], p1[1], p4[0], p2[1])

			# Make contact click-able
			self.poi.append((contact.x, contact.y, contact))

		painter.end()

	def draw_ais(self):

		painter = QPainter()
		painter.begin(self.dispImg)
		ais_a_pen = QPen(colA, 2)
		ais_b_pen = QPen(colB, 2)

		# correct for image scaling
		xf = float(self.dispImg.width()) / self.currIm.width()
		yf = float(self.dispImg.height()) / self.currIm.height()

		currTime = file_time(self.imageList[self.imageIndex])
		currTimeObj = datetime.datetime(*currTime)

		mmsis = self.caliDB.aisDB.get_mmsis(currTime)
		self.aisBox.change_mmsis(mmsis)
		for mmsi in self.aisBox.get_selected_mmsis():
			if self.caliDB.aisDB.is_A(mmsi):
				painter.setPen(ais_a_pen)
			else:
				painter.setPen(ais_b_pen)
			gpsPoints = self.caliDB.aisDB.get_points(mmsi, currTime)

			#TODO: this doesn't work (won't remove anything) before the georectifier is calibrated (first image)
			# remove points that are beyond our AIS render distance
			i = 0
			while i < len(gpsPoints):
				p = gpsPoints[i]
				# TODO: This shouldn't need to be here, but the first point is glitching.
				# This is a hack-fix, and the root needs to be found
				# NOTE: this might be fixed now, but not tested
				if len(p) < 3:
					gpsPoints.pop(i)
					continue
				# print(p)
				if self.caliDB.get_dist_from_coords(p[1], p[2]) > self.AISRenderDistance:
					gpsPoints.pop(i)
					# print("dropping point with coords:", p[1], p[2], ". Distance: ", self.caliDB.get_dist_from_coords(p[1], p[2]))
				else:
					i += 1

			# Skip track if we don't have enough points to draw it
			if len(gpsPoints) < 2:
				continue
			p = self.caliDB.get_xy(gpsPoints[0][1], gpsPoints[0][2], currTimeObj)
			print(p)
			painter.drawLine(p[0] * xf, p[1] * yf + 5, p[0] * xf, p[1] * yf - 5)

			gpsPoints = []
			pointTime = currTime[:]
			# Negative seconds works fine here due to later processing
			# TODO: start using datetime objects like a normal person
			pointTime[5] -= self.AISTimeLimit
			for i in range(self.AISTimeLimit):
				gpsPoints.append(self.caliDB.aisDB.get_points(mmsi, pointTime)[0])
				pointTime[5] += 2

			p = self.caliDB.get_xy(gpsPoints[1][1], gpsPoints[1][2], currTimeObj)
			for i in range(2, len(gpsPoints)):
				p2 = p
				p = self.caliDB.get_xy(gpsPoints[i][1], gpsPoints[i][2], currTimeObj)
				painter.drawLine(p[0] * xf, p[1] * yf, p2[0] * xf, p2[1] * yf)

		painter.end()

	def show_zoomed(self, x, y):
		# Zooming only makes sense if the image width and height are greater than the display
		if self.imWidget.width() >= self.currIm.width() or self.imWidget.height() >= self.currIm.height():
			return

		self.zoomed = True
		minX = x - self.imWidget.width() // 2
		maxX = x + self.imWidget.width() // 2
		if minX < 0:
			maxX -= minX    # this actually increases maxX
			minX = 0
		if maxX > self.currIm.width():
			minX -= maxX - self.currIm.width()
			maxX = self.currIm.width()

		minY = y - self.imWidget.height() // 2
		maxY = y + self.imWidget.height() // 1
		if minY < 0:
			maxY -= minY   # increases maxY
			minY = 0
		if maxY > self.currIm.height():
			minY -= maxY - self.currIm.height()
			maxY = self.currIm.height()

		self.zoomOffsets = (minX, minY)
		self.dispImg = self.currIm.copy(QtCore.QRect(minX, minY, maxX - minX, maxY - minY))

		if self.mode == 'c':
			self.draw_cali_poi()

		self.imLabel.setPixmap(self.dispImg)

	def load_curr_img(self):
		self.currIm = QPixmap(self.imageList[self.imageIndex])

	def load_next_img(self):
		if self.imageIndex + 1 < len(self.imageList):
			self.nextIm = QPixmap(self.imageList[self.imageIndex + 1])
		else:
			self.nextIm = None

	def load_prev_img(self):
		if self.imageIndex - 1 < len(self.imageList) and self.imageIndex > 0:
			self.prevIm = QPixmap(self.imageList[self.imageIndex - 1])
		else:
			self.prevIm = None

	# Loads a new folder of input images
	def load_image_set(self, folder=None):
		if not folder:
			folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
			if not folder:
				return
		self.imageList = []
		for file in os.listdir(folder):
			if file.endswith('.jpg') or file.endswith('.png'):
				self.imageList.append(os.path.join(folder, file))
		print("Loaded " + str(len(self.imageList)) + " images")
		# Update the pre-loaded images in memory (and the display)
		self.imageIndex = 0
		if len(self.imageList) > 0:
			self.imageList.sort()
			self.currIm = QPixmap(self.imageList[0])
			# self.contactsDB.load_db(file_time(self.imageList[0]))
			self.reload_display(False)
		if len(self.imageList) > 1:
			self.nextIm = QPixmap(self.imageList[1])
		self.prevIm = None

	def create_daily_report(self):
		self.reportWin = GenerateReportGui(self.contactsDB.create_daily_report, self.caliDB, 'daily_report')

	def create_minute_report(self):
		self.reportWin = GenerateReportGui(self.contactsDB.create_minute_report, self.caliDB, 'minute_report')

	def create_vessel_report(self):
		self.reportWin = GenerateReportGui(self.contactsDB.create_vessel_report, self.caliDB, 'vessel_report')

	def change_contact_db_caller(self):
		self.changeDBWin = SwitchContactDatabasePopup(self.change_contact_db)

	def change_contact_db(self, folderName):
		# Save any changes to the current database
		self.contactsDB.save_db()

		# Load new database
		print(folderName)
		self.contactsFolder = folderName
		self.contactsDB = Contact_db(self.contactsFolder)

		# reload the display, unless we don't have any images
		if len(self.imageList) > 0:
			self.reload_display(False)
		self.change_calibrate_db_caller()

	def save_contact_db(self):
		self.contactsDB.save_db()

	# Starts displaying images for the user to go through to calibrate the distance calculations
	# Calibration data is stored in its own database that must be selected on startup (TODO)
	# Disables unnecessary GUI components
	def switch_calibrate_mode(self):
		if self.mode == 'c':
			self.mode = ''
			self.caliDB.save_db()
			# Re-enable file menu options
			self.viewDailySummaryAction.setEnabled(True)
			self.viewMinuteSummaryAction.setEnabled(True)
			self.saveContactsAction.setEnabled(True)
			self.changeContactsDBAction.setEnabled(True)
			self.calibrateModeAction.setText("&Calibration mode...")

			self.gotoTimeBtn.setEnabled(True)

			# return buttons to original functionality
			self.nextBtn.clicked.disconnect()
			self.nextBtn.clicked.connect(self.next_img)

			self.prevBtn.clicked.disconnect()
			self.prevBtn.clicked.connect(self.prev_img)

			self.gotoBtn.clicked.disconnect()
			self.gotoBtn.setText("Go to image")
			self.gotoBtn.clicked.connect(self.goto_img)

			try:
				self.caliWidg.deleteLater()
			except:
				pass

			self.reload_display(False)

		else:
			self.mode = 'c'
			# disable unnecessary file menu options
			self.viewDailySummaryAction.setEnabled(False)
			self.viewMinuteSummaryAction.setEnabled(False)
			self.saveContactsAction.setEnabled(False)
			self.changeContactsDBAction.setEnabled(False)
			self.calibrateModeAction.setText("&Exit Calibration mode")
			self.gotoTimeBtn.setEnabled(False)

			# change buttons to link to our new methods
			self.nextBtn.clicked.disconnect()
			self.nextBtn.clicked.connect(self.next_image_cali_mode)

			self.prevBtn.clicked.disconnect()
			self.prevBtn.clicked.connect(self.prev_image_cali_mode)

			self.gotoBtn.clicked.disconnect()
			self.gotoBtn.setText("Calibrate next")
			self.gotoBtn.clicked.connect(self.seek_next_cali_img)

			try:
				self.contactWidg.deleteLater()
			except:
				pass

			self.reload_display(False)

	# Go to the next image that has either has calibration data, or needs it.
	def next_image_cali_mode(self):
		self.nextBtn.setEnabled(False)
		self.prevBtn.setEnabled(False)

		imIndex = self.imageIndex
		while imIndex < len(self.imageList) - 1:
			imIndex += 1
			time = file_time(self.imageList[imIndex])
			timeObj = datetime.datetime(*time)
			if self.caliDB.get_calibration_set(timeObj) or not self.caliDB.is_calibrated(timeObj):
				break
		self.goto_img(imIndex)

		self.nextBtn.setEnabled(True)
		self.prevBtn.setEnabled(True)

	# Go to the previous image that either has calibration data, or needs it.
	def prev_image_cali_mode(self):
		self.nextBtn.setEnabled(False)
		self.prevBtn.setEnabled(False)

		imIndex = self.imageIndex
		while imIndex > 0:
			imIndex -= 1
			time = file_time(self.imageList[imIndex])
			timeObj = datetime.datetime(*time)
			if self.caliDB.get_calibration_set(timeObj) or not self.caliDB.is_calibrated(timeObj):
				break
		self.goto_img(imIndex)

		self.nextBtn.setEnabled(True)
		self.prevBtn.setEnabled(True)

	def create_reset_cali_widget(self):
		try:
			self.caliWidg.deleteLater()
		# If it's already been deleted (internally through a cancel or confirm), don't worry
		except:
			pass
		time = file_time(self.imageList[self.imageIndex])
		timeObj = datetime.datetime(time[0], time[1], time[2], time[3], time[4], time[5])
		self.caliWidg = CaliEditWidget(timeObj, self.caliDB.add_calibration_set, self.reload_display)
		self.contactScrollLayout.addWidget(self.caliWidg)
		presets = self.caliDB.get_calibration_set(timeObj)
		if presets:
			self.caliWidg.set_point(presets[0][0], presets[0][1], True)
			self.caliWidg.set_point(presets[1][0], presets[1][1], True)

	# Go to the next image that needs calibration data
	def seek_next_cali_img(self):
		self.nextBtn.setEnabled(False)
		self.prevBtn.setEnabled(False)

		imIndex = self.imageIndex
		while imIndex < len(self.imageList) - 1:
			imIndex += 1
			time = file_time(self.imageList[imIndex])
			timeObj = datetime.datetime(*time)
			if not self.caliDB.is_calibrated(timeObj):
				break
		self.goto_img(imIndex)

		self.nextBtn.setEnabled(True)
		self.prevBtn.setEnabled(True)

	def draw_cali_poi(self):
		if self.caliWidg:
			caliPoints = self.caliWidg.get_points()
			if not caliPoints:
				return

			painter = QPainter()
			painter.begin(self.dispImg)
			pen = QPen(QtCore.Qt.red, 2)

			for i, cali in enumerate(caliPoints):

				# Create points for an "X" over the target point
				dist = 5

				p1, p2, p3, p4 = 0, 0, 0, 0
				if not self.zoomed:
					# correct for image scaling
					xf = float(self.dispImg.width()) / self.currIm.width()
					yf = float(self.dispImg.height()) / self.currIm.height()
					p1 = (int(cali[0] * xf - dist), int(cali[1] * yf - dist))
					p2 = (int(cali[0] * xf + dist), int(cali[1] * yf + dist))
					p3 = (int(cali[0] * xf + dist), int(cali[1] * yf - dist))
					p4 = (int(cali[0] * xf - dist), int(cali[1] * yf + dist))

				else:
					# set offsets
					p1 = (int(cali[0] - self.zoomOffsets[0] - dist), int(cali[1] - self.zoomOffsets[1] - dist))
					p2 = (int(cali[0] - self.zoomOffsets[0] + dist), int(cali[1] - self.zoomOffsets[1] + dist))
					p3 = (int(cali[0] - self.zoomOffsets[0] + dist), int(cali[1] - self.zoomOffsets[1] - dist))
					p4 = (int(cali[0] - self.zoomOffsets[0] - dist), int(cali[1] - self.zoomOffsets[1] + dist))


				painter.setPen(pen)

				painter.drawLine(p1[0], p1[1], p2[0], p2[1])
				painter.drawLine(p3[0], p1[1], p4[0], p2[1])

			painter.end()
			self.imLabel.setPixmap(self.dispImg)

	def update_cali(self, x, y):
		if self.caliWidg:
			self.caliWidg.set_point(x, y)

	def change_calibrate_db_caller(self):
		self.changeDBWin = SwitchCalibrateDatabasePopup(self.change_calibrate_db)

	def change_calibrate_db(self, folderName):
		# Save any changes to the current database
		self.caliDB.save_db()

		# Load new database
		print(folderName)
		self.caliFolder = folderName
		self.caliDB = Calibration_db(self.caliFolder, 5184, 3456)
		if not self.caliDB.dbLoaded:
			print('warning: calibration database did not load metadata properly')

		# reload the display, unless we don't have any images
		if len(self.imageList) > 0:
			self.reload_display()

	def AIS_toggle_distance_limit(self):
		if self.AISRenderDistance == 150000:
			self.AISRenderDistance = 2000
			self.AISDistanceAction.setText("&Stop limiting AIS distance")
			self.AISDistanceAction.setToolTip("Limit: 2000 meters")
		else:
			self.AISRenderDistance = 150000
			self.AISDistanceAction.setText("&Limit AIS display distance")
			self.AISDistanceAction.setToolTip("Currently unlimited. Limit if enabled: 2000 meters")

		self.reload_display()

	def AIS_toggle_time_limit(self):
		if self.AISTimeLimit == 60:
			self.AISTimeLimit = 120
			self.AISTimeAction.setText("&Display time: +/- 2 minutes")
		elif self.AISTimeLimit == 120:
			self.AISTimeLimit = 300
			self.AISTimeAction.setText("&Display time: +/- 5 minutes")
		else:
			self.AISTimeLimit = 60
			self.AISTimeAction.setText("&Display time: +/- 1 minute")

		# Update the database and display
		# time_offsets is for the database determining if a point is active
		# self.AISTimeLimit adjusts the actual drawing
		self.caliDB.aisDB.set_time_offsets(self.AISTimeLimit)
		self.reload_display()

	def image_event(self, event):

		# Distance for editing existing contacts
		dist = 10 * (float(self.currIm.width()) / self.dispImg.width())
		if self.zoomed:
			y = event.pos().y() + self.zoomOffsets[1]
			x = event.pos().x() + self.zoomOffsets[0]

			if event.button() == QtCore.Qt.LeftButton:
				if self.mode == '':
					self.create_contact(x, y)
				elif self.mode == 'c':
					self.update_cali(x, y)
			elif event.button() == QtCore.Qt.RightButton:
				self.reload_display()
			elif event.button() == QtCore.Qt.MidButton:
				pass
		else:
			y = int(event.pos().y() * (float(self.currIm.height()) / self.dispImg.height()))
			x = int(event.pos().x() * (float(self.currIm.width()) / self.dispImg.width()))
			if event.button() == QtCore.Qt.LeftButton:
				for p in self.poi:
					if abs(p[0] - x) <= dist and abs(p[1] - y) <= dist:
						self.edit_contact(p[2])
						return
				if self.mode == '':
					self.create_contact(x, y)
				elif self.mode == 'c':
					self.update_cali(x, y)
			elif event.button() == QtCore.Qt.RightButton:
				self.show_zoomed(x, y)

	def create_contact(self, x, y):
		try:
			self.contactWidg.deleteLater()
		# If it's already been deleted (internally through a cancel or confirm), don't worry
		except:
			pass
		geo = self.caliDB.get_geopoint_from_xy(x, y, 0, datetime.datetime(*file_time(self.imageList[self.imageIndex])))
		self.contactWidg = ContactWidget(file_time(self.imageList[self.imageIndex]), x, y, self.contactsDB,
					geo.dist, geo.lat, geo.lon, self.reload_display)
		self.contactScrollLayout.addWidget(self.contactWidg)

	def edit_contact(self, contact):
		try:
			self.contactWidg.deleteLater()
		# It's already been deleted (by the user through a cancel or confirm). Don't worry
		except:
			pass
		self.contactWidg = ContactEditWidget(contact, self.contactsDB, self.reload_display)
		self.contactScrollLayout.addWidget(self.contactWidg)

	@staticmethod
	def build_time_string(time):
		res = str(time[3]) + ":"
		if time[4] < 10:
			res += "0"
		res += str(time[4]) + ":"
		if time[5] < 10:
			res += "0"
		return res + str(time[5])

	# Save database when the program is exited - name as required by pyqt
	# Also writes 'metadata' to be loaded the next time the program is started
	def closeEvent(self, event):
		self.contactsDB.save_db()
		self.caliDB.save_db()
		with open('meta.txt', 'w+') as meta:
			meta.write('contacts_db=' + str(self.contactsFolder) + '\n')

	# # Loads settings on start-up
	# def load_metadata(self):
	# 	try:
	# 		with open('meta.txt', 'r') as meta:
	# 			for line in meta:
	# 				if re.search(r"^contacts_db=.+", line):
	# 					self.contactsFolder = line.split('=')[1].rstrip()
	# 	except:
	# 		print("Cannot read meta.txt")
	# 		self.contactsFolder = "contacts_db1"

	def link_ais(self, mmsi):
		if self.contactWidg:
			self.contactWidg.link_ais(mmsi, self.caliDB.aisDB.is_A(mmsi))

	def demo_init(self):
		self.load_image_set("C:/Workspace/clickytool/Vessels")


def main():
	app = QApplication(sys.argv)
	ex = Program()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()
