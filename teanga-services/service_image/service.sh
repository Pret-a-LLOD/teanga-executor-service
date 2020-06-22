#!/bin/bash
for i in {1..3};
do
	sleep 3 
	echo $i
done;
echo 312 >> ./output/output9000.csv
echo done
