function [packedEnergy] = packFingerprintEnergy(signalEnergy, freqVect)
% PACKFINGERPRINTENERGY Reformat audio fingerprint metadata (frames energy)
% for more convenient storage

%   Input args:
%   - signalEnergy - Frame energies in different frequency bands (struct)
%   - freqVect - Frequency bands (struct)

%   Output args: 
%   - packedEnergy - Frames energy of corresponding frequency bands (struct)

% Restore energy to cell
signalEnergy = num2cell(signalEnergy, 2);

% Output struct array
packedEnergy = struct;

% should be 17 -> see audioFingerprint. m
nFrames = length(signalEnergy); 
% should be 32 -> see audioFingerprint. m
nFreqBands = length(signalEnergy{1}); 

% Iterate over all frames
for i=1:nFrames
    
    % Initalize params for a hashmap: "<freq_band>:" "<energy_value>"
    keySet = cell(1, nFreqBands);
    valueSet = zeros(1, nFreqBands);
    
    dec = 0;
    % Iterate over all frequency bands
    for j=1:nFreqBands
        
        % For the last band we have 7999 Hz instead of 8000 Hz, see
        % audioFingerprint. m for details
        if j == nFreqBands
            dec = 1;
        end
        
        % Construct keys for a hashmap
        % 01, 02, ... vs. 10, 11
        if j < 10
            keySet{j} = strcat('0', num2str(j), '_', num2str(freqVect(j)+1), '-', num2str(freqVect(j+1)-dec));
        else    
            keySet{j} = strcat(num2str(j), '_',  num2str(freqVect(j)+1), '-', num2str(freqVect(j+1)-dec));
        end
        
        % Add values to hashmap
        valueSet(j) = signalEnergy{i}(j);
        
%         fprintf('%s: %d\n', keySet{j}, valueSet(j));
       
    end
    
    % Constuct a packedEnergy field
    structField = '';
    
    % 01, 02, ... vs. 10, 11
    if i < 10
        structField = strcat('frame_', '0', num2str(i));
    else
        structField = strcat('frame_', num2str(i));
    end
    
    % Add an element to our struct array: e.g. 'frame01' = <hashmap>
    packedEnergy.(structField) = containers.Map(keySet, valueSet);
    
end