function [hamDist] = binHammingDist(bfp1, bfp2)
%BINHAMMINGDIST Summary of this function goes here
%   Compute Hamming distance between two binary fingerprints

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

