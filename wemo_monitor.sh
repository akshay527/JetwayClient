#!/bin/bash

WEMOPID="wemomonitor.pid"
WEMOLOG="energy.log"
WEMOSCRIPT="WemoControl/wemo_insight.py"
WEMO="myWemo.txt"

case "$1" in
	start)
		if [ -e "$WORK$WEMOPID" ] ; then # Checks if the file wemomonitor.pid exists
			echo wemo monitor is already running
		else
			echo starting wemo monitor
			nohup python $WORK$WEMOSCRIPT $(cat $HOME$WEMO) > $WORK$WEMOLOG  2>&1&
			echo $! > $WORK$WEMOPID
		fi
		;;
	stop)
		if [ -e "$WORK$WEMOPID" ] ; then # Checks if the file wemomonitor.pid exists
			echo stopping wemo monitor
			kill -9 "$(cat $WORK$WEMOPID)" # Kills the job with PID stored in wemomonitor.pid
			rm $WORK$WEMOPID # Deletes the file wemomonitor.pid
		else
			echo wemo monitor is already stopped
		fi
		;;
	status)
		if [ -e "$WORK$WEMOPID" ] ; then # Checks if the file wemomonitor.pid exists
			echo wemo monitor is running
		else
			echo wemo monitor is not running
		fi
		;;
	*)
	  echo "Usage: wemo_monitor.sh {start | stop | status}" >&2
	  exit 3
	  ;;
esac
exit 0
