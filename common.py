import re
import datetime as dt

# Returns the corrected time of the file
# TODO: actually correct the time!
def file_time(imName):
	match = re.search(r'(\d\d\d\d).?(\d\d).?(\d\d).?(\d\d).?(\d\d).?(\d\d).*', imName)
	if not match:
		return [0, 0, 0, 0, 0, 0]
	m = match.groups()
	time = [int(m[0]), int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5])]
	if time < [2017, 5, 22, 0, 0, 0]:
		if time < [2017, 6, 1, 0, 0, 0]:
			pass

	# print("calculating file time")
	return time


# Input: time: (year, month, day, hour, minute, second)
# Output: int: time in seconds
# Note that it assumes 31 days in every month, so will skip a good chunk of time on
# half of the month transitions.
def sec_time(time):
	return ((((time[0] * 12 + time[1]) * 31 + time[2]) * 24 + time[3]) * 60 + time[4]) * 60 + time[5]

def datetime_from_sec_time(stime):
	year = int(stime / 12 / 31 / 24 / 60 / 60)
	month = int(stime / 31 / 24 / 60 / 60) % 12
	day = int(stime / 24 / 60 / 60) % 31
	hour = int(stime / 60 / 60) % 24
	minute = int(stime / 60) % 60
	second = int(stime) % 60
	# print(stime, year, month, day, hour, minute, second)
	return dt.datetime(year, month, day, hour, minute, second)

# Input: any integer (intended: 1 <= int <= 12)
# Output: string with month name, or "" if outside of expected value
def get_month_name(monthNum):
	if monthNum == 1:
		return 'January'
	if monthNum == 2:
		return 'February'
	if monthNum == 3:
		return 'March'
	if monthNum == 4:
		return 'April'
	if monthNum == 5:
		return 'May'
	if monthNum == 6:
		return 'June'
	if monthNum == 7:
		return 'July'
	if monthNum == 8:
		return 'August'
	if monthNum == 9:
		return 'September'
	if monthNum == 10:
		return 'October'
	if monthNum == 11:
		return 'November'
	if monthNum == 12:
		return 'December'
	return ''


# input: date of form [year, month, day], int days (positive)
# output: date changed by the number of days
# Notes: accounts for month sizes and leap years
# - also keeps any extra values after days unchanged
def change_date_by_days(date, days):
	monthDays = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
	if date[0] % 4 == 0 and not (date[0] % 100 == 0 and not date[0] % 400 == 0):
		monthDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
	date = date[:]
	date[2] += days
	while date[2] > monthDays[date[1]]:
		date[2] -= monthDays[date[1]]
		date[1] += 1
		if date[1] > 12:
			date[0] += 1
			date[1] = 1
			# Reset monthDays, since we might enter (or leave) a leap year
			monthDays = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
			if date[0] % 4 == 0 and not (date[0] % 100 == 0 and not date[0] % 400 == 0):
				monthDays = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

	return date


# Input: time in form of [year, month, day, hour, minute, second], seconds as a positive int
# Output: copy of time, incremented by input number of seconds
# Note: accounts for month sizes and leap years as appropriate
def change_time_by_seconds(time, seconds):
	time = time[:]      # Copy first
	time[5] += seconds
	if time[5] >= 60:
		time[4] += time[5] // 60
		time[5] = time[5] % 60

		if time[4] >= 60:
			time[3] += time[4] // 60
			time[4] = time[4] % 60

			if time[3] >= 24:
				time = change_date_by_days(time, time[3] // 24)
				time[3] = time[3] % 24
	return time
