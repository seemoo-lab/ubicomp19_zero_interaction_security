function [maxXCorr, xcorrFreqBands] = soundProofXcorr(S1, S2, sampleDiff, Fs, spfFilterBank)
% %SOUNDPROOFXCORR Implementaition of the Sound-Proof correlation engine

% Frequency bands to be splitted into -> 20 bands: 50-4000Hz as in the SPF
% paper
Fb = [50 63 80 100 125 160 200 250 315 400, ...
    500 630 800 1000 1250 1600 2000 2500 3150 4000];

% Align two signals based on the computed with xcorr delay (sampleDiff)
[S1, S2] = alignTwoSignals(S1, S2, sampleDiff);

% Splitting into 1/3 Octave Bands without Audio Toolbox
freqBankS1 = thirdOctaveSplitter(S1, spfFilterBank);
freqBankS2 = thirdOctaveSplitter(S2, spfFilterBank);

% Max lag param, we have 1 sec as compared to 150 ms from the SPF paper,
% because we do not have tight sync between devices
maxLag = round(1*Fs);

% Hashmap: "<freq_band>:<max_xcorr>" for all freq bands
keySet = cell(1, length(Fb));
valueSet = zeros(1, length(Fb));

% Accumulate xcorr values from different freq bands
maxXCorr = 0;

% Compute correlation in each 1/3 Octave Band
for i = 1:length(Fb)
    
    % Compute max xcorr between two freq banks
    bankXcorr = max(abs(xcorr(freqBankS1(i,:), freqBankS2(i,:), maxLag)));
    
    % Compute max acorr of freqBankS1
    acorrS1 = max(abs(xcorr(freqBankS1(i,:))));
    
    % Compute max acorr of freqBankS2
    acorrS2 = max(abs(xcorr(freqBankS2(i,:))));
    
    % Compute normalized max xcorr
    bankXcorr = bankXcorr/(sqrt(acorrS1 * acorrS2));
    
    % Construct key value for the hashmap 01_50 ... 20_4000
    % 01, 02, ... vs. 10, 11
    if i < 10
        keySet{i} = strcat('0', num2str(i), '_', num2str(Fb(i)));
    else    
        keySet{i} = strcat(num2str(i), '_', num2str(Fb(i)));
    end
    
    % Add the bank max xcorr value to the valueSet
    valueSet(i) = bankXcorr;
  
    % Accumulate max xcorr
    maxXCorr = maxXCorr + bankXcorr;
    
end

% Construct a hashmap
xcorrFreqBands = containers.Map(keySet, valueSet);

% Get the average maxXCorr
maxXCorr = maxXCorr/length(Fb);

end


