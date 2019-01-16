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
```
CAR SCENARIO:

*python3 generate_datasets.py ~/data/car/ ~/sets/ truong car full 30* - generate dataset for the full car scenario using 30 cores (scheme by Truong et al.)
*python3 generate_datasets.py ~/data/car/ ~/sets/ truong car city 10* - generate dataset for the city car subscenario using 10 cores (scheme by Truong et al.)

*python3 generate_datasets.py ~/data/car/ ~/sets/ shrestha car full 30* - generate dataset for the full car scenario using 30 cores (scheme by Shrestha et al.)
*python3 generate_datasets.py ~/data/car/ ~/sets/ shrestha car city 10* - generate dataset for the city car subscenario using 10 cores (scheme by Shrestha et al.)

*highway* and *parked* subscenarios are launched similarly


OFFICE SCENARIO:

*python3 generate_datasets.py ~/data/office/ ~/sets/ truong office full 35* - generate dataset for the full office scenario using 35 cores (scheme by Truong et al.)
*python3 generate_datasets.py ~/data/office/ ~/sets/ truong office weekday 20* - generate dataset for the weekday office subscenario using 20 cores (scheme by Truong et al.)

*python3 generate_datasets.py ~/data/office/ ~/sets/ shrestha office full 35* - generate dataset for the full office scenario using 35 cores (scheme by Shrestha et al.)
*python3 generate_datasets.py ~/data/office/ ~/sets/ shrestha office weekday 20* - generate dataset for the weekday office subscenario using 20 cores (scheme by Shrestha et al.)

*night* and *weekend* subscenarios are launched similarly


MOBILE SCENARIO:

*python3 generate_datasets.py ~/data/mobile/ ~/sets/ truong mobile full 15* - generate dataset for the full mobile scenario using 15 cores (scheme by Truong et al.)

*python3 generate_datasets.py ~/data/mobile/ ~/sets/ shrestha mobile full 25* - generate dataset for the full mobile scenario using 25 cores (scheme by Shrestha et al.)


~/data - folder to store postprocessed data from car, office or mobile scenario 
~/sets - folder to store the generated ML datasets

```
**Note:** By default Truong et al. datasets are generated using a 10sec interval, to generate datasets on a 30sec interval discussed in the paper, set *time_interval = '30sec'* in *get_truong_dataset* function. Other intervals (5sec, 15sec, 1min, 2min) have not been tested, so the correctness of dataset generation on these intervals is not guaranteed! 


### Prerequisites

* *generate_datasets.py* - a script to generate ML datasets for the schemes by Truong et al. (PerCom'14) and Shrestha et al. (FC'14).

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc