function [afpFilterBank] = preComputeFilterAFP()
%PRECOMPUTEFILTERAFP Summary of this function goes here
%   Detailed explanation goes here

% Basic sampling frequency with which we are working
Fs = 16000;

% Number of frequency bands to uniformly split frequency spectrum of a
% singal (in our case Fs = 16kHz, maxFreq = 8 kHz -> 32 bands, also close to 
% parameters by Schuermann and Sigg, they had 33 bands)
nFreqBands = 32;

% Filter order
filterOrder = 20;

% Construct a vector of frequency bands: from 0 to 8 kHz, step 250 Hz
freqStep = (Fs/2)/nFreqBands;
freqVect = [];

j = 1;
for i=0:freqStep:(Fs/2)
    freqVect(j) = i;
    j = j + 1;
end

% Initialize a cell to store filters
afpFilterBank = cell(nFreqBands, 1);

% Construct BP-filters to split 8kHz audio signal into 32 uniform freq bands:
% 1-250Hz, 251-500Hz, ... 7751-7999Hz
dec = 0;
for i=1:nFreqBands
   
    % Having 'HalfPowerFrequency2' == Fs/2 == 8 kHz may result in weird 
    % effects, so subtract one for such frequency 
    if i == nFreqBands
        dec = 1;
    end
  
    % Design a bandpass filter
    bpFilter = designfilt('bandpassiir', 'FilterOrder', filterOrder, ...
    'HalfPowerFrequency1', freqVect(i)+1, 'HalfPowerFrequency2', freqVect(i+1)-dec, ...
    'SampleRate', Fs);

    % Save a filter to the cell
    afpFilterBank{i} = bpFilter;
end

end

