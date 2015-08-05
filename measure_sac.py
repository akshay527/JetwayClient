#!/bin/python

from mdb import *
import subprocess
import sys
import socket
import smtplib
import os.path
import os
import binascii
import time
import datetime
from mcontrol import *
import hashlib

# Main measurement util for SaC
#
# assumes one or more measurement series as parameter
# will process series sequentially


def ex(p):
	return subprocess.call(p, shell=True)


# Use symbolic links to map powermeter readings to local files if necessary
home = os.environ['HOME'] # Sets home file path (/home/feature/)
workingDir = os.environ['WORK'] # Sets workingDir path (/home/feature/energy)
powermeterPath = workingDir+"energy.log" # Sets powermeterPath (/home/feature/energy/energy.log)
cpumeterPath = workingDir+"cpu.log" # Sets cpumeterPath (/home/feature/energy/cpu.log)
resultPath = workingDir+"result.log" # Sets resultPath (/home/feature/energy/result.log)

tmpPowermeterPath = workingDir+".energy.log.tmp" # Sets temporary powermeterPath (/home/feature/energy/.energy.log.tmp)
tmpCpumeterPath = workingDir+".cpu.log.tmp" # Sets temporary cpumeterPath (/home/feature/energy/.cpu.log.tmp)

timeout = "20m" # Sets timeout to 20 minutes

time_start = time.time()
time_end = time.time()

msrDir = workingDir+"sac_results/" # Sets the result directory  to /home/feature/energy/sac_results/

SACOUT = workingDir+"sac/tmp.out" 
SACCOMPILE = workingDir+"sac-compile.sh" # Sets SACCOMPILE to /home/feature/energy/sac-compile.sh
SACRUN = workingDir+"sac-run.sh" # Sets SACRUN to /home/feature/energy/sac-run.sh

ERRORLOG = workingDir+"errorlog.txt" # Sets ERRORLOG to /home/feature/energy/errorlog.txt
MYWEMO = home+"myWemo.txt"

ex("mkdir -p "+workingDir) # Creates the working directory if it does not already exist
ex("mkdir -p "+msrDir) # Creates the result directory if it does not already exist
os.chdir(workingDir) # cd /home/feature/energy
assert os.path.isfile(SACCOMPILE) # Checks that sac-compile.sh exists at /home/feature/energy/sac-compile.sh
assert os.path.isfile(SACRUN) # Checks that sac-run.sh exists at /home/feature/energy/sac-run.sh
print "starting measuring process. make sure power readings are activated and directed to "+powermeterPath

def countLines(f):
	with open(fname) as f:
		for i, l in enumerate(f):
            		pass
    	return i + 1

def hasErrors(elapsedTime):
	with open(ERRORLOG) as f:
		x = int(f.readline())
		if (x > 2 and elapsedTime < 15) or x > 10:
			return True
		else:
			return False
			
def normalize(datapoint):
	wemo = subprocess.Popen("cat " + MYWEMO, shell=True, stdout=subprocess.PIPE).stdout.readline().strip()	
	if wemo == "172.25.33.26": # Feature 2
		return (0.9347 * datapoint) - 498.64
	if wemo == "172.25.33.27": # Feature 3
		return datapoint
	if wemo == "172.25.33.28": # Feature 4
		return datapoint
	if wemo == "172.25.33.29": # Feature 5
		return (1.0159 * datapoint) - 762.55
	if wemo == "172.25.33.30": # Feature 6
		return datapoint
	if wemo == "172.25.33.31": # Feature 7
		return (1.0393 * datapoint) - 688.21
	if wemo == "172.25.33.32": # Feature 8
		return (1.0127 * datapoint) - 48.389
	if wemo == "172.25.33.24": # Feature 10
		return (0.9686 * datapoint) - 46.065
	if wemo == "172.25.33.25": # Feature 11
		return (1.035 * datapoint) - 644.22
	return datapoint

def checkLogFileIntegrity(logFile, cmd, elapsedTime):
	x = subprocess.Popen("stat " + logFile + " | grep -o -e \"Modify: ....-..-.. ..:..:..\" | sed \'s/Modify: //g\'", shell=True, stdout=subprocess.PIPE).stdout.readline()
	lastAccess = datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S\n")
	currentTime = datetime.datetime.today()
	difference = currentTime - lastAccess
	if difference.seconds > 5 or hasErrors(elapsedTime):
                message = "The Wemo connected to " + socket.gethostname() + " lost responsiveness. The previous measurement was repeated to ensure accuracy. Last command was " + cmd 
		sendEmail(message)
		print "Sending Error Email and Repeating"
                sys.stdout.flush()
		server.quit()
		raise Exception("Wemo Error")
		
