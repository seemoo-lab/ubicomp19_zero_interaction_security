function [S1, S2] = alignTwoSignals(S1, S2, sampleDiff)
%ALIGNTWOSIGNALS Align two audio signals using: 1)xcorr delay and
% 2) cutting the length of both signals to the length of the shortest
% signal

%   Input args:
%   - S1 - first audio signal (Nx1 vector)
%   - S2 - second audio signal (Nx1 vector)
%   - sampleDiff - delay between two signals in samples (integer)

%   Output args:
%   - S1 - first audio signal aligned (Mx1 vector)
%   - S2 - second audio signal aligned (Mx1 vector)

%   N - the size of origninal audio signals(in samples)
%   M - the size of aligned audio signal (in samples)
%   M <= N

% Align two signals according to the delay
if sampleDiff > 0
    S1 = S1(sampleDiff:end);
elseif sampleDiff < 0
    S2 = S2(-sampleDiff:end);
end

% Lengths of the aligned signals
S1Len = length(S1);
S2Len = length(S2);

% The length of both signals is min(S1_len, S2_len)
signalLen = min(S1Len, S2Len);

% Make lengths of two signals equal
S1 = S1(1:signalLen);
S2 = S2(1:signalLen);

end


