#!/bin/ash

# Execute the sync script in a loop, waiting DELAY before running again
while true
do
	python /radarr_folder_organizer/FolderOrganizer.py
	sleep $DELAY
done