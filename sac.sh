#!/bin/bash

SACPID="sac.pid"
OUTPUT="nohup.out"
WEMOMONITOR="wemo_monitor.sh"
CPUMONITOR="CPU_monitor.sh"
STOP="stop.py"
MEASURESAC="measure_sac.py"
CONFIG=".config"
SAC="sac2c-1.00-beta-linux-x86_64"
SACRESULTS="sac_results"

source $CONFIG

case "$1" in
	start)
		if [ -e "$WORK$SACPID" ] ; then #Checks if SAC measurements are running
			echo sac measurements are presumably already running
		else
			if [ -e "$WORK$SACRESULTS" ] ; then
				rm -rf $WORK$SACRESULTS
			fi
			export SACBASE=$HOME$SAC # Specifies variable paths for Ansible to work
			export SAC2CBASE=$SACBASE/sac2c # Specifies variable paths for Ansible to work
			export LD_LIBRARY_PATH=$SAC2CBASE/lib:$LD_LIBRARY_PATH # Specifies variable paths for Ansible to work
			export PATH=$SAC2CBASE/bin:$PATH # Specifies variable paths for Ansible to work
			echo starting sac measurements
			> $WORK$OUTPUT
			sh $WORK$WEMOMONITOR start # Starts the WeMo Power Meter
			sleep 60 # Waits 60 seconds for the WeMo to cycle through the ports
			sh $WORK$CPUMONITOR start	
		        nohup python $WORK$MEASURESAC $2 >> $WORK$OUTPUT 2>&1& # Begins SAC measurements
			echo $! > $WORK$SACPID # Stores the SAC process ID
		fi
		;;
	stop)
		if [ -e "$WORK$SACPID" ] ; then # Checks if SAC measurements are stopped
			echo stopping sac measurements
			sh $WORK$WEMOMONITOR stop # Stops the WeMo Power Meter
			sh $WORK$CPUMONITOR stop # Stops the CPU Monitor
			kill -9 "$(cat $WORK$SACPID)" # Stops the SAC measurements
			rm $WORK$SACPID # Removes the file containing the SAC process ID
			python $WORK$STOP
		else
			echo sac measurements are already stopped
		fi
		;;
	status)
		if [ -e "$WORK$SACPID" ] ; then # Checks if SAC measurements are running
			echo "sac measurements are presumably running"
		else
			echo "sac measurements are stopped"
		fi
		;;

	*)
		echo "Usage: sac.sh {start | stop | status} SERIESID" >&2
	
		exit 3
	  	;;
esac
exit 0
