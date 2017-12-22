function [] = computeNFP(nL1, nL2, timeInterval, noiseData)
%COMPUTENFP Summary of this function goes here
%   Detailed explanation goes here

% Construct metadata struct
metadata = struct;

% Metadata struct: generator_version
metadata.generator_version = noiseData.scriptVersion;

% Params to compute hash
Opt.Format = 'hex';
Opt.Method = 'SHA-1';
Opt.Input = 'array';

% Compute sha-1 hashes over audio files
hash1 = DataHash(nL1, Opt);
hash2 = DataHash(nL2, Opt);
    
% Get file paths similar to AFP, SPF and TFD: Sensor-xx/audio/xx.flac
res = split(noiseData.filePath1, noiseData.expPath);
if strcmp(res{2}(1), '\') | strcmp(res{2}(1), '/')
    res{2} = res{2}(2:end);
end
pathS1 = res{2};

res = split(noiseData.filePath2, noiseData.expPath);
if strcmp(res{2}(1), '\') | strcmp(res{2}(1), '/')
    res{2} = res{2}(2:end);
end
pathS2 = res{2};

% FileInfo struct: pack file paths (file hashes) and audioDuration
fileInfo = struct;
fileInfo.file1 = strcat(pathS1, ' (', hash1, ')');
fileInfo.file2 = strcat(pathS2, ' (', hash2, ')');

% Length of the audio recording over which noise levels were computed
fileInfo.audio_len = strcat(num2str(length(nL1)), ' sec'); 

% Metadata struct: source_files
metadata.source_files = fileInfo;

% Metadata struct: generator_script
metadata.generator_script = strcat('audioJob.m', '/', mfilename);

% Metadata struct: processing_start
metadata.processing_start = datestr(datetime('now'), noiseData.dateFormat);

% Compute NFP
[nfpS1, nfpS2] = noiseFingerprint(nL1, nL2, timeInterval, noiseData);

% Get length of the NFP, note len(nfpS1) = len(nfpS2) 
nfpLen = length(nfpS1); 

% Compute Hamming distance between NFPs
hamDist = binHammingDist(nfpS1, nfpS2);

% Pack noise fingerprints
[nfpS1Str, nfpS2Str] = packNoiseFingerprint(nfpS1, nfpS2);

% Metadata struct: processing_end
metadata.processing_end = datestr(datetime('now'), noiseData.dateFormat);

% Key-value pairs for a hashmap
keySet = {};
valueSet = {};

% Feature struct: fp1, fp2, fps_ham_dist, fps_similarity, fp_len
feature = struct;
feature.fingerprint_noise_lev1 = nfpS1Str;
feature.fingerprint_noise_lev2 = nfpS2Str;
feature.fingerprints_hamming_dist = hamDist;
feature.fingerprints_similarity_percent = ((nfpLen - hamDist)/nfpLen)*100;
feature.fingerprint_len_bits = nfpLen;

% Hashmap: "<timestamp>:" "<feature_struct>"

keySet{1} = noiseData.startTime;
valueSet{1} = feature;

% Metadata struct: created_on
metadata.created_on = datestr(datetime('now'), noiseData.dateFormat);
                
% Output struct: contains both metadata and results
output.metadata = metadata; 
output.results = containers.Map(keySet, valueSet);

% Save the main log file
fileName = extractBetween(pathS2, 'audio/', '.flac');
res = strsplit(pathS1, '/');
logPath = strcat(noiseData.expPath, '/', res{1}, '/', res{2}); 
mainLogFile = strcat(logPath, '/', noiseData.feature, '/', ...
    'sensor-', fileName, '.json');

saveJsonFile(char(mainLogFile), output);

% % Flip metadata.source_files for symmetric log file
% tmpStruct = metadata.source_files;
% fileInfo.file1 = tmpStruct.file2;
% fileInfo.file2 = tmpStruct.file1;
% metadata.source_files = fileInfo;
% 
% % Flip feature.fingerprint_file1 and feature.fingerprint_file2 for
% % symmetric log file
% feature.fingerprint_noise_lev1 = nfpS2Str;
% feature.fingerprint_noise_lev2 = nfpS1Str;
% 
% % Update hashmap
% valueSet{1} = feature;
% 
% % Update output struct
% output.metadata = metadata; 
% output.results = containers.Map(keySet, valueSet);
% 
% % Save the symmetric log file
% fileName = extractBetween(pathS1, 'audio/', '.flac');
% res = strsplit(pathS2, '/');
% logPath = strcat(noiseData.expPath, '/', res{1}, '/', res{2}); 
% symLogFile = strcat(logPath, '/', noiseData.feature, '/', ...
%     'sensor-', fileName, '.json');
% 
% saveJsonFile(char(symLogFile), output);

end

