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

To compute audio features, the following functions/components are used (a brief description is provided, see comments inside *.m* files for details):

* *audioJob.m* - **a main function** to launch audio feature computations. 
* *alignTwoSignals.m* - a function to align two discrete (audio) signals. 
* *audioFingerprint.m* - implementation of the AFP feature. 
* *binHammingDist.m* - compute a Hamming Distance between two binary vectors.
* *computeAFP.m* - a wrapper to compute the AFP feature and store the results.
* *computeNFP.m* - a wrapper to compute the NFP feature and store the results.
* *computeSPF.m* - a wrapper to compute the SPF feature and store the results.
* *computeTFD.m* - a wrapper to compute the TFD feature and store the results.
* *correctBands.m* - a helper function to format the resulting JSON files. 
* *correctDate.m* - a helper function to format the resulting JSON files. 
* *loadSignal.m* - a function to load two audio signals from audio files (e.g., *.FLAC); the samplig rate in Hz is set inside the function.  
* *localMerge.m* - a function to merge resulting JSON files from smaller audio chunks into the final result JSON file. 
* *maxCrossCorrelation.m* - compute maximum cross-correlation between two normalized descrete (audio) signals. 
* *noiseFingerprint.m* - implementation of the NFP feature. 
* *normalizeSignal.m* - energy normalization of a discrete (audio) signal. 
* *packFingerprintEnergy.m* - a helper function to store metadata for the AFP. 
* *packNoiseFingerprint.m* - a helper function to format the results of the NFP computation. 
* *preComputeFilterAFP.m* - precompute the AFP filter bank (produces the *afpFilterBank.mat* file). 
* *preComputeFilterSPF.m* - precompute the SPF filter bank (produces the *spfFilterBank.mat* file). 
* *saveJsonFile.m* - store the resluts of audio feature computations in a JSON file. 
* *saveNoiseLevels.m* - genereate a JSON file containing noise levels of two input audio signals (metadata for the NFP feature).
* *soundProofXcorr.m* - implementation of the SPF feature. 
* *thirdOctaveSplitter.m* - split an audio signal into 1/3 octave bands using the *spfFilterBank.mat* filter bank. 
* *timeFreqDistance.m* - implementation of the TFD feature. 
* *xcorrDelay.m* - compute a delay between two discrete (audio) signals using MATLAB's *xcorr* function. 
* *afpFilterBank.mat* - a filter bank necessary for computing the AFP feature (regenerated if is not present in the folder).  
* *spfFilterBank.mat* - a filter bank necessary for computing the SPF feature (regenerated if is not present in the folder).  
* *~/Add-Ons* - a folder containing third party utilites used by our code (the licenses are compatible with the GNU GPLv3, see individual folders inside Add-Ons for details). 

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
**Note:** say about what is the network share and what is the fast local storage


Here, ~/json is the folder contaning [JSON files with error rates](https://www.seemoo.tu-darmstadt.de/), and ~/gfx is the folder to store the generated plots.


## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) for details
