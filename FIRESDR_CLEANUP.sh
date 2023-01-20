#!/bin/bash
echo "FIRESDR_CLEANUP Created By Joe Greening"
for i in {1..3}
do
	{
	ps -ef | grep rtl_fm | grep -v grep | awk '{print $2}' | xargs kill
	ps -ef | grep multimon-ng | grep -v grep | awk '{print $2}' | xargs kill
	ps -ef | grep python3 | grep -v grep | awk '{print $2}' | xargs kill
	} &> /dev/null & echo "Cleaning up previous sessions... ($i/3)"
done
sleep 5