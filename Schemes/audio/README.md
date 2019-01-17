# Implementation of audio features

This folder contains implementation of audio features for the paper "Perils of Zero-Interaction Security in the Internet of Things", by Mikhail Fomichev, Max Maass, Lars Almon, Alejandro Molina, Matthias Hollick, in Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies, vol. 3, Issue 1, 2019. 

The following audio features from the four zero-interaction schemes are implemented:

* *Audio fingerprint (AFP)* [1]
* *Time-frequency distance (TFD)* [2]
* *Noise fingerprint (NFP)* [3]
* *SoundProof (SPF)*  [4]

[1] - Schürmann, Dominik, and Stephan Sigg. "Secure communication based on ambient audio." IEEE Transactions on mobile computing 12.2 (2013): 358-370.

[2] - Truong, Hien Thi Thu, et al. "Comparing and fusing different sensor modalities for relay attack resistance in zero-interaction authentication." Pervasive Computing and Communications (PerCom), 2014 IEEE International Conference on. IEEE, 2014.

[3] - Miettinen, Markus, et al. "Context-based zero-interaction pairing and key evolution for advanced personal devices." Proceedings of the 2014 ACM SIGSAC conference on computer and communications security. ACM, 2014.

[4] - Karapanos, Nikolaos, et al. "Sound-Proof: Usable Two-Factor Authentication Based on Ambient Sound. "USENIX Security Symposium. 2015.

## Getting Started

To compute audio features, the following functions are used (brief description is provided, see comments inside *.m* files for details):

~~* *plot_error_rates.py* - a script to generate false reject rates (FRRs) with target false accept rates (FARs) plots.~~

The [results of audio feature computations](https://www.seemoo.tu-darmstadt.de/) were generated under *CentOS Linux release 7.5.1804 (kernel 3.10.0-862.9.1.el7.x86_64)* using *MATLAB R2017a (9.2.0.556344) 64-bit (glnxa64)* with the following requirements:

```
Signal Processing Toolbox (Version 7.4)
Parallel Computing Toolbox (Version 6.10)
```
**Note:** These toolboxes are not part of standard MATLAB distribution and need to be acquired separately. In a standard setup, each instance of MATLAB (i.e., launching *audioJob.m*) requires a license!


The script is used as follows:

```bash
$ mcc -R -nodisplay -T link:exe -v -m audioJob.m -a Add-Ons/Functions/DataHash/code/ -a Add-Ons/Collections/Natural-Order/Filename/Sort/code/

$ sudo ./run_audioJob.sh .../matlab/ .../CarExp/Sensor-01/audio/01.flac .../CarExp/Sensor-02/audio/02.flac .../CarExp .../tmp-for-matlab-parallel-toolbox .../local-storage

```

Here, ~/json is the folder contaning [JSON files with error rates](https://www.seemoo.tu-darmstadt.de/), and ~/gfx is the folder to store the generated plots.


## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) for details
