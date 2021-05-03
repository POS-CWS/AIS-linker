from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from functools import partial
import os
import re

from contacts_db import Contact, Contact_db


class ContactWidget(QWidget):

	def __init__(self, time, x, y, targetDB, distance, lat, lon, on_finish=None):
		super(ContactWidget, self).__init__()
		self.aisCode = 0
		self.aisTag = ""
		self.activitySelects = []
		self.directionSelects = []
		self.content = []

		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		self.topLayout = QVBoxLayout()
		self.botLayout = QVBoxLayout()
		self.layout.addLayout(self.topLayout)
		self.layout.addLayout(self.botLayout)

		self.label = QLabel("New Contact")
		self.topLayout.addWidget(self.label)

		self.distLbl = QLabel("Distance: " + str(int(distance)) + "m")
		self.topLayout.addWidget(self.distLbl)

		self.coordsLbl = QLabel("{:.6f}, {:.6f}".format(lat, lon))
		self.topLayout.addWidget(self.coordsLbl)

		aisBtn = QPushButton("AIS")
		aisBtn.clicked.connect(self.ais)
		self.topLayout.addWidget(aisBtn)
		self.content.append(aisBtn)

		susBtn = QPushButton("Suspect AIS")
		susBtn.clicked.connect(self.suspect)
		self.topLayout.addWidget(susBtn)
		self.content.append(susBtn)

		nonAisBtn = QPushButton("Non-AIS")
		nonAisBtn.clicked.connect(self.non_ais)
		self.topLayout.addWidget(nonAisBtn)
		self.content.append(nonAisBtn)

		nonVesselBtn = QPushButton("Marine Mammal")
		nonVesselBtn.clicked.connect(self.nonvessel)
		self.topLayout.addWidget(nonVesselBtn)
		self.content.append(nonVesselBtn)

		cancelBtn = QPushButton("Cancel")
		cancelBtn.clicked.connect(self.deleteLater)
		self.topLayout.addWidget(cancelBtn)

		self.time = time
		self.x = x
		self.y = y
		self.db = targetDB
		self.distance = distance
		self.lat = lat
		self.lon = lon
		self.on_finish = on_finish

		self.tags = ""
		self.vesselType = ""

		self.tagsField = QLineEdit()
		self.confirmBtn = QPushButton("Confirm")
		self.aisLbl = QLabel("Waiting for ais...")
		self.repeatBox = QCheckBox("Repeat")
		self.repeatBox.setToolTip("Skip counting this contact when generating most reports")

	def populateLowerContent(self):
		self.botLayout.addWidget(self.tagsField)
		self.botLayout.addWidget(self.repeatBox)
		self.botLayout.addWidget(self.confirmBtn)
		self.confirmBtn.clicked.connect(self.save_contact)

	def ais(self, event, fromStart=True):
		self.aisCode = 2
		self.clear_content()
		if fromStart:
			self.topLayout.addWidget(self.aisLbl)
			self.populateLowerContent()

		self.types =  ["Cargo", "Cruise ship", "EcoTourism", "Ferry", "Fishing", "Pleasure craft",
					   "Sailing vessel", "Tanker", "Tug", "Misc."]

		# self.types = ["Cargo", "Container Ship", "Tanker", "Naval Vessel", "Ferry", "Fishing",
		# 			  "Ecotourism", "Research/Coastguard", "Tug", "Sailboat", "Pleasurecraft", "Charter fishing",
		# 			  "Misc."]

		for type in self.types:
			btn = QPushButton(type)
			self.topLayout.addWidget(btn)
			self.content.append(btn)
			btn.clicked.connect(partial(self.activity_select, type, True))


	def link_ais(self, mmsi, isA):
		# Prevents us from assigning ais to a non-ais or mammal contact
		if self.aisCode > 0:
			self.aisCode = mmsi
			if isA:
				self.aisTag = "A"
			else:
				self.aisTag = "B"
			self.aisLbl.setText(str(mmsi) + " (" + self.aisTag + ")")

	def suspect(self, event, fromStart=True):
		self.aisCode = 1
		self.clear_content()

		self.types =  ["Cargo", "Cruise ship", "EcoTourism", "Ferry", "Fishing", "Pleasure craft",
					   "Sailing vessel", "Tanker", "Tug", "Misc."]

		# self.types = ["Cargo", "Container Ship", "Tanker", "Naval Vessel", "Ferry", "Fishing",
		# 			  "Ecotourism", "Research/Coastguard", "Tug", "Sailboat", "Pleasurecraft", "Charter fishing",
		# 			  "Misc."]
		for type in self.types:
			btn = QPushButton(type)
			self.topLayout.addWidget(btn)
			self.content.append(btn)
			btn.clicked.connect(partial(self.activity_select, type, True))

		if fromStart:
			self.populateLowerContent()

	def non_ais(self, event, fromStart=True):
		self.aisCode = 0
		self.clear_content()

		self.types = ["Motorboat", "Sailboat", "Comercial fishing", "Sport fishing", "Ecotourism",
					  "Tug", "Kayak", "UnID vessel", "Misc."]

		for type in self.types:
			btn = QPushButton(type)
			self.topLayout.addWidget(btn)
			self.content.append(btn)
			btn.clicked.connect(partial(self.activity_select, type, True))

		if fromStart:
			self.populateLowerContent()

	def nonvessel(self, event, fromStart=True):
		self.aisCode = -1
		self.clear_content()

		self.types = ["Killer Whale", "Humpback Whale", "Harbour Porpoise",
					  "Dall's Porpoise", "Sealion", "Misc."]

		for type in self.types:
			btn = QPushButton(type)
			self.topLayout.addWidget(btn)
			self.content.append(btn)
			btn.clicked.connect(partial(self.activity_select, type, False))

		if fromStart:
			self.populateLowerContent()

	def activity_select(self, vesselType, isVessel):
		self.vesselType = vesselType
		self.clear_content()
		if isVessel:
			activityTypes = ["Trolling", "Jigging", "UnID fishing", "Transiting",
							 "Stationary non-fishing", "Marine mammal viewing"]
		else:
			activityTypes = ["Resting", "Travelling", "Foraging", "Socializing", "Unknown", "Misc"]

		typeLabel = QLabel(vesselType)
		self.topLayout.addWidget(typeLabel)
		self.content.append(typeLabel)
		self.activityRadioGroup = QButtonGroup()

		for activity in activityTypes:
			btn = QRadioButton(activity)
			self.activityRadioGroup.addButton(btn)
			self.content.append(btn)
			self.topLayout.addWidget(btn)
			self.activitySelects.append(btn)

		divider = QHLine()
		self.content.append(divider)
		self.topLayout.addWidget(divider)
		directionLabel = QLabel("Direction of travel:")
		self.topLayout.addWidget(directionLabel)
		self.content.append(directionLabel)

		self.directionRadioGroup = QButtonGroup()

		for direction in ["North", "South"]:
			btn = QRadioButton(direction)
			self.directionRadioGroup.addButton(btn)
			self.content.append(btn)
			self.topLayout.addWidget(btn)
			self.directionSelects.append(btn)


	def save_contact(self):
		# If declared as ais and no ais added yet, don't do anything:
		if self.aisCode == 2:
			return
		# Add positional data, category, and activity as tags
		tags = "dist=" + str(self.distance)
		tags += ",lat=" + str(self.lat) + ",lon=" + str(self.lon)
		tags += ",type=" + self.vesselType
		for btn in self.activitySelects:
			if btn.isChecked():
				tags += ",activity="
				tags += btn.text()
		for btn in self.directionSelects:
			if btn.isChecked():
				tags += ",direction="
				tags += btn.text()
		if self.repeatBox.isChecked():
			tags += ",repeat=True"
		# Add any other tags
		tags += ","
		tags += self.tagsField.text()
		# check if AIS A or B (defaults to B)
		c = Contact(self.time, self.x, self.y, self.aisCode, self.aisTag, tags)
		self.db.add_contact(c)
		if self.on_finish:
			self.on_finish()
		self.deleteLater()

	def clear_content(self):
		for item in self.content:
			item.deleteLater()
		self.content = []
		self.activitySelects = []


