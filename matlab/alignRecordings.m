function [] = alignRecordings(expPath, fileFormat)
%ALIGNRECORDINGS Summary of this function goes here
%   Detailed explanation goes here

% Date format of timestamps
dateFormat = 'yyyy-mm-dd HH:MM:SS.FFF';

% Basic sampling frequency with which we are working
Fs = 16000;

% Get folder structure
expFolder = dir(expPath);

% Check the number of subfolders in the selected folder: we ignore folders
% '.' and '..' as well as files
nSubfolders = sum([expFolder(~ismember({expFolder.name}, {'.', '..'})).isdir]);

if nSubfolders == 0
    fprintf('Selected folder: "%s" is empty!\n', expFolder(1).folder);
    return;
end

% Initialize array of root sub-folder names (e.g. Sensor-1, ...)
subFolderArr = strings(1, nSubfolders);

% Check file format (we only support .wav or .flac formats)
if ~strcmpi(fileFormat, 'wav') & ~strcmpi(fileFormat, 'flac')
    fprintf('Only "wav" or "flac" file formats are supported!\n');
    return;
end

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
                j = j + 1;
            else
                fprintf('Sub-folder "%s" has wrong format: must be /Sensor-xx!\n', expFolder(i).name);
                return;
            end
        end 
    end
end

% Cell array to store audio timestamps (when audio started)
audioTimestamps = cell(nSubfolders, 1);

% Array of datenum timestamps
numTimestamps = zeros(nSubfolders, 1);

% Array of original singal lengths
origSigLens = zeros(nSubfolders, 1);

% Name of a folder where audio data is stored
audioFolderName = 'audio';

% Day to sec multiplier
day2Sec = 24*3600;

% Type of loaded audio data: native or double
dataType = 'native';

% Iterate over the sub-folders and load audio timestamps
fprintf('Reading folders with audio data...\n');
for i = 1:nSubfolders 
    
    % Construct path to the audio timestamps (\ - on Windows)
    audioTSPath = strcat(expFolder(1).folder, '/', char(subFolderArr(i)),...
        '/', audioFolderName);
    
    audioFolder = dir(strcat(audioTSPath, '/', '*.time'));
    
    % Check if timestamp file exists
    if isempty(audioFolder)
        fprintf('Cannot find *.time file in: %s\n', audioTSPath);
        return; 
    end
    
    % File name to read a timestamp from 
    fileName = char(strcat(audioTSPath, '/', audioFolder.name));
    
    % Open a file for reading
    fileID = fopen(fileName);

    % Read the first line from the file, removing new line characters
    startTime = fgetl(fileID);

    % Close *.time file
    fclose(fileID);

    % Verify that startTime has required dateFormat (# of milliseconds is ignored)
    try
        startTimeNum = datenum(startTime, dateFormat);
    catch
        fprintf('File "%s" contains incorrect date format, must be "%s"\n', fileName, dateFormat);
        return;
    end
    
    % Store a timestamp (string)
    audioTimestamps{i} = startTime;
    
    % Store a timestamp (number in seconds)
    numTimestamps(i) = startTimeNum*day2Sec;
    
    % Get the audio file in audioTSPath folder
    audioFolder = dir(strcat(audioTSPath, '/', '*.', fileFormat));

    % Check if audio file exists
    if isempty(audioFolder)
        fprintf('Cannot find *.%s file in: %s\n', audioTSPath, fileFormat);
        return; 
    end

    % Name of audio file
    fileName = char(strcat(audioTSPath, '/', audioFolder.name));
    
    % Load signal
    sig = loadSignal(fileName, dataType);

    % Get the lenght of the audio signal
    origSigLens(i) = length(sig);

    % Clear the signal
    clear sig;
end

% Find max timestamp
[val, idx] = max(numTimestamps);

% Aligned start time - the latest timestamp
startTime = audioTimestamps{idx};

% Start time log file name
startLogName = 'audio.time';

% Audio start file name
fileName = strcat(expFolder(1).folder, '/', startLogName);

% Open a file for writing
logID = fopen(fileName, 'w');

% Save the start time into a file
fprintf(logID, startTime);

% Close file
fclose(logID);

% Get delays in number of samples
sigSampleDelays = round((val - numTimestamps)*Fs); 

% Get min signal length after the alignment
minSigLen = min(origSigLens - sigSampleDelays);

% Save vars
save('sigSampleDelays.mat', 'sigSampleDelays');
save('minSigLen.mat', 'minSigLen');

% Load audio signals, align them and save back to disk
fprintf('Aligning audio files ...\n');
for i = 1:nSubfolders 
    
    % Construct path to the audio timestamps (\ - on Windows)
    audioPath = strcat(expFolder(1).folder, '/', char(subFolderArr(i)),...
        '/', audioFolderName);
    
    % Get the audio file in audioPath folder
    audioFolder = dir(strcat(audioPath, '/', '*.', fileFormat));
    
    % Check if audio file exists
    if isempty(audioFolder)
        fprintf('Cannot find *.%s file in: %s\n', audioPath, fileFormat);
        return; 
    end
    
    % Name of audio file
    fileName = char(strcat(audioPath, '/', audioFolder.name));
    
    % Load signal
    sig = loadSignal(fileName, dataType);
    
    % Align signal
    if sigSampleDelays(i) ~= 0
        sig = sig(sigSampleDelays(i):end);
    end

    sig = sig(1:minSigLen);
    
    % New file name of alinged audio
    aligFileName = extractBetween(fileName, 'Sensor-', '/audio');
    
    % Save alinged audio signal
    audiowrite(strcat(audioPath, '/', char(aligFileName), '.', fileFormat), sig, Fs);
  
    % Clear the signal
    clear sig;
end

end

