function [] = computePowerSPF(filePath1, filePath2, expPath)
%COMPUTEPOWERSPF Summary of this function goes here
%   Detailed explanation goes here

p = gcp('nocreate');
if isempty(p)
   parpool('local');
end

% Array of time intervals to compute on in sec
timeInterval = [5 10 15 30 60 120];

% Basic sampling frequency with which we are working
Fs = 16000;

% Names of S1 and S2
nameS1 = extractBetween(filePath1, 'audio/', '.flac');
nameS2 = extractBetween(filePath2, 'audio/', '.flac');
    
pathS1 = strcat('Sensor-', nameS1, '/audio/');
pathS2 = strcat('Sensor-', nameS2, '/audio/');

% Log folders
logFolders = {'soundProofXcorr'};

% Create log folders
for i = 1:length(logFolders)
    mkdir(strcat(expPath, '/', char(pathS1), logFolders{i}));
    mkdir(strcat(expPath, '/', char(pathS2), logFolders{i}));
end

% Log paths
logPath1 = strcat(expPath, '/', char(pathS1));
logPath2 = strcat(expPath, '/', char(pathS2));

% Length of one hour recoding in samples: nSec * Fs (here - test only 1m)
hourLen = 3600*Fs; 

% Type of loaded audio data: native for noise features
dataType = 'native';

% Load two audio signals
S1 = loadSignal(filePath1, dataType);
S2 = loadSignal(filePath2, dataType);

% Get only the first hour of audio
hourS1 = S1(1:hourLen);
hourS2 = S2(1:hourLen);
    
% Time lag in sec to bind xcorrDelay computation: we assume devices
% should be able to sycn at some point in time, but not tightly
timeLag = 3;
    
% Find a delay between two 1-hour chunks of two signals
sampleDiff = xcorrDelay(hourS1, hourS2, timeLag, Fs);
    
% Align two signals based on the delay
[S1, S2] = alignTwoSignals(S1, S2, sampleDiff);

% Main loop
for i = 1:length(timeInterval)
    
    % Chunk length
    chunkLen = timeInterval(i)*Fs;
    
    % Find number of chunks
    nChunks = round(length(S1)/chunkLen);
    
    % Allocate necessary amount of memory for chunked S1
    sig1 = cell(nChunks, 1);
    
    % Break S1 into a number of chunks according to timeInterval(i)
    for j = 1:nChunks
       if j == nChunks
           sig1{j} = S1((j-1)*chunkLen+1:length(S1));
       else
           sig1{j} = S1((j-1)*chunkLen+1:chunkLen*j);
       end
    end
    
    % Allocate necessary amount of memory for chunked S2
    sig2 = cell(nChunks, 1);
    
    % Break S1 into a number of chunks according to timeInterval(i)
    for j = 1:nChunks
       if j == nChunks
           sig2{j} = S2((j-1)*chunkLen+1:length(S2));
       else
           sig2{j} = S2((j-1)*chunkLen+1:chunkLen*j);
       end
    end
    
    % Define if the time interval is in min or sec
    if floor(timeInterval(i)/60) >= 1
        timeStr = 'min';
        timeDiv = 60;
    else
        timeStr = 'sec';
        timeDiv = 1;
    end
    
    % Names of chunks for sig1 and sig2
    nameSlice1 = strings(nChunks, 1); 
    nameSlice2 = strings(nChunks, 1); 
    
    for j = 1:nChunks
        nameSlice1(j) = strcat(pathS1, nameS1, '_', num2str(floor((j-1)*timeInterval(i)/timeDiv)), ...
            '-', num2str(floor(j*timeInterval(i)/timeDiv)), timeStr, '.flac');
        
        nameSlice2(j) = strcat(pathS2, nameS2, '_', num2str(floor((j-1)*timeInterval(i)/timeDiv)), ...
            '-', num2str(floor(j*timeInterval(i)/timeDiv)), timeStr, '.flac');
    end
    
    % Create time interval folders within log folders
    for j = 1:length(logFolders)
        mkdir(strcat(logPath1, logFolders{j}, '/', ...
            num2str(floor(timeInterval(i)/timeDiv)), timeStr));
        mkdir(strcat(logPath2, logFolders{j}, '/', ...
            num2str(floor(timeInterval(i)/timeDiv)), timeStr));
    end
    
    % Feature path
    featurePath = strcat(logFolders{1}, '/', ...
        num2str(floor(timeInterval(i)/timeDiv)), timeStr); % SPF folder
  
    % Key-value pairs for the hashmap
    keySet = cell(nChunks, 1);
    valueSet = cell(nChunks, 1);
              
    % Get number of digits in nChunks
    nDigits = length(num2str(nChunks));
    
    % Compute power
    fprintf('Computing power %s...\n', num2str(timeInterval(i)));
    parfor j = 1:nChunks
        
        % Power struct
        powerStruct = struct;
        
        % Compute power in dB of two audio chunks
        powerStruct.power1_db = pow2db(sum(abs(sig1{j}).^2)/length(sig1{j}));
        powerStruct.power2_db = pow2db(sum(abs(sig2{j}).^2)/length(sig2{j}));
        
        % Convert current digit to string
        curDigitLen = length(num2str(j));
                        
        % Check how many zeros must be padded: e.g. in case of 4 digits 0001
        nZeros = nDigits - curDigitLen;
                        
        % Prefix string with zeros
        prefixStr = strrep(num2str(zeros(1, nZeros)), ' ', '');
                        
        % Key field: e.g. pair01
        keySet{j} = strcat('pair_', prefixStr, num2str(j));
                        
        % Value field: source_files info
        valueSet{j} = powerStruct;
    end
    
    % Map of chunk powers
    mapChunkPower = containers.Map(keySet, valueSet);
    
    % Json struct
    jsonStruct = struct;
    
    jsonStruct.results = mapChunkPower;
    
    % Path to a log file
    fileName = strcat(logPath1, featurePath, '/', 'Power-', nameS2, '.json');
    
    % Save powers to a JSON file
    saveJsonFile(char(fileName), jsonStruct);  
end

end