# TODO: improve this interface. Maybe allow for linking to AIS?
class ContactEditWidget(QWidget):
	def __init__(self, contact, contact_db, on_finish=None):
		super(ContactEditWidget, self).__init__()
		self.db = contact_db
		self.contact = contact
		self.on_finish = on_finish

		self.layout = QVBoxLayout()
		self.setLayout(self.layout)

		# Add ais information if applicable
		self.aisTag = QLabel(str(contact.ais) + " (" + contact.aisClass + ")")
		if contact.ais > 0:
			self.layout.addWidget(self.aisTag)

		self.infoLabel = QLabel("Edit Contact tags:")
		self.layout.addWidget(self.infoLabel)

		self.tagsLabel = QTextEdit()
		self.tagsLabel.setText(contact.tags)
		self.layout.addWidget(self.tagsLabel)

		self.confirmBtn = QPushButton("Save changes")
		self.confirmBtn.clicked.connect(self.confirm_change)
		self.layout.addWidget(self.confirmBtn)

		self.cancelBtn = QPushButton("Cancel")
		self.cancelBtn.clicked.connect(self.cancel_change)
		self.layout.addWidget(self.cancelBtn)

		self.delBtn = QPushButton("Delete contact")
		self.delBtn.clicked.connect(self.delete_contact)
		self.layout.addWidget(self.delBtn)

	def confirm_change(self):
		self.contact.tags = self.tagsLabel.text()
		self.db.update_contact(self.contact)
		if self.on_finish:
			self.on_finish()
		self.deleteLater()

	def cancel_change(self):
		if self.on_finish:
			self.on_finish()
		self.deleteLater()

	def delete_contact(self):
		self.db.remove_contact(self.contact)
		if self.on_finish:
			self.on_finish()
		self.deleteLater()


