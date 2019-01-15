function [freqBank] = thirdOctaveSplitter(signal, spfFilterBank)
% THIRDOCTAVESPLITTER Split an audio signal into 1/3 Octave bands.
% This implementation "manually" splits the signal using a set of bandpass 
% Butterworth filters. The inspiration for this script is from: 
% oct3bankFc.m and oct3dsgn.m

%   Input args:
%   - signal - Audio signal in samples (Nx1 vector)
%   - spfFilterBank - Filter bank (cell of size Mx1, each cell contains
% a digitalFilter object)

%   Output args:
%   - freqBank - Signal split into specified freqeuncy bands (MxN matrix)

%   Notes:
%   The filters are constructed in preComputeFilterSPF.m

% Initialize frequency bank 
freqBank = zeros(length(spfFilterBank), length(signal));

% Split audio signal in 1/3 Octave bands
for i = 1:length(spfFilterBank)
    freqBank(i,:) = filter(spfFilterBank{i}, signal);
end

end