#!/bin/ash

set -e

# Execute the sync script in a loop, waiting DELAY before running again
if [ "${DELAY}" == "DISABLED" ] ; then
  python /FolderOrganizer.py
else
  while true
    do
      python /FolderOrganizer.py
      sleep ${DELAY:-15m}
    done
fi

