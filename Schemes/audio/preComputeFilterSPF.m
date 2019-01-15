function [spfFilterBank] = preComputeFilterSPF()
% PRECOMPUTEFILTERSPF Precompute a filter bank for splitting an audio
% signal into 20 octave bands

%   Input args: None

%   Output args:
%   - spfFilterBank - Filter bank (cell of size 20x1, each cell contains
% a digitalFilter object)

% Basic sampling frequency with which we are working
Fs = 16000;

% Frequency bands to be splitted into -> 20 bands: 50-4000Hz as in the SPF paper
Fb = [50 63 80 100 125 160 200 250 315 400, ...
    500 630 800 1000 1250 1600 2000 2500 3150 4000];

% Filter order (translates to 2*filterOrder order filter for bandpass and bandstop filters:
% see MATLAB "butter" function)
filterOrder = 20;

% Bandwidth: 1/3 Octave
Bw = 1/3;

% 1/3 Octave center frequency labels: 
% see http://www.engineeringtoolbox.com/octave-bands-frequency-limits-d_1602.html
F = [16 20 25 31.5 40 50 63 80 100 125 160 200 250 315 400 500 630 800 1000 1250, ... 
 	1600 2000 2500 3150 4000 5000 6300 8000 10000 12500 16000 20000];  

% Extract actual 1/3 Octave center frequencies: 
% see https://en.wikipedia.org/wiki/Octave_band
Fc = 10^3 * (2 .^ ([-18:13]/3)); 

% Get center frequencies from user defined bands (Fb)
for id = 1:length(Fb)
   iF(id) = find(F == Fb(id)); 
end
Fc = Fc(iF);

% Initialize a cell to store filters
spfFilterBank = cell(length(Fc), 1);

% Construct BP-filters for 1/3 Octave bands
for i = 1:length(Fc)
   
    % Low and high cutoff frequencies
    Fl = Fc(i)*(2^(-Bw/2));
    Fh = Fc(i)*(2^(Bw/2));
    
    % Design a bandpass filter
    bpFilter = designfilt('bandpassiir', 'FilterOrder', filterOrder, ...
    'HalfPowerFrequency1', Fl, 'HalfPowerFrequency2', Fh, ...
    'SampleRate', Fs);

    % Save a filter to the cell
    spfFilterBank{i} = bpFilter;
end

end