function [] = splitRecordings(inFolder, outFolder, chunkLen)
%SPLITRECORDINGS Summary of this function goes here
%   Detailed explanation goes here

% Basic sampling frequency with which we are working
Fs = 16000;

% Hour to sec multiplier
hour2Sec = 3600; 

% Type of loaded audio data
dataType = 'native';

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

% Name of a folder where audio data is stored
audioFolderName = 'audio';

% Get the name of audio file
res = split(subFolderArr(1), '-');

% Sample audio path (audio must already be aligned!)
sampleAudioPath = strcat(subFolderArr(1), '/', audioFolderName, '/', ...
    res(2), '.flac');

% Load a sample audio signal to find out nChunks
sig = loadSignal(strcat(expFolder(1).folder, '/', char(sampleAudioPath)), ...
    dataType);

% Get nChunks
nChunks = round(length(sig)/(chunkLen*hour2Sec*Fs));

fprintf('Number of chunks: %d\n', nChunks);

% Clear sig
clear sig;

% Folder paths to store split audio data
chunkFolders = cell(nChunks, 1);

% Create chunkFolders
for i=1:nChunks
    % Name of the chunk folder
    folderName = strcat(num2str((i-1)*chunkLen), '-', ...
         num2str(i*chunkLen), 'h');
     
    % Absolute path of the chunk folder
    chunkFolders{i} = strcat(outFolder, '/', folderName);
    
    % Create chunk folders
    mkdir(chunkFolders{i});
end

% Split interval in number of samples 
splitInterval = chunkLen*hour2Sec*Fs;

% Load stuff from previous iteration
load('sigSampleDelays.mat');
load('minSigLen.mat');

% Iterate over audio folders and save chunks in chunk folders
for i=1:nSubfolders
    
	if i ~= 7
	
		% Construct path to the audio timestamps (\ - on Windows)
		audioPath = strcat(expFolder(1).folder, '/', char(subFolderArr(i)),...
        '/', audioFolderName);
    
		% Get the audio file in audioTSPath folder
		audioFolder = dir(strcat(audioPath, '/', '*.flac'));
    
		% Check if audio file exists
		if isempty(audioFolder)
			fprintf('Cannot find *.flac file in: %s\n', audioPath);
			return; 
		end
    
		% Name of audio file
		fileName = char(strcat(audioPath, '/', audioFolder.name));
		
		fprintf('loading audio file: %s\n', fileName);
    
		% Load audio signal
		sig = loadSignal(fileName, dataType);
		
		% Align signal
		if sigSampleDelays(i) ~= 0
			sig = sig(sigSampleDelays(i):end);
		end

		sig = sig(1:minSigLen);
		
		% Chunk name
		chunkName = audioFolder.name;
	
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
		
		% Align signal
		if sigSampleDelays(i) ~= 0
			sig = sig(sigSampleDelays(i):end);
		end

		sig = sig(1:minSigLen);
		
		% Chunk name
		chunkName = '07.flac';
		
		% Clean up
		clear sig1;
		clear sig2;
		clear outVect;
		
	end
	
    % Split audio signal into chunks and store chunks in chunk folders
    for j=1:nChunks
        
        % Chunk audio signal
        if j == nChunks
            % The last split signal -> take the reminder of initial signal
            chunk = sig((j-1)*splitInterval+1:length(sig));
        else
            % Regular split
            chunk = sig((j-1)*splitInterval+1:splitInterval*j);
        end
        
        % Chunk folder path
        chunkFolder = strcat(chunkFolders{j}, '/', subFolderArr(i), '/', ...
            audioFolderName);
        
        % Create chunkFolder
        mkdir(char(chunkFolder));
        
        % Save chunkFile
        audiowrite(char(strcat(chunkFolder, '/', chunkName)), chunk, Fs);    
    end  
end

end

