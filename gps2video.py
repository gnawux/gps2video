#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser

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

	def has_option_with_output(self, section, option):
		ret = self.has_option(section, option)
		if not ret:
			print section,"中的项目", option, "没设置啊！"


def gps2video(config_file_path="config.ini"):
	global cf

	try:
		cf = gps2video_cf(config_file_path)
	except:
		print config_file_path+"文件打开失败。"
		print "打开example.ini文件，对里面的配置信息进行修改后另存为"+config_file_path+"。"
		print "不用担心不会配置，里面有中文注释。"
		return
	
	if not cf.has_option_with_output("required", "gps_file"):
		return
	

if __name__ == "__main__":
	gps2video()
