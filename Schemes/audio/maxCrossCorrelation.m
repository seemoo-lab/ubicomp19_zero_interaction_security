function [maxXCorr, S1, S2] = maxCrossCorrelation(S1, S2)
% MAXCROSSCORRELATION Compute absolute value of maximum cross-correlation
% between two normalized signals

%   Input args:
%   - S1 - First audio signal (Mx1 vector)
%   - S2 - Second audio signal (Mx1 vector)

%   Output args: 
%   - S1 - Normalized first audio signal (Mx1 vector)
%   - S2 - Normalized second audio signal (Mx1 vector)
%   - maxXCorr - Maximum cross-correlation (float)

% Normalize audio signals (Energy norm from Truong et al.)
S1 = normalizeSignal(S1);
S2 = normalizeSignal(S2);

% Compute max xcorr between the normalized audio signals
maxXCorr = max(abs(xcorr(S1, S2)));

end