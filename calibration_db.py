import os
import datetime
from georectifier import Georectifier
from ais_db import AIS_db


class Calibration_db:
	def __init__(self, folder, imHeight, imWidth):
		self.folder = folder
		self.dbLoaded = False
		self.cameraPos = [0, 0, 0]
		self.ref1Pos = [0, 0, 0]
		self.ref2Pos = [0, 0, 0]
		self.latBounds = [0, 0]
		self.lonBounds = [0, 0]
		self.locatorPoints = []

		self.geo = Georectifier(imWidth, imHeight)
		self.imHeight = imHeight
		self.imWidth = imWidth
		self.lastRef1Coords = [0, 0]
		self.lastRef2Coords = [0, 0]

		self.date = datetime.datetime(1, 1, 1)
		self.newData = False
		self.aisDB = None
		self.aisFolder = None

		self.load_metadata()

	# Reads the meta information from a database. This is stored in a single text file,
	# and doesn't change for a given camera.
	def load_metadata(self):
		self.dbLoaded = True
		with open(os.path.join(self.folder, 'meta.txt'), 'r') as meta:
			# Parse and save each line. Ignore extras (comments)
			for line in meta.readlines():
				line = line.strip()
				if line.startswith("camlat:"):
					self.cameraPos[0] = float(line[7:])
				elif line.startswith("camlon:"):
					self.cameraPos[1] = float(line[7:])
				elif line.startswith("camheight:"):
					self.cameraPos[2] = float(line[10:])

				elif line.startswith("ref1lat:"):
					self.ref1Pos[0] = float(line[8:])
				elif line.startswith("ref1lon:"):
					self.ref1Pos[1] = float(line[8:])
				elif line.startswith("ref1height:"):
					self.ref1Pos[2] = float(line[11:])

				elif line.startswith("ref2lat:"):
					self.ref2Pos[0] = float(line[8:])
				elif line.startswith("ref2lon:"):
					self.ref2Pos[1] = float(line[8:])
				elif line.startswith("ref2height:"):
					self.ref2Pos[2] = float(line[11:])

				elif line.startswith("latH:"):
					self.latBounds[1] = float(line[5:])
				elif line.startswith("latL:"):
					self.latBounds[0] = float(line[5:])
				elif line.startswith("lonH:"):
					self.lonBounds[1] = float(line[5:])
				elif line.startswith("lonL:"):
					self.lonBounds[0] = float(line[5:])
				elif line.startswith("aisFolder:"):
					self.aisFolder = line.split(':')[1]

		# ensure non-zero latitudes and longitudes. If some of these are missing, we can't work
		# Heights may still be zero, and are defaulted to this if not saved.
		if self.cameraPos[0] and self.cameraPos[1] and self.ref1Pos[0] and self.ref1Pos[1] \
				and self.ref2Pos[0] and self.ref2Pos[1]:
			self.dbLoaded = True
		else:
			self.dbLoaded = False

		# Load AIS data
		self.aisDB = AIS_db(self.aisFolder)
		self.aisDB.set_time_offsets(30)
		self.aisDB.set_location(self.latBounds[1], self.latBounds[0], self.lonBounds[1], self.lonBounds[0])
		print(self.latBounds[1], self.latBounds[0], self.lonBounds[1], self.lonBounds[0])

	# returns True if all of the needed metadata was loaded, or false otherwise
	def is_loaded(self):
		return self.dbLoaded

	# loads in reference data for the current, previous, and next day
	def load_current_date(self):
		# If data for the day exists, load it and adjacent days:
		todayFilename = os.path.join(self.folder, str(self.date.year), str(self.date.month), str(self.date.day) + '.csv')
		if os.path.exists(todayFilename):
			self.newData = False
			# load previous day if possible
			prev = self.date - datetime.timedelta(1)
			prevFilename = os.path.join(self.folder, str(prev.year), str(prev.month), str(prev.day) + '.csv')
			if os.path.exists(prevFilename):
				self.load_file(prevFilename, prev)

			# load current day
			self.load_file(todayFilename, self.date)

			# load next day if possible
			nxt = self.date + datetime.timedelta(1)
			nextFilename = os.path.join(self.folder, str(nxt.year), str(nxt.month), str(nxt.day) + '.csv')
			if os.path.exists(nextFilename):
				self.load_file(nextFilename, nxt)

		# If no data from current day, look for (approximately) the closest single point
		# and use that. Alternate trying forwards and backwards
		else:
			future = self.date + datetime.timedelta(days=1)
			past = self.date - datetime.timedelta(days=1)
			while True:
				# try next day
				futureName = os.path.join(self.folder, str(future.year), str(future.month), str(future.day) + '.csv')
				# check if file exists
				if os.path.exists(futureName):
					# load file
					self.load_file(futureName, future)
					# ensure it wasn't blank. Discard extra points for speed
					if len(self.locatorPoints) > 0:
						self.locatorPoints = self.locatorPoints[0:1]
						break
				# try previous day.
				pastName = os.path.join(self.folder, str(past.year), str(past.month), str(past.day) + '.csv')
				if os.path.exists(pastName):
					self.load_file(pastName, past)
					# ensure we loaded some data. Discard extra points for speed
					if len(self.locatorPoints) > 0:
						self.locatorPoints = self.locatorPoints[-1:]
						break
				future += datetime.timedelta(days=1)
				past -= datetime.timedelta(days=1)

	# Read a day of data
	def load_file(self, filename, time):
		year = time.year
		month = time.month
		day = time.day
		with open(filename, 'r') as inFile:
			for line in inFile.readlines():
				nums = line.split(',')
				if len(nums) == 5:
					# format: (datetime, x1, y1, x2, y2) - time is in seconds of the day
					# since we control write order and read order, we don't have to sort
					self.locatorPoints.append((datetime.datetime(year, month, day, int(nums[0]) // 3600,
																 (int(nums[0]) // 60) % 60, int(nums[0]) % 60),
												int(nums[1]), int(nums[2]),
												int(nums[3]), int(nums[4])))

	def save_db(self):
		# We don't need to save if we didn't do anything
		if not self.newData or len(self.locatorPoints) == 0:
			return

		# handle not being given a folder
		if self.folder is None or len(self.folder) < 1:
			self.folder = "calibration_db_mia"

		# we only need to save today's points - we'll only add them here,
		# and save/reload the database whenever we add or access a different day
		todayFilename = os.path.join(self.folder, str(self.date.year), str(self.date.month), str(self.date.day) + '.csv')
		if not os.path.exists(os.path.join(self.folder, str(self.date.year), str(self.date.month))):
			os.makedirs(os.path.join(self.folder, str(self.date.year), str(self.date.month)))

		with open(todayFilename, 'w+') as saveFile:
			for locPoint in self.locatorPoints:
				# just day is a strong enough condition as we'll only ever have 3 days loaded at once
				# skip points that aren't today, because we'll only insert points from today
				if locPoint[0].day == self.date.day:
					secTimeOfDay = locPoint[0].second + locPoint[0].minute * 60 + locPoint[0].hour * 3600
					saveFile.write(str(secTimeOfDay) + ',' + str(locPoint[1]) + ',' + str(locPoint[2]) +
								   ',' + str(locPoint[3]) + ',' + str(locPoint[4]) + '\n')

		self.newData = False

	def get_xy(self, lat, lon, time):
		self.update_geo(time)
		return self.geo.get_xy(lat, lon)

	def get_geopoint_from_xy(self, x, y, height, time):
		self.update_geo(time)
		return self.geo.get_geopoint_from_xy(x, y, height)

	def get_dist_from_coords(self, lat, lon):
		return self.geo.get_dist_from_coords(lat, lon)

	# saves and reloads the database IF NEEDED to center on the target date
	# Accepts either a Date or a DateTime object
	def switch_day(self, date):
		if not (self.date.year == date.year and self.date.month == date.month and self.date.day == date.day):
			self.save_db()
			self.date = date
			self.load_current_date()

	# Builds the best geo possible using linear interpolation
	def update_geo(self, time):
		# update database time if needed
		self.switch_day(time)

		# If target is out of list range, just use closest point
		newRef1Coords, newRef2Coords = [0, 0], [0, 0]
		if time <= self.locatorPoints[0][0]:
			newRef1Coords, newRef2Coords = self.locatorPoints[0][1:3], self.locatorPoints[0][3:5]
			# print("less than case")
		elif time >= self.locatorPoints[-1][0]:
			newRef1Coords, newRef2Coords = self.locatorPoints[-1][1:3], self.locatorPoints[-1][3:5]
			# print("more than case")
		# interpolate new refpoint positions
		else:
			for i in range(len(self.locatorPoints) - 1):
				if self.locatorPoints[i][0] <= time and self.locatorPoints[i+1][0] > time:
					# print("interpolation case")
					distanceFactor = float((time - self.locatorPoints[i][0]).total_seconds())
					distanceFactor /= (self.locatorPoints[i+1][0] - self.locatorPoints[i][0]).total_seconds()
					newRef1Coords[0] = self.locatorPoints[i][1] + \
						(self.locatorPoints[i+1][1] - self.locatorPoints[i][1]) * distanceFactor
					newRef1Coords[1] = self.locatorPoints[i][2] + \
										(self.locatorPoints[i + 1][2] - self.locatorPoints[i][2]) * distanceFactor
					newRef2Coords[0] = self.locatorPoints[i][3] + \
										(self.locatorPoints[i + 1][3] - self.locatorPoints[i][3]) * distanceFactor
					newRef2Coords[1] = self.locatorPoints[i][4] + \
										(self.locatorPoints[i + 1][4] - self.locatorPoints[i][4]) * distanceFactor
		# create new geo if needed
		if (not newRef1Coords == self.lastRef1Coords) or (not newRef2Coords == self.lastRef2Coords):
			self.geo = Georectifier(self.imWidth, self.imHeight)
			self.geo.set_camera_pos(*self.cameraPos)
			# print("ref1Stuff", self.ref1Pos, newRef1Coords)
			# print("ref2Stuff", self.ref2Pos, newRef2Coords)
			self.geo.set_ref_point(self.ref1Pos[0], self.ref1Pos[1], self.ref1Pos[2], newRef1Coords[0], newRef1Coords[1])
			self.geo.set_ref_point(self.ref2Pos[0], self.ref2Pos[1], self.ref2Pos[2], newRef2Coords[0], newRef2Coords[1])
			self.lastRef1Coords = newRef1Coords
			self.lastRef2Coords = newRef2Coords
			self.geo.init()


	# Returns true if it has a calibration point within 'hoursOK' hours
	# time: datetime.datetime object
	# hoursOK: int (or float)
	def is_calibrated(self, time, hoursOK=2):
		# load current day first if needed
		self.switch_day(time)

		distance = datetime.timedelta(0, seconds=hoursOK*3600)
		for locatorPoint in self.locatorPoints:
			if abs(locatorPoint[0] - time) < distance:
				return True
			elif locatorPoint[0] > time:
				return False
		return False

	# time: datetime.datetime object
	def add_calibration_set(self, x1, y1, x2, y2, time):
		# load current day first if needed
		self.switch_day(time)

		self.newData = True
		for i, p in enumerate(self.locatorPoints):
			# insert new point set
			if p[0] > time:
				self.locatorPoints.insert(i, (time, x1, y1, x2, y2))
				return
			# replace if there is an overlap
			elif p[0] == time:
				self.locatorPoints[i] = (time, x1, y1, x2, y2)
				return

		self.locatorPoints.append((time, x1, y1, x2, y2))

	# returns the set of calibration points corresponding to a certain time.
	# Only shows actual points - does NOT extrapolate. TODO: change this?
	# return ((x1, y1), (x2, y2)) or NONE if it doesn't exist
	def get_calibration_set(self, time):
		for locPoint in self.locatorPoints:
			if locPoint[0] == time:
				return ((locPoint[1], locPoint[2]), (locPoint[3], locPoint[4]))
		return None
