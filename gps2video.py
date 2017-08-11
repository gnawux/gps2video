#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, ConfigParser, gpxpy, math, urllib2, cv2

class gps2video_cf(ConfigParser.ConfigParser):
	def __init__(self, config_file_path):
		self.cfp = open(config_file_path)
		ConfigParser.ConfigParser.__init__(self)
		ConfigParser.ConfigParser.readfp(self, self.cfp)

		self.output_dir = "./output/"
		if self.has_option("optional", "output_dir"):
			self.output_dir = self.get("optional", "output_dir")
			if os.path.exists(self.output_dir) and not os.path.isdir(self.output_dir):
				raise Exception("输出目录"+self.output_dir+"不是目录，不好好设置信不信给你删了？")
		if not os.path.exists(self.output_dir):
			os.mkdir(self.output_dir)
		print "输出目录设置为:" + self.output_dir

	def __del__(self):
		if hasattr(self, 'cfp'):
			self.cfp.close()

	def has_option(self, section, option):
		if not ConfigParser.ConfigParser.has_option(self, section, option):
			return False
		if ConfigParser.ConfigParser.get(self, section, option) == "":
			return False
		return True

	def get(self, section, option):
		if not self.has_option(section, option):
			raise Exception(section+"中的项目"+option+"没设置啊！")
		return ConfigParser.ConfigParser.get(self, section, option)

	def getint(self, section, option):
		if not self.has_option(section, option):
			raise Exception(section+"中的项目"+option+"没设置啊！")
		return ConfigParser.ConfigParser.getint(self, section, option)


class gps_class:
	def __init__(self, cf):
		self.cf = cf
		self.gfp = open(cf.get("required", "gps_file"))
		self.rec = gpxpy.parse(self.gfp)
		self.get_max_min()

	def __del__(self):
		if hasattr(self, 'gfp'):
			self.gfp.close()

	def get_max_min(self):
		self.max_latitude = None
		self.min_latitude = None
		self.max_longitude = None
		self.min_longitude = None
		for track in self.rec.tracks:
			for segment in track.segments:
				for point in segment.points:
					if self.max_latitude == None or point.latitude > self.max_latitude:
						self.max_latitude = point.latitude
					if self.min_latitude == None or point.latitude < self.min_latitude:
						self.min_latitude = point.latitude
					if self.max_longitude == None or point.longitude > self.max_longitude:
						self.max_longitude = point.longitude
					if self.min_longitude == None or point.longitude < self.min_longitude:
						self.min_longitude = point.longitude
		self.latitude_size = self.max_latitude - self.min_latitude
		self.longitude_size = self.max_longitude - self.min_longitude
		self.latitude = self.min_latitude + (self.latitude_size / 2)
		self.longitude = self.min_longitude + (self.longitude_size / 2)

	def write_video(self, m):
		vw = cv2.VideoWriter(os.path.join(self.cf.output_dir, 'v.avi'),
				     fourcc = cv2.cv.CV_FOURCC('D','I', 'V','X'),
				     fps = 36,
				     frameSize = (m.width, m.height))
		for track in self.rec.tracks:
			for segment in track.segments:
				for point in segment.points:
					m.write_video(vw, point.latitude, point.longitude)
		m.write_video_last(vw)
		vw.release()

class map_class:
	def __init__(self, cf, gps):
		self.gps = gps
		self.cf = cf
		self.prev_x = None
		self.prev_y = None

		self.premium = False
		if cf.has_option("optional", "google_map_premium"):
			self.premium = cf.get("optional", "google_map_premium")
			if self.premium == "yes":
				self.premium = True
			elif self.premium == "no":
				self.premium = False
			else:
				raise Exception("你到底是不是google map premium，写清楚！")

		self.width = cf.getint("required", "video_width")
		if not self.premium and self.width > 640:
			raise Exception("你把video_width设置这么大不怕系统爆炸吗？")
		self.height = cf.getint("required", "video_height")
		if not self.premium and self.height > 640:
			raise Exception("你把video_height设置这么大不怕系统爆炸吗？")
		self.border = cf.getint("required", "video_border")
		b_tmp = self.border * 2
		if b_tmp >= self.width or b_tmp >= self.height:
			raise Exception("你把video_border设置这么大不怕系统爆炸吗？")
		self.real_width = self.width - b_tmp
		self.real_height = self.height - b_tmp
		self.get_zoom()
		self.x = float(self.width) / 2
		self.y = float(self.height) / 2
		#print "缩放率是",self.zoom

		self.map_key = cf.get("required", "google_map_key")

		self.map_type = cf.get("required", "google_map_type")
		if self.map_type != "roadmap" and self.map_type != "satellite" and self.map_type != "terrain" and self.map_type != "hybrid":
			raise Exception("地图类型"+self.map_type+"是什么鬼？")

	def get_zoom(self):
		self.zoom = int(math.log(self.real_width / self.gps.longitude_size, 2))
		h_zoom = int(math.log(self.real_height / self.gps.latitude_size, 2))
		if h_zoom < self.zoom:
			self.zoom = h_zoom
		if self.zoom > 15:
			self.zoom = 15
		self.times = 2 ** self.zoom

	def gps_to_pixel(self, latitude, longitude):
		y = round(self.y - (latitude - self.gps.latitude) * self.times)
		x = round(self.x - (self.gps.longitude - longitude) * self.times)
		return int(x), int(y)

	def get_map(self):
		url = "https://maps.googleapis.com/maps/api/staticmap?format=png"
		url += "&key=" + self.map_key
		url += "&center=" + str(self.gps.latitude) + "," + str(self.gps.longitude)
		url += "&zoom=" + str(self.zoom)
		url += "&size=" + str(self.width) + "x" + str(self.height)
		url += "&maptype=" + self.map_type
		print "将从下面的地址下载地图："
		print url

		self.pic = os.path.join(self.cf.output_dir, "base.png")

		ufp = urllib2.urlopen(url = url, timeout = 10)
		fp = open(self.pic, "wb")
		fp.write(ufp.read())
		fp.close()
		ufp.close()

		self.img = cv2.imread(self.pic)

	def write_video(self, vw, latitude, longitude):
		x, y = self.gps_to_pixel(latitude, longitude)
		if self.prev_x != None:
			cv2.line(self.img, (self.prev_x, self.prev_y), (x, y), (0, 0, 0), 3, lineType=cv2.CV_AA)
		cv2.circle(self.img, (x, y), 0, (0, 0, 0), 3, lineType=cv2.CV_AA)
		vw.write(self.img)
		self.prev_x = x
		self.prev_y = y

	def write_video_last(self, vw):
		for i in range(36 * 2):
			vw.write(self.img)

def gps2video(config_file_path="config.ini"):
	#配置对象cf初始化
	try:
		cf = gps2video_cf(config_file_path)
	except Exception as e:
		print config_file_path + "文件打开出错：", e
		print "打开example.ini文件，对里面的配置信息进行修改后另存为"+config_file_path+"。"
		print "不用担心不会配置，里面有中文注释。"
		return

	#轨迹对象gps初始化
	gps = gps_class(cf)

	#地图对象map初始化
	m = map_class(cf, gps)

	#下载地图
	m.get_map()

	gps.write_video(m)

if __name__ == "__main__":
	gps2video()
