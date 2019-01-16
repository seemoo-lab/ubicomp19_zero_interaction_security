#!/bin/bash

### Script to restart an instance of nodejs (capture of sensor data from SensorTag) 

# Path to main nodejs script
nodejs_script="/home/pi/nodejs/main.js"

# May want to add check if 2 command line params were provided

# Infinite loop
while [ true ]
do

  # Check if nodejs is running
  if ! pgrep -x "node" > /dev/null
  then

    # Display when nodejs stopped
    stop_date=$(date +'%Y-%m-%d %H:%M:%S')
    echo "Stopped: $stop_date"

    # Restart nodejs
    echo "Restarting nodejs..."
    node $nodejs_script "$1" "${2}" &
  fi

  # Sleep 
  sleep 5

done
