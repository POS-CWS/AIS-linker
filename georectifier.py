from math import *

class Geopoint:
	def __init__(self, lat=0, lon=0, height=0, x=0, y=0):
		self.lat = lat
		self.lon = lon
		self.height = height
		self.x = x
		self.y = y

		self.dist = 0
		self.AoDInv = 0
		self.bearing = 0


class Georectifier:
	R = 6371000
	def __init__(self, imageWidth, imageHeight, debug=False):
		self.imRows = imageWidth
		self.imCols = imageHeight
		self.debug = debug
		self.initialized = False

		self.cameraPos = ()
		self.refPoints = []

	def set_camera_pos(self, lat, lon, height):
		if lat < -90 or lat > 90 or lon < -180 or lon > 180:
			return False
		self.cameraPos = Geopoint(lat, lon, height, 0, 0)
		return True

	def set_ref_point(self, lat, lon, height, x, y):
		self.refPoints.append(Geopoint(lat, lon, height, x, y))

	def init(self):
		if len(self.refPoints) < 2:
			return False

		pC = self.cameraPos
		p1 = self.refPoints[0]
		p2 = self.refPoints[1]

		# Convert information to radians
		psiC = pC.lat * pi / 180
		psi1 = p1.lat * pi / 180
		psi2 = p2.lat * pi / 180
		lambdaC = pC.lon * pi / 180
		lambda1 = p1.lon * pi / 180
		lambda2 = p2.lon * pi / 180

		# Calculate distance, bearing, and vertical ange to reference point 1
		a1 = pow(sin((psi1 - psiC) / 2), 2) + cos(psiC) * cos(psi1) * pow(sin((lambda1 - lambdaC) / 2), 2)
		c1 = 2 * atan2(pow(a1, 0.5), pow(1 - a1, 0.5))
		p1.dist = self.R * c1

		theta1 = atan2(sin(lambda1 - lambdaC) * cos(psi1), cos(psiC) * sin(psi1) - sin(psiC) * cos(psi1) * cos(lambda1 - lambdaC))
		p1.bearing = theta1 * 180 / pi

		hC = pC.height
		h1 = p1.height
		dDirect1 = pow(pow(self.R + hC, 2) + pow(self.R + h1, 2) - 2 * (self.R + hC) * (self.R + h1) * cos(c1), 0.5)
		p1.AoDInv = asin((self.R + h1) * sin(c1) / dDirect1)

		# Calculate distance, bearing, and vertical angle to reference point 2
		a2 = pow(sin((psi2 - psiC) / 2), 2) + cos(psiC) * cos(psi2) * pow(sin((lambda2 - lambdaC) / 2), 2)
		c2 = 2 * atan2(pow(a2, 0.5), pow(1 - a2, 0.5))
		p2.dist = self.R * c2

		theta2 = atan2(sin(lambda2 - lambdaC) * cos(psi2), cos(psiC) * sin(psi2) - sin(psiC) * cos(psi2) * cos(lambda2 - lambdaC))
		p2.bearing = theta2 * 180 / pi

		hC = pC.height
		h2 = p2.height
		dDirect2 = pow(pow(self.R + hC, 2) + pow(self.R + h2, 2) - 2 * (self.R + hC) * (self.R + h2) * cos(c2), 0.5)
		p2.AoDInv = asin((self.R + h2) * sin(c2) / dDirect2)

		beta = atan2(p1.y - p2.y, p2.x - p1.x)
		imRotationRad = atan2(p2.AoDInv - p1.AoDInv, theta2 - theta1)
		imRotationRad -= beta
		self.imRotRad = imRotationRad
		if self.debug:
			print("Debug: imRotationRad = " + str(imRotationRad))

		#TODO: fix signs. Shouldn't need to have the absolute value at the end
		angleChangePerPixel = abs(p2.AoDInv - p1.AoDInv)
		angleChangePerPixel /= pow(pow(p2.x - p1.x, 2) + pow(p1.y - p2.y, 2), 0.5)
		angleChangePerPixel /= sin(imRotationRad + beta)
		angleChangePerPixel = abs(angleChangePerPixel * 180 / pi)
		self.anglePerPixel = angleChangePerPixel
		if self.debug:
			print("Debug: angle change per pixel (degrees): " + str(angleChangePerPixel))
			print("Debug: angle change across entire image (horizontal) " + str(angleChangePerPixel * self.imCols))
			print("Debug: angle of left side of image: " + str(p1.bearing - p1.x * angleChangePerPixel))

		# TODO: Is this step needed?
		self.refPoints[0] = p1
		self.refPoints[1] = p2

		self.initialized = True
		return True

	# Return: (x, y)
	def get_xy(self, lat, lon, height=0):
		if not self.initialized:
			return 0, 0

		psiC = self.cameraPos.lat * pi / 180
		psi0 = lat * pi / 180
		lambdaC = self.cameraPos.lon * pi / 180
		lambda0 = lon * pi / 180

		a = pow(sin((psi0 - psiC) / 2), 2) + cos(psiC) * cos(psi0) * pow(sin((lambda0 - lambdaC) / 2), 2)
		c = 2 * atan2(pow(a, 0.5), pow(1 - a, 0.5))
		distance = self.R * c

		theta1 = atan2(sin(lambda0 - lambdaC) * cos(psi0), cos(psiC) * sin(psi0) - sin(psiC) * cos(psi0) * cos(lambda0 - lambdaC))
		bearing = theta1 * 180 / pi
		if bearing - self.refPoints[0].bearing > 180:
			bearing -= 360
		elif bearing - self.refPoints[0].bearing < -180:
			bearing += 360

		hC = self.cameraPos.height
		h1 = height
		dDirect = pow(pow(self.R + hC, 2) + pow(self.R + h1, 2) - 2 * (self.R + hC) * (self.R + h1) * cos(c), 0.5)
		AoDInv = asin((self.R + h1) * sin(c) / dDirect)

		if self.debug:
			print(AoDInv)
			print(self.refPoints[0].AoDInv)
		bearingPixelChange = (bearing - self.refPoints[0].bearing) / self.anglePerPixel
		distancePixelChange = (AoDInv - self.refPoints[0].AoDInv) * 180 / pi / self.anglePerPixel

		x = self.refPoints[0].x + bearingPixelChange * cos(self.imRotRad)
		# TODO: sine terms
		y = self.refPoints[0].y - distancePixelChange * cos(self.imRotRad)
		return x, y

	# Returns a Geopoint object for the target x, y and height.
	# If not initialized or ****an error occurs****, returns None
	# WARNING: distance has been tested, but the other return values have not!
	def get_geopoint_from_xy(self, x, y, height=0):
		if not self.initialized:
			return None
		target = Geopoint(x=x, y=y, height=height)

		dx = x - self.refPoints[0].x
		dy = self.refPoints[0].y - y
		# base case: when dx and dy are both equal to zero, the point is our reference point
		# This case breaks some math below if handled.
		# Note: this returns an in
		if dx == 0 and dy == 0:
			if self.refPoints[0].height != height:
				return None
			target = Geopoint(self.refPoints[0].lat, self.refPoints[0].lon,
							  self.refPoints[0].height, self.refPoints[0].x, self.refPoints[0].y)
			return target

		beta = atan2(dy, dx)
		h = pow(pow(dx, 2) + pow(dy, 2), 0.5)
		x1 = h * cos(beta + self.imRotRad)
		y1 = h * sin(beta + self.imRotRad)
		if self.debug:
			print("Y-prime: " + str(y1))

		target.bearing = x1 * self.anglePerPixel + self.refPoints[0].bearing
		target.AoDInv = self.refPoints[0].AoDInv + y1 * self.anglePerPixel * pi / 180
		if self.debug:
			print("Target AoD inverse: " + str(target.AoDInv))
			print("Target to camera AoD inverse: " + str((self.R + cameraPos.height)
														 / (self.R + height) * sin(target.AoDInv)))

		# Angles of a triangle sum to pi. Formula is pi - angle1 - angle2
		# Uses obtuse sign law here
		# multiply by the radius of Earth to find arc distance
		try:
			target.dist = self.R * (pi - target.AoDInv -
									(pi - asin((self.R + self.cameraPos.height) * sin(target.AoDInv) / (self.R + height))))
		# positions above the horizon will throw an error (py2) or be negative (py3).
		# Override this with 'far away' (15km)
		except:
			target.dist = 15000
		if target.dist < 0:
			target.dist = 15000

		# Math works in radians, but we want degrees for output
		bearingRad = target.bearing * pi / 180
		angDist = target.dist / self.R
		target.lat = asin(sin(self.cameraPos.lat * pi / 180) * cos(angDist) + cos(self.cameraPos.lat * pi / 180) * sin(angDist) * cos(bearingRad))
		target.lon = self.cameraPos.lon * pi / 180 + atan2(sin(bearingRad) * sin(angDist) * cos(self.cameraPos.lat * pi / 180), cos(angDist) - sin(self.cameraPos.lat * pi / 180) * sin(target.lat))
		target.lat *= 180 / pi
		target.lon *= 180 / pi

		return target

	def get_dist_from_coords(self, lat, lon):
		if not self.initialized:
			return 0

		psiC = self.cameraPos.lat * pi / 180
		psi0 = lat * pi / 180
		lambdaC = self.cameraPos.lon * pi / 180
		lambda0 = lon * pi / 180

		a = pow(sin((psi0 - psiC) / 2), 2) + cos(psiC) * cos(psi0) * pow(sin((lambda0 - lambdaC) / 2), 2)
		c = 2 * atan2(pow(a, 0.5), pow(1 - a, 0.5))
		distance = self.R * c

		return distance
