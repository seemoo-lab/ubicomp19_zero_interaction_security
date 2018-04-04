function [] = audioBenchmarking(inFile, scenario)
%AUDIOBENCHMARKING Summary of this function goes here
%   Detailed explanation goes here

% Version of the script
scriptVersion = 'v.1.0.0';

% Date format for logs
dateFormat = 'yyyy-mm-dd HH:MM:SS.FFF';

% Basic sampling frequency with which we are working
Fs = 16000;

% Open file for reading
fileID = fopen(inFile, 'r');

% Read file
format = '%s %s';
audioPairs = textscan(fileID, format);

% Close file
fclose(fileID);

% Precompute SPF filter bank
spfFilterBankFile = strcat('spfFilterBank.mat');
if exist(spfFilterBankFile, 'file') == 2
   fprintf('"%s" exists, loading it...\n', spfFilterBankFile);
   load(spfFilterBankFile);
else
    fprintf('"%s" does not exist, precomputing...\n', spfFilterBankFile);
    spfFilterBank = preComputeFilterSPF();
    save(spfFilterBankFile, 'spfFilterBank');
end

% Precompute AFP filter bank
afpFilterBankFile = strcat('afpFilterBank.mat');
if exist(afpFilterBankFile, 'file') == 2
   fprintf('"%s" exists, loading it...\n', afpFilterBankFile);
   load(afpFilterBankFile);
else
    fprintf('"%s" does not exist, precomputing...\n', afpFilterBankFile);
    afpFilterBank = preComputeFilterAFP();
    save(afpFilterBankFile, 'afpFilterBank');
end

% Check if we have a valid scenario
if strcmp(scenario, 'car') == 0 & strcmp(scenario, 'office') == 0
    fprintf('Scenario: "%s" is not allowed, only "car" or "office"\n', scenario);
    return;
end

% Time interval used for NFP
timeInterval = str2double(extractBetween(audioPairs{1}{1}, ...
    strcat('_', scenario, '-'), '.flac'));

% Matrix of results (r1 - tfd, r2 - spf, r3 - afp, r4 - nfp, r5 - npf conv)
res = zeros(5, length(audioPairs{1}));

% Iterate over audio pairs
for i=1:length(audioPairs{1})
    
    % Type of loaded audio data: native for noise features
    dataType = 'native';
    
    % Load two audio signals
    S1 = loadSignal(audioPairs{1}{i}, dataType);
    S2 = loadSignal(audioPairs{2}{i}, dataType);
   
    % Number of samples to compute one value of noise level: 
    % in Miettinen et al. time window was 100 ms and 1 sec
    winLen = round(1*Fs);

    % Number of noise samples out of S1 and S2
    nNoiseSamples = round(length(S1)/winLen);

    % Resulting noise level arrays
    nL1 = zeros(1, nNoiseSamples);
    nL2 = zeros(1, nNoiseSamples);
    
    tic;
    % Get noise levels
    for j=1:nNoiseSamples

        % Split into chunks of length winLen
        if j == nNoiseSamples
            % The last split signal -> take the reminder of initial signal
            winS1 = S1((j-1)*winLen+1:length(S1));
            winS2 = S2((j-1)*winLen+1:length(S2));   
        else
            % Regular split
            winS1 = S1((j-1)*winLen+1:winLen*j);
            winS2 = S2((j-1)*winLen+1:winLen*j);
        end

        % Compute average noise of the window 
        % (we have signed 16-bit: take abs values)
        nL1(j) = mean(abs(winS1));
        nL2(j) = mean(abs(winS2));   
    end
    res(5, i) = toc;
    
    % Clear S1 and S2
    clear S1;
    clear S2;
    
    % Switch back to double data type which we used in our implementation
    dataType = 'double';
    
    % Load two audio signals again
    S1 = loadSignal(audioPairs{1}{i}, dataType);
    S2 = loadSignal(audioPairs{2}{i}, dataType);
    
    % Compute TFD
    tic;
    timeFreqDistance(S1, S2);
    res(1, i) = toc;
%     fprintf('tfd time: %f\n', res(1, i));
    
    % Compute SPF
    tic;
    soundProofXcorr(S1, S2, Fs, spfFilterBank);
    res(2, i) = toc;
%     fprintf('spf time: %f\n', res(2, i));
    
    % Compute AFP
    tic;
    audioFingerprint(S1, S2, afpFilterBank);
    res(3, i) = toc;
%     fprintf('afp time: %f\n', res(3, i));
    
    % Compute NFP
    tic;
    noiseFingerprint([nL1 nL2], [nL2 nL1], timeInterval);
    res(4, i) = toc;
%     fprintf('nfp time: %f\n', res(4, i));
end

% Construct metadata struct
metadata = struct;

% Metadata struct: generator_version
metadata.generator_version = scriptVersion;

% Params to compute hash
Opt.Format = 'hex';
Opt.Method = 'SHA-1';
Opt.Input = 'file';

% Metadata struct: source_file
metadata.source_file = strcat(inFile, ' (', DataHash(inFile, Opt), ')');

% Metadata struct: generator_script
metadata.generator_script = strcat(mfilename, '.m');

% TFD stuct: exec time mean, std and values
tfd = struct;
tfd.exec_mean = mean(res(1,:));
tfd.exec_std = std(res(1,:));
tfd.exec_val = res(1,:);

% SPF stuct: exec time mean, std and values
spf = struct;
spf.exec_mean = mean(res(2,:));
spf.exec_std = std(res(2,:));
spf.exec_val = res(2,:);

% AFP stuct: exec time mean, std and values
afp = struct;
afp.exec_mean = mean(res(3,:));
afp.exec_std = std(res(3,:));
afp.exec_val = res(3,:);

% NFP stuct: exec time mean, std and values
nfp = struct;
nfp.exec_mean = mean(res(4,:));
nfp.exec_std = std(res(4,:));
nfp.exec_val = res(4,:);
nfp.conv_mean = mean(res(5,:));

% Feature struct: tfd, spf, afp, nfp
feature = struct;
feature.tfd = tfd;
feature.spf = spf;
feature.afp = afp;
feature.nfp = nfp;

% Metadata struct: created_on
metadata.created_on = datestr(datetime('now'), dateFormat);

% Output struct: contains both metadata and results
output.metadata = metadata; 
output.results = feature;

% Construct full path for log file
tmp = strsplit(inFile, '/');
fileName = strsplit(char(tmp(length(tmp))), '.');
fileName = fileName{1};
fileName(1) = upper(fileName(1)); 
logFile = strcat(strjoin(tmp(1:end-1),'/'), '/', fileName, '.json');

saveJsonFile(char(logFile), output);

end

