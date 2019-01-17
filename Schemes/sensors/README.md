# Implementation of sensor features

This folder contains implementation of sensor features for the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

The following sensor features from the three zero-interaction schemes are implemented:

* *Luminosity Fingerprint for Miettinen et al.* [1]
* *Feature computation for Truong et al.* [2]
* *Feature computation for Shrestha et al.* [3]

[1] - Miettinen, Markus, et al. "Context-based zero-interaction pairing and key evolution for advanced personal devices." Proceedings of the 2014 ACM SIGSAC conference on computer and communications security. ACM, 2014.

[2] - Truong, Hien Thi Thu, et al. "Comparing and fusing different sensor modalities for relay attack resistance in zero-interaction authentication." Pervasive Computing and Communications (PerCom), 2014 IEEE International Conference on. IEEE, 2014.

[3] - Shrestha, Babins et al. "Drone to the Rescue: Relay-Resilient Authentication using Ambient Multi-sensing." Financial Cryptography and Data Security. pp. 349–364 (2014).

## Getting Started

To compute sensor features, the following functions/components are used (a brief description is provided, see comments inside *.py* files for details):

* *ble_wifi_truong.py* contains feature computations for the paper by Truong et al.
* *lux_miettinen.py* contains luminosity fingerprints for the paper by Miettien et al. The audio-based fingerprints are computed using Matlab scripts in a separate folder.
* *temp_hum_press_shrestha.py* contains feature computations for the paper by Shrestha et al.
* *util.py* is never called directly and contains common logic between the scripts.

The [results](https://dx.doi.org/10.5281/zenodo.2537721) were generated under *Ubuntu 16.04.4 LTS (kernel 4.4.0-128-generic x86_64)* using Python 3 (the exact version can be found in the results metadata of each generated JSON file) with the libraries as listed in requirements.txt

The scripts expect the data to be in a specific folder structure relative to the script:

```
Sensor-XX/              # where XX is the sensor number. The scripts support arbitrary numbers of sensors.
  + sensors/
  | + luxData.clean     # luminosity data with outliers removed
  | + tmpData           # Temperature data
  | + humData           # Humidity data
  | + barData           # Barometric data
  + ble/
  | + ble.txt.blinded   # BLE Data with blinded MAC addresses
  + wifi/
    + wifi.txt.blinded  # WiFi data with blinded MAC addresses
```

The output is saved in a "results" folder. See the individual files for more details.


## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) for details
