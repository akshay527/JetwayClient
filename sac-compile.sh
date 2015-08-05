#!/bin/bash

PROGRAM="sac/kmeans/kmeans.sac"
OUTFILE="sac/tmp.out"

sac2c $WORK$PROGRAM -o $OUTFILE $@ # Compiles the given program for benchmark testing
