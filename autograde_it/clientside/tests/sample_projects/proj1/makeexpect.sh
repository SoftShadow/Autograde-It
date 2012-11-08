#!/bin/bash
for f in test/*
do
	echo "Getting output for $f"
	./$f > $f.out
done
