function [signal, Fs] = loadSignal(fileName, dataType)
%LOADSIGNAL Summary of this function goes here
%   Detailed explanation goes here

%   Input args:
%   - fileName - absolute path to an audio file
%   - dataType - type of data to be loaded from an audio file:
%   'double' - double-precision normalized samples ([-1, 1])
%   'native' - raw PCM values from a .flac file

% Sampling frequency of audio from SensorTag
Fs = 16000;

% Check dataType value (make 'double' default as in audioread function)
if ~strcmp(dataType, 'double') & ~strcmp(dataType, 'native')
    dataType = 'double';
end

% Read signal from a .flac file
[signal, Fs1] = audioread(fileName, dataType);

% fprintf('Fs1 = %.1f\n', Fs1);
% Fs = Fs1;

% Resample signals to Fs if necessary
if Fs1 ~= Fs
    fprintf('Resampling signal from %.1f to %.1f kHz\n', Fs1, Fs);
    [P, Q] = rat(Fs/Fs1);
    signal = resample(signal, P, Q);
end

end