class AisWidget(QWidget):
	def __init__(self, link_func, update_func=None):
		super(AisWidget, self).__init__()
		self.layout = QVBoxLayout()
		self.setLayout(self.layout)
		self.aisLayouts = []
		self.boxes = []
		self.btns = []
		self.mmsis = []
		self.ignoreList = []
		self.link_func = link_func
		self.update_func = update_func

	def change_mmsis(self, mmsis):
		mmsis = list(map(str, mmsis))
		# Remove old tracks
		for box in self.boxes:
			box.deleteLater()
		for btn in self.btns:
			btn.deleteLater()
		for l in self.aisLayouts:
			l.deleteLater()

		self.boxes = []
		self.btns = []
		self.aisLayouts = []
		self.mmsis = mmsis

		# Add new tracks
		for mmsi in mmsis:
			box = QCheckBox(mmsi)
			btn = QPushButton("Link")
			btn.setFixedWidth(50)
			lay = QHBoxLayout()
			if mmsi not in self.ignoreList:
				box.setChecked(True)
			else:
				box.setChecked(False)
			lay.addWidget(box)
			self.boxes.append(box)
			box.stateChanged.connect(self.on_change)

			btn.clicked.connect(partial(self.link_func, int(mmsi)))
			lay.addWidget(btn)
			self.btns.append(btn)

			self.aisLayouts.append(lay)
			self.layout.addLayout(lay)

		# Update ignore list
		ignoreList = []
		for mmsi in self.ignoreList:
			if mmsi in self.mmsis:
				ignoreList.append(mmsi)
		self.ignoreList = ignoreList

	def on_change(self):
		# update ignore list
		self.ignoreList = []
		for box in self.boxes:
			if not box.isChecked():
				self.ignoreList.append(str(box.text()))

		self.update_func()

	def get_selected_mmsis(self):
		retList = []
		for mmsi in self.mmsis:
			if mmsi not in self.ignoreList:
				retList.append(int(mmsi))

		return retList


