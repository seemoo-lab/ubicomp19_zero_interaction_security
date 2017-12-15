function [maxXCorr, S1, S2] = maxCrossCorrelation(S1, S2)
%MAXCROSSCORRELATION Summary of this function goes here
%   Detailed explanation goes here

% Normalize audio signals (Energy norm from Truong et al.)
S1 = normalizeSignal(S1);
S2 = normalizeSignal(S2);

% Compute max xcorr between the normalized audio signals
maxXCorr = max(abs(xcorr(S1, S2)));

end


