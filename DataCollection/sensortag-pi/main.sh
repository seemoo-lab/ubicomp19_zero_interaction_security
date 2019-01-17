#!/bin/bash

### Main script to start, maintain and stop the capture of sensor data (SensorTag), audio, as well as WiFi and BLE scans

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
nodejs_counter=0
max_attempts=2
conf_size=4
mac_size=12
min_uptime_size=2
start_time_size=16
key_id_size=10

# Config params
tag_address=""
uptime=""
start_time=""
key_id=""

# Paths: setting
device="/dev/ttyACM0"
nodejs_dir="/home/pi/nodejs"
conf_dir="/home/pi/conf"
scripts_dir="/home/pi/scripts"
ble_script="/home/pi/scripts/ble_capture.py"
wifi_script="/home/pi/scripts/wifi_capture.py"
main_conf="/home/pi/conf/main_conf.txt"
nodejs_conf="/home/pi/conf/nodejs_conf.txt"

# Paths: data
audio_data="/home/pi/data/audio/audio"
ble_data="/home/pi/data/ble/ble.txt"
wifi_data="/home/pi/data/wifi/wifi.txt"
sensor_data="/home/pi/data/sensors"

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

if [ ! -f /home/pi/conf/hostname ]; then
  echo "Notice: no hostname file found, not setting hostname"
else
  hostname $(cat /home/pi/conf/hostname)
  echo "Changed hostname to" $(cat /home/pi/conf/hostname)
fi

### MAIN BODY

# Remove old readings if exist: THIS IS A DESTRUCTIVE BEHAVIOR, ADJUST TO APPEND BEHAVIOR IF NECESSARY!
rm -r $audio_data > /dev/null 2>&1
rm -r $ble_data > /dev/null 2>&1
rm -r $wifi_data > /dev/null 2>&1
rm -r $sensor_data/* > /dev/null 2>&1

# Connect to NTP server for sync
/etc/init.d/ntp stop
sleep 2
ntpdate 0.de.pool.ntp.org 1.de.pool.ntp.org 2.de.pool.ntp.org 3.de.pool.ntp.org
/etc/init.d/ntp start
sleep 2

### GPG part is currently commented out

# Import a GPG key
# gpg --import /home/pi/$key_id.asc

# Test that GPG imported correctly
# echo test > /tmp/testenc
# gpg -r $key_id --trust-model always -e /tmp/testenc
# if [ $? -ne 0 ]; then
#   echo "Test encryption failed, aborting."
#   shutdown -P now
#   exit 1
# fi
# rm /tmp/testenc /tmp/testenc.gpg

# Schedule the date for the start
current_date=$(date +%s)

target_date=$(date -d "$start_time" +%s)

sleep_seconds=$(( $target_date - $current_date ))

# Sleep before the start date
echo "$sleep_seconds"
sleep $sleep_seconds

echo "We start measuring at: $(date)" 

# Check if SensorTag is detected
if [ -c "$device" ]; then 
  echo "SensorTag is attached"
  # Confiure the serial port to receive audio data 
  stty -F /dev/ttyACM0 115200 raw -clocal -echo
else
  echo "Error: could not detect SensorTag!"
  touch /boot/1stexp.txt
  shutdown -P now
  exit 1
fi

# Change to nodejs_dir
cd "$nodejs_dir"

# Start nodejs: connect to SensorTag (3 attempts to start)
while [ $nodejs_counter -lt $max_attempts ]
do
  node main.js "$tag_address" "${uptime}" & 
  nodejs_pid=$!
  
  sleep 15
  
  if ps -p $nodejs_pid > /dev/null
  then
    echo "process is still runnig, good!"
    break
  else
    echo "the process ended, we will retry..."
    #sleep 5
	
	# Make sure the BT stack is ok (stop the service, reset the interface, start the service)
	systemctl stop bluetooth
	sleep 3
	hciconfig hci0 reset
	sleep 3
	systemctl start bluetooth
	sleep 3

    nodejs_counter=$((nodejs_counter + 1))
  fi
  
done

nodejs_flag=0
# Check if we need to reboot, because of nodejs bug
while IFS='' read -r param || [[ -n "$param" ]]; do
  nodejs_flag=$(($param))
done < "$nodejs_conf"

# Check the nodejs_counter
if [ $nodejs_counter -eq $max_attempts ]; then
  if [ $nodejs_flag -ne 1 ]; then
    echo "1" > "$nodejs_conf"
    echo "Error:could not start nodejs! Rebooting..."   
    reboot
  else 
    echo "0" > "$nodejs_conf"
    echo "Error:could not start nodejs! Shutting down..."
    shutdown -P now
	exit 1
  fi
fi

# Change to /home/pi
cd ".."

# Sleep here so that audio, Wi-Fi and BLE captures will stop ~sychronously with nodejs 
sleep 7

# Log the start of audio
echo "Start audio at: $(date +'%Y-%m-%d %H:%M:%S.%3N')"
date +'%Y-%m-%d %H:%M:%S.%3N' > $audio_data.time

# Compute the uptime in seconds provided in main_conf file
uptime_secs=$(python3 scripts/get_uptime.py $uptime)

# Start audio capture
arecord -t raw -f S16_LE -r16000 -d $uptime_secs -D sysdefault:CARD=1 | flac - -f --endian little --sign signed --channels 1 --bps 16 --sample-rate 16000 -s -c > $audio_data &

# Audio capture command if GPG is used
# arecord -t raw -f S16_LE -r16000 -d $uptime_secs -D sysdefault:CARD=1 | flac - -f --endian little --sign signed --channels 1 --bps 16 --sample-rate 16000 -s -c | gpg -e -r $key_id --trust-model always > $audio_data &

# Change to scripts_dir
cd "$scripts_dir"

# Start BLE capture
python $ble_script "${uptime}" > $ble_data &

# Start Wi-Fi capture
python $wifi_script "${uptime}" > $wifi_data

# Create a control file -> no measurement upon the reboot (see crontab)
touch /boot/1stexp.txt

sleep 5

# Power off the Pi
shutdown -P now