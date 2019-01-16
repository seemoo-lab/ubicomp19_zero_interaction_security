#!/bin/bash

### Watchdog to keep nodejs capture (collectes sensor data from SensorTag) running

# Add paths
PATH=$PATH:/bin:/usr/bin:/sbin:/usr/sbin

# Sleep for 2 minutes (make sure NTP sync happened in main.sh)
sleep 120

# Paths
main_conf="/home/pi/conf/main_conf.txt"
check_script="/home/pi/scripts/check_nodejs.sh"

# Counters, min/max sizes
conf_size=4
mac_size=12
min_uptime_size=2
start_time_size=16
key_id_size=10
sleep_time=120 # Sleep for 2 minutes 

# Config params
tag_address=""
uptime=""
start_time=""
key_id=""

### MAIN BODY

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

# Get tag_address, uptime (in s-sec, m-min, h-hours) and start_time (format: MM/DD/YYYY HH:MM)
for i in "${!conf_arr[@]}"
do 
  case "$i" in
  "0")
    tag_address=${conf_arr[$i]}
    ;;
  "1")
    uptime=${conf_arr[$i]}
    ;;
  "2")
    start_time=${conf_arr[$i]}
    ;;
  "3")
    key_id=${conf_arr[$i]}
    ;;
  esac
done

# Remove leading and trailing spaces (for the next check)
tag_address="$(echo -e "${tag_address}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
uptime="$(echo -e "${uptime}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
start_time="$(echo -e "${start_time}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
# This parameter is only relevant if GPG is used (e.g., for audio data encryption) 
key_id="$(echo -e "${key_id}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

# Final config checks, sigh!
if [ ${#tag_address} -ne $mac_size ]; then 
  echo "Error: tag_address has invalid number of characters!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

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

# This check is only relevant if GPG is used (e.g., for audio data encryption) 
if [ ${#key_id} -ne $key_id_size ]; then 
  echo "Error: key_id has invalid number of characters!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

# Schedule the date for the start
current_date=$(date +%s)

target_date=$(date -d "$start_time" +%s)

# Sleep simlar to main.sh, plus 10 extra minutes for measurements
sleep_seconds=$(( $target_date - $current_date ))

if [ $sleep_seconds -lt 0 ]; then
  sleep_seconds=$sleep_time
else
  sleep_seconds=$(($target_date - $current_date + $sleep_time))
fi

# Sleep before the start date
sleep $sleep_seconds

echo "Starting watchdog"

# Launch check_nodejs.sh to continously monitor if nodejs process is running and restart it if necessary
timeout "${uptime}" bash $check_script $tag_address $uptime
