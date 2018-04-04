function [] = getRandAudioSamples(inPath, outPath, scenario)
%GETRANDAUDIOSAMPLES Summary of this function goes here
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

if strcmp(scenario, 'car') == 0 & strcmp(scenario, 'office') == 0
    fprintf('Scenario: "%s" is not allowed, only "car" or "office"\n', scenario);
    return;
end

% Iterate over *.flac files
for i=1:length(inFolder)
    % Get file name
    fileName = char(strcat(inPath, '/', inFolder(i).name));

    % Load signal
	sig = loadSignal(fileName, dataType);
    
    % Iterate over time intervals
    for j = 1:length(timeInterval)
        
        % Chunk length
        chunkLen = timeInterval(j)*Fs;
    
        % Find number of chunks
        nChunks = floor(length(sig)/chunkLen);
        
        % Generate a random number from 1 to nChunks
        rChunk = randi([1 nChunks], 1);
        
%         fprintf('chunkLen = %d, nChunks = %d, rChunk = %d\n', chunkLen, nChunks, rChunk);
        
        % Get audio chunk
        audioSample = sig(rChunk*chunkLen:(rChunk+1)*chunkLen-1);

        % Split audio file name, e.g. 01.flac to '01' and 'flac'
        res = strsplit(inFolder(i).name, '.');

        % Construct file name of audio sample
        fileName = strcat(outPath, '/', res{1}, '_', scenario, ...
            '-', num2str(timeInterval(j)), '.', res{2});

        % Save audio file
        audiowrite(char(fileName), audioSample, Fs);
    end
%     fprintf('\n');
    % Clear sig
    clear sig; 
end

end

