# Data collector comprised of Rapsberry Pi + SensorTag + USB microphone

This folder contains the codebase used for data collection (audio, sensor data, WiFi and BLE beacons) for the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

The setup consists of the following hardware:

* *Raspberry Pi 3 Model B Rev 1.2* with *Raspbian GNU/Linux 9.1 (stretch, 4.9.41-v7+)*
* *Texas Instruments SensorTag CC2650* with *Firmware Revision 1.40 (Nov 3 2017)*
* *Samson Go USB microphone*

The SensorTag and microphone are attached to Raspberry Pi via USB ports.

The data collector is used to collect the following sensor modalities:

| **Hardware**      | **Sensors**       | **Sampling rate**  | **Comments** |
| ------------- |:-------------:| -----:|:-----------------------:|
| SensorTag      | Temperature (°C), humidity (%RH), barometric pressure (hPa), luminosity (lux);  movement -> accelerometer (*G* units), gyroscope (*deg/s*), magnetometer (*uT*) | 10 Hz |         The sensor data is sent to Raspberry Pi via Bluetooth             |
| Raspberry Pi      | Bluetooth low energy (BLE) and WiFi beacons      |   0.1 Hz |  Scan visible BLE and WiFi access points (APs) for 10 seconds     |
| Samson Go | Raw audio stream (S16_LE, little endian)    |    16 kHz |     The audio is encoded into a lossles *.FLAC using *arecord (v1.1.3)*


## Getting Started

The data collector consists of the following scripts/components:

* *main.sh* - **a main script** to start, maintain and stop the data collection. 
* *~/nodejs* - a folder containing Node.js functionality to capture sensor data from the SensorTag. The main Node.js script to launch, maintain and stop data collection is *~/nodejs/main.js* (*Node.js v8.7.0* was used). We use a number of third party libraries to implement data acquisition from the SensorTag, the most important one is [node-sensortag](https://github.com/sandeepmistry/node-sensortag), located in  *~/nodejs/lib/*. The remaining third party libraries are located in *~/nodejs/node_modules/*, the versions of used Node.js libraries and their depenencies are summarized in *~/nodejs/package-lock.json*. All used third party libraries are compatable with the GNU GPLv3. 
* *~/conf* - a folder containing configuration parameters used by the *main.sh*. The most important file is *~/conf/main_conf.txt* containing 1) the MAC address of the SensorTag to be connected to, 2) the duration of the data collection, 3) the date and time to start the data collection (see comments in *~/conf/main_conf.txt* for details). 
* *~/capture_scripts* - a folder containing *.py and *.sh scripts to perform WiFi and BLE captures, as well as deal with infrequent disconnectes between the SensorTag and RaspberryPi:
    * *ble_capture.py* (requires *bluepy v1.1.2* or higher) and *wifi_capture.py* were used with *Python 2.7.13*.
    * *get_uptime.py* - a helper script to compute data collection time in seconds, was used with *Python 3.5.3*.
    * *check_nodejs.sh* and *watchdog.sh* are used to continously monitor if the Node.js process is running and restart the data collection from SensorTag (i.e., start *main.js* again) in case of a disconnect between the Rapsberry Pi and the SensorTag. 


## Deployment

* To deploy the collector on a Raspberry Pi (should also work on the most recent Raspbian) first install necessary libraries with dependencies: see the *~/nodejs* folder for the list of Node.js libraries, for *Python* only *bluepy* is required. Then copy all the content of the *~/sensortag-pi* to */home/pi* on the Raspberry Pi. 
* The SensorTag should be flashed with the default firmware (we used *ble_sdk_2_02_01_18/examples/hex/cc2650stk_sensortag_rel.hex*) using *SmartRF Flash Programmer 2* (we used *ver. 1.7.5 (build #16)*) and connected to the Raspberry Pi via USB. 
* The Samson Go should similarlly be plugged via USB.


**Notes:** 

* The data collection functionality is invoked inside *main.sh*, thus the script should be consulted to see how individual components are called. Other scripts (*main.js* + the ones in *~/capture_scripts*) are also supplied with meaningful  comments. Also, check the *main.sh* script to see which **other utilities need to be installed**, e.g., the ones used for audio recording, NTP update, etc.    
* The correctness of *~/conf/main_conf.txt* must be thoroughly checked: if the Raspberry Pi cannot find the SensorTag it will shut down and there might be issues upon the next start (see below)!
* Since we are using timestamps, the NTP synchronization is mandatory, thus make sure that the Raspberry Pi can access the Internet and use the *ntpdate* to obtain the time update. 

In our experiments we started the *main.sh* and *watchdog.sh* from crontab as follows:

```bash
# The crontab file is located at /var/spool/cron/crontabs/root
@reboot /bin/bash /home/pi/main.sh 2>&1 | tee -a /home/pi/out.txt
@reboot /bin/bash /home/pi/scripts/watchdog.sh 2>&1 | tee -a /home/pi/out.txt
```
Here, */home/pi/out.txt* is a log file to monitor the data collection process. 

**Caution:** For debugging purposes we introduced the following mechanism: if a critical problem or error occur (*touch /boot/1stexp.txt* in the *main.sh*), the Raspberry Pi will shut down, then we will manually inspect the log file (*/home/pi/out.txt*) to resolve the problem. 
In order not to start the data collection again (because it will destroy old results) we create a watchdog file (*/boot/1stexp.txt*) when a critical error occurs. If this file is created the *main.sh* will always shut down the Raspberry Pi, see the first lines in the script: 


```bash
# Check if we should shutdown
if [ -e /boot/1stexp.txt ]; then
  echo "File exists, exiting..."
  shutdown -P now
  exit 1
fi
```

The data collection runs for the duration specified in *~/conf/main_conf.txt*, after the time is up the Raspberry Pi automatically shuts down. The collected sensor data is stored in the following structure in */home/pi/*:

```
data/                   # Root folder of the sensor data
  + audio/
  | + audio.flac        # Encoded audio data
  | + audio.time        # Time when the audio started
  + ble/
  | + ble.txt           # BLE data
  + sensors/
  | + accData           # Accelerometer data
  | + barData           # Barometric data
  | + gyrData           # Gyroscope data
  | + humData           # Humidity data
  | + luxData           # Lluminosity data
  | + magData           # Magnetometer data
  | + tmpData           # Temperature data
  + wifi/
    + wifi.txt          # WiFi data
```

To make the audio file readable by applications necessary headers must be added like this:
```bash
# Install sox utility
$ sox audio.flac audio_full.flac --show-progress
```

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) for details
