function [] = mergeJson(inFolder)
%MERGEJSON Summary of this function goes here
%   Detailed explanation goes here

% Enable parallel execution with Parallel Computing Toolbox
p = gcp('nocreate');
if isempty(p)
    parpool('local');
end

% Get folder structure
expFolder = dir(inFolder);

% Check the number of subfolders in the selected folder: we ignore folders
% '.' and '..' as well as files
nSubfolders = sum([expFolder(~ismember({expFolder.name}, {'.', '..'})).isdir]);

if nSubfolders == 0
    fprintf('Selected folder: "%s" is empty!\n', expFolder(1).folder);
    return;
end

% Initialize array of root sub-folder names (e.g. Sensor-1, ...)
subFolderArr = strings(1, nSubfolders);

% Store root sub-folder names in the array
j = 1;
for i = 1:length(expFolder)
    % Only check folders, ignore files
    if expFolder(i).isdir == 1
        % Only check the meaninful sub-folder names
        if expFolder(i).name ~= '.' | expFolder(i).name ~= '..'
            % Check for the correct names of the sub-folders
            if strfind(expFolder(i).name, 'Sensor-')
                subFolderArr(j) = expFolder(i).name;
%               fprintf('sub-folder name: %s\n', expFolder(i).name);
                j = j + 1;
            else
                fprintf('Sub-folder "%s" has wrong format: must be /Sensor-xx!\n', expFolder(i).name);
                return;
            end
        end 
    end
end

% Log folders
logFolders = {'audioFingerprint', 'soundProofXcorr', 'timeFreqDistance'};

% Name of a folder where audio data is stored
audioFolderName = 'audio';

% Iterate over the sub-folders and load audio timestamps
fprintf('Reading folders with audio data...\n');
for i = 1:nSubfolders 
    
    % Construct path to the audio timestamps (\ - on Windows)
    audioPath = strcat(expFolder(1).folder, '/', char(subFolderArr(i)),...
        '/', audioFolderName);
    
    % Iterate over log folders
    for j=1:length(logFolders)
        
        % Path to a log folder: AFP, SPF, TFD (NFP does not require merging)
        logPath = strcat(audioPath, '/', logFolders{j});
        
        % Content of a log folder
        logFolder = dir(logPath);
        
        % Number of result folders: we ignore folders '.' and '..' 
        % as well as files
        nResFolders = sum([logFolder(~ismember({logFolder.name}, ...
            {'.', '..'})).isdir]);
        
        if nResFolders == 0
            fprintf('Selected folder: "%s" is empty or does not exist!\n', ...
				logPath);
            return;
        end
        
        % Array to store result foldres: 5sec, 30sec, 1min, etc
        resFolderArr =  strings(1, nResFolders);
        
        % Store result foldres names in resFolderArr
        k = 1;
        for m = 1:length(logFolder)
             % Only check folders, ignore files
             if logFolder(m).isdir == 1
                 % Only check the meaninful sub-folder names
                  if logFolder(m).name ~= '.' | logFolder(m).name ~= '..'
                      % Check for the correct names of the res folders
                      if ~isempty(strfind(logFolder(m).name, 'sec')) | ... 
                              ~isempty(strfind(logFolder(m).name, 'min'))
                          resFolderArr(k) = logFolder(m).name;
                          k = k + 1;
                      else
                          fprintf('Res-folder "%s" has wrong format: must contain sec or min!\n', ...
                              logFolder(m).name);
                          return;
                      end
                  end
             end 
        end
       
        % Current sensor index
        curSensorIdx = strsplit(subFolderArr(i), '-');
        curSensorIdx = curSensorIdx{2};
        
        % Iterate over res folders
        for k=1:nResFolders
            % Check .json files for each individual sensor (sensor-xx_*.json)
            parfor m=1:nSubfolders
                % Get sensor index
                sensorIdx = strsplit(subFolderArr(m), '-');
                sensorIdx = sensorIdx{2};
                % Each res folder contains results between curSensorIdx and
                % all other sensors apart from curSensorIdx
                if ~strcmp(sensorIdx, curSensorIdx)
					% Log statments
					fprintf('in folder: %s\n', strcat(logPath, '/', resFolderArr(k)));
                    fprintf('proceed with index: %s\n', sensorIdx);

                    % Content of the result folder for a specific sensorIdx
                    resFolder = dir(char(strcat(logPath, '/', resFolderArr(k), ...
                        '/', 'sensor-', sensorIdx, '*.json')));
                    
                    % Number of json files
                    nJsonFiles = length(resFolder);
                    
                    % Cell to store json file names
                    jsonFileNames = cell(nJsonFiles, 1);
                    
                    % Store json file names in jsonFileNames
                    for l=1:nJsonFiles
                        jsonFileNames{l} = resFolder(l).name;
                    end
                    
                    % Sort names of json files in ascending order
                    jsonFileNames = natsortfiles(jsonFileNames);
                    
                    % Cell to store content of json files
                    jsonFiles = cell(nJsonFiles, 1);
                    
                    % Save content of json files into jsonFiles
                    for l=1:nJsonFiles
                        jsonFiles{l} = jsondecode(fileread(strcat(resFolder(1).folder, ...
                            '/', jsonFileNames{l})));
                    end
                    
                    % Key-value pairs for the hashmap
                    keySet = cell(nJsonFiles, 1);
                    valueSet = cell(nJsonFiles, 1);
                    
                    % Get number of digits in nJsonFiles
                    nDigits = length(num2str(nJsonFiles));
                    
                    % Aggregate source_files
                    for l=1:nJsonFiles
                        % Convert current digit to string
                        curDigitLen = length(num2str(l));
                        
                        % Check how many zeros must be padded: e.g. in case
                        % of 4 digits 0001
                        nZeros = nDigits - curDigitLen;
                        
                        % Prefix string with zeros
                        prefixStr = strrep(num2str(zeros(1, nZeros)), ' ', '');
                        
                        % Key field: e.g. pair01
                        keySet{l} = strcat('pair_', prefixStr, num2str(l));
                        
                        % Value field: source_files info
                        valueSet{l} = jsonFiles{l}.metadata.source_files;  
                    end
                    
                    % Map of source files
                    mapSourceFiles = containers.Map(keySet, valueSet);
                    
                    % Aggregate results
                    for l=1:nJsonFiles
                        % Get timestamp value
                        timestamp = fieldnames(jsonFiles{l}.results);
                        
                        % Key field: date
                        keySet{l} = correctDate(timestamp{1});
                        
                        % Value field: results
                        valueSet{l} = correctBands(jsonFiles{l}.results.(timestamp{1}));
                        
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
                    resJsonFile = strcat(logPath, '/', resFolderArr(k), ...
                         '/', 'Sensor-', sensorIdx, '.json');
                     
                    % Delete source JSON files
                    delPath = strcat(logPath, '/', resFolderArr(k), ...
                        '/', 'sensor-', sensorIdx, '*.json');
                    
                    delete(char(delPath));
                     
                    % Save the resuting json
                    saveJsonFile(resJsonFile, jsonFiles{1});
                end
            end
        end   
    end
end


end

