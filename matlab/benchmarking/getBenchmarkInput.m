function [] = getBenchmarkInput(inPath, outPath, scenario)
%GETBENCHMARKINPUT Summary of this function goes here
%   Detailed explanation goes here

% Array of time intervals to compute on in sec
timeInterval = [5 10 15 30 60 120];

if strcmp(scenario, 'car') == 1 
    nSensors = 12;
    nContexts = 2;
    nSensorsPerContext = nSensors/nContexts;
elseif strcmp(scenario, 'office') == 1
    nSensors = 24;
    nContexts = 3;
    nSensorsPerContext = nSensors/nContexts;
else
    fprintf('Scenario: "%s" is not allowed, only "car" or "office"\n', scenario);
    return;
end

% Iterate over time intervals
for i=1:length(timeInterval)
    
    % Read all files from the same interval
    inPattern = strcat('*', scenario,  '-', num2str(timeInterval(i)),'.flac');
    inFolder = dir(strcat(inPath, '/', inPattern));
    
    % Check if audio files exist
    if isempty(inFolder)
        fprintf('Cannot find %s files in: %s\n', inPattern, inPath);
        return; 
    end
    
    % Check if we have the correct number of sensors
    if length(inFolder) ~= nSensors
        fprintf('The number of files must be %d not %d\n', nSensors, ...
            length(inFolder));
        return;
    end
    
    % allPairs = (nSensors-1)*(nSensors-nSensors/2);
    
    % Number of co-located pairs (symmetry is in place)
    nColocatedPairs = nContexts*((nSensorsPerContext-1)*(nSensorsPerContext-nSensorsPerContext/2));
    colocatedPairs = cell(nColocatedPairs, 1);
    
    % Loop for co-located pairs
    idx = 1;
    for k=1:nContexts
%         fprintf('k = %d, j1 = %d, j2 = %d\n', k, (k-1)*nSensorsPerContext+1, k*nSensorsPerContext-1);
        for j=(k-1)*nSensorsPerContext+1:k*nSensorsPerContext-1
            for m=j+1:k*nSensorsPerContext
                colocatedPairs{idx} = horzcat(inPath, '/', inFolder(j).name, ...
                    ' ', inPath, '/', inFolder(m).name);
                idx = idx + 1;
            end
        end
    end
    
    % Save co-located pairs
    fileName = strcat(outPath, '/', scenario, '_', num2str(timeInterval(i)),...
        '_co-located.txt');
    fileID = fopen(fileName,'w');
    fprintf(fileID,'%s\n', colocatedPairs{:});
    fclose(fileID);
    
    % Number of non-colocated pairs (symmetry is in place)
    nNonColocatedPairs = (nContexts-1)*nSensorsPerContext*(nSensors-(nContexts/2)*nSensorsPerContext);
    nonColocatedPairs = cell(nNonColocatedPairs, 1);
    
    % Loop for non-colocated pairs
    idx = 1;
    for k=1:nContexts-1
%         fprintf('k = %d, j1 = %d, j2 = %d\n', k, (k-1)*nSensorsPerContext+1, k*nSensorsPerContext);
        for j=(k-1)*nSensorsPerContext+1:k*nSensorsPerContext 
%             fprintf('j = %d, m1 = %d, m2 = %d\n', j, k*nSensorsPerContext+1, nSensors);
            for m=k*nSensorsPerContext+1:nSensors
                nonColocatedPairs{idx} = horzcat(inPath, '/', inFolder(j).name, ...
                    ' ', inPath, '/', inFolder(m).name);
                idx = idx + 1;
            end
        end
    end
    
    % Save non-colocated pairs
    fileName = strcat(outPath, '/', scenario, '_', num2str(timeInterval(i)),...
        '_non-colocated.txt');
    fileID = fopen(fileName,'w');
    fprintf(fileID,'%s\n', nonColocatedPairs{:});
    fclose(fileID);
end

end