class CaliEditWidget(QWidget):
	def __init__(self, time, update_func=None, reset_func=None):
		super(CaliEditWidget, self).__init__()
		self.layout = QGridLayout()
		self.setLayout(self.layout)
		self.update_func = update_func
		self.reset_funct = reset_func
		self.time = time

		self.pointLbls = []
		self.resetbtns = []

		for i in range(2):
			self.pointLbls.append(QLabel('( , )'))
			self.layout.addWidget(self.pointLbls[i], 0, i)

			self.resetbtns.append(QPushButton("reset\npoint " + str(i + 1)))
			self.resetbtns[i].setEnabled(False)
			self.layout.addWidget(self.resetbtns[i], 1, i)
			self.resetbtns[i].clicked.connect(partial(self.reset_point, i))

	def set_point(self, x, y, initializing=False):
		for i, lbl in enumerate(self.pointLbls):
			if str(lbl.text()) == '( , )':
				lbl.setText("(" + str(x) + "," + str(y) + ")")
				self.resetbtns[i].setEnabled(True)
				if (not initializing) and self.check_for_completed():
					self.save_point()
				if self.reset_funct:
					self.reset_funct()
				return

	def reset_point(self, i):
		self.pointLbls[i].setText('( , )')
		self.resetbtns[i].setEnabled(False)
		if self.reset_funct:
			self.reset_funct()

	def check_for_completed(self):
		for lbl in self.pointLbls:
			if not re.match(r'\((\d+),(\d+)\)', str(lbl.text())):
				return False
		return True

	def save_point(self):
		print('saving calibration data to memory')
		points = []
		for lbl in self.pointLbls:
			m = re.match(r'\((\d+),(\d+)\)', str(lbl.text()))
			points.extend([int(m.group(1)), int(m.group(2))])
		self.update_func(points[0], points[1], points[2], points[3], self.time)

	# returns ((x1, y1), (x2, y2))
	def get_points(self):
		points = []
		for lbl in self.pointLbls:
			m = re.match(r'\((\d+),(\d+)\)', str(lbl.text()))
			if m:
				points.append((int(m.group(1)), int(m.group(2))))
		return points


class GenerateReportGui(QWidget):
	def __init__(self, targetFunc, caliDB, defaultReportName="report"):
		super(GenerateReportGui, self).__init__()

		self.targFunc = targetFunc
		self.caliDB = caliDB

		# Set primary layout to window
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)
		self.setGeometry(400, 250, 1000, 600)

		# Create and position calendar widgets
		self.calLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.calLayout)
		self.cal = QCalendarWidget()
		self.cal2 = QCalendarWidget()
		self.calLayout.addWidget(self.cal)
		self.calLayout.addWidget(self.cal2)

		# Add place to change the file name
		self.repNameLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.repNameLayout)
		self.repNameLbl = QLabel("Report name:")
		self.repNameLayout.addWidget(self.repNameLbl)
		self.repNameEdit = QLineEdit()
		self.repNameEdit.setText(defaultReportName)
		self.repNameEdit.textChanged.connect(self.verify_path)
		self.repNameLayout.addWidget(self.repNameEdit)

		self.cancelBtn = QPushButton("Cancel")
		self.cancelBtn.clicked.connect(self.deleteLater)
		self.mainLayout.addWidget(self.cancelBtn)

		self.confirmBtn = QPushButton("Generate Report")
		self.confirmBtn.clicked.connect(self.call_targ_func)
		self.mainLayout.addWidget(self.confirmBtn)

		self.show()
		self.verify_path()

	# checks if the filename chosen already
	def verify_path(self):
		fileName = str(self.repNameEdit.text()) + '.csv'
		if os.path.exists(fileName):
			self.confirmBtn.setText("File already exists")
			self.confirmBtn.setEnabled(False)
		else:
			self.confirmBtn.setText("Generate Report")
			self.confirmBtn.setEnabled(True)

	def call_targ_func(self):
		start = list(self.cal.selectedDate().getDate())
		end = list(self.cal2.selectedDate().getDate())
		self.targFunc(start, end, self.caliDB, str(self.repNameEdit.text()) + '.csv')
		self.deleteLater()


