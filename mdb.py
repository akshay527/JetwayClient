#!/usr/bin/python
import MySQLdb
import ConfigParser
import sys
import subprocess
import os

configParser = ConfigParser.RawConfigParser()   
configFilePath = r'.dbconfig'
configParser.read(configFilePath)

db = MySQLdb.connect(host=os.environ['SQLHOST'], # your host, usually localhost
                     user=configParser.get('db','user'), # your username
                      passwd=configParser.get('db','passwd'), # your password
                      db=os.environ['DBNAME']) # name of the data base
cur = db.cursor() 


seriesIdCache = {}
nfpIdCache = {}
priority = 0

SID = os.environ['WORK'] + ".sid"
CONFIGID = os.environ['WORK']  + ".configID"

def execSqlOne(sql):
	cur.execute(sql)
	r=cur.fetchone()
	if r==None:
		return None
	return r[0]

#looks up the series. fails if series does not exist
def getSeriesId(seriesname):
	if seriesname not in seriesIdCache:
		cur.execute('select SeriesId from Series where name="'+seriesname+'"')
		r=cur.fetchone()
		if r==None:
			print "Series "+seriesname+" not found in measurement database. Quitting."
			sys.exit(1)
		seriesIdCache[seriesname]=r[0]
	return seriesIdCache[seriesname]

#looks up an NFP, creates that NFP if it does not exist
def getNFPId(nfp):
	if nfp not in nfpIdCache:
		cur.execute('select ID from NFP where name="'+nfp+'"')
		r=cur.fetchone()
		if r==None:
			print "creating new NFP: "+nfp
			cur.execute('insert into NFP (Name) values ("'+nfp+'")')
			cur.execute('select ID from NFP where name="'+nfp+'"')
			db.commit()
			r=cur.fetchone()
		nfpIdCache[nfp]=r[0]
	return nfpIdCache[nfp]

#resultmap is a map from NFP-names to string values representing results
def storeMeasurements(seriesName, configId, resultMap):
	global cur
	assert len(resultMap)>0
	sql = 'insert into MResults (ConfigurationID, SeriesID, NFPID, Value) values '
	for k in resultMap:
		sql += '({0}, {1}, {2}, "{3}"), '.format(configId, getSeriesId(seriesName), getNFPId(k), resultMap[k])
	cur.execute(sql[:-2])
	db.commit()

#add configuration to todo table
def addConfig(seriesName, configId, priority):
	global cur
	sql = 'insert into Todos (SeriesID, ConfigurationID, Priority) values '
	sql += '({0}, {1}, {2})'.format(getSeriesId(seriesName), configId, priority)
	cur.execute(sql)
	db.commit()

#remove configuration from MResults
def removeConfig(seriesName, configId):
	global cur
	sql = 'delete from MResults where SeriesID = {0} and ConfigurationID = {1}'.format(getSeriesId(seriesName), configId)
	cur.execute(sql)
	db.commit() 

#gets priority of current configuration being tested
def getPriority():
	global priority
	return priority


#finds the next available measurement in the todo table
#returns the configurationId or None if there is no remaining configuration (or if there is a concurrency issue)
#deletes the entry from the todo table, so that it's not claimed again
def claimNextMeasurement(seriesName):
	global priority
	db.commit()
	try:
		sid=getSeriesId(seriesName)
		subprocess.call("echo " + str(seriesName) + " > " + SID, shell=True)
		nextConfig = execSqlOne("select ConfigurationID from Todos where SeriesId={0} order by priority, ConfigurationID Limit 1".format(sid))
		if nextConfig != None:
			priority = execSqlOne("select Priority from Todos where ConfigurationID={0}".format(nextConfig))
			cur.execute("delete from Todos where SeriesId={0} and ConfigurationId={1}".format(sid,nextConfig))
		db.commit();
		subprocess.call("echo " + str(nextConfig) + " > "  + CONFIGID, shell=True)
		return nextConfig
	except Exception, e:
		print e
		db.rollback()
		return None

def countRemainingMeasurements(seriesNames):
	return execSqlOne("select count(*) from Todos, Series where "+
		" or ".join(map((lambda x: '(Series.Name="'+x+'")'),seriesNames)))


def getConfigParams(configId):
	return execSqlOne("select CompilerOptions from Configurations where ID="+str(configId))	
