#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser

def gps2video(config_file_path="config.ini"):
	cf = ConfigParser.ConfigParser()
	try:
		cfp = open(config_file_path)
	except:
		print config_file_path+"文件打开失败。"
		print "打开example.ini文件，对里面的配置信息进行修改后另存为"+config_file_path+"。"
		print "不用担心不会配置，里面有中文注释。"
		return
	cf.readfp(cfp)

if __name__ == "__main__":
	gps2video()
