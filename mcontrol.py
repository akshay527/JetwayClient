from mdb import *
import socket
import time
import subprocess
import smtplib

# Main measurement control loop
#
# interacts with the database to pick the next measurements
# and stores the results
#
# runs indefinetly

def sendEmail(message):
	sender = "synergylabserrordaemon@gmail.com"
        receivers = "akshaypa@andrew.cmu.edu"
        username = 'synergylabserrordaemon'
        password = 'synergy_lab'
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(username,password)
        server.sendmail(sender, receivers, message)
	server.quit()

STATUS = os.environ['WORK'] + 'status.txt'
ERRORLOG = os.environ['WORK'] + 'errorlog.txt'
# wemoCheck checks if the Wemo is taking measurements successfully. It will stop the measurement process and send an email message 
# indicating failure after ten failed attempts to read from the Wemo.
def wemoCheck():
	errorCount = 0
	while ((subprocess.Popen("tail -n 1 " + STATUS, shell=True, stdout=subprocess.PIPE)).stdout).readline() == "Error\n":
		errorCount += 1
		if errorCount > 10:
			message = "The Wemo connected to " + socket.gethostname() + " is no longer responsive. Measurements have been stopped, and it is recommended that you refer to ~/energy/nohup.out and rerun the last measurement configuration(s)."
			sendEmail(message)
			print "Sending Error Email" 
			sys.stdout.flush()
			subprocess.call("sh " + os.environ['WORK'] + "sac.sh stop", shell=True)




# mControl input:
# - seriesNames: list of seriesNames
# - mfun: measurement function that takes a (seriesName, configurationId) and returns a map with measurement results
def mControl(seriesNames, mfun):
	assertSeries(seriesNames)
	currentSeriesIdx = 0
	currentSeries = seriesNames[currentSeriesIdx]
	errorCounter = 0
	totalTime = 0
	totalCount = 0

	wemoCheck()

	while True:
		sys.stdout.flush()	
		# change series after 20 errors
		if errorCounter>0 and (errorCounter % 20 == 0) and len(seriesNames)>1:
			currentSeriesIdx = (currentSeriesIdx + 1) % len(seriesNames)
			currentSeries = seriesNames[currentSeriesIdx]
			print "#switching to series "+currentSeries
		nextConfigId = claimNextMeasurement(currentSeries)
		if nextConfigId == None:
			if countRemainingMeasurements(currentSeries) == 0:
				print "All Measurements Complete"
				sys.stdout.flush()
				subprocess.call("sh " + os.environ['WORK'] + "sac.sh stop", shell=True)
			errorCounter += 1
			wait = 1
			#slowly increasing waits between errors
			if errorCounter > 10:
				wait = 5
			if errorCounter > 20:
				wait = 10
			if errorCounter > 30:
				wait = 30
			if errorCounter > 100:
				wait = 120
			print("#no next measurement found, waiting {0} seconds".format(wait))
			time.sleep(wait)
		else:
			# no errors, so let's measure
			try:
				errorCounter = 0
				t1= time.time()
				mresult = mfun(currentSeries, nextConfigId)
				t2= time.time()
				if mresult!=None:
					try:
						with open(ERRORLOG) as f:
							mresult.update({ 'wemo timeout' : f.readline(), 'analysis time' : format(t2-t1,".2f"), 'host' : socket.gethostname() , 'analysis start' : format(t1,".2f"), 'analysis end' : format(t2,".2f") })
						storeMeasurements(currentSeries, nextConfigId, mresult)
					except Exception:
						print "Duplicate Entry Found. Ignoring Result\n"
						sys.stdout.flush()
				else:
					if getPriority() > -3:
						print "No Results Found. Inserting back into Todos\n"
						addConfig(currentSeries, nextConfigId, getPriority() - 1)
					else:
						print "Too many failures... Skipping"
				t3=time.time()
				totalCount += 1	
				totalTime += (t3-t1)
				remainingTime = (totalTime/totalCount)*countRemainingMeasurements(seriesNames)
				print("#analysis time: "+format(t2-t1,".2f")+"s, estimated remaining: "+formatTime(remainingTime))
			
			except Exception:
				print "Power Meter Failure. Retrying with same priority."
				addConfig(currentSeries, nextConfigId, getPriority())
				

def formatTime(t):
	d,r=divmod(t,60*60*24)
	h,r=divmod(r,60*60)
	m,r=divmod(r,60)
	return "{0}d {1}h {2}m".format(int(d),int(h),int(m))

def assertSeries(seriesNames):
	#check that series exist
	for s in seriesNames:
		getSeriesId(s)

