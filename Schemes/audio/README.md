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
* *saveJsonFile.m* - store the results of audio feature computations in a JSON file. 
* *saveNoiseLevels.m* - generate a JSON file containing noise levels of two input audio signals (metadata for the NFP feature).
* *soundProofXcorr.m* - implementation of the SPF feature. 
* *thirdOctaveSplitter.m* - split an audio signal into 1/3 octave bands using the *spfFilterBank.mat* filter bank. 
* *timeFreqDistance.m* - implementation of the TFD feature. 
* *xcorrDelay.m* - compute a delay between two discrete (audio) signals using MATLAB's *xcorr* function. 
* *afpFilterBank.mat* - a filter bank necessary for computing the AFP feature (regenerated if is not present in the folder).  
* *spfFilterBank.mat* - a filter bank necessary for computing the SPF feature (regenerated if is not present in the folder).  
* *~/Add-Ons* - a folder containing third party utilities used by our code (the licenses are compatible with the GNU GPLv3, see individual folders inside Add-Ons for details). 

The results of audio feature computations (e.g., see the [Car](https://dx.doi.org/10.5281/zenodo.2537705) scenario, other scenarios maintain the same structure) were generated under *CentOS Linux release 7.5.1804 (kernel 3.10.0-862.9.1.el7.x86_64)* using *MATLAB R2017a (9.2.0.556344) 64-bit (glnxa64)* with the following requirements:

```
Signal Processing Toolbox (Version 7.4)
Parallel Computing Toolbox (Version 6.10)
```
**Note:** These toolboxes are not part of standard MATLAB distribution and need to be acquired separately. In a standard setup, each instance of MATLAB (i.e., launching *audioJob.m*) requires a license!


The audio feature computation is launched (from a MATLAB command line) as follows:

```bash
# The audio feature computation between sensors 05 and 06 in the mobile scenario
>> audioJob(.../MobileExp/Sensor-05/audio/05.flac, .../MobileExp/Sensor-06/audio/06.flac, .../MobileExp/, .../tmp-for-matlab-parallel-toolbox/, .../local-storage/)
```
Here, the first two arguments are full paths to audio files of sensors 05 and 06 respectively, *.../MobileExp/* is the folder storing audio files from all sensors (i.e., */Sensor-02* to */Sensor-25* in the mobile scenario), *.../tmp-for-matlab-parallel-toolbox/* is a temporary folder used by MATLAB's Parallel Computing Toolbox, *.../local-storage/* is the local storage (also a temporary folder) useful when the cluster architecture is used for audio feature computations (see the Notes below). 

**Notes:** 

* The *Add-Ons* folder must be added to the MATLAB path as audio feature computation requires third party utilities!
* All the arguments are mandatory in the *audioJob.m*!
* The results of the audio feature computations are stored in the individual folders inside the *.../Sensor-XX/audio/* folder (e.g., see the [Car](https://dx.doi.org/10.5281/zenodo.2537705) scenario, other scenarios maintain the same structure).
* The rationale for *.../local-storage/*: in our computations we used a cluster. Therefore, we stored *.../MobileExp/* (and similar folders for the car and office experiments) on the shared network drive, which was accessible by a number of nodes (each running an instance of *audioJob.m*). Each node had limited HDD storage not suitable for storing all the audio files (especially in the case of the Office scenario). Additionally, we compute audio features on a number of intervals (5sec, 10sec, 30sec, 1min, 2min), resulting in many small result JSON files (e.g., think of a 24h audio recording split into 5sec intervals). With several nodes simultaneously using the network share and writing thousands of small files results in fragmentation issues and easily hits the max number of files limited by the files system. Thus, we leveraged the local storage on each node to store these small files for each interval, merge them into a single JSON file and copy back to the network share (e.g., *.../MobileExp/Sensor-05/audio/* in the above example). 

### The audio feature computation using the MATLAB's compiled executable

From the above info, it is easily seen that if many instances of MATLAB are used (we used up to 45 instances simultaneously), it is very easy to run into the licensing issue with the required toolboxes. To overcome this issue we used a MATLAB Compiler (Version 6.4, R2017a)—this toolbox needs to be acquired separately as well. The compiler allows building a MATLAB executable and running it on any other machine without requiring any license! The MATLAB's executable is built and run as follows (tested under *CentOS Linux release 7.5.1804 (kernel 3.10.0-862.9.1.el7.x86_64)* and *Ubuntu 17.10 (kernel 4.13.0-46, x86_64)*): 

```bash
# Run this in the folder containing all the *.m files and Add-Ons folder
# Two files are generated: a binary "audioJob" and the script "run_audioJob.sh" to run it
$ mcc -R -nodisplay -T link:exe -v -m audioJob.m -a Add-Ons/Functions/DataHash/code/ -a Add-Ons/Collections/Natural-Order\ Filename\ Sort/code/

# The audio feature computation between sensors 05 and 06 in the mobile scenario
$ sudo ./run_audioJob.sh .../matlab/ .../MobileExp/Sensor-05/audio/05.flac .../MobileExp/Sensor-06/audio/06.flac .../MobileExp/ .../tmp-for-matlab-parallel-toolbox/ .../local-storage/
```
Here, *.../matlab/* points to the instance of MATLAB installed on the machine (e.g., full installation on Ubuntu is */usr/local/MATLAB/R2017a*, runtime environment installation on Ubuntu is */usr/local/MATLAB/MATLAB_Runtime/v92*), the remaining arguments are the same as described above. 

## Authors

Mikhail Fomichev and Max Maass


## License

The code is licensed under the GNU GPLv3 - see [LICENSE.txt](https://dev.seemoo.tu-darmstadt.de/zia/evaluation-public/blob/master/LICENSE.txt) for details
