#!/bin/bash

### Main script to start, maintain and stop the capture of sensor data from RuuviTag

# Add paths
PATH=$PATH:/bin:/usr/bin:/sbin:/usr/sbin

# Check if we should shutdown
if [ -e /boot/1stexp.txt ]; then
  echo "File exists, exiting..."
  shutdown -P now
  exit 1
fi

# Since we start it from crontab, 
# make sure all other stuff booted
sleep 60

### VARIABLES

# Counters, min/max sizes
conf_size=3
min_uptime_size=2
start_time_size=16

# Config params
macs=""
uptime=""
start_time=""

# Paths: setting
main_conf="/home/pi/conf/main_conf.txt"
ruuvi_capture="/home/pi/scripts/ruuvi_capture.py"

# Remove empty lines in main_conf.txt (just in case)
sed -i '/^$/d' $main_conf

# Read main_conf.txt into array
readarray -t conf_arr < $main_conf

# Check if we have the correct number of config params
if [ ${#conf_arr[@]} -ne $conf_size ]; then
  echo "Error: main_conf.txt contains incorrect number of params!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

# Get macs, uptime (in s-sec, m-min, h-hours) and start_time (format: MM/DD/YYYY HH:MM)
for i in "${!conf_arr[@]}"
do 
  case "$i" in
  "0")
    macs=${conf_arr[$i]}
    ;;
  "1")
    uptime=${conf_arr[$i]}
    ;;
  "2")
    start_time=${conf_arr[$i]}
    ;;
  esac
done

# Remove leading and trailing spaces (for the next check)
macs="$(echo -e "${macs}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
uptime="$(echo -e "${uptime}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
start_time="$(echo -e "${start_time}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

# Final config checks, sigh!
if [ ${#uptime} -lt $min_uptime_size ]; then 
  echo "Error: uptime has invalid number of characters!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

if [ ${#start_time} -ne $start_time_size ]; then 
  echo "Error: start_time has invalid number of characters!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

### MAIN BODY

# Connect to NTP server for sync
/etc/init.d/ntp stop
sleep 2
ntpdate 0.de.pool.ntp.org 1.de.pool.ntp.org 2.de.pool.ntp.org 3.de.pool.ntp.org
/etc/init.d/ntp start
sleep 10

# Schedule the date for the start
current_date=$(date +%s)

target_date=$(date -d "$start_time" +%s)

sleep_seconds=$(( $target_date - $current_date ))

echo "$sleep_seconds"

# Sleep before the start date
sleep $sleep_seconds

echo "We start measuring at: $(date)" 

# Start the RuuviTag capture
sudo -u pi python3 $ruuvi_capture ${macs} ${uptime} /home/pi

# Create a control file -> no measurement upon the reboot (see crontab)
touch /boot/1stexp.txt

sleep 5

# Power off the Pi
shutdown -P now