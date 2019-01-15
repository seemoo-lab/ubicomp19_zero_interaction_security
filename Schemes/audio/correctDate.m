function [outDate] = correctDate(inDate)
%CORRECTDATE Remove JSON artifacts in the timestamp part fo the JSON after
% merging log files from the whole signal

%   Input args:
%   - inDate - Input date, format: 'xyyyy_mm_ddHH_MM_SS_FFF' (string)

%   Output args: 
%   - outDate - Output date, format: 'yyyy-mm-dd HH:MM:SS.FFF' (string)

% Desired format
desiredFormat = 'yyyy-mm-dd HH:MM:SS.FFF';

% Remove the first 'x' symbol
inDate = inDate(2:end);

% Find date length from desiredFormat
tmp = strsplit(desiredFormat, ' ');
dateLen = length(tmp{1});

% Split inDate in date and time
date = inDate(1:dateLen);
time = inDate(dateLen+1:end);

% Replace '_'s with '-'es in date
date = strrep(date, '_', '-');

% Replace '_'s with ':'s in time
time = strrep(time, '_', ':');

% Find index of '.' in desiredFormat
idx = strfind(desiredFormat, '.');

% Idx from the end of desiredFormat string
idx = length(desiredFormat) - idx;

% Replace the last ':' with '.': .FFF
time(length(time)-idx) = '.';

% Construct outDate
outDate = horzcat(date, ' ', time);

end