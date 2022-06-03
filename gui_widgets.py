from PyQt5 import QtGui, QtCore, uic, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from functools import partial
import os
import re

from contacts_db import Contact, Contact_db

archivedPrefix = "archived_"


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


# ---------------------------

class DatabaseSelector(QWidget):
	def __init__(self, type, setVariableFunc):
		super(DatabaseSelector, self).__init__()
		self.setVariableFunc = setVariableFunc
		self.content = []

		typeText = 'calibration' if type == 'cali' else 'contacts'
		self.folderPrefix = 'calibration_db_' if type == 'cali' else 'contacts_db_'
		self.type = type

		self.setWindowTitle('Select {} database'.format(typeText))

		# Set primary layout to window
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)
		# self.setGeometry(450, 300, 400, 500)

		# Set up scroll area
		self.scrollArea = QScrollArea()
		self.scrollArea.setWidgetResizable(True)
		self.scrollWidget = QWidget()
		self.scrollLayout = QVBoxLayout()

		self.scrollWidget.setLayout(self.scrollLayout)
		self.scrollArea.setWidget(self.scrollWidget)
		self.mainLayout.addWidget(self.scrollArea)

		self.populate_scroll_area()

		# Add general buttons at the bottom
		hLayout = QHBoxLayout()
		self.mainLayout.addLayout(hLayout)

		newBtn = QPushButton("Create new database")
		newBtn.clicked.connect(self.on_edit)
		hLayout.addWidget(newBtn)

		hSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
		hLayout.addSpacerItem(hSpacer)

		recoverArchivedBtn = QPushButton("Recover archived databases")
		recoverArchivedBtn.clicked.connect(self.on_recover_archived)
		hLayout.addWidget(recoverArchivedBtn)

		self.show()

	def populate_scroll_area(self):
		# Start by removing all old stuff here
		for item in self.content:
			item.deleteLater()
		self.content = []

		# Find all folders that look like the correct type of database
		folderList = []
		for folder in os.listdir(os.getcwd()):
			if os.path.isdir(folder) and re.match(self.folderPrefix, folder):
				folderList.append(folder)

		# Add each to scroll area
		for folder in folderList:
			name = folder[len(self.folderPrefix):]
			try:
				with open(os.path.join(folder, "info.txt"), 'r') as infoFile:
					description = infoFile.read()
					# truncate the file if someone writes a ludicrous description
					if len(description) > 500:
						description = description[0:500] + '...'

					hLayout = QHBoxLayout()
					self.scrollLayout.addLayout(hLayout)

					nameLbl = QLabel(name)
					hLayout.addWidget(nameLbl)

					selectBtn = QPushButton("Select")
					selectBtn.clicked.connect(partial(self.on_select, folder))
					hLayout.addWidget(selectBtn)

					editBtn = QPushButton("Edit")
					editBtn.clicked.connect(partial(self.on_edit, folder))
					hLayout.addWidget(editBtn)

					archiveBtn = QPushButton("Archive")
					archiveBtn.clicked.connect(partial(self.on_archive, folder))
					hLayout.addWidget(archiveBtn)

					selectBtn.setMaximumWidth(80)
					selectBtn.setMinimumWidth(80)
					editBtn.setMaximumWidth(80)
					editBtn.setMinimumWidth(80)
					archiveBtn.setMaximumWidth(80)
					archiveBtn.setMinimumWidth(80)

					descriptionLbl = QLabel(description)
					descriptionLbl.setWordWrap(True)
					self.scrollLayout.addWidget(descriptionLbl)

					self.content.extend([nameLbl, descriptionLbl, selectBtn, editBtn, archiveBtn])

			except:
				print("Warning: could not read folder " + folder + ". Skipping")
				continue

	def on_select(self, foldername):
		if foldername:
			self.setVariableFunc(foldername)
		self.deleteLater()

	def on_edit(self, foldername=None):
		creator = Cali_DB_constructor if self.type == 'cali' else Contacts_DB_constructor
		self.databaseCreateEdit = creator(self.populate_scroll_area, foldername)

	def on_archive(self, foldername):
		global archivedPrefix
		msgbox = QMessageBox(QMessageBox.Question, "Confirm archive",
							 "Are you sure you want to archive {}?".format(foldername[len(self.folderPrefix):]))
		msgbox.addButton(QMessageBox.Yes)
		msgbox.addButton(QMessageBox.Cancel)

		reply = msgbox.exec()
		if reply != QMessageBox.Yes:
			return

		os.rename(foldername, archivedPrefix + foldername)
		self.populate_scroll_area()

	def on_recover_archived(self):
		self.recoverer = Database_recoverer(self.type, self.populate_scroll_area)


