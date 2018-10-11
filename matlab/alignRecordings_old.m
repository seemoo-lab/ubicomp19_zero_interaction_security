function [] = alignRecordings(expFolder)
%ALIGNRECORDINGS Summary of this function goes here
%   Detailed explanation goes here

% Date format of timestamps
dateFormat = 'yyyy-mm-dd HH:MM:SS.FFF';

% Basic sampling frequency with which we are working
Fs = 16000;

% Get folder structure
expFolder = dir(expFolder);

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

% Type of loaded audio data: native
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
    
    % Load a timestamp from a file 
    fileName = char(strcat(audioTSPath, '/', audioFolder.name));
    
    fileID = fopen(fileName);
    
    % File should contain only one line with a timestamp of dateFormat
    tline = fgets(fileID);
    
    % Close *.time file
    fclose(fileID);
    
    % Remove new line character
    tline = tline(1:end-1);
    
    % Check if we stick to dateFormat
    if length(tline) ~= length(dateFormat)
       fprintf('Date format is incorrect in %s\n', fileName);
       fprintf('Correct date format is "%s"\n', dateFormat);
       return;
    end
    
    % Store a timestamp (string)
    audioTimestamps{i} = tline;
    
    % Store a timestamp (number in seconds)
    numTimestamps(i) = datenum(audioTimestamps{i}, dateFormat)*day2Sec;
    
	if i ~= 7
	
		% Get the audio file in audioTSPath folder
		audioFolder = dir(strcat(audioTSPath, '/', '*.flac'));
    
		% Check if audio file exists
		if isempty(audioFolder)
			fprintf('Cannot find *.flac file in: %s\n', audioTSPath);
			return; 
		end
    
		% Name of audio file
		fileName = char(strcat(audioTSPath, '/', audioFolder.name));
		
		fprintf('loading audio file: %s\n', fileName);
    
		% Load signal
		sig = loadSignal(fileName, dataType);
    
		% Get the lenght of the audio signal
		origSigLens(i) = length(sig);
    
		% Clear the signal
		clear sig;
	else
	
		fprintf('loading chunks...\n');
	
		% Load two chunks
		sig1 = loadSignal('/opt/code/audio-old.flac', dataType);
		sig2 = loadSignal('/opt/code/audio.flac', dataType);
		
		% Lenght of outSamples
		outSamples = round(421.33*Fs);
		
		% Out samples are set to zero
		outVect = int16(zeros(outSamples, 1));
		
		% Combine all vectors
		sig = vertcat(sig1, outVect, sig2);
		
		% Get the lenght of the audio signal
		origSigLens(i) = length(sig);
		
		% Clean up
		clear sig1;
		clear sig2;
		clear outVect;
		clear sig;
	end
	
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
    audioFolder = dir(strcat(audioPath, '/', '*.flac'));
    
    % Check if audio file exists
    if isempty(audioFolder)
        fprintf('Cannot find *.flac file in: %s\n', audioPath);
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
    audiowrite(strcat(audioPath, '/', char(aligFileName), '.flac'), sig, Fs);
  
    % Clear the signal
    clear sig;
	
	% Delte old .flac audio file
    delete(fileName);
        
end

end

