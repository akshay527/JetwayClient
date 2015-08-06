#!/bin/bash

CPUPID="cpumonitor.pid"
RUN="run_CPU.sh"
CPULOG="cpu.log"

case "$1" in
  start)
	if [ -e "$WORK$CPUPID" ] ; then # Checks if the temporary file exists
		echo cpu monitor is already running
	else
		echo starting CPU monitor
		nohup sh $WORK$RUN >> $WORK$CPULOG  2>&1 & # Activates the CPU Monitor
		echo $! > $WORK$CPUPID	# Stores the PID in a temporary file
	fi	
	;;
  stop)
	if [ -e "$WORK$CPUPID" ] ; then # Checks if the temporary file exists
		echo stopping CPU monitor
		kill -9 $(cat $WORK$CPUPID) # Kills the PID stored
		rm $WORK$CPUPID	# Deletes the temporary file containing the PID
	else
		echo cpu monitor is not running
	fi
	;;	
  status)
	if [ -e "$WORK$CPUPID" ] ; then # Checks if the temporary file exists
		echo cpu monitor is running
	else
		echo cpu monitor is not running
	fi
	;;
  *)
    echo "Usage: CPU_monitor.sh {start|stop|status}" >&2
    exit 3
    ;;
esac
exit 0
