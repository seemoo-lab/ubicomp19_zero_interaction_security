# Postprocessing scripts

This folder contains scripts to generate intermediate results for the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

## Getting Started

* *generate_datasets.py* - a script to generate machine learning datasets for the schemes by Truong et al. (PerCom'14) and Shrestha et al. (FC'14).

The [resulting datasets](https://www.seemoo.tu-darmstadt.de/) were generated with the script under *Ubuntu 16.04.5 LTS (kernel 4.4.0-139, x86_64)* using *Python 3.5.2* with the following requirements:

```
glob2==0.6
numpy==1.15.2
pandas==0.23.4
python-dateutil==2.7.3
pytz==2018.5
six==1.11.0
```

**Note:** The script won't direclty work under Windows as it uses Linux built-in commands (see function *merge_and_clean*). The rest of functionlaity works under Windows as well (tested under *Windows 10* with *Python 3.6.5*). 

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

Here, ~/data is the folder the postprocessed data from car, office or mobile scenario is stored, and ~/sets is the folder to store the generated ML datasets.

**Note:** By default Truong et al. datasets are generated using a 10sec interval, to generate datasets on a 30sec interval discussed in the paper, set *time_interval = '30sec'* in *get_truong_dataset* function. Other intervals (5sec, 15sec, 1min, 2min) have not been tested, so the correctness of dataset generation on these intervals is not guaranteed! 

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) file for details
