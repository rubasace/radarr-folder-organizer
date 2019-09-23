#!/bin/ash

# Execute the sync script in a loop, waiting DELAY before running again
while true
do
	python /FolderOrganizer.py
	sleep ${DELAY:-15m}
done