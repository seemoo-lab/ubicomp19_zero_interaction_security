function [outResult] = correctBands(inResult)
%CORRECTBANDS Summary of this function goes here
%   Detailed explanation goes here

if isfield(inResult, 'vect_energy_chunk1') % Check if the feature is AFP
    
    % Adjsut vect_energy_chunk1
    energyChunk = inResult.vect_energy_chunk1;
    
    % Cell array of frame names
    frameNames = fieldnames(energyChunk);
   
    for i=1:length(frameNames)
        
        % Get a single freq band
        freqBand = getfield(energyChunk, frameNames{i});
        
        % Cell array of freq band names
        freqBandNames = fieldnames(freqBand);
       
        % Key-value pairs for the hashmap
        keySet = cell(length(freqBandNames), 1);
        valueSet = cell(length(freqBandNames), 1);
        
        % Correct freq band names
        for j=1:length(freqBandNames)
            % Remove the first 'x' symbol
            tmp = freqBandNames{j}(2:end);
            
            % Replace the second '_' with '-'
            idx = strfind(tmp, '_');
            tmp(idx(length(idx))) = '-';
            
            % Save a new freq band name
            keySet{j} = tmp;
            
            % The energy value of the band remains intact
            valueSet{j} = getfield(freqBand, freqBandNames{j});
        end
        % Write the result back to .frame_xx struct
         energyChunk.(frameNames{i}) = containers.Map(keySet, valueSet);  
    end
    
    % Write back to vect_energy_chunk1
    inResult.vect_energy_chunk1 = energyChunk;
    
    % Adjsut vect_energy_chunk2
    energyChunk = inResult.vect_energy_chunk2;
    
    % Cell array of frame names
    frameNames = fieldnames(energyChunk);
   
    % Iterate over each frame
    for i=1:length(frameNames)
        
        % Get a single freq band
        freqBand = getfield(energyChunk, frameNames{i});
        
        % Cell array of freq band names
        freqBandNames = fieldnames(freqBand);
       
        % Key-value pairs for the hashmap
        keySet = cell(length(freqBandNames), 1);
        valueSet = cell(length(freqBandNames), 1);
        
        % Correct freq band names
        for j=1:length(freqBandNames)
            % Remove the first 'x' symbol
            tmp = freqBandNames{j}(2:end);
            
            % Replace the second '_' with '-'
            idx = strfind(tmp, '_');
            tmp(idx(length(idx))) = '-';
            
            % Save a new freq band name
            keySet{j} = tmp;
            
            % The energy value of the band remains intact
            valueSet{j} = getfield(freqBand, freqBandNames{j});
        end
        % Write the result back to .frame_xx struct
         energyChunk.(frameNames{i}) = containers.Map(keySet, valueSet);  
    end
    
    % Write back to vect_energy_chunk2
    inResult.vect_energy_chunk2 = energyChunk;
        
elseif isfield(inResult, 'xcorr_freq_bands') % Check if the feature is SPF
    
    % Adjust xcorr_freq_bands
    freqBands = inResult.xcorr_freq_bands;
    
    % Cell array of freq band names
    freqBandNames = fieldnames(freqBands);
    
    % Key-value pairs for the hashmap
    keySet = cell(length(freqBandNames), 1);
    valueSet = cell(length(freqBandNames), 1);
    
    % Correct freq band names
    for i=1:length(freqBandNames)
        % Remove the first 'x' symbol
        keySet{i} = freqBandNames{i}(2:end);
        
        % xcorr of each octave band remains intact
        valueSet{i} = getfield(freqBands, freqBandNames{i});
    end
    
    % Write the result back to .xcorr_freq_bands struct
    inResult.xcorr_freq_bands = containers.Map(keySet, valueSet);
end
  
if isfield(inResult, 'fingerprint_noise_lev1')
    
    % Adjust fingerprint_noise_lev1
    noiseBands = inResult.fingerprint_noise_lev1;
    
    % Check if we have a structure or not
    if isstruct(noiseBands) ~= 0
        
        % Cell array of noise level bits
        noiseBandNames = fieldnames(noiseBands);
    
        % Key-value pairs for the hashmap
        keySet = cell(length(noiseBandNames), 1);
        valueSet = cell(length(noiseBandNames), 1);
    
        % Correct noise band names
        for i=1:length(noiseBandNames)
        
            % Remove the first 'x' symbol
            tmp = noiseBandNames{i}(2:end);
            
            % Replace the second '_' with '-'
            idx = strfind(tmp, '_');
            tmp(idx(length(idx))) = '-';
            
            % Save a new noise band name
            keySet{i} = tmp;
         
            % The bits of the band remain intact
            valueSet{i} = getfield(noiseBands, noiseBandNames{i});
        end
    
        % Write the result back to .fingerprint_noise_lev1 struct
        inResult.fingerprint_noise_lev1 = containers.Map(keySet, valueSet);
    end 
end

if isfield(inResult, 'fingerprint_noise_lev2')
    
    % Adjust fingerprint_noise_lev2
    noiseBands = inResult.fingerprint_noise_lev2;
    
     % Check if we have a structure or not
    if isstruct(noiseBands) ~= 0
        
        % Cell array of noise level bits
        noiseBandNames = fieldnames(noiseBands);
    
        % Key-value pairs for the hashmap
        keySet = cell(length(noiseBandNames), 1);
        valueSet = cell(length(noiseBandNames), 1);
    
        % Correct noise band names
        for i=1:length(noiseBandNames)
        
            % Remove the first 'x' symbol
            tmp = noiseBandNames{i}(2:end);
            
            % Replace the second '_' with '-'
            idx = strfind(tmp, '_');
            tmp(idx(length(idx))) = '-';
            
            % Save a new noise band name
            keySet{i} = tmp;
         
            % The bits of the band remain intact
            valueSet{i} = getfield(noiseBands, noiseBandNames{i});
        end
    
        % Write the result back to .fingerprint_noise_lev2 struct
        inResult.fingerprint_noise_lev2 = containers.Map(keySet, valueSet);  
    end 
end

outResult = inResult;

end

