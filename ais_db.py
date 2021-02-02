import re
import os
import common

class Track:

	def __init__(self, mmsi, isA):
		self.mmsi = mmsi
		self.isA = isA

		self.timeOffset = 0
		self.points = []
		# Tuples of start and end indexes (inclusive both sides)
		# Technically this is storing redundant information, but it makes traversals easier
		self.endIndexes = []

	def add_point(self, sTime, lat, lon):
		self.points.append((sTime, lat, lon))

	def set_time_offsets(self, seconds):
		self.timeOffset = seconds

	def is_active(self, sTime):
		for ind in self.endIndexes:
			if self.points[ind[0]][0] < sTime + self.timeOffset and self.points[ind[1]][0] > sTime - self.timeOffset:
				return True
		return False

	def get_points(self, sTime):
		retPoints = []
		currPos = self.get_pos(sTime)
		retPoints.append((sTime, currPos[0], currPos[1]))

		# Get the set of points that is closest to the time provided.
		# This separates tracks if a single ship crosses through multiple times
		passNum = 0
		if sTime > self.points[self.endIndexes[-1][0]][0]:
			passNum = len(self.endIndexes) - 1
		elif sTime > self.points[self.endIndexes[0][1]][0]:
			for i in range(len(self.endIndexes) - 1):
				midTime = (self.points[self.endIndexes[i][1]][0] + self.points[self.endIndexes[i + 1][0]][0]) / 2
				if sTime > midTime:
					passNum += 1
				else:
					break
		for i in range(self.endIndexes[passNum][0], self.endIndexes[passNum][1] + 1):
			retPoints.append(self.points[i])
		return retPoints

	# idea: integrate into get_points above?
	def get_pos(self, sTime):
		if sTime >= self.points[-1][0]:
			return (self.points[-1][1], self.points[-1][2])
		if sTime <= self.points[0][0]:
			return (self.points[0][1], self.points[0][2])

		prevPoint = self.points[0]
		currPoint = self.points[0]
		for point in self.points:
			if sTime < point[0]:
				# Border case: shouldn't run on normal data, but prevents errors:
				if currPoint[0] == prevPoint[0]:
					return currPoint[1], currPoint[2]

				timeRatio = float(sTime - prevPoint[0]) / (currPoint[0] - prevPoint[0])
				lat = prevPoint[1] + (currPoint[1] - prevPoint[1]) * timeRatio
				lon = prevPoint[2] + (currPoint[2] - prevPoint[2]) * timeRatio
				return lat, lon

			prevPoint = currPoint
			currPoint = point
		print("ERROR: unexpected branch reached in ais_db get_pos")

	# Sets start and end active times, deletes any unneeded points, and separates paths with
	# multiple passes
	def compress(self, latH, latL, lonH, lonL):
		# Ensure input points are in sorted order for later logic
		self.points.sort()

		shortPoints = []
		# state tracks what we've just done previously. This saves having to check previous point
		state = 0
		for p in self.points:
			if state == 0:
				# If point is inside the box bounded by the parameters
				if p[1] > latL and p[1] < latH and p[2] > lonL and p[2] < lonH:
					pass
				else:
					pass

		ps = self.points
		i = 1
		prevPointIn = False
		currStart = None
		# If first point is inside bounds, keep it
		if ps[0][1] > latL and ps[0][1] < latH and ps[0][2] > lonL and ps[0][2] < lonH:
			shortPoints.append(ps[0])
			prevPointIn = True
			currStart = 0

		# TODO: path starts, that corner case of in out in
		# Look at remaining points
		while i < len(self.points):
			# point i is inside area
			if ps[i][1] > latL and ps[i][1] < latH and ps[i][2] > lonL and ps[i][2] < lonH:
				if not prevPointIn:
					currStart = len(shortPoints)
					shortPoints.append(ps[i - 1])
				shortPoints.append(ps[i])
				prevPointIn = True
			# point i is outside area
			else:
				if prevPointIn:
					self.endIndexes.append((currStart, len(shortPoints)))
					currStart = None
					shortPoints.append(ps[i])
				prevPointIn = False
			i += 1
		if currStart is not None:
			self.endIndexes.append((currStart, len(shortPoints) - 1))
		self.points = shortPoints

		if self.mmsi == 316023833:
			for point in shortPoints:
				print(common.datetime_from_sec_time(point[0]))


