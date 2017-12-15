function [] = saveJsonFile(fileName, fileContent)
%SAVEJSONFILE Summary of this function goes here
%   Detailed explanation goes here

% Open a file for writing
logID = fopen(fileName, 'w');

% Convert file content to JSON and write it to a file
fprintf(logID, jsonencode(fileContent));

% Close file
fclose(logID);

end

