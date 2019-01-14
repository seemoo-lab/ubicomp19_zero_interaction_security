function [maxXCorr, freqDist, timeFreqDist] = timeFreqDistance(S1, S2, sampleDiff)
%TIMEFREQDISTANCE Summary of this function goes here
%   Detailed explanation goes here

% Align two signals based on the computed with xcorr delay (sampleDiff)
[S1, S2] = alignTwoSignals(S1, S2, sampleDiff);

% Compute max xcorr between the aligned and normalized audio signals
[maxXCorr, S1, S2] = maxCrossCorrelation(S1, S2);

% Length of the alinged and normalized signal
signalLen = length(S1);

% Apply the Hamming window to normalized audio signals
S1 = S1 .* hamming(signalLen, 'periodic'); 
S2 = S2 .* hamming(signalLen, 'periodic');

% Param to speed up FFT computation
nfft = 2^nextpow2(signalLen);

% Compute FFTs of two audio signals
fftS1 = fft(S1, nfft);
fftS2 = fft(S2, nfft);

% Take half of the computed FFT
halfFFT = round(nfft/2);
fftS1 = abs(fftS1(1:halfFFT));
fftS2 = abs(fftS2(1:halfFFT));

% Normalize computed FFTs
fftS1 = normalizeSignal(fftS1);
fftS2 = normalizeSignal(fftS2);

% Frequency distance
freqDist = sqrt(sum((fftS1 - fftS2) .* (fftS1 - fftS2)));

% Time-frequency distance
timeFreqDist = sqrt((1 - maxXCorr)^2 + freqDist^2);

end