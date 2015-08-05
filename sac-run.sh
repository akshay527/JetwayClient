#!/bin/bash

OUTFILE="sac/tmp.out"
INPUT="sac/kmeans/input/sac_819200.txt"
OUTPUT="result.log"

$WORK$OUTFILE < $WORK$INPUT >> $WORK$OUTPUT # Runs the compiled program and stores the result in result.log
