function [nfpS1Str, nfpS2Str] = packNoiseFingerprint(nfpS1, nfpS2)
%PACKNOISEFINGERPRINT Summary of this function goes here
%   Detailed explanation goes here

% The size of one nfp chunk
chunkSize = 512;

% Number of noise fingerprint chunks
nChunks = floor(length(nfpS1)/chunkSize);

% Check if fingerprints are less or equal 512 bits
if nChunks <=1 & length(nfpS1)-chunkSize <= 0
    
   % Convert NFPs to strings
    nfpS1Str = num2str(nfpS1);
    nfpS2Str = num2str(nfpS2); 
    
    % Remove spaces in NFPs strings
    nfpS1Str = nfpS1Str(~isspace(nfpS1Str));
    nfpS2Str = nfpS2Str(~isspace(nfpS2Str));
    
    return;
end

% Update number of chunks
nChunks = nChunks + 1;

% Key-value pairs for a hashmap
keySet1 = cell(1, nChunks);
valueSet1 = cell(1, nChunks);

% Key-value pairs for a hashmap
keySet2 = cell(1, nChunks);
valueSet2 = cell(1, nChunks);

% Split big nfpSx into nChunks of chunkSize
for i=1:nChunks
    
    % Split into chunks of length chunkSize
    if i == nChunks
        % The last split signal -> take the reminder of initial signal
        % 01, 02, ... vs. 10, 11
        if i < 10
            keySet1{i} = strcat('0', num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(length(nfpS1)));
            keySet2{i} = strcat('0', num2str(i), '_', ...
                 num2str((i-1)*chunkSize+1), '-', num2str(length(nfpS2)));
        else    
            keySet1{i} = strcat(num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(length(nfpS1)));
            keySet2{i} = strcat(num2str(i), '_', ...
                 num2str((i-1)*chunkSize+1), '-', num2str(length(nfpS2)));
        end
        
        tmpChunk = num2str(nfpS1((i-1)*chunkSize+1:length(nfpS1)));
        valueSet1{i} = tmpChunk(~isspace(tmpChunk)); 
        
        tmpChunk = num2str(nfpS2((i-1)*chunkSize+1:length(nfpS2)));
        valueSet2{i} = tmpChunk(~isspace(tmpChunk));        
    else
		% Regular split
        % 01, 02, ... vs. 10, 11
        if i < 10
            keySet1{i} = strcat('0', num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(chunkSize*i));         
            keySet2{i} = strcat('0', num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(chunkSize*i));
        else    
            keySet1{i} = strcat(num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(chunkSize*i));
            keySet2{i} = strcat(num2str(i), '_', ...
                num2str((i-1)*chunkSize+1), '-', num2str(chunkSize*i));
        end
        
        tmpChunk = num2str(nfpS1((i-1)*chunkSize+1:chunkSize*i));
        valueSet1{i} = tmpChunk(~isspace(tmpChunk));
        
        tmpChunk = num2str(nfpS2((i-1)*chunkSize+1:chunkSize*i));
        valueSet2{i} = tmpChunk(~isspace(tmpChunk));      
    end    
end

% Construct hashmaps
nfpS1Str = containers.Map(keySet1, valueSet1);
nfpS2Str = containers.Map(keySet2, valueSet2);

end

