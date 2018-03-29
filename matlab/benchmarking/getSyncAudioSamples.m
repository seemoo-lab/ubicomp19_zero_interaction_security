function [] = getSyncAudioSamples(inPath, outPath, scenario)
%GETSYNCAUDIOSAMPLES Summary of this function goes here
%   Detailed explanation goes here

% Array of time intervals to compute on in sec
timeInterval = [5 10 15 30 60 120];

% Basic sampling frequency with which we are working
Fs = 16000;

% Type of loaded audio data: native
dataType = 'native';

% Construct path to the audio timestamps (\ - on Windows)   
inFolder = dir(strcat(inPath, '/', '*.flac'));
    
% Check if audio files exist
if isempty(inFolder)
    fprintf('Cannot find *.flac files in: %s\n', inPath);
    return; 
end

if strcmp(scenario, 'car') == 1 
    nSensors = 12;
    nContexts = 2;
    nSensorsPerContext = nSensors/nContexts;
elseif strcmp(scenario, 'office') == 1
    nSensors = 24;
    nContexts = 3;
    nSensorsPerContext = nSensors/nContexts;
else
    fprintf('Scenario: "%s" is not allowed, only "car" or "office"\n', scenario);
    return;
end

% Get reference file name (all signals alinged and have the same length)
fileName = char(strcat(inPath, '/', inFolder(1).name));

% Load reference signal
sig = loadSignal(fileName, dataType);

% % Cell array to store chunk numbers for each time interval
% syncChunkArr = cell(1, length(timeInterval));

% Array to store chunk numbers for each time interval
syncChunkArr = zeros(1, length(timeInterval));

% Iterate over time intervals
for i = 1:length(timeInterval)
    % Chunk length
    chunkLen = timeInterval(i)*Fs;

    % Find number of chunks
    nChunks = floor(length(sig)/chunkLen);
    
    % Generate a random number for each timeInterval for both contexts
    syncChunkArr(i) = randperm(nChunks, 1);  
    
%     % Generate two random numbers for each timeInterval for each context
%     syncChunkArr{i} = randperm(nChunks, nContexts);
end

% Clear reference signal
clear sig;

% Iterate over sensors within one context
for k=1:nContexts
    for i=(k-1)*nSensorsPerContext+1:k*nSensorsPerContext
        % Get file name
        fileName = char(strcat(inPath, '/', inFolder(i).name));
%         fprintf('file name: %s\n', fileName);
        
        % Load signal
        sig = loadSignal(fileName, dataType);
        
        % Iterate over time intervals
        for j = 1:length(timeInterval)
            % Chunk length
            chunkLen = timeInterval(j)*Fs;
            
            % Get audio chunk
            audioSample = sig(syncChunkArr(j)*chunkLen:(syncChunkArr(j)+1)*chunkLen-1);
            
            % Split audio file name, e.g. 01.flac to '01' and 'flac'
            res = strsplit(inFolder(i).name, '.');

            % Construct file name of audio sample
            fileName = strcat(outPath, '/', res{1}, '_', scenario, ...
                '-', num2str(timeInterval(j)), '.', res{2});

            % Save audio file
            audiowrite(char(fileName), audioSample, Fs);
            
%             fprintf('interval = %d, rand = %d\n', timeInterval(j), syncChunkArr(j));
        end
        % Clear signal
        clear sig;
    end
end

end

