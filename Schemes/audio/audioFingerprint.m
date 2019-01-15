function [afpS1, afpS2, resForLog] = audioFingerprint(S1, S2, sampleDiff, afpFilterBank)
% AUDIO_FINGERPRINT Implementation of the scheme by Schuermann, Dominik, 
% and Stephan Sigg. "Secure communication based on ambient audio." 
% IEEE Transactions on mobile computing 12.2 (2013): 358-370.

%   Input args:
%   - S1 - First audio signal (Nx1 vector)
%   - S2 - Second audio signal (Nx1 vector)
%   - sampleDiff - Delay between two signals in samples (integer)
%   - afpFilterBank - Filter bank (cell of size 32x1, each cell contains
% a digitalFilter object)

%   Output args:
%   - afpS1 - S1 binary fingerprint ((nFrames-1)*(nFreqBands-1)x1 vector)
%   - afpS2 - S2 binary fingerprint ((nFrames-1)*(nFreqBands-1)x1 vector)
%   - resForLog - Metadata for fingerprint generation, 
% including energy levels (struct)

% Basic sampling frequency with which we are working
Fs = 16000;

% Number of frames. This param affects the length of the audio fingerprint
% in bits: (nFrames-1)*(nFreqBands-1), currently = 496 bits. Since we cannot 
% change the nFreqBands -> already max given our Fs = 16 kHz, we can only 
% adjust nFrames. This param is exactly the same as in Schuermann and Sigg. 
% nFrames defines the length of a single frame, in our case it is dynamic,
% e.g., bound to the signal length. The min signal length in our evaluation
% is 5 sec -> length of one frame d = 5/17 ~0.294 sec = 4705(d*16 kHz) 
% samples, for other intervals e.g., 1 min d equals 60/17 ~3.5 sec, etc.
% In Schuermann and Sigg d = 0.375 sec = 16317 samples(d*44.1 kHz) and
% is fixed, which corresponds to ~ 1 sec of audio for our Fs: 0,375*44.1 kHz 
% ~ 1*16 kHz. 
 nFrames = 17; 

% Number of frequency bands to uniformly split frequency spectrum of a
% singal (in our case Fs = 16kHz, maxFreq = 8 kHz -> 32 bands, close to 
% parameters by Schuermann and Sigg, they had 33 bands)
nFreqBands = 32;

% Construct a vector of frequency bands: from 0 to 8 kHz, step 250 Hz
freqStep = (Fs/2)/nFreqBands;
freqVect = [];

j = 1;
for i=0:freqStep:(Fs/2)
    freqVect(j) = i;
    j = j + 1;
end

% Align two signals based on the computed with xcorr delay (sampleDiff)
[S1, S2] = alignTwoSignals(S1, S2, sampleDiff);

% Frame length (note len(S1) == len(S2))
frameLen = round(length(S1)/nFrames);

% fprintf('One frame has a duriation of ~ %.3f sec\n', round((frameLen/Fs), 3));

% Energy cells of S1 and S2
energyS1 = cell(nFrames, 1);
energyS2 = cell(nFrames, 1);

% Split audio signals into nFrames and compute energy in each frequency 
% band for each frame
for i=1:nFrames
    
    % Split into nFrames
    if i == nFrames
        % The last split signal -> take the reminder of initial signal
        frameS1 = S1((i-1)*frameLen+1:length(S1));
        frameS2 = S2((i-1)*frameLen+1:length(S2));   
     else
         % Regular split
         frameS1 = S1((i-1)*frameLen+1:frameLen*i);
         frameS2 = S2((i-1)*frameLen+1:frameLen*i);
    end
    
    % Energy of a single frame for S1 and S2
    frameEnergyS1 = zeros(1, nFreqBands);
    frameEnergyS2 = zeros(1, nFreqBands);
    
    % Compute energy in each frequency band for each frame
    for j=1:nFreqBands % length(afpFilterBank) == nFreqBands
    
        % Filter frames of S1 and S2
        filtFrameS1 = filter(afpFilterBank{j}, frameS1);
        filtFrameS2 = filter(afpFilterBank{j}, frameS2);
        
        % Compute energy of each filtered frame for S1 and S2
        frameEnergyS1(j) = filtFrameS1' * filtFrameS1;
        frameEnergyS2(j) = filtFrameS2' * filtFrameS2;
        
%         fprintf('frame%d_%d: lowFreq = %d, highFreq = %d, energyS1 = %f, energyS2 = %f\n', i, j, freqVect(j)+1, freqVect(j+1)-dec, frameEnergyS1(j), frameEnergyS2(j));
    end
    
    energyS1{i} = frameEnergyS1;
    energyS2{i} = frameEnergyS2;
    
%     fprintf('\n');
end

% Audio fingerprints
afpSize = (nFrames-1)*(nFreqBands-1);
afpS1 = zeros(1, afpSize);
afpS2 = zeros(1, afpSize);

% Obtain audio fingerprints
k = 1;
for i=1:nFrames-1 % -1 because we compute between consecutive elements 
   for j=1:nFreqBands-1 % -1 because we compute between consecutive elements
       
       %fprintf('i = %d, j = %d, (%f - %f) - (%f - %f)\n', i, j, energyS1{i+1}(j), energyS1{i+1}(j+1), energyS1{i}(j), energyS1{i}(j+1));
       
       % Check the energies for S1, formula (5) from Schuermann and Sigg
       if ((energyS1{i+1}(j)-energyS1{i+1}(j+1))-(energyS1{i}(j)-energyS1{i}(j+1)) > 0)
           afpS1(k) = 1;
       else
           afpS1(k) = 0;
       end
       
       % Check the energies for S2, formula (5) from Schuermann and Sigg
       if ((energyS2{i+1}(j)-energyS2{i+1}(j+1))-(energyS2{i}(j)-energyS2{i}(j+1)) > 0)
            afpS2(k) = 1;
       else
            afpS2(k) = 0;
       end
       
       % Index in afpSx arrays
       k = k + 1; 
       
   end
end

% Constuct results for log struct

% Fields
f1 = 'nFrames';
f2 = 'nFreqBands';
f3 = 'frameLen';
f4 = 'freqVect';
f5 = 'energyS1';
f6 = 'energyS2';

% Values
v1 = nFrames;
v2 = nFreqBands;
v3 = round((frameLen/Fs), 3);
v4 = freqVect;
v5 = cell2mat(energyS1); % convert from cell to array for storing in the struct
v6 = cell2mat(energyS2); % convert from cell to array for storing in the struct

resForLog = struct(f1, v1, f2, v2, f3, v3, f4, v4, f5, v5, f6, v6);

end