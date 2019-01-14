function [nfpS1, nfpS2] = noiseFingerprint(nL1, nL2, snapshotLen, noiseData)
%NOISEFINGERPRINT Summary of this function goes here
%   Detailed explanation goes here

%   Input args:
%   - nL1 - array of noise levels transformed from S1
%   - nL2 - array of noise levels transformed from S2
%   - snapshotLen - lenght of snapshot: e.g. 60 sec, 120 sec
%	(snapshotLen values are form Miettinen et al.)

% Threshold values are from Miettinen et al.

% Absolute threshold 
absThreshold = 10;

% Relative threshold
relThreshold = 0.1;

% Number of snapshots (split noise level arrays 
% into a number of snapshots)
nSnapshots = round(length(nL1)/snapshotLen);

% Snapshot arrays
snapshot1 = zeros(1, nSnapshots);
snapshot2 = zeros(1, nSnapshots);

% Construct snapshot values
for i=1:nSnapshots
    
    % Split into chunks of length snapshotLen
    if i == nSnapshots
        % The last split signal -> take the reminder of initial signal
        winNl1 = nL1((i-1)*snapshotLen+1:length(nL1));
        winNl2 = nL2((i-1)*snapshotLen+1:length(nL2));   
    else
        % Regular split
        winNl1 = nL1((i-1)*snapshotLen+1:snapshotLen*i);
        winNl2 = nL2((i-1)*snapshotLen+1:snapshotLen*i);
    end
    
	% Compute average noise level of the window
    snapshot1(i) = mean(winNl1);
    snapshot2(i) = mean(winNl2);   
end

% Adjust noiseData
noiseData.sampleLenSec = snapshotLen;

% Save noise levels into JSON-files
saveNoiseLevels(snapshot1, snapshot2, noiseData);

% Noise fingerprints
nfpSize = nSnapshots-1;
nfpS1 = zeros(1, nfpSize);
nfpS2 = zeros(1, nfpSize);

% Construct noise fingerprints
for i=1:nfpSize

    if snapshot1(i) == 0
       snapshot1(i) = 0.000001;
    end

    if snapshot2(i) == 0
       snapshot2(i) = 0.000001;
    end
    
	% Check noise levels of nL1, formula (3) from Miettinen et al.
    if  abs(snapshot1(i+1)/snapshot1(i)-1) > relThreshold & ...
            abs(snapshot1(i+1)-snapshot1(i)) > absThreshold
        nfpS1(i) = 1;
    else 
        nfpS1(i) = 0;
    end
    
	% Check noise levels nL2, formula (3) from Miettinen et al.
    if abs(snapshot2(i+1)/snapshot2(i)-1) > relThreshold & ...
            abs(snapshot2(i+1)-snapshot2(i)) > absThreshold
        nfpS2(i) = 1;
    else 
        nfpS2(i) = 0;
    end   
end

end
