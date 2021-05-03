import os
import re
import datetime
import common as cmn

# AIS = 0: non-ais; AIS = -1: non-contact; AIS > 0: ais code
# aisClass: "A", "B", "". Only referenced if ais > 0
# Other information can be saved as tags. Tags including '=' are reserved and not counted in tallies
class Contact:
	def __init__(self, time, x, y, ais=0, aisClass="A", tags=''):
		self.time = time
		self.x = x
		self.y = y
		self.ais = ais
		self.aisClass = aisClass
		self.tags = tags

	def get_distance(self):
		print(self.tags)
		for tag in self.tags.split(','):
			if re.search(r'^dist=(\d+.?\d*)$', tag):
				print(tag)
				return float(tag.split('=')[1])


class Contact_db:
	def __init__(self, folder):
		self.folder = folder
		self.date = [0, 0, 0]
		self.contacts = []

	# Input: time formatted as [year, month, day, hour, minute, second]
	# Return: list of Contacts for that time
	def get_contacts(self, time):
		if time[0] != self.date[0] or time[1] != self.date[1] or time[2] != self.date[2]:
			self.load_db(time[:])
		res = []
		for c in self.contacts:
			append = True
			for i in range(5, -1, -1):
				if not time[i] == c.time[i]:
					append = False
					break
			if append:
				res.append(c)
		return res

	# TODO: no checking for duplicates here!
	def add_contact(self, contact):
		if contact.time[0] != self.date[0] or contact.time[1] != self.date[1] or contact.time[2] != self.date[2]:
			self.load_db(contact.time[:])
		self.contacts.append(contact)

	# Replaces a contact if the time, x, and y match. Otherwise appends it.
	def update_contact(self, contact):
		for c in self.contacts:
			if c.x == contact.x and c.y == contact.y:
				match = True
				for i in range(5, -1, -1):
					if not contact.time[i] == c.time[i]:
						match = False
						break
				if match:
					c.ais = contact.ais
					c.aisClass = contact.aisClass
					c.tags = contact.tags
					return

	def remove_contact(self, contact):
		for c in self.contacts:
			if c.x == contact.x and c.y == contact.y:
				match = True
				for i in range(5, -1, -1):
					if not contact.time[i] == c.time[i]:
						match = False
						break
				if match:
					self.contacts.remove(c)
					return

	# TODO: Make this a running tally (more efficient)
	def count_nonais_contacts(self):
		count = 0
		for c in self.contacts:
			if c.ais == 0:
				count += 1
		return count

	def count_ais_contacts(self):
		count = 0
		for c in self.contacts:
			if c.ais > 1:
				count += 1
		return count

	def count_suspect_contacts(self):
		count = 0
		for c in self.contacts:
			if c.ais == 1:
				count += 1
		return count

	def count_misc_contacts(self):
		count = 0
		for c in self.contacts:
			if c.ais == -1:
				count += 1
		return count

	# Input: date as [year, month, day] in integers (extra terms in date is fine)
	# save_on_close should be true except for when generating reports
	def load_db(self, date, save_on_close=True, dump_on_open=True):
		if save_on_close:
			self.save_db()
		if dump_on_open:
			self.contacts = []
		self.date = date

		path = os.path.join(self.folder, str(date[0]), str(date[1]), str(date[2]), "contacts.csv")
		# print("Trying to read from: " + path)
		if os.path.exists(path):
			with open(path, 'r') as loadFile:
				if loadFile:
					for line in loadFile:
						try:
							split = line.split(',', 5)
							time = split[0].split(":", 6)
							time = [int(time[0]), int(time[1]), int(time[2]), int(time[3]), int(time[4]),int(time[5])]
							c = Contact(time, int(split[1]), int(split[2]), int(split[3]), split[4], split[5])
							self.contacts.append(c)
						except:
							pass

		print("Loaded " + str(len(self.contacts)) + " contacts")

	def save_db(self):
		# path = os.path.join(self.folder, str(self.date[0]), str(self.date[1]), str(self.date[2]))
		# if not os.path.exists(path):
		#     os.mkdir(path)

		# handle not being given a folder
		if self.folder is None or len(self.folder) < 1:
			self.folder = "contacts_db_mia"

		# Ensure folder structure exists
		path = self.folder
		if not os.path.exists(path):
			os.mkdir(path)
			# TODO: CREATE THE INFO FILE HERE***
		path = os.path.join(path, str(self.date[0]))
		if not os.path.exists(path):
			os.mkdir(path)
		path = os.path.join(path, str(self.date[1]))
		if not os.path.exists(path):
			os.mkdir(path)
		path = os.path.join(path, str(self.date[2]))
		if not os.path.exists(path):
			os.mkdir(path)

		with open(os.path.join(path, 'contacts.csv'), 'w+') as saveFile:
			for contact in self.contacts:
				saveFile.write(str(contact.time[0]) + ":" + str(contact.time[1]) + ":" + str(contact.time[2]) + ":"
						   + str(contact.time[3]) + ":" + str(contact.time[4]) + ":" + str(contact.time[5]) + ",")
				saveFile.write(str(contact.x) + ",")
				saveFile.write(str(contact.y) + ",")
				saveFile.write(str(contact.ais) + ",")
				saveFile.write(contact.aisClass + ",")
				saveFile.write(contact.tags + "\n")

	# Input: startDate, endDate of form (year, month, day) (inclusive)
	# - can have hours, etc... but these are ignored
	# Output: 'fileName' in program folder (unless full path is provided), with daily tallies
	def create_daily_report(self, startDate, endDate, csliDB=None, fileName='report.csv'):
		self.save_db()
		date = startDate[:3]
		repDB = Contact_db(self.folder)

		aisACountT = 0
		aisBCountT = 0
		aisSusCountT = 0
		nonAisCountT = 0
		nonVesselCountT = 0
		tags = []
		tagCountsT = []

		# List that will store the required information to print a each line
		linesRaw = []

		# Load one day at a time, until we iterate through all applicable days
		while date <= endDate:
			aisACount = 0
			aisBCount = 0
			aisSusCount = 0
			nonAisCount = 0
			nonVesselCount = 0
			tagCounts = [0] * len(tags)

			# Load two days. Dump any old loaded data, but don't dump day one when loading day 2
			# Note that contacts aren't necessarily ordered by time
			repDB.load_db(date, False)
			repDB.load_db(cmn.change_date_by_days(date, 1), False, False)

			startTime = [date[0], date[1], date[2], 8, 0, 0]
			endTime = cmn.change_date_by_days(startTime, 1)

			for c in repDB.contacts:
				# Count any contacts within the time frame. This gives pst (NOT pdt) instead of gmt
				if c.time >= startTime and c.time < endTime:
					if c.ais > 1:
						if c.aisClass == 'A':
							aisACount += 1
						else:
							aisBCount += 1
					elif c.ais == 1:
						aisSusCount += 1
					elif c.ais == 0:
						nonAisCount += 1
					else:
						nonVesselCount += 1
					# Add each tag individually
					for tag in c.tags.split(','):
						# Skip 'reserved' tags
						if re.search(r'=', tag):
							continue
						tag = tag.strip()
						# Skip 'reserved' tags
						if re.search(r'=', tag):
							continue
						tag = tag.strip()
						if c.ais > 1:
							if c.aisClass == 'A':
								tag += " ais-A"
							else:
								tag += " ais-B"
						elif c.ais == 1:
							tag += " suspect-ais"
						elif c.ais == 0:
							tag += " non-ais"
						else:
							tag += " marine-mammal"
						# If the tag already exists, increment the counter
						added = False
						for i, t in enumerate(tags):
							if t == tag:
								tagCounts[i] += 1
								added = True
								break
						# If the tag doesn't exist, add it to the master list
						if not added:
							tags.append(tag)
							tagCounts.append(1)
							tagCountsT.append(0)

			# Record data for spreadsheet. Note that we don't want to write yet since we don't have all unique tags
			linesRaw.append((aisACount, aisBCount, aisSusCount, nonAisCount, nonVesselCount, tagCounts, date[:]))
			# Keep a running tally of totals (end of spreadsheet)
			aisACountT += aisACount
			aisBCountT += aisBCount
			aisSusCountT += aisSusCount
			nonAisCountT += nonAisCount
			nonVesselCountT += nonVesselCount
			tagCountsT = [x + y for x, y in zip(tagCounts, tagCountsT)]

			# Increment the date counter
			date[2] += 1
			if date[2] > 31:
				date[2] = 1
				date[1] += 1
				if date[1] > 12:
					date[1] = 1
					date[0] += 1

		# Create spreadsheet
		with open(fileName, 'w+') as csv:
			# Write info bar across top
			csv.write("Date,Total Vessels,Total AIS,AIS A,AIS B,Suspect AIS,Total Non-AIS,Marine Mammals,,")
			for t in tags:
				csv.write(t + ",")
			csv.write("\n")

			# Record each line
			for raw in linesRaw:
				line = str(raw[6][2]) + " " + cmn.get_month_name(raw[6][1]) + " " + str(raw[6][0]) + ','
				line += str(raw[0] + raw[1] + raw[2] + raw[3]) + ','   # Total vessels
				line += str(raw[0] + raw[1]) + ',' + str(raw[0]) + ',' + str(raw[1]) + ','  # AIS counts
				line += str(raw[2]) + ',' + str(raw[3]) + ',' + str(raw[4]) + ',,'   # sus-ais, non-ais and non-vessel counts
				for c in raw[5]:            # all tag counts
					line += str(c) + ','
				csv.write(line + '\n')

			# Repeat info above summary
			csv.write("\n,Total Vessels,Total AIS,AIS A,AIS B,Suspect AIS,Total Non-AIS,Marine Mammals,,")
			for t in tags:
				csv.write(t + ",")
			csv.write("\n")

			# Record summary
			line = 'Totals:,'
			line += str(aisACountT + aisBCountT + nonAisCountT) + ','   # Total vessels
			line += str(aisACountT + aisBCountT) + ',' + str(aisACountT) + ',' + str(aisBCountT) + ','
			line += str(aisSusCountT) + ',' + str(nonAisCountT) + ',' + str(nonVesselCountT) + ',,'
			for c in tagCountsT:            # all tag counts
				line += str(c) + ','
			csv.write(line + '\n')

	def create_vessel_report(self, startDate, endDate, caliDB, fileName='report.csv'):
		self.save_db()
		date = startDate[:3]
		repDB = Contact_db(self.folder)

		lines = []

		# Load one day at a time
		while date <= endDate:
			linesDay = []
			repDB.load_db(date, False)
			for c in repDB.contacts:
				if c.time >= startDate and c.time <= endDate:
					geopoint = caliDB.get_geopoint_from_xy(c.x, c.y, 0,
							datetime.datetime(c.time[0], c.time[1], c.time[2], c.time[3], c.time[4], c.time[5]))
					mmsi = c.ais
					aisClass = c.aisClass

					repeat = False
					type = None
					activity = None
					tags = []
					for tag in c.tags.split(','):
						tag = tag.strip()
						if tag.find('=') > 0:
							split = tag.split('=')
							if split[0] == 'type':
								type = split[1]
							elif split[0] == 'repeat':
								repeat = split[1] == 'True'
							elif split[0] == 'activity':
								activity = split[1]
						else:
							if tag:
								tags.append(tag)
					tags = ', '.join(tags) if tags else None

					linesDay.append([c.time, geopoint, aisClass, mmsi, repeat, type, activity, tags, (c.x, c.y)])

			# Sort the day's contacts, then add them to the master list
			linesDay.sort(key=lambda x: x[0])
			lines.extend(linesDay)

			# Increment the date counter
			date[2] += 1
			if date[2] > 31:
				date[2] = 1
				date[1] += 1
				if date[1] > 12:
					date[1] = 1
					date[0] += 1

		with open(fileName, 'w+') as csv:
			csv.write("Id,Date,Time,Latitude,Longitude,AIS class,MMSI,Repeat?,Type,Activity,Notes,X,Y\n")
			for i, line in enumerate(lines):
				text = str(i) + ','
				text += str(line[0][0]) + '-' + str(line[0][1]) + '-' + str(line[0][2]) + ","
				text += str(line[0][3]) + '-' + str(line[0][4]) + '-' + str(line[0][5]) + ","
				text += str(line[1].lat) + ',' + str(line[1].lon) + ','
				if line[2]:
					text += line[2] + ',' + str(line[3]) + ','
				elif line[3] == 1:
					text += "suspect AIS,,"
				elif line[3] == 0:
					text += "Non-ais,,"
				else:
					text += "Marine Mammal,,"
				text += 'Repeat,' if line[4] else ','
				text += line[5] + ',' if line[5] else ','
				text += line[6] + ',' if line[6] else ','
				text += line[7] + ',' if line[7] else ','
				text += str(line[8][0]) + "," + str(line[8][1]) + '\n'
				csv.write(text)


	# Creates a minute-by-minute report of the vessels. Tallies by minute, and ignores tags
	# Input: startDate, endDate of form (year, month, day) (inclusive)
	# - can have hours, etc... but these are ignored
	# Output: 'fileName' in program folder (unless full path is provided), with minute-to-minute tallies
	def create_minute_report(self, startDate, endDate, caliDB, fileName='report.csv'):
		self.save_db()
		date = startDate[:3]
		repDB = Contact_db(self.folder)

		lines = []
		tags = []

		# Two distance bands. Can be edited here
		# TODO: expose editing these in the GUI
		dist1 = 1000
		dist2 = 3000

		# Load one day at a time, until we iterate through all applicable days
		while date <= endDate:
			startTime = [date[0], date[1], date[2], 8, 0, 0]
			dayEndTime = cmn.change_date_by_days(startTime, 1)
			endTime = cmn.change_time_by_seconds(startTime, 60)

			# Load two days. Dump any old loaded data, but don't dump day one when loading day 2
			# Note that contacts aren't necessarily ordered by time
			repDB.load_db(date, False)
			repDB.load_db(cmn.change_date_by_days(date, 1), False, False)

			# Look at each minute independently
			# Inefficient, but otherwise we need some type of way to sort contacts
			while endTime <= dayEndTime:
				# minute counts
				aisACountM = [0, 0, 0]
				aisBCountM = [0, 0, 0]
				suspectCountM = [0, 0, 0]
				nonAisCountM = [0, 0, 0]
				tagCounts = [0] * len(tags)
				for c in repDB.contacts:
					# Count any contacts within the time frame. This gives pst (NOT pdt) instead of gmt
					if c.time >= startTime and c.time < endTime:
						dist = caliDB.get_geopoint_from_xy(c.x, c.y, 0,
								datetime.datetime(c.time[0], c.time[1], c.time[2], c.time[3], c.time[4], c.time[5])).dist
						print(dist)
						if c.ais > 1:
							if c.aisClass == 'A':
								if dist > dist2:
									aisACountM[2] += 1
								elif dist > dist1:
									aisACountM[1] += 1
								else:
									aisACountM[0] += 1
							else:
								if dist > dist2:
									aisBCountM[2] += 1
								elif dist > dist1:
									aisBCountM[1] += 1
								else:
									aisBCountM[0] += 1
						elif  c.ais == 1:
							if dist > dist2:
								suspectCountM[2] += 1
							elif dist > dist1:
								suspectCountM[1] += 1
							else:
								suspectCountM[0] += 1
						elif c.ais == 0:
							if dist > dist2:
								nonAisCountM[2] += 1
							elif dist > dist1:
								nonAisCountM[1] += 1
							else:
								nonAisCountM[0] += 1
						# Skip non-vessel contacts
						else:
							continue

						# Add each tag individually
						for tag in c.tags.split(','):
							# Skip 'reserved' tags
							if re.search(r'=', tag):
								continue
							tag = tag.strip()

							# Put distance and AIS info on tag
							if dist > dist2:
								tag += " far"
							elif dist > dist1:
								tag += " mid"
							else:
								tag += " near"

							if c.ais > 1:
								if c.aisClass == 'A':
									tag += " ais-A"
								else:
									tag += " ais-B"
							elif c.ais == 1:
								tag += " suspect-ais"
							else:
								tag += " non-ais"

							# If the tag already exists, increment the counter
							added = False
							for i, t in enumerate(tags):
								if t == tag:
									tagCounts[i] += 1
									added = True
									break
							# If the tag doesn't exist, add it to the master list
							if not added:
								tags.append(tag)
								tagCounts.append(1)

				# if non-zero, prepare the line to print
				if aisACountM > [0, 0, 0] or aisBCountM > [0, 0, 0]\
						or nonAisCountM > [0, 0, 0] or suspectCountM > [0, 0, 0]:
					# Time as a string
					ln = str(startTime[0]) + '-' + str(startTime[1]) + '-' + str(startTime[2]) + ','
					ln += str(startTime[3]) + ':' + str(startTime[4]) + ':' + str(startTime[5]) + ','
					# Contact counts
					ln += str(aisACountM[0]) + ',' + str(aisACountM[1]) + ',' + str(aisACountM[2]) + ','
					ln += str(aisBCountM[0]) + ',' + str(aisBCountM[1]) + ',' + str(aisBCountM[2]) + ','
					ln += str(suspectCountM[0]) + ',' + str(suspectCountM[1]) + ',' + str(suspectCountM[2]) + ','
					ln += str(nonAisCountM[0]) + ',' + str(nonAisCountM[1]) + ',' + str(nonAisCountM[2]) + ','
					# More detailed tags
					for c in tagCounts:
						ln += ',' + str(c)
					ln += "\n"
					lines.append(ln)

				# increment times
				startTime = cmn.change_time_by_seconds(startTime, 60)
				endTime = cmn.change_time_by_seconds(endTime, 60)

			# Increment the date counter
			date[2] += 1
			if date[2] > 31:
				date[2] = 1
				date[1] += 1
				if date[1] > 12:
					date[1] = 1
					date[0] += 1


		with open(fileName, 'w+') as csv:
			csv.write("Date,Time,AIS A near,AIS A mid,AIS A far,AIS B near,AIS B mid,AIS B far,"
					  + "suspect AIS near,suspect AIS mid, suspect AIS far,non-AIS near,non-AIS mid,non-AIS far" + ',')
			for tag in tags:
				csv.write(',' + tag)
			csv.write('\n')
			for line in lines:
				csv.write(line)
