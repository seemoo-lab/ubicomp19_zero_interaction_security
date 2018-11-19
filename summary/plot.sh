#!/bin/bash

# SPF part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF car full
python3 plot_error_rates.py /home/seemoo/json1/CarExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF car city
python3 plot_error_rates.py /home/seemoo/json1/CarExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF car highway
python3 plot_error_rates.py /home/seemoo/json1/CarExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF car parked

python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF office full
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF office night
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF office weekday
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF office weekend

python3 plot_error_rates.py /home/seemoo/json1/MobileExp/soundProofXcorr/max_xcorr/ /home/seemoo/test/ SPF mobile full

# AFP part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP car full
python3 plot_error_rates.py /home/seemoo/json1/CarExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP car city
python3 plot_error_rates.py /home/seemoo/json1/CarExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP car highway
python3 plot_error_rates.py /home/seemoo/json1/CarExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP car parked

python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP office full
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP office night
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP office weekday
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP office weekend

python3 plot_error_rates.py /home/seemoo/json1/MobileExp/audioFingerprint/fingerprints_similarity_percent/ /home/seemoo/test/ AFP mobile full

# NFP part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/noiseFingerprint/similarity_percent/ /home/seemoo/test/ NFP car
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/noiseFingerprint/similarity_percent/ /home/seemoo/test/ NFP office
python3 plot_error_rates.py /home/seemoo/json1/MobileExp/noiseFingerprint/similarity_percent/ /home/seemoo/test/ NFP mobile

# LFP part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/lux_miettinen/similarity_percent/ /home/seemoo/test/ LFP car 
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/lux_miettinen/similarity_percent/ /home/seemoo/test/ LFP office
python3 plot_error_rates.py /home/seemoo/json1/MobileExp/lux_miettinen/similarity_percent/ /home/seemoo/test/ LFP mobile

# Truong part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/truong/ml/ /home/seemoo/test/ truong car
python3 plot_error_rates.py /home/seemoo/json1/CarExp/truong/ml/ /home/seemoo/test/ truong_30sec car

python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/truong/ml/ /home/seemoo/test/ truong office
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/truong/ml/ /home/seemoo/test/ truong_30sec office

python3 plot_error_rates.py /home/seemoo/json1/MobileExp/truong/ml/ /home/seemoo/test/ truong mobile
python3 plot_error_rates.py /home/seemoo/json1/MobileExp/truong/ml/ /home/seemoo/test/ truong_30sec mobile

# Shrestha part
python3 plot_error_rates.py /home/seemoo/json1/CarExp/shrestha/ml/ /home/seemoo/test/ shrestha car
python3 plot_error_rates.py /home/seemoo/json1/OfficeExp/shrestha/ml/ /home/seemoo/test/ shrestha office
python3 plot_error_rates.py /home/seemoo/json1/MobileExp/shrestha/ml/ /home/seemoo/test/ shrestha mobile
