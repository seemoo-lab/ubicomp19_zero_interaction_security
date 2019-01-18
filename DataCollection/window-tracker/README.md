# Post-processing scripts

This folder contains a script that was used to track the doors and windows of the three offices in the Office experiment.

## Getting Started

* *reed.py* - a script to get readings from a reed sensor attached to the GPIO pins of a Raspberry Pi.

Attach the one wire of a reed switch to pin 23 and a second reed switch to pin 25 of a Raspberry Pi 2 B+ and start the script (the other wire of each reed switch should be connected to a GND pin). The script will check the state of the reed switch once per second and write a log entry to `results.csv` if the state of the switch changed.

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) file for details