function [sampleDiff] = xcorrDelay(S1, S2, timeLag, Fs)
%XCORRDELAY Summary of this function goes here
%   Detailed explanation goes here

% We assume that devices are sync to a certain degree, so we should use a
% l_max parameter, similarly to Sound-Proof. In Sound-Proof l_max was found
% emperically (150 ms) as the max delay between two signals -> depends on the
% precision of the sync protocol. We will follow the same approach and
% introduce maxLag parameter, which will be used for estimation the delay
% estimation of two signals (see maxlag in xcorr function).
% From the observed data so far: 6 SensorTags in the same room l_max ~= 1.6
% sec, we will double this value for the default maxLag = 3 sec
maxLag = round(timeLag*Fs);

% Find a delay between two signals (use cross-correlation)
[acorr, lag] = xcorr(S1, S2, maxLag);
[~, I] = max(abs(acorr));
sampleDiff = lag(I);

end

