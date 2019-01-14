function [] = localMerge(localPath, sensorIdx, savePath)
%LOCALMERGE Summary of this function goes here
%   Detailed explanation goes here

% Content of the result folder for a specific sensorIdx
resFolder = dir(char(strcat(localPath, '/', 'sensor-', sensorIdx, '*.json')));

% Number of json files
nJsonFiles = length(resFolder);
                    
% Cell to store json file names
jsonFileNames = cell(nJsonFiles, 1);
                    
% Store json file names in jsonFileNames
for i=1:nJsonFiles
    jsonFileNames{i} = resFolder(i).name;
end

% Sort names of json files in ascending order
jsonFileNames = natsortfiles(jsonFileNames);
                    
% Cell to store content of json files
jsonFiles = cell(nJsonFiles, 1);
                    
% Save content of json files into jsonFiles
parfor i=1:nJsonFiles
    jsonFiles{i} = jsondecode(fileread(strcat(localPath, '/', jsonFileNames{i})));
end

% Key-value pairs for the hashmap
keySet = cell(nJsonFiles, 1);
valueSet = cell(nJsonFiles, 1);
                    
% Get number of digits in nJsonFiles
nDigits = length(num2str(nJsonFiles));

% Aggregate source_files
parfor i=1:nJsonFiles
    % Convert current digit to string
    curDigitLen = length(num2str(i));
                        
    % Check how many zeros must be padded: e.g. in case of 4 digits 0001
    nZeros = nDigits - curDigitLen;
                        
    % Prefix string with zeros
    prefixStr = strrep(num2str(zeros(1, nZeros)), ' ', '');
                        
    % Key field: e.g. pair01
    keySet{i} = strcat('pair_', prefixStr, num2str(i));
                        
    % Value field: source_files info
    valueSet{i} = jsonFiles{i}.metadata.source_files;  
end

% Map of source files
mapSourceFiles = containers.Map(keySet, valueSet);
                    
% Aggregate results
parfor i=1:nJsonFiles
    % Get timestamp value
    timestamp = fieldnames(jsonFiles{i}.results);
                        
    % Key field: date
    keySet{i} = correctDate(timestamp{1});
                        
    % Value field: results
    valueSet{i} = correctBands(jsonFiles{i}.results.(timestamp{1}));                       
end

% Map of results
mapResults = containers.Map(keySet, valueSet);
                    
% Adjust metadata
jsonFiles{1}.metadata.created_on = jsonFiles{nJsonFiles}.metadata.created_on;
jsonFiles{1}.metadata.processing_end = jsonFiles{nJsonFiles}.metadata.processing_end;
jsonFiles{1}.metadata.source_files = mapSourceFiles;
                    
% Adust results
jsonFiles{1}.results = mapResults;
                    
% Path of the resulting JSON file
resJsonFile = strcat(savePath, '/', 'Sensor-', sensorIdx, '.json');

% Save the resuting json
saveJsonFile(char(resJsonFile), jsonFiles{1});

% Delete source JSON files
delPath = strcat(localPath, '/', 'sensor-', sensorIdx, '*.json');
                    
delete(char(delPath));

end

