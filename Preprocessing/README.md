# Preprocessing scripts

This folder contains scripts to preprocess the raw sensor data for further evalutation in the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

## Getting Started

* *blind_radio.py* - **TBD**

* *lux_outlier_removal.py* - **TBD**

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
