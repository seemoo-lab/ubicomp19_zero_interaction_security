function [hamDist] = binHammingDist(bfp1, bfp2)
% BINHAMMINGDIST Compute Hamming Distance between two binary fingerprints

%   Input args:
%   - bfp1 - First binary fingerprint (Nx1 vector)
%   - bfp2 - Second binary fingerprint (Nx1 vector)

%   Output args: 
%   - hamDist - Hamming distance, i.e., a number of differing bits (integer)

% Hamming distance in number of bits
hamDist = 0;

% Length of a binary fingerprint (bfp1 == bpf2)
bfpSize = length(bfp1);

% Get Hamming distance in number of bits
for i=1:bfpSize
    if bfp1(i) ~= bfp2(i)
       hamDist = hamDist + 1; 
    end
end

end