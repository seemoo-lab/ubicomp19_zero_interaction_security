function [] = benchmarkingJob(inPath, scenario)
%BENCHMARKINGJOB Summary of this function goes here
%   Detailed explanation goes here

% Construct path to text input bencmark files  
inFolder = dir(strcat(inPath, '/', '*.txt'));
    
% Check if audio files exist
if isempty(inFolder)
    fprintf('Cannot find *.txt files in: %s\n', inPath);
    return; 
end

if strcmp(scenario, 'car') == 0 & strcmp(scenario, 'office') == 0
    fprintf('Scenario: "%s" is not allowed, only "car" or "office"\n', scenario);
    return;
end

% Iterate over *.txt files
for i=1:length(inFolder)
    % Get file name
    fileName = char(strcat(inPath, '/', inFolder(i).name));
    
    fprintf('processing: %s\n', fileName);
    
    % Launch audio banchmarking 
    audioBenchmarking(fileName, scenario)
end

end

