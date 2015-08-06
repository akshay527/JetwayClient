#!/usr/bin/python

# This script is executed when sac.sh is told to stop running measurements. It essentially destroys the measurement
# being performed from the MResults table of the database, and then reinserts the configID into the Todo table of the database

import sys
import subprocess
import os.path
from mdb import *

def ex(cmd):
	subprocess.call(cmd, shell=True) # Used to execute command line commands

SID = os.environ['WORK'] + ".sid"
CONFIGID = os.environ['WORK']  + ".configID"

with open(SID) as seriesID:
	with open(CONFIGID) as configurationID:
		s = seriesID.readline().rstrip()
		c = configurationID.readline().rstrip()
		try:
			removeConfig(s, c)
			addConfig(s, c, 0)
			ex("rm " + SID)
			ex("rm " + CONFIGID)
		except Exception, e:
			pass
		

