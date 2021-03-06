function [] = computeTFD(S1, S2, sampleDiff, pathS1, pathS2, commonData, idx)
%COMPUTETFD Wrapper to compute time-frequency distance + metadata 
% and store the results in a JSON file

%   Input args:
%   - S1 - First audio chunk (Kx1 vector)
%   - S2 - Second audio chunk (Kx1 vector)
%   - sampleDiff - Delay between two chunks in samples (integer)
%   - pathS1 - Name of the first audio chunk (string)
%   - pathS2 - Name of the second audio chunk (string)
%   - commonData - Structure storing metadata (struct)
%   - idx - Index of an audio chunk (integer)

%   Output args: None

% Construct metadata struct
metadata = struct;

% Metadata struct: generator_version
metadata.generator_version = commonData.scriptVersion;

% Params to compute hash
Opt.Format = 'hex';
Opt.Method = 'SHA-1';
Opt.Input = 'array';

% Compute sha-1 hashes over audio files
hash1 = DataHash(S1, Opt);
hash2 = DataHash(S2, Opt);
               
% FileInfo struct: pack file paths (file hashes) and audioDuration
fileInfo = struct;
fileInfo.chunk1 = strcat(pathS1, ' (', hash1, ')');
fileInfo.chunk2 = strcat(pathS2, ' (', hash2, ')');

% Take the min length of two signals, only relevant for the very last
% chunk, otherwise len(S1) == len(S2)
minLen = min(length(S1), length(S2));

% Get signal length in seconds
audioLenSec = round(minLen/commonData.Fs);

% Check signal duration and assign min, min and sec or sec 
if floor(audioLenSec/60) >= 1 
    reminder = mod(audioLenSec, 60);
    if reminder == 0
        % in min
        audioDuration = strcat(num2str(floor(audioLenSec/60)), ' min'); 
    else     
        % in min and sec
        audioDuration = horzcat(num2str(floor(audioLenSec/60)), ' min ', ...
            num2str(reminder), ' sec');
    end
else 
    % in sec
    audioDuration = strcat(num2str(audioLenSec), ' sec'); 
end

fileInfo.audio_len = audioDuration;
                  
% Metadata struct: source_files
metadata.source_files = fileInfo;

% Metadata struct: generator_script
metadata.generator_script = strcat('audioJob.m', '/', mfilename);

% Metadata struct: processing_start
metadata.processing_start = datestr(datetime('now'), commonData.dateFormat);

% Compute TFD
[maxXCorr, freqDist, timeFreqDist] = timeFreqDistance(S1, S2, sampleDiff);

% Metadata struct: processing_end
metadata.processing_end = datestr(datetime('now'), commonData.dateFormat);

% Key-value pairs for a hashmap
keySet = {};
valueSet = {};
                
% Feature struct: xcorr_delay, fdist, mxcorr, tfdist
feature = struct;
% Add this field only if we compute per chunk sampleDiff
if sampleDiff ~= 0 
    feature.delay_xcorr_sec = sampleDiff/commonData.Fs;
end
feature.freq_dist = freqDist;
feature.max_xcorr = maxXCorr;
feature.time_freq_dist = timeFreqDist; 
                
% Hashmap: "<timestamp>:" "<feature_struct>"

% Convert start time into a number
startTimeNum = datenum(commonData.startTime, commonData.dateFormat);

% Time of one audio chunk should be added to the start time of each audio
% signal (/Sensor-xx/audio)
currentChunk = mod(idx, commonData.nAudioChunks);

% Get the number of seconds we need to add to start time 
if currentChunk == 0 % the last chunk in /Sensor-xx/audio folder
    chunkTime = (commonData.nAudioChunks-1)*commonData.timeInterval;
else 
    chunkTime = (currentChunk-1)*audioLenSec;
end

% Add chunkTime to startTimeNum
startTimeNum = addtodate(startTimeNum, chunkTime, 'second');

keySet{1} = datestr(startTimeNum, commonData.dateFormat);
valueSet{1} = feature;
                
% Metadata struct: created_on
metadata.created_on = datestr(datetime('now'), commonData.dateFormat);
                
% Output struct: contains both metadata and results
output.metadata = metadata; 
output.results = containers.Map(keySet, valueSet);

% Construct log file path
fileName = extractBetween(pathS2, 'audio/', '.flac');
logFilePath = strcat(commonData.expPath, '/', 'sensor-', fileName, '.json');

% Save log file
saveJsonFile(logFilePath, output);

end