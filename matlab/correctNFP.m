function [] = correctNFP(inFolder)
%CORRECTNFP Summary of this function goes here
%   Detailed explanation goes here

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

nfpFolder = 'audio/noiseFingerprint';

% Iterate over Sensor-01, 02, etc.
for i=1:nSubfolders
    
    % Construct path to NFP log folders
    nfpPath = strcat(expFolder(1).folder, '/', char(subFolderArr(i)),...
        '/', nfpFolder);
    
    % Content of a log folder
    logFolder = dir(nfpPath);
        
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
    
    % Store result folders names in resFolderArr
    k = 1;
    for j = 1:length(logFolder)
         % Only check folders, ignore files
         if logFolder(j).isdir == 1
             % Only check the meaninful sub-folder names
              if logFolder(j).name ~= '.' | logFolder(j).name ~= '..'
                  % Check for the correct names of the res folders
                  if ~isempty(strfind(logFolder(j).name, 'sec')) | ... 
                          ~isempty(strfind(logFolder(j).name, 'min'))
                      resFolderArr(k) = logFolder(j).name;
                      k = k + 1;
                  else
                      fprintf('Res-folder "%s" has wrong format: must contain sec or min!\n', ...
                          logFolder(j).name);
                      return;
                  end
              end
         end 
    end
    
    % Iterate over 10sec, 1min, etc.
    for j=1:nResFolders
        
        % Get JSON files in each resLogFolder
        logPath = strcat(nfpPath, '/', resFolderArr{j});
        resFolder = dir(strcat(logPath, '/', 'sensor-*.json'));
        
        % Number of json files
        nJsonFiles = length(resFolder);
        
        % Cell to store json file names
        jsonFileNames = cell(nJsonFiles, 1);
        
        % Store json file names in jsonFileNames
        for k=1:nJsonFiles
            jsonFileNames{k} = resFolder(k).name; 
        end
        
        % Sort names of json files in ascending order
        jsonFileNames = natsortfiles(jsonFileNames);
                    
        % Cell to store content of json files
        jsonFiles = cell(nJsonFiles, 1);
        
        % Save content of json files into jsonFiles
        parfor k=1:nJsonFiles
            jsonFiles{k} = jsondecode(fileread(strcat(logPath, '/', ...
                jsonFileNames{k})));
        end
       
        % Adjust the results
        parfor k=1:nJsonFiles % parfor
            
%             fprintf('path: %s\n', logPath);
%             fprintf('file: %d\n', k);
            
            % Get timestamp value
            timestamp = fieldnames(jsonFiles{k}.results);
            
            % Get results struct
            res = getfield(jsonFiles{k}.results, char(timestamp));
            
%             check = 'C:\Users\LabVIEW\Desktop\car/Sensor-02/audio/noiseFingerprint/1min';
%             
%             if strcmp(logPath, check)
%                 fprintf('wait...\n');
%             end
            
            % Check if excessive fields exist
            if isfield(res, 'noise_fingerprint1') & ...
                    isfield(res, 'noise_fingerprint2')
                
                % Remove unnecessary fields
                res = rmfield(res, 'noise_fingerprint1');
                res = rmfield(res, 'noise_fingerprint2');
                
                % Flip lev1 and lev2
                nfp1 = res.fingerprint_noise_lev2;
                nfp2 = res.fingerprint_noise_lev1;
                
                res.fingerprint_noise_lev1 = nfp1;
                res.fingerprint_noise_lev2 = nfp2;
                
                % Correct bit bands
                res = correctBands(res);
                
                % Key field: date
                key = correctDate(timestamp{1});
                
                % Value field: results
                value = res;
                
                % Map of results
                mapResults = containers.Map(key, value);
                
                % Update results
                jsonFiles{k}.results = mapResults;
                
                % Path of the resulting JSON file
                resJsonFile = strcat(logPath, '/', jsonFileNames{k});
                
                fprintf('saving file: %s\n', resJsonFile);

                % Save the resulting json
                saveJsonFile(char(resJsonFile), jsonFiles{k});
                
            end
        end
    end
end

end

