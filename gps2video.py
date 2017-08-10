#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, ConfigParser, gpxpy, math, urllib2

class gps2video_cf(ConfigParser.ConfigParser):
	def __init__(self, config_file_path):
		self.cfp = open(config_file_path)
		ConfigParser.ConfigParser.__init__(self)
		ConfigParser.ConfigParser.readfp(self, self.cfp)

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
		self.latitude = self.min_latitude + self.latitude_size
		self.longitude = self.min_longitude + self.longitude_size


class map_class:
	def __init__(self, cf, gps):
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
		self.gps = gps
		self.get_zoom()
		#print "缩放率是",self.zoom

		self.map_key = cf.get("required", "google_map_key")

		self.map_type = cf.get("required", "google_map_type")
		if self.map_type != "roadmap" and self.map_type != "satellite" and self.map_type != "terrain" and self.map_type != "hybrid":
			raise Exception("地图类型"+self.map_type+"是什么鬼？")

		self.output_dir="./"
		if cf.has_option("optional", "output_dir"):
			self.output_dir = cf.get("optional", "output_dir")
			if not os.path.isdir(self.output_dir):
				raise Exception("输出目录"+self.output_dir+"有问题。")

	def get_zoom(self):
		self.zoom = int(math.log(self.real_width / self.gps.longitude_size, 2))
		h_zoom = int(math.log(self.real_height / self.gps.latitude_size, 2))
		if h_zoom < self.zoom:
			self.zoom = h_zoom

	def get_map(self):
		url = "https://maps.googleapis.com/maps/api/staticmap?format=png"
		url += "&key=" + self.map_key
		url += "&center=" + str(self.gps.latitude) + "," + str(self.gps.longitude)
		url += "&zoom=" + str(self.zoom)
		url += "&size=" + str(self.width) + "x" + str(self.height)
		url += "&maptype=" + self.map_type
		print url
		#fp = urllib2.urlopen(url = url,timeout = 10)

def gps2video(config_file_path="config.ini"):
	#配置对象cf初始化
	try:
		cf = gps2video_cf(config_file_path)
	except:
		print config_file_path+"文件打开失败。"
		print "打开example.ini文件，对里面的配置信息进行修改后另存为"+config_file_path+"。"
		print "不用担心不会配置，里面有中文注释。"
		return

	#轨迹对象gps初始化
	gps = gps_class(cf)

	#地图对象map初始化
	m = map_class(cf, gps)
	m.get_map()

if __name__ == "__main__":
	gps2video()