class AIS_db:
	tracks = []
	latH = 90
	latL = -90
	lonH = 180
	lonL = -180
	timeOffset = 30
	currDate = [0, 0, 0]

	def __init__(self, folder="Processed_ais"):
		self.folder = folder

	# Input: time: (year, month, day, hour, minute, second)
	#   window: amount of time (seconds) to get a line for
	# Output: list of all mmsis (ints) active at the given time
	def get_mmsis(self, time):
		if self.currDate[0] != time[0] or self.currDate[1] != time[1] or self.currDate[2] != time[2]:
			self.load_db(time)
		sTime = ((((time[0] * 12 + time[1]) * 31 + time[2]) * 24 + time[3]) * 60 + time[4]) * 60 + time[5]
		mmsis = []
		for track in self.tracks:
			if track.is_active(sTime):
				mmsis.append(track.mmsi)
		return mmsis

	# Input: date: (year, month, day, hour, minute, second); mmsi: int
	# Output: list of tuples (lat, lon) First point is the extrapolated position at the
	# input time, followed by a list of the path
	# Returns an empty list if the mmsi doesn't exist
	def get_points(self, mmsi, time):
		sTime = ((((time[0] * 12 + time[1]) * 31 + time[2]) * 24 + time[3]) * 60 + time[4]) * 60 + time[5]
		for track in self.tracks:
			if track.mmsi == mmsi:
				return track.get_points(sTime)
		return []

	def is_A(self, mmsi):
		for track in self.tracks:
			if track.mmsi == mmsi:
				return track.isA
		return False

	def load_db(self, time):
		filePath = os.path.join(self.folder, str(time[0]), str(time[1]), str(time[2]), "condensed_ais.txt")
		print("Searching for: " + filePath)
		if not os.path.exists(filePath):
			print("can't find file")
			return
		if self.currDate[0] < time[0] or self.currDate[1] < time[1] or self.currDate[2] < time[2]:
			self.tracks = []
		self.currDate = time
		with open(filePath, 'r') as inFile:
			for line in inFile:
				if line.startswith("#"):
					continue
				split = line.split(",", 5)
				if len(split) < 5:
					continue
				secTime = common.sec_time(common.file_time(split[0]))
				mmsi = int(split[1])
				isA = split[2] == "A"   # Boolean, since it can (should) only be 'A' or 'B'
				lat = float(split[3])
				lon = float(split[4])
				# If the mmsi is already being tracked, add the new point
				added = False
				for track in self.tracks:
					if track.mmsi == mmsi:
						track.add_point(secTime, lat, lon)
						added = True
						break
				# If not, create a new track for it
				if not added:
					track = Track(mmsi, isA)
					track.set_time_offsets(self.timeOffset)
					track.add_point(secTime, lat, lon)
					self.tracks.append(track)
		print("AIS initial load - found " + str(len(self.tracks)) + " initial tracks")

		# Compress points. This saves memory and speeds access
		smallTracks = []
		for track in self.tracks:
			track.compress(self.latH, self.latL, self.lonH, self.lonL)
			if len(track.points) > 1:
				smallTracks.append(track)
		self.tracks = smallTracks

		print("Loaded " + str(len(self.tracks)) + " Tracks")
		# for track in self.tracks:
		# 	print(track.mmsi, len(track.points))

	# Must be called before read_new_db call
	def set_location(self, latHigh, latLow, lonHigh, lonLow):
		self.latH = latHigh
		self.latL = latLow
		self.lonH = lonHigh
		self.lonL = lonLow

	def set_time_offsets(self, seconds):
		self.timeOffset = seconds
		for track in self.tracks:
			track.set_time_offsets(seconds)


def test_ais_db():
	testDB = AIS_db()
	testDB.set_location(1, -1, 1, -1)
	testDB.set_time_offsets(3)
	testDB.load_db("C:/Workspace/test_ais_data.txt")
	print(len(testDB.tracks[0].points))
	print(testDB.tracks[0].endIndexes)
	print(len(testDB.tracks[1].points))
	print(testDB.tracks[1].endIndexes)
	print("Time Active mmsis check: should be 4, both, neither, 4, neither")
	print(testDB.get_mmsis([2017, 6, 1, 10, 1, 4]))
	print(testDB.get_mmsis([2017, 6, 1, 10, 1, 9]))
	print(testDB.get_mmsis([2017, 6, 1, 10, 1, 26]))
	print(testDB.get_mmsis([2017, 6, 1, 10, 1, 37]))
	print(testDB.get_mmsis([2017, 6, 1, 10, 1, 59]))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 1, 0])))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 1, 15])))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 1, 23])))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 1, 30])))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 1, 40])))
	print(len(testDB.get_points(111222334, [2017, 6, 1, 10, 2, 59])))


if __name__ == "__main__":
	test_ais_db()