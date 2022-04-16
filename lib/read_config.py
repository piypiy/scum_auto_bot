import configparser
import os
from os.path import expanduser


class Read_Config(object):
  def __init__(self):
    self.config = configparser.ConfigParser()
    home = expanduser("~")
    #%USERPROFILE%\AppData\Local\SCUM_Admin_Helper\
    if(os.path.exists(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini") == False):
        self.config.read("config/config.ini")
        with open(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini", 'w') as configfile:
          self.config.write(configfile)
    else:
      self.config.read(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini")

  def getConfig(self):
    return self.config

  def writeConfig(self,category, name, value):
    home = expanduser("~")
    self.config.read(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini")
    self.config.set(category, name, value)
    with open(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini", 'w') as configfile:
        self.config.write(configfile)
    self.config.read(home+"\\AppData\\Local\\SCUM_Admin_Helper\\config.ini")
