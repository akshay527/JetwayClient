#!/usr/bin/python

# This script is executed at startup on each of the Feature machines as a workaround for when the Wemos randomly switch themselves off.
# If a measurement is in progress at the time of power loss, the machine will scrap the last measurement and add it back to the Todo list
# If a measurement is not in progress at the time of power loss, the machine does nothing


import sys
import subprocess
import os
import os.path
import socket
from mdb import *
from mcontrol import *
import time

SACPID = os.environ['WORK'] + "sac.pid"
SID = os.environ['WORK'] + ".sid"
CONFIGID = os.environ['WORK']  + ".configID"
FAILSAFE = os.environ['HOME'] + "failsafe.log"

def ex(cmd):
	subprocess.call(cmd, shell=True)

if os.path.isfile(SACPID):
	x = subprocess.check_output("cat " + SACPID, shell=True).strip() # Stores the PID
	try: # Tries to check if the process exists ; does nothing if the process exists
		y = subprocess.check_output('[ -e /proc/' + x + ' ]', shell=True).strip() 
	except Exception, e: # Catches an exception that is thrown when the process does not exist
		sendEmail(socket.gethostname() + " has just rebooted") # Sends error email
		with open(SID) as seriesID:
			with open(CONFIGID) as configurationID:
				s = seriesID.readline().rstrip()
				c = configurationID.readline().rstrip()
				ex("sh " + os.environ['WORK'] + "/sac.sh stop > /dev/null") # Stops measurements
				try:
					removeConfig(s, c) # Removes last measurement from MResults
					addConfig(s, c, 0) # Inserts last measurement into Todos
				except Exception, e:
					pass
				ex("sh " + os.environ['WORK'] + "/sac.sh start " + s + " > /dev/null &") # Restarts measurements

ex("echo 'failsafe.py was executed at " + time.strftime("%H:%M:%S") + "' >> " + FAILSAFE)