class Database_recoverer(QWidget):
	def __init__(self, type, onDeleteCallback):
		super(Database_recoverer, self).__init__()

		self.folderPrefix = 'calibration_db_' if type == 'cali' else 'contacts_db_'
		self.content = []
		self.onDeleteCallback = onDeleteCallback

		typeText = 'calibration' if type == 'cali' else 'contacts'
		self.setWindowTitle('Restore archived {} databases'.format(typeText))

		# Set primary layout to window
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)

		# Set up scroll area
		self.scrollArea = QScrollArea()
		self.scrollArea.setWidgetResizable(True)
		self.scrollWidget = QWidget()
		self.scrollLayout = QVBoxLayout()

		self.scrollWidget.setLayout(self.scrollLayout)
		self.scrollArea.setWidget(self.scrollWidget)
		self.mainLayout.addWidget(self.scrollArea)

		self.populate_scroll_area()

		# Add close button at the bottom
		hLayout = QHBoxLayout()
		self.mainLayout.addLayout(hLayout)

		hSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
		hLayout.addSpacerItem(hSpacer)

		recoverArchivedBtn = QPushButton("Done")
		recoverArchivedBtn.clicked.connect(self.close_window)
		hLayout.addWidget(recoverArchivedBtn)

		self.show()

	def populate_scroll_area(self):
		global archivedPrefix
		# Start by removing all old stuff here
		for item in self.content:
			item.deleteLater()
		self.content = []

		# Find all folders that look like the correct type of database
		folderList = []
		for folder in os.listdir(os.getcwd()):
			if os.path.isdir(folder) and re.match(archivedPrefix + self.folderPrefix, folder):
				folderList.append(folder)

		# Add each to scroll area
		for folder in folderList:
			name = folder[len(archivedPrefix + self.folderPrefix):]
			try:
				with open(os.path.join(folder, "info.txt"), 'r') as infoFile:
					description = infoFile.read()
					# truncate the file if someone writes a ludicrous description
					if len(description) > 500:
						description = description[0:500] + '...'

					hLayout = QHBoxLayout()
					self.scrollLayout.addLayout(hLayout)

					nameLbl = QLabel(name)
					hLayout.addWidget(nameLbl)

					recoverBtn = QPushButton("Recover")
					recoverBtn.clicked.connect(partial(self.on_recover_archived, folder))
					hLayout.addWidget(recoverBtn)

					recoverBtn.setMaximumWidth(80)
					recoverBtn.setMinimumWidth(80)

					descriptionLbl = QLabel(description)
					descriptionLbl.setWordWrap(True)
					self.scrollLayout.addWidget(descriptionLbl)

					self.content.extend([nameLbl, descriptionLbl, recoverBtn])

			except:
				print("Warning: could not read folder " + folder + ". Skipping")
				continue

	def on_recover_archived(self, foldername):
		global archivedPrefix
		os.rename(foldername, foldername[len(archivedPrefix):])
		self.populate_scroll_area()

	def close_window(self):
		self.onDeleteCallback()
		self.deleteLater()

