function [signal] = normalizeSignal(signal)
%NORMALIZESIGNAL Normalize audio signal w.r.t. its energy

%   The code is courtesy of Hien Thi Thu Truong
%   Paper: "Comparing and Fusing Different Sensor Modalities for
%   Relay Attack Resistance in Zero-Interaction Authentication"

%   Input args:
%   - signal - incoming audio signal (can be Nx1 vector or NxM matrix)

%   N - the size of audio signal (in samples)
%   M - the number of audio signals in signal

%   Output args:
%   - signal - normalized audio signal (can be Nx1 vector or NxM matrix)

% Flip signal if necessary
[rows, columns] = size(signal);
if (columns > rows)
    signal = signal';
end

% Compute total energy of a signal
signalEnergy = signal' * signal;

% Get the number of audio channels, i.e. distinct audio signals
[~, nAudioChannels] = size(signal);

% Normalize energy of signal, store the result in normSignal
for i = 1:nAudioChannels
    signal(:,i) = signal(:,i)/(signalEnergy(i,i)^0.5);
end

end





