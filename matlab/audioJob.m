function [] = audioJob(filePath1, filePath2, expPath, tmpPath, localPath)
%AUDIOJOB Summary of this function goes here
%   Detailed explanation goes here

% Sleep for 1+X seconds to avoid problems when launching many instances
% at once (See https://de.mathworks.com/matlabcentral/answers/97141-why-am-i-unable-to-start-a-local-matlabpool-from-multiple-matlab-sessions-that-use-a-shared-preferen#comment_181845)
pause(1+30*rand());

% Enable parallel execution with Parallel Computing Toolbox
c = parcluster();
c.JobStorageLocation = tmpPath;
p = parpool(c);

%p = gcp('nocreate');
%if isempty(p)
%    parpool('local');
%end

% Version of the script
scriptVersion = 'v1.2.2';

% Date format for logs
dateFormat = 'yyyy-mm-dd HH:MM:SS.FFF';

% Array of time intervals to compute on in sec
timeInterval = [5 10 15 30 60 120];

% Basic sampling frequency with which we are working
Fs = 16000;

% Construct path to the audio timestamps (\ - on Windows)   
expFolder = dir(strcat(expPath, '/', '*.time'));
    
% Check if timestamp file exists
if isempty(expFolder)
    fprintf('Cannot find *.time file in: %s\n', expPath);
    return; 
end

% Load a timestamp from a file 
fileName = char(strcat(expPath, '/', expFolder.name));
    
fileID = fopen(fileName);
    
% File should contain only one line with a timestamp of dateFormat
tline = fgets(fileID);
    
% Close *.time file
fclose(fileID);
    
% Remove new line character
startTime = tline(1:end-1);

% Precompute SPF filter bank
spfFilterBankFile = strcat(expPath, '/', 'spfFilterBank.mat');
if exist(spfFilterBankFile, 'file') == 2
   fprintf('"%s" exists, loading it...\n', spfFilterBankFile);
   load(spfFilterBankFile);
else
    fprintf('"%s" does not exist, precomputing...\n', spfFilterBankFile);
    spfFilterBank = preComputeFilterSPF();
    save(spfFilterBankFile, 'spfFilterBank');
end

% Precompute AFP filter bank
afpFilterBankFile = strcat(expPath, '/', 'afpFilterBank.mat');
if exist(afpFilterBankFile, 'file') == 2
   fprintf('"%s" exists, loading it...\n', afpFilterBankFile);
   load(afpFilterBankFile);
else
    fprintf('"%s" does not exist, precomputing...\n', afpFilterBankFile);
    afpFilterBank = preComputeFilterAFP();
    save(afpFilterBankFile, 'afpFilterBank');
end

% Names of S1 and S2
nameS1 = extractBetween(filePath1, 'audio/', '.flac');
nameS2 = extractBetween(filePath2, 'audio/', '.flac');
    
pathS1 = strcat('Sensor-', nameS1, '/audio/');
pathS2 = strcat('Sensor-', nameS2, '/audio/');

% Log folders
logFolders = {'timeFreqDistance', 'soundProofXcorr', 'audioFingerprint', ...
    'noiseFingerprint'};

% Create log folders
for i = 1:length(logFolders)
    mkdir(strcat(expPath, '/', char(pathS1), logFolders{i}));
    mkdir(strcat(expPath, '/', char(pathS2), logFolders{i}));
end

% Log paths
logPath1 = strcat(expPath, '/', char(pathS1));
logPath2 = strcat(expPath, '/', char(pathS2));

% Length of one hour recoding in samples: nSec * Fs
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

% Number of samples to compute one value of noise level: 
% in Miettinen et al. time window was 100 ms and 1 sec
winLen = round(1*Fs);

% Number of noise samples out of S1 and S2
nNoiseSamples = round(length(S1)/winLen);

% Resulting noise level arrays
nL1 = zeros(1, nNoiseSamples);
nL2 = zeros(1, nNoiseSamples);

% Get noise levels
for i=1:nNoiseSamples
    
    % Split into chunks of length winLen
    if i == nNoiseSamples
        % The last split signal -> take the reminder of initial signal
        winS1 = S1((i-1)*winLen+1:length(S1));
        winS2 = S2((i-1)*winLen+1:length(S2));   
    else
		% Regular split
        winS1 = S1((i-1)*winLen+1:winLen*i);
        winS2 = S2((i-1)*winLen+1:winLen*i);
    end
    
    % Compute average noise of the window 
	% (we have signed 16-bit: take abs values)
    nL1(i) = mean(abs(winS1));
    nL2(i) = mean(abs(winS2));   
end

% Params to compute hash
Opt.Format = 'hex';
Opt.Method = 'SHA-1';
Opt.Input = 'array';

% Compute hashes of nL1 and nL2
nL1Hash = DataHash(nL1, Opt);
nL2Hash = DataHash(nL2, Opt);

% Construct noiseData struct
noiseData = struct;
noiseData.dateFormat = dateFormat;
noiseData.scriptVersion = scriptVersion;
noiseData.expPath = expPath;
noiseData.feature = '';
noiseData.filePath1 = filePath1;
noiseData.filePath2 = filePath2;
noiseData.sampleLenSec = 1;
noiseData.nL1Hash = nL1Hash;
noiseData.nL2Hash = nL2Hash;
noiseData.nNoiseSamples = length(nL1); % note nL1 == nL2
noiseData.startTime = startTime;

% Save noise levels into JSON-files
saveNoiseLevels(nL1, nL2, noiseData)

% Clear S1 and S2
clear S1;
clear S2;

% Type of loaded audio data: double for audio features
dataType = 'double';

% Compute different audio features per signal basis:
% 1. Time-frequency distance - TFD (Paper: Truong et al., ZIA'14)
% 2. Sound-Proof - SPF (Paper: Karapanos et al., Sound-Proof'15)
% 3. Audido fingerprinting - AFP (Paper: Sch??rmann and Sigg, Ambient audio'13)
% 4. Noise fingerprinting - NFP (Paper: Miettinen et al., ZIP'14)

% Main loop
for i = 1:length(timeInterval)
    
    % Load two audio signals
    S1 = loadSignal(filePath1, dataType);
    S2 = loadSignal(filePath2, dataType);
    
    % Align two signals based on the delay
    [S1, S2] = alignTwoSignals(S1, S2, sampleDiff);

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
    
    % Clear S1
    clear S1;
    
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
    
    % Clear S2
    clear S2;
    
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

    % Array of delays between audio pairs in samples computed with xcorr
    audioPairDelay = zeros(nChunks, 1);

    % Construct commonData struct
    commonData = struct;
    commonData.Fs = Fs;
    commonData.dateFormat = dateFormat;
    commonData.scriptVersion = scriptVersion;
    commonData.expPath = localPath;
    commonData.feature = strcat(logFolders{1}, '/', ...
        num2str(floor(timeInterval(i)/timeDiv)), timeStr); % TFD folder
    commonData.nAudioChunks = nChunks;
    commonData.startTime = startTime;
	commonData.timeInterval = timeInterval(i);
    
    % Compute TFD
    fprintf('Computing TFD...\n');
    parfor j = 1:nChunks
        computeTFD(sig1{j}, sig2{j}, audioPairDelay(j), ...
        nameSlice1(j), nameSlice2(j), commonData, j);
    end
    
    % Construct savePath
    res = strsplit(nameSlice1(nChunks), '/');
    savePath = strcat(expPath, '/', res{1}, '/', res{2}, '/', ...
        commonData.feature); 
    
    % Merge JSONs and save the result back to the network share
    localMerge(localPath, nameS2, savePath);
  
    % Change the feature log folder: SPF
    commonData.feature = strcat(logFolders{2}, '/', ...
        num2str(floor(timeInterval(i)/timeDiv)), timeStr);

    % Compute SPF
    fprintf('Computing SPF...\n');
    parfor j = 1:nChunks
        computeSPF(sig1{j}, sig2{j}, audioPairDelay(j), ...
        spfFilterBank, nameSlice1(j), nameSlice2(j), commonData, j);
    end
    
    % Construct savePath
    savePath = strcat(expPath, '/', res{1}, '/', res{2}, '/', ...
        commonData.feature); 
    
    % Merge JSONs and save the result back to the network share
    localMerge(localPath, nameS2, savePath);
    
	% Change the feature log folder: AFP
	commonData.feature = strcat(logFolders{3}, '/', ...
		num2str(floor(timeInterval(i)/timeDiv)), timeStr);

	% Compute AFP
	fprintf('Computing AFP...\n');
    parfor j = 1:nChunks
		computeAFP(sig1{j}, sig2{j}, audioPairDelay(j), ...
		afpFilterBank, nameSlice1(j), nameSlice2(j), commonData, j);
    end
	
    % Construct savePath
    savePath = strcat(expPath, '/', res{1}, '/', res{2}, '/', ...
        commonData.feature); 
    
    % Merge JSONs and save the result back to the network share
    localMerge(localPath, nameS2, savePath);
    
    % Change the feature log folder: NFP
    noiseData.feature = strcat(logFolders{4}, '/', ...
        num2str(floor(timeInterval(i)/timeDiv)), timeStr);
    
    % Compute NFP
    fprintf('Computing NFP...\n');
    computeNFP(nL1, nL2, timeInterval(i), noiseData);
       
end

% Close all open files (just in case)
fclose('all');

fprintf('Computations finished\n');

exit;

end