def readAvgLogValue(logFile, normalization):
	try:
		f = open(logFile) # Opens the log file containing the measurement data
		fline = f.readline() # Reads the first line of the file
		ftotal = 0 # Intializes total
		fcount = 0 # Initialize line/measurement count
		while fline: # While there are more lines in the file to be read
			fcount = fcount + 1 # Increments the line/measurement count
			if normalization:
				ftotal = ftotal + normalize(float(fline)) # Adds the normalized measurement data on the given line to the total 
			else:
				ftotal = ftotal + float(fline) # Adds the measurement data on the given line to the total
			fline = f.readline() # Reads the next line
		if fcount > 0: # Ensures no division by 0 error occurs (ie Ensures there is measurement data)
			cpu = str( ftotal / fcount) # Sets CPU to be the average CPU utilization
		else: # There are no measurements
			cpu = "-1"
		return cpu
	except Exception as err:
                message = "An error occurred while reading averages from a log file. Measurements have been stopped, and it is recommended that you repeat your most recent measurement."
                sendEmail(message)
		print "Sending Error Email"
                sys.stdout.flush()
		server.quit()
		ex("sh " + os.environ['WORK'] + "sac.sh stop")	

def readLogFile(logfile):
	myvars = {}
	assert os.path.isfile(logfile) # Makes sure that the file exists
	with open(logfile) as myfile: # Opems the logfile and stores it as myfile
		for line in myfile: # While there are more lines in myfile to be read
			if ":" in line: # If there is a : in the current line. then extract the data from the line (indicates a proper measurement)
				name, var = line.partition(":")[::2] 
				myvars[name.strip()] = var.strip()
	return myvars
	

def hashfile(f):
        return hashlib.sha1(open(f, 'rb').read()).hexdigest()

def measure(logfile, cmd, extraGatherResults=None):
        global time_start
	global time_end
	command = "time -f \"real:%e\nuser:%U\nsys:%S\nexit:%x\nioin:%I\nioout:%O\nmaxmem:%M\navgmem:%K\" -o "+logfile+" -a timeout " + timeout + " " + cmd 
	#discard old measurements
	ex(">{0}; >{1}; >{2} ; >{3}".format(powermeterPath, cpumeterPath, logfile, resultPath))
	time_start = time.time()
	exitcode = ex(command)
	time_end = time.time()
	ex("sed -e 's/^.*: \([0-9]*\)$/\\1/' < {0} | grep -a \"^[0-9]*$\" > {1}".format(powermeterPath, tmpPowermeterPath))
	# ex("cat "+tmpPowermeterPath)
	ex("cat " + tmpPowermeterPath + " | grep -c \'#\' > " + ERRORLOG)
	ex("sed -i \'/#/d\' " + tmpPowermeterPath)
	ex("cp {0} {1}".format(cpumeterPath, tmpCpumeterPath))
	ex("sed -i \'s/M  all  100.00/100.0/g\' " + tmpCpumeterPath)
	avgCpu=readAvgLogValue(tmpCpumeterPath, False)
	checkLogFileIntegrity(tmpPowermeterPath, command, time_end - time_start) # Checks that the power measurements exist and are valid
	avgPower=readAvgLogValue(tmpPowermeterPath, True)
	results = { "cpu": avgCpu, "power": avgPower, "exit": exitcode }
	if extraGatherResults!=None:
		results.update(extraGatherResults())
	results.update(readLogFile(logfile))
	return results



#perform a measurement for a specific configuration (in a series) and 
#returns a list of measurement results (map from NFP name to value)
#
#the method is called by the mcontrol infrastructure
#the actual measurement depends heavily on the actual program
#being measured.
#in this case, both the compilation and the running of the compiled
#program are measured. it used measurements from `time` as well as
#measurement from external CPU meters and power meters
def measureSaC(seriesName, configId):
	param = getConfigParams(configId)
	print "\n*** measuring {0} ({1})".format(configId, param)
	sys.stdout.flush()
	time.sleep(5)	
	compileResults = measure(msrDir+".compilelog."+seriesName,SACCOMPILE+" "+param)
	results = {}
	results.update({ "compile start" : format(time_start,".2f"), "compile end" : format(time_end,".2f"), "compile time" : format(time_end - time_start,".2f") })
	if compileResults["exit"] != "0":
		print "compilation failed."
		runResults = {}
	else:
		compileResults["size"]=os.path.getsize(SACOUT)
		hashv=hashfile(SACOUT)
		compileResults["hash"]=hashv	
		runlogFile=msrDir+".runlog."+seriesName+"."+hashv
		if os.path.isfile(runlogFile):
			print "same binary measured earlier, skipping"
			runResults = {}
		else:
			time.sleep(5)
			runResults = measure(runlogFile, SACRUN)
			with open(resultPath) as myfile:
				output=myfile.read()
				results.update({ "run start" : format(time_start,".2f"), "run end" : format(time_end,".2f"), "run time" : format(time_end - time_start,".2f"), "result" : output })
	results.update(dict(("compile-"+k, v) for (k,v) in compileResults.items()))
	results.update(dict(("run-"+k, v) for (k,v) in runResults.items()))
	print str(results)
	return results



if len(sys.argv)<=1:
	print "expecting measurement series as parameter"
	sys.exit(1)
mControl(sys.argv[1:], measureSaC)