class Cali_DB_constructor(QWidget):
	def __init__(self, onDeleteCallback, foldername=None):
		super(Cali_DB_constructor, self).__init__()
		self.prefix = "calibration_db_"
		self.origName = None if not foldername else foldername[len(self.prefix):]			# Also used for new/edit differentiation
		self.onDeleteCallback = onDeleteCallback

		self.setWindowTitle('{} calibration database:'.format("New" if not self.origName else "Edit"))

		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)

		# Stuff for database name
		self.nameLayout = QHBoxLayout()
		self.nameLayout.addWidget(QLabel("Name:"))
		self.mainLayout.addLayout(self.nameLayout)

		self.nameEdit = QLineEdit()
		self.nameLayout.addWidget(self.nameEdit)

		# stuff for database description
		self.infoLayout = QHBoxLayout()
		self.infoLayout.addWidget(QLabel("Short description:"))
		self.mainLayout.addLayout(self.infoLayout)

		self.infoEdit = QTextEdit()
		self.infoLayout.addWidget(self.infoEdit)

		# AIS folder location
		self.aisLayout = QHBoxLayout()
		self.aisLayout.addWidget(QLabel("AIS folder location:"))
		self.mainLayout.addLayout(self.aisLayout)

		self.aisEdit = QLineEdit()
		self.aisLayout.addWidget(self.aisEdit)

		self.aisBrowseBtn = QPushButton("Browse...")
		self.aisBrowseBtn.clicked.connect(partial(self.folder_browse_popup, self.aisEdit))
		self.aisBrowseBtn.setMaximumWidth(80)
		self.aisLayout.addWidget(self.aisBrowseBtn)

		# Reference points and related
		self.mainLayout.addWidget(QHLine())
		self.gridLayout = QGridLayout()
		self.mainLayout.addLayout(self.gridLayout)
		self.gridLayout.addWidget(QLabel("Latitude (degrees)"), 0, 1)
		self.gridLayout.addWidget(QLabel("Longitude (degrees)"), 0, 2)
		self.gridLayout.addWidget(QLabel("Elevation (meters)"), 0, 3)
		self.gridLayout.addWidget(QLabel("Camera:"), 1, 0)
		self.gridLayout.addWidget(QLabel("Reference point 1:"), 2, 0)
		self.gridLayout.addWidget(QLabel("Reference point 2:"), 3, 0)

		self.latEdits = []
		self.longEdits = []
		self.heightEdits = []
		for i in range(1, 4):
			latEdit = QLineEdit()
			latEdit.setValidator(QtGui.QDoubleValidator())
			self.gridLayout.addWidget(latEdit, i, 1)
			self.latEdits.append(latEdit)

			longEdit = QLineEdit()
			longEdit.setValidator(QtGui.QDoubleValidator())
			self.gridLayout.addWidget(longEdit, i, 2)
			self.longEdits.append(longEdit)

			heightEdit = QLineEdit()
			heightEdit.setValidator(QtGui.QDoubleValidator())
			self.gridLayout.addWidget(heightEdit, i, 3)
			self.heightEdits.append(heightEdit)

		# AIS limits
		self.mainLayout.addWidget(QHLine())
		self.mainLayout.addWidget(QLabel("Bounding box on camera field of view:"))
		self.boundingBoxLayout = QGridLayout()
		self.mainLayout.addLayout(self.boundingBoxLayout)
		self.boundingBoxLayout.addWidget(QLabel("Minimum"), 0, 1)
		self.boundingBoxLayout.addWidget(QLabel("Maximum"), 0, 2)
		self.boundingBoxLayout.addWidget(QLabel("Latitude:"), 1, 0)
		self.boundingBoxLayout.addWidget(QLabel("Longitude:"), 2, 0)

		self.latEditH = QLineEdit()
		self.latEditH.setValidator(QtGui.QDoubleValidator())
		self.boundingBoxLayout.addWidget(self.latEditH, 1, 2)
		self.latEditL = QLineEdit()
		self.latEditL.setValidator(QtGui.QDoubleValidator())
		self.boundingBoxLayout.addWidget(self.latEditL, 1, 1)

		self.longEditH = QLineEdit()
		self.longEditH.setValidator(QtGui.QDoubleValidator())
		self.boundingBoxLayout.addWidget(self.longEditH, 2, 2)
		self.longEditL = QLineEdit()
		self.longEditL.setValidator(QtGui.QDoubleValidator())
		self.boundingBoxLayout.addWidget(self.longEditL, 2, 1)

		# General controls at bottom
		self.mainLayout.addWidget(QHLine())
		self.buttonsLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.buttonsLayout)
		hSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.buttonsLayout.addSpacerItem(hSpacer)

		self.cancelBtn = QPushButton("Cancel")
		self.cancelBtn.clicked.connect(self.close_window)
		self.buttonsLayout.addWidget(self.cancelBtn)

		self.saveBtn = QPushButton("Save")
		self.saveBtn.clicked.connect(self.save_db)
		self.buttonsLayout.addWidget(self.saveBtn)

		if foldername and os.path.exists(foldername):
			self.load_db()

		self.show()

	def load_db(self):
		self.nameEdit.setText(self.origName)
		with open(os.path.join(self.prefix + self.origName, "info.txt"), 'r') as infile:
			self.infoEdit.setText(infile.read())

		metaDict = {
			'camlat': self.latEdits[0],
			'camlon': self.longEdits[0],
			'camheight': self.heightEdits[0],
			'ref1lat': self.latEdits[1],
			'ref1lon': self.longEdits[1],
			'ref1height': self.heightEdits[1],
			'ref2lat': self.latEdits[2],
			'ref2lon': self.longEdits[2],
			'ref2height': self.heightEdits[2],
			'latH': self.latEditH,
			'latL': self.latEditL,
			'lonH': self.longEditH,
			'lonL': self.longEditL,
			'aisFolder': self.aisEdit
		}
		with open(os.path.join(self.prefix + self.origName, "meta.txt"), 'r') as infile:
			for line in infile.readlines():
				splt = line.split(":")
				if len(splt) == 2:
					try:
						metaDict[splt[0]].setText(splt[1].strip())
					except:
						print("unidentified line in cali db edit load")
						print(line)

	def save_db(self):
		name = self.nameEdit.text()
		description = self.infoEdit.toPlainText()
		# TODO: add more validation here
		if len(name) == 0 or len(description) == 0:
			# TODO: add warning here
			return

		if not self.origName:
			os.mkdir(self.prefix + name)
		else:
			if not self.origName == name:
				os.rename(self.prefix + self.origName, self.prefix + name)

		with open(os.path.join(self.prefix + name, "info.txt"), 'w+') as infoFile:
			infoFile.write(description)

		with open(os.path.join(self.prefix + name, "meta.txt"), 'w+') as metaFile:
			metaFile.write("camlat:{}\n".format(self.latEdits[0].text()))
			metaFile.write("camlon:{}\n".format(self.longEdits[0].text()))
			metaFile.write("camheight:{}\n\n".format(self.heightEdits[0].text()))

			metaFile.write("ref1lat:{}\n".format(self.latEdits[1].text()))
			metaFile.write("ref1lon:{}\n".format(self.longEdits[1].text()))
			metaFile.write("ref1height:{}\n\n".format(self.heightEdits[1].text()))

			metaFile.write("ref2lat:{}\n".format(self.latEdits[2].text()))
			metaFile.write("ref2lon:{}\n".format(self.longEdits[2].text()))
			metaFile.write("ref2height:{}\n\n".format(self.heightEdits[2].text()))

			metaFile.write("latH:{}\n".format(self.latEditH.text()))
			metaFile.write("latL:{}\n".format(self.latEditL.text()))
			metaFile.write("lonH:{}\n".format(self.longEditH.text()))
			metaFile.write("lonL:{}\n\n".format(self.longEditL.text()))

			metaFile.write("aisFolder:{}".format(self.aisEdit.text()))

		self.close_window()

	def close_window(self):
		self.onDeleteCallback()
		self.deleteLater()

	# lineEdit will have its text set to wherever the user selects
	# Borrowed from SonicTrail (copywrite Gregory O'Hagan)
	def folder_browse_popup(self, lineEdit):
		folder = QFileDialog.getExistingDirectory(self, "Select Directory")
		if folder:
			lineEdit.setText(str(folder))


