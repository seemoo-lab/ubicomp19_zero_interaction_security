# Preprocessing scripts

This folder contains scripts to preprocess the raw sensor data for further evalutation in the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

## Getting Started

* *blind_radio.py* - A script to remove identifying information from the WiFi and BLE recordings

This script is placed in the base folder of the data directory (with a folder structure following the pattern "Sensor-XX/wifi/wifi.txt" and "Sensor-XX/ble/ble.txt" below it) and iterates through all BLE and WiFi files, replacing the MAC addresses with globally unique numbers to anonymize them. The results are saved to wifi.txt.blinded / ble.txt.blinded. The script does not require any parameters, and has no dependencies aside from `glob`.

* *lux_outlier_removal.py* - A script to remove outliers from the luminosity data

The luminosity sensor on the TI SensorTag has a bug that introduces incorrect readings - readings of "13.6" are interspersed between the legitimate readings. This script removes such readings if they aren't plausible (i.e., it tries to avoid removing legitimate readings with that value by checking if the previous or next reading have the same value). The script also has no parameters, and relies on `glob` to find the files (same folder structure as above). The results are saved to luxData.clean in the same folder as the source file.

* *structure-gear-data.py* - a script to restructure sensor data extracted from a Samsung Gear S3 smartwatch. 

The script was used under *Windows 10 x64* with *Python 3.6.5* and the following requirements:

```
glob2==0.6
```

The script takes the flat input structure in which sensor data is [extracted from the Gear S3 smartwatch](https://www.seemoo.tu-darmstadt.de/) and reformats the data into the output structure required for further evaluation:
```bash
# Reformats the data from the smartwatch to the required stucture and stores it in ~/MobileExp/Sensor-05/
$ python3 structure-gear-data.py ~/Others ~/MobileExp 5
```

**Input file structure:**
```
+ Others/ 
| + accData.txt
| + audio.wav
| + audio.time
| + barData.txt
| + ble.txt
| + gyrData.txt
| + luxData.txt
| + wifi.txt
```

**Output file structure:**
```
+ Sensor-XX/  # Where XX is the sensor number between 1 and 25
| + audio/
| | + XX.flac
| | + audio.time
| + ble/
| | + ble.txt
| + sensors/
| | + accData.txt
| | + barData.txt
| | + gyrData.txt
| | + luxData.txt
| + wifi/
| | + wifi.txt
```

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) file for details
