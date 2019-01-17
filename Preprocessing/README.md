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

The script takes the flat structure in which sensor data is extracted from the Gear S3 smartwatch and reformats the data into the structure required for further evaluation:



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









**Note:** The script won't directly work under Windows as it uses Linux built-in commands (see function *merge_and_clean*). The rest of functionality works under Windows as well (tested under *Windows 10 x64* with *Python 3.6.5*). 

The script is used as follows:

```bash
# Car scenario
$ python3 generate_datasets.py ~/data/car/ ~/sets/ truong car full 30    # generate dataset for the full car scenario using 30 cores (scheme by Truong et al.)
$ python3 generate_datasets.py ~/data/car/ ~/sets/ truong car city 10    # generate dataset for the city car subscenario using 10 cores (scheme by Truong et al.)
$ python3 generate_datasets.py ~/data/car/ ~/sets/ shrestha car full 30  # generate dataset for the full car scenario using 30 cores (scheme by Shrestha et al.)
$ python3 generate_datasets.py ~/data/car/ ~/sets/ shrestha car city 10  # generate dataset for the city car subscenario using 10 cores (scheme by Shrestha et al.)
# highway and parked subscenarios are launched similarly

# Office scenario
$ python3 generate_datasets.py ~/data/office/ ~/sets/ truong office full 35       # generate dataset for the full office scenario using 35 cores (scheme by Truong et al.)
$ python3 generate_datasets.py ~/data/office/ ~/sets/ truong office weekday 20    # generate dataset for the weekday office subscenario using 20 cores (scheme by Truong et al.)
$ python3 generate_datasets.py ~/data/office/ ~/sets/ shrestha office full 35     # generate dataset for the full office scenario using 35 cores (scheme by Shrestha et al.)
$ python3 generate_datasets.py ~/data/office/ ~/sets/ shrestha office weekday 20  # generate dataset for the weekday office subscenario using 20 cores (scheme by Shrestha et al.)
# night and weekend subscenarios are launched similarly

# Mobile Scenario
$ python3 generate_datasets.py ~/data/mobile/ ~/sets/ truong mobile full 15    # generate dataset for the full mobile scenario using 15 cores (scheme by Truong et al.)
$ python3 generate_datasets.py ~/data/mobile/ ~/sets/ shrestha mobile full 25  # generate dataset for the full mobile scenario using 25 cores (scheme by Shrestha et al.)
```

Here, ~/data is the folder the post-processed data from car, office or mobile scenario is stored, and ~/sets is the folder to store the generated ML datasets.

**Note:** By default Truong et al. datasets are generated using a 10sec interval, to generate datasets on a 30sec interval discussed in the paper, set *time_interval = '30sec'* in *get_truong_dataset* function. Other intervals (5sec, 15sec, 1min, 2min) have not been tested, so the correctness of dataset generation on these intervals is not guaranteed! 


* ml_to_json.py - **TBD (split requirements for different .py files?)**

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) file for details