class Contacts_DB_constructor(QWidget):
	def __init__(self, onDeleteCallback, foldername=None):
		super(Contacts_DB_constructor, self).__init__()
		self.prefix = "contacts_db_"
		self.origName = None if not foldername else foldername[len(self.prefix):]			# Also used for new/edit differentiation
		self.onDeleteCallback = onDeleteCallback

		self.setWindowTitle('{} contacts database:'.format("New" if not self.origName else "Edit"))

		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)

		# Stuff for database name
		self.nameLayout = QHBoxLayout()
		self.nameLayout.addWidget(QLabel("Name:"))
		self.mainLayout.addLayout(self.nameLayout)

		self.nameEdit = QLineEdit()
		self.nameLayout.addWidget(self.nameEdit)

		# stuff for database description
		self.infoLayout = QHBoxLayout()
		self.infoLayout.addWidget(QLabel("Short description:"))
		self.mainLayout.addLayout(self.infoLayout)

		self.infoEdit = QTextEdit()
		self.infoLayout.addWidget(self.infoEdit)

		# General controls at bottom
		self.buttonsLayout = QHBoxLayout()
		self.mainLayout.addLayout(self.buttonsLayout)
		hSpacer = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum)
		self.buttonsLayout.addSpacerItem(hSpacer)

		self.cancelBtn = QPushButton("Cancel")
		self.cancelBtn.clicked.connect(self.close_window)
		self.buttonsLayout.addWidget(self.cancelBtn)

		self.saveBtn = QPushButton("Save")
		self.saveBtn.clicked.connect(self.save_db)
		self.buttonsLayout.addWidget(self.saveBtn)

		if self.origName:
			self.load_db()

		self.show()

	def load_db(self):
		self.nameEdit.setText(self.origName)
		with open(os.path.join(self.prefix + self.origName, "info.txt"), 'r') as infile:
			self.infoEdit.setText(infile.read())

	def save_db(self):
		name = self.nameEdit.text()
		description = self.infoEdit.toPlainText()
		if len(name) == 0 or len(description) == 0:
			# TODO: add warning here
			return

		if not self.origName:
			os.mkdir(self.prefix + name)
		else:
			if not self.origName == name:
				os.rename(self.prefix + self.origName, self.prefix + name)

		with open(os.path.join(self.prefix + name, "info.txt"), 'w+') as infoFile:
			infoFile.write(description)

		self.close_window()

	def close_window(self):
		self.onDeleteCallback()
		self.deleteLater()

# ---------------------------


# https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
class QHLine(QFrame):
	def __init__(self):
		super(QHLine, self).__init__()
		self.setFrameShape(QFrame.HLine)
		self.setFrameShadow(QFrame.Sunken)