# Popup window for allowing the user to change the database
class SwitchContactDatabasePopup(QWidget):
	def __init__(self, targetFunc):
		super(SwitchContactDatabasePopup, self).__init__()
		self.setWindowTitle('Select a contact database')

		self.folderList = []
		self.targetFunc = targetFunc

		# Find all folders that look like contact databases
		for folder in os.listdir(os.getcwd()):
			if os.path.isdir(folder) and re.search(r"contacts_db_.+", folder):
				self.folderList.append(folder)

		# Set primary layout to window
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)
		# self.setGeometry(400, 250, 1000, 600)

		# Create a button for each data set
		pos = 1
		for folder in self.folderList:
			text = folder[12:]
			try:
				with open(os.path.join(folder, "info.txt"), 'r') as infoFile:
					text += "\n" + infoFile.read()
					# truncate the file if someone writes a ludicrous description
					if len(text) > 500:
						text = text[0:500]
					btn = QPushButton(text)
					btn.clicked.connect(partial(self.on_select, folder))
					self.mainLayout.addWidget(btn)
			except:
				print("Warning: could not read folder " + folder + ". Skipping")
				continue

		# Add option at bottom to create a new database at bottom
		self.endSpacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.mainLayout.addSpacerItem(self.endSpacer)
		self.createNewBtn = QPushButton("Create new data set")
		self.createNewBtn.clicked.connect(self.create_new_database)
		self.createNewBtn.setEnabled(False)
		self.mainLayout.addWidget(self.createNewBtn)

		# force window on front. Note: this line must be before self.show()
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.show()

	def on_select(self, folder):
		if folder:
			self.targetFunc(folder)
		self.deleteLater()

	def create_new_database(self):
		pass


# Popup window for allowing the user to change the database
class SwitchCalibrateDatabasePopup(QWidget):
	def __init__(self, targetFunc):
		super(SwitchCalibrateDatabasePopup, self).__init__()
		self.setWindowTitle('Select a calibration database')

		self.folderList = []
		self.targetFunc = targetFunc

		# Find all folders that look like calibration databases
		for folder in os.listdir(os.getcwd()):
			if os.path.isdir(folder) and re.search(r"calibration_db_.+", folder):
				self.folderList.append(folder)

		# Set primary layout to window
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)
		# self.setGeometry(400, 250, 1000, 600)

		# Create a button for each data set
		for folder in self.folderList:
			text = folder[15:]
			try:
				with open(os.path.join(folder, "info.txt"), 'r') as infoFile:
					text += "\n" + infoFile.read()
					# truncate the file if someone writes a ludicrous description
					if len(text) > 500:
						text = text[0:500]
					btn = QPushButton(text)
					btn.clicked.connect(partial(self.on_select, folder))
					self.mainLayout.addWidget(btn)
			except:
				print("Warning: could not read folder " + folder + ". Skipping")
				continue

		# Add option at bottom to create a new database at bottom
		self.endSpacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.mainLayout.addSpacerItem(self.endSpacer)
		self.createNewBtn = QPushButton("Create new data set")
		self.createNewBtn.clicked.connect(self.create_new_database)
		self.createNewBtn.setEnabled(False)
		self.mainLayout.addWidget(self.createNewBtn)

		# force window to front. Note: this line must be before self.show()
		self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
		self.show()

	def on_select(self, folder):
		if folder:
			self.targetFunc(folder)
		self.deleteLater()

	def create_new_database(self):
		pass


# GUI unit for recalibrating the georectifier. Is NOT persistent between sessions
class recalibrate(QWidget):
	def __init__(self, targetFunc):
		super(recalibrate, self).__init__()


# https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
class QHLine(QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)