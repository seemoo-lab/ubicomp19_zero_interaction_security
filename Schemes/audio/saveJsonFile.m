function [] = saveJsonFile(fileName, fileContent)
% SAVEJSONFILE Save data to a JSON file

%   Input args:
%   - fileName - Full path of the resulting JSON file (string)
%   - fileContent - Data to be saved (struct)

%   Output args: None

% Open a file for writing
logID = fopen(fileName, 'w');

% Convert file content to JSON and write it to a file
fprintf(logID, jsonencode(fileContent));

% Close file
fclose(logID);

